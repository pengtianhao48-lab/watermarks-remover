const localeNames = {
  en: 'English', zh: '中文', es: 'Español', hi: 'हिन्दी', ar: 'العربية', fr: 'Français', pt: 'Português', de: 'Deutsch', ja: '日本語', ko: '한국어', ru: 'Русский', id: 'Indonesia', tr: 'Türkçe', vi: 'Tiếng Việt', th: 'ไทย', it: 'Italiano', nl: 'Nederlands', pl: 'Polski', uk: 'Українська', ms: 'Melayu', fa: 'فارسی', ur: 'اردو', bn: 'বাংলা', ta: 'தமிழ்', te: 'తెలుగు', mr: 'मराठी', sw: 'Kiswahili', he: 'עברית', el: 'Ελληνικά', cs: 'Čeština', ro: 'Română', hu: 'Magyar', sv: 'Svenska', da: 'Dansk', fi: 'Suomi', no: 'Norsk'
};

const supportedLocales = Object.keys(localeNames);
const pathLocale = window.location.pathname.split('/').filter(Boolean)[0];
const storedLocale = localStorage.getItem('preferredLocale');
const browserLocale = (navigator.languages || [navigator.language || 'en'])
  .map((value) => value.toLowerCase().split('-')[0])
  .find((value) => supportedLocales.includes(value));
const preferredLocale = supportedLocales.includes(storedLocale) ? storedLocale : (browserLocale || 'en');
if (!pathLocale && preferredLocale !== 'en') {
  window.location.replace(`/${preferredLocale}`);
}

const copy = {
  en: {
    language: 'Language', eyebrow: 'Open. Clean. Download.', brandTitle: 'AI Watermarks Remover', headline: 'Remove watermarks and hidden traces now.', subtitle: 'Removes visible and hidden AI watermarks from Claude, ChatGPT/OpenAI, Gemini and more: text marks, C2PA, EXIF/XMP, invisible Unicode, and document metadata.', targetUnicode: 'Hidden Unicode', targetMetadata: 'Metadata', targetDocs: 'Document traces', fileTab: 'File', textTab: 'Text', chooseFile: 'Choose file', fileHint: 'txt, md, html, png, jpg, svg, pdf, docx, odt · max 32 MB', autoDetect: 'Auto detect file type', asText: 'Text', asImage: 'Image', asDocument: 'Document', nfkc: 'Normalize text', deepClean: 'Deep text clean', keepMetadata: 'Keep safe image metadata', nfkcTip: 'Makes text use standard characters and spacing. Useful when copy/paste looks normal but behaves strangely.', deepCleanTip: 'Removes look-alike letters and hidden text tricks more aggressively. Use if a file still looks suspicious.', keepMetadataTip: 'Keeps ordinary camera/app info when it is not related to AI provenance. Turn off to strip more image metadata.', inspect: 'Check first', cleanDownload: 'Clean watermark', textPlaceholder: 'Paste text here. Invisible Unicode and suspicious spacing will be cleaned instantly.', cleanText: 'Clean text', copyResult: 'Copy result', resultLabel: 'Result', readyTitle: 'Ready to clean', download: 'Download file', stepUpload: 'Upload or paste content', stepScan: 'Scan for watermarks and traces', stepClean: 'Clean supported traces', removedCount: 'Removed', traceTypes: 'Trace types', readyMessage: 'Choose a file or paste text. You will see exactly what was found and removed.', seoTitle: 'Fast watermark and metadata removal for urgent use', seoBody: 'Works in the browser on desktop and mobile. Supports common text, image, web, and document files, with a clear after-action report for AI marks, C2PA, EXIF/XMP, invisible characters, and document metadata.', inspecting: 'Checking file…', cleaning: 'Cleaning file…', cleaningText: 'Cleaning text…', doneTitle: 'Cleaned', checkedTitle: 'Check complete', nothingFound: 'No supported traces were found.', cleanedTextReady: 'Text cleaned and placed back in the box.', copied: 'Copied', downloadReady: 'Cleaned file is ready.', errorTitle: 'Could not process', rawReport: 'Technical report', found: 'Found', cleaned: 'Cleaned', risk: 'Note', fileSelected: 'Selected', cleaningTitle: 'Cleaning…', expiresNotice: 'Download soon: cleaned files are deleted after 10 minutes.'
  },
  zh: {
    language: '语言', eyebrow: '打开 · 清理 · 下载', brandTitle: 'AI 水印移除', headline: '立即清除水印和隐藏痕迹。', subtitle: '支持 Claude、ChatGPT/OpenAI、Gemini 等常见 AI 明水印与电子水印：文字标记、C2PA、EXIF/XMP、隐藏 Unicode 和文档元数据。', targetUnicode: '隐藏 Unicode', targetMetadata: '元数据', targetDocs: '文档痕迹', fileTab: '文件', textTab: '文本', chooseFile: '选择文件', fileHint: 'txt、md、html、png、jpg、svg、pdf、docx、odt · 最大 32 MB', autoDetect: '自动识别文件类型', asText: '文本', asImage: '图片', asDocument: '文档', nfkc: '规范化文本', deepClean: '深度文本清理', keepMetadata: '保留安全图片元数据', nfkcTip: '把文字和空格转成标准形式，解决看着正常但复制异常的问题。', deepCleanTip: '更强力处理相似字母和隐藏字符；文件仍可疑时再打开。', keepMetadataTip: '保留普通相机/软件信息；关闭后会更彻底移除图片元数据。', inspect: '先检查', cleanDownload: '清除水印', textPlaceholder: '把文本粘贴到这里。隐藏 Unicode 和异常空格会被立即清理。', cleanText: '清理文本', copyResult: '复制结果', resultLabel: '结果', readyTitle: '准备清理', download: '下载文件', stepUpload: '上传或粘贴内容', stepScan: '扫描水印和电子痕迹', stepClean: '清理支持的痕迹', removedCount: '已清除', traceTypes: '痕迹类型', readyMessage: '选择文件或粘贴文本后，这里会清楚告诉你发现并处理了什么。', seoTitle: '面向着急使用场景的快速水印与元数据清除', seoBody: '桌面和手机浏览器都可用。支持常见文本、图片、网页和文档文件，并提供清晰的处理报告：AI 标记、C2PA、EXIF/XMP、隐藏字符和文档元数据。', inspecting: '正在检查文件…', cleaning: '正在清理文件…', cleaningText: '正在清理文本…', doneTitle: '已清理完成', checkedTitle: '检查完成', nothingFound: '未发现当前支持清理的痕迹。', cleanedTextReady: '文本已清理，并放回输入框。', copied: '已复制', downloadReady: '清理后的文件已准备好。', errorTitle: '处理失败', rawReport: '技术报告', found: '发现', cleaned: '已清理', risk: '提示', fileSelected: '已选择', cleaningTitle: '正在清理…', expiresNotice: '请及时下载：清理后的文件会在 10 分钟后删除。'
  },
  es: { brandTitle: 'Eliminador de marcas de agua IA', headline: 'Elimina marcas de agua y rastros ocultos ahora.', subtitle: 'Para marcas visibles y electrónicas de Claude, ChatGPT/OpenAI, Gemini y más: C2PA, EXIF/XMP, Unicode invisible y metadatos.', chooseFile: 'Elegir archivo', cleanDownload: 'Limpiar y descargar', cleanText: 'Limpiar texto', resultLabel: 'Resultado', readyTitle: 'Listo para limpiar', download: 'Descargar' },
  hi: { brandTitle: 'AI वॉटरमार्क रिमूवर', headline: 'वॉटरमार्क और छिपे निशान अभी हटाएँ।', subtitle: 'Claude, ChatGPT/OpenAI, Gemini आदि के दिखने वाले और छिपे AI watermark, C2PA, EXIF/XMP, invisible Unicode और metadata साफ़ करें।', chooseFile: 'फ़ाइल चुनें', cleanDownload: 'साफ़ करें और डाउनलोड करें', cleanText: 'टेक्स्ट साफ़ करें', resultLabel: 'परिणाम', readyTitle: 'साफ़ करने के लिए तैयार', download: 'डाउनलोड' },
  ar: { brandTitle: 'مزيل علامات AI المائية', headline: 'أزل العلامات المائية والآثار المخفية الآن.', subtitle: 'يدعم علامات Claude وChatGPT/OpenAI وGemini المرئية والإلكترونية: C2PA وEXIF/XMP وUnicode غير المرئي والبيانات الوصفية.', chooseFile: 'اختر ملفاً', cleanDownload: 'تنظيف وتنزيل', cleanText: 'تنظيف النص', resultLabel: 'النتيجة', readyTitle: 'جاهز للتنظيف', download: 'تنزيل' },
  fr: { brandTitle: 'Suppresseur de filigranes IA', headline: 'Supprimez maintenant les filigranes et traces cachées.', subtitle: 'Prend en charge Claude, ChatGPT/OpenAI, Gemini et plus : filigranes visibles, C2PA, EXIF/XMP, Unicode invisible et métadonnées.', chooseFile: 'Choisir un fichier', cleanDownload: 'Nettoyer et télécharger', cleanText: 'Nettoyer le texte', resultLabel: 'Résultat', readyTitle: 'Prêt à nettoyer', download: 'Télécharger' },
  pt: { brandTitle: 'Removedor de marcas d’água de IA', headline: 'Remova marcas d’água e rastros ocultos agora.', subtitle: 'Suporta Claude, ChatGPT/OpenAI, Gemini e mais: marcas visíveis, C2PA, EXIF/XMP, Unicode invisível e metadados.', chooseFile: 'Escolher arquivo', cleanDownload: 'Limpar e baixar', cleanText: 'Limpar texto', resultLabel: 'Resultado', readyTitle: 'Pronto para limpar', download: 'Baixar' },
  de: { brandTitle: 'KI-Wasserzeichen-Entferner', headline: 'Wasserzeichen und versteckte Spuren jetzt entfernen.', subtitle: 'Für Claude, ChatGPT/OpenAI, Gemini und mehr: sichtbare KI-Wasserzeichen, C2PA, EXIF/XMP, unsichtbares Unicode und Metadaten.', chooseFile: 'Datei wählen', cleanDownload: 'Bereinigen & herunterladen', cleanText: 'Text bereinigen', resultLabel: 'Ergebnis', readyTitle: 'Bereit zum Bereinigen', download: 'Herunterladen' },
  ja: { brandTitle: 'AI 透かし削除', headline: '透かしと隠れた痕跡を今すぐ削除。', subtitle: 'Claude、ChatGPT/OpenAI、Gemini などの可視透かし、C2PA、EXIF/XMP、不可視 Unicode、メタデータに対応。', chooseFile: 'ファイルを選択', cleanDownload: '削除してダウンロード', cleanText: 'テキストを削除', resultLabel: '結果', readyTitle: '準備完了', download: 'ダウンロード' },
  ko: { brandTitle: 'AI 워터마크 제거', headline: '워터마크와 숨겨진 흔적을 지금 제거하세요.', subtitle: 'Claude, ChatGPT/OpenAI, Gemini 등의 보이는 워터마크와 전자 워터마크, C2PA, EXIF/XMP, 보이지 않는 Unicode, 메타데이터를 처리합니다.', chooseFile: '파일 선택', cleanDownload: '정리 및 다운로드', cleanText: '텍스트 정리', resultLabel: '결과', readyTitle: '정리 준비 완료', download: '다운로드' }
};

const localePacks = {
  ja: { language:'言語', eyebrow:'開く・削除・保存', brandTitle:'AI 透かし削除', headline:'透かしと隠れた痕跡を今すぐ削除。', subtitle:'Claude、ChatGPT/OpenAI、Gemini などの可視透かし・電子透かし、C2PA、EXIF/XMP、不可視 Unicode、文書メタデータに対応。', targetUnicode:'不可視 Unicode', targetMetadata:'メタデータ', targetDocs:'文書の痕跡', fileTab:'ファイル', textTab:'テキスト', chooseFile:'ファイルを選択', fileHint:'txt、md、html、png、jpg、svg、pdf、docx、odt · 最大 32 MB', autoDetect:'ファイル形式を自動判定', asText:'テキスト', asImage:'画像', asDocument:'文書', nfkc:'文字を正規化', deepClean:'テキストを深く削除', keepMetadata:'安全な画像情報を保持', nfkcTip:'文字や空白を標準形に整え、見た目は普通でもコピー時に不自然な文字を直します。', deepCleanTip:'似た文字や隠し文字をより強力に削除します。まだ不安な時に使ってください。', keepMetadataTip:'通常のカメラ/アプリ情報は残します。オフにすると画像メタデータをより徹底的に削除します。', inspect:'先に確認', cleanDownload:'削除して保存', textPlaceholder:'ここにテキストを貼り付けてください。不可視 Unicode や不自然な空白をすぐに削除します。', cleanText:'テキストを削除', copyResult:'結果をコピー', resultLabel:'結果', readyTitle:'準備完了', download:'ダウンロード', stepUpload:'ファイルを選ぶ、またはテキストを貼り付ける', stepScan:'透かしと電子的な痕跡を確認', stepClean:'対応する痕跡を削除', removedCount:'削除数', traceTypes:'痕跡の種類', readyMessage:'ファイルを選ぶかテキストを貼ると、検出・削除内容がここに表示されます。', inspecting:'確認中…', cleaning:'削除中…', cleaningText:'テキストを削除中…', doneTitle:'削除完了', checkedTitle:'確認完了', nothingFound:'対応する痕跡は見つかりませんでした。', cleanedTextReady:'テキストを削除し、入力欄に戻しました。', copied:'コピー済み', downloadReady:'削除済みファイルを保存できます。', errorTitle:'処理できませんでした', rawReport:'技術レポート', found:'検出', cleaned:'削除済み', risk:'注意', fileSelected:'選択済み' },
  ko: { language:'언어', eyebrow:'열기 · 정리 · 다운로드', brandTitle:'AI 워터마크 제거', headline:'워터마크와 숨겨진 흔적을 지금 제거하세요.', subtitle:'Claude, ChatGPT/OpenAI, Gemini 등의 보이는 워터마크와 전자 워터마크, C2PA, EXIF/XMP, 보이지 않는 Unicode, 문서 메타데이터를 처리합니다.', targetUnicode:'숨은 Unicode', targetMetadata:'메타데이터', targetDocs:'문서 흔적', fileTab:'파일', textTab:'텍스트', chooseFile:'파일 선택', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · 최대 32 MB', autoDetect:'파일 형식 자동 감지', asText:'텍스트', asImage:'이미지', asDocument:'문서', nfkc:'텍스트 정규화', deepClean:'텍스트 심층 정리', keepMetadata:'안전한 이미지 정보 유지', nfkcTip:'문자와 공백을 표준 형태로 바꿔 복사 시 이상한 문자를 줄입니다.', deepCleanTip:'비슷한 글자와 숨은 문자를 더 강하게 제거합니다.', keepMetadataTip:'일반 카메라/앱 정보는 유지합니다. 끄면 이미지 메타데이터를 더 많이 제거합니다.', inspect:'먼저 확인', cleanDownload:'정리 후 다운로드', textPlaceholder:'텍스트를 붙여넣으세요. 보이지 않는 Unicode와 이상한 공백을 정리합니다.', cleanText:'텍스트 정리', copyResult:'결과 복사', resultLabel:'결과', readyTitle:'정리 준비 완료', download:'다운로드', stepUpload:'파일 업로드 또는 텍스트 붙여넣기', stepScan:'워터마크와 흔적 검사', stepClean:'지원되는 흔적 정리', removedCount:'제거됨', traceTypes:'흔적 유형', readyMessage:'파일이나 텍스트를 넣으면 발견 및 처리 내용이 표시됩니다.', inspecting:'파일 확인 중…', cleaning:'파일 정리 중…', cleaningText:'텍스트 정리 중…', doneTitle:'정리 완료', checkedTitle:'확인 완료', nothingFound:'지원되는 흔적을 찾지 못했습니다.', cleanedTextReady:'텍스트를 정리해 입력칸에 다시 넣었습니다.', copied:'복사됨', downloadReady:'정리된 파일을 다운로드할 수 있습니다.', errorTitle:'처리 실패', rawReport:'기술 보고서', found:'발견', cleaned:'정리됨', risk:'알림', fileSelected:'선택됨' },
  es: { language:'Idioma', eyebrow:'Abrir · Limpiar · Descargar', targetUnicode:'Unicode oculto', targetMetadata:'Metadatos', targetDocs:'Rastros del documento', fileTab:'Archivo', textTab:'Texto', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · máx. 32 MB', autoDetect:'Detectar tipo de archivo', asText:'Texto', asImage:'Imagen', asDocument:'Documento', nfkc:'Normalizar texto', deepClean:'Limpieza profunda', keepMetadata:'Conservar metadatos seguros', nfkcTip:'Convierte caracteres y espacios a una forma estándar.', deepCleanTip:'Elimina con más fuerza letras parecidas y caracteres ocultos.', keepMetadataTip:'Conserva información normal de cámara/app; desactívalo para quitar más metadatos.', inspect:'Comprobar primero', textPlaceholder:'Pega texto aquí. Se limpiarán Unicode invisible y espacios sospechosos.', copyResult:'Copiar resultado', stepUpload:'Subir o pegar contenido', stepScan:'Buscar marcas y rastros', stepClean:'Limpiar rastros compatibles', removedCount:'Eliminado', traceTypes:'Tipos de rastro', readyMessage:'Elige un archivo o pega texto para ver qué se detectó y limpió.', inspecting:'Comprobando archivo…', cleaning:'Limpiando archivo…', cleaningText:'Limpiando texto…', doneTitle:'Limpio', checkedTitle:'Comprobación completa', nothingFound:'No se encontraron rastros compatibles.', cleanedTextReady:'Texto limpio devuelto al cuadro.', copied:'Copiado', downloadReady:'Archivo limpio listo.', errorTitle:'No se pudo procesar', rawReport:'Informe técnico', found:'Encontrado', cleaned:'Limpio', risk:'Nota', fileSelected:'Seleccionado' },
  fr: { language:'Langue', eyebrow:'Ouvrir · Nettoyer · Télécharger', targetUnicode:'Unicode caché', targetMetadata:'Métadonnées', targetDocs:'Traces du document', fileTab:'Fichier', textTab:'Texte', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · max 32 Mo', autoDetect:'Détecter le type de fichier', asText:'Texte', asImage:'Image', asDocument:'Document', nfkc:'Normaliser le texte', deepClean:'Nettoyage profond', keepMetadata:'Garder les métadonnées sûres', nfkcTip:'Convertit caractères et espaces en forme standard.', deepCleanTip:'Supprime plus fortement lettres similaires et caractères cachés.', keepMetadataTip:'Garde les infos normales de caméra/app ; désactivez pour supprimer plus de métadonnées.', inspect:'Vérifier d’abord', textPlaceholder:'Collez le texte ici. Unicode invisible et espaces suspects seront nettoyés.', copyResult:'Copier le résultat', stepUpload:'Importer ou coller du contenu', stepScan:'Analyser les filigranes et traces', stepClean:'Nettoyer les traces prises en charge', removedCount:'Supprimés', traceTypes:'Types de traces', readyMessage:'Choisissez un fichier ou collez du texte pour voir ce qui est détecté et supprimé.', inspecting:'Vérification…', cleaning:'Nettoyage…', cleaningText:'Nettoyage du texte…', doneTitle:'Nettoyé', checkedTitle:'Vérification terminée', nothingFound:'Aucune trace prise en charge trouvée.', cleanedTextReady:'Texte nettoyé replacé dans le champ.', copied:'Copié', downloadReady:'Fichier nettoyé prêt.', errorTitle:'Traitement impossible', rawReport:'Rapport technique', found:'Trouvé', cleaned:'Nettoyé', risk:'Note', fileSelected:'Sélectionné' },
  de: { language:'Sprache', eyebrow:'Öffnen · Bereinigen · Herunterladen', targetUnicode:'Verstecktes Unicode', targetMetadata:'Metadaten', targetDocs:'Dokumentspuren', fileTab:'Datei', textTab:'Text', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · max. 32 MB', autoDetect:'Dateityp automatisch erkennen', asText:'Text', asImage:'Bild', asDocument:'Dokument', nfkc:'Text normalisieren', deepClean:'Tiefenreinigung', keepMetadata:'Sichere Bilddaten behalten', nfkcTip:'Bringt Zeichen und Leerzeichen in eine Standardform.', deepCleanTip:'Entfernt ähnliche Buchstaben und versteckte Zeichen stärker.', keepMetadataTip:'Behält normale Kamera/App-Infos; ausschalten entfernt mehr Bildmetadaten.', inspect:'Zuerst prüfen', textPlaceholder:'Text hier einfügen. Unsichtbares Unicode und verdächtige Leerzeichen werden bereinigt.', copyResult:'Ergebnis kopieren', stepUpload:'Datei hochladen oder Text einfügen', stepScan:'Wasserzeichen und Spuren prüfen', stepClean:'Unterstützte Spuren bereinigen', removedCount:'Entfernt', traceTypes:'Spurtypen', readyMessage:'Datei wählen oder Text einfügen, um erkannte und entfernte Spuren zu sehen.', inspecting:'Datei wird geprüft…', cleaning:'Datei wird bereinigt…', cleaningText:'Text wird bereinigt…', doneTitle:'Bereinigt', checkedTitle:'Prüfung fertig', nothingFound:'Keine unterstützten Spuren gefunden.', cleanedTextReady:'Text bereinigt und zurückgesetzt.', copied:'Kopiert', downloadReady:'Bereinigte Datei ist bereit.', errorTitle:'Verarbeitung fehlgeschlagen', rawReport:'Technischer Bericht', found:'Gefunden', cleaned:'Bereinigt', risk:'Hinweis', fileSelected:'Ausgewählt' },
  ar: { language:'اللغة', eyebrow:'افتح · نظّف · نزّل', targetUnicode:'Unicode مخفي', targetMetadata:'بيانات وصفية', targetDocs:'آثار المستند', fileTab:'ملف', textTab:'نص', fileHint:'txt وmd وhtml وpng وjpg وsvg وpdf وdocx وodt · حتى 32 م.ب', autoDetect:'اكتشاف نوع الملف تلقائياً', asText:'نص', asImage:'صورة', asDocument:'مستند', nfkc:'توحيد النص', deepClean:'تنظيف نص عميق', keepMetadata:'إبقاء بيانات الصورة الآمنة', nfkcTip:'يحوّل الحروف والمسافات إلى شكل قياسي.', deepCleanTip:'يزيل الحروف المتشابهة والرموز المخفية بقوة أكبر.', keepMetadataTip:'يبقي معلومات الكاميرا/التطبيق العادية؛ عطّله لإزالة بيانات أكثر.', inspect:'افحص أولاً', textPlaceholder:'الصق النص هنا. سيتم تنظيف Unicode غير المرئي والمسافات المشبوهة.', copyResult:'نسخ النتيجة', stepUpload:'ارفع ملفاً أو الصق محتوى', stepScan:'فحص العلامات والآثار', stepClean:'تنظيف الآثار المدعومة', removedCount:'تمت الإزالة', traceTypes:'أنواع الآثار', readyMessage:'اختر ملفاً أو الصق نصاً لمعرفة ما تم العثور عليه وتنظيفه.', inspecting:'جارٍ فحص الملف…', cleaning:'جارٍ تنظيف الملف…', cleaningText:'جارٍ تنظيف النص…', doneTitle:'تم التنظيف', checkedTitle:'اكتمل الفحص', nothingFound:'لم يتم العثور على آثار مدعومة.', cleanedTextReady:'تم تنظيف النص وإعادته إلى المربع.', copied:'تم النسخ', downloadReady:'الملف النظيف جاهز.', errorTitle:'تعذرت المعالجة', rawReport:'تقرير تقني', found:'تم العثور', cleaned:'تم التنظيف', risk:'ملاحظة', fileSelected:'تم الاختيار' },
  hi: { language:'भाषा', eyebrow:'खोलें · साफ़ करें · डाउनलोड', targetUnicode:'छिपा Unicode', targetMetadata:'मेटाडेटा', targetDocs:'दस्तावेज़ निशान', fileTab:'फ़ाइल', textTab:'टेक्स्ट', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · अधिकतम 32 MB', autoDetect:'फ़ाइल प्रकार स्वतः पहचानें', asText:'टेक्स्ट', asImage:'चित्र', asDocument:'दस्तावेज़', nfkc:'टेक्स्ट सामान्य करें', deepClean:'गहरी टेक्स्ट सफ़ाई', keepMetadata:'सुरक्षित चित्र जानकारी रखें', nfkcTip:'अक्षर और खाली जगह को मानक रूप में बदलता है।', deepCleanTip:'मिलते-जुलते अक्षर और छिपे चिन्ह अधिक मजबूती से हटाता है।', keepMetadataTip:'सामान्य कैमरा/ऐप जानकारी रखता है; बंद करने पर अधिक मेटाडेटा हटेगा।', inspect:'पहले जाँचें', textPlaceholder:'टेक्स्ट यहाँ पेस्ट करें। छिपे Unicode और संदिग्ध स्पेस साफ़ होंगे।', copyResult:'परिणाम कॉपी करें', stepUpload:'फ़ाइल अपलोड करें या टेक्स्ट पेस्ट करें', stepScan:'वॉटरमार्क और निशान स्कैन करें', stepClean:'समर्थित निशान साफ़ करें', removedCount:'हटाए गए', traceTypes:'निशान प्रकार', readyMessage:'फ़ाइल चुनें या टेक्स्ट पेस्ट करें; क्या मिला और साफ़ हुआ यहाँ दिखेगा।', inspecting:'फ़ाइल जाँची जा रही है…', cleaning:'फ़ाइल साफ़ हो रही है…', cleaningText:'टेक्स्ट साफ़ हो रहा है…', doneTitle:'साफ़ हो गया', checkedTitle:'जाँच पूरी', nothingFound:'समर्थित निशान नहीं मिले।', cleanedTextReady:'टेक्स्ट साफ़ कर बॉक्स में वापस रखा गया।', copied:'कॉपी हुआ', downloadReady:'साफ़ फ़ाइल तैयार है।', errorTitle:'प्रोसेस नहीं हो सका', rawReport:'तकनीकी रिपोर्ट', found:'मिला', cleaned:'साफ़', risk:'नोट', fileSelected:'चुना गया' },
  pt: { language:'Idioma', eyebrow:'Abrir · Limpar · Baixar', targetUnicode:'Unicode oculto', targetMetadata:'Metadados', targetDocs:'Rastros do documento', fileTab:'Arquivo', textTab:'Texto', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · máx. 32 MB', autoDetect:'Detectar tipo de arquivo', asText:'Texto', asImage:'Imagem', asDocument:'Documento', nfkc:'Normalizar texto', deepClean:'Limpeza profunda', keepMetadata:'Manter metadados seguros', nfkcTip:'Converte caracteres e espaços para formato padrão.', deepCleanTip:'Remove letras parecidas e caracteres ocultos com mais força.', keepMetadataTip:'Mantém informações normais de câmera/app; desligue para remover mais metadados.', inspect:'Verificar primeiro', textPlaceholder:'Cole o texto aqui. Unicode invisível e espaços suspeitos serão limpos.', copyResult:'Copiar resultado', stepUpload:'Enviar ou colar conteúdo', stepScan:'Verificar marcas e rastros', stepClean:'Limpar rastros suportados', removedCount:'Removidos', traceTypes:'Tipos de rastro', readyMessage:'Escolha um arquivo ou cole texto para ver o que foi encontrado e removido.', inspecting:'Verificando arquivo…', cleaning:'Limpando arquivo…', cleaningText:'Limpando texto…', doneTitle:'Limpo', checkedTitle:'Verificação concluída', nothingFound:'Nenhum rastro suportado encontrado.', cleanedTextReady:'Texto limpo colocado de volta na caixa.', copied:'Copiado', downloadReady:'Arquivo limpo pronto.', errorTitle:'Não foi possível processar', rawReport:'Relatório técnico', found:'Encontrado', cleaned:'Limpo', risk:'Nota', fileSelected:'Selecionado' },
  it: { language:'Lingua', eyebrow:'Apri · Pulisci · Scarica', brandTitle:'Rimozione watermark AI', headline:'Rimuovi watermark e tracce nascoste ora.', subtitle:'Rimuove watermark visibili e nascosti da Claude, ChatGPT/OpenAI, Gemini e altri: segni nel testo, C2PA, EXIF/XMP, Unicode invisibile e metadati dei documenti.', targetUnicode:'Unicode nascosto', targetMetadata:'Metadati', targetDocs:'Tracce del documento', fileTab:'File', textTab:'Testo', chooseFile:'Scegli file', fileHint:'txt, md, html, png, jpg, svg, pdf, docx, odt · max 32 MB', autoDetect:'Rileva automaticamente il tipo di file', asText:'Testo', asImage:'Immagine', asDocument:'Documento', nfkc:'Normalizza testo', deepClean:'Pulizia profonda del testo', keepMetadata:'Mantieni metadati immagine sicuri', nfkcTip:'Converte caratteri e spazi in una forma standard.', deepCleanTip:'Rimuove in modo più aggressivo lettere simili e caratteri nascosti.', keepMetadataTip:'Mantiene normali informazioni di fotocamera/app; disattiva per rimuovere più metadati.', inspect:'Controlla prima', cleanDownload:'Rimuovi watermark', textPlaceholder:'Incolla qui il testo. Unicode invisibile e spazi sospetti verranno puliti.', cleanText:'Pulisci testo', copyResult:'Copia risultato', resultLabel:'Risultato', readyTitle:'Pronto per la pulizia', download:'Scarica file pulito', stepUpload:'Carica o incolla contenuto', stepScan:'Scansione watermark e tracce', stepClean:'Pulizia delle tracce supportate', removedCount:'Rimossi', traceTypes:'Tipi di traccia', readyMessage:'Scegli un file o incolla testo: qui vedrai cosa è stato trovato e rimosso.', inspecting:'Controllo file…', cleaningTitle:'Pulizia in corso…', cleaning:'Pulizia del file in corso…', cleaningText:'Pulizia del testo in corso…', doneTitle:'Pulizia completata', checkedTitle:'Controllo completato', nothingFound:'Non sono state trovate tracce supportate.', cleanedTextReady:'Testo pulito e reinserito nel campo.', copied:'Copiato', downloadReady:'Il file pulito è pronto.', expiresNotice:'Scarica presto: i file puliti vengono eliminati dopo 10 minuti.', errorTitle:'Impossibile elaborare', rawReport:'Rapporto tecnico', found:'Trovato', cleaned:'Pulito', risk:'Nota', fileSelected:'Selezionato', foundVisibleWatermark:'Trovato {count} watermark visibile', removedVisibleWatermark:'Rimosso {count} watermark visibile', foundAiWatermarkC2pa:'Trovato {count} possibile watermark AI (metadati C2PA)', removedAiWatermarkC2pa:'Rimosso {count} watermark AI (metadati C2PA)', foundHiddenUnicode:'Trovato {count} segno di testo nascosto (Unicode invisibile)', removedHiddenUnicode:'Rimosso {count} segno di testo nascosto (Unicode invisibile)', foundImageMetadata:'Trovata {count} traccia di metadati immagine', removedImageMetadata:'Rimossa {count} traccia di metadati immagine', foundDocumentTrace:'Trovata {count} traccia del documento', removedDocumentTrace:'Rimossa {count} traccia del documento', foundGenericTrace:'Trovata {count} traccia supportata', removedGenericTrace:'Rimossa {count} traccia supportata' }
};

const rtlLocales = new Set(['ar', 'fa', 'ur', 'he']);
const fallback = copy.en;
const currentLocale = document.documentElement.lang || 'en';
const localizedFallback = currentLocale === 'en' ? fallback : (localePacks[currentLocale] || copy.zh);
let dictionary = { ...localizedFallback, ...(copy[currentLocale] || {}), ...(localePacks[currentLocale] || {}) };
const reportCopy = {
  en: { foundVisibleWatermark:'Found {count} visible watermark', removedVisibleWatermark:'Removed {count} visible watermark', foundAiWatermarkC2pa:'Found {count} suspected AI watermark (C2PA metadata)', removedAiWatermarkC2pa:'Removed {count} AI watermark (C2PA metadata)', foundHiddenUnicode:'Found {count} hidden text marker (invisible Unicode)', removedHiddenUnicode:'Removed {count} hidden text marker (invisible Unicode)', foundImageMetadata:'Found {count} image metadata trace', removedImageMetadata:'Removed {count} image metadata trace', foundDocumentTrace:'Found {count} document trace', removedDocumentTrace:'Removed {count} document trace', foundGenericTrace:'Found {count} supported trace', removedGenericTrace:'Removed {count} supported trace' },
  zh: { foundVisibleWatermark:'发现 {count} 个可见水印', removedVisibleWatermark:'已移除 {count} 个可见水印', foundAiWatermarkC2pa:'发现 {count} 个疑似 AI 水印（C2PA 元数据）', removedAiWatermarkC2pa:'已移除 {count} 个 AI 水印（C2PA 元数据）', foundHiddenUnicode:'发现 {count} 个隐藏文本标记（不可见 Unicode）', removedHiddenUnicode:'已移除 {count} 个隐藏文本标记（不可见 Unicode）', foundImageMetadata:'发现 {count} 个图片元数据痕迹', removedImageMetadata:'已移除 {count} 个图片元数据痕迹', foundDocumentTrace:'发现 {count} 个文档痕迹', removedDocumentTrace:'已移除 {count} 个文档痕迹', foundGenericTrace:'发现 {count} 个可处理痕迹', removedGenericTrace:'已移除 {count} 个可处理痕迹' },
  ja: { foundAiWatermarkC2pa:'疑わしい AI 透かし（C2PA メタデータ）を {count} 件検出', removedAiWatermarkC2pa:'AI 透かし（C2PA メタデータ）を {count} 件削除', foundHiddenUnicode:'不可視 Unicode のテキスト痕跡を {count} 件検出', removedHiddenUnicode:'不可視 Unicode のテキスト痕跡を {count} 件削除', foundImageMetadata:'画像メタデータの痕跡を {count} 件検出', removedImageMetadata:'画像メタデータの痕跡を {count} 件削除', foundDocumentTrace:'文書の痕跡を {count} 件検出', removedDocumentTrace:'文書の痕跡を {count} 件削除', foundGenericTrace:'対応する痕跡を {count} 件検出', removedGenericTrace:'対応する痕跡を {count} 件削除' },
  ko: { foundAiWatermarkC2pa:'의심되는 AI 워터마크(C2PA 메타데이터) {count}개 발견', removedAiWatermarkC2pa:'AI 워터마크(C2PA 메타데이터) {count}개 제거', foundHiddenUnicode:'숨은 텍스트 표시(보이지 않는 Unicode) {count}개 발견', removedHiddenUnicode:'숨은 텍스트 표시(보이지 않는 Unicode) {count}개 제거', foundImageMetadata:'이미지 메타데이터 흔적 {count}개 발견', removedImageMetadata:'이미지 메타데이터 흔적 {count}개 제거', foundDocumentTrace:'문서 흔적 {count}개 발견', removedDocumentTrace:'문서 흔적 {count}개 제거', foundGenericTrace:'처리 가능한 흔적 {count}개 발견', removedGenericTrace:'처리 가능한 흔적 {count}개 제거' },
  es: { foundAiWatermarkC2pa:'Encontró {count} posible marca de agua IA (metadatos C2PA)', removedAiWatermarkC2pa:'Eliminó {count} marca de agua IA (metadatos C2PA)', foundHiddenUnicode:'Encontró {count} marca de texto oculta (Unicode invisible)', removedHiddenUnicode:'Eliminó {count} marca de texto oculta (Unicode invisible)', foundImageMetadata:'Encontró {count} rastro de metadatos de imagen', removedImageMetadata:'Eliminó {count} rastro de metadatos de imagen', foundDocumentTrace:'Encontró {count} rastro de documento', removedDocumentTrace:'Eliminó {count} rastro de documento', foundGenericTrace:'Encontró {count} rastro compatible', removedGenericTrace:'Eliminó {count} rastro compatible' },
  fr: { foundAiWatermarkC2pa:'A trouvé {count} filigrane IA possible (métadonnées C2PA)', removedAiWatermarkC2pa:'A supprimé {count} filigrane IA (métadonnées C2PA)', foundHiddenUnicode:'A trouvé {count} marque de texte cachée (Unicode invisible)', removedHiddenUnicode:'A supprimé {count} marque de texte cachée (Unicode invisible)', foundImageMetadata:'A trouvé {count} trace de métadonnées image', removedImageMetadata:'A supprimé {count} trace de métadonnées image', foundDocumentTrace:'A trouvé {count} trace de document', removedDocumentTrace:'A supprimé {count} trace de document', foundGenericTrace:'A trouvé {count} trace prise en charge', removedGenericTrace:'A supprimé {count} trace prise en charge' },
  de: { foundAiWatermarkC2pa:'{count} mögliches KI-Wasserzeichen gefunden (C2PA-Metadaten)', removedAiWatermarkC2pa:'{count} KI-Wasserzeichen entfernt (C2PA-Metadaten)', foundHiddenUnicode:'{count} versteckte Textmarkierung gefunden (unsichtbares Unicode)', removedHiddenUnicode:'{count} versteckte Textmarkierung entfernt (unsichtbares Unicode)', foundImageMetadata:'{count} Bildmetadaten-Spur gefunden', removedImageMetadata:'{count} Bildmetadaten-Spur entfernt', foundDocumentTrace:'{count} Dokumentspur gefunden', removedDocumentTrace:'{count} Dokumentspur entfernt', foundGenericTrace:'{count} unterstützte Spur gefunden', removedGenericTrace:'{count} unterstützte Spur entfernt' },
  pt: { foundAiWatermarkC2pa:'Encontrou {count} possível marca d’água de IA (metadados C2PA)', removedAiWatermarkC2pa:'Removeu {count} marca d’água de IA (metadados C2PA)', foundHiddenUnicode:'Encontrou {count} marca de texto oculta (Unicode invisível)', removedHiddenUnicode:'Removeu {count} marca de texto oculta (Unicode invisível)', foundImageMetadata:'Encontrou {count} rastro de metadados de imagem', removedImageMetadata:'Removeu {count} rastro de metadados de imagem', foundDocumentTrace:'Encontrou {count} rastro de documento', removedDocumentTrace:'Removeu {count} rastro de documento', foundGenericTrace:'Encontrou {count} rastro suportado', removedGenericTrace:'Removeu {count} rastro suportado' },
  hi: { foundAiWatermarkC2pa:'{count} संदिग्ध AI watermark मिला (C2PA metadata)', removedAiWatermarkC2pa:'{count} AI watermark हटाया गया (C2PA metadata)', foundHiddenUnicode:'{count} hidden text marker मिला (invisible Unicode)', removedHiddenUnicode:'{count} hidden text marker हटाया गया (invisible Unicode)', foundImageMetadata:'{count} image metadata trace मिला', removedImageMetadata:'{count} image metadata trace हटाया गया', foundDocumentTrace:'{count} document trace मिला', removedDocumentTrace:'{count} document trace हटाया गया', foundGenericTrace:'{count} supported trace मिला', removedGenericTrace:'{count} supported trace हटाया गया' },
  ar: { foundAiWatermarkC2pa:'تم العثور على {count} علامة AI محتملة (بيانات C2PA)', removedAiWatermarkC2pa:'تمت إزالة {count} علامة AI (بيانات C2PA)', foundHiddenUnicode:'تم العثور على {count} علامة نص مخفية (Unicode غير مرئي)', removedHiddenUnicode:'تمت إزالة {count} علامة نص مخفية (Unicode غير مرئي)', foundImageMetadata:'تم العثور على {count} أثر بيانات صورة', removedImageMetadata:'تمت إزالة {count} أثر بيانات صورة', foundDocumentTrace:'تم العثور على {count} أثر مستند', removedDocumentTrace:'تمت إزالة {count} أثر مستند', foundGenericTrace:'تم العثور على {count} أثر مدعوم', removedGenericTrace:'تمت إزالة {count} أثر مدعوم' }
};
Object.assign(dictionary, reportCopy[currentLocale] || (currentLocale === 'en' ? reportCopy.en : reportCopy.zh));

const languageSelect = document.querySelector('#languageSelect');
const fileForm = document.querySelector('#fileForm');
const fileInput = document.querySelector('#fileInput');
const uploadProgress = document.querySelector('#uploadProgress');
const uploadProgressBar = document.querySelector('#uploadProgressBar');
const fileLabel = document.querySelector('#fileLabel');
const cleanTextBtn = document.querySelector('#cleanTextBtn');
const copyTextBtn = document.querySelector('#copyTextBtn');
const textInput = document.querySelector('#textInput');
const tooltipPopover = document.createElement('div');
tooltipPopover.className = 'tooltip-popover';
document.body.append(tooltipPopover);
const downloadLink = document.querySelector('#downloadLink');
const expiryNotice = document.querySelector('#expiryNotice');
const textSuccess = document.querySelector('#textSuccess');
const resultTitle = document.querySelector('#resultTitle');
const steps = Array.from(document.querySelectorAll('#steps li'));
const clearList = document.querySelector('#clearList');
const removedCount = document.querySelector('#removedCount');
const traceTypes = document.querySelector('#traceTypes');

function t(key) { return dictionary[key] || reportCopy.zh[key] || fallback[key] || key; }

function initLanguage() {
  Object.entries(localeNames).forEach(([code, name]) => {
    const option = document.createElement('option');
    option.value = code;
    option.textContent = name;
    option.selected = code === currentLocale;
    languageSelect.append(option);
  });
  languageSelect.addEventListener('change', () => {
    localStorage.setItem('preferredLocale', languageSelect.value);
    window.location.href = languageSelect.value === 'en' ? '/' : `/${languageSelect.value}`;
  });
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  document.querySelectorAll('[data-tooltip-i18n]').forEach((node) => {
    const value = t(node.dataset.tooltipI18n);
    node.dataset.tooltip = value;
    node.setAttribute('aria-label', value);
  });
  document.documentElement.dir = rtlLocales.has(currentLocale) ? 'rtl' : 'ltr';
}

function setBusy(isBusy) {
  document.querySelectorAll('button, input, select, textarea').forEach((element) => {
    if (element.id === 'languageSelect') return;
    element.disabled = isBusy;
    element.style.opacity = isBusy ? '0.62' : '1';
  });
}

function setSteps(state) {
  steps.forEach((step, index) => {
    step.className = '';
    if (index < state) step.classList.add('done');
    if (index === state) step.classList.add('active');
    if (index > state) step.classList.add('pending');
  });
}

function resetDownload() {
  downloadLink.classList.add('hidden');
  downloadLink.removeAttribute('href');
  expiryNotice.classList.add('hidden');
  textSuccess.classList.add('hidden');
  document.querySelector('.result-card')?.classList.remove('expanded');
}

function formDataWithBooleans(form) {
  const data = new FormData(form);
  ['nfkc', 'aggressive_homoglyphs', 'keep_non_ai_metadata'].forEach((name) => {
    data.set(name, form.elements[name].checked ? 'true' : 'false');
  });
  return data;
}

async function postForm(url, data) {
  setBusy(true);
  resetDownload();
  uploadProgress?.classList.remove('hidden');
  if (uploadProgressBar) uploadProgressBar.style.width = '8%';
  try {
    const payload = await new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open('POST', url);
      request.responseType = 'json';
      request.upload.onprogress = (event) => {
        if (!event.lengthComputable || !uploadProgressBar) return;
        const percent = Math.max(8, Math.min(95, Math.round((event.loaded / event.total) * 100)));
        uploadProgressBar.style.width = `${percent}%`;
      };
      request.onload = () => {
        if (uploadProgressBar) uploadProgressBar.style.width = '100%';
        const response = request.response || JSON.parse(request.responseText || '{}');
        if (request.status >= 200 && request.status < 300) resolve(response);
        else reject(new Error(response.detail || 'Request failed'));
      };
      request.onerror = () => reject(new Error('Network error'));
      request.send(data);
    });
    return payload;
  } finally {
    setBusy(false);
    setTimeout(() => uploadProgress?.classList.add('hidden'), 450);
  }
}

function summarizeReport(payload, mode) {
  const report = payload.report || {};
  const stats = report.stats || {};
  const findings = report.findings || report.pre_findings || [];
  const actions = report.actions || [];
  const removed = stats.removed || {};
  const replaced = stats.replaced || {};
  const items = [];
  let count = Number(stats.removed_count || 0) + Number(stats.replaced_count || 0);

  Object.entries(removed).forEach(([name, value]) => items.push({ label: friendlyReportLabel(name, mode, value), value: '' }));
  Object.entries(replaced).forEach(([name, value]) => items.push({ label: friendlyReportLabel(name, mode, value), value: '' }));
  const meaningfulActions = actions.filter((action) => !isNoopReportItem(action));
  meaningfulActions.forEach((action) => items.push({ label: friendlyReportLabel(action, mode, 1), value: '' }));
  findings.filter((finding) => !isNoopReportItem(finding)).forEach((finding) => items.push({ label: friendlyReportLabel(finding, 'inspect', 1), value: '' }));

  if (!count) count = meaningfulActions.length || Object.keys(removed).length + Object.keys(replaced).length;
  const typeCount = new Set(items.map((item) => item.label.split(':')[0] + item.label.slice(0, 26))).size;
  const title = mode === 'inspect' ? t('checkedTitle') : t('doneTitle');
  const lead = mode === 'text' ? t('cleanedTextReady') : payload.download_url ? t('downloadReady') : t('nothingFound');

  return { report, items, count, typeCount, title, lead, downloadUrl: payload.download_url };
}

function isNoopReportItem(item) {
  const text = formatReportItem(item).toLowerCase();
  return /no .* removed/.test(text) || text.includes('already clean') || text.includes('none matched') || text.includes('no metadata chunks removed');
}

function friendlyReportLabel(item, mode = 'clean', count = 1) {
  const text = formatReportItem(item);
  const lower = text.toLowerCase();
  const prefix = mode === 'inspect' ? 'found' : 'removed';
  let key = 'GenericTrace';
  if (lower.includes('visible') || lower.includes('text watermark') || lower.includes('watermark overlay')) key = 'VisibleWatermark';
  else if (lower.includes('c2pa') || lower.includes('content credential') || lower.includes('cabx') || lower.includes('jumb')) key = 'AiWatermarkC2pa';
  else if (lower.includes('unicode') || lower.includes('zero-width') || lower.includes('zero width') || lower.includes('homoglyph') || lower.includes('u+200') || lower.includes('ufeff')) key = 'HiddenUnicode';
  else if (lower.includes('exif') || lower.includes('xmp') || lower.includes('metadata') || lower.includes('png chunk') || lower.includes('image')) key = 'ImageMetadata';
  else if (lower.includes('pdf') || lower.includes('docx') || lower.includes('odt') || lower.includes('document')) key = 'DocumentTrace';
  return t(`${prefix}${key}`).replace('{count}', String(count || 1));
}

function formatReportItem(item) {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object') {
    return item.label || item.name || item.kind || item.type || item.message || JSON.stringify(item);
  }
  return String(item ?? '');
}

function renderResult(payload, mode = 'clean') {
  document.querySelector('.result-card')?.classList.add('expanded');
  const summary = summarizeReport(payload, mode);
  resultTitle.textContent = summary.title;
  removedCount.textContent = String(summary.count || 0);
  traceTypes.textContent = String(summary.typeCount || 0);

  const visibleItems = summary.items.length ? summary.items : [{ label: summary.lead, value: '' }];
  clearList.innerHTML = `
    <ul>${visibleItems.slice(0, 8).map((item) => `<li>${item.value ? `<strong>${escapeHtml(String(item.value))}</strong> ` : ''}${escapeHtml(item.label)}</li>`).join('')}</ul>
    ${summary.report.notes ? `<p class="raw-details">${escapeHtml(summary.report.notes)}</p>` : ''}
    <details><summary>${escapeHtml(t('rawReport'))}</summary><pre class="raw-details">${escapeHtml(JSON.stringify(summary.report, null, 2))}</pre></details>
  `;
  setSteps(3);
  textSuccess.classList.toggle('hidden', mode !== 'text');
  expiryNotice.classList.toggle('hidden', !summary.downloadUrl);
}

function renderReady() {
  document.querySelector('.result-card')?.classList.remove('expanded');
  resultTitle.textContent = t('readyTitle');
  clearList.innerHTML = `<p>${escapeHtml(t('readyMessage'))}</p><ul class="ready-traces"><li><strong>Unicode</strong><span>${escapeHtml(t('targetUnicode'))}</span></li><li><strong>C2PA / EXIF / XMP</strong><span>${escapeHtml(t('targetMetadata'))}</span></li><li><strong>PDF / DOCX</strong><span>${escapeHtml(t('targetDocs'))}</span></li></ul>`;
  removedCount.textContent = '0';
  traceTypes.textContent = '0';
  setSteps(0);
  resetDownload();
}

function renderMessage(title, message, step = 1) {
  document.querySelector('.result-card')?.classList.remove('expanded');
  resultTitle.textContent = title;
  clearList.innerHTML = `<p>${escapeHtml(message)}</p>`;
  removedCount.textContent = '0';
  traceTypes.textContent = '0';
  setSteps(step);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    document.querySelectorAll('.tool-panel').forEach((panel) => panel.classList.toggle('active', panel.dataset.panel === tab.dataset.mode));
  });
});

fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  fileLabel.textContent = file ? `${t('fileSelected')}: ${file.name}` : t('chooseFile');
  renderReady();
});

fileForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!fileForm.reportValidity()) return;
  renderMessage(t('cleaningTitle'), t('cleaning'), 2);
  try {
    const payload = await postForm('/api/clean', formDataWithBooleans(fileForm));
    renderResult(payload, 'clean');
    if (payload.download_url) {
      downloadLink.href = `${payload.download_url}?name=${encodeURIComponent(payload.download_name || 'cleaned-file')}`;
      downloadLink.download = payload.download_name || 'cleaned-file';
      downloadLink.classList.remove('hidden');
    }
  } catch (error) {
    renderMessage(t('errorTitle'), error.message, 1);
  }
});

cleanTextBtn.addEventListener('click', async () => {
  const data = new FormData();
  data.set('text', textInput.value);
  data.set('nfkc', 'false');
  data.set('aggressive_homoglyphs', 'true');
  renderMessage(t('cleaningTitle'), t('cleaningText'), 2);
  try {
    const payload = await postForm('/api/clean-text', data);
    textInput.value = payload.cleaned_text || '';
    renderResult(payload, 'text');
  } catch (error) {
    renderMessage(t('errorTitle'), error.message, 1);
  }
});

