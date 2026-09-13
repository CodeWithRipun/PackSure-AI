from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from app.core.config import settings

def report_text(value) -> str:
    """Turn untrusted OCR-derived text into safe ReportLab paragraph markup."""
    return escape(str(value)).replace("\n", "<br/>")

def create_report(
    scan_id,
    filename,
    text,
    extracted,
    results,
    score,
    status,
):
    path = settings.report_dir / f"packsure_report_{scan_id}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    
    story = [
        Paragraph("PackSure AI", styles["Title"]),
        Paragraph("Smart Packaging Compliance Verification", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(f"Scan ID: {scan_id}", styles["Normal"]),
        Paragraph(f"File: {report_text(filename)}", styles["Normal"]),
        Paragraph(f"Overall score: {score}%", styles["Heading2"]),
        Paragraph(f"Status: {report_text(status)}", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph("Extracted Information", styles["Heading2"]),
    ]
    
    rows = [["Field", "Value"]]
    for key, value in extracted.items():
        rows.append(
            [
                key.replace("_", " ").title(),
                Paragraph(report_text(value), styles["BodyText"]),
            ]
        )
        
    story.append(Table(rows, colWidths=[55 * mm, 115 * mm]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Compliance Checks", styles["Heading2"]))
    
    checks = [["Code", "Requirement", "Status", "Explanation"]]
    for result in results:
        checks.append(
            [
                Paragraph(report_text(result["code"]), styles["BodyText"]),
                Paragraph(report_text(result["name"]), styles["BodyText"]),
                Paragraph(report_text(result["status"]), styles["BodyText"]),
                Paragraph(report_text(result["message"]), styles["BodyText"]),
            ]
        )
        
    table = Table(
        checks,
        repeatRows=1,
        colWidths=[18 * mm, 48 * mm, 25 * mm, 79 * mm],
    )
    
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("OCR Text", styles["Heading2"]))
    
    safe = report_text((text or "No readable OCR text.")[:6000])
    story.append(Paragraph(safe, styles["Code"]))
    
    doc.build(story)
    return str(path)