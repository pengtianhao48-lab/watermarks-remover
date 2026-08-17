#!/usr/bin/env python3
"""Lightweight statistical SynthID-style text detector and neutralizer.

The real Claude / SynthID-family watermarking schemes are proprietary or require
heavy upstream checkpoints. This module provides an equivalent *statistical
likelihood* workflow suitable for deployment in this repo:

- detection: estimate how strongly the text still exhibits watermark-friendly
  token-boundary regularity and low-burstiness language patterns
- neutralization: perturb token boundaries with legal Unicode spaces and apply
  limited synonym rewrites on verbs/adjectives via spaCy + Open Multilingual
  WordNet (falls back to whitespace-only for unsupported languages)

Detection language is inferred at runtime (langdetect); each language selects
its own spaCy model and OMW WordNet lang code. Missing models/OMW entries
degrade gracefully to whitespace-only neutralization without raising errors.

It is intentionally conservative: scores are probabilistic, not proofs.
"""

from __future__ import annotations

import logging
import math
import random
import re
from collections import Counter
from functools import lru_cache
from typing import Any

try:
    import spacy
except ImportError:  # pragma: no cover - optional until deps are installed
    spacy = None  # type: ignore[assignment]

try:
    from nltk.corpus import wordnet as wn
except ImportError:  # pragma: no cover - optional until deps are installed
    wn = None  # type: ignore[assignment]

try:
    from langdetect import detect as _lang_detect, DetectorFactory
    DetectorFactory.seed = 0
except ImportError:  # pragma: no cover - optional until deps are installed
    _lang_detect = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
SPACE_RE = re.compile(r"[ \t\u00a0\u202f]+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s*")
CONNECTOR_WORDS = {
    "however", "moreover", "therefore", "additionally", "furthermore",
    "overall", "indeed", "notably", "meanwhile", "consequently",
    "ultimately", "specifically",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "for", "from", "had", "has",
    "have", "he", "her", "his", "i", "if", "in", "into", "is", "it", "its", "of", "on", "or", "our", "she", "that",
    "the", "their", "them", "there", "they", "this", "to", "was", "we", "were", "will", "with", "you", "your",
}
WHITESPACE_VARIANTS = ("\u00a0", "\u202f")
# Zero-width joinable spaces we can splice INSIDE CJK/other-non-space text
CJK_INVISIBLE_VARIANTS = ("\u200b", "\u200c")
TEXTISH_EXTENSIONS = {"txt", "md", "markdown", "html", "htm", "csv", "json", "xml", "yaml", "yml"}

# ---------- Language configuration ----------
LANG_SPACY_MODELS: dict[str, str] = {
    "en": "en_core_web_sm",
    "zh": "zh_core_web_sm",
    "es": "es_core_news_sm",
    "fr": "fr_core_news_sm",
    "de": "de_core_news_sm",
    "ja": "ja_core_news_sm",
}
# NLTK Open Multilingual WordNet (omw-1.4) language codes.
# Only languages that actually ship with omw-1.4 are listed; others fall back
# to whitespace-only neutralization (no synonym rewrite).
LANG_OMW: dict[str, str] = {
    "en": "eng",
    "zh": "cmn",
    "es": "spa",
    "fr": "fra",
    "ja": "jpn",
    "ar": "arb",
}
# spaCy blank languages used when a full model is unavailable but we still
# want basic tokenization (helps for Arabic / Korean).
LANG_BLANK: dict[str, str] = {
    "ar": "ar",
    "ko": "ko",
    "hi": "hi",
}
SUPPORTED_LANGS = {"en", "zh", "es", "fr", "de", "ja", "ar", "ko", "hi"}


class SynthIDRuntimeError(RuntimeError):
    """Raised when optional synthid-text dependencies are unavailable."""


def _normalize_lang(code: str | None) -> str:
    if not code:
        return "en"
    code = code.lower().replace("_", "-")
    primary = code.split("-", 1)[0]
    aliases = {
        "zh": "zh", "zh-cn": "zh", "zh-tw": "zh", "cmn": "zh",
        "es": "es", "fr": "fr", "de": "de", "ja": "ja", "jp": "ja",
        "ko": "ko", "kr": "ko", "ar": "ar", "hi": "hi", "en": "en",
    }
    return aliases.get(primary, primary if primary in SUPPORTED_LANGS else "en")


