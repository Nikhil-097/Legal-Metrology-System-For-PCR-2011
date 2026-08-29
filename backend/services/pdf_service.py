import io
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.config import settings

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class PDFService:
    """Generates official statutory inspection notices and audit PDF reports."""

    def __init__(self):
        self.output_dir = os.path.join(settings.BASE_DIR, "generated_reports")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_inspection_pdf(self, scan_data: Dict[str, Any]) -> str:
        """
        Creates a formatted PDF report with compliance scoring and itemized violations.
        Returns: Absolute file path to the generated PDF.
        """
        scan_id = str(scan_data.get("scan_id", "UNKNOWN"))[:8]
        filename = f"Inspection_Report_{scan_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=1,
            textColor=colors.HexColor("#1A202C")
        )
        
        sub_style = ParagraphStyle(
            name="DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#4A5568")
        )
        
        section_heading = ParagraphStyle(
            name="SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#2B6CB0")
        )
        
        body_text = ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748")
        )

        story = []

        # 1. Header
        story.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", title_style))
        story.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION", sub_style))
        story.append(Paragraph("STATUTORY COMPLIANCE INSPECTION AUDIT REPORT", sub_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=12))

        # 2. Metadata Table
        meta_data = [
            [
                Paragraph(f"<b>Report Reference:</b> SCN-{scan_id.upper()}", body_text),
                Paragraph(f"<b>Date of Inspection:</b> {datetime.now(timezone.utc).strftime('%d %B %Y')}", body_text)
            ],
            [
                Paragraph(f"<b>Brand / Product:</b> {scan_data.get('brand_name', 'N/A')}", body_text),
                Paragraph(f"<b>Commodity:</b> {scan_data.get('commodity_name', 'N/A')}", body_text)
            ],
            [
                Paragraph(f"<b>Inspector ID:</b> {scan_data.get('inspector_id', 'INSP-DEFAULT')}", body_text),
                Paragraph(f"<b>Status:</b> {'COMPLIANT' if scan_data.get('is_compliant') else 'NON-COMPLIANT'}", body_text)
            ]
        ]
        
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 3. Compliance Summary Metrics
        story.append(Paragraph("1. Surface & Compliance Metrics", section_heading))
        metrics_data = [
            ["Calculated PDP Area", f"{scan_data.get('pdp_area_cm2', 0.0)} cm²"],
            ["Rule 7 Min Font Required", f"{scan_data.get('required_min_font_height_mm', 1.0)} mm"],
            ["Barcode Detected", scan_data.get("barcode") or "None / Unresolved"],
            ["Overall Compliance Score", f"{scan_data.get('compliance_score', 0.0)}%"]
        ]
        metrics_table = Table(metrics_data, colWidths=[270, 270])
        metrics_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#2D3748")),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 12))

        # 4. Extracted Statutory Declarations
        story.append(Paragraph("2. Extracted Package Declarations (Rule 6)", section_heading))
        extracted = scan_data.get("extracted_declarations") or scan_data.get("extracted_data") or {}
        has_tax = extracted.get("has_tax_clause", False) or extracted.get("has_tax_inclusive_statement", False)

        dec_data = [
            ["Declared Net Quantity", str(extracted.get("net_quantity") or extracted.get("net_quantity_raw") or "Missing / Undetected")],
            ["Maximum Retail Price (MRP)", str(extracted.get("mrp") or (f"₹ {extracted.get('mrp_value')}" if extracted.get('mrp_value') else "Missing / Undetected"))],
            ["Tax Inclusive Wording", "Present" if has_tax else "MISSING"],
            ["Unit Sale Price (USP)", str(extracted.get("unit_sale_price") or extracted.get("usp_raw") or "Missing / Undetected")],
            ["Mfg / Packing Date", str(extracted.get("mfg_date") or "Missing / Undetected")],
            ["Country of Origin", str(extracted.get("country_of_origin") or "India (Presumed / Domestic)")]
        ]
        dec_table = Table(dec_data, colWidths=[270, 270])
        dec_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(dec_table)
        story.append(Spacer(1, 12))

        # 5. Detected Violations Table
        story.append(Paragraph("3. Statutory Violations & Contraventions", section_heading))
        violations: List[Dict[str, Any]] = scan_data.get("violations", [])

        if not violations:
            story.append(Paragraph("<b>No statutory violations detected.</b> The package meets mandatory declarations under Legal Metrology Rules, 2011.", body_text))
        else:
            viol_rows = [["Rule Ref.", "Code", "Severity", "Violation Detail"]]
            for v in violations:
                viol_rows.append([
                    v.get("rule", "Rule 6"),
                    v.get("code", "VIOLATION"),
                    v.get("severity", "HIGH"),
                    Paragraph(v.get("detail", ""), body_text)
                ])

            viol_table = Table(viol_rows, colWidths=[80, 110, 60, 290])
            viol_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E53E3E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FEB2B2")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(viol_table)

        story.append(Spacer(1, 20))
        story.append(Paragraph("<i>This document is an automatically generated audit trail issued by the Legal Metrology Compliance Verification Engine.</i>", sub_style))

        doc.build(story)
        return filepath


pdf_service = PDFService()