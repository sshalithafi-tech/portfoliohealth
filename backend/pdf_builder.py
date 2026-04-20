"""
PDF builder helpers for PortfolioHealth Advisor reports.

Contains section-building functions used by the FastAPI routes in
`server.py` to keep route handlers small and focused.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi"
DIMENSIONS = ["people", "process", "data", "technology"]

# --- Brand palette (Deep Navy Corporate) ---
NAVY = colors.HexColor('#0A1628')
NAVY_DEEP = colors.HexColor('#1A1A2E')
GOLD = colors.HexColor('#C9A84C')
GOLD_BG = colors.HexColor('#FAF6E8')
GOLD_HILITE = colors.HexColor('#EEE8D5')
TEXT_DARK = colors.HexColor('#333333')
TEXT_MUTED = colors.HexColor('#666666')
ROW_ALT = colors.HexColor('#F8F8F8')
LINE_LIGHT = colors.HexColor('#E0E0E0')

# Hannila L1–L5 maturity ladder definitions (mirrors the web MaturityLevelsPanel)
MATURITY_LADDER = [
    ("L1", "Ad Hoc",      "No structured approach. Decisions are reactive, informal, based on individual intuition. Data is inaccessible or unreliable."),
    ("L2", "Developing",  "Some processes are defined but inconsistently applied. Basic data collection exists but lacks integration. A few PPM practices emerging."),
    ("L3", "Defined",     "Structured processes and roles are established. Data is accessible but not fully integrated. A formal PPM discipline is in place."),
    ("L4", "Managed",     "Data-driven decisions are supported by integrated systems. Metrics are defined and tracked. PPM is aligned to strategy."),
    ("L5", "Optimising",  "Continuous improvement culture is embedded. An end-to-end PPDT discipline is fully aligned. Predictive, evidence-based decisions."),
]


# ============================================================
# STYLE FACTORIES
# ============================================================

def make_report_styles():
    """Build the ParagraphStyle set used across full + quick PDF reports."""
    base = getSampleStyleSheet()
    return {
        "base": base,
        "heading": ParagraphStyle(
            'Heading', parent=base['Heading2'], fontSize=12, spaceAfter=6, spaceBefore=10,
            textColor=NAVY, fontName='Helvetica-Bold'
        ),
        "body": ParagraphStyle(
            'Body', parent=base['Normal'], fontSize=9.5, spaceAfter=5, leading=13, textColor=TEXT_DARK
        ),
        "gov": ParagraphStyle(
            'Governance', parent=base['Normal'], fontSize=9, spaceAfter=4,
            textColor=colors.HexColor('#5C4A1E'), backColor=GOLD_BG,
            borderPadding=6, borderColor=GOLD, borderWidth=0.5, leading=12
        ),
        "closing": ParagraphStyle(
            'Closing', parent=base['Normal'], fontSize=9, textColor=TEXT_DARK,
            borderPadding=12, backColor=GOLD_BG, borderColor=GOLD,
            borderWidth=1, leading=13
        ),
        "footer": ParagraphStyle(
            'Footer', fontSize=7.5, textColor=colors.HexColor('#999999'),
            alignment=1, spaceBefore=12
        ),
    }


# ============================================================
# COVER PAGE  &  PAGE DECORATIONS
# ============================================================

def _page_decoration(canvas, doc):
    """Slim brand strip at the bottom of every content page (not the cover)."""
    if doc.page == 1:
        return  # cover owns its own decoration
    canvas.saveState()
    page_width = A4[0]
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.4)
    canvas.line(50, 40, page_width - 50, 40)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(
        50, 26,
        "PortfolioHealth Advisor  ·  PPM Capability Maturity Assessment  ·  University of Oulu",
    )
    canvas.drawRightString(page_width - 50, 26, f"Page {doc.page - 1}")
    canvas.restoreState()


def build_cover_page(story, assessment, report):
    """Full-page branded cover: title, company card, headline score, date.

    Renders on page 1 and is terminated by a PageBreak, so all subsequent
    numbered sections get a clean top-of-page start.
    """
    # Tall navy banner that occupies the top half of the cover page
    brand_title = Paragraph(
        '<font size="30" color="#FFFFFF"><b>PortfolioHealth</b></font>'
        '<font size="30" color="#C9A84C"><b> Advisor</b></font>',
        ParagraphStyle("CovBrand", leading=36),
    )
    brand_sub = Paragraph(
        '<font size="10" color="#C9A84C"><b>PPM CAPABILITY MATURITY ASSESSMENT</b></font>',
        ParagraphStyle("CovBrandSub", leading=14, spaceBefore=8),
    )
    report_title = Paragraph(
        '<font size="16" color="#FFFFFF">Capability Maturity Report</font>',
        ParagraphStyle("CovReportTitle", leading=22, spaceBefore=48),
    )

    banner = Table(
        [[brand_title], [brand_sub], [report_title]],
        colWidths=[490],
    )
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 32),
        ('RIGHTPADDING', (0, 0), (-1, -1), 32),
        ('TOPPADDING', (0, 0), (0, 0), 48),
        ('TOPPADDING', (0, 1), (0, 1), 6),
        ('TOPPADDING', (0, 2), (0, 2), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 56),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(banner)

    # Thin gold accent rule
    accent = Table([[""]], colWidths=[490], rowHeights=[4])
    accent.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), GOLD)]))
    story.append(accent)
    story.append(Spacer(1, 40))

    # PREPARED FOR — company name + industry
    company_name = assessment.get("company_name", "—")
    industry = assessment.get("company_industry", "")
    prepared_label = Paragraph(
        '<font size="9" color="#C9A84C"><b>PREPARED FOR</b></font>',
        ParagraphStyle("PrepLabel", leading=12),
    )
    company = Paragraph(
        f'<font size="28" color="#0A1628"><b>{company_name}</b></font>',
        ParagraphStyle("CovCompany", leading=32, spaceBefore=4),
    )
    industry_p = (
        Paragraph(
            f'<font size="11" color="#666666">{industry}</font>',
            ParagraphStyle("CovIndustry", leading=14, spaceBefore=4),
        )
        if industry else None
    )
    prep_cells = [[prepared_label], [company]]
    if industry_p:
        prep_cells.append([industry_p])
    prep = Table(prep_cells, colWidths=[490])
    prep.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 32),
        ('RIGHTPADDING', (0, 0), (-1, -1), 32),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(prep)
    story.append(Spacer(1, 36))

    # Headline maturity card (overall score + level) centered on the page
    scores = report.get("scores", {}) or {}
    overall = scores.get("overall")
    level_names = report.get("level_names", {}) or {}
    overall_level = level_names.get("overall") or _derive_level_name(overall)
    if overall is None:
        overall_text = "—"
    else:
        try:
            overall_text = f"{float(overall):.2f}"
        except (TypeError, ValueError):
            overall_text = str(overall)

    score_badge = Paragraph(
        f'<font size="8" color="#666666"><b>OVERALL MATURITY SCORE</b></font><br/>'
        f'<font size="48" color="#0A1628"><b>{overall_text}</b></font>'
        f'<font size="16" color="#999999"> / 5.00</font><br/>'
        f'<font size="12" color="#C9A84C"><b>{overall_level}</b></font>',
        ParagraphStyle("CovScore", leading=52, alignment=1),  # centered
    )
    badge_table = Table([[score_badge]], colWidths=[490])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD_BG),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, GOLD),
        ('LINEBELOW', (0, 0), (-1, -1), 1.2, GOLD),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 28),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 28),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 40))

    # Footer row: report date + respondent + confidentiality
    report_date = (
        assessment.get("completed_at")
        or assessment.get("created_at")
        or ""
    )[:10] or "—"
    respondent = assessment.get("respondent_name") or "—"
    respondent_role = assessment.get("respondent_role") or ""
    respondent_cell = respondent + (f"  ·  {respondent_role}" if respondent_role else "")

    meta_style = ParagraphStyle("CovMeta", leading=12)
    meta = Table(
        [[
            Paragraph(
                '<font size="7" color="#888888"><b>REPORT DATE</b></font><br/>'
                f'<font size="10" color="#0A1628"><b>{report_date}</b></font>',
                meta_style,
            ),
            Paragraph(
                '<font size="7" color="#888888"><b>RESPONDENT</b></font><br/>'
                f'<font size="10" color="#0A1628"><b>{respondent_cell}</b></font>',
                meta_style,
            ),
        ]],
        colWidths=[245, 245],
    )
    meta.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 32),
        ('RIGHTPADDING', (0, 0), (-1, -1), 32),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6FA')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta)
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        '<font size="7" color="#999999"><i>CONFIDENTIAL  ·  Prepared for the named organisation only.  '
        'Distribution without authorisation is not permitted.</i></font>',
        ParagraphStyle("CovConfidential", leading=10, alignment=1),
    ))

    story.append(PageBreak())


# ============================================================
# HEADER & FOOTER
# ============================================================

def build_pdf_header(story, styles, title_text=""):
    """Professional PDF header for management-level reports."""
    brand_style = ParagraphStyle('BrandName', fontSize=20, fontName='Helvetica-Bold',
                                 textColor=colors.white, leading=24)
    sub_style = ParagraphStyle('BrandSub', fontSize=8, textColor=colors.HexColor('#8899AA'),
                               leading=10)

    brand_content = Table([
        [Paragraph("PortfolioHealth Advisor", brand_style)],
        [Paragraph("PPM Capability Maturity Assessment  |  University of Oulu", sub_style)]
    ], colWidths=[450])
    brand_content.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    header_bar = Table([[brand_content]], colWidths=[490], rowHeights=[56])
    header_bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_DEEP),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_bar)

    accent_line = Table([[""]], colWidths=[490], rowHeights=[3])
    accent_line.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), GOLD)]))
    story.append(accent_line)
    story.append(Spacer(1, 20))

    if title_text:
        title_style = ParagraphStyle('ReportTitle', fontName='Helvetica-Bold',
                                     fontSize=16, spaceAfter=8, textColor=NAVY)
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 6))


def build_pdf_closing(story, styles):
    """Professional closing statement for PDF reports."""
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        f"Thank you for completing this assessment. For further analysis, expert input, or tailored "
        f"recommendations, please contact: <b>{CONTACT_EMAIL}</b>",
        styles["closing"]
    ))
    story.append(Spacer(1, 16))
    footer_line = Table([[""]], colWidths=[490], rowHeights=[1])
    footer_line.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC'))]))
    story.append(footer_line)
    story.append(Paragraph("PortfolioHealth Advisor  |  PPM Capability Maturity Assessment  |  University of Oulu",
                           styles["footer"]))
    story.append(Paragraph("This report is confidential. Distribution without authorisation is not permitted.",
                           styles["footer"]))


# ============================================================
# FULL ASSESSMENT SECTIONS
# ============================================================

def build_section_label(story, styles, number: int, title: str, subtitle: str = ""):
    """Numbered section header: '01  PORTFOLIO CONTEXT' with optional italic subtitle.

    Mirrors the web report's numbered section layout."""
    label_style = ParagraphStyle(
        'SectionLabel', fontSize=11, fontName='Helvetica-Bold',
        textColor=NAVY, spaceAfter=2, spaceBefore=14, leading=14,
    )
    sub_style = ParagraphStyle(
        'SectionSubtitle', fontSize=8, fontName='Helvetica-Oblique',
        textColor=TEXT_MUTED, spaceAfter=8, leading=10,
    )
    story.append(Paragraph(
        f'<font color="#C9A84C">{number:02d}</font>&nbsp;&nbsp;{title.upper()}',
        label_style,
    ))
    if subtitle:
        story.append(Paragraph(subtitle, sub_style))
    # Thin gold underline
    rule = Table([[""]], colWidths=[490], rowHeights=[1])
    rule.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.6, GOLD)]))
    story.append(rule)
    story.append(Spacer(1, 6))


def build_portfolio_context(story, assessment, report, body):
    """01 — Portfolio Context. Expanded from the old company_info card to mirror
    the web PortfolioContext component: company, industry, size, business model,
    active products, strategic priority, respondent, date."""
    company_size = (
        assessment.get('company_size')
        or assessment.get('portfolio_size')
        or report.get('company_size')
        or report.get('portfolio_size')
    )
    active_products = (
        report.get('active_products')
        or assessment.get('active_products')
        or report.get('num_products')
    )
    bm = report.get('business_model')
    sp = report.get('strategic_priority')
    date_str = (assessment.get('completed_at') or assessment.get('created_at') or 'N/A')[:10]

    rows = [
        ("Company", assessment.get('company_name', 'N/A')),
        ("Industry", assessment.get('company_industry', 'N/A')),
        ("Company Size", company_size or "\u2013"),
        ("Business Model", bm or "\u2013"),
        ("Active Products", active_products or "\u2013"),
        ("Strategic Priority", sp or "\u2013"),
        ("Respondent", f"{assessment.get('respondent_name', 'N/A')} ({assessment.get('respondent_role', 'N/A')})"),
        ("Date", date_str),
    ]
    data = [[Paragraph(f"<b>{k}</b>", body), Paragraph(str(v), body)] for k, v in rows]
    table = Table(data, colWidths=[130, 360])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), GOLD_BG),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, LINE_LIGHT),
        ('LINEABOVE', (0, 0), (-1, 0), 0.8, GOLD),
        ('LINEBELOW', (0, -1), (-1, -1), 0.8, GOLD),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)

    note = report.get('business_model_note')
    if note:
        note_style = ParagraphStyle(
            'ContextNote', fontSize=8, fontName='Helvetica-Oblique',
            textColor=TEXT_MUTED, spaceBefore=6, leading=10,
        )
        story.append(Paragraph(note, note_style))
    story.append(Spacer(1, 14))


