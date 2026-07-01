"""
Executive Summary Report — a 4-page condensed alternative to the full 15-page
consultant report. Consumes the extended JSON schema (failure pattern,
90-day projection, first action, financial consequence) added in Part 1
of the PPDT Summary Report track.

Design goals:
  • 100% additive — nothing here mutates or shortens the full report path
    in `pdf_builder.py`. Both PDFs render from the same `assessment.report`.
  • Backwards-compatible — if any new field is missing (older assessments
    saved before the schema extension), sensible defaults render instead
    of raising.
  • Same brand tokens as the full report so the two PDFs feel like one
    product family.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    SimpleDocTemplate,
    PageBreak,
    KeepTogether,
    HRFlowable,
)

from pdf_builder import (
    NAVY,
    NAVY_DEEP,
    GOLD,
    GOLD_BG,
    LINE_LIGHT,
    TEXT_DARK,
    TEXT_MUTED,
    band_color,
    score_band,
    make_report_styles,
    BAND_COLORS_HEX,
    _page_decoration,
)


# ============================================================
# Small helpers
# ============================================================

DIMENSIONS = ("people", "process", "data", "technology")

FAILURE_PATTERNS = {
    "Silent Knowledge Risk",
    "Salami Effect",
    "Business Case Validity Risk",
    "Hidden Maintenance Cost",
    "Technology Misattribution Risk",
}

PRECONDITION_LABELS = {
    "p1_product_structure": "P1 · Product structure",
    "p2_product_classification": "P2 · Product classification",
    "p3_data_model": "P3 · Data model",
    "p4_data_governance": "P4 · Data governance",
    "p5_business_it": "P5 · Business IT",
}

STATUS_COLORS = {
    "met": colors.HexColor("#10B981"),
    "partial": colors.HexColor("#F59E0B"),
    "not met": colors.HexColor("#DC2626"),
}


def _pillar_from_dbi(report: dict) -> str:
    dbi = (report or {}).get("decision_bottleneck_index") or {}
    if dbi.get("pillar"):
        return str(dbi["pillar"])
    bp = (report or {}).get("bottleneck_pillar") or ""
    return str(bp).lower() if bp else "process"


def _fallback_failure_pattern(pillar: str, report: dict) -> str:
    """When the LLM did not emit `failure_pattern_name`, derive a sensible
    default from the bottleneck pillar so the summary still renders."""
    scores = (report or {}).get("scores") or {}
    if pillar == "people":
        return "Silent Knowledge Risk"
    if pillar == "process":
        return "Salami Effect"
    if pillar == "technology":
        return "Technology Misattribution Risk"
    # Data — pick between Business Case Validity Risk and Hidden Maintenance Cost
    if float(scores.get("process", 0) or 0) >= 3.0:
        return "Business Case Validity Risk"
    return "Hidden Maintenance Cost"


def _capitalise_level(name: str) -> str:
    n = (name or "").strip().title()
    return n or "Developing"


def _pillar_label(key: str) -> str:
    return {"people": "People", "process": "Process", "data": "Data", "technology": "Technology"}.get(
        key, key.capitalize()
    )


# ============================================================
# Styles
# ============================================================

def _styles():
    base = make_report_styles()
    body = base["body"]
    from reportlab.lib.styles import ParagraphStyle
    return {
        **base,
        "h1": ParagraphStyle(
            "SumH1", parent=body, fontSize=22, leading=26, textColor=NAVY,
            fontName="Helvetica-Bold", spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "SumH2", parent=body, fontSize=14, leading=18, textColor=NAVY,
            fontName="Helvetica-Bold", spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "SumH3", parent=body, fontSize=11, leading=14, textColor=NAVY_DEEP,
            fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "eyebrow": ParagraphStyle(
            "SumEyebrow", parent=body, fontSize=8, leading=10,
            textColor=colors.HexColor("#0891B2"), fontName="Helvetica-Bold",
            spaceAfter=2, spaceBefore=0,
        ),
        "lead": ParagraphStyle(
            "SumLead", parent=body, fontSize=10.5, leading=15,
            textColor=TEXT_DARK, spaceAfter=8,
        ),
        "note": ParagraphStyle(
            "SumNote", parent=body, fontSize=8.5, leading=11,
            textColor=TEXT_MUTED, spaceAfter=4,
        ),
        "cta": ParagraphStyle(
            "SumCTA", parent=body, fontSize=9.5, leading=13,
            textColor=NAVY, backColor=GOLD_BG, borderPadding=12,
            borderColor=GOLD, borderWidth=0.7, spaceBefore=8, spaceAfter=8,
        ),
    }


# ============================================================
# PAGE 1 — THE VERDICT
# ============================================================

def _horizontal_score_bars(scores: dict, bottleneck: str):
    """Return a Table that draws a 4-row horizontal-bar visualisation of
    pillar scores. The bottleneck row is tinted amber and labelled."""
    rows = []
    max_bar_width = 8 * cm
    for dim in DIMENSIONS:
        s = float(scores.get(dim, 0) or 0)
        bar_w = max(0.05 * cm, min(max_bar_width, (s / 5.0) * max_bar_width))
        c = band_color(s)
        label = _pillar_label(dim)
        if dim == bottleneck:
            label = f"<b>{label}</b>  <font size='7' color='#DC2626'><b>BOTTLENECK</b></font>"
        # Build a tiny inner table for the bar so it has a coloured fill
        bar = Table(
            [[""]], colWidths=[bar_w], rowHeights=[0.4 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c),
                ("BOX", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ])
        )
        rows.append([Paragraph(label, _styles()["body"]), bar, Paragraph(f"<b>{s:.1f}</b> / 5.0", _styles()["body"])])
    return Table(
        rows, colWidths=[4.2 * cm, 8.4 * cm, 3.0 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, LINE_LIGHT),
        ])
    )


def _build_page1(story, report, styles, assessment):
    """PAGE 1 — THE VERDICT."""
    company_name = assessment.get("company_name") or report.get("company_name") or "—"
    scores = report.get("scores") or {}
    overall = float(scores.get("overall") or report.get("equal_weighted_score") or 0)
    bottleneck = _pillar_from_dbi(report)
    level_names = report.get("level_names") or {}
    bottleneck_level = _capitalise_level(level_names.get(bottleneck, ""))
    if not bottleneck_level:
        bottleneck_level = "Developing"

    # Header
    story.append(Paragraph("EXECUTIVE SUMMARY", styles["eyebrow"]))
    story.append(Paragraph(f"{company_name}", styles["h1"]))
    story.append(Paragraph("Portfolio Decision Capability — 4-Page Verdict", styles["h3"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceBefore=6, spaceAfter=10))

    # Score visual
    story.append(Paragraph("PILLAR SCORES", styles["eyebrow"]))
    story.append(_horizontal_score_bars(scores, bottleneck))
    story.append(Spacer(0, 6))

    # DBI callout
    dbi = report.get("decision_bottleneck_index") or {}
    if dbi.get("pillar"):
        gap = dbi.get("gap", 0.0)
        sign = "+" if gap >= 0 else ""
        direction = dbi.get("direction", "").replace("-", " ")
        callout = (
            f"<b>Overall {overall:.2f} / 5.0</b> &nbsp;·&nbsp; "
            f"<b>DBI</b> {_pillar_label(dbi['pillar'])} "
            f"<font color='#94A3B8'>({sign}{float(gap):.2f}, {direction})</font>"
        )
    else:
        callout = f"<b>Overall {overall:.2f} / 5.0</b>"
    story.append(Paragraph(callout, styles["lead"]))
    story.append(Spacer(0, 4))

    # One-line verdict
    verdict = (
        f"Your portfolio decision capability is operating at "
        f"<b>{bottleneck_level}</b>. Your weakest capability is "
        f"<b>{_pillar_label(bottleneck)}</b>."
    )
    story.append(Paragraph(verdict, styles["lead"]))
    story.append(HRFlowable(width="100%", thickness=0.4, color=LINE_LIGHT, spaceBefore=6, spaceAfter=10))

    # Failure pattern
    fp_name = report.get("failure_pattern_name") or _fallback_failure_pattern(bottleneck, report)
    fp_narrative = report.get("failure_pattern_narrative") or (
        f"The {bottleneck} pillar is the binding constraint on portfolio decisions today. "
        f"Decisions that depend on this pillar arrive with insufficient evidence and stall or drift. "
        f"The organisation is missing the operational capability to close this loop consistently."
    )
    story.append(Paragraph("FAILURE PATTERN", styles["eyebrow"]))
    story.append(Paragraph(fp_name, styles["h2"]))
    story.append(Paragraph(fp_narrative, styles["lead"]))

    # Financial consequence (single framed sentence)
    fc = report.get("financial_consequence") or {}
    cost_cat = fc.get("cost_category") or ""
    metric_framing = fc.get("metric_framing") or ""
    if cost_cat or metric_framing:
        line = ""
        if cost_cat:
            line += f"<b>Cost category:</b> {cost_cat}. "
        if metric_framing:
            line += metric_framing
        story.append(Paragraph(line, styles["cta"]))

    story.append(PageBreak())


# ============================================================
# PAGE 2 — YOUR #1 ACTION
# ============================================================

def _preconditions_row(preconditions: dict, styles):
    """Small 5-cell strip showing precondition status."""
    cells = []
    for key, label in PRECONDITION_LABELS.items():
        status = (preconditions.get(key) or "partial").lower()
        c = STATUS_COLORS.get(status, STATUS_COLORS["partial"])
        pill = Paragraph(
            f"<font color='{c.hexval()}'><b>{status.upper()}</b></font>",
            styles["note"],
        )
        cells.append([Paragraph(label, styles["note"]), pill])
    # Render as one row of 5 mini stacks
    inner_rows = [[c[0] for c in cells], [c[1] for c in cells]]
    tbl = Table(
        inner_rows, colWidths=[3.1 * cm] * 5,
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOX", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
        ]),
    )
    return tbl


def _build_page2(story, report, styles):
    """PAGE 2 — YOUR #1 ACTION."""
    first_action = report.get("first_action") or {}
    headline = first_action.get("headline") or "Establish a monthly portfolio review with a named owner"
    description = first_action.get("description") or (
        "Convene the Head of Product, PMO and Finance monthly to review the active-product list, "
        "using the current maturity assessment as the baseline evidence pack."
    )
    expected_outcome = first_action.get("expected_outcome") or (
        "A traceable go/kill/hold decision on every active product every 30 days."
    )
    who_owns_it = first_action.get("who_owns_it") or "Head of Product + PMO"
    time_to_implement = first_action.get("time_to_implement") or "2–4 weeks"
    preconditions = first_action.get("preconditions_met") or {}

    story.append(Paragraph("YOUR #1 ACTION", styles["eyebrow"]))
    story.append(Paragraph(headline, styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceBefore=6, spaceAfter=10))

    story.append(Paragraph("What to do", styles["h3"]))
    story.append(Paragraph(description, styles["lead"]))

    # Owner + timing card
    meta_tbl = Table(
        [[
            Paragraph("<b>Who owns it</b><br/>" + who_owns_it, styles["body"]),
            Paragraph("<b>Time to implement</b><br/>" + time_to_implement, styles["body"]),
            Paragraph("<b>Expected outcome</b><br/>" + expected_outcome, styles["body"]),
        ]],
        colWidths=[5.2 * cm, 4.5 * cm, 6.0 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GOLD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, GOLD),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    )
    story.append(meta_tbl)
    story.append(Spacer(0, 12))

    # Preconditions status
    story.append(Paragraph("PRECONDITIONS", styles["eyebrow"]))
    story.append(_preconditions_row(preconditions, styles))
    story.append(Spacer(0, 12))

    # Governance signal (2 gaps + 1 positive)
    story.append(Paragraph("GOVERNANCE SIGNAL", styles["eyebrow"]))
    critical_gaps = report.get("critical_gaps") or []
    key_findings = report.get("key_findings") or []
    gaps = [g for g in critical_gaps[:2] if g]
    positive = next((f for f in key_findings if isinstance(f, str) and any(
        w in f.lower() for w in ("strong", "clear", "established", "documented", "consistent")
    )), None)
    bullets = []
    for g in gaps:
        bullets.append(f"<font color='#DC2626'>•</font> {g}")
    if positive:
        bullets.append(f"<font color='#10B981'>•</font> {positive}")
    for b in bullets:
        story.append(Paragraph(b, styles["body"]))
    if not bullets:
        story.append(Paragraph(
            "Governance signals will populate once the assessment conversation is complete.",
            styles["note"],
        ))
    story.append(Spacer(0, 12))

    # 90-day projection box
    ninety = report.get("ninety_day_projection") or {}
    sc = float(ninety.get("score_current") or report.get("equal_weighted_score") or (report.get("scores") or {}).get("overall") or 0)
    sp = float(ninety.get("score_projected") or sc)
    sd = float(ninety.get("score_delta") or (sp - sc))
    bl_c = _capitalise_level(ninety.get("bottleneck_level_current") or "")
    bl_p = _capitalise_level(ninety.get("bottleneck_level_projected") or "")
    possible = ninety.get("what_becomes_possible") or (
        "Portfolio decisions will begin arriving with evidence rather than opinion. "
        "Leadership can close the loop on discontinuation and change decisions inside a monthly cadence."
    )
    comparable = ninety.get("comparable_outcome") or "Reduced portfolio-decision cycle time (Hannila, 2019)."

    proj_tbl = Table(
        [[
            Paragraph(
                f"<font size='9' color='#0891B2'><b>90-DAY PROJECTION</b></font><br/><br/>"
                f"<b>Score:</b> {sc:.1f} → <b>{sp:.1f}</b> "
                f"<font color='#94A3B8'>(Δ {sd:+.1f})</font><br/>"
                f"<b>Bottleneck level:</b> {bl_c} → {bl_p}<br/>",
                styles["body"],
            ),
            Paragraph(
                f"<b>What becomes possible:</b><br/>{possible}<br/><br/>"
                f"<i>Comparable outcome:</i> {comparable}",
                styles["body"],
            ),
        ]],
        colWidths=[6.0 * cm, 9.7 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]),
    )
    # Rebuild the left cell with white text for contrast on navy
    story.append(proj_tbl)
    story.append(PageBreak())


# ============================================================
# PAGE 3 — 90-DAY ROADMAP
# ============================================================

RELABEL = [
    ("immediate",   "This Month",   "0–30 days"),
    ("short_term",  "This Quarter", "30–90 days"),
    ("strategic",   "This Year",    "90–365 days"),
]


def _build_page3(story, report, styles):
    """PAGE 3 — 90-DAY ROADMAP (relabelled)."""
    roadmap = report.get("roadmap") or {}
    story.append(Paragraph("YOUR ROADMAP", styles["eyebrow"]))
    story.append(Paragraph("Three moves. Same team. One quarter.", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceBefore=6, spaceAfter=10))

    for phase_key, label, window in RELABEL:
        phase = roadmap.get(phase_key) or {}
        actions = phase.get("actions") or "—"
        pillar_focus = phase.get("pillar_focus") or "—"
        owner = phase.get("management_required") or "—"
        milestone = phase.get("governance_milestone") or ""
        expected_gain = phase.get("expected_gain") or ""

        card = Table(
            [[
                Paragraph(
                    f"<font size='8' color='#0891B2'><b>{label.upper()}</b></font>"
                    f"<br/><font size='7' color='#94A3B8'>{window}</font>",
                    styles["body"],
                ),
                Paragraph(
                    f"<b>Action:</b> {actions}<br/>"
                    f"<b>Who owns it:</b> {owner}<br/>"
                    f"<b>What it unlocks:</b> {milestone or pillar_focus}",
                    styles["body"],
                ),
            ]],
            colWidths=[3.6 * cm, 12.2 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), GOLD_BG),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]),
        )
        story.append(KeepTogether(card))
        if expected_gain:
            story.append(Paragraph(f"<i>Expected gain — {expected_gain}</i>", styles["note"]))
        story.append(Spacer(0, 8))

    story.append(PageBreak())


# ============================================================
# PAGE 4 — FULL SCORECARD REFERENCE
# ============================================================

def _build_page4(story, report, styles):
    """PAGE 4 — FULL SCORECARD REFERENCE (compressed)."""
    scores = report.get("scores") or {}
    level_names = report.get("level_names") or {}
    interps = report.get("pillar_interpretations") or {}
    summaries = report.get("dimension_summaries") or {}
    reliability = (report.get("assessment_reliability") or {}).get("confidence") or "—"
    mgmt = report.get("management_commitment") or "—"
    dvr = report.get("decision_vulnerability_ratings") or {}

    story.append(Paragraph("SCORECARD REFERENCE", styles["eyebrow"]))
    story.append(Paragraph("Full detail — for the record", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceBefore=6, spaceAfter=10))

    # Compressed pillar table
    rows = [["Pillar", "Score", "Level", "Two-line interpretation"]]
    for dim in DIMENSIONS:
        s = float(scores.get(dim, 0) or 0)
        lvl = _capitalise_level(level_names.get(dim, ""))
        interp = (interps.get(dim) or summaries.get(dim) or "").strip()
        # Truncate to ~180 chars for "2-line" feel
        if len(interp) > 200:
            cut = interp[:200]
            interp = cut[: cut.rfind(" ")] + "…"
        band = BAND_COLORS_HEX[score_band(s)]
        rows.append([
            Paragraph(f"<b>{_pillar_label(dim)}</b>", styles["body"]),
            Paragraph(f"<font color='{band}'><b>{s:.1f}</b></font>", styles["body"]),
            Paragraph(f"<font color='{band}'>{lvl}</font>", styles["body"]),
            Paragraph(interp or "—", styles["body"]),
        ])
    tbl = Table(
        rows, colWidths=[2.6 * cm, 1.4 * cm, 2.6 * cm, 9.0 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE_LIGHT),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]),
    )
    story.append(tbl)
    story.append(Spacer(0, 10))

    # Management commitment + assessment reliability line
    story.append(Paragraph(
        f"<b>Management commitment:</b> {mgmt}  &nbsp;·&nbsp;  "
        f"<b>Assessment reliability:</b> {reliability}",
        styles["body"],
    ))
    story.append(Spacer(0, 10))

    # Decision-type vulnerability table
    story.append(Paragraph("DECISION-TYPE VULNERABILITY", styles["eyebrow"]))
    dvr_rows = [
        ["Discontinuation", dvr.get("discontinuation", "—")],
        ["New product launch", dvr.get("new_launch", "—")],
        ["Product change", dvr.get("product_change", "—")],
        ["Portfolio investment", dvr.get("portfolio_investment", "—")],
    ]
    dvr_tbl = Table(
        [["Decision type", "Vulnerability"]] + dvr_rows,
        colWidths=[7 * cm, 4 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE_LIGHT),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    )
    story.append(dvr_tbl)
    story.append(Spacer(0, 12))
    story.append(Paragraph(
        "This Executive Summary is a companion to the full 15-page PortfolioHealth report. "
        "Detailed methodology, weighted-score calculation tables, and academic citations are exclusive "
        "to the Full Report.",
        styles["note"],
    ))


# ============================================================
# Public entry point
# ============================================================

def build_executive_summary_pdf(assessment: dict) -> BytesIO:
    """Assemble the 4-page Executive Summary PDF into an in-memory buffer."""
    report = assessment.get("report") or {}
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title="PortfolioHealth — Executive Summary",
    )
    styles = _styles()
    story: list[Any] = []

    _build_page1(story, report, styles, assessment)
    _build_page2(story, report, styles)
    _build_page3(story, report, styles)
    _build_page4(story, report, styles)

    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    buffer.seek(0)
    return buffer
