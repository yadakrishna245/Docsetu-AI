"""
DocSetu AI - PDF Export Service
Generates professional compliance report PDFs for CAs and auditors.
Uses ReportLab for PDF generation with Indian regulatory branding.
"""

import io
import logging
from datetime import datetime
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
)
from reportlab.platypus.flowables import KeepTogether

logger = logging.getLogger(__name__)

# ─── Brand Colors ────────────────────────────────────────────────────────────
SAFFRON = colors.HexColor("#FF9933")
NAVY = colors.HexColor("#1B2A4A")
DARK_NAVY = colors.HexColor("#0F1B33")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MEDIUM_GRAY = colors.HexColor("#E0E0E0")
WHITE = colors.white

# Score colors
SCORE_GREEN = colors.HexColor("#28A745")
SCORE_YELLOW = colors.HexColor("#FFC107")
SCORE_RED = colors.HexColor("#DC3545")

# Severity colors
SEVERITY_COLORS = {
    "critical": colors.HexColor("#DC3545"),
    "high": colors.HexColor("#E85D04"),
    "medium": colors.HexColor("#FFC107"),
    "low": colors.HexColor("#17A2B8"),
    "info": colors.HexColor("#6C757D"),
}


def _get_score_color(score: float) -> colors.HexColor:
    """Get the appropriate color for a compliance score."""
    if score > 80:
        return SCORE_GREEN
    elif score >= 60:
        return SCORE_YELLOW
    else:
        return SCORE_RED


def _get_custom_styles() -> dict:
    """Create custom paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    custom_styles = {
        "Title": ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=NAVY,
            spaceAfter=6,
            alignment=TA_CENTER,
        ),
        "Subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
            alignment=TA_CENTER,
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=NAVY,
            spaceBefore=16,
            spaceAfter=8,
            borderPadding=4,
        ),
        "SubSection": ParagraphStyle(
            "SubSection",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "BodyText": ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=DARK_NAVY,
            spaceAfter=6,
            leading=14,
        ),
        "SmallText": ParagraphStyle(
            "SmallText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#666666"),
        ),
        "ScoreText": ParagraphStyle(
            "ScoreText",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=36,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "ScoreLabel": ParagraphStyle(
            "ScoreLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WHITE,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK_NAVY,
            leading=12,
        ),
        "RecommendationText": ParagraphStyle(
            "RecommendationText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=DARK_NAVY,
            leftIndent=20,
            spaceAfter=6,
            leading=13,
        ),
    }

    return custom_styles


class _FooterCanvas:
    """Custom canvas handler for header/footer on each page."""

    def __init__(self, doc, report_title: str):
        self.doc = doc
        self.report_title = report_title

    def __call__(self, canvas, doc):
        canvas.saveState()

        # ─── Header Bar ──────────────────────────────────────────────
        page_width = A4[0]
        canvas.setFillColor(SAFFRON)
        canvas.rect(0, A4[1] - 25, page_width, 25, fill=True, stroke=False)

        # Header text
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(20, A4[1] - 17, "DocSetu AI")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(page_width - 20, A4[1] - 17, "Compliance Report")

        # ─── Footer ─────────────────────────────────────────────────
        canvas.setFillColor(MEDIUM_GRAY)
        canvas.rect(0, 0, page_width, 30, fill=True, stroke=False)

        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20, 12, "Generated by DocSetu AI")
        canvas.drawCentredString(page_width / 2, 12, self.report_title)
        canvas.drawRightString(page_width - 20, 12, f"Page {doc.page}")

        canvas.restoreState()


def generate_compliance_report_pdf(report_data: dict, document_info: dict) -> bytes:
    """
    Generate a professional compliance report PDF.

    Args:
        report_data: Compliance report data containing:
            - overall_score (float): 0-100 compliance score
            - overall_status (str): compliant/non_compliant/partial/needs_review
            - violations (list): List of violation dicts
            - recommendations (list): List of recommendation strings
            - gst_compliance (dict|None): GST category results
            - dpdp_compliance (dict|None): DPDP Act category results
            - sebi_compliance (dict|None): SEBI category results
            - rbi_compliance (dict|None): RBI category results
            - mca_compliance (dict|None): MCA category results
            - rules_checked (list): Rules that were checked
            - created_at (str|datetime): Report creation timestamp
        document_info: Document metadata containing:
            - id (str): Document ID
            - filename (str): Original filename
            - file_type (str): File type
            - document_type (str|None): Detected document type

    Returns:
        bytes: PDF file content as bytes.
    """
    buffer = io.BytesIO()

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="DocSetu AI - Compliance Report",
        author="DocSetu AI",
    )

    styles = _get_custom_styles()
    elements = []

    # ─── Title Section ───────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("COMPLIANCE REPORT", styles["Title"]))

    # Report date
    created_at = report_data.get("created_at")
    if isinstance(created_at, datetime):
        report_date = created_at.strftime("%d %B %Y, %I:%M %p")
    elif isinstance(created_at, str):
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            report_date = dt.strftime("%d %B %Y, %I:%M %p")
        except (ValueError, TypeError):
            report_date = datetime.utcnow().strftime("%d %B %Y, %I:%M %p")
    else:
        report_date = datetime.utcnow().strftime("%d %B %Y, %I:%M %p")

    elements.append(Paragraph(f"Generated on {report_date}", styles["Subtitle"]))
    elements.append(Spacer(1, 0.3 * cm))

    # ─── Document Info Table ─────────────────────────────────────────────────
    elements.append(Paragraph("Document Information", styles["SectionHeader"]))

    doc_filename = document_info.get("filename", "Unknown")
    doc_id = document_info.get("id", "N/A")
    doc_type = document_info.get("document_type") or document_info.get("file_type", "N/A")
    overall_status = report_data.get("overall_status", "unknown").replace("_", " ").title()

    doc_info_data = [
        ["Document Name", doc_filename],
        ["Document ID", doc_id],
        ["Document Type", doc_type.upper()],
        ["Compliance Status", overall_status],
    ]

    doc_info_table = Table(doc_info_data, colWidths=[4.5 * cm, 13 * cm])
    doc_info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, MEDIUM_GRAY),
            ]
        )
    )
    elements.append(doc_info_table)
    elements.append(Spacer(1, 0.5 * cm))

    # ─── Compliance Score Section ────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=10))
    elements.append(Paragraph("Overall Compliance Score", styles["SectionHeader"]))
    elements.append(Spacer(1, 0.3 * cm))

    score = report_data.get("overall_score", 0) or 0
    score_color = _get_score_color(score)

    # Score display
    score_style = ParagraphStyle(
        "ScoreDisplay",
        fontName="Helvetica-Bold",
        fontSize=42,
        textColor=score_color,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    elements.append(Paragraph(f"{score:.1f}%", score_style))
    elements.append(Paragraph("Compliance Score", styles["ScoreLabel"]))

    # Score interpretation
    if score > 80:
        interpretation = "✓ Document is largely compliant with applicable Indian regulations."
    elif score >= 60:
        interpretation = "⚠ Document requires attention — some compliance issues detected."
    else:
        interpretation = "✗ Document has significant compliance gaps — immediate action recommended."

    interp_style = ParagraphStyle(
        "Interpretation",
        fontName="Helvetica",
        fontSize=10,
        textColor=score_color,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=12,
    )
    elements.append(Paragraph(interpretation, interp_style))
    elements.append(Spacer(1, 0.3 * cm))

    # ─── Violations Table ────────────────────────────────────────────────────
    violations = report_data.get("violations", []) or []

    elements.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=10))
    elements.append(
        Paragraph(f"Violations ({len(violations)} found)", styles["SectionHeader"])
    )

    if violations:
        # Table header
        header_row = [
            Paragraph("Severity", styles["TableHeader"]),
            Paragraph("Rule", styles["TableHeader"]),
            Paragraph("Description", styles["TableHeader"]),
            Paragraph("Recommendation", styles["TableHeader"]),
        ]

        table_data = [header_row]

        for v in violations:
            severity = v.get("severity", "medium").capitalize()
            rule_name = v.get("rule_name", v.get("rule_id", "N/A"))
            description = v.get("detail", v.get("description", "N/A"))
            recommendation = v.get("recommendation", "Review and address this issue.")

            row = [
                Paragraph(severity, styles["TableCell"]),
                Paragraph(str(rule_name), styles["TableCell"]),
                Paragraph(str(description)[:200], styles["TableCell"]),
                Paragraph(str(recommendation)[:200], styles["TableCell"]),
            ]
            table_data.append(row)

        # Create table with proportional widths
        col_widths = [2.2 * cm, 3.5 * cm, 5.5 * cm, 6 * cm]
        violations_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Style the table
        table_style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Body styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]

        # Color-code severity column
        for i, v in enumerate(violations, start=1):
            severity = v.get("severity", "medium").lower()
            sev_color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["medium"])
            table_style_commands.append(("TEXTCOLOR", (0, i), (0, i), sev_color))
            table_style_commands.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))

        violations_table.setStyle(TableStyle(table_style_commands))
        elements.append(violations_table)
    else:
        elements.append(
            Paragraph(
                "✓ No violations found. Document is compliant.",
                styles["BodyText"],
            )
        )

    elements.append(Spacer(1, 0.5 * cm))

    # ─── Recommendations Section ─────────────────────────────────────────────
    recommendations = report_data.get("recommendations", []) or []

    if recommendations:
        elements.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=10))
        elements.append(Paragraph("Recommendations", styles["SectionHeader"]))

        for i, rec in enumerate(recommendations, start=1):
            rec_text = f"<b>{i}.</b> {rec}"
            elements.append(Paragraph(rec_text, styles["RecommendationText"]))

        elements.append(Spacer(1, 0.5 * cm))

    # ─── Category-wise Breakdown ─────────────────────────────────────────────
    categories = {
        "GST": report_data.get("gst_compliance"),
        "DPDP Act": report_data.get("dpdp_compliance"),
        "SEBI": report_data.get("sebi_compliance"),
        "RBI": report_data.get("rbi_compliance"),
        "MCA": report_data.get("mca_compliance"),
    }

    # Check if any category data exists
    has_category_data = any(v is not None for v in categories.values())

    if has_category_data:
        elements.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=10))
        elements.append(Paragraph("Category-wise Compliance Breakdown", styles["SectionHeader"]))
        elements.append(Spacer(1, 0.3 * cm))

        # Summary table
        cat_header = [
            Paragraph("Regulation", styles["TableHeader"]),
            Paragraph("Status", styles["TableHeader"]),
            Paragraph("Score", styles["TableHeader"]),
            Paragraph("Issues", styles["TableHeader"]),
        ]
        cat_table_data = [cat_header]

        for cat_name, cat_data in categories.items():
            if cat_data is None:
                status_text = "Not Checked"
                score_text = "—"
                issues_text = "—"
            elif isinstance(cat_data, dict):
                status_text = cat_data.get("status", "N/A").replace("_", " ").title()
                cat_score = cat_data.get("score")
                score_text = f"{cat_score:.0f}%" if cat_score is not None else "—"
                issues_count = cat_data.get("violations_count", cat_data.get("issues", 0))
                issues_text = str(issues_count) if issues_count else "0"
            else:
                status_text = str(cat_data)
                score_text = "—"
                issues_text = "—"

            row = [
                Paragraph(f"<b>{cat_name}</b>", styles["TableCell"]),
                Paragraph(status_text, styles["TableCell"]),
                Paragraph(score_text, styles["TableCell"]),
                Paragraph(issues_text, styles["TableCell"]),
            ]
            cat_table_data.append(row)

        cat_col_widths = [4 * cm, 5 * cm, 3 * cm, 3 * cm]
        cat_table = Table(cat_table_data, colWidths=cat_col_widths, repeatRows=1)
        cat_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (2, 1), (3, -1), "CENTER"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(cat_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Individual category details
        for cat_name, cat_data in categories.items():
            if cat_data and isinstance(cat_data, dict):
                details = cat_data.get("details") or cat_data.get("findings")
                if details and isinstance(details, list) and len(details) > 0:
                    elements.append(Paragraph(f"{cat_name} — Details", styles["SubSection"]))
                    for detail in details[:5]:  # Limit to 5 details per category
                        if isinstance(detail, dict):
                            detail_text = detail.get("description", detail.get("detail", str(detail)))
                        else:
                            detail_text = str(detail)
                        elements.append(
                            Paragraph(f"• {detail_text}", styles["BodyText"])
                        )
                    elements.append(Spacer(1, 0.2 * cm))

    # ─── Rules Checked Summary ───────────────────────────────────────────────
    rules_checked = report_data.get("rules_checked", []) or []
    if rules_checked:
        elements.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=10))
        elements.append(
            Paragraph(f"Rules Checked ({len(rules_checked)} total)", styles["SectionHeader"])
        )

        # Show as comma-separated list for compactness
        if isinstance(rules_checked[0], dict):
            rule_names = [r.get("rule_name", r.get("rule_id", "Unknown")) for r in rules_checked]
        else:
            rule_names = [str(r) for r in rules_checked]

        rules_text = " • ".join(rule_names[:20])  # Limit display
        if len(rule_names) > 20:
            rules_text += f" ... and {len(rule_names) - 20} more"

        elements.append(Paragraph(rules_text, styles["BodyText"]))
        elements.append(Spacer(1, 0.5 * cm))

    # ─── Disclaimer ──────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY, spaceAfter=8))
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
        spaceBefore=10,
    )
    elements.append(
        Paragraph(
            "This report is generated by DocSetu AI for informational purposes. "
            "It does not constitute legal or professional advice. Please consult "
            "a qualified professional for regulatory compliance decisions.",
            disclaimer_style,
        )
    )

    # ─── Build PDF ───────────────────────────────────────────────────────────
    report_title = f"Compliance Report - {doc_filename}"

    try:
        doc.build(
            elements,
            onFirstPage=_FooterCanvas(doc, report_title),
            onLaterPages=_FooterCanvas(doc, report_title),
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise RuntimeError(f"Failed to generate PDF: {str(e)}")

    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(
        f"Generated compliance report PDF for document {doc_id} "
        f"({len(pdf_bytes)} bytes, score={score})"
    )

    return pdf_bytes