def build_company_info(story, assessment, report, body):
    """Kept for backwards compatibility — delegates to portfolio_context."""
    build_portfolio_context(story, assessment, report, body)


def build_overall_score(story, scores, report, level_names, heading, body):
    equal = scores.get("overall", "N/A")
    ctx = report.get("contextual_score")
    lvl_overall = level_names.get("overall") or _derive_level_name(equal)
    # Dual-score card as a 2-col table
    eq_cell = Paragraph(
        f'<font size="7" color="#C9A84C"><b>EQUAL-WEIGHTED SCORE · PRIMARY</b></font><br/>'
        f'<font size="22" color="#0A1628"><b>{equal}</b></font>'
        f'<font size="10" color="#999999"> / 5.00</font><br/>'
        f'<font size="10"><b>{lvl_overall}</b></font><br/>'
        f'<font size="7" color="#666666"><i>Academically validated baseline (25% each pillar)</i></font>',
        body,
    )
    if isinstance(ctx, (int, float)):
        ctx_cell = Paragraph(
            f'<font size="7" color="#666666"><b>CONTEXTUAL SCORE · SECONDARY</b></font><br/>'
            f'<font size="22" color="#0A1628"><b>{ctx:.2f}</b></font>'
            f'<font size="10" color="#999999"> / 5.00</font><br/>'
            f'<font size="7" color="#666666"><i>Adjusted for business model + stated priority</i></font>',
            body,
        )
    else:
        ctx_cell = Paragraph(
            '<font size="7" color="#666666"><b>CONTEXTUAL SCORE · SECONDARY</b></font><br/>'
            '<font size="10" color="#999999"><i>Not yet calculated for this assessment.</i></font>',
            body,
        )
    card = Table([[eq_cell, ctx_cell]], colWidths=[245, 245])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD_BG),
        ('LINEABOVE', (0, 0), (-1, 0), 1, GOLD),
        ('LINEBELOW', (0, -1), (-1, -1), 1, GOLD),
        ('LINEAFTER', (0, 0), (0, 0), 0.5, LINE_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(card)
    story.append(Spacer(1, 12))


def build_pillar_maturity_levels(story, scores, report, body):
    """03 — Pillar Maturity Levels (L1\u2013L5). Hannila ladder + each pillar's level."""
    # The L1\u2013L5 ladder (mirrors the web MaturityLevelsPanel)
    ladder_style = ParagraphStyle(
        'Ladder', fontSize=7.5, textColor=TEXT_DARK, leading=10.5, spaceAfter=0
    )
    ladder_data = [[
        Paragraph(
            f'<font color="#C9A84C" size="9"><b>{lvl}</b></font><br/>'
            f'<font color="#0A1628" size="9"><b>{name}</b></font><br/><br/>'
            f'<font color="#666666">{desc}</font>',
            ladder_style,
        )
        for (lvl, name, desc) in MATURITY_LADDER
    ]]
    ladder = Table(ladder_data, colWidths=[98, 98, 98, 98, 98])
    ladder.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6FA')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBEFORE', (1, 0), (-1, -1), 0.3, LINE_LIGHT),
        ('LINEABOVE', (0, 0), (-1, 0), 0.6, GOLD),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, GOLD),
    ]))
    story.append(ladder)
    story.append(Spacer(1, 14))

    # Per-pillar interpretations
    cell_style = ParagraphStyle("PillarCell", fontSize=8.5, leading=11, textColor=TEXT_DARK)
    header = ["Pillar", "Score", "Level", "Interpretation"]
    interp_data = [header]
    pillar_interps = report.get("pillar_interpretations", {}) or {}
    level_names = report.get("level_names", {}) or {}
    for dim in DIMENSIONS:
        s = scores.get(dim, 0)
        lvl = level_names.get(dim) or _derive_level_name(s)
        interp = pillar_interps.get(dim, "") or "\u2013"
        interp_data.append([
            Paragraph(f"<b>{dim.capitalize()}</b>", cell_style),
            Paragraph(str(s), cell_style),
            Paragraph(lvl, cell_style),
            Paragraph(interp, cell_style),
        ])
    table = Table(interp_data, colWidths=[70, 45, 85, 290], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, LINE_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))


