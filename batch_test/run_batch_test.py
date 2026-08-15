#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "remove-ai-marks" / "scripts"
MANIFEST_PATH = ROOT / "batch-test-samples" / "manifest.json"
SCREENSHOT_DIR = ROOT / "batch-test-screenshots"
DOWNLOAD_DIR = ROOT / "batch-test-downloads"
RESULTS_DIR = ROOT / "batch-test-results"
RESULTS_JSON = RESULTS_DIR / "results.json"
REPORT_MD = RESULTS_DIR / "report.md"
SITE_URL = "https://watermarks-remover-production.up.railway.app/zh"

sys.path.insert(0, str(SCRIPTS))

from image_meta import inspect_image  # noqa: E402
from container_meta import inspect_container  # noqa: E402

CATEGORY_LABELS = {
    "claude_hidden_unicode": "Claude 输出文本（隐藏 Unicode）",
    "gpt_hidden_unicode": "GPT 输出文本（隐藏 Unicode）",
    "zero_width_characters": "零宽字符",
    "homoglyph_substitution": "同形异义字替换",
    "bidi_control_characters": "Unicode 方向控制字符",
    "html_entity_or_hidden_span": "HTML 实体 / 不可见 span 注入",
    "other_ai_tool_text": "其他 AI 工具输出文本",
    "image_exif_watermark": "PNG/JPG EXIF 水印",
    "png_c2pa_chunk": "PNG C2PA chunk",
    "png_custom_text_chunks": "PNG 自定义 tEXt / iTXt chunk",
    "jpg_xmp_watermark": "JPG XMP 水印",
    "pdf_hidden_metadata": "PDF 隐藏元数据",
}

TEXT_CATEGORIES = {
    "claude_hidden_unicode",
    "gpt_hidden_unicode",
    "zero_width_characters",
    "homoglyph_substitution",
    "bidi_control_characters",
    "html_entity_or_hidden_span",
    "other_ai_tool_text",
}

FILE_CATEGORIES = set(CATEGORY_LABELS) - TEXT_CATEGORIES


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def ensure_dirs() -> None:
    for path in (SCREENSHOT_DIR, DOWNLOAD_DIR, RESULTS_DIR):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def wait_until_idle(page) -> None:
    page.wait_for_timeout(250)
    page.wait_for_load_state("networkidle", timeout=15000)


def open_site(page, site_url: str) -> None:
    page.goto(site_url, wait_until="domcontentloaded", timeout=45000)
    wait_until_idle(page)
    page.locator("body").wait_for(timeout=10000)


def ensure_text_tab(page) -> None:
    page.locator('.tab[data-mode="text"]').click(timeout=10000)
    page.locator('#textInput').wait_for(timeout=10000)


def ensure_file_tab(page) -> None:
    page.locator('.tab[data-mode="file"]').click(timeout=10000)
    page.locator('form#fileForm').wait_for(state="visible", timeout=10000)


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(" ", "_")


def capture(page, name: str) -> str:
    path = SCREENSHOT_DIR / name
    page.screenshot(path=str(path), full_page=True)
    return str(path.relative_to(ROOT))


def verify_file_output(sample: dict[str, Any], downloaded_path: Path) -> tuple[bool, str, dict[str, Any]]:
    category = sample["category"]
    if category in {"image_exif_watermark", "png_c2pa_chunk", "png_custom_text_chunks", "jpg_xmp_watermark"}:
        report = inspect_image(downloaded_path).to_dict()
        ok = not report["has_ai_metadata"] and not report["has_c2pa"]
        reason = "clean" if ok else f"残留图片元数据/C2PA: {report['findings'][:5]}"
        return ok, reason, report
    if category == "pdf_hidden_metadata":
        report = inspect_container(downloaded_path).to_dict()
        ok = not report["has_ai_metadata"] and not report["has_c2pa"]
        reason = "clean" if ok else f"残留 PDF 元数据: {report['findings'][:5]}"
        return ok, reason, report
    raise ValueError(f"unexpected file category: {category}")


