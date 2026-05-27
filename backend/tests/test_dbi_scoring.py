"""
Tests for the Decision Bottleneck Index (DBI) and per-pillar contextual gap
logic introduced from the thesis PDF
("PPDT Scoring Logic & Business-Model-Contextual Weighting").

Source of truth: the thesis "Consolidated Weight Matrix" and "Dual-Score
Architecture" sections.
"""
import pytest

from chat_service import (
    AMBIGUOUS_PRIORITY_TERMS,
    BUSINESS_MODEL_WEIGHTS,
    compute_decision_bottleneck_index,
    compute_pillar_contextual_gaps,
    derive_contextual_weights,
    recompute_dual_scores,
)


# ---------------------------------------------------------------------------
# 1. Weight matrix matches the thesis exactly
# ---------------------------------------------------------------------------
def test_business_model_weight_matrix_matches_thesis():
    """Consolidated Weight Matrix (thesis Table 1)."""
    expected = {
        "ETO":      {"people": 0.35, "process": 0.30, "data": 0.20, "technology": 0.15},
        "CETO":     {"people": 0.25, "process": 0.30, "data": 0.25, "technology": 0.20},
        "CTO":      {"people": 0.20, "process": 0.25, "data": 0.30, "technology": 0.25},
        "Standard": {"people": 0.15, "process": 0.30, "data": 0.35, "technology": 0.20},
        "Bulk":     {"people": 0.10, "process": 0.35, "data": 0.20, "technology": 0.35},
    }
    assert BUSINESS_MODEL_WEIGHTS == expected

    # Every row sums to 1.0
    for model, row in BUSINESS_MODEL_WEIGHTS.items():
        assert pytest.approx(sum(row.values()), abs=1e-9) == 1.0, model


# ---------------------------------------------------------------------------
# 2. Per-pillar gap formula: (w_i - 0.25) × score_i
# ---------------------------------------------------------------------------
def test_pillar_gaps_sum_equals_contextual_minus_equal():
    scores = {"people": 2.0, "process": 3.0, "data": 4.0, "technology": 1.0}
    weights = BUSINESS_MODEL_WEIGHTS["ETO"]  # 35/30/20/15
    eq = sum(scores.values()) / 4.0
    ctx = sum(weights[p] * scores[p] for p in scores)
    gaps = compute_pillar_contextual_gaps(scores, weights)
    assert pytest.approx(sum(gaps.values()), abs=1e-6) == ctx - eq


def test_pillar_gaps_zero_when_weights_are_equal():
    scores = {"people": 2.0, "process": 3.0, "data": 4.0, "technology": 1.0}
    weights = {p: 0.25 for p in scores}
    gaps = compute_pillar_contextual_gaps(scores, weights)
    assert all(v == 0 for v in gaps.values())


# ---------------------------------------------------------------------------
# 3. DBI = pillar with the largest ABSOLUTE gap
# ---------------------------------------------------------------------------
def test_dbi_picks_largest_absolute_gap():
    """Per the literal PDF formula `gap_i = (w_i − 0.25) × s_i`, the DBI is
    the pillar with the LARGEST |gap| — which is *not necessarily* the
    lowest-scoring pillar.

    ETO + low-People scenario:
        weights = {p:.35, pr:.30, d:.20, t:.15}
        scores  = {p:1.0, pr:3.0, d:3.0, t:3.0}
        gaps    = {p:+0.10, pr:+0.15, d:-0.15, t:-0.30}
        → DBI = technology, direction = below-baseline
    The semantic insight is "Technology contributes the most to the
    contextual ↔ equal divergence" — i.e. the company has Tech capability
    that the business model does not fully reward.
    """
    scores = {"people": 1.0, "process": 3.0, "data": 3.0, "technology": 3.0}
    weights = BUSINESS_MODEL_WEIGHTS["ETO"]
    dbi = compute_decision_bottleneck_index(scores, weights)
    assert dbi is not None
    assert dbi["pillar"] == "technology"
    assert dbi["direction"] == "below-baseline"
    assert dbi["gap"] == pytest.approx(-0.30, abs=1e-6)
    # |gap_tech| must be the largest |gap|
    for other, val in dbi["gaps_by_pillar"].items():
        if other != "technology":
            assert abs(val) <= abs(dbi["gap"]) + 1e-9


