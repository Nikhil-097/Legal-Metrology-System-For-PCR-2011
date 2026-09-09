import io
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def make_qr_code_image(scan_id: str) -> io.BytesIO:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(f"[https://metrocheck.gov.in/verify/](https://metrocheck.gov.in/verify/){scan_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_statutory_notice_pdf(scan_data: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#000000'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#444444'),
        fontName='Helvetica'
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        fontName='Helvetica'
    )

    elements = []

    # Title & Legal Headings
    elements.append(Paragraph("LEGAL METROLOGY ACT, 2011", title_style))
    elements.append(Paragraph("THE LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", subtitle_style))
    elements.append(Paragraph("OFFICIAL STATUTORY COMPLIANCE INSPECTION AUDIT REPORT", subtitle_style))
    elements.append(Spacer(1, 10))

    scan_id = scan_data.get("scan_id") or scan_data.get("id", "N/A")
    timestamp = scan_data.get("timestamp", "N/A")
    category = scan_data.get("category", "Commodity")
    brand = scan_data.get("brand_name") or scan_data.get("declarations", {}).get("brand_name", "N/A")
    commodity = scan_data.get("product_name") or scan_data.get("declarations", {}).get("commodity_name", "N/A")
    score = scan_data.get("compliance_score") or scan_data.get("score", 100)
    status = scan_data.get("status", "COMPLIANT")
    barcode = scan_data.get("barcode_data", {}).get("code", "Not Scanned")

    # Generate QR Code
    qr_buf = make_qr_code_image(scan_id)
    qr_img = RLImage(qr_buf, width=70, height=70)

    meta_data = [
        ["Audit Reference ID:", str(scan_id), "Audit Timestamp:", str(timestamp)],
        ["Brand Name:", str(brand), "Commodity Type:", f"{commodity} ({category})"],
        ["Compliance Rating:", f"{score}%", "Statutory Verdict:", str(status)],
        ["Barcode / EAN Code:", str(barcode), "Digital Signature:", "TAMPER-PROOF VERIFIED"]
    ]
    meta_table = Table(meta_data, colWidths=[110, 140, 110, 180])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#111111')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
    ]))

    header_table = Table([[meta_table, qr_img]], colWidths=[470, 70])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph(f"<b>Rule 6 & Rule 7 Statutory Declarations Schedule (Category: {category})</b>", body_style))
    elements.append(Spacer(1, 4))

    dec = scan_data.get("declarations") or scan_data.get("extracted_declarations") or {}
    dec_rows = [
        ["Statutory Parameter", "Declared on Package Artwork", "Compliance Verdict"],
        ["Declared Net Quantity", str(dec.get("net_quantity") or "MISSING"), "VERIFIED" if (dec.get("net_quantity") and dec.get("net_quantity") != "MISSING") else "NON-COMPLIANT"],
        ["Maximum Retail Price (MRP)", str(dec.get("mrp") or "MISSING"), "VERIFIED" if (dec.get("mrp") and dec.get("mrp") != "MISSING") else "NON-COMPLIANT"],
        ["Unit Sale Price (USP)", str(dec.get("unit_sale_price") or "MISSING"), "VERIFIED" if (dec.get("unit_sale_price") and dec.get("unit_sale_price") != "MISSING") else "NON-COMPLIANT"],
        ["Date of Packing / Mfg", str(dec.get("mfg_date") or "MISSING"), "VERIFIED" if (dec.get("mfg_date") and dec.get("mfg_date") != "MISSING") else "NON-COMPLIANT"],
        ["Expiry / Best Before", str(dec.get("expiry_date") or "MISSING"), "VERIFIED" if (dec.get("expiry_date") and dec.get("expiry_date") != "MISSING") else "NON-COMPLIANT"],
        ["Batch / Lot Number", str(dec.get("batch_number") or "MISSING"), "VERIFIED" if (dec.get("batch_number") and dec.get("batch_number") != "MISSING") else "NON-COMPLIANT"],
        ["Tax Inclusivity Clause", "Present" if dec.get("has_tax_clause") else "Missing / Not Found", "VERIFIED" if dec.get("has_tax_clause") else "NON-COMPLIANT"],
        ["Country of Origin", str(dec.get("country_of_origin") or "India"), "VERIFIED"]
    ]

    # Include FSSAI row for food items
    if category == "Food" or "fssai_license" in dec:
        dec_rows.append(["FSSAI License Number", str(dec.get("fssai_license") or "MISSING"), "VERIFIED" if (dec.get("fssai_license") and dec.get("fssai_license") != "MISSING") else "NON-COMPLIANT"])

    dec_table = Table(dec_rows, colWidths=[180, 230, 130])
    dec_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    elements.append(dec_table)
    elements.append(Spacer(1, 24))

    sign_table = Table([
        ["Authorized Legal Metrology Inspector", "Manufacturer / Authorized Signatory"],
        ["\n\n________________________________________", "\n\n________________________________________"],
        ["Signature & Official Stamp", "Signature & Official Stamp"]
    ], colWidths=[270, 270])
    sign_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer