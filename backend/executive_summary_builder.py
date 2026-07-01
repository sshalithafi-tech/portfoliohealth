"""
Executive Summary Report — a 4-page condensed alternative to the full 15-page
consultant report. Consumes the extended JSON schema (failure pattern,
90-day projection, first action, financial consequence) added in Part 1
of the PPDT Summary Report track.

Design goals (v3 — "McKinsey/BCG one-pager" redesign):
  • Restrained, management-consulting aesthetic: neutral white/light-grey
    base, ONE accent colour (muted teal) for scores/emphasis, red/amber used
    ONLY for two specific semantic flags (decision-vulnerability
    Critical/High, and "Not Met" preconditions) — nowhere else.
  • No radar/spider chart — pillar scores are 4 clean score cards with a
    thin progress bar each.
  • Modern typography via the Inter font family (falls back to Helvetica
    automatically if the bundled TTFs are ever unavailable, so the PDF can
    never fail to render).
  • Consistent header + footer chrome on every page: report title, company
    name, page number, and a subtle "PortfolioHealth Advisor" brand line.
  • 100% additive — nothing here mutates or shortens the full report path
    in `pdf_builder.py`. Both PDFs render from the same `assessment.report`.
  • Backwards-compatible — if any new field is missing (older assessments
    saved before the schema extension), sensible defaults render instead
    of raising.
"""
from __future__ import annotations

import os
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String

from pdf_builder import sanitized_assessment


# ============================================================
# Typography — Inter (bundled TTFs), with a safe Helvetica fallback
# ============================================================

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_INTER_OK = False
try:
    pdfmetrics.registerFont(TTFont("Inter", os.path.join(_FONT_DIR, "Inter-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Inter-Medium", os.path.join(_FONT_DIR, "Inter-Medium.ttf")))
    pdfmetrics.registerFont(TTFont("Inter-SemiBold", os.path.join(_FONT_DIR, "Inter-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("Inter-Bold", os.path.join(_FONT_DIR, "Inter-Bold.ttf")))
    pdfmetrics.registerFontFamily(
        "Inter", normal="Inter", bold="Inter-Bold", italic="Inter", boldItalic="Inter-Bold"
    )
    _INTER_OK = True
except Exception:
    _INTER_OK = False

F_REG = "Inter" if _INTER_OK else "Helvetica"
F_MED = "Inter-Medium" if _INTER_OK else "Helvetica"
F_SEMI = "Inter-SemiBold" if _INTER_OK else "Helvetica-Bold"
F_BOLD = "Inter-Bold" if _INTER_OK else "Helvetica-Bold"


# ============================================================
# Colour palette — neutral base + ONE accent (muted teal).
# Red/amber are reserved EXCLUSIVELY for: decision-vulnerability
# Critical/High flags, and "Not Met" preconditions. Nowhere else.
# ============================================================

INK = colors.HexColor("#111827")           # primary text (near-black)
INK_SOFT = colors.HexColor("#475569")      # secondary body text
MUTED = colors.HexColor("#94A3B8")         # captions / muted labels
LINE = colors.HexColor("#E2E8F0")          # thin hairlines / subtle borders
BG_ALT = colors.HexColor("#F8FAFC")        # alternating row shading / card fill
WHITE = colors.white

ACCENT = colors.HexColor("#0E7490")        # THE single accent — muted teal
ACCENT_DARK = colors.HexColor("#0B4F5E")
ACCENT_TINT = colors.HexColor("#F0F9FA")   # very light teal wash

AMBER = colors.HexColor("#B45309")         # reserved: High vulnerability / Not Met
AMBER_TINT = colors.HexColor("#FFFBEB")
RED = colors.HexColor("#B91C1C")           # reserved: Critical vulnerability / Not Met
RED_TINT = colors.HexColor("#FEF2F2")

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

# Precondition status → (text colour, thin top-rule colour). Background stays
# neutral for ALL statuses — only "not met" ever uses red (per design brief).
STATUS_STYLE = {
    "met": (ACCENT_DARK, ACCENT),
    "partial": (AMBER, AMBER),
    "not met": (RED, RED),
}

# Decision-vulnerability rating → text colour. Only Critical/High are
# coloured; Medium/Low stay neutral ink (per design brief: "sparingly").
VULN_STYLE = {
    "low": (INK_SOFT, None),
    "medium": (INK_SOFT, None),
    "high": (AMBER, AMBER_TINT),
    "critical": (RED, RED_TINT),
}

# Page margins — identical on all sides for a clean, consistent grid.
MARGIN = 1.6 * cm
CONTENT_WIDTH = A4[0] - 2 * MARGIN  # ≈ 17.8cm


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
    from reportlab.lib.styles import ParagraphStyle, TA_CENTER, TA_RIGHT

    body = ParagraphStyle(
        "Body", fontName=F_REG, fontSize=9.5, leading=14, textColor=INK_SOFT,
    )
    return {
        "body": body,
        # Big page-opening headline (e.g. "Portfolio Verdict")
        "h1": ParagraphStyle(
            "SumH1", parent=body, fontName=F_BOLD, fontSize=19, leading=23,
            textColor=INK, spaceAfter=2,
        ),
        "h2": ParagraphStyle(
            "SumH2", parent=body, fontName=F_SEMI, fontSize=12.5, leading=16,
            textColor=INK, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "SumH3", parent=body, fontName=F_SEMI, fontSize=10.5, leading=13,
            textColor=INK, spaceAfter=4,
        ),
        # Small tracked-caps section label above each block
        "eyebrow": ParagraphStyle(
            "SumEyebrow", parent=body, fontName=F_SEMI, fontSize=7.6, leading=10,
            textColor=ACCENT, spaceAfter=3, spaceBefore=0,
        ),
        "lead": ParagraphStyle(
            "SumLead", parent=body, fontName=F_REG, fontSize=10, leading=15,
            textColor=INK_SOFT, spaceAfter=8,
        ),
        "note": ParagraphStyle(
            "SumNote", parent=body, fontName=F_REG, fontSize=8.3, leading=11.5,
            textColor=MUTED, spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "SumCaption", parent=body, fontName=F_REG, fontSize=7.3, leading=9.5,
            textColor=MUTED, spaceAfter=0,
        ),
        # NOTE: autoLeading="max" is critical for any style used on Paragraphs
        # that mix several inline <font size="..."> tags via <br/>. Without
        # it, ReportLab uses one FIXED leading for the whole paragraph, and a
        # large inline font size would visually overlap the adjacent line.
        "card_label": ParagraphStyle(
            "SumCardLabel", parent=body, fontName=F_SEMI, fontSize=6.8, leading=8.6,
            alignment=TA_CENTER, textColor=MUTED, spaceAfter=0, autoLeading="max",
        ),
        "card_body_center": ParagraphStyle(
            "SumCardBodyCenter", parent=body, fontName=F_REG, fontSize=8.5, leading=12,
            alignment=TA_CENTER, textColor=INK, spaceAfter=0, autoLeading="max",
        ),
        "badge_label": ParagraphStyle(
            "SumBadgeLabel", parent=body, fontName=F_MED, fontSize=6.9, leading=9,
            alignment=TA_CENTER, textColor=INK_SOFT, spaceAfter=0, autoLeading="max",
        ),
        "section_tag": ParagraphStyle(
            "SumSectionTag", parent=body, fontName=F_MED, fontSize=7.2, leading=9.6,
            alignment=TA_RIGHT, textColor=MUTED, spaceAfter=0, autoLeading="max",
        ),
        "block": ParagraphStyle(
            "SumBlock", parent=body, fontName=F_REG, fontSize=9.5, leading=13.5,
            textColor=INK_SOFT, spaceAfter=0, autoLeading="max",
        ),
    }


# ============================================================
# Chart & card visual primitives (ReportLab graphics — additive helpers)
# ============================================================

def _bar_drawing(score: float, width: float, height: float = 0.24 * cm, max_score: float = 5.0,
                  color=ACCENT, track=LINE):
    """A single track+fill horizontal bar — always rendered in the ONE accent
    colour (scores are never traffic-light banded in this redesign; red/amber
    are reserved for vulnerability flags and "Not Met" preconditions only).
    Returns a Drawing (a Flowable — usable directly in a story or Table cell).
    """
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=track, strokeColor=None))
    fill_w = max(0.05 * cm, min(width, (max(0.0, float(score or 0)) / max_score) * width))
    d.add(Rect(0, 0, fill_w, height, fillColor=color, strokeColor=None))
    return d


def _dual_bar_drawing(current: float, projected: float, width: float, row_h: float = 0.30 * cm,
                       gap: float = 0.14 * cm, max_score: float = 5.0):
    """Two stacked track+fill bars (Now vs +90 days). Both rendered in the
    single accent colour — a lighter tint for "now", full accent for the
    "+90 day" target — never traffic-light banded."""
    total_h = row_h * 2 + gap
    d = Drawing(width, total_h)
    y_top = row_h + gap
    for y, val, fill_color in ((y_top, current, colors.HexColor("#A8D3D8")), (0, projected, ACCENT)):
        d.add(Rect(0, y, width, row_h, fillColor=LINE, strokeColor=None))
        fill_w = max(0.05 * cm, min(width, (max(0.0, float(val or 0)) / max_score) * width))
        d.add(Rect(0, y, fill_w, row_h, fillColor=fill_color, strokeColor=None))
    return d


def _timeline_drawing(width: float, n: int = 3, height: float = 0.95 * cm):
    """Slim horizontal timeline connector with numbered milestone nodes,
    evenly centred so it lines up with an n-column Table placed beneath it."""
    d = Drawing(width, height)
    y = height * 0.55
    margin = width / (2 * n)
    usable = width - 2 * margin
    xs = [margin + (usable * i / (n - 1) if n > 1 else 0) for i in range(n)]
    d.add(Line(xs[0], y, xs[-1], y, strokeColor=LINE, strokeWidth=1.2))
    for i, x in enumerate(xs):
        d.add(Circle(x, y, 8, fillColor=ACCENT, strokeColor=colors.white, strokeWidth=1.4))
        d.add(String(x, y - 2.6, str(i + 1), fontName=F_BOLD, fontSize=7.6,
                     fillColor=colors.white, textAnchor="middle"))
    return d


def _pillar_score_cards(scores: dict, bottleneck: str, styles):
    """Four equal-width score cards — replaces the radar/spider chart per the
    redesign brief. Each card: pillar name, score /5.0, a thin accent
    progress bar, and (for the bottleneck only) a small outlined tag —
    never a red/amber fill, since colour is reserved for the two flagged
    use-cases elsewhere in the report."""
    col_w = CONTENT_WIDTH / 4.0
    bar_w = col_w - 1.6 * cm
    cells = []
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ]
    for i, dim in enumerate(DIMENSIONS):
        s = float(scores.get(dim, 0) or 0)
        is_bn = (dim == bottleneck)
        tag = (
            '<br/><font size="6.2" color="#0B4F5E">&#9679; BOTTLENECK PILLAR</font>'
            if is_bn else ""
        )
        cell = [
            Paragraph(
                f'<font color="#94A3B8" size="7"><b>{_pillar_label(dim).upper()}</b></font><br/>'
                f'<font color="#111827" size="21"><b>{s:.1f}</b></font>'
                f'<font color="#94A3B8" size="9"> /5.0</font>{tag}',
                styles["card_body_center"],
            ),
            Spacer(0, 7),
            _bar_drawing(s, bar_w, height=0.22 * cm),
        ]
        cells.append(cell)
        if is_bn:
            style_cmds.append(("BOX", (i, 0), (i, 0), 0.9, ACCENT))
        if i > 0:
            style_cmds.append(("LINEBEFORE", (i, 0), (i, 0), 0.6, LINE))
    return Table([cells], colWidths=[col_w] * 4, style=TableStyle(style_cmds))


def _kpi_card_row(overall: float, overall_level: str, bottleneck_label: str,
                   bottleneck_level: str, dbi_gap: float, dbi_direction: str, styles):
    """Three equal-width, neutral stat cards (Overall Score / Bottleneck
    Pillar / Bottleneck Level) — a single-row Table so all three share one
    auto height. Neutral white/light-grey per the redesign brief; the ONE
    accent colour carries the headline numbers."""
    sign = "+" if (dbi_gap or 0) >= 0 else ""
    direction_txt = (dbi_direction or "").replace("-", " ").strip()

    c1 = Paragraph(
        f'<font size="7" color="#94A3B8"><b>OVERALL SCORE</b></font><br/>'
        f'<font size="23" color="#0E7490"><b>{overall:.2f}</b></font>'
        f'<font size="10" color="#94A3B8"> /5.0</font><br/>'
        f'<font size="8.5" color="#475569">{overall_level}</font>',
        styles["card_body_center"],
    )
    c2 = Paragraph(
        f'<font size="7" color="#94A3B8"><b>BOTTLENECK PILLAR</b></font><br/>'
        f'<font size="16" color="#111827"><b>{bottleneck_label}</b></font><br/>'
        f'<font size="7.6" color="#94A3B8">{sign}{dbi_gap:.2f} vs. average'
        + (f" &nbsp;\u00b7&nbsp; {direction_txt}" if direction_txt else "") + '</font>',
        styles["card_body_center"],
    )
    c3 = Paragraph(
        f'<font size="7" color="#94A3B8"><b>BOTTLENECK LEVEL</b></font><br/>'
        f'<font size="16" color="#0E7490"><b>{bottleneck_level}</b></font><br/>'
        f'<font size="7.6" color="#94A3B8">Hannila L1&ndash;L5 ladder</font>',
        styles["card_body_center"],
    )
    col_w = CONTENT_WIDTH / 3.0
    row = Table(
        [[c1, c2, c3]], colWidths=[col_w, col_w, col_w],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LINEAFTER", (0, 0), (0, 0), 0.6, LINE),
            ("LINEAFTER", (1, 0), (1, 0), 0.6, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 13),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]),
    )
    return row


