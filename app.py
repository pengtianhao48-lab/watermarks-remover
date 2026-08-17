from __future__ import annotations

import json
from html import escape as html_escape
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.sax.saxutils import escape

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "service" / "scripts"
STATIC = ROOT / "static"
sys.path.insert(0, str(SCRIPTS))

from synthid_text import detect_synthid_likelihood, neutralize_synthid_text  # noqa: E402

MAX_UPLOAD_BYTES = 32 * 1024 * 1024
OUTPUT_RETENTION_SECONDS = 10 * 60
OUTPUTS = Path(tempfile.gettempdir()) / "watermarks-remover-outputs"
SITE_URL = "https://watermarks-remover-production.up.railway.app"
BRAND_NAME = "AI Watermarks Remover"
ASSET_VERSION = "20260817-2340"
HTML_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}
OUTPUTS.mkdir(parents=True, exist_ok=True)

LOCALES = {
    "en": ("Watermarks Remover", "Remove AI watermarks, C2PA metadata, EXIF/XMP traces, invisible Unicode marks, and document provenance from files you own."),
    "zh": ("水印清除工具", "清除你拥有文件中的 AI 水印、C2PA 元数据、EXIF/XMP 电子痕迹、隐藏 Unicode 标记和文档来源信息。"),
    "es": ("Eliminador de marcas de agua", "Elimina marcas de agua de IA, metadatos C2PA, rastros EXIF/XMP, Unicode invisible y procedencia documental."),
    "hi": ("वॉटरमार्क रिमूवर", "अपनी फ़ाइलों से AI वॉटरमार्क, C2PA मेटाडेटा, EXIF/XMP निशान, अदृश्य Unicode और दस्तावेज़ स्रोत हटाएँ।"),
    "ar": ("مزيل العلامات المائية", "أزل علامات الذكاء الاصطناعي وبيانات C2PA وEXIF/XMP وآثار Unicode غير المرئية من ملفاتك."),
    "fr": ("Suppresseur de filigranes", "Supprimez les filigranes IA, métadonnées C2PA, traces EXIF/XMP, Unicode invisible et provenance documentaire."),
    "de": ("Wasserzeichen-Entferner", "Entfernen Sie KI-Wasserzeichen, C2PA-Metadaten, EXIF/XMP-Spuren, unsichtbares Unicode und Dokumentherkunft."),
    "ja": ("ウォーターマークリムーバー", "所有ファイルから AI 透かし、C2PA メタデータ、EXIF/XMP 痕跡、不可視 Unicode、文書来歴を削除します。"),
    "ko": ("워터마크 제거기", "소유한 파일에서 AI 워터마크, C2PA 메타데이터, EXIF/XMP 흔적, 보이지 않는 Unicode, 문서 출처 정보를 제거합니다."),
}
RTL_LOCALES = {"ar"}

BRAND_LOCAL_NAMES = {
    "en": "AI Watermarks Remover",
    "zh": "AI 水印移除",
    "es": "AI Watermarks Remover",
    "hi": "AI Watermarks Remover",
    "ar": "AI Watermarks Remover",
    "fr": "AI Watermarks Remover",
    "de": "AI Watermarks Remover",
    "ja": "AI Watermarks Remover",
    "ko": "AI Watermarks Remover",
}

# Brand-first titles per locale. All start with the localized brand name.
SITE_TITLES = {
    "en": "AI Watermarks Remover — Remove Claude Watermarks, C2PA & Metadata",
    "zh": "AI 水印移除 — 清除 Claude 电子水印、C2PA 与元数据",
    "hi": "AI Watermarks Remover — Claude वॉटरमार्क, C2PA और मेटाडेटा हटाएँ",
    "es": "AI Watermarks Remover — Elimina marcas de Claude, C2PA y metadatos",
    "fr": "AI Watermarks Remover — Supprimer filigranes Claude, C2PA et métadonnées",
    "ar": "AI Watermarks Remover — إزالة علامات Claude المائية وC2PA والبيانات الوصفية",
    "de": "AI Watermarks Remover — Claude-Wasserzeichen, C2PA und Metadaten entfernen",
    "ja": "AI Watermarks Remover — Claude 透かし、C2PA、メタデータを削除",
    "ko": "AI Watermarks Remover — Claude 워터마크, C2PA, 메타데이터 제거",
}