def _derive_level_name(score):
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "\u2013"
    if s < 1.5:
        return "Ad Hoc"
    if s < 2.5:
        return "Developing"
    if s < 3.5:
        return "Defined"
    if s < 4.5:
        return "Managed"
    return "Optimising"


def build_assessment_reliability(story, report, assessment, body):
    """09 — Assessment Reliability. High/Medium/Low confidence + evidence signals."""
    provided = report.get("assessment_reliability")
    if isinstance(provided, dict):
        confidence = str(provided.get("confidence", "Medium")).capitalize()
        factors = provided.get("factors") or []
    elif isinstance(provided, str) and provided:
        confidence = provided.capitalize()
        factors = []
    else:
        # Heuristic fallback mirroring the web AssessmentReliability component
        factors = []
        data_score = float((report.get("scores") or {}).get("data") or 0)
        if data_score and data_score < 2:
            factors.append({"label": "Data Availability", "detail": "Limited product-level profitability data.", "tone": "low"})
        elif data_score and data_score < 3:
            factors.append({"label": "Data Availability", "detail": "Partial product-level data; some evidence self-reported.", "tone": "medium"})
        elif data_score:
            factors.append({"label": "Data Availability", "detail": "Product-level data is accessible enough to ground findings.", "tone": "high"})
        factors.append({
            "label": "Respondent Scope",
            "detail": f"Single respondent ({assessment.get('respondent_role', 'individual view')}) \u2014 not cross-functionally triangulated.",
            "tone": "medium",
        })
        factors.append({"label": "Answer Clarity", "detail": "Based on the respondent's self-reported evidence captured in the conversation.", "tone": "medium"})
        low_count = sum(1 for f in factors if f.get("tone") == "low")
        if low_count >= 2:
            confidence = "Low"
        elif all(f.get("tone") == "high" for f in factors):
            confidence = "High"
        else:
            confidence = "Medium"

    tone_color = {"High": "#34A853", "Medium": "#C9A84C", "Low": "#C0392B"}.get(confidence, "#C9A84C")
    blurb = {
        "High": "Results are well-supported by the evidence shared during the assessment.",
        "Medium": "Directionally sound \u2014 some signals are self-reported or based on a single respondent.",
        "Low": "Treat as indicative only \u2014 key evidence is missing or comes from a narrow perspective.",
    }.get(confidence, "")

    # Confidence badge row
    badge = Paragraph(
        f'<font size="7" color="#666666"><b>CONFIDENCE</b></font>&nbsp;&nbsp;'
        f'<font size="10" color="{tone_color}"><b>{confidence.upper()}</b></font>',
        body,
    )
    story.append(badge)
    if blurb:
        story.append(Paragraph(blurb, body))
    story.append(Spacer(1, 6))

    if factors:
        cell_style = ParagraphStyle("RelCell", fontSize=8.5, leading=11, textColor=TEXT_DARK)
        data = [["Signal", "Tone", "Detail"]]
        for f in factors:
            tone = str(f.get("tone", "medium")).capitalize()
            data.append([
                Paragraph(f"<b>{f.get('label', '–')}</b>", cell_style),
                Paragraph(tone, cell_style),
                Paragraph(f.get("detail", "") or "\u2013", cell_style),
            ])
        table = Table(data, colWidths=[120, 60, 310], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, GOLD),
            ('LINEBELOW', (0, 1), (-1, -1), 0.3, LINE_LIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(table)
    story.append(Spacer(1, 12))


def build_dimension_scores_table(story, scores, level_names, dim_summaries, heading):
    body_cell = ParagraphStyle(
        "DimCell", fontSize=8.5, leading=11, textColor=TEXT_DARK
    )
    header = ["Dimension", "Score", "Level", "Summary"]
    data = [header]
    for dim in DIMENSIONS:
        summary_raw = dim_summaries.get(dim, "") or "\u2013"
        lvl = level_names.get(dim) or _derive_level_name(scores.get(dim))
        data.append([
            Paragraph(f"<b>{dim.capitalize()}</b>", body_cell),
            Paragraph(str(scores.get(dim, "\u2013")), body_cell),
            Paragraph(lvl, body_cell),
            Paragraph(summary_raw, body_cell),
        ])

    table = Table(data, colWidths=[70, 40, 90, 290], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, LINE_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))