def _precondition_grid(preconditions: dict, styles):
    """Five-item checklist grid. Every card shares the SAME neutral white
    background and thin grey border — only the status word's text colour
    (and a 2pt top rule) changes per status, and "not met" is the only
    state that uses red (per the redesign brief's "use red sparingly")."""
    row = []
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, (key, label) in enumerate(PRECONDITION_LABELS.items()):
        status = (preconditions.get(key) or "partial").lower()
        text_color, rule_color = STATUS_STYLE.get(status, STATUS_STYLE["partial"])
        cell = Paragraph(
            f'<font color="#64748B"><b>{label}</b></font><br/><br/>'
            f'<font size="9" color="{text_color.hexval()}"><b>{status.upper()}</b></font>',
            styles["badge_label"],
        )
        row.append(cell)
        style_cmds.append(("LINEABOVE", (i, 0), (i, 0), 2.2, rule_color))
        if i > 0:
            style_cmds.append(("LINEBEFORE", (i, 0), (i, 0), 0.6, LINE))
    col_w = CONTENT_WIDTH / 5.0
    return Table([row], colWidths=[col_w] * 5, style=TableStyle(style_cmds))


def _vulnerability_badge(level_text: str, styles):
    """Vulnerability rating cell: Critical/High get a small coloured badge;
    Medium/Low render as plain neutral text (colour used sparingly)."""
    key = (level_text or "").strip().lower()
    text_color, bg = VULN_STYLE.get(key, (INK_SOFT, None))
    label = (level_text or "\u2014").upper()
    if bg is None:
        return Paragraph(f'<font color="{text_color.hexval()}">{label}</font>', styles["card_label"])
    pill = Table(
        [[Paragraph(f'<font color="{text_color.hexval()}"><b>{label}</b></font>', styles["card_label"])]],
        colWidths=[2.6 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
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

def _page_title_block(eyebrow_text: str, title_html: str, styles):
    """Consistent in-body page opener: small accent eyebrow + big headline,
    followed by a thin rule. The repeating report title / company name /
    page number chrome lives in the canvas header+footer (see
    `_page_chrome`), so this stays lean — just this page's own headline."""
    return [
        Paragraph(eyebrow_text, styles["eyebrow"]),
        Paragraph(title_html, styles["h1"]),
        HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceBefore=8, spaceAfter=14),
    ]


def _build_page1(story, report, styles, assessment):
    """PAGE 1 — THE VERDICT."""
    scores = report.get("scores") or {}
    overall = float(scores.get("overall") or report.get("equal_weighted_score") or 0)
    bottleneck = _pillar_from_dbi(report)
    level_names = report.get("level_names") or {}
    bottleneck_level = _capitalise_level(level_names.get(bottleneck, "")) or "Developing"
    overall_level = _capitalise_level(level_names.get("overall", "")) or bottleneck_level
    dbi = report.get("decision_bottleneck_index") or {}
    dbi_gap = float(dbi.get("gap", 0.0) or 0.0)
    dbi_direction = (dbi.get("direction") or "").replace("-", " ")

    story.extend(_page_title_block(
        "EXECUTIVE SUMMARY &middot; PAGE 1 OF 4".replace("&middot;", "\u00b7"),
        "The Verdict", styles,
    ))

    # --- KPI stat card row ---
    story.append(_kpi_card_row(overall, overall_level, _pillar_label(bottleneck),
                                bottleneck_level, dbi_gap, dbi_direction, styles))
    story.append(Spacer(0, 16))

    # --- Four pillar score cards (replaces the radar/spider chart) ---
    story.append(Paragraph("PILLAR SCORES", styles["eyebrow"]))
    story.append(_pillar_score_cards(scores, bottleneck, styles))
    story.append(Spacer(0, 14))

    verdict = (
        f"Your portfolio decision capability is operating at <b>{bottleneck_level}</b>. "
        f"Your weakest capability is <b>{_pillar_label(bottleneck)}</b>, which caps what the rest "
        f"of the organisation can reliably deliver."
    )
    story.append(Paragraph(verdict, styles["lead"]))
    story.append(Spacer(0, 8))

    # --- Failure pattern card (thin accent rule + title + narrative) ---
    fp_name = report.get("failure_pattern_name") or _fallback_failure_pattern(bottleneck, report)
    fp_narrative = report.get("failure_pattern_narrative") or (
        f"The {bottleneck} pillar is the binding constraint on portfolio decisions today. "
        f"Decisions that depend on this pillar arrive with insufficient evidence and stall or drift. "
        f"The organisation is missing the operational capability to close this loop consistently."
    )
    fp_card = Table(
        [[Paragraph(
            f'<font color="#0E7490" size="7.5"><b>FAILURE PATTERN</b></font><br/>'
            f'<font color="#111827" size="13"><b>{fp_name}</b></font><br/><br/>'
            f'<font color="#475569" size="9.5">{fp_narrative}</font>',
            styles["block"],
        )]],
        colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LINEBEFORE", (0, 0), (0, 0), 2.5, ACCENT),
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
        story.append(Table(
            [[Paragraph(line, styles["block"])]],
            colWidths=[CONTENT_WIDTH],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT_TINT),
                ("BOX", (0, 0), (-1, -1), 0.6, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]),
        ))

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

    story.extend(_page_title_block(
        "EXECUTIVE SUMMARY &middot; PAGE 2 OF 4".replace("&middot;", "\u00b7"),
        "Your #1 Action", styles,
    ))

    headline_card = Table(
        [[Paragraph(f'<font color="#111827" size="12.5"><b>{headline}</b></font>', styles["block"])]],
        colWidths=[CONTENT_WIDTH],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT_TINT),
            ("LINEBEFORE", (0, 0), (0, 0), 2.5, ACCENT),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    )
    story.append(headline_card)
    story.append(Spacer(0, 10))

    story.append(Paragraph("WHAT TO DO", styles["eyebrow"]))
    story.append(Paragraph(description, styles["lead"]))
    story.append(Spacer(0, 6))

    # Owner + timing + outcome — 3 aligned cards, equal height (single row Table)
    meta_tbl = Table(
        [[
            Paragraph('<font color="#0E7490" size="6.8"><b>WHO OWNS IT</b></font><br/><br/>'
                      f'<font color="#111827" size="10"><b>{who_owns_it}</b></font>', styles["block"]),
            Paragraph('<font color="#0E7490" size="6.8"><b>TIME TO IMPLEMENT</b></font><br/><br/>'
                      f'<font color="#111827" size="10"><b>{time_to_implement}</b></font>', styles["block"]),
            Paragraph('<font color="#0E7490" size="6.8"><b>EXPECTED OUTCOME</b></font><br/><br/>'
                      f'<font color="#111827" size="9.3">{expected_outcome}</font>', styles["block"]),
        ]],
        colWidths=[CONTENT_WIDTH * 0.26, CONTENT_WIDTH * 0.24, CONTENT_WIDTH * 0.50],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LINEAFTER", (0, 0), (0, 0), 0.6, LINE),
            ("LINEAFTER", (1, 0), (1, 0), 0.6, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]),
    )
    story.append(meta_tbl)
    story.append(Spacer(0, 14))

    # Preconditions — 5-item checklist grid (neutral cards, coloured text only)
    story.append(Paragraph("PRECONDITIONS", styles["eyebrow"]))
    story.append(_precondition_grid(preconditions, styles))
    story.append(Spacer(0, 14))

    # Governance signal (2B) — a SEPARATE short field, not a copy of critical_gaps.
    story.append(Paragraph("GOVERNANCE SIGNAL", styles["eyebrow"]))
    gov_summary = report.get("governance_signal_summary") or []
    bullets = []
    if isinstance(gov_summary, list) and any(gov_summary):
        for b in gov_summary:
            if isinstance(b, str) and b.strip():
                bullets.append(f"<font color='#0E7490'>&bull;</font> {b.strip()}")
    else:
        # Legacy fallback: distil from critical_gaps + a positive finding.
        critical_gaps = report.get("critical_gaps") or []
        key_findings = report.get("key_findings") or []
        gaps = [g for g in critical_gaps[:2] if g]
        positive = next((f for f in key_findings if isinstance(f, str) and any(
            w in f.lower() for w in ("strong", "clear", "established", "documented", "consistent")
        )), None)
        for g in gaps:
            bullets.append(f"<font color='#0E7490'>&bull;</font> {g}")
        if positive:
            bullets.append(f"<font color='#0E7490'>&bull;</font> {positive}")
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
    story.append(Spacer(0, 14))

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
        Paragraph('<font color="#0E7490" size="8"><b>90-DAY PROJECTION</b></font>', styles["block"]),
        Spacer(0, 8),
        _dual_bar_drawing(sc, sp, width=5.0 * cm),
        Spacer(0, 5),
        Paragraph(
            f'<font size="7.3" color="#94A3B8">NOW</font>  <b>{sc:.1f}</b>/5.0'
            f'&nbsp;&nbsp;&#8594;&nbsp;&nbsp;<font size="7.3" color="#94A3B8">+90 DAYS</font>  '
            f'<b>{sp:.1f}</b>/5.0&nbsp;&nbsp;<font size="7.3" color="#0E7490">(+{sd:.1f})</font>',
            styles["block"],
        ),
        Spacer(0, 6),
        Paragraph(f'<font size="8" color="#475569">Bottleneck level:<br/><b>{bl_c}</b> &#8594; <b>{bl_p}</b></font>',
                  styles["block"]),
    ]
    right_cell = [
        Paragraph(f'<b>What becomes possible:</b><br/>{possible}', styles["block"]),
        Spacer(0, 8),
        Paragraph(f'<i>Comparable outcome:</i> {comparable}', styles["note"]),
    ]
    proj_tbl = Table(
        [[left_cell, right_cell]],
        colWidths=[6.0 * cm, CONTENT_WIDTH - 6.0 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), BG_ALT),
            ("BACKGROUND", (1, 0), (1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LINEAFTER", (0, 0), (0, 0), 0.6, LINE),
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

    story.extend(_page_title_block(
        "EXECUTIVE SUMMARY &middot; PAGE 3 OF 4".replace("&middot;", "\u00b7"),
        "Your Roadmap", styles,
    ))

    # Visual timeline connector + aligned 3-column phase-window labels
    story.append(_timeline_drawing(CONTENT_WIDTH, n=3))
    col_w = CONTENT_WIDTH / 3.0
    story.append(Table(
        [[
            Paragraph('<font color="#111827" size="9.5"><b>THIS MONTH</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">0\u201330 days</font>', styles["card_body_center"]),
            Paragraph('<font color="#111827" size="9.5"><b>THIS QUARTER</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">30\u201390 days</font>', styles["card_body_center"]),
            Paragraph('<font color="#111827" size="9.5"><b>THIS YEAR</b></font><br/>'
                      '<font color="#94A3B8" size="7.3">90\u2013365 days</font>', styles["card_body_center"]),
        ]],
        colWidths=[col_w, col_w, col_w],
        style=TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]),
    ))
    story.append(Spacer(0, 16))

    for i, (phase_key, label, window) in enumerate(RELABEL):
        phase = roadmap.get(phase_key) or {}
        # 2A — Executive Summary renders ONLY the one-sentence action, not the
        # full numbered action list (that detail stays exclusive to the Full Report).
        action = phase.get("action_summary") or _first_sentence(phase.get("actions", "")) or "\u2014"
        pillar_focus = phase.get("pillar_focus") or "\u2014"
        owner = phase.get("management_required") or "\u2014"
        milestone = phase.get("governance_milestone") or ""
        expected_gain = phase.get("expected_gain") or ""

        num_cell = Paragraph(f'<font color="#FFFFFF" size="15"><b>{i + 1}</b></font>', styles["card_body_center"])
        content_cell = [
            Paragraph(
                f'<font color="#0E7490" size="7.6"><b>{label.upper()}</b></font>'
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
                f'<font color="#94A3B8" size="6.6"><b>EXPECTED GAIN</b></font><br/><br/>'
                f'<font color="#0E7490" size="8.5"><b>{expected_gain}</b></font>',
                styles["card_body_center"],
            ) if expected_gain else Paragraph("", styles["block"])
        )

        card = Table(
            [[num_cell, content_cell, gain_cell]],
            colWidths=[1.1 * cm, CONTENT_WIDTH - 1.1 * cm - 4.2 * cm, 4.2 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), ACCENT),
                ("BACKGROUND", (1, 0), (1, 0), colors.white),
                ("BACKGROUND", (2, 0), (2, 0), BG_ALT),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEAFTER", (1, 0), (1, 0), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "CENTER"),
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

    story.extend(_page_title_block(
        "EXECUTIVE SUMMARY &middot; PAGE 4 OF 4".replace("&middot;", "\u00b7"),
        "Full Scorecard Reference", styles,
    ))

    # Compressed pillar table — clean styling: thin header rule + subtle
    # alternating row shading, no heavy grid/box borders. Score column
    # carries a real mini bar-chart (single accent colour, not banded).
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
        score_cell = [
            Paragraph(f'<font color="#0E7490"><b>{s:.1f}</b></font>', styles["body"]),
            Spacer(0, 2),
            _bar_drawing(s, 2.0 * cm, height=0.2 * cm),
        ]
        rows.append([
            Paragraph(f"<b>{_pillar_label(dim)}</b>", styles["body"]),
            score_cell,
            Paragraph(lvl, styles["body"]),
            Paragraph(interp or "\u2014", styles["body"]),
        ])
    tbl = Table(
        rows, colWidths=[2.9 * cm, 2.3 * cm, 2.3 * cm, CONTENT_WIDTH - 7.5 * cm],
        style=TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), INK),
            ("FONTNAME", (0, 0), (-1, 0), F_SEMI),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]),
    )
    story.append(tbl)
    story.append(Spacer(0, 14))

    # Management commitment + assessment reliability — two aligned info cards
    story.append(Table(
        [[
            Paragraph(f'<font color="#94A3B8" size="7"><b>MANAGEMENT COMMITMENT</b></font><br/>'
                      f'<font color="#111827" size="11"><b>{mgmt}</b></font>', styles["block"]),
            Paragraph(f'<font color="#94A3B8" size="7"><b>ASSESSMENT RELIABILITY</b></font><br/>'
                      f'<font color="#111827" size="11"><b>{reliability}</b></font>', styles["block"]),
        ]],
        colWidths=[CONTENT_WIDTH / 2.0, CONTENT_WIDTH / 2.0],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, LINE),
            ("LINEAFTER", (0, 0), (0, 0), 0.6, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]),
    ))
    story.append(Spacer(0, 14))

    # Decision-type vulnerability — clean table, colour used sparingly
    # (only Critical/High get a coloured badge; Medium/Low are plain text)
    story.append(Paragraph("DECISION-TYPE VULNERABILITY", styles["eyebrow"]))
    dvr_labels = [
        ("Discontinuation", dvr.get("discontinuation", "\u2014")),
        ("New product launch", dvr.get("new_launch", "\u2014")),
        ("Product change", dvr.get("product_change", "\u2014")),
        ("Portfolio investment", dvr.get("portfolio_investment", "\u2014")),
    ]
    dvr_rows = [["Decision type", "Vulnerability"]]
    for name, level in dvr_labels:
        dvr_rows.append([Paragraph(name, styles["body"]), _vulnerability_badge(level, styles)])
    dvr_tbl = Table(
        dvr_rows, colWidths=[CONTENT_WIDTH - 3.4 * cm, 3.4 * cm],
        style=TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), INK),
            ("FONTNAME", (0, 0), (-1, 0), F_SEMI),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_ALT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]),
    )
    story.append(dvr_tbl)
    story.append(Spacer(0, 16))
    story.append(Paragraph(
        "This Executive Summary is a companion to the full 15-page PortfolioHealth report. "
        "Detailed methodology, weighted-score calculation tables, and academic citations are exclusive "
        "to the Full Report.",
        styles["caption"],
    ))