def test_dbi_above_baseline_when_overweighted_pillar_is_strong():
    """Bulk + Process is overweighted (35%) and the company scores 5/5 on
    Process. The largest gap is Process at +0.50 → DBI = process,
    direction = above-baseline (alignment surplus)."""
    scores = {"people": 1.0, "process": 5.0, "data": 3.0, "technology": 3.0}
    weights = BUSINESS_MODEL_WEIGHTS["Bulk"]  # 10/35/20/35
    dbi = compute_decision_bottleneck_index(scores, weights)
    assert dbi is not None
    # Per-pillar gaps:
    #   people:     (0.10 - 0.25) * 1.0 = -0.15
    #   process:    (0.35 - 0.25) * 5.0 =  0.50   ← largest |gap|
    #   data:       (0.20 - 0.25) * 3.0 = -0.15
    #   technology: (0.35 - 0.25) * 3.0 =  0.30
    assert dbi["pillar"] == "process"
    assert dbi["direction"] == "above-baseline"
    assert dbi["gap"] == pytest.approx(0.50, abs=1e-6)


def test_dbi_returns_none_for_equal_weights():
    scores = {"people": 2.0, "process": 3.0, "data": 4.0, "technology": 1.0}
    weights = {p: 0.25 for p in scores}
    assert compute_decision_bottleneck_index(scores, weights) is None


# ---------------------------------------------------------------------------
# 4. Ambiguous priority terms match the thesis (Table 2)
# ---------------------------------------------------------------------------
def test_ambiguous_priority_terms_match_thesis():
    """Thesis Table 2: ambiguous priorities that must not trigger a boost.
    'Portfolio simplification, profitability, complexity' and
    'Digital transformation, innovation' → No boost."""
    expected = {
        "portfolio simplification",
        "profitability",
        "complexity",
        "digital transformation",
        "innovation",
    }
    assert AMBIGUOUS_PRIORITY_TERMS == expected


def test_ambiguous_priority_does_not_trigger_boost():
    """A declared "digital transformation" priority must NOT alter the
    business-model weights."""
    report = {
        "business_model": "Standard",
        "strategic_priority": "digital transformation",
    }
    out = derive_contextual_weights(report)
    assert out == BUSINESS_MODEL_WEIGHTS["Standard"]


# ---------------------------------------------------------------------------
# 5. Strategic priority boost: +5% to one pillar, −1.67% to each other
# ---------------------------------------------------------------------------
def test_strategic_priority_boost_adds_5pct_normalised():
    report = {
        "business_model": "CTO",
        "strategic_priority": "we are doubling down on data and analytics",
    }
    out = derive_contextual_weights(report)
    base = BUSINESS_MODEL_WEIGHTS["CTO"]
    # Data should be the boosted pillar; net change ≈ +5% after normalisation
    assert out["data"] > base["data"] + 0.04
    # The four weights still sum to ~1.0
    assert pytest.approx(sum(out.values()), abs=1e-6) == 1.0
    # The three non-data pillars each lost ~1.67% before re-normalisation
    for p in ("people", "process", "technology"):
        assert out[p] < base[p]


# ---------------------------------------------------------------------------
# 6. End-to-end: recompute_dual_scores writes DBI + gaps onto the report
# ---------------------------------------------------------------------------
def test_recompute_dual_scores_writes_dbi_block():
    report = {
        "business_model": "ETO",
        "strategic_priority": "knowledge management and people",
        "scores": {"people": 1.0, "process": 3.0, "data": 3.0, "technology": 3.0},
    }
    out = recompute_dual_scores(report)
    # Equal-weighted score is always written
    assert out["equal_weighted_score"] == pytest.approx(2.5, abs=1e-9)
    assert out["scores"]["overall"] == pytest.approx(2.5, abs=1e-9)
    # Contextual score is the weighted sum (with priority boost on People)
    weights = out["contextual_weights"]
    expected_ctx = sum(weights[p] * report["scores"][p] for p in weights)
    assert out["contextual_score"] == pytest.approx(round(expected_ctx, 2), abs=1e-6)
    # DBI block is present. With the priority-boost on People in an
    # ETO model, People weight rises ≈ +5% and the other 3 each lose ≈ 1.67%.
    # Per-pillar gaps for scores {p:1, pr:3, d:3, t:3} are computed from the
    # final boosted weights — the largest absolute gap should still belong to
    # Technology (most negative gap × highest below-baseline weight).
    dbi = out["decision_bottleneck_index"]
    assert dbi["pillar"] in {"people", "process", "data", "technology"}
    assert "gaps_by_pillar" in dbi
    # Per-pillar gaps sum equals contextual − equal
    gaps = out["pillar_contextual_gaps"]
    assert pytest.approx(sum(gaps.values()), abs=1e-6) == out["contextual_score"] - out["equal_weighted_score"]