def build_weighted_breakdown(story, scores, weights_raw, weights_norm, heading, body):
    # Methodology one-liner (mirrors the web ScoreMethodology blurb)
    story.append(Paragraph(
        "The overall score is a weighted sum across the four PPDT pillars. "
        "Weights reflect what <b>the organisation</b> declared as most strategically important \u2014 "
        "so a low score in a high-weight pillar has a disproportionate impact on overall maturity.",
        body,
    ))
    story.append(Spacer(1, 6))

    data = [["Pillar", "Raw Score", "Weight", "Contribution"]]
    for dim in DIMENSIONS:
        s = scores.get(dim, 0)
        w_norm = weights_norm.get(dim, 0.25)
        data.append([dim.capitalize(), str(s), f"{w_norm * 100:.1f}%", f"{s * w_norm:.2f}"])
    data.append(["", "", "Overall:", f"{scores.get('overall', 0):.2f}"])

    table = Table(data, colWidths=[90, 80, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, ROW_ALT]),
        ('BACKGROUND', (0, -1), (-1, -1), GOLD_HILITE),
        ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, LINE_LIGHT),
        ('LINEABOVE', (0, -1), (-1, -1), 1, GOLD),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))


def build_governance_sections(story, report, heading, body, gov):
    gov_obs = report.get("governance_observations", {}) or {}
    has_gov = any(v and "N/A" not in str(v) and "below" not in str(v).lower() for v in gov_obs.values())
    if has_gov:
        for dim in DIMENSIONS:
            obs = gov_obs.get(dim, "")
            if obs and "N/A" not in str(obs) and "below" not in str(obs).lower():
                story.append(Paragraph(f"<b>{dim.capitalize()} \u2014 Governance:</b> {obs}", gov))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Governance is the connective tissue between all four PPDT dimensions. Without clear "
        "ownership and accountability, even high capability produces unreliable portfolio decisions.",
        body))
    if report.get("governance_assessment"):
        story.append(Paragraph(f"<i>{report['governance_assessment']}</i>", body))
    story.append(Spacer(1, 8))