# ============================================================
# Page chrome — consistent header + footer with correct page numbering
# ============================================================

def _make_page_chrome(company_name: str):
    """Factory returning a canvas callback used on every page: report title,
    company name, page number, and a subtle 'PortfolioHealth Advisor' brand
    line — drawn once here so all 4 pages stay pixel-identical.

    (Also fixes a real bug from an earlier version that reused the full
    report's page-decoration function, which assumes a cover+TOC and prints
    `doc.page - 2` — this report has no cover/TOC, so every page is numbered
    directly as "Page X of 4".)
    """
    def _decoration(canvas, doc):
        canvas.saveState()
        page_width, page_height = A4
        left = MARGIN
        right = page_width - MARGIN

        # Top: subtle brand line (left) + company name (right), hairline below
        canvas.setFont(F_SEMI, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(left, page_height - 22, "PORTFOLIOHEALTH ADVISOR  \u00b7  EXECUTIVE SUMMARY")
        canvas.setFont(F_SEMI, 8)
        canvas.setFillColor(INK)
        canvas.drawRightString(right, page_height - 22, company_name)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(left, page_height - 29, right, page_height - 29)

        # Bottom: hairline + subtle brand line (left) + page number (right)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(left, 34, right, 34)
        canvas.setFont(F_REG, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(left, 22, "PortfolioHealth Advisor \u2014 PPM Capability Maturity Assessment")
        canvas.drawRightString(right, 22, f"Page {doc.page} of 4")
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
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="PortfolioHealth — Executive Summary",
    )
    styles = _styles()
    story: list[Any] = []

    _build_page1(story, report, styles, assessment)
    _build_page2(story, report, styles)
    _build_page3(story, report, styles)
    _build_page4(story, report, styles)

    decoration = _make_page_chrome(company_name)
    doc.build(story, onFirstPage=decoration, onLaterPages=decoration)
    buffer.seek(0)
    return buffer