def run_text_sample(page, sample: dict[str, Any], category_done: set[str]) -> dict[str, Any]:
    ensure_text_tab(page)
    raw_text = Path(ROOT / sample["input_path"]).read_text(encoding="utf-8")
    expected = normalize_text(sample["expected_text"])
    textarea = page.locator("#textInput")
    textarea.fill(raw_text)
    with page.expect_response(lambda r: "/api/clean-text" in r.url and r.request.method == "POST", timeout=45000) as response_info:
        page.locator("#cleanTextBtn").click(timeout=10000)
    response = response_info.value
    payload = response.json()
    page.wait_for_timeout(300)
    actual = normalize_text(textarea.input_value())
    passed = actual == expected
    failure_reason = ""
    if not passed:
        failure_reason = f"期望 {expected!r}，实际 {actual!r}"
    screenshot = None
    if sample["category"] not in category_done:
        screenshot = capture(page, f"category-{safe_name(sample['category'])}.png")
        category_done.add(sample["category"])
    failure_screenshot = None
    if not passed:
        failure_screenshot = capture(page, f"failure-{sample['id']}.png")
    return {
        "id": sample["id"],
        "kind": "text",
        "category": sample["category"],
        "category_label": CATEGORY_LABELS[sample["category"]],
        "source": sample["source"],
        "input_path": sample["input_path"],
        "passed": passed,
        "expected_text": expected,
        "actual_text": actual,
        "failure_reason": failure_reason,
        "category_screenshot": screenshot,
        "failure_screenshot": failure_screenshot,
        "api_ok": payload.get("ok"),
        "api_report": payload.get("report"),
    }


def run_file_sample(page, sample: dict[str, Any], category_done: set[str]) -> dict[str, Any]:
    ensure_file_tab(page)
    input_path = ROOT / sample["input_path"]
    page.locator("#fileInput").set_input_files(str(input_path))
    page.wait_for_timeout(250)
    submit = page.locator("form#fileForm button[type='submit']")
    with page.expect_response(lambda r: "/api/clean" in r.url and r.request.method == "POST", timeout=90000) as response_info:
        submit.click(timeout=10000)
    response = response_info.value
    payload = response.json()
    page.wait_for_timeout(500)

    screenshot = None
    if sample["category"] not in category_done:
        screenshot = capture(page, f"category-{safe_name(sample['category'])}.png")
        category_done.add(sample["category"])

    download_path_rel = None
    verify_ok = False
    verify_reason = "API 未返回下载链接"
    verify_report: dict[str, Any] | None = None

    if payload.get("download_url"):
        download_link = page.locator("#downloadLink")
        try:
            with page.expect_download(timeout=45000) as download_info:
                download_link.click(timeout=10000)
            download = download_info.value
            suffix = input_path.suffix or Path(download.suggested_filename).suffix
            saved_path = DOWNLOAD_DIR / f"{sample['id']}{suffix}"
            download.save_as(str(saved_path))
            download_path_rel = str(saved_path.relative_to(ROOT))
            verify_ok, verify_reason, verify_report = verify_file_output(sample, saved_path)
        except PlaywrightTimeoutError:
            verify_reason = "点击下载后未收到浏览器下载事件"
    else:
        verify_reason = f"API 未返回下载链接，payload={payload}"

    passed = bool(verify_ok)
    failure_screenshot = None
    if not passed:
        failure_screenshot = capture(page, f"failure-{sample['id']}.png")

    return {
        "id": sample["id"],
        "kind": "file",
        "category": sample["category"],
        "category_label": CATEGORY_LABELS[sample["category"]],
        "source": sample["source"],
        "input_path": sample["input_path"],
        "download_path": download_path_rel,
        "passed": passed,
        "failure_reason": verify_reason if not passed else "",
        "category_screenshot": screenshot,
        "failure_screenshot": failure_screenshot,
        "api_ok": payload.get("ok"),
        "api_report": payload.get("report"),
        "verification_report": verify_report,
    }