HOWTO_STEPS = {
    "en": [
        ("Upload or paste content", "Choose a file (text, image, PDF, DOCX, ODT) up to 32 MB or paste text into the box."),
        ("Scan for watermarks and metadata traces", "The tool inspects your content for visible watermarks, hidden Unicode, C2PA credentials, EXIF/XMP metadata and document traces."),
        ("Clean supported traces and download", "Remove the traces we support and download the cleaned file — everything is deleted from our server within 10 minutes."),
    ],
    "zh": [
        ("上传或粘贴内容", "选择一个不超过 32 MB 的文件（文本、图片、PDF、DOCX、ODT），或直接把文本粘贴到输入框。"),
        ("扫描水印", "工具会检查内容里的可见水印、隐藏 Unicode、C2PA 凭证、EXIF/XMP 元数据和文档痕迹。"),
        ("下载清理后的文件", "清理支持的痕迹并下载已清理的文件；服务器端会在 10 分钟内自动删除。"),
    ],
    "hi": [
        ("सामग्री अपलोड करें या पेस्ट करें", "32 MB तक की फ़ाइल (टेक्स्ट, इमेज, PDF, DOCX, ODT) चुनें या टेक्स्ट पेस्ट करें।"),
        ("वॉटरमार्क और मेटाडेटा निशान स्कैन करें", "टूल visible watermarks, hidden Unicode, C2PA credentials, EXIF/XMP metadata और document traces की जाँच करता है।"),
        ("साफ़ फ़ाइल डाउनलोड करें", "समर्थित निशान हटाकर साफ़ फ़ाइल डाउनलोड करें — 10 मिनट के भीतर सर्वर से हट जाती है।"),
    ],
    "es": [
        ("Sube o pega el contenido", "Elige un archivo (texto, imagen, PDF, DOCX, ODT) de hasta 32 MB o pega el texto."),
        ("Escanea marcas de agua y metadatos", "La herramienta revisa marcas visibles, Unicode oculto, credenciales C2PA, EXIF/XMP y rastros del documento."),
        ("Descarga el archivo limpio", "Elimina los rastros compatibles y descarga el archivo limpio; se borra del servidor en 10 minutos."),
    ],
    "fr": [
        ("Importer ou coller le contenu", "Choisissez un fichier (texte, image, PDF, DOCX, ODT) jusqu’à 32 Mo ou collez du texte."),
        ("Analyser filigranes et métadonnées", "L’outil vérifie les filigranes visibles, l’Unicode caché, les identifiants C2PA, les métadonnées EXIF/XMP et les traces documentaires."),
        ("Télécharger le fichier nettoyé", "Supprimez les traces prises en charge et téléchargez le fichier nettoyé ; supprimé du serveur en 10 minutes."),
    ],
    "de": [
        ("Inhalt hochladen oder einfügen", "Wählen Sie eine Datei (Text, Bild, PDF, DOCX, ODT) bis 32 MB oder fügen Sie Text ein."),
        ("Wasserzeichen und Metadaten prüfen", "Das Tool prüft sichtbare Wasserzeichen, verstecktes Unicode, C2PA-Credentials, EXIF/XMP-Metadaten und Dokumentspuren."),
        ("Bereinigte Datei herunterladen", "Unterstützte Spuren werden entfernt; die Datei wird innerhalb von 10 Minuten vom Server gelöscht."),
    ],
    "ar": [
        ("ارفع أو الصق المحتوى", "اختر ملفاً (نص، صورة، PDF، DOCX، ODT) بحجم أقصاه 32 م.ب أو الصق النص."),
        ("افحص العلامات والبيانات الوصفية", "تفحص الأداة العلامات المرئية، وUnicode المخفي، وشهادات C2PA، وبيانات EXIF/XMP، وآثار المستندات."),
        ("نزّل الملف النظيف", "أزل الآثار المدعومة ونزّل الملف النظيف؛ يُحذف من الخادم خلال 10 دقائق."),
    ],
    "ja": [
        ("ファイルをアップロードまたはテキストを貼り付け", "テキスト、画像、PDF、DOCX、ODT（最大 32 MB）を選ぶか、テキストを貼り付けます。"),
        ("透かしとメタデータの痕跡をスキャン", "可視透かし、不可視 Unicode、C2PA、EXIF/XMP メタデータ、文書痕跡を検査します。"),
        ("削除済みファイルをダウンロード", "対応する痕跡を削除し、削除後のファイルを保存できます。サーバー上のファイルは 10 分以内に削除されます。"),
    ],
    "ko": [
        ("파일을 업로드하거나 텍스트를 붙여넣기", "텍스트, 이미지, PDF, DOCX, ODT(최대 32MB) 파일을 선택하거나 텍스트를 붙여넣습니다."),
        ("워터마크와 메타데이터 흔적 검사", "보이는 워터마크, 숨은 Unicode, C2PA, EXIF/XMP 메타데이터, 문서 흔적을 검사합니다."),
        ("정리된 파일 다운로드", "지원되는 흔적을 제거하고 정리된 파일을 다운로드합니다. 서버의 파일은 10분 이내 삭제됩니다."),
    ],
}

