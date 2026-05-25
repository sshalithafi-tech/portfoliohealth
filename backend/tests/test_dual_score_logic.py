"""Unit tests for the dual-score invariants.

What we guarantee:
  • equal_weighted_score == simple mean of the four pillar scores.
  • scores.overall       == equal_weighted_score (primary view contract).
  • contextual_score     uses the business-model weight table (+ optional
                         unambiguous priority boost) — distinct from the
                         equal-weighted baseline for any known business model.
  • PDF/UI labels for the two scores remain distinct, even when the values
    happen to be numerically identical.

Run with:  PYTHONPATH=/app/backend pytest -q /app/backend/tests/test_dual_score_logic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_service import (  # noqa: E402
    BUSINESS_MODEL_WEIGHTS,
    derive_contextual_weights,
    recompute_dual_scores,
)


def _make_report(business_model, scores, **extra):
    return {
        "business_model": business_model,
        "scores": dict(scores),
        **extra,
    }


def test_equal_weighted_is_simple_mean_regardless_of_llm_value():
    """Even if the LLM pushed the contextual value into the equal slot,
    we must recompute equal_weighted_score from the four pillar scores."""
    report = _make_report(
        "CETO",
        {"people": 4, "process": 3, "data": 2, "technology": 1},
        equal_weighted_score=2.7,  # WRONG — LLM put the contextual value here
        contextual_score=2.7,
    )
    out = recompute_dual_scores(report)
    expected_mean = round((4 + 3 + 2 + 1) / 4, 1)  # 2.5
    assert out["equal_weighted_score"] == expected_mean
    assert out["scores"]["overall"] == expected_mean


def test_contextual_recomputed_when_llm_duplicates_equal_for_known_bm():
    """If the LLM copied the equal-weighted value into contextual_score for a
    known business model, we must replace it with the real weighted sum."""
    report = _make_report(
        "ETO",  # 35/30/20/15
        {"people": 4, "process": 3, "data": 2, "technology": 1},
        contextual_score=2.5,  # WRONG — same as equal mean
    )
    out = recompute_dual_scores(report)
    # Contextual for ETO with these scores:
    #   4*0.35 + 3*0.30 + 2*0.20 + 1*0.15 = 1.40 + 0.90 + 0.40 + 0.15 = 2.85
    assert out["contextual_score"] == pytest.approx(2.85, abs=0.01)
    assert out["equal_weighted_score"] == 2.5


def test_contextual_recomputed_when_llm_omitted_it():
    report = _make_report(
        "Standard",  # 15/30/35/20
        {"people": 3, "process": 4, "data": 2, "technology": 3},
    )
    out = recompute_dual_scores(report)
    expected = 3 * 0.15 + 4 * 0.30 + 2 * 0.35 + 3 * 0.20  # 0.45+1.20+0.70+0.60=2.95
    assert out["contextual_score"] == pytest.approx(expected, abs=0.01)
    # Equal-weighted = (3+4+2+3)/4 = 3.0
    assert out["equal_weighted_score"] == 3.0


def test_scores_overall_equals_equal_weighted():
    report = _make_report(
        "CTO",
        {"people": 3, "process": 3, "data": 3, "technology": 3},
    )
    out = recompute_dual_scores(report)
    assert out["scores"]["overall"] == out["equal_weighted_score"]


def test_unknown_business_model_keeps_equal_baseline():
    """When the business model isn't in the canonical table and no LLM value
    is supplied, the contextual score may legitimately equal the equal-weighted
    score — but the *labels* surfaced in UI/PDF remain distinct (asserted in
    the layout tests). The function itself just leaves contextual untouched."""
    report = _make_report(
        None,
        {"people": 4, "process": 4, "data": 4, "technology": 4},
    )
    out = recompute_dual_scores(report)
    assert out["equal_weighted_score"] == 4.0
    # No business model → no contextual recomputation forced.
    assert out.get("contextual_score") in (None,)


def test_priority_boost_applied_only_when_unambiguous():
    base_report = _make_report(
        "CTO",  # base: 20/25/30/25
        {"people": 3, "process": 3, "data": 5, "technology": 3},
    )
    # Ambiguous priority must NOT boost.
    ambiguous = derive_contextual_weights({**base_report, "strategic_priority": "digital transformation"})
    assert ambiguous == pytest.approx(BUSINESS_MODEL_WEIGHTS["CTO"])

    # Clear "data" priority must boost the Data pillar.
    boosted = derive_contextual_weights({**base_report, "strategic_priority": "data quality"})
    assert boosted["data"] > BUSINESS_MODEL_WEIGHTS["CTO"]["data"]
    # Other pillars must shrink and weights must still sum to ~1.0.
    assert sum(boosted.values()) == pytest.approx(1.0, abs=0.001)


def test_all_business_models_distinct_from_equal_weights():
    """No canonical row should equal 25/25/25/25 — that would defeat the point
    of the contextual score."""
    equal = {p: 0.25 for p in ("people", "process", "data", "technology")}
    for bm, row in BUSINESS_MODEL_WEIGHTS.items():
        assert row != equal, f"{bm} row collapses to equal weights"


def test_pdf_and_dashboard_labels_distinct():
    """Smoke-check: the source files render distinct labels for the two scores,
    and never describe the contextual score as 'the same' as the equal one."""
    pdf_src = (Path(__file__).resolve().parents[1] / "pdf_builder.py").read_text()
    dash_src = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "pages" / "ReportPage.jsx"
    ).read_text()

    # Both files must reference both labels.
    for src, name in [(pdf_src, "pdf_builder.py"), (dash_src, "ReportPage.jsx")]:
        assert "Equal-Weighted" in src or "EQUAL-WEIGHTED" in src, f"{name} missing Equal-Weighted label"
        assert "Contextual" in src or "CONTEXTUAL" in src, f"{name} missing Contextual label"

    # The misleading "vs" wording must be gone from the PDF.
    assert "Equal-weighted vs contextual score" not in pdf_src
    # The dashboard must no longer claim equal-weight is unaffected by BM context.
    assert "Equal-weight scoring is not adjusted by business model" not in dash_src