def detect_text_language(text: str, hint: str | None = None) -> str:
    if hint:
        norm = _normalize_lang(hint)
        if norm in SUPPORTED_LANGS:
            return norm
    stripped = (text or "").strip()
    if not stripped:
        return "en"
    if _lang_detect is not None:
        try:
            code = _lang_detect(stripped)
            norm = _normalize_lang(code)
            if norm in SUPPORTED_LANGS:
                return norm
        except Exception:  # pragma: no cover - langdetect is noisy on short input
            logger.debug("langdetect failed", exc_info=True)
    # Fallback heuristics
    if CJK_RE.search(stripped):
        # very rough: hiragana/katakana = ja, hangul = ko, else zh
        if re.search(r"[\u3040-\u30ff]", stripped):
            return "ja"
        if re.search(r"[\uac00-\ud7af]", stripped):
            return "ko"
        return "zh"
    if re.search(r"[\u0600-\u06ff]", stripped):
        return "ar"
    if re.search(r"[\u0900-\u097f]", stripped):
        return "hi"
    return "en"


@lru_cache(maxsize=16)
def _load_spacy_for(lang: str):
    """Load the best spaCy pipeline available for a language.

    Returns (nlp, kind) where kind is 'full' (proper model), 'blank' (blank
    language, tokenization only), or None if spaCy itself is missing.
    """
    if spacy is None:
        return None, None
    model_name = LANG_SPACY_MODELS.get(lang)
    if model_name:
        try:
            return spacy.load(model_name, disable=["parser"]), "full"
        except OSError:
            logger.info("spaCy model %s missing, falling back to blank", model_name)
    blank_code = LANG_BLANK.get(lang, lang)
    try:
        return spacy.blank(blank_code), "blank"
    except Exception:
        logger.info("spaCy blank(%s) not available, using blank(en)", blank_code)
        try:
            return spacy.blank("en"), "blank"
        except Exception:  # pragma: no cover
            return None, None


def _load_spacy_model():
    """Backward-compatible shim; used by legacy callers/tests expecting English only."""
    nlp, kind = _load_spacy_for("en")
    if nlp is None or kind != "full":
        raise SynthIDRuntimeError(
            "spaCy English model is missing; install en_core_web_sm"
        )
    return nlp


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokenize_words(text: str) -> list[str]:
    tokens = WORD_RE.findall(text.lower())
    if tokens:
        return tokens
    # CJK / other scripts have no ASCII words → use single-character tokens
    return [c for c in text if c.strip() and not c.isspace() and not c.isdigit()]


def _sentence_lengths(text: str) -> list[int]:
    parts = [chunk.strip() for chunk in SENTENCE_SPLIT_RE.split(text.strip()) if chunk.strip()]
    if not parts:
        return []
    return [len(_tokenize_words(part)) for part in parts if _tokenize_words(part)]


def _ordinary_space_ratio(text: str) -> float:
    whitespace_chars = [char for char in text if char.isspace()]
    if not whitespace_chars:
        return 0.58 if len(text) > 40 else 0.35
    ordinary = sum(1 for char in whitespace_chars if char == " ")
    return ordinary / len(whitespace_chars)


def _ttr_score(words: list[str]) -> float:
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    return _clamp((0.68 - unique_ratio) / 0.28)


def _repetition_score(words: list[str]) -> float:
    if len(words) < 8:
        return 0.0
    bigrams = list(zip(words, words[1:]))
    top_bigram = Counter(bigrams).most_common(1)[0][1]
    top_word = Counter(words).most_common(1)[0][1]
    bigram_ratio = top_bigram / max(1, len(bigrams))
    word_ratio = top_word / max(1, len(words))
    return _clamp((bigram_ratio * 1.55) + ((word_ratio - 0.07) * 1.75))


def _burstiness_score(text: str) -> float:
    lengths = _sentence_lengths(text)
    if len(lengths) < 2:
        return 0.38
    mean = sum(lengths) / len(lengths)
    if mean <= 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in lengths) / len(lengths)
    normalized = math.sqrt(variance) / mean
    return _clamp((0.44 - normalized) / 0.28)


def _connector_score(words: list[str]) -> float:
    if not words:
        return 0.0
    connector_hits = sum(1 for word in words if word in CONNECTOR_WORDS)
    return _clamp(connector_hits / max(1, len(words) / 22.0))


def _stopword_score(words: list[str]) -> float:
    if not words:
        return 0.0
    ratio = sum(1 for word in words if word in STOPWORDS) / len(words)
    return _clamp((ratio - 0.42) / 0.22)