def build_bottleneck_section(story, report, scores, heading, body):
    """Explicit bottleneck pillar with score + interpretation."""
    bottleneck = report.get("bottleneck_pillar")
    if not bottleneck:
        return
    key = str(bottleneck).lower()
    score = scores.get(key, "N/A")
    story.append(Paragraph(
        f"<b>{bottleneck.capitalize()}</b> (score: {score} / 5) is the lowest-scoring pillar and "
        "caps real-world capability regardless of other scores. The bottleneck is where "
        "capability investment will deliver the highest marginal return.",
        body))
    interp = (report.get("pillar_interpretations") or {}).get(key)
    if interp:
        story.append(Paragraph(f"<i>{interp}</i>", body))
    story.append(Spacer(1, 12))


def build_management_commitment_section(story, report, heading, body):
    """Dedicated management-commitment section with Low/Med/High rating."""
    rating = report.get("management_commitment")
    if rating:
        story.append(Paragraph(f"<b>Rating:</b> {rating}", body))
    story.append(Paragraph(
        "Management commitment acts as a multiplier on all capability investments. Without "
        "leadership buy-in, PPM improvements produce limited, short-lived change.",
        body))
    if report.get("management_commitment_assessment"):
        story.append(Paragraph(f"<i>{report['management_commitment_assessment']}</i>", body))
    story.append(Spacer(1, 12))


def build_decision_vulnerability_section(story, report, heading, body):
    """Decision-type vulnerability with the 4 risk ratings as a table."""
    ratings = report.get("decision_vulnerability_ratings") or {}
    if ratings:
        data = [["Decision Type", "Risk Level"]]
        labels = [
            ("discontinuation", "Discontinuation"),
            ("new_launch", "New Launch"),
            ("product_change", "Product Change"),
            ("portfolio_investment", "Portfolio Investment"),
        ]
        for key, label in labels:
            data.append([label, str(ratings.get(key, "\u2013"))])
        t = Table(data, colWidths=[200, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, GOLD),
            ('LINEBELOW', (0, 1), (-1, -1), 0.4, LINE_LIGHT),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))
    narrative = report.get("decision_vulnerability", "")
    if narrative:
        story.append(Paragraph(narrative, body))
    story.append(Spacer(1, 12))


def build_findings_and_gaps(story, report, heading, body):
    # Side-by-side on the web; stacked on the PDF for readability.
    story.append(Paragraph('<font color="#0A1628"><b>Key Findings</b></font>', body))
    for item in report.get("key_findings", []) or []:
        story.append(Paragraph(f"\u2022 {item}", body))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<font color="#C0392B"><b>Critical Capability Gaps</b></font>', body))
    for item in report.get("critical_gaps", []) or []:
        story.append(Paragraph(f"\u2022 {item}", body))
    story.append(Spacer(1, 12))


def build_roadmap(story, roadmap, heading, body):
    phases = [
        ("immediate", "PHASE 1 \u2014 IMMEDIATE (0\u20133 months)"),
        ("short_term", "PHASE 2 \u2014 SHORT-TERM (3\u201312 months)"),
        ("strategic", "PHASE 3 \u2014 STRATEGIC (12+ months)"),
    ]
    for key, title in phases:
        phase_data = roadmap.get(key, []) if roadmap else []
        story.append(Paragraph(f"<b>{title}</b>", body))
        if isinstance(phase_data, dict):
            actions = phase_data.get("actions", [])
        else:
            actions = phase_data
        # actions may be a list or a single string
        if isinstance(actions, list):
            for a in actions:
                story.append(Paragraph(f"  \u2022 {a}", body))
        elif isinstance(actions, str) and actions:
            story.append(Paragraph(f"  \u2022 {actions}", body))
        if isinstance(phase_data, dict):
            if phase_data.get("pillar_focus"):
                story.append(Paragraph(f"  <i>Pillar Focus:</i> {phase_data['pillar_focus']}", body))
            if phase_data.get("governance_milestone"):
                story.append(Paragraph(f"  <i>Governance Milestone:</i> {phase_data['governance_milestone']}", body))
            # Support both management_required (new) and management_commitment (old) field names
            mgmt = phase_data.get("management_required") or phase_data.get("management_commitment")
            if mgmt:
                story.append(Paragraph(f"  <i>Management Commitment:</i> {mgmt}", body))
            if phase_data.get("expected_gain"):
                story.append(Paragraph(f"  <i>Expected Gain:</i> {phase_data['expected_gain']}", body))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 12))


