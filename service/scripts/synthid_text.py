#!/usr/bin/env python3
"""Lightweight statistical SynthID-style text detector and neutralizer.

The real Claude / SynthID-family watermarking schemes are proprietary or require
heavy upstream checkpoints. This module provides an equivalent *statistical
likelihood* workflow suitable for deployment in this repo:

- detection: estimate how strongly the text still exhibits watermark-friendly
  token-boundary regularity and low-burstiness language patterns
- neutralization: perturb token boundaries with legal Unicode spaces and apply
  limited synonym rewrites on verbs/adjectives via spaCy + WordNet

It is intentionally conservative: scores are probabilistic, not proofs.
"""

from __future__ import annotations

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

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SPACE_RE = re.compile(r"[ \t\u00a0\u202f]+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
CONNECTOR_WORDS = {
    "however",
    "moreover",
    "therefore",
    "additionally",
    "furthermore",
    "overall",
    "indeed",
    "notably",
    "meanwhile",
    "consequently",
    "ultimately",
    "specifically",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "for", "from", "had", "has",
    "have", "he", "her", "his", "i", "if", "in", "into", "is", "it", "its", "of", "on", "or", "our", "she", "that",
    "the", "their", "them", "there", "they", "this", "to", "was", "we", "were", "will", "with", "you", "your",
}
WHITESPACE_VARIANTS = ("\u00a0", "\u202f")
TEXTISH_EXTENSIONS = {"txt", "md", "markdown", "html", "htm", "csv", "json", "xml", "yaml", "yml"}


class SynthIDRuntimeError(RuntimeError):
    """Raised when optional synthid-text dependencies are unavailable."""


@lru_cache(maxsize=1)
def _load_spacy_model():
    if spacy is None:
        raise SynthIDRuntimeError("spaCy is not installed")
    try:
        return spacy.load("en_core_web_sm", disable=["parser"])
    except OSError as exc:  # pragma: no cover - depends on runtime image
        raise SynthIDRuntimeError(
            "spaCy English model is missing; install en_core_web_sm"
        ) from exc


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokenize_words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


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


def _mix_whitespace(text: str, rng: random.Random) -> tuple[str, dict[str, int]]:
    indexes = set(_pick_space_indexes(text, rng))
    if not indexes:
        return text, {"nbsp": 0, "nnbsp": 0, "changed_spaces": 0}

    chars = list(text)
    counts = {"nbsp": 0, "nnbsp": 0, "changed_spaces": 0}
    for index in indexes:
        replacement = rng.choice(WHITESPACE_VARIANTS)
        chars[index] = replacement
        counts["changed_spaces"] += 1
        if replacement == "\u00a0":
            counts["nbsp"] += 1
        else:
            counts["nnbsp"] += 1
    return "".join(chars), counts


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
    return None


def _score_synonym(candidate: str, token_text: str, lemma_count: int) -> tuple[float, float, int]:
    length_gap = abs(len(candidate) - len(token_text))
    same_first = 1.0 if candidate[:1].lower() == token_text[:1].lower() else 0.0
    return (length_gap, -same_first, -lemma_count)


def _synonym_candidates(token) -> list[str]:
    if wn is None:
        raise SynthIDRuntimeError("nltk WordNet is not installed")
    if not token.lemma_:
        return []
    wn_pos = _wordnet_pos(token.pos_)
    if wn_pos is None:
        return []

    seen: dict[str, int] = {}
    target = token.lemma_.lower()
    for synset in wn.synsets(target, pos=wn_pos):
        for lemma in synset.lemmas():
            raw = lemma.name().replace("_", " ").strip().lower()
            if raw == target or raw == token.text.lower() or " " in raw or not raw.isalpha():
                continue
            seen[raw] = max(seen.get(raw, 0), int(lemma.count() or 0))
    ordered = sorted(seen.items(), key=lambda item: _score_synonym(item[0], token.text, item[1]))
    candidates = []
    for raw, _count in ordered[:8]:
        replacement = raw
        if token.pos_ == "VERB":
            replacement = _simple_inflect(raw, token.tag_)
        replacement = _apply_case(replacement, token.text)
        if replacement.lower() != token.text.lower():
            candidates.append(replacement)
    return candidates


def _rewrite_with_synonyms(text: str, rng: random.Random) -> tuple[str, dict[str, Any]]:
    nlp = _load_spacy_model()
    doc = nlp(text)

    frozen_indexes = {
        token.i
        for token in doc
        if token.ent_iob_ != "O" or token.pos_ == "PROPN" or token.like_num or token.is_punct or token.is_space
    }
    candidates = [
        token
        for token in doc
        if token.i not in frozen_indexes
        and token.pos_ in {"VERB", "ADJ"}
        and token.is_alpha
        and len(token.text) > 2
        and token.text.lower() not in STOPWORDS
    ]
    if not candidates:
        return text, {"candidate_count": 0, "selected_count": 0, "replacements": []}

    lower_rate = 0.30
    upper_rate = 0.40
    desired = max(1, round(len(candidates) * rng.uniform(lower_rate, upper_rate)))
    rng.shuffle(candidates)

    replacements: dict[int, str] = {}
    applied: list[dict[str, str]] = []
    for token in candidates:
        options = _synonym_candidates(token)
        if not options:
            continue
        chosen = options[0]
        replacements[token.i] = chosen
        applied.append({"from": token.text, "to": chosen, "pos": token.pos_})
        if len(replacements) >= desired:
            break

    if not replacements:
        return text, {"candidate_count": len(candidates), "selected_count": 0, "replacements": []}

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
    }


def neutralize_synthid_text(text: str, seed: int | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    before = detect_synthid_likelihood(text)
    whitespace_text, whitespace_stats = _mix_whitespace(text, rng)
    rewritten_text, synonym_stats = _rewrite_with_synonyms(whitespace_text, rng)
    after = detect_synthid_likelihood(rewritten_text)
    return {
        "text": rewritten_text,
        "stats": {
            "whitespace": whitespace_stats,
            "synonyms": synonym_stats,
        },
        "before": before,
        "after": after,
    }


def is_textish_filename(name: str) -> bool:
    if "." not in name:
        return False
    extension = name.rsplit(".", 1)[-1].lower()
    return extension in TEXTISH_EXTENSIONS