def _length_regularization_score(words: list[str]) -> float:
    if len(words) < 6:
        return 0.0
    lengths = [len(word) for word in words]
    mean = sum(lengths) / len(lengths)
    variance = sum((value - mean) ** 2 for value in lengths) / len(lengths)
    return _clamp((2.7 - variance) / 1.9)


def detect_synthid_likelihood(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {
            "score": 0.0,
            "label": "low",
            "components": {
                "boundary_signal": 0.0,
                "lexical_signal": 0.0,
                "burstiness_signal": 0.0,
                "repetition_signal": 0.0,
                "connector_signal": 0.0,
                "stopword_signal": 0.0,
                "length_signal": 0.0,
            },
        }

    words = _tokenize_words(stripped)
    components = {
        "boundary_signal": _ordinary_space_ratio(stripped),
        "lexical_signal": _ttr_score(words),
        "burstiness_signal": _burstiness_score(stripped),
        "repetition_signal": _repetition_score(words),
        "connector_signal": _connector_score(words),
        "stopword_signal": _stopword_score(words),
        "length_signal": _length_regularization_score(words),
    }
    score = 100.0 * (
        (components["boundary_signal"] * 0.31)
        + (components["lexical_signal"] * 0.19)
        + (components["burstiness_signal"] * 0.16)
        + (components["repetition_signal"] * 0.14)
        + (components["connector_signal"] * 0.08)
        + (components["stopword_signal"] * 0.07)
        + (components["length_signal"] * 0.05)
    )
    if len(words) < 40:
        score *= 0.78
    if len(words) < 16:
        score *= 0.72
    score = round(_clamp(score / 100.0) * 100.0, 1)
    if score < 30:
        label = "low"
    elif score < 70:
        label = "medium"
    else:
        label = "high"
    return {"score": score, "label": label, "components": components}


def _pick_space_indexes(text: str, rng: random.Random) -> list[int]:
    candidates = [index for index, char in enumerate(text) if char == " "]
    if not candidates:
        return []
    rate = rng.uniform(0.15, 0.25)
    target = max(1, round(len(candidates) * rate))
    rng.shuffle(candidates)
    return sorted(candidates[:target])


def _pick_cjk_split_indexes(text: str, rng: random.Random) -> list[int]:
    """For text without regular spaces (CJK), pick insertion points *between*
    tokens where an invisible zero-width space is legal."""
    candidates: list[int] = []
    prev_is_word = False
    for index, char in enumerate(text):
        is_word = bool(CJK_RE.match(char)) or char.isalnum()
        if prev_is_word and is_word:
            candidates.append(index)
        prev_is_word = is_word
    if not candidates:
        return []
    rate = rng.uniform(0.08, 0.15)
    target = max(1, round(len(candidates) * rate))
    rng.shuffle(candidates)
    return sorted(candidates[:target])


def _mix_whitespace(text: str, lang: str, rng: random.Random) -> tuple[str, dict[str, int]]:
    """Swap a fraction of ordinary spaces with legal look-alike Unicode
    whitespace. For CJK (no ASCII spaces), insert legal zero-width joiners
    between adjacent word-forming characters instead."""
    indexes = set(_pick_space_indexes(text, rng))
    counts = {"nbsp": 0, "nnbsp": 0, "zwsp": 0, "changed_spaces": 0}
    if indexes:
        chars = list(text)
        for index in indexes:
            replacement = rng.choice(WHITESPACE_VARIANTS)
            chars[index] = replacement
            counts["changed_spaces"] += 1
            if replacement == "\u00a0":
                counts["nbsp"] += 1
            else:
                counts["nnbsp"] += 1
        return "".join(chars), counts

    # No ASCII spaces (typical for CJK). Fall back to zero-width insertion.
    if lang in {"zh", "ja"}:
        insert_positions = _pick_cjk_split_indexes(text, rng)
        if insert_positions:
            pieces: list[str] = []
            cursor = 0
            for pos in insert_positions:
                pieces.append(text[cursor:pos])
                pieces.append(rng.choice(CJK_INVISIBLE_VARIANTS))
                cursor = pos
                counts["zwsp"] += 1
                counts["changed_spaces"] += 1
            pieces.append(text[cursor:])
            return "".join(pieces), counts

    return text, counts


def _apply_case(candidate: str, original: str) -> str:
    if original.isupper():
        return candidate.upper()
    if original.istitle():
        return candidate.title()
    return candidate


def _simple_inflect(base: str, tag: str) -> str:
    if tag == "VBZ":
        if base.endswith(("s", "x", "z", "ch", "sh", "o")):
            return f"{base}es"
        if base.endswith("y") and len(base) > 1 and base[-2] not in "aeiou":
            return f"{base[:-1]}ies"
        return f"{base}s"
    if tag == "VBG":
        if base.endswith("ie"):
            return f"{base[:-2]}ying"
        if base.endswith("e") and not base.endswith("ee"):
            return f"{base[:-1]}ing"
        return f"{base}ing"
    if tag in {"VBD", "VBN"}:
        if base.endswith("e"):
            return f"{base}d"
        if base.endswith("y") and len(base) > 1 and base[-2] not in "aeiou":
            return f"{base[:-1]}ied"
        return f"{base}ed"
    return base


def _wordnet_pos(pos_tag: str):
    if wn is None:
        raise SynthIDRuntimeError("nltk WordNet is not installed")
    if pos_tag == "VERB":
        return wn.VERB
    if pos_tag == "ADJ":
        return wn.ADJ
    if pos_tag == "NOUN":
        return wn.NOUN
    return None


def _score_synonym(candidate: str, token_text: str, lemma_count: int) -> tuple[float, float, int]:
    length_gap = abs(len(candidate) - len(token_text))
    same_first = 1.0 if candidate[:1].lower() == token_text[:1].lower() else 0.0
    return (length_gap, -same_first, -lemma_count)


def _lookup_wordnet(target: str, wn_pos, omw_lang: str) -> dict[str, int]:
    """Fetch OMW synset candidates for target using the requested lang code.

    Returns a mapping of raw lemma → best lemma count (higher = more common).
    """
    seen: dict[str, int] = {}
    if wn is None:
        return seen
    try:
        # Prefer OMW-native lookup: wn.synsets(word, pos=..., lang=<iso3>)
        native_synsets = list(wn.synsets(target, pos=wn_pos, lang=omw_lang))
    except Exception:
        native_synsets = []

    for synset in native_synsets:
        # Same-lang synonyms
        try:
            for lemma in synset.lemmas(lang=omw_lang):
                raw = lemma.name().replace("_", " ").strip()
                if raw.lower() == target.lower() or not raw:
                    continue
                seen[raw] = max(seen.get(raw, 0), int(lemma.count() or 0))
        except Exception:
            pass

    # Fallback: if native lookup was empty, try via English pivot for widely-used langs
    if not seen and omw_lang != "eng":
        try:
            for synset in wn.synsets(target, pos=wn_pos, lang=omw_lang):
                for lemma in synset.lemmas("eng"):
                    raw = lemma.name().replace("_", " ").strip()
                    if raw.lower() == target.lower() or not raw:
                        continue
                    # For non-English source we only use pivot if candidate is same script
                    seen[raw] = max(seen.get(raw, 0), int(lemma.count() or 0))
        except Exception:
            pass
    return seen


def _synonym_candidates(token, lang: str) -> list[str]:
    if wn is None:
        raise SynthIDRuntimeError("nltk WordNet is not installed")
    lemma_text = (getattr(token, "lemma_", None) or token.text).strip()
    if not lemma_text:
        return []
    wn_pos = _wordnet_pos(getattr(token, "pos_", ""))
    if wn_pos is None:
        return []
    omw_lang = LANG_OMW.get(lang)
    if not omw_lang:
        return []
    target = lemma_text.lower() if lang in {"en"} else lemma_text

    seen = _lookup_wordnet(target, wn_pos, omw_lang)
    if not seen:
        return []
    ordered = sorted(seen.items(), key=lambda item: _score_synonym(item[0], token.text, item[1]))
    candidates: list[str] = []
    for raw, _count in ordered[:8]:
        replacement = raw
        # English-specific morphology; skip for other langs
        if lang == "en" and getattr(token, "pos_", "") == "VERB":
            replacement = _simple_inflect(raw, getattr(token, "tag_", ""))
        if lang == "en":
            replacement = _apply_case(replacement, token.text)
        if replacement.lower() != token.text.lower() and " " not in replacement:
            candidates.append(replacement)
    return candidates


def _pos_of_interest(lang: str) -> set[str]:
    # For CJK / RTL we also allow NOUN since verbs/adjectives are sparser after
    # tokenization by blank pipelines. English keeps VERB+ADJ for stronger effect.
    if lang in {"en", "es", "fr", "de"}:
        return {"VERB", "ADJ"}
    return {"VERB", "ADJ", "NOUN"}


def _rewrite_with_synonyms(
    text: str, lang: str, rng: random.Random
) -> tuple[str, dict[str, Any]]:
    empty_stats = {"candidate_count": 0, "selected_count": 0, "replacements": [], "language": lang, "engine": "none"}
    nlp, kind = _load_spacy_for(lang)
    if nlp is None:
        logger.info("spaCy unavailable → skip synonyms for lang=%s", lang)
        return text, empty_stats
    if wn is None:
        return text, empty_stats
    if not LANG_OMW.get(lang):
        # OMW does not carry synonyms for this language → whitespace-only path
        return text, {**empty_stats, "engine": f"spacy-{kind}", "reason": "omw-unavailable"}

    doc = nlp(text)
    interest = _pos_of_interest(lang)

    frozen_indexes: set[int] = set()
    for token in doc:
        if getattr(token, "is_space", False) or getattr(token, "is_punct", False):
            frozen_indexes.add(token.i)
        elif getattr(token, "like_num", False):
            frozen_indexes.add(token.i)
        elif getattr(token, "ent_iob_", "O") != "O":
            frozen_indexes.add(token.i)
        elif getattr(token, "pos_", "") == "PROPN":
            frozen_indexes.add(token.i)

    candidates = []
    for token in doc:
        if token.i in frozen_indexes:
            continue
        pos = getattr(token, "pos_", "")
        if pos not in interest:
            # blank pipelines emit "" for POS; still allow alpha content tokens
            if kind != "blank":
                continue
            if not (token.is_alpha and len(token.text) > 2):
                continue
        if not token.text or token.text.lower() in STOPWORDS:
            continue
        if len(token.text) < 2:
            continue
        candidates.append(token)

    if not candidates:
        return text, {**empty_stats, "engine": f"spacy-{kind}"}

    lower_rate = 0.20
    upper_rate = 0.35
    desired = max(1, round(len(candidates) * rng.uniform(lower_rate, upper_rate)))
    rng.shuffle(candidates)

    replacements: dict[int, str] = {}
    applied: list[dict[str, str]] = []
    for token in candidates:
        try:
            options = _synonym_candidates(token, lang)
        except SynthIDRuntimeError:
            options = []
        except Exception:
            logger.debug("synonym lookup failed for %r", token.text, exc_info=True)
            options = []
        if not options:
            continue
        chosen = options[0]
        replacements[token.i] = chosen
        applied.append({"from": token.text, "to": chosen, "pos": getattr(token, "pos_", "")})
        if len(replacements) >= desired:
            break

    if not replacements:
        return text, {
            "candidate_count": len(candidates),
            "selected_count": 0,
            "replacements": [],
            "language": lang,
            "engine": f"spacy-{kind}",
        }

    pieces: list[str] = []
    cursor = 0
    for token in doc:
        replacement = replacements.get(token.i)
        if replacement is None:
            continue
        pieces.append(text[cursor:token.idx])
        pieces.append(replacement)
        cursor = token.idx + len(token.text)
    pieces.append(text[cursor:])
    return "".join(pieces), {
        "candidate_count": len(candidates),
        "selected_count": len(replacements),
        "replacements": applied,
        "language": lang,
        "engine": f"spacy-{kind}",
    }


def neutralize_synthid_text(
    text: str, seed: int | None = None, language: str | None = None
) -> dict[str, Any]:
    rng = random.Random(seed)
    lang = detect_text_language(text, hint=language)
    before = detect_synthid_likelihood(text)
    whitespace_text, whitespace_stats = _mix_whitespace(text, lang, rng)
    rewritten_text, synonym_stats = _rewrite_with_synonyms(whitespace_text, lang, rng)
    after = detect_synthid_likelihood(rewritten_text)
    return {
        "text": rewritten_text,
        "stats": {
            "whitespace": whitespace_stats,
            "synonyms": synonym_stats,
            "language": lang,
        },
        "language": lang,
        "before": before,
        "after": after,
    }


def is_textish_filename(name: str) -> bool:
    if "." not in name:
        return False
    extension = name.rsplit(".", 1)[-1].lower()
    return extension in TEXTISH_EXTENSIONS