def build_benchmark_and_note(story, report, heading, body):
    story.append(Paragraph('<font color="#0A1628"><b>Benchmark Context</b></font>', body))
    story.append(Paragraph(report.get("benchmark_context", "N/A"), body))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<font color="#C9A84C"><b>Consultant\'s Note</b></font>', body))
    story.append(Paragraph(f'<i>"{report.get("consultant_note", "N/A")}"</i>', body))


# ============================================================
# TOP-LEVEL BUILDERS
# ============================================================

def build_full_assessment_pdf(assessment: dict) -> BytesIO:
    """Build the full PPDT Assessment PDF and return an in-memory buffer.

    Layout overview — one management-grade deliverable with a cover page and
    each major group on its own page cluster for readability:
      Cover page (branded)
      -- page break --
      01 Portfolio Context  +  02 Overall Maturity
      -- page break --
      03 Pillar Maturity Levels (full page — ladder + interpretations)
      -- page break --
      04 Dimension Scores  +  05 Weighted Score Calculation
      -- page break --
      06 Bottleneck Pillar  +  07 Governance & Ownership
      -- page break --
      08 Management Commitment  +  09 Assessment Reliability
      -- page break --
      10 Decision-Type Vulnerability  +  11 Key Findings & Critical Gaps
      -- page break --
      12 Improvement Roadmap (full page)
      -- page break --
      13 Benchmark & Consultant's Note  +  Closing
    """
    report = assessment["report"]
    scores = report.get("scores", {}) or {}
    weights_raw = report.get("weights_raw", {"people": 5, "process": 5, "data": 5, "technology": 5})
    raw_total = sum(weights_raw.values()) or 1
    weights_norm = report.get("weights_normalised", {
        d: weights_raw.get(d, 5) / raw_total for d in DIMENSIONS
    })
    level_names = report.get("level_names", {}) or {}
    dim_summaries = report.get("dimension_summaries", {}) or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=60,
    )
    styles = make_report_styles()
    heading, body, gov = styles["heading"], styles["body"], styles["gov"]

    story = []

    # --- Cover page ---
    build_cover_page(story, assessment, report)

    # --- Group A: Context + Overall Score ---
    build_section_label(story, styles, 1, "Portfolio Context", "Who and what this report is about")
    build_portfolio_context(story, assessment, report, body)
    build_section_label(story, styles, 2, "Overall Maturity", "Equal-weighted vs contextual score")
    build_overall_score(story, scores, report, level_names, heading, body)
    story.append(PageBreak())

    # --- Group B: Pillar Maturity Ladder (dedicated page) ---
    build_section_label(story, styles, 3, "Pillar Maturity Levels", "Where each pillar sits on the L1\u2013L5 Hannila ladder")
    build_pillar_maturity_levels(story, scores, report, body)
    story.append(PageBreak())

    # --- Group C: Dimension Scores + Weighted Calc ---
    build_section_label(story, styles, 4, "Dimension Scores", "Raw pillar grades (1\u20135)")
    build_dimension_scores_table(story, scores, level_names, dim_summaries, heading)
    build_section_label(story, styles, 5, "Weighted Score Calculation", "How the overall score is derived from strategic weighting")
    build_weighted_breakdown(story, scores, weights_raw, weights_norm, heading, body)
    story.append(PageBreak())

    # --- Group D: Bottleneck + Governance ---
    build_section_label(story, styles, 6, "Bottleneck Pillar", "The weakest pillar caps real-world capability")
    build_bottleneck_section(story, report, scores, heading, body)
    build_section_label(story, styles, 7, "Governance & Ownership", "Accountability for portfolio decisions")
    build_governance_sections(story, report, heading, body, gov)
    story.append(PageBreak())

    # --- Group E: Management Commitment + Reliability ---
    build_section_label(story, styles, 8, "Management Commitment", "The multiplier on all capability investments")
    build_management_commitment_section(story, report, heading, body)
    build_section_label(story, styles, 9, "Assessment Reliability", "How much to rely on these results")
    build_assessment_reliability(story, report, assessment, body)
    story.append(PageBreak())

    # --- Group F: Decision Vulnerability + Key Findings & Gaps ---
    build_section_label(story, styles, 10, "Decision-Type Vulnerability", "Risk by portfolio decision type")
    build_decision_vulnerability_section(story, report, heading, body)
    build_section_label(story, styles, 11, "Key Findings & Critical Gaps", "What matters most from this assessment")
    build_findings_and_gaps(story, report, heading, body)
    story.append(PageBreak())

    # --- Group G: Roadmap (dedicated page) ---
    build_section_label(story, styles, 12, "Improvement Roadmap", "Phased plan \u2014 immediate, short-term, strategic")
    build_roadmap(story, report.get("roadmap", {}), heading, body)
    story.append(PageBreak())

    # --- Group H: Benchmark + Consultant's Note + Closing ---
    build_section_label(story, styles, 13, "Benchmark & Consultant's Note", "Context and a direct final take")
    build_benchmark_and_note(story, report, heading, body)
    build_pdf_closing(story, styles)

    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    buffer.seek(0)
    return buffer


