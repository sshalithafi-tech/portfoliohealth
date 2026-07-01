"""Ad-hoc verification of the Part 1-4 report fixes (run directly)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chat_service import normalise_report_weights, _parse_expected_gain
from pdf_builder import build_full_assessment_pdf, _ascii_arrows
from executive_summary_builder import build_executive_summary_pdf


def lumivex_report():
    return {
        "ready_for_report": True,
        "company_name": "Lumivex Photonics",
        "industry": "Photonics / Precision Optics",
        "respondent_name": "A. Virtanen",
        "respondent_role": "Head of Product",
        "business_model": "ETO",
        "strategic_priority": "Process",
        "scores": {"people": 3.5, "process": 3.0, "data": 4.0, "technology": 4.0, "overall": 9.9},
        "equal_weighted_score": 9.9,   # deliberately wrong -> must be recomputed
        "contextual_score": 3.48,
        "weights_raw": {"people": 5, "process": 5, "data": 5, "technology": 5},
        "level_names": {"people": "Managed", "process": "Defined", "data": "Managed",
                        "technology": "Managed", "overall": "Managed"},
        "pillar_interpretations": {p: f"{p} long form interpretation. " * 6 for p in
                                   ["people", "process", "data", "technology"]},
        "pillar_interpretation_short": {p: f"{p.title()} is solid but process-bound." for p in
                                        ["people", "process", "data", "technology"]},
        "bottleneck_pillar": "Process",
        "failure_pattern_name": "Salami Effect",
        "failure_pattern_narrative": "Portfolio creep accumulates via the Windchill -> SAP handoff. "
                                     "Product-change decisions are most at risk. Missing a gate.",
        "governance_signal_summary": [
            "No single owner for discontinuation decisions.",
            "Change reviews happen ad hoc, not on cadence.",
            "Finance is absent from portfolio gates.",
        ],
        "governance_observations": {p: "Some governance obs." for p in
                                    ["people", "process", "data", "technology"]},
        "governance_assessment": "Governance is fragmented across functions.",
        "decision_vulnerability_ratings": {"discontinuation": "High", "new_launch": "Critical",
                                           "product_change": "High", "portfolio_investment": "Medium"},
        "decision_vulnerability": "New launch governance is immature. System chain: Windchill -> SAP -> Salesforce.",
        "key_findings": ["Strong data foundation.", "Process cadence is weak."],
        "critical_gaps": [
            "No holistic data model linking master data to processes (Precondition 3: holistic data model).",
        ],
        "ninety_day_projection": {
            "score_current": 3.6,   # wrong / stale -> must be recomputed to overall
            "score_projected": 3.6,  # bug: no change
            "score_delta": 0.0,
            "bottleneck_level_current": "Developing",  # bug: mismatches level_names (Defined)
            "bottleneck_level_projected": "Developing",
            "what_becomes_possible": "Decisions arrive with evidence. Cadence closes the loop.",
            "comparable_outcome": "Reduced discontinuation cycle time.",
        },
        "roadmap": {
            "immediate": {"action_summary": "Stand up a monthly portfolio gate with a named owner.",
                          "actions": "1. Do X. 2. Do Y. 3. Do Z.",
                          "pillar_focus": "Process", "governance_milestone": "Gate live",
                          "management_required": "PMO Lead",
                          "expected_gain": "People: 3.5 -> 3.5 | Process: 3.0 -> 4.0 | Data: 4.0 -> 4.0 | Technology: 4.0 -> 4.0",
                          "timeframe": "0-3 months"},
            "short_term": {"action_summary": "Introduce Stage-Gate intake for launches.",
                           "actions": "Detail ...", "pillar_focus": "Process",
                           "governance_milestone": "Intake live", "management_required": "Head of Product",
                           "expected_gain": "People: 3.5 -> 4.0 | Process: 4.0 -> 4.5 | Data: 4.0 -> 4.5 | Technology: 4.0 -> 4.5",
                           "timeframe": "3-12 months"},
            "strategic": {"action_summary": "Embed predictive portfolio analytics.",
                          "actions": "Detail ...", "pillar_focus": "Data",
                          "governance_milestone": "Analytics live", "management_required": "CIO",
                          "expected_gain": "People: 4.0 -> 4.5 | Process: 4.5 -> 4.5 | Data: 4.5 -> 5.0 | Technology: 4.5 -> 5.0",
                          "timeframe": "12+ months"},
        },
        "assessment_reliability": {"confidence": "Medium", "factors": []},
        "benchmark_context": "Peer ETO firms sit around 3.2.",
        "consultant_note": "A direct take.",
        "closing_statement": "Thank you.",
    }


def main():
    r = normalise_report_weights(lumivex_report())

    # --- Part 1B: overall consistency ---
    eq = r["equal_weighted_score"]
    assert eq == round((3.5 + 3.0 + 4.0 + 4.0) / 4.0, 1) == 3.6, eq
    assert r["scores"]["overall"] == eq, r["scores"]["overall"]

    # --- Part 1C: projection derived from Phase-1 gain + overall ---
    proj = r["ninety_day_projection"]
    assert proj["score_current"] == eq, ("score_current", proj["score_current"])
    # Phase-1 end scores: 3.5, 4.0, 4.0, 4.0 -> avg 3.875 -> round 3.9 (delta 0.3 <= 0.8)
    assert proj["score_projected"] == 3.9, ("score_projected", proj["score_projected"])
    assert proj["score_delta"] == round(3.9 - 3.6, 1), ("delta", proj["score_delta"])
    # bottleneck level current must match authoritative level_names (Defined), not "Developing"
    assert proj["bottleneck_level_current"] == "Defined", proj["bottleneck_level_current"]
    # Process 3.0 (Defined) -> 4.0 (Managed) = +1 band => projected Managed
    assert proj["bottleneck_level_projected"] == "Managed", proj["bottleneck_level_projected"]
    print("Projection:", proj["score_current"], "->", proj["score_projected"],
          "| bottleneck", proj["bottleneck_level_current"], "->", proj["bottleneck_level_projected"])

    # --- parser handles both -> and unicode arrow ---
    g = _parse_expected_gain("People: 2.0 \u2192 2.5 | Process: 1.5 -> 2.5")
    assert g["people"] == (2.0, 2.5) and g["process"] == (1.5, 2.5), g

    # --- Part 1A: arrow sanitiser ---
    assert _ascii_arrows("Windchill \u2192 SAP \u2192 Salesforce") == "Windchill -> SAP -> Salesforce"

    # --- PDFs build without error ---
    full = build_full_assessment_pdf({"report": r, "company_name": "Lumivex Photonics",
                                      "company_industry": "Photonics", "respondent_name": "A. Virtanen",
                                      "respondent_role": "Head of Product", "created_at": "2026-07-01"})
    ex = build_executive_summary_pdf({"report": r, "company_name": "Lumivex Photonics",
                                      "company_industry": "Photonics", "respondent_name": "A. Virtanen",
                                      "respondent_role": "Head of Product", "created_at": "2026-07-01"})
    fb, xb = full.getvalue(), ex.getvalue()
    assert fb[:4] == b"%PDF" and len(fb) > 5000, len(fb)
    assert xb[:4] == b"%PDF" and len(xb) > 3000, len(xb)
    print("Full PDF bytes:", len(fb), "| Exec PDF bytes:", len(xb))

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