def summarize(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["category"]].append(result)

    category_rows: list[dict[str, Any]] = []
    passed_total = 0
    for category in CATEGORY_LABELS:
        items = grouped.get(category, [])
        passed = sum(1 for item in items if item["passed"])
        total = len(items)
        passed_total += passed
        category_rows.append(
            {
                "category": category,
                "category_label": CATEGORY_LABELS[category],
                "passed": passed,
                "total": total,
                "pass_rate": round((passed / total * 100.0), 2) if total else 0.0,
                "screenshot": next((item.get("category_screenshot") for item in items if item.get("category_screenshot")), None),
            }
        )

    overall = {
        "passed": passed_total,
        "total": len(results),
        "pass_rate": round((passed_total / len(results) * 100.0), 2) if results else 0.0,
        "target_met": passed_total / len(results) >= 0.9 if results else False,
    }
    return category_rows, overall


def infer_improvements(category_rows: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[str]:
    failed_by_category = {row["category"]: row for row in category_rows if row["passed"] < row["total"]}
    suggestions: list[str] = []
    if "homoglyph_substitution" in failed_by_category:
        suggestions.append("文本输入框当前固定关闭 aggressive_homoglyphs，建议为文本模式增加“深度清理/同形字归一化”开关，并在后端允许默认或可选调用 `--aggressive-homoglyphs`。")
    if "html_entity_or_hidden_span" in failed_by_category:
        suggestions.append("文本模式当前只做字符级清理，不会解析 HTML 实体或剥离隐藏标签；建议在文本模式增加 HTML decode 与隐藏标签剥离逻辑，或者在界面上明确提示“文本框不处理 HTML 结构”。")
    if "pdf_hidden_metadata" in failed_by_category:
        suggestions.append("PDF 清理依赖 exiftool 时效果更稳定；若线上环境未安装 exiftool，建议在 Railway 镜像中补齐，避免仅靠纯 Python 降级路径。")
    if any(result["category"] == "jpg_xmp_watermark" and not result["passed"] for result in results):
        suggestions.append("如果 JPG XMP 样本仍有残留，建议在清理后再做一次更严格的 APP1/XMP 扫描，确认 `xmpmeta` 和相关 APP 段都被完整剥离。")
    if any(result["category"] == "png_custom_text_chunks" and not result["passed"] for result in results):
        suggestions.append("若 PNG 文本块样本存在漏清，建议在保守模式之外提供“完全移除全部 tEXt/zTXt/iTXt chunk”的明确选项，并在报告中区分保守清理和彻底清理。")
    if not suggestions:
        suggestions.append("本轮 100 个样本没有发现需要立即修复的类别级问题，下一步可补充更复杂的真实世界样本，例如混合格式 HTML、带嵌入资源的 PDF、以及更长文本段落。")
    return suggestions


def build_report(results: list[dict[str, Any]], category_rows: list[dict[str, Any]], overall: dict[str, Any], improvements: list[str], site_url: str) -> str:
    failures = [item for item in results if not item["passed"]]
    lines: list[str] = []
    lines.append("# Watermarks Remover 批量真实浏览器测试报告")
    lines.append("")
    lines.append(f"测试时间（UTC）：{datetime.now(timezone.utc).isoformat()}")
    lines.append(f"目标站点：{site_url}")
    lines.append("浏览器执行方式：Playwright Chromium（沙盒真实浏览器自动化）。")
    lines.append("说明：我先尝试了本地 aime-browser，但本地浏览器扩展在读取页面内容时持续报 `Cannot access a chrome-extension:// URL of different extension`，因此改用 Playwright 继续完成真实浏览器批量验证。")
    lines.append("")
    lines.append(f"总体通过率：**{overall['passed']}/{overall['total']} = {overall['pass_rate']}%**。")
    lines.append(f"是否达到 ≥90% 目标：**{'是' if overall['target_met'] else '否'}**。")
    lines.append("")
    lines.append("## 各类别通过率")
    lines.append("")
    lines.append("| 类别 | 通过/总数 | 通过率 | 类别截图 |")
    lines.append("| --- | ---: | ---: | --- |")
    for row in category_rows:
        shot = f"[{Path(row['screenshot']).name}]({row['screenshot']})" if row.get("screenshot") else "-"
        lines.append(f"| {row['category_label']} | {row['passed']}/{row['total']} | {row['pass_rate']}% | {shot} |")
    lines.append("")
    lines.append("## 失败样本详情")
    lines.append("")
    if not failures:
        lines.append("本轮没有失败样本。")
    else:
        lines.append("| 样本 ID | 类别 | 原因 | 失败截图 |")
        lines.append("| --- | --- | --- | --- |")
        for item in failures:
            shot = f"[{Path(item['failure_screenshot']).name}]({item['failure_screenshot']})" if item.get("failure_screenshot") else "-"
            reason = item["failure_reason"].replace("|", "\\|")[:240]
            lines.append(f"| {item['id']} | {item['category_label']} | {reason} | {shot} |")
    lines.append("")
    lines.append("## 改进建议")
    lines.append("")
    for suggestion in improvements:
        lines.append(f"- {suggestion}")
    lines.append("")
    lines.append("## 输出文件")
    lines.append("")
    lines.append(f"- 结果 JSON: [{RESULTS_JSON.relative_to(ROOT)}]({RESULTS_JSON.relative_to(ROOT)})")
    lines.append(f"- 截图目录: [{SCREENSHOT_DIR.relative_to(ROOT)}]({SCREENSHOT_DIR.relative_to(ROOT)})")
    lines.append(f"- 下载后的清理文件: [{DOWNLOAD_DIR.relative_to(ROOT)}]({DOWNLOAD_DIR.relative_to(ROOT)})")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run batch browser tests against the deployed site.")
    parser.add_argument("--kind", choices=["all", "text", "file"], default="all")
    parser.add_argument("--url", default=SITE_URL)
    args = parser.parse_args()

    manifest = load_manifest()
    samples: list[dict[str, Any]] = manifest["samples"]
    ensure_dirs()
    ordered_samples = sorted(samples, key=lambda item: (0 if item["kind"] == "text" else 1, item["category"], item["id"]))
    if args.kind != "all":
        ordered_samples = [item for item in ordered_samples if item["kind"] == args.kind]
    category_done: set[str] = set()
    results: list[dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True, locale="zh-CN")
        page = context.new_page()
        open_site(page, args.url)

        for index, sample in enumerate(ordered_samples, start=1):
            start = time.time()
            try:
                if sample["kind"] == "text":
                    result = run_text_sample(page, sample, category_done)
                else:
                    result = run_file_sample(page, sample, category_done)
            except Exception as exc:  # noqa: BLE001
                failure_shot = capture(page, f"failure-{sample['id']}-exception.png")
                result = {
                    "id": sample["id"],
                    "kind": sample["kind"],
                    "category": sample["category"],
                    "category_label": CATEGORY_LABELS[sample["category"]],
                    "source": sample["source"],
                    "input_path": sample["input_path"],
                    "passed": False,
                    "failure_reason": f"执行异常: {exc}",
                    "category_screenshot": None,
                    "failure_screenshot": failure_shot,
                }
                open_site(page, args.url)
            result["duration_seconds"] = round(time.time() - start, 3)
            results.append(result)
            if index % 10 == 0:
                print(f"processed {index}/{len(ordered_samples)} samples")

        context.close()
        browser.close()

    category_rows, overall = summarize(results)
    improvements = infer_improvements(category_rows, results)
    payload = {
        "generated_at": manifest.get("generated_at"),
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "site_url": args.url,
        "browser": "Playwright Chromium (sandbox)",
        "sample_total": len(results),
        "overall": overall,
        "categories": category_rows,
        "results": results,
        "improvements": improvements,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(build_report(results, category_rows, overall, improvements, args.url), encoding="utf-8")
    print(json.dumps({"results": str(RESULTS_JSON.relative_to(ROOT)), "report": str(REPORT_MD.relative_to(ROOT)), "overall": overall}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