def build_quick_assessment_pdf(quick: dict) -> BytesIO:
    """Build the Quick Health Check PDF and return an in-memory buffer."""
    scores = quick.get("scores", {}) or {}
    traffic_lights = quick.get("traffic_lights", {}) or {}
    level_names = quick.get("level_names", {}) or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = make_report_styles()
    base = styles["base"]
    heading = ParagraphStyle('Heading', parent=base['Heading2'], fontSize=14,
                             spaceAfter=8, textColor=NAVY, fontName='Helvetica-Bold')
    body = styles["body"]
    cta_style = ParagraphStyle('CTA', parent=base['Normal'], fontSize=10, spaceAfter=6,
                               textColor=NAVY, borderPadding=10)

    story = []
    build_pdf_header(story, styles, "PPDT QUICK HEALTH CHECK REPORT")

    story.append(Paragraph(f"<b>Industry:</b> {quick.get('industry', 'N/A')}", body))
    story.append(Paragraph(f"<b>Date:</b> {quick.get('created_at', 'N/A')[:10]}", body))
    if quick.get('respondent_name'):
        story.append(Paragraph(f"<b>Respondent:</b> {quick.get('respondent_name')}", body))
    story.append(Spacer(1, 20))

    overall = scores.get("overall", 0)
    level_name = level_names.get("overall", "Unknown")
    story.append(Paragraph(f"<b>OVERALL MATURITY LEVEL: {overall} / 5.0 — {level_name}</b>", heading))
    story.append(Spacer(1, 16))

    # Dimension table
    data = [["Dimension", "Score", "Level", "Status"]]
    for dim in DIMENSIONS:
        data.append([dim.capitalize(), str(scores.get(dim, 0)),
                     level_names.get(dim, "N/A"),
                     traffic_lights.get(dim, "red").upper()])
    table = Table(data, colWidths=[100, 60, 100, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
        ('GRID', (0, 0), (-1, -1), 0.5, LINE_LIGHT),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # Insights
    story.append(Paragraph("KEY INSIGHTS", heading))
    dim_scores = sorted(
        [(d, scores.get(d, 0)) for d in DIMENSIONS], key=lambda x: x[1]
    )
    weakest, strongest = dim_scores[0], dim_scores[-1]
    story.append(Paragraph(
        f"• <b>Weakest Area:</b> {weakest[0].capitalize()} ({weakest[1]}/5) — "
        f"This dimension requires immediate attention.", body))
    story.append(Paragraph(
        f"• <b>Strongest Area:</b> {strongest[0].capitalize()} ({strongest[1]}/5) — "
        f"Build on this foundation.", body))
    if scores.get("data", 0) < 3:
        story.append(Paragraph(
            "• <b>Data Gap Alert:</b> Data capability is the most critical bottleneck in "
            "PPM maturity. Prioritise data governance.", body))
    story.append(Spacer(1, 24))

    # CTA
    story.append(Paragraph("NEXT STEPS", heading))
    gap_desc = quick.get("gap_description", "")
    story.append(Paragraph(
        f"Based on your score of {overall}/5, your organisation is at the <b>{level_name}</b> stage. "
        f"Companies at this level typically have {gap_desc}. A full PPDT assessment takes 60–90 "
        f"minutes and produces a prioritised improvement roadmap with specific, actionable recommendations.",
        body))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Schedule a Full Assessment →</b> Contact your PortfolioHealth Advisor consultant",
        cta_style))

    build_pdf_closing(story, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer
