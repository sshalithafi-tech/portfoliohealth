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

import math
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
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Polygon

from pdf_builder import (
    NAVY,
    NAVY_DEEP,
    GOLD,
    GOLD_BG,
    GOLD_HILITE,
    SCORE_CYAN,
    ROW_ALT,
    LINE_LIGHT,
    TEXT_DARK,
    TEXT_MUTED,
    band_color,
    score_band,
    make_report_styles,
    BAND_COLORS_HEX,
    sanitized_assessment,
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

# Light tint backgrounds for the status "cards" (Page 2 preconditions strip)
STATUS_BG = {
    "met": colors.HexColor("#ECFDF5"),
    "partial": colors.HexColor("#FFFBEB"),
    "not met": colors.HexColor("#FEF2F2"),
}

# Decision-vulnerability badge palette (Page 4) — schema values are always
# exactly one of Low | Medium | High | Critical (see report_sections.py).
VULN_COLORS = {
    "low": (colors.HexColor("#10B981"), colors.HexColor("#ECFDF5")),
    "medium": (colors.HexColor("#F59E0B"), colors.HexColor("#FFFBEB")),
    "high": (colors.HexColor("#DC2626"), colors.HexColor("#FEF2F2")),
    "critical": (colors.HexColor("#991B1B"), colors.HexColor("#FEE2E2")),
}

# Full available content width on the A4 page (margins set in
# build_executive_summary_pdf: 1.5cm left/right) — every table/drawing
# below is sized to stay within this so nothing ever clips or overlaps.
CONTENT_WIDTH = A4[0] - 2 * 1.5 * cm  # ≈ 18.0cm


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


def _first_sentence(text: str, max_chars: int = 220) -> str:
    """Return the first sentence of `text` (fallback when a short field is
    missing). Keeps the Executive Summary concise without the full detail."""
    t = (text or "").strip()
    if not t:
        return ""
    import re as _re
    m = _re.search(r"(.+?[.!?])(\s|$)", t)
    sentence = m.group(1).strip() if m else t
    if len(sentence) > max_chars:
        cut = sentence[:max_chars]
        sentence = cut[: cut.rfind(" ")].rstrip() + "\u2026"
    return sentence


# ============================================================
# Styles
# ============================================================

def _styles():
    base = make_report_styles()
    body = base["body"]
    from reportlab.lib.styles import ParagraphStyle, TA_CENTER, TA_RIGHT
    return {
        **base,
        "h1": ParagraphStyle(
            "SumH1", parent=body, fontSize=21, leading=25, textColor=NAVY,
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
            "SumLead", parent=body, fontSize=10.5, leading=15.5,
            textColor=TEXT_DARK, spaceAfter=8,
        ),
        "note": ParagraphStyle(
            "SumNote", parent=body, fontSize=8.5, leading=11.5,
            textColor=TEXT_MUTED, spaceAfter=4,
        ),
        "cta": ParagraphStyle(
            "SumCTA", parent=body, fontSize=9.5, leading=13,
            textColor=NAVY, backColor=GOLD_BG, borderPadding=12,
            borderColor=GOLD, borderWidth=0.7, spaceBefore=8, spaceAfter=8,
        ),
        # --- New premium-redesign styles (additive, visual-only) ---
        # NOTE: autoLeading="max" is critical here — these styles are used for
        # Paragraphs that mix several inline <font size="..."> tags via <br/>.
        # Without it, ReportLab uses one FIXED leading for every line, and a
        # large inline font size (e.g. a 24pt score inside an 11pt-leading
        # style) would visually overlap the line above/below it. "max" makes
        # each line's own leading grow to fit its tallest glyph, guaranteeing
        # no overlap regardless of how large an inline font tag is.
        "card_label": ParagraphStyle(
            "SumCardLabel", parent=body, fontSize=7.3, leading=9, alignment=TA_CENTER,
            textColor=colors.HexColor("#94A3B8"), fontName="Helvetica-Bold",
            spaceAfter=0, autoLeading="max",
        ),
        "card_body_center": ParagraphStyle(
            "SumCardBodyCenter", parent=body, fontSize=8.5, leading=13, alignment=TA_CENTER,
            textColor=TEXT_DARK, spaceAfter=0, autoLeading="max",
        ),
        "badge_label": ParagraphStyle(
            "SumBadgeLabel", parent=body, fontSize=6.6, leading=8.4, alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"), fontName="Helvetica-Bold", spaceAfter=0,
            autoLeading="max",
        ),
        "section_tag": ParagraphStyle(
            "SumSectionTag", parent=body, fontSize=7.5, leading=10, alignment=TA_RIGHT,
            textColor=colors.HexColor("#94A3B8"), fontName="Helvetica-Bold", spaceAfter=0,
            autoLeading="max",
        ),
        "caption": ParagraphStyle(
            "SumCaption", parent=body, fontSize=7.3, leading=9.5,
            textColor=colors.HexColor("#94A3B8"), fontName="Helvetica-Oblique", spaceAfter=0,
        ),
        "block": ParagraphStyle(
            "SumBlock", parent=body, fontSize=10, leading=14, textColor=TEXT_DARK,
            spaceAfter=0, autoLeading="max",
        ),
        "block_on_dark": ParagraphStyle(
            "SumBlockOnDark", parent=body, fontSize=10, leading=14, textColor=colors.white,
            spaceAfter=0, autoLeading="max",
        ),
    }


# ============================================================
# Chart & card visual primitives (ReportLab graphics — additive helpers)
# ============================================================

def _bar_drawing(score: float, width: float, height: float = 0.40 * cm, max_score: float = 5.0):
    """A single track+fill horizontal bar (real chart, not a coloured cell).

    Draws a light-grey full-width track (the 0–5 scale reference) with a
    coloured fill proportional to `score` layered on top, plus a thin
    frame. Returns a Drawing (a Flowable — usable directly in a story or
    inside a Table cell).
    """
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=LINE_LIGHT, strokeColor=None))
    fill_w = max(0.06 * cm, min(width, (max(0.0, float(score or 0)) / max_score) * width))
    d.add(Rect(0, 0, fill_w, height, fillColor=band_color(score), strokeColor=None))
    d.add(Rect(0, 0, width, height, fillColor=None, strokeColor=LINE_LIGHT, strokeWidth=0.6))
    return d


