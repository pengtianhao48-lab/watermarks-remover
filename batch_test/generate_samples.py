#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import re
import struct
import zlib
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Callable

import piexif
import piexif.helper
from PIL import Image, ImageDraw, PngImagePlugin
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "remove-ai-marks" / "scripts"
SAMPLES_ROOT = ROOT / "batch-test-samples"
TEXT_DIR = SAMPLES_ROOT / "text"
FILE_DIR = SAMPLES_ROOT / "files"
MANIFEST_PATH = SAMPLES_ROOT / "manifest.json"

import sys
sys.path.insert(0, str(SCRIPTS))

from image_meta import inspect_image  # noqa: E402
from container_meta import inspect_container  # noqa: E402

PNG_SIG = b"\x89PNG\r\n\x1a\n"
ZERO_WIDTH_MARKERS = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2060"]
BIDI_MARKERS = ["\u202a", "\u202b", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069"]
TAG_MARKERS = [chr(0xE0041), chr(0xE0062), chr(0xE0063)]

HOMOGLYPH_MAP = {
    "a": "а",  # cyrillic a
    "e": "е",  # cyrillic e
    "o": "о",  # cyrillic o
    "p": "р",  # cyrillic er
    "c": "с",  # cyrillic es
    "x": "х",  # cyrillic ha
    "y": "у",  # cyrillic u
    "i": "і",  # cyrillic i
}

CATEGORY_COUNTS = {
    "claude_hidden_unicode": 20,
    "gpt_hidden_unicode": 20,
    "zero_width_characters": 10,
    "homoglyph_substitution": 5,
    "bidi_control_characters": 5,
    "html_entity_or_hidden_span": 5,
    "other_ai_tool_text": 5,
    "image_exif_watermark": 10,
    "png_c2pa_chunk": 5,
    "png_custom_text_chunks": 5,
    "jpg_xmp_watermark": 5,
    "pdf_hidden_metadata": 5,
}

BASE_TEXTS = [
    "The launch checklist is ready for tomorrow morning.",
    "Please archive the client notes after the meeting.",
    "A quiet workflow often produces better writing.",
    "Keep the roadmap simple and review risks weekly.",
    "The support queue dropped after the copy update.",
    "Short summaries are easier to verify and share.",
    "We saved the clean version in the review folder.",
    "Every draft should explain the next concrete step.",
    "A reliable process matters more than a clever trick.",
    "The export finished faster after we removed noise.",
    "Good tools are honest about what they can verify.",
    "The analyst checked each file before publishing it.",
    "A hidden marker should never surprise the owner.",
    "Review the evidence before declaring the task done.",
    "The browser workflow must match the real product.",
    "Metadata can travel farther than people expect.",
    "A clean report needs both numbers and examples.",
    "The final note should mention every failed case.",
    "We compare the input and output before approving.",
    "A stable script is better than a rushed manual step.",
]

CLAUDE_SENTENCES = [f"Claude sample {i+1}: {BASE_TEXTS[i]}" for i in range(20)]
GPT_SENTENCES = [f"GPT sample {i+1}: {BASE_TEXTS[i]}" for i in range(20)]
ZERO_WIDTH_SENTENCES = [
    "Zero width sample one keeps the visible wording intact.",
    "Zero width sample two checks several separators in one line.",
    "Zero width sample three should clean invisible glue safely.",
    "Zero width sample four verifies word joiners between tokens.",
    "Zero width sample five makes the copied text look ordinary.",
    "Zero width sample six mixes BOM and joiners in one sentence.",
    "Zero width sample seven hides marks between short words.",
    "Zero width sample eight verifies the output length shrinks.",
    "Zero width sample nine keeps punctuation readable.",
    "Zero width sample ten finishes the explicit zero width set.",
]
HOMOGLYPH_SENTENCES = [
    "Payment codes must stay readable in every report.",
    "Copy the roadmap once the release note is final.",
    "A concise summary prevents support confusion.",
    "Verify every example before the client review.",
    "Daily status posts should avoid noisy wording.",
]
BIDI_SENTENCES = [
    "Bidi sample one keeps the phrase visually confusing.",
    "Bidi sample two inserts direction controls mid sentence.",
    "Bidi sample three tests isolate marks around words.",
    "Bidi sample four checks override characters in text.",
    "Bidi sample five closes the direction control set.",
]
HTML_TEXT_SAMPLES = [
    ("Plan&#8203; ahead before launch.", "Plan ahead before launch."),
    ("Visible<span style=\"display:none\">hidden</span> note.", "Visible note."),
    ("A&nbsp;B&#xfeff;C", "A B C"),
    ("<span hidden>ghost</span>Budget update.", "Budget update."),
    ("Keep&#x200d; moving<span style=\"font-size:0\">skip</span> forward.", "Keep moving forward."),
]
OTHER_AI_SENTENCES = [
    ("Gemini", "Gemini draft: The sample includes an invisible separator for testing."),
    ("Copilot", "Copilot note: The issue summary should remain easy to read."),
    ("DeepSeek", "DeepSeek memo: A silent marker should disappear after cleanup."),
    ("Perplexity", "Perplexity brief: Metadata and text traces need separate checks."),
    ("Poe", "Poe reply: Reports should show both pass rate and evidence."),
]


def ensure_dirs() -> None:
    for path in (TEXT_DIR, FILE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def make_png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def insert_png_chunk(png_bytes: bytes, chunk_type: bytes, payload: bytes) -> bytes:
    if not png_bytes.startswith(PNG_SIG):
        raise ValueError("not a png")
    pos = 8
    while pos + 8 <= len(png_bytes):
        length = struct.unpack(">I", png_bytes[pos:pos+4])[0]
        ctype = png_bytes[pos+4:pos+8]
        end = pos + 8 + length + 4
        if ctype == b"IHDR":
            return png_bytes[:end] + make_png_chunk(chunk_type, payload) + png_bytes[end:]
        pos = end
    raise ValueError("IHDR not found")


def create_base_image(label: str, size: tuple[int, int] = (512, 512)) -> Image.Image:
    image = Image.new("RGB", size, (244, 247, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, size[0]-24, size[1]-24), fill=(228, 235, 255), outline=(94, 114, 228), width=6)
    draw.rectangle((60, 90, size[0]-60, size[1]-120), fill=(255, 255, 255), outline=(186, 198, 255), width=4)
    draw.text((80, 140), "Batch Test Sample", fill=(48, 62, 128))
    draw.text((80, 210), label[:36], fill=(76, 86, 122))
    draw.text((80, 280), "Owned content for watermark-cleaning QA", fill=(76, 86, 122))
    return image


def save_jpeg(image: Image.Image, path: Path, exif_bytes: bytes | None = None) -> None:
    if exif_bytes:
        image.save(path, format="JPEG", quality=95, exif=exif_bytes)
    else:
        image.save(path, format="JPEG", quality=95)


def save_png(image: Image.Image, path: Path, pnginfo: PngImagePlugin.PngInfo | None = None) -> None:
    image.save(path, format="PNG", pnginfo=pnginfo)


def exif_bytes(vendor: str, prompt: str) -> bytes:
    return piexif.dump(
        {
            "0th": {
                piexif.ImageIFD.ImageDescription: f"Generated by {vendor} | {prompt}".encode("utf-8"),
                piexif.ImageIFD.Artist: vendor.encode("utf-8"),
                piexif.ImageIFD.Software: f"{vendor} Studio AIGC".encode("utf-8"),
            },
            "Exif": {
                piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(
                    f"Prompt: {prompt}; marker: AI generated by {vendor}", encoding="unicode"
                )
            },
        }
    )


def save_png_with_exif(path: Path, vendor: str, prompt: str) -> None:
    base = io.BytesIO()
    create_base_image(vendor).save(base, format="PNG")
    raw = insert_png_chunk(base.getvalue(), b"eXIf", exif_bytes(vendor, prompt))
    path.write_bytes(raw)


def save_png_with_c2pa(path: Path, vendor: str) -> None:
    base = io.BytesIO()
    create_base_image(f"{vendor} C2PA").save(base, format="PNG")
    payload = f"c2pa contentcredentials manifest for {vendor} sample".encode("utf-8")
    raw = insert_png_chunk(base.getvalue(), b"caBX", payload)
    path.write_bytes(raw)


def save_png_with_text_chunk(path: Path, vendor: str, index: int) -> None:
    pnginfo = PngImagePlugin.PngInfo()
    if index % 2 == 0:
        pnginfo.add_text("Comment", f"Generated by {vendor}; digitalSourceType=trainedAlgorithmicMedia")
    else:
        pnginfo.add_itxt("parameters", f"{vendor} workflow; prompt=night skyline; AIGC=1")
    save_png(create_base_image(f"{vendor} text"), path, pnginfo=pnginfo)


def inject_xmp_into_jpeg(jpeg_bytes: bytes, xmp_xml: str) -> bytes:
    header = b"http://ns.adobe.com/xap/1.0/\x00"
    payload = header + xmp_xml.encode("utf-8")
    segment = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    if not jpeg_bytes.startswith(b"\xff\xd8"):
        raise ValueError("not a jpeg")
    return jpeg_bytes[:2] + segment + jpeg_bytes[2:]


def save_jpeg_with_xmp(path: Path, vendor: str, prompt: str) -> None:
    temp = io.BytesIO()
    create_base_image(vendor).save(temp, format="JPEG", quality=95)
    xml = (
        "<?xpacket begin='\ufeff'?>"
        "<x:xmpmeta xmlns:x='adobe:ns:meta/'>"
        "<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>"
        "<rdf:Description xmlns:xmp='http://ns.adobe.com/xap/1.0/' xmlns:c2pa='https://c2pa.org/ns/' "
        "xmlns:stRef='http://ns.adobe.com/xap/1.0/sType/ResourceRef#'>"
        f"<xmp:CreatorTool>{vendor}</xmp:CreatorTool>"
        f"<xmp:Label>Generated by {vendor}</xmp:Label>"
        "<c2pa:digitalSourceType>trainedAlgorithmicMedia</c2pa:digitalSourceType>"
        f"<stRef:documentID>{prompt}</stRef:documentID>"
        "</rdf:Description></rdf:RDF></x:xmpmeta>"
        "<?xpacket end='w'?>"
    )
    path.write_bytes(inject_xmp_into_jpeg(temp.getvalue(), xml))


def save_pdf_with_metadata(path: Path, vendor: str, prompt: str, index: int) -> None:
    packet = io.BytesIO()
    pdf = canvas.Canvas(packet, pagesize=letter)
    pdf.setTitle(f"{vendor} report {index}")
    pdf.setAuthor(vendor)
    pdf.setSubject("AI generated sample with hidden metadata")
    pdf.setCreator(f"{vendor} document pipeline")
    pdf.setKeywords(f"AIGC, trainedAlgorithmicMedia, {prompt}")
    pdf.drawString(72, 720, f"PDF metadata sample {index}")
    pdf.drawString(72, 690, "This file is used for end-to-end watermark-cleaning QA.")
    pdf.drawString(72, 660, f"Source vendor marker: {vendor}")
    pdf.save()
    path.write_bytes(packet.getvalue())


def inject_markers(text: str, markers: list[str]) -> str:
    parts = text.split(" ")
    out: list[str] = []
    for idx, part in enumerate(parts):
        out.append(part)
        if idx < len(parts) - 1:
            out.append(markers[idx % len(markers)])
            out.append(" ")
    return "".join(out)


def insert_marker_inside_words(text: str, marker: str) -> str:
    return re.sub(r"([A-Za-z])([A-Za-z])", rf"\1{marker}\2", text, count=3)


def homoglyphize(text: str) -> str:
    result = []
    used = 0
    for char in text:
        lower = char.lower()
        if lower in HOMOGLYPH_MAP and used < 6:
            repl = HOMOGLYPH_MAP[lower]
            if char.isupper():
                repl = repl.upper()
            result.append(repl)
            used += 1
        else:
            result.append(char)
    return "".join(result)


def html_expected(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"<span[^>]*display\s*:\s*none[^>]*>.*?</span>", "", text, flags=re.I | re.S)
    text = re.sub(r"<span[^>]*font-size\s*:\s*0[^>]*>.*?</span>", "", text, flags=re.I | re.S)
    text = re.sub(r"<span[^>]*hidden[^>]*>.*?</span>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "").replace("\u2060", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def write_text_sample(sample_id: str, category: str, source: str, raw_text: str, expected_text: str, description: str, markers: list[str]) -> dict:
    path = TEXT_DIR / f"{sample_id}.txt"
    path.write_text(raw_text, encoding="utf-8")
    return {
        "id": sample_id,
        "kind": "text",
        "category": category,
        "source": source,
        "input_path": str(path.relative_to(ROOT)),
        "description": description,
        "markers": markers,
        "expected_text": expected_text,
    }


def verify_generated_image(path: Path, expect_c2pa: bool = False) -> None:
    report = inspect_image(path)
    if not report.has_ai_metadata and not report.has_c2pa:
        raise RuntimeError(f"image sample did not contain detectable metadata: {path}")
    if expect_c2pa and not report.has_c2pa:
        raise RuntimeError(f"image sample missing expected C2PA marker: {path}")


def verify_generated_container(path: Path) -> None:
    report = inspect_container(path)
    if not report.has_ai_metadata and not report.has_c2pa:
        raise RuntimeError(f"container sample did not contain detectable metadata: {path}")


def generate_text_samples(samples: list[dict]) -> None:
    for idx, text in enumerate(CLAUDE_SENTENCES, start=1):
        markers = [ZERO_WIDTH_MARKERS[idx % len(ZERO_WIDTH_MARKERS)], TAG_MARKERS[idx % len(TAG_MARKERS)]]
        raw = inject_markers(text, markers)
        samples.append(write_text_sample(
            f"txt_claude_{idx:03d}",
            "claude_hidden_unicode",
            "Claude",
            raw,
            text,
            "Claude-style copied output with zero-width and tag characters embedded between words.",
            markers,
        ))

    for idx, text in enumerate(GPT_SENTENCES, start=1):
        markers = [ZERO_WIDTH_MARKERS[(idx + 1) % len(ZERO_WIDTH_MARKERS)], BIDI_MARKERS[idx % len(BIDI_MARKERS)]]
        raw = inject_markers(text, markers)
        samples.append(write_text_sample(
            f"txt_gpt_{idx:03d}",
            "gpt_hidden_unicode",
            "GPT / OpenAI",
            raw,
            text,
            "GPT/OpenAI-style copied output with invisible Unicode and direction marks mixed into plain text.",
            markers,
        ))

    for idx, text in enumerate(ZERO_WIDTH_SENTENCES, start=1):
        marker = ZERO_WIDTH_MARKERS[(idx - 1) % len(ZERO_WIDTH_MARKERS)]
        raw = insert_marker_inside_words(text, marker)
        samples.append(write_text_sample(
            f"txt_zw_{idx:03d}",
            "zero_width_characters",
            "Programmatic zero-width sample",
            raw,
            text,
            "Direct zero-width character injection inside visible words.",
            [marker],
        ))

    for idx, text in enumerate(HOMOGLYPH_SENTENCES, start=1):
        raw = homoglyphize(text)
        samples.append(write_text_sample(
            f"txt_homoglyph_{idx:03d}",
            "homoglyph_substitution",
            "Programmatic homoglyph sample",
            raw,
            text,
            "Latin letters replaced with Cyrillic lookalikes that should normalize back to the original sentence.",
            ["cyrillic confusables"],
        ))

    for idx, text in enumerate(BIDI_SENTENCES, start=1):
        marker = BIDI_MARKERS[(idx - 1) % len(BIDI_MARKERS)]
        raw = insert_marker_inside_words(text, marker)
        samples.append(write_text_sample(
            f"txt_bidi_{idx:03d}",
            "bidi_control_characters",
            "Programmatic bidi sample",
            raw,
            text,
            "Unicode direction-control characters inserted into normal prose.",
            [marker],
        ))

    for idx, (raw, expected) in enumerate(HTML_TEXT_SAMPLES, start=1):
        samples.append(write_text_sample(
            f"txt_html_{idx:03d}",
            "html_entity_or_hidden_span",
            "HTML entity / hidden span sample",
            raw,
            html_expected(expected if "<" in expected else raw),
            "Literal HTML entity or hidden-span injection that should reduce to visible text only.",
            ["html-entity-or-hidden-span"],
        ))

    for idx, (source, text) in enumerate(OTHER_AI_SENTENCES, start=1):
        marker = TAG_MARKERS[(idx - 1) % len(TAG_MARKERS)] if idx % 2 else ZERO_WIDTH_MARKERS[idx % len(ZERO_WIDTH_MARKERS)]
        raw = inject_markers(text, [marker])
        samples.append(write_text_sample(
            f"txt_other_{idx:03d}",
            "other_ai_tool_text",
            source,
            raw,
            text,
            f"{source} sample with invisible tag or zero-width markers.",
            [marker],
        ))


def generate_file_samples(samples: list[dict]) -> None:
    exif_vendors = [
        ("Midjourney", "cinematic mountain lake"),
        ("DALL-E", "orange cat astronaut"),
        ("Stable Diffusion", "retro city skyline"),
        ("Adobe Firefly", "paper collage bird"),
        ("Flux", "neon alley at dusk"),
        ("Midjourney", "glass library"),
        ("DALL-E", "blue whale mural"),
        ("Stable Diffusion", "botanical study"),
        ("Adobe Firefly", "sunlit kitchen"),
        ("Flux", "quiet train platform"),
    ]
    for idx, (vendor, prompt) in enumerate(exif_vendors, start=1):
        if idx <= 5:
            path = FILE_DIR / f"img_exif_{idx:03d}.jpg"
            save_jpeg(create_base_image(vendor), path, exif_bytes(vendor, prompt))
        else:
            path = FILE_DIR / f"img_exif_{idx:03d}.png"
            save_png_with_exif(path, vendor, prompt)
        verify_generated_image(path)
        samples.append({
            "id": f"img_exif_{idx:03d}",
            "kind": "file",
            "category": "image_exif_watermark",
            "source": vendor,
            "input_path": str(path.relative_to(ROOT)),
            "description": f"Image with EXIF/eXIf metadata referencing {vendor} and an AI-generation prompt.",
            "expected_verification": "image_no_ai_metadata",
        })

    c2pa_vendors = ["OpenAI", "Adobe", "Midjourney", "Gemini", "Claude"]
    for idx, vendor in enumerate(c2pa_vendors, start=1):
        path = FILE_DIR / f"png_c2pa_{idx:03d}.png"
        save_png_with_c2pa(path, vendor)
        verify_generated_image(path, expect_c2pa=True)
        samples.append({
            "id": f"png_c2pa_{idx:03d}",
            "kind": "file",
            "category": "png_c2pa_chunk",
            "source": vendor,
            "input_path": str(path.relative_to(ROOT)),
            "description": "PNG with a private C2PA-style chunk containing content-credentials markers.",
            "expected_verification": "image_no_c2pa_or_ai_metadata",
        })

    text_chunk_vendors = ["Stable Diffusion", "ComfyUI", "InvokeAI", "Fooocus", "Automatic1111"]
    for idx, vendor in enumerate(text_chunk_vendors, start=1):
        path = FILE_DIR / f"png_text_{idx:03d}.png"
        save_png_with_text_chunk(path, vendor, idx)
        verify_generated_image(path)
        samples.append({
            "id": f"png_text_{idx:03d}",
            "kind": "file",
            "category": "png_custom_text_chunks",
            "source": vendor,
            "input_path": str(path.relative_to(ROOT)),
            "description": "PNG with tEXt/iTXt chunks that expose AI-generator metadata.",
            "expected_verification": "image_no_ai_metadata",
        })

    xmp_vendors = ["DALL-E", "Midjourney", "Stable Diffusion", "OpenAI", "Gemini"]
    for idx, vendor in enumerate(xmp_vendors, start=1):
        path = FILE_DIR / f"jpg_xmp_{idx:03d}.jpg"
        save_jpeg_with_xmp(path, vendor, f"xmp sample {idx}")
        verify_generated_image(path)
        samples.append({
            "id": f"jpg_xmp_{idx:03d}",
            "kind": "file",
            "category": "jpg_xmp_watermark",
            "source": vendor,
            "input_path": str(path.relative_to(ROOT)),
            "description": "JPEG with an injected APP1 XMP packet carrying AI provenance hints.",
            "expected_verification": "image_no_ai_metadata",
        })

    pdf_vendors = ["Claude", "ChatGPT", "Gemini", "Midjourney", "Stable Diffusion"]
    for idx, vendor in enumerate(pdf_vendors, start=1):
        path = FILE_DIR / f"pdf_meta_{idx:03d}.pdf"
        save_pdf_with_metadata(path, vendor, f"pdf sample {idx}", idx)
        verify_generated_container(path)
        samples.append({
            "id": f"pdf_meta_{idx:03d}",
            "kind": "file",
            "category": "pdf_hidden_metadata",
            "source": vendor,
            "input_path": str(path.relative_to(ROOT)),
            "description": "PDF with author/creator/keyword metadata that signals AI generation.",
            "expected_verification": "pdf_no_ai_metadata",
        })


def main() -> int:
    ensure_dirs()
    samples: list[dict] = []
    generate_text_samples(samples)
    generate_file_samples(samples)

    summary: dict[str, int] = {}
    for sample in samples:
        summary[sample["category"]] = summary.get(sample["category"], 0) + 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "samples_root": str(SAMPLES_ROOT.relative_to(ROOT)),
        "total_samples": len(samples),
        "category_counts": summary,
        "samples": samples,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST_PATH.relative_to(ROOT)), "total_samples": len(samples), "category_counts": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
