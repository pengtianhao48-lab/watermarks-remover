from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "service" / "scripts"))

import app as web_app  # noqa: E402
from synthid_text import detect_synthid_likelihood, neutralize_synthid_text  # noqa: E402

client = TestClient(web_app.app)


def test_detect_synthid_endpoint_returns_score_and_label():
    text = (
        "However, the careful analyst reviewed the detailed report and presented "
        "the final summary with consistent phrasing across every section."
    )
    response = client.post("/detect_synthid", data={"text": text})

    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["score"] <= 100
    assert body["label"] in {"low", "medium", "high"}
    assert "components" in body



def test_neutralize_synthid_text_preserves_entities_and_reduces_score():
    text = (
        "Alice reviewed the detailed report and approved the final design before "
        "she presented it in Paris in 2024."
    )

    result = neutralize_synthid_text(text, seed=11)

    assert "Alice" in result["text"]
    assert "Paris" in result["text"]
    assert "2024" in result["text"]
    assert result["stats"]["whitespace"]["changed_spaces"] >= 1
    assert result["stats"]["synonyms"]["selected_count"] >= 1
    assert result["after"]["score"] <= result["before"]["score"]



def test_mixed_unicode_spaces_lower_boundary_score():
    original = "This sentence uses ordinary spaces to keep every token neatly aligned for scoring."
    mixed = original.replace(" ", "\u00a0", 3)

    original_score = detect_synthid_likelihood(original)
    mixed_score = detect_synthid_likelihood(mixed)

    assert mixed_score["components"]["boundary_signal"] < original_score["components"]["boundary_signal"]
    assert mixed_score["score"] <= original_score["score"]