copyTextBtn.addEventListener('click', async () => {
  await navigator.clipboard.writeText(textInput.value);
  copyTextBtn.textContent = t('copied');
  setTimeout(() => { copyTextBtn.textContent = t('copyResult'); }, 1300);
});

function showTooltip(tip) {
  tooltipPopover.textContent = tip.dataset.tooltip || '';
  const rect = tip.getBoundingClientRect();
  const isMobile = window.innerWidth <= 720;
  const width = Math.min(isMobile ? 236 : 300, window.innerWidth - 24);
  const left = Math.min(Math.max(12, rect.right - width), window.innerWidth - width - 12);
  let top = isMobile ? rect.bottom + 8 : rect.top - 96;
  tooltipPopover.style.width = `${width}px`;
  tooltipPopover.style.left = `${left}px`;
  tooltipPopover.style.top = `${Math.max(12, top)}px`;
  tooltipPopover.classList.add('active');
  const popoverRect = tooltipPopover.getBoundingClientRect();
  if (popoverRect.bottom > window.innerHeight - 12) {
    top = Math.max(12, rect.top - popoverRect.height - 8);
    tooltipPopover.style.top = `${top}px`;
  }
}

function hideTooltip() {
  tooltipPopover.classList.remove('active');
}

document.querySelectorAll('.tip').forEach((tip) => {
  tip.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    document.querySelectorAll('.tip').forEach((item) => {
      if (item !== tip) item.classList.remove('show-tooltip');
    });
    tip.classList.toggle('show-tooltip');
    if (tip.classList.contains('show-tooltip')) showTooltip(tip); else hideTooltip();
  });
  tip.addEventListener('mouseenter', () => showTooltip(tip));
  tip.addEventListener('mouseleave', () => {
    if (!tip.classList.contains('show-tooltip')) hideTooltip();
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.tip').forEach((tip) => tip.classList.remove('show-tooltip'));
  hideTooltip();
});

initLanguage();
applyTranslations();
renderReady();