SEO_SUFFIXES = {
    "en": "Claude Watermark Remover, C2PA & Metadata Cleaner",
    "zh": "Claude 水印移除、C2PA 元数据清理",
    "ja": "Claude 透かし削除・C2PA メタデータ削除",
    "ko": "Claude 워터마크 제거, C2PA 메타데이터 정리",
    "es": "quitar marca de agua Claude, C2PA y metadatos",
    "fr": "supprimer filigrane Claude, C2PA et métadonnées",
    "de": "Claude Wasserzeichen entfernen, C2PA & Metadaten löschen",
    "pt": "remover marca d'água Claude, C2PA e metadados",
    "hi": "Claude watermark remover, C2PA metadata cleaner",
    "ar": "إزالة علامة Claude المائية وتنظيف C2PA والبيانات الوصفية",
}

SEO_DESCRIPTIONS = {
    "en": "Remove visible watermarks, Claude and ChatGPT hidden Unicode marks, C2PA Content Credentials, EXIF/XMP metadata, and document traces from files you own. Free online cleaner with check-first report.",
    "zh": "在线清理你拥有文件中的可见水印、Claude/ChatGPT 隐藏 Unicode、C2PA 内容凭证、EXIF/XMP 元数据和文档痕迹，并先检查再下载。",
    "ja": "所有ファイルの可視透かし、Claude/ChatGPT の不可視 Unicode、C2PA Content Credentials、EXIF/XMP メタデータ、文書痕跡をオンラインで確認・削除します。",
    "ko": "소유한 파일의 보이는 워터마크, Claude/ChatGPT 숨은 Unicode, C2PA Content Credentials, EXIF/XMP 메타데이터와 문서 흔적을 온라인으로 확인하고 정리합니다.",
    "es": "Quita marcas visibles, Unicode oculto de Claude/ChatGPT, credenciales C2PA, metadatos EXIF/XMP y rastros de documentos de archivos propios, con informe previo.",
    "fr": "Supprimez les filigranes visibles, Unicode caché Claude/ChatGPT, Content Credentials C2PA, métadonnées EXIF/XMP et traces de documents sur vos fichiers.",
    "de": "Entfernen Sie sichtbare Wasserzeichen, verstecktes Claude/ChatGPT-Unicode, C2PA Content Credentials, EXIF/XMP-Metadaten und Dokumentspuren aus eigenen Dateien.",
    "pt": "Remova marcas visíveis, Unicode oculto do Claude/ChatGPT, credenciais C2PA, metadados EXIF/XMP e rastros de documentos de arquivos próprios.",
    "hi": "अपने फ़ाइलों से visible watermarks, Claude/ChatGPT hidden Unicode, C2PA Content Credentials, EXIF/XMP metadata और document traces ऑनलाइन साफ़ करें।",
    "ar": "نظّف ملفاتك من العلامات المرئية وUnicode المخفي من Claude/ChatGPT وبيانات C2PA وEXIF/XMP وآثار المستندات مع تقرير واضح.",
}

SEO_KEYWORDS = {
    "en": "watermark remover, AI watermark remover, Claude watermark remover, ChatGPT watermark remover, remove hidden AI watermarks, zero-width character remover, invisible Unicode remover, C2PA metadata remover, Content Credentials remover, EXIF XMP metadata cleaner, document metadata remover",
    "zh": "水印移除, 去水印, AI 水印移除, Claude 水印移除, ChatGPT 水印移除, 隐藏 Unicode 清理, 零宽字符移除, C2PA 元数据清理, 内容凭证移除, EXIF XMP 元数据清理, 文档元数据清理",
    "ja": "透かし削除, AI 透かし削除, Claude 透かし削除, ChatGPT 透かし削除, 不可視 Unicode 削除, ゼロ幅文字 削除, C2PA メタデータ 削除, EXIF XMP 削除",
    "ko": "워터마크 제거, AI 워터마크 제거, Claude 워터마크 제거, ChatGPT 워터마크 제거, 보이지 않는 Unicode 제거, 제로폭 문자 제거, C2PA 메타데이터 제거, EXIF XMP 정리",
    "es": "quitar marca de agua, eliminador de marcas de agua IA, quitar marca de agua Claude, eliminar Unicode invisible, eliminar caracteres de ancho cero, eliminar metadatos C2PA, limpiar EXIF XMP",
    "fr": "supprimer filigrane, suppresseur de filigrane IA, supprimer filigrane Claude, supprimer Unicode invisible, supprimer caractères zéro largeur, supprimer métadonnées C2PA, nettoyer EXIF XMP",
    "de": "Wasserzeichen entfernen, KI Wasserzeichen entfernen, Claude Wasserzeichen entfernen, unsichtbares Unicode entfernen, Zero Width Zeichen entfernen, C2PA Metadaten entfernen, EXIF XMP löschen",
    "pt": "remover marca d'água, removedor de marca d'água IA, remover marca Claude, remover Unicode invisível, remover caracteres zero-width, remover metadados C2PA, limpar EXIF XMP",
    "hi": "watermark remover, AI watermark remover, Claude watermark remover, ChatGPT watermark remover, hidden Unicode remover, zero-width character remover, C2PA metadata remover, EXIF XMP cleaner",
    "ar": "إزالة العلامة المائية, مزيل علامات AI المائية, إزالة علامة Claude المائية, إزالة Unicode المخفي, إزالة أحرف zero-width, إزالة بيانات C2PA, تنظيف EXIF XMP",
}

SEO_COPY = {
    "en": ("Remove AI watermarks, metadata and hidden traces online", "Use AI Watermarks Remover when you need a fast check-first workflow for owned files: visible watermark cleanup, Claude or ChatGPT hidden Unicode cleanup, C2PA Content Credentials and EXIF/XMP metadata stripping, and document trace cleaning. The tool reports what it found before you download the cleaned file."),
    "zh": ("在线移除 AI 水印、元数据和隐藏痕迹", "当你需要处理自己拥有的文件时，可以用 AI Watermarks Remover 先检查再清理：包括可见水印、Claude 或 ChatGPT 复制文本里的隐藏 Unicode、C2PA 内容凭证、EXIF/XMP 元数据，以及 PDF/DOCX 等文档痕迹。清理后会显示发现和处理了什么。"),
    "ja": ("AI 透かし、メタデータ、隠れた痕跡をオンラインで削除", "所有しているファイルを先に確認し、可視透かし、Claude/ChatGPT の不可視 Unicode、C2PA Content Credentials、EXIF/XMP メタデータ、文書の痕跡を削除できます。"),
    "ko": ("AI 워터마크, 메타데이터, 숨은 흔적 온라인 정리", "소유한 파일을 먼저 검사한 뒤 보이는 워터마크, Claude/ChatGPT 숨은 Unicode, C2PA Content Credentials, EXIF/XMP 메타데이터와 문서 흔적을 정리합니다."),
    "es": ("Eliminar marcas de agua IA, metadatos y rastros ocultos", "Revisa y limpia archivos propios: marcas visibles, Unicode oculto de Claude o ChatGPT, Content Credentials C2PA, metadatos EXIF/XMP y rastros de documentos."),
    "fr": ("Supprimer filigranes IA, métadonnées et traces cachées", "Vérifiez puis nettoyez vos fichiers : filigranes visibles, Unicode caché Claude/ChatGPT, Content Credentials C2PA, métadonnées EXIF/XMP et traces documentaires."),
    "de": ("KI-Wasserzeichen, Metadaten und versteckte Spuren online entfernen", "Prüfen und bereinigen Sie eigene Dateien: sichtbare Wasserzeichen, verstecktes Claude/ChatGPT-Unicode, C2PA Content Credentials, EXIF/XMP-Metadaten und Dokumentspuren."),
    "pt": ("Remover marcas d'água de IA, metadados e rastros ocultos", "Verifique e limpe arquivos próprios: marcas visíveis, Unicode oculto do Claude/ChatGPT, credenciais C2PA, metadados EXIF/XMP e rastros de documentos."),
    "hi": ("AI watermarks, metadata और hidden traces ऑनलाइन हटाएँ", "अपनी फ़ाइलों को पहले जाँचें, फिर visible watermarks, Claude/ChatGPT hidden Unicode, C2PA Content Credentials, EXIF/XMP metadata और document traces साफ़ करें।"),
    "ar": ("إزالة علامات AI المائية والبيانات الوصفية والآثار المخفية", "افحص ملفاتك أولاً ثم نظّف العلامات المرئية وUnicode المخفي من Claude/ChatGPT وبيانات C2PA وEXIF/XMP وآثار المستندات."),
}

SEO_POINTS = {
    "en": ["Claude watermark remover for zero-width and invisible Unicode text", "C2PA Content Credentials, EXIF and XMP metadata cleaner", "PDF, DOCX, ODT, image and text trace report before download"],
    "zh": ["Claude 水印移除：清理零宽字符和隐藏 Unicode", "C2PA 内容凭证、EXIF、XMP 元数据清理", "PDF、DOCX、ODT、图片和文本先检查再下载"],
    "ja": ["Claude 透かし削除：ゼロ幅文字と不可視 Unicode を処理", "C2PA Content Credentials、EXIF、XMP メタデータを削除", "PDF、DOCX、ODT、画像、テキストをダウンロード前に確認"],
    "ko": ["Claude 워터마크 제거: 제로폭 문자와 숨은 Unicode 정리", "C2PA Content Credentials, EXIF, XMP 메타데이터 정리", "PDF, DOCX, ODT, 이미지, 텍스트를 다운로드 전 검사"],
}

FAQS = {
    "en": [
        ("Can this remove Claude watermarks?", "It can clean character-based Claude traces such as zero-width characters and invisible Unicode. It does not promise to defeat statistical or model-level watermarks."),
        ("Does it remove ChatGPT or OpenAI image metadata?", "It strips supported C2PA Content Credentials, EXIF/XMP metadata and other file traces when they are present in files you own."),
        ("Can it remove Gemini or SynthID watermarks?", "It can remove ordinary metadata and visible traces, but no public tool can guarantee surgical removal of SynthID or secret model-level signals."),
        ("What files are supported?", "Text, Markdown, HTML, PNG, JPG, SVG, PDF, DOCX and ODT files up to 32 MB are supported."),
    ],
    "zh": [
        ("这个工具能移除 Claude 水印吗？", "它可以清理基于字符的 Claude 痕迹，例如零宽字符和隐藏 Unicode；但不承诺破解统计学或模型级水印。"),
        ("能移除 ChatGPT/OpenAI 图片里的元数据吗？", "当你拥有的文件中存在 C2PA 内容凭证、EXIF/XMP 元数据或其他文件痕迹时，工具会尽量清理并显示报告。"),
        ("能移除 Gemini 或 SynthID 水印吗？", "它可以清理普通元数据和可见痕迹，但不承诺手术式移除 SynthID 或秘密模型级信号。"),
        ("支持哪些文件？", "支持 txt、md、html、png、jpg、svg、pdf、docx、odt，单文件最大 32 MB。"),
    ],
}

OG_LOCALES = {
    "en": "en_US", "zh": "zh_CN", "ja": "ja_JP", "ko": "ko_KR", "es": "es_ES", "fr": "fr_FR",
    "de": "de_DE", "pt": "pt_PT", "hi": "hi_IN", "ar": "ar_AR", "ru": "ru_RU", "it": "it_IT",
}

app = FastAPI(title=BRAND_NAME, version="1.2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots() -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"


@app.get("/sitemap.xml")
def sitemap() -> Response:
    def locale_url(code: str) -> str:
        return f"{SITE_URL}/" if code == "en" else f"{SITE_URL}/{escape(code)}"

    alternates = [f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/" />']
    alternates.extend(
        f'<xhtml:link rel="alternate" hreflang="{escape(code)}" href="{locale_url(code)}" />'
        for code in LOCALES
    )
    urls = []
    for code in LOCALES:
        priority = "1.0" if code == "en" else "0.9"
        urls.append(
            f"<url><loc>{locale_url(code)}</loc>{''.join(alternates)}<changefreq>weekly</changefreq><priority>{priority}</priority></url>"
        )
    body = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" "
        "xmlns:xhtml=\"http://www.w3.org/1999/xhtml\">"
        + "".join(urls)
        + "</urlset>"
    )
    return Response(body, media_type="application/xml")


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return _render_page("en")


@app.get("/{locale}", response_class=HTMLResponse)
def localized_home(locale: str) -> HTMLResponse:
    if locale not in LOCALES:
        raise HTTPException(status_code=404, detail="Not found")
    return _render_page(locale)


@app.post("/api/inspect")
async def inspect(file: UploadFile = File(...), force_type: str = Form("auto")) -> JSONResponse:
    source = await _save_upload(file)
    try:
        result = _run_script("inspect_file.py", source, force_type=force_type)
        return JSONResponse({"ok": result["returncode"] in (0, 1), "report": _decode_report(result)})
    finally:
        _safe_unlink(source)


@app.post("/api/clean")
async def clean(
    file: UploadFile = File(...),
    force_type: str = Form("auto"),
    nfkc: bool = Form(False),
    aggressive_homoglyphs: bool = Form(False),
    keep_non_ai_metadata: bool = Form(False),
) -> JSONResponse:
    _purge_expired_outputs()
    source = await _save_upload(file)
    job_id = uuid4().hex
    extension = source.suffix or ".cleaned"
    output = OUTPUTS / f"{job_id}{extension}"
    try:
        args = ["clean_file.py", str(source), "-o", str(output), "--json", "--as", force_type]
        if nfkc:
            args.append("--nfkc")
        if aggressive_homoglyphs:
            args.append("--aggressive-homoglyphs")
        if keep_non_ai_metadata:
            args.append("--keep-non-ai-metadata")
        result = _run(args)
        if not output.exists():
            raise HTTPException(status_code=422, detail=_decode_error(result))
        download_name = _clean_download_name(file.filename or "download", output.suffix)
        threading.Timer(OUTPUT_RETENTION_SECONDS, _safe_unlink, args=(output,)).start()
        return JSONResponse(
            {
                "ok": result["returncode"] == 0,
                "download_url": f"/download/{job_id}",
                "download_name": download_name,
                "expires_in_seconds": OUTPUT_RETENTION_SECONDS,
                "report": _decode_report(result),
            }
        )
    finally:
        _safe_unlink(source)


@app.post("/api/clean-text")
async def clean_text(text: str = Form(...), nfkc: bool = Form(False), aggressive_homoglyphs: bool = Form(False)) -> JSONResponse:
    if len(text.encode("utf-8")) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Text is too large")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        handle.write(text)
        source = Path(handle.name)
    output = OUTPUTS / f"{uuid4().hex}.txt"
    try:
        args = ["clean_file.py", str(source), "-o", str(output), "--json", "--as", "text"]
        if nfkc:
            args.append("--nfkc")
        if aggressive_homoglyphs:
            args.append("--aggressive-homoglyphs")
        result = _run(args)
        cleaned = output.read_text(encoding="utf-8", errors="replace") if output.exists() else ""
        return JSONResponse({"ok": result["returncode"] == 0, "cleaned_text": cleaned, "report": _decode_report(result)})
    finally:
        _safe_unlink(source)
        _safe_unlink(output)


@app.post("/detect_synthid")
async def detect_synthid(text: str = Form(...)) -> JSONResponse:
    if len(text.encode("utf-8")) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Text is too large")
    result = detect_synthid_likelihood(text)
    return JSONResponse(result)


@app.post("/neutralize_synthid")
async def neutralize_synthid(text: str = Form(...)) -> JSONResponse:
    if len(text.encode("utf-8")) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Text is too large")
    try:
        result = neutralize_synthid_text(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return JSONResponse({
        "ok": True,
        "text": result["text"],
        "stats": result["stats"],
        "before": result["before"],
        "after": result["after"],
    })


@app.get("/download/{job_id}")
def download(job_id: str, name: str | None = None) -> Response:
    _purge_expired_outputs()
    if not job_id.isalnum() or len(job_id) != 32:
        raise HTTPException(status_code=404, detail="Not found")
    matches = list(OUTPUTS.glob(f"{job_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File expired or not found")
    path = matches[0]
    return FileResponse(path, filename=name or path.name, media_type="application/octet-stream")


async def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "upload.bin").suffix[:16]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        total = 0
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                _safe_unlink(Path(handle.name))
                raise HTTPException(status_code=413, detail="File is larger than 32 MB")
            handle.write(chunk)
        return Path(handle.name)


def _render_page(locale: str) -> HTMLResponse:
    base_title, base_description = LOCALES[locale]
    suffix = SEO_SUFFIXES.get(locale, SEO_SUFFIXES["en"])
    title = SITE_TITLES.get(locale, f"{BRAND_NAME} — {suffix}")
    description = SEO_DESCRIPTIONS.get(locale, base_description)
    keywords = SEO_KEYWORDS.get(locale, SEO_KEYWORDS["en"])
    seo_heading, seo_body = SEO_COPY.get(locale, (base_title, description))
    points = SEO_POINTS.get(locale, ["Claude watermark remover", "C2PA, EXIF and XMP metadata cleaner", "Hidden Unicode and document trace cleaner"])
    faqs = FAQS.get(locale, [])
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    canonical_path = "" if locale == "en" else f"/{locale}"
    canonical_url = f"{SITE_URL}{canonical_path or '/'}"
    hreflangs = [f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/" />']
    hreflangs.extend(
        f'<link rel="alternate" hreflang="{code}" href="{SITE_URL}{"" if code == "en" else f"/{code}"}" />'
        for code in LOCALES
    )
    schema = _schema_json(locale, title, description, canonical_url, keywords, points, faqs)
    faq_html = "".join(
        f"<details><summary>{html_escape(question)}</summary><p>{html_escape(answer)}</p></details>"
        for question, answer in faqs
    )
    point_html = "".join(f"<span>{html_escape(point)}</span>" for point in points)
    replacements = {
        "__LANG__": locale,
        "__DIR__": "rtl" if locale in RTL_LOCALES else "ltr",
        "__TITLE__": html_escape(title, quote=True),
        "__DESCRIPTION__": html_escape(description, quote=True),
        "__KEYWORDS__": html_escape(keywords, quote=True),
        "__CANONICAL__": canonical_url,
        "__OG_LOCALE__": OG_LOCALES.get(locale, locale),
        "__OG_IMAGE__": f"{SITE_URL}/static/og.svg?v={ASSET_VERSION}",
        "__OG_IMAGE_ALT__": html_escape(title, quote=True),
        "__HREFLANGS__": "\n  ".join(hreflangs),
        "__SCHEMA_JSON__": schema,
        "__BRAND_TITLE__": html_escape(base_title),
        "__SUBTITLE__": html_escape(description),
        "__SEO_HEADING__": html_escape(seo_heading),
        "__SEO_BODY__": html_escape(seo_body),
        "__SEO_POINTS__": point_html,
        "__FAQ_HTML__": faq_html,
        "__ASSET_VERSION__": ASSET_VERSION,
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return HTMLResponse(html, headers=HTML_HEADERS)


def _schema_json(locale: str, title: str, description: str, canonical_url: str, keywords: str, points: list[str], faqs: list[tuple[str, str]]) -> str:
    steps = HOWTO_STEPS.get(locale, HOWTO_STEPS["en"])
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebApplication",
            "@id": f"{canonical_url}#app",
            "name": BRAND_NAME,
            "alternateName": BRAND_LOCAL_NAMES.get(locale, LOCALES[locale][0]),
            "url": canonical_url,
            "description": description,
            "inLanguage": locale,
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Web",
            "softwareVersion": ASSET_VERSION,
            "featureList": points,
            "keywords": keywords,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        },
        {
            "@type": "HowTo",
            "@id": f"{canonical_url}#howto",
            "name": title,
            "description": description,
            "inLanguage": locale,
            "step": [
                {
                    "@type": "HowToStep",
                    "position": index + 1,
                    "name": name,
                    "text": text,
                }
                for index, (name, text) in enumerate(steps)
            ],
        },
    ]
    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{canonical_url}#faq",
                "inLanguage": locale,
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faqs
                ],
            }
        )
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def _run_script(script: str, path: Path, force_type: str = "auto") -> dict[str, Any]:
    return _run([script, str(path), "--json", "--as", force_type])


def _run(args: list[str]) -> dict[str, Any]:
    force_type = "auto"
    if "--as" in args:
        type_index = args.index("--as") + 1
        force_type = args[type_index] if type_index < len(args) else "auto"
    if force_type not in {"auto", "text", "image", "container"}:
        raise HTTPException(status_code=400, detail="Invalid file type")
    command = ["python3", str(SCRIPTS / args[0]), *args[1:]]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=45)
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def _decode_report(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("stdout", "").strip()
    if payload:
        try:
            report = json.loads(payload)
        except json.JSONDecodeError:
            report = {"message": payload}
    else:
        report = {}
    if result.get("stderr"):
        report["notes"] = result["stderr"].strip()
    report["exit_code"] = result.get("returncode")
    return report


def _decode_error(result: dict[str, Any]) -> str:
    report = _decode_report(result)
    return report.get("notes") or report.get("message") or "Could not process this file"


def _clean_download_name(filename: str, suffix: str) -> str:
    stem = Path(filename).stem or "cleaned"
    safe_stem = "".join(char for char in stem if char.isalnum() or char in ("-", "_", " ")).strip() or "cleaned"
    return f"{safe_stem}.cleaned{suffix}"


def _purge_expired_outputs() -> None:
    cutoff = time.time() - OUTPUT_RETENTION_SECONDS
    for path in OUTPUTS.glob("*"):
        try:
            if path.stat().st_mtime < cutoff:
                _safe_unlink(path)
        except OSError:
            pass


def _safe_unlink(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    except OSError:
        pass
