"""
PDF builder helpers for PortfolioHealth Advisor reports.

Contains section-building functions used by the FastAPI routes in
`server.py` to keep route handlers small and focused.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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

def build_company_info(story, assessment, report, body):
    story.append(Paragraph(f"<b>Company:</b> {assessment.get('company_name', 'N/A')}", body))
    story.append(Paragraph(f"<b>Industry:</b> {assessment.get('company_industry', 'N/A')}", body))
    story.append(Paragraph(
        f"<b>Respondent:</b> {assessment.get('respondent_name', 'N/A')} "
        f"({assessment.get('respondent_role', 'N/A')})", body))
    date_str = assessment.get('completed_at', assessment.get('created_at', 'N/A')) or 'N/A'
    story.append(Paragraph(f"<b>Date:</b> {date_str[:10]}", body))
    bm = report.get('business_model')
    sp = report.get('strategic_priority')
    if bm:
        story.append(Paragraph(f"<b>Business Model:</b> {bm}", body))
    if sp:
        story.append(Paragraph(f"<b>Strategic Priority:</b> {sp}", body))
    story.append(Spacer(1, 20))


def build_overall_score(story, scores, report, level_names, heading, body):
    equal = scores.get("overall", "N/A")
    ctx = report.get("contextual_score")
    lvl_overall = level_names.get('overall', 'N/A')
    story.append(Paragraph(
        "<b>OVERALL MATURITY \u2014 DUAL SCORE</b>",
        heading))
    story.append(Paragraph(
        f"<b>Equal-Weighted (primary):</b> {equal} / 5.0 \u2014 {lvl_overall}",
        body))
    if isinstance(ctx, (int, float)):
        story.append(Paragraph(
            f"<b>Contextual (secondary):</b> {ctx:.1f} / 5.0 \u2014 adjusted for business model + stated priority",
            body))
    story.append(Spacer(1, 12))


def build_dimension_scores_table(story, scores, level_names, dim_summaries, heading):
    story.append(Paragraph("DIMENSION SCORES", heading))
    data = [["Dimension", "Score", "Level", "Summary"]]
    for dim in DIMENSIONS:
        summary = dim_summaries.get(dim, "N/A")
        if len(summary) > 60:
            summary = summary[:60] + "..."
        data.append([dim.capitalize(), str(scores.get(dim, "N/A")),
                     level_names.get(dim, "N/A"), summary])

    table = Table(data, colWidths=[70, 45, 85, 290])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ('LINEBELOW', (0, 0), (-1, 0), 2, GOLD),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, LINE_LIGHT),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, LINE_LIGHT),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))


def build_weighted_breakdown(story, scores, weights_raw, weights_norm, heading):
    story.append(Paragraph("WEIGHTED SCORE CALCULATION", heading))
    data = [["Pillar", "Raw Score", "Weight (1-10)", "Normalised", "Contribution"]]
    for dim in DIMENSIONS:
        s = scores.get(dim, 0)
        w_raw = weights_raw.get(dim, 5)
        w_norm = weights_norm.get(dim, 0.25)
        data.append([dim.capitalize(), str(s), str(w_raw), f"{w_norm:.2f}", f"{s * w_norm:.2f}"])
    data.append(["", "", "", "Overall:", f"{scores.get('overall', 0):.2f}"])

    table = Table(data, colWidths=[75, 55, 75, 70, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
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
        story.append(Paragraph("GOVERNANCE INDICATORS (Levels 4\u20135)", heading))
        for dim in DIMENSIONS:
            obs = gov_obs.get(dim, "")
            if obs and "N/A" not in str(obs) and "below" not in str(obs).lower():
                story.append(Paragraph(f"<b>{dim.capitalize()} \u2014 Governance:</b> {obs}", gov))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 12))

    story.append(Paragraph("GOVERNANCE &amp; OWNERSHIP", heading))
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
    story.append(Paragraph("BOTTLENECK PILLAR", heading))
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
    story.append(Paragraph("MANAGEMENT COMMITMENT", heading))
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
    story.append(Paragraph("DECISION-TYPE VULNERABILITY ANALYSIS", heading))
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
    story.append(Paragraph("KEY FINDINGS", heading))
    for item in report.get("key_findings", []) or []:
        story.append(Paragraph(f"\u2022 {item}", body))
    story.append(Spacer(1, 12))

    story.append(Paragraph("CRITICAL CAPABILITY GAPS", heading))
    for item in report.get("critical_gaps", []) or []:
        story.append(Paragraph(f"\u2022 {item}", body))
    story.append(Spacer(1, 12))


def build_roadmap(story, roadmap, heading, body):
    story.append(Paragraph("IMPROVEMENT ROADMAP", heading))
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
    story.append(Paragraph("BENCHMARK CONTEXT", heading))
    story.append(Paragraph(report.get("benchmark_context", "N/A"), body))
    story.append(Spacer(1, 12))

    story.append(Paragraph("CONSULTANT'S NOTE", heading))
    story.append(Paragraph(report.get("consultant_note", "N/A"), body))


# ============================================================
# TOP-LEVEL BUILDERS
# ============================================================

def build_full_assessment_pdf(assessment: dict) -> BytesIO:
    """Build the full PPDT Assessment PDF and return an in-memory buffer."""
    report = assessment["report"]
    scores = report.get("scores", {}) or {}
    weights_raw = report.get("weights_raw", {"people": 5, "process": 5, "data": 5, "technology": 5})
    raw_total = sum(weights_raw.values()) or 1
    weights_norm = report.get("weights_normalised", {
        d: weights_raw.get(d, 5) / raw_total for d in DIMENSIONS
    })

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = make_report_styles()
    heading, body, gov = styles["heading"], styles["body"], styles["gov"]

    story = []
    build_pdf_header(story, styles, "PPDT CAPABILITY MATURITY ASSESSMENT REPORT")
    build_company_info(story, assessment, report, body)
    build_overall_score(story, scores, report, report.get("level_names", {}), heading, body)
    build_dimension_scores_table(story, scores, report.get("level_names", {}),
                                 report.get("dimension_summaries", {}), heading)
    build_weighted_breakdown(story, scores, weights_raw, weights_norm, heading)
    build_bottleneck_section(story, report, scores, heading, body)
    build_governance_sections(story, report, heading, body, gov)
    build_management_commitment_section(story, report, heading, body)
    build_findings_and_gaps(story, report, heading, body)
    build_decision_vulnerability_section(story, report, heading, body)
    build_roadmap(story, report.get("roadmap", {}), heading, body)
    build_benchmark_and_note(story, report, heading, body)
    build_pdf_closing(story, styles)

    doc.build(story)
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