def _dual_bar_drawing(current: float, projected: float, width: float, row_h: float = 0.34 * cm,
                       gap: float = 0.16 * cm, max_score: float = 5.0):
    """Two stacked track+fill bars (Now vs +90 days) for the projection panel."""
    total_h = row_h * 2 + gap
    d = Drawing(width, total_h)
    y_top = row_h + gap
    for y, val in ((y_top, current), (0, projected)):
        d.add(Rect(0, y, width, row_h, fillColor=colors.HexColor("#334155"), strokeColor=None))
        fill_w = max(0.06 * cm, min(width, (max(0.0, float(val or 0)) / max_score) * width))
        d.add(Rect(0, y, fill_w, row_h, fillColor=band_color(val), strokeColor=None))
    return d


def _radar_drawing(scores: dict, bottleneck: str, size: float = 7.4 * cm, label_pad: float = 2.05 * cm):
    """Custom 4-axis radar/spider chart for the People/Process/Data/Technology
    pillar scores, drawn with primitive shapes (no dependency on reportlab's
    chart-package spider API — full control over brand styling).

    Layout is clockwise from the top: People (top) → Process (right) →
    Technology (bottom) → Data (left). The bottleneck axis is highlighted.
    """
    dw = size + 2 * label_pad
    dh = size + 2 * label_pad
    d = Drawing(dw, dh)
    cx, cy = dw / 2.0, dh / 2.0
    max_r = size / 2.0 - 0.3 * cm

    axis_order = ("people", "process", "technology", "data")
    angles = {"people": 90, "process": 0, "technology": 270, "data": 180}

    def _pt(angle_deg, r):
        rad = math.radians(angle_deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    # Concentric grid rings (levels 1–5)
    for level in range(1, 6):
        r = (level / 5.0) * max_r
        pts = []
        for k in axis_order:
            x, y = _pt(angles[k], r)
            pts += [x, y]
        d.add(Polygon(pts, strokeColor=LINE_LIGHT, strokeWidth=0.6, fillColor=None))

    # Spoke axis lines from centre
    for k in axis_order:
        x, y = _pt(angles[k], max_r)
        d.add(Line(cx, cy, x, y, strokeColor=LINE_LIGHT, strokeWidth=0.6))

    # Data polygon (filled, pale brand tint)
    data_pts = []
    for k in axis_order:
        s = float((scores or {}).get(k, 0) or 0)
        r = (min(s, 5.0) / 5.0) * max_r
        x, y = _pt(angles[k], r)
        data_pts += [x, y]
    d.add(Polygon(data_pts, strokeColor=GOLD, strokeWidth=1.6, fillColor=colors.HexColor("#CFFAFE")))

    # Data point markers + axis labels
    label_r = max_r + 0.55 * cm
    for k in axis_order:
        s = float((scores or {}).get(k, 0) or 0)
        r = (min(s, 5.0) / 5.0) * max_r
        x, y = _pt(angles[k], r)
        is_bn = (k == bottleneck)
        d.add(Circle(x, y, 4.6 if is_bn else 3.0, fillColor=band_color(s),
                     strokeColor=colors.white, strokeWidth=1))

        lx, ly = _pt(angles[k], label_r)
        anchor = "middle"
        if angles[k] == 0:
            anchor = "start"
        elif angles[k] == 180:
            anchor = "end"
        label_color = colors.HexColor("#DC2626") if is_bn else NAVY
        d.add(String(lx, ly + 3, _pillar_label(k).upper(), fontName="Helvetica-Bold",
                     fontSize=8, fillColor=label_color, textAnchor=anchor))
        d.add(String(lx, ly - 8, f"{s:.1f} / 5.0", fontName="Helvetica",
                     fontSize=7.3, fillColor=TEXT_MUTED, textAnchor=anchor))
        if is_bn:
            d.add(String(lx, ly - 18, "BOTTLENECK", fontName="Helvetica-Bold",
                         fontSize=6.3, fillColor=colors.HexColor("#DC2626"), textAnchor=anchor))
    return d


def _timeline_drawing(width: float, n: int = 3, height: float = 1.05 * cm):
    """Slim horizontal timeline connector with numbered milestone nodes,
    evenly centred so it lines up with an n-column Table placed beneath it."""
    d = Drawing(width, height)
    y = height * 0.55
    margin = width / (2 * n)
    usable = width - 2 * margin
    xs = [margin + (usable * i / (n - 1) if n > 1 else 0) for i in range(n)]
    d.add(Line(xs[0], y, xs[-1], y, strokeColor=colors.HexColor("#CBD5E1"), strokeWidth=1.4))
    for i, x in enumerate(xs):
        d.add(Circle(x, y, 8.5, fillColor=GOLD, strokeColor=colors.white, strokeWidth=1.4))
        d.add(String(x, y - 2.8, str(i + 1), fontName="Helvetica-Bold", fontSize=8,
                     fillColor=colors.white, textAnchor="middle"))
    return d


def _kpi_card_row(overall: float, overall_level: str, bottleneck_label: str,
                   bottleneck_level: str, dbi_gap: float, dbi_direction: str, styles):
    """Three equal-width stat cards (Overall Score / Bottleneck Pillar /
    Maturity Level) — a single-row Table so all three share one auto height."""
    sign = "+" if (dbi_gap or 0) >= 0 else ""
    direction_txt = (dbi_direction or "").replace("-", " ").strip()

    c1 = Paragraph(
        f'<font size="7" color="#94A3B8"><b>OVERALL SCORE</b></font><br/>'
        f'<font size="24" color="#22D3EE"><b>{overall:.2f}</b></font>'
        f'<font size="10" color="#67E8F9"> /5.0</font><br/>'
        f'<font size="8.5" color="#FFFFFF">{overall_level}</font>',
        styles["card_body_center"],
    )
    c2 = Paragraph(
        f'<font size="7" color="#92400E"><b>BOTTLENECK PILLAR</b></font><br/>'
        f'<font size="17" color="#B45309"><b>{bottleneck_label}</b></font><br/>'
        f'<font size="8" color="#92400E">{sign}{dbi_gap:.2f} vs. average'
        + (f" &nbsp;\u00b7&nbsp; {direction_txt}" if direction_txt else "") + '</font>',
        styles["card_body_center"],
    )
    c3 = Paragraph(
        f'<font size="7" color="#0E7490"><b>BOTTLENECK LEVEL</b></font><br/>'
        f'<font size="17" color="#0891B2"><b>{bottleneck_level}</b></font><br/>'
        f'<font size="8" color="#0E7490">Hannila L1&ndash;L5 ladder</font>',
        styles["card_body_center"],
    )
    col_w = CONTENT_WIDTH / 3.0
    row = Table(
        [[c1, c2, c3]], colWidths=[col_w, col_w, col_w],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), NAVY),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFF7ED")),
            ("BACKGROUND", (2, 0), (2, 0), GOLD_BG),
            ("BOX", (0, 0), (0, 0), 0.7, NAVY_DEEP),
            ("BOX", (1, 0), (1, 0), 0.7, colors.HexColor("#FDBA74")),
            ("BOX", (2, 0), (2, 0), 0.7, GOLD),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 13),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]),
    )
    return row


def _precondition_cards(preconditions: dict, styles):
    """Five colour-coded 'traffic-light' status cards (replaces the old
    monotone text-pill row)."""
    row = []
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, (key, label) in enumerate(PRECONDITION_LABELS.items()):
        status = (preconditions.get(key) or "partial").lower()
        c = STATUS_COLORS.get(status, STATUS_COLORS["partial"])
        bg = STATUS_BG.get(status, STATUS_BG["partial"])
        cell = Paragraph(
            f'<font color="#475569"><b>{label}</b></font><br/><br/>'
            f'<font size="9" color="{c.hexval()}"><b>{status.upper()}</b></font>',
            styles["badge_label"],
        )
        row.append(cell)
        style_cmds.append(("BACKGROUND", (i, 0), (i, 0), bg))
        style_cmds.append(("BOX", (i, 0), (i, 0), 0.8, c))
    col_w = CONTENT_WIDTH / 5.0
    return Table([row], colWidths=[col_w] * 5, style=TableStyle(style_cmds))


def _vulnerability_pill(level_text: str, styles):
    """Small coloured badge Table for a Low/Medium/High/Critical rating."""
    key = (level_text or "").strip().lower()
    fg, bg = VULN_COLORS.get(key, (TEXT_MUTED, ROW_ALT))
    pill = Table(
        [[Paragraph(f'<font color="{fg.hexval()}"><b>{(level_text or "—").upper()}</b></font>',
                    styles["card_label"])]],
        colWidths=[2.6 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 0.6, fg),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    )
    return pill


# ============================================================
# PAGE 1 — THE VERDICT
# ============================================================

# ============================================================
# PAGE 1 — THE VERDICT
# ============================================================

def _pillar_detail_list(scores: dict, bottleneck: str, styles):
    """Compact 4-row label + track-bar + value list, paired alongside the
    radar chart so exact numbers are still available at a glance."""
    rows = []
    bar_w = 3.9 * cm
    for dim in DIMENSIONS:
        s = float(scores.get(dim, 0) or 0)
        label = _pillar_label(dim)
        label_html = f'<font color="#DC2626"><b>{label}</b></font>' if dim == bottleneck else f"<b>{label}</b>"
        rows.append([
            Paragraph(label_html, styles["body"]),
            _bar_drawing(s, bar_w),
            Paragraph(f"<b>{s:.1f}</b>/5.0", styles["body"]),
        ])
    return Table(
        rows, colWidths=[2.5 * cm, bar_w + 0.2 * cm, 1.6 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE_LIGHT),
        ]),
    )


def _score_visual_row(scores: dict, bottleneck: str, styles):
    """Radar chart (left) + numeric detail list (right), side by side."""
    radar = _radar_drawing(scores, bottleneck, size=6.0 * cm, label_pad=1.55 * cm)
    detail = _pillar_detail_list(scores, bottleneck, styles)
    return Table(
        [[radar, detail]], colWidths=[9.3 * cm, 8.3 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 10),
            ("LINEAFTER", (0, 0), (0, 0), 0.5, LINE_LIGHT),
        ]),
    )


def _build_page1(story, report, styles, assessment):
    """PAGE 1 — THE VERDICT."""
    company_name = assessment.get("company_name") or report.get("company_name") or "—"
    scores = report.get("scores") or {}
    overall = float(scores.get("overall") or report.get("equal_weighted_score") or 0)
    bottleneck = _pillar_from_dbi(report)
    level_names = report.get("level_names") or {}
    bottleneck_level = _capitalise_level(level_names.get(bottleneck, "")) or "Developing"
    overall_level = _capitalise_level(level_names.get("overall", "")) or bottleneck_level
    dbi = report.get("decision_bottleneck_index") or {}
    dbi_gap = float(dbi.get("gap", 0.0) or 0.0)
    dbi_direction = (dbi.get("direction") or "").replace("-", " ")

    # --- Header band: title block (left) + page tag (right) ---
    header_row = Table(
        [[
            Paragraph(
                f'<font color="#0891B2" size="8"><b>EXECUTIVE SUMMARY</b></font><br/>'
                f'<font color="#0D1B2A" size="20"><b>{company_name}</b></font><br/>'
                f'<font color="#1A3550" size="10">Portfolio Decision Capability \u2014 4-Page Verdict</font>',
                styles["block"],
            ),
            Paragraph("PREPARED BY<br/>PORTFOLIOHEALTH ADVISOR<br/>PAGE 1 OF 4 &middot; THE VERDICT"
                       .replace("&middot;", "\u00b7"), styles["section_tag"]),
        ]],
        colWidths=[12.6 * cm, 5.4 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    story.append(header_row)
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceBefore=8, spaceAfter=10))

    # --- KPI stat card row ---
    story.append(_kpi_card_row(overall, overall_level, _pillar_label(bottleneck),
                                bottleneck_level, dbi_gap, dbi_direction, styles))
    story.append(Spacer(0, 10))

    # --- Radar chart + numeric detail ---
    story.append(Paragraph("PILLAR SCORES \u2014 PORTFOLIO RENEWAL RADAR", styles["eyebrow"]))
    story.append(_score_visual_row(scores, bottleneck, styles))
    story.append(Spacer(0, 6))

    verdict = (
        f"Your portfolio decision capability is operating at <b>{bottleneck_level}</b>. "
        f"Your weakest capability is <b>{_pillar_label(bottleneck)}</b>, which caps what the rest "
        f"of the organisation can reliably deliver."
    )
    story.append(Paragraph(verdict, styles["lead"]))
    story.append(HRFlowable(width="100%", thickness=0.4, color=LINE_LIGHT, spaceBefore=2, spaceAfter=10))

    # --- Failure pattern card (accent bar + title + narrative) ---
    fp_name = report.get("failure_pattern_name") or _fallback_failure_pattern(bottleneck, report)
    fp_narrative = report.get("failure_pattern_narrative") or (
        f"The {bottleneck} pillar is the binding constraint on portfolio decisions today. "
        f"Decisions that depend on this pillar arrive with insufficient evidence and stall or drift. "
        f"The organisation is missing the operational capability to close this loop consistently."
    )
    fp_card = Table(
        [[Paragraph(
            f'<font color="#DC2626" size="7.5"><b>FAILURE PATTERN</b></font><br/>'
            f'<font color="#0D1B2A" size="13"><b>{fp_name}</b></font><br/><br/>'
            f'<font color="#1E293B" size="9.5">{fp_narrative}</font>',
            styles["block"],
        )]],
        colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ROW_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE_LIGHT),
            ("LINEBEFORE", (0, 0), (0, 0), 3, colors.HexColor("#DC2626")),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]),
    )
    story.append(fp_card)
    story.append(Spacer(0, 10))

    # --- Financial consequence highlight ---
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
    time_to_implement = first_action.get("time_to_implement") or "2\u20134 weeks"
    preconditions = first_action.get("preconditions_met") or {}

    header_row = Table(
        [[
            Paragraph(
                f'<font color="#0891B2" size="8"><b>YOUR #1 ACTION</b></font><br/>'
                f'<font color="#0D1B2A" size="18"><b>{headline}</b></font>',
                styles["block"],
            ),
            Paragraph("PAGE 2 OF 4 &middot; THE ACTION".replace("&middot;", "\u00b7"), styles["section_tag"]),
        ]],
        colWidths=[13.4 * cm, 4.6 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    story.append(header_row)
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceBefore=8, spaceAfter=10))

    story.append(Paragraph("WHAT TO DO", styles["eyebrow"]))
    story.append(Paragraph(description, styles["lead"]))
    story.append(Spacer(0, 4))

    # Owner + timing + outcome — 3 aligned cards, equal height (single row Table)
    meta_tbl = Table(
        [[
            Paragraph('<font color="#0E7490" size="7"><b>WHO OWNS IT</b></font><br/><br/>'
                      f'<font color="#0D1B2A" size="10"><b>{who_owns_it}</b></font>', styles["block"]),
            Paragraph('<font color="#0E7490" size="7"><b>TIME TO IMPLEMENT</b></font><br/><br/>'
                      f'<font color="#0D1B2A" size="10"><b>{time_to_implement}</b></font>', styles["block"]),
            Paragraph('<font color="#0E7490" size="7"><b>EXPECTED OUTCOME</b></font><br/><br/>'
                      f'<font color="#0D1B2A" size="9.5">{expected_outcome}</font>', styles["block"]),
        ]],
        colWidths=[CONTENT_WIDTH * 0.28, CONTENT_WIDTH * 0.24, CONTENT_WIDTH * 0.48],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GOLD_BG),
            ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
            ("LINEAFTER", (0, 0), (0, 0), 0.6, colors.HexColor("#99D8E8")),
            ("LINEAFTER", (1, 0), (1, 0), 0.6, colors.HexColor("#99D8E8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]),
    )
    story.append(meta_tbl)
    story.append(Spacer(0, 12))

    # Preconditions status — 5 colour-coded "traffic-light" cards
    story.append(Paragraph("PRECONDITIONS", styles["eyebrow"]))
    story.append(_precondition_cards(preconditions, styles))
    story.append(Spacer(0, 12))

    # Governance signal (2B) — a SEPARATE short field, not a copy of critical_gaps.
    story.append(Paragraph("GOVERNANCE SIGNAL", styles["eyebrow"]))
    gov_summary = report.get("governance_signal_summary") or []
    bullets = []
    if isinstance(gov_summary, list) and any(gov_summary):
        for b in gov_summary:
            if isinstance(b, str) and b.strip():
                bullets.append(f"<font color='#0891B2'>&bull;</font> {b.strip()}")
    else:
        # Legacy fallback: distil from critical_gaps + a positive finding.
        critical_gaps = report.get("critical_gaps") or []
        key_findings = report.get("key_findings") or []
        gaps = [g for g in critical_gaps[:2] if g]
        positive = next((f for f in key_findings if isinstance(f, str) and any(
            w in f.lower() for w in ("strong", "clear", "established", "documented", "consistent")
        )), None)
        for g in gaps:
            bullets.append(f"<font color='#DC2626'>&bull;</font> {g}")
        if positive:
            bullets.append(f"<font color='#10B981'>&bull;</font> {positive}")
    gov_rows = [[Paragraph(b, styles["body"])] for b in bullets] or [[Paragraph(
        "Governance signals will populate once the assessment conversation is complete.", styles["note"],
    )]]
    story.append(Table(
        gov_rows, colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]),
    ))
    story.append(Spacer(0, 12))

    # 90-day projection panel — dual bar chart (Now vs +90 days) + narrative
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
    comparable = ninety.get("comparable_outcome") or "Reduced portfolio-decision cycle time."

    left_cell = [
        Paragraph('<font color="#67E8F9" size="8.5"><b>90-DAY PROJECTION</b></font>', styles["block_on_dark"]),
        Spacer(0, 8),
        _dual_bar_drawing(sc, sp, width=5.0 * cm),
        Spacer(0, 4),
        Paragraph(
            f'<font size="7.5" color="#94A3B8">NOW</font>  <b>{sc:.1f}</b>/5.0'
            f'&nbsp;&nbsp;-&gt;&nbsp;&nbsp;<font size="7.5" color="#94A3B8">+90 DAYS</font>  <b>{sp:.1f}</b>/5.0'
            f'&nbsp;&nbsp;<font size="7.5" color="#67E8F9">(+{sd:.1f})</font>',
            styles["block_on_dark"],
        ),
        Spacer(0, 6),
        Paragraph(f'<font size="8">Bottleneck level:<br/><b>{bl_c}</b> -&gt; <b>{bl_p}</b></font>',
                  styles["block_on_dark"]),
    ]
    right_cell = [
        Paragraph(f'<b>What becomes possible:</b><br/>{possible}', styles["block"]),
        Spacer(0, 8),
        Paragraph(f'<i>Comparable outcome:</i> {comparable}', styles["note"]),
    ]
    proj_tbl = Table(
        [[left_cell, right_cell]],
        colWidths=[6.2 * cm, 11.4 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), NAVY),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ]),
    )
    story.append(proj_tbl)
    story.append(PageBreak())


# ============================================================
# PAGE 3 — 90-DAY ROADMAP
# ============================================================

RELABEL = [
    ("immediate",   "This Month",   "0\u201330 days"),
    ("short_term",  "This Quarter", "30\u201390 days"),
    ("strategic",   "This Year",    "90\u2013365 days"),
]


def _build_page3(story, report, styles):
    """PAGE 3 — 90-DAY ROADMAP (relabelled), with a visual timeline connector."""
    roadmap = report.get("roadmap") or {}

    header_row = Table(
        [[
            Paragraph(
                '<font color="#0891B2" size="8"><b>YOUR ROADMAP</b></font><br/>'
                '<font color="#0D1B2A" size="18"><b>Three moves. Same team. One quarter.</b></font>',
                styles["block"],
            ),
            Paragraph("PAGE 3 OF 4 &middot; THE ROADMAP".replace("&middot;", "\u00b7"), styles["section_tag"]),
        ]],
        colWidths=[13.4 * cm, 4.6 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    story.append(header_row)
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceBefore=8, spaceAfter=12))

    # Visual timeline connector + aligned 3-column phase-window labels
    story.append(_timeline_drawing(CONTENT_WIDTH, n=3))
    col_w = CONTENT_WIDTH / 3.0
    story.append(Table(
        [[
            Paragraph('<font color="#0D1B2A" size="9.5"><b>THIS MONTH</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">0\u201330 days</font>', styles["card_body_center"]),
            Paragraph('<font color="#0D1B2A" size="9.5"><b>THIS QUARTER</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">30\u201390 days</font>', styles["card_body_center"]),
            Paragraph('<font color="#0D1B2A" size="9.5"><b>THIS YEAR</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">90\u2013365 days</font>', styles["card_body_center"]),
        ]],
        colWidths=[col_w, col_w, col_w],
        style=TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]),
    ))
    story.append(Spacer(0, 14))

    for i, (phase_key, label, window) in enumerate(RELABEL):
        phase = roadmap.get(phase_key) or {}
        # 2A — Executive Summary renders ONLY the one-sentence action, not the
        # full numbered action list (that detail stays exclusive to the Full Report).
        action = phase.get("action_summary") or _first_sentence(phase.get("actions", "")) or "\u2014"
        pillar_focus = phase.get("pillar_focus") or "\u2014"
        owner = phase.get("management_required") or "\u2014"
        milestone = phase.get("governance_milestone") or ""
        expected_gain = phase.get("expected_gain") or ""

        num_cell = Paragraph(f'<font color="#FFFFFF" size="16"><b>{i + 1}</b></font>', styles["card_body_center"])
        content_cell = [
            Paragraph(
                f'<font color="#0891B2" size="8"><b>{label.upper()}</b></font>'
                f'&nbsp;&nbsp;<font color="#94A3B8" size="7">{window}</font>',
                styles["block"],
            ),
            Spacer(0, 5),
            Paragraph(
                f'<b>Action:</b> {action}<br/>'
                f'<b>Who owns it:</b> {owner}<br/>'
                f'<b>What it unlocks:</b> {milestone or pillar_focus}',
                styles["block"],
            ),
        ]
        gain_cell = (
            Paragraph(
                f'<font color="#0E7490" size="6.8"><b>EXPECTED GAIN</b></font><br/><br/>'
                f'<font color="#0D1B2A" size="8.5">{expected_gain}</font>',
                styles["block"],
            ) if expected_gain else Paragraph("", styles["block"])
        )

        card = Table(
            [[num_cell, content_cell, gain_cell]],
            colWidths=[1.3 * cm, 11.5 * cm, 4.4 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), GOLD),
                ("BACKGROUND", (1, 0), (1, 0), colors.white),
                ("BACKGROUND", (2, 0), (2, 0), GOLD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]),
        )
        story.append(KeepTogether(card))
        story.append(Spacer(0, 10))

    story.append(PageBreak())


# ============================================================
# PAGE 4 — FULL SCORECARD REFERENCE
# ============================================================

def _build_page4(story, report, styles):
    """PAGE 4 — FULL SCORECARD REFERENCE (compressed)."""
    scores = report.get("scores") or {}
    level_names = report.get("level_names") or {}
    interps = report.get("pillar_interpretations") or {}
    interps_short = report.get("pillar_interpretation_short") or {}
    summaries = report.get("dimension_summaries") or {}
    reliability = (report.get("assessment_reliability") or {}).get("confidence") or "\u2014"
    mgmt = report.get("management_commitment") or "\u2014"
    dvr = report.get("decision_vulnerability_ratings") or {}

    header_row = Table(
        [[
            Paragraph(
                '<font color="#0891B2" size="8"><b>SCORECARD REFERENCE</b></font><br/>'
                '<font color="#0D1B2A" size="18"><b>Full detail \u2014 for the record</b></font>',
                styles["block"],
            ),
            Paragraph("PAGE 4 OF 4 &middot; THE RECORD".replace("&middot;", "\u00b7"), styles["section_tag"]),
        ]],
        colWidths=[13.4 * cm, 4.6 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    story.append(header_row)
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceBefore=8, spaceAfter=12))

    # Compressed pillar table — score column now carries a real mini bar-chart
    rows = [["Pillar", "Score", "Level", "Two-line interpretation"]]
    for dim in DIMENSIONS:
        s = float(scores.get(dim, 0) or 0)
        lvl = _capitalise_level(level_names.get(dim, ""))
        # 2C — use the separate short field; only fall back to a truncated
        # long-form interpretation for legacy reports missing the short field.
        interp = (interps_short.get(dim) or "").strip()
        if not interp:
            interp = (interps.get(dim) or summaries.get(dim) or "").strip()
            if len(interp) > 200:
                cut = interp[:200]
                interp = cut[: cut.rfind(" ")] + "\u2026"
        band = BAND_COLORS_HEX[score_band(s)]
        score_cell = [
            Paragraph(f'<font color="{band}"><b>{s:.1f}</b></font>', styles["body"]),
            Spacer(0, 2),
            _bar_drawing(s, 2.0 * cm, height=0.24 * cm),
        ]
        rows.append([
            Paragraph(f"<b>{_pillar_label(dim)}</b>", styles["body"]),
            score_cell,
            Paragraph(f"<font color='{band}'>{lvl}</font>", styles["body"]),
            Paragraph(interp or "\u2014", styles["body"]),
        ])
    tbl = Table(
        rows, colWidths=[2.4 * cm, 2.3 * cm, 2.5 * cm, 8.8 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE_LIGHT),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]),
    )
    story.append(tbl)
    story.append(Spacer(0, 12))

    # Management commitment + assessment reliability — two aligned info cards
    story.append(Table(
        [[
            Paragraph(f'<font color="#94A3B8" size="7"><b>MANAGEMENT COMMITMENT</b></font><br/>'
                      f'<font color="#0D1B2A" size="11"><b>{mgmt}</b></font>', styles["block"]),
            Paragraph(f'<font color="#94A3B8" size="7"><b>ASSESSMENT RELIABILITY</b></font><br/>'
                      f'<font color="#0D1B2A" size="11"><b>{reliability}</b></font>', styles["block"]),
        ]],
        colWidths=[CONTENT_WIDTH / 2.0, CONTENT_WIDTH / 2.0],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GOLD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE_LIGHT),
            ("LINEAFTER", (0, 0), (0, 0), 0.5, colors.HexColor("#99D8E8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    ))
    story.append(Spacer(0, 12))

    # Decision-type vulnerability — colour-coded badge per row
    story.append(Paragraph("DECISION-TYPE VULNERABILITY", styles["eyebrow"]))
    dvr_labels = [
        ("Discontinuation", dvr.get("discontinuation", "\u2014")),
        ("New product launch", dvr.get("new_launch", "\u2014")),
        ("Product change", dvr.get("product_change", "\u2014")),
        ("Portfolio investment", dvr.get("portfolio_investment", "\u2014")),
    ]
    dvr_rows = [["Decision type", "Vulnerability"]]
    for name, level in dvr_labels:
        dvr_rows.append([Paragraph(name, styles["body"]), _vulnerability_pill(level, styles)])
    dvr_tbl = Table(
        dvr_rows, colWidths=[10.6 * cm, 3.0 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.4, LINE_LIGHT),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_LIGHT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]),
    )
    story.append(dvr_tbl)
    story.append(Spacer(0, 14))
    story.append(Paragraph(
        "This Executive Summary is a companion to the full 15-page PortfolioHealth report. "
        "Detailed methodology, weighted-score calculation tables, and academic citations are exclusive "
        "to the Full Report.",
        styles["caption"],
    ))


# ============================================================
# Page decoration (header hairline + footer with correct numbering)
# ============================================================

def _make_footer(company_name: str):
    """Factory returning a canvas callback for this specific PDF build.

    Fixes a real bug from reusing the full-report's `_page_decoration`: that
    function assumes a cover + TOC (skips footers on pages <=2 and prints
    `doc.page - 2`), which made THIS 4-page report show blank footers on
    pages 1–2 and "Page 1"/"Page 2" on what are actually pages 3–4. This
    report has no cover/TOC — every page is numbered directly.
    """
    def _decoration(canvas, doc):
        canvas.saveState()
        page_width, page_height = A4
        left = 1.5 * cm
        right = page_width - 1.5 * cm

        # Top hairline + brand tag (sits inside the top margin, above content)
        canvas.setStrokeColor(LINE_LIGHT)
        canvas.setLineWidth(0.6)
        canvas.line(left, page_height - 30, right, page_height - 30)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(NAVY)
        canvas.drawString(left, page_height - 24, "PORTFOLIOHEALTH ADVISOR")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawRightString(right, page_height - 24, f"EXECUTIVE SUMMARY  \u00b7  {company_name}")

        # Bottom hairline + correct page numbering (sits inside bottom margin)
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.5)
        canvas.line(left, 40, right, 40)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawString(left, 26, "PortfolioHealth Advisor  \u00b7  PPM Capability Maturity Assessment  \u00b7  University of Oulu")
        canvas.drawRightString(right, 26, f"Page {doc.page} of 4")
        canvas.restoreState()
    return _decoration


# ============================================================
# Public entry point
# ============================================================

def build_executive_summary_pdf(assessment: dict) -> BytesIO:
    """Assemble the 4-page Executive Summary PDF into an in-memory buffer."""
    # Arrow-safe copy for PDF rendering (Part 1A) — stored data / UI keep the
    # original glyphs; only PDF text is normalised.
    assessment = sanitized_assessment(assessment)
    report = assessment.get("report") or {}
    company_name = assessment.get("company_name") or report.get("company_name") or "\u2014"
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

    decoration = _make_footer(company_name)
    doc.build(story, onFirstPage=decoration, onLaterPages=decoration)
    buffer.seek(0)
    return buffer
