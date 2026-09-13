from __future__ import annotations

import io
import os
from html import escape
from typing import Any, Dict, Optional

import qrcode

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# =============================================================================
# NORMALIZATION HELPERS
# =============================================================================

def _as_dict(value: Any) -> dict:
    """
    Safely convert a value to a dictionary.

    This protects the PDF generator from old/legacy database records
    containing lists, strings, None, etc.
    """
    if isinstance(value, dict):
        return value

    return {}


def _as_list(value: Any) -> list:
    """
    Safely convert a value to a list.
    """
    if isinstance(value, list):
        return value

    return []


def _safe(
    value: Any,
    fallback: str = "N/A",
) -> str:
    """
    Convert arbitrary values to safe text for ReportLab.
    """

    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return escape(text)


def _missing(value: Any) -> bool:
    """
    Determine whether a declaration is effectively missing.
    """

    if value is None:
        return True

    if isinstance(value, str):

        return value.strip().upper() in {
            "",
            "MISSING",
            "N/A",
            "NA",
            "UNKNOWN",
            "NONE",
            "NULL",
        }

    return False


def _check(
    scan_data: Dict[str, Any],
    name: str,
) -> Dict[str, Any]:
    """
    Safely retrieve a compliance check.

    Prevents:
        'list' object has no attribute 'get'
    """

    checks = _as_dict(
        scan_data.get(
            "compliance_checks"
        )
    )

    value = checks.get(name)

    return _as_dict(value)


def _status_from_check(
    check: Optional[Dict[str, Any]],
) -> str:
    """
    Convert a compliance check into a human-readable verdict.
    """

    if not isinstance(check, dict):
        return "NOT ASSESSED"

    status = check.get("status")

    if status is not None:

        return str(
            status
        ).upper()

    passed = check.get("passed")

    if passed is True:
        return "VERIFIED"

    if passed is False:
        return "NON-COMPLIANT"

    return "NOT ASSESSED"


def _declaration_verdict(
    scan_data: Dict[str, Any],
    field: str,
    value: Any,
) -> str:
    """
    Get the verdict for a declaration.

    The deterministic compliance result takes priority over
    simply checking whether text exists.
    """

    check_name = field

    if field == "unit_sale_price":
        check_name = "usp_math"

    check = _check(
        scan_data,
        check_name,
    )

    if check:
        return _status_from_check(
            check
        )

    if _missing(value):
        return "NOT ASSESSED"

    return "VERIFIED"


# =============================================================================
# QR CODE
# =============================================================================

def make_qr_code_image(
    scan_id: str,
) -> io.BytesIO:
    """
    Generate a QR code for the assessment reference.

    If PUBLIC_VERIFY_BASE_URL is configured, the QR points to:

        <PUBLIC_VERIFY_BASE_URL>/<scan_id>

    Otherwise it contains a local assessment reference.
    """

    base_url = os.getenv(
        "PUBLIC_VERIFY_BASE_URL",
        "",
    ).strip().rstrip("/")

    if base_url:

        payload = (
            f"{base_url}/{scan_id}"
        )

    else:

        payload = (
            f"Assessment Reference: {scan_id}"
        )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )

    qr.add_data(
        payload
    )

    qr.make(
        fit=True
    )

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    buffer.seek(0)

    return buffer


# =============================================================================
# MAIN PDF GENERATOR
# =============================================================================

def generate_statutory_notice_pdf(
    scan_data: dict,
) -> io.BytesIO:
    """
    Generate an AI-assisted Legal Metrology compliance assessment PDF.

    IMPORTANT:
    This is an assessment report, not an official government certificate.
    """

    # -------------------------------------------------------------------------
    # Validate top-level input
    # -------------------------------------------------------------------------

    if not isinstance(
        scan_data,
        dict,
    ):
        raise TypeError(
            "scan_data must be a dictionary"
        )

    # -------------------------------------------------------------------------
    # Create PDF buffer
    # -------------------------------------------------------------------------

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=(
            "AI-Assisted Legal Metrology "
            "Compliance Assessment"
        ),
        author=(
            "Legal Metrology Compliance System"
        ),
    )

    # -------------------------------------------------------------------------
    # Styles
    # -------------------------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=15,
        leading=18,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=10.5,
        leading=13,
        spaceBefore=7,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
    )

    elements = []

    # =========================================================================
    # BASIC DATA
    # =========================================================================

    scan_id = (
        scan_data.get(
            "scan_id"
        )
        or scan_data.get(
            "id"
        )
        or "N/A"
    )

    timestamp = (
        scan_data.get(
            "timestamp"
        )
        or scan_data.get(
            "created_at"
        )
        or "N/A"
    )

    declarations = _as_dict(
        scan_data.get(
            "declarations"
        )
        or scan_data.get(
            "extracted_data"
        )
    )

    brand = (
        scan_data.get(
            "brand_name"
        )
        or declarations.get(
            "brand_name"
        )
        or "N/A"
    )

    commodity = (
        scan_data.get(
            "product_name"
        )
        or declarations.get(
            "commodity_name"
        )
        or "N/A"
    )

    category = (
        scan_data.get(
            "category"
        )
        or "Commodity"
    )

    # -------------------------------------------------------------------------
    # Score
    #
    # DO NOT use:
    #
    #     score = value or 100
    #
    # because 0 is a valid score.
    # -------------------------------------------------------------------------

    score = scan_data.get(
        "compliance_score"
    )

    if score is None:

        score = scan_data.get(
            "score",
            0,
        )

    try:

        score = float(
            score
        )

    except (
        TypeError,
        ValueError,
    ):

        score = 0.0

    status = str(
        scan_data.get(
            "status",
            "INCONCLUSIVE",
        )
    ).upper()

    extraction_status = str(
        scan_data.get(
            "extraction_status",
            "success",
        )
    ).lower()

    # =========================================================================
    # TITLE
    # =========================================================================

    elements.append(
        Paragraph(
            "LEGAL METROLOGY ACT, 2009",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            "THE LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011",
            subtitle_style,
        )
    )

    elements.append(
        Paragraph(
            "AI-ASSISTED LEGAL METROLOGY COMPLIANCE ASSESSMENT",
            subtitle_style,
        )
    )

    elements.append(
        Spacer(
            1,
            8,
        )
    )

    # =========================================================================
    # QR CODE
    # =========================================================================

    qr_buffer = make_qr_code_image(
        str(scan_id)
    )

    qr_image = RLImage(
        qr_buffer,
        width=0.75 * inch,
        height=0.75 * inch,
    )

    # =========================================================================
    # BARCODE DATA
    # =========================================================================

    barcode_data = _as_dict(
        scan_data.get(
            "barcode_data"
        )
    )

    # =========================================================================
    # HEADER METADATA
    # =========================================================================

    metadata = [
        [
            Paragraph(
                "<b>Assessment Reference</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    scan_id
                ),
                body_style,
            ),
            Paragraph(
                "<b>Assessment Timestamp</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    timestamp
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Brand Name</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    brand
                ),
                body_style,
            ),
            Paragraph(
                "<b>Commodity</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    f"{commodity} ({category})"
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Assessment Score</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    f"{score:.1f}%"
                ),
                body_style,
            ),
            Paragraph(
                "<b>Assessment Status</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    status
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Barcode</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    barcode_data.get(
                        "code",
                        "N/A",
                    )
                ),
                body_style,
            ),
            Paragraph(
                "<b>Extraction Status</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    extraction_status.upper()
                ),
                body_style,
            ),
        ],
    ]

    metadata_table = Table(
        metadata,
        colWidths=[
            105,
            145,
            105,
            165,
        ],
    )

    metadata_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#f8fafc"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    header_table = Table(
        [
            [
                metadata_table,
                qr_image,
            ]
        ],
        colWidths=[
            520,
            55,
        ],
    )

    header_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    elements.append(
        header_table
    )

    elements.append(
        Spacer(
            1,
            10,
        )
    )

    # =========================================================================
    # EXTRACTION FAILURE / INCONCLUSIVE
    # =========================================================================

    is_inconclusive = (
        status == "INCONCLUSIVE"
        or extraction_status
        in {
            "unavailable",
            "failed",
            "error",
            "inconclusive",
        }
    )

    if is_inconclusive:

        notice = Table(
            [
                [
                    Paragraph(
                        "<b>EXTRACTION UNAVAILABLE — "
                        "ASSESSMENT INCONCLUSIVE</b>",
                        body_style,
                    )
                ],
                [
                    Paragraph(
                        (
                            "The package image could not be "
                            "reliably processed. Declaration-level "
                            "compliance has therefore not been "
                            "assessed. Values below are shown as "
                            "NOT ASSESSED and must not be interpreted "
                            "as confirmed package deficiencies."
                        ),
                        body_style,
                    )
                ],
            ],
            colWidths=[
                575
            ],
        )

        notice.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor(
                            "#64748b"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#f8fafc"
                        ),
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        elements.append(
            notice
        )

        elements.append(
            Spacer(
                1,
                8,
            )
        )

    # =========================================================================
    # RULE 6 DECLARATIONS
    # =========================================================================

    elements.append(
        Paragraph(
            "Rule 6 Declaration Assessment",
            heading_style,
        )
    )

    declaration_rows = [
        [
            Paragraph(
                "<b>Statutory Parameter</b>",
                body_style,
            ),
            Paragraph(
                "<b>Detected Declaration</b>",
                body_style,
            ),
            Paragraph(
                "<b>Assessment</b>",
                body_style,
            ),
        ]
    ]

    declaration_fields = [
        (
            "Declared Net Quantity",
            "net_quantity",
        ),
        (
            "Maximum Retail Price (MRP)",
            "mrp",
        ),
        (
            "Unit Sale Price (USP)",
            "unit_sale_price",
        ),
        (
            "Date of Packing / Mfg",
            "mfg_date",
        ),
        (
            "Expiry / Best Before",
            "expiry_date",
        ),
        (
            "Batch / Lot Number",
            "batch_number",
        ),
    ]

    for label, key in declaration_fields:

        value = declarations.get(
            key
        )

        if is_inconclusive:

            displayed_value = (
                "NOT ASSESSED"
            )

            verdict = (
                "NOT ASSESSED"
            )

        else:

            displayed_value = (
                "MISSING"
                if _missing(value)
                else value
            )

            verdict = (
                _declaration_verdict(
                    scan_data,
                    key,
                    value,
                )
            )

        declaration_rows.append(
            [
                Paragraph(
                    _safe(
                        label
                    ),
                    body_style,
                ),
                Paragraph(
                    _safe(
                        displayed_value
                    ),
                    body_style,
                ),
                Paragraph(
                    _safe(
                        verdict
                    ),
                    body_style,
                ),
            ]
        )

    # =========================================================================
    # MRP TAX CLAUSE
    # =========================================================================

    if is_inconclusive:

        tax_value = (
            "NOT ASSESSED"
        )

        tax_verdict = (
            "NOT ASSESSED"
        )

    else:

        tax_present = declarations.get(
            "has_tax_clause"
        )

        tax_value = (
            "Present"
            if tax_present
            else "Missing / Not Found"
        )

        tax_verdict = (
            _status_from_check(
                _check(
                    scan_data,
                    "mrp_tax_clause",
                )
            )
        )

    declaration_rows.append(
        [
            Paragraph(
                "Tax Inclusivity Clause",
                body_style,
            ),
            Paragraph(
                _safe(
                    tax_value
                ),
                body_style,
            ),
            Paragraph(
                _safe(
                    tax_verdict
                ),
                body_style,
            ),
        ]
    )

    # =========================================================================
    # FSSAI
    # =========================================================================

    is_food = (
        str(
            category
        ).lower()
        == "food"
        or "fssai_license"
        in declarations
    )

    if is_food:

        fssai = declarations.get(
            "fssai_license"
        )

        if is_inconclusive:

            fssai_value = (
                "NOT ASSESSED"
            )

            fssai_verdict = (
                "NOT ASSESSED"
            )

        else:

            fssai_value = (
                "MISSING"
                if _missing(fssai)
                else fssai
            )

            fssai_verdict = (
                _status_from_check(
                    _check(
                        scan_data,
                        "fssai",
                    )
                )
            )

        declaration_rows.append(
            [
                Paragraph(
                    "FSSAI License Number",
                    body_style,
                ),
                Paragraph(
                    _safe(
                        fssai_value
                    ),
                    body_style,
                ),
                Paragraph(
                    _safe(
                        fssai_verdict
                    ),
                    body_style,
                ),
            ]
        )

    # =========================================================================
    # COUNTRY OF ORIGIN
    # =========================================================================

    country = declarations.get(
        "country_of_origin"
    )

    country_check = _check(
        scan_data,
        "country_of_origin",
    )

    country_check_status = (
        country_check.get(
            "status"
        )
    )

    if (
        country_check_status
        == "NOT_APPLICABLE"
    ):

        country_verdict = (
            "NOT APPLICABLE"
        )

    elif is_inconclusive:

        country_verdict = (
            "NOT ASSESSED"
        )

    else:

        country_verdict = (
            _status_from_check(
                country_check
            )
        )

    country_display = (
        "NOT ASSESSED"
        if is_inconclusive
        else (
            "MISSING"
            if _missing(country)
            else country
        )
    )

    declaration_rows.append(
        [
            Paragraph(
                "Country of Origin",
                body_style,
            ),
            Paragraph(
                _safe(
                    country_display
                ),
                body_style,
            ),
            Paragraph(
                _safe(
                    country_verdict
                ),
                body_style,
            ),
        ]
    )

    # =========================================================================
    # DECLARATION TABLE
    # =========================================================================

    declaration_table = Table(
        declaration_rows,
        colWidths=[
            190,
            245,
            140,
        ],
        repeatRows=1,
    )

    declaration_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#0f172a"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    elements.append(
        declaration_table
    )

    # =========================================================================
    # CONSUMER CARE
    # =========================================================================

    elements.append(
        Paragraph(
            "Rule 6(1)(h) Consumer Redressal Audit",
            heading_style,
        )
    )

    care = _as_dict(
        scan_data.get(
            "consumer_care"
        )
    )

    if is_inconclusive:

        phone = (
            "NOT ASSESSED"
        )

        email = (
            "NOT ASSESSED"
        )

        officer = (
            "NOT ASSESSED"
        )

        care_verdict = (
            "NOT ASSESSED"
        )

    else:

        has_phone = bool(
            care.get(
                "has_care_phone",
                False,
            )
        )

        has_email = bool(
            care.get(
                "has_care_email",
                False,
            )
        )

        has_person = bool(
            care.get(
                "has_person_or_designation",
                False,
            )
        )

        phone = (
            care.get(
                "extracted_phone",
                "MISSING",
            )
            if has_phone
            else "MISSING"
        )

        email = (
            care.get(
                "extracted_email",
                "MISSING",
            )
            if has_email
            else "MISSING"
        )

        officer = (
            "DESIGNATED / DETECTED"
            if has_person
            else "MISSING"
        )

        care_check = _check(
            scan_data,
            "consumer_care",
        )

        care_verdict = (
            _status_from_check(
                care_check
            )
            if care_check
            else (
                "VERIFIED"
                if care.get(
                    "is_fully_compliant",
                    False,
                )
                else "NON-COMPLIANT"
            )
        )

    care_rows = [
        [
            Paragraph(
                "<b>Helpline Phone</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    phone
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Helpline Email</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    email
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Officer / Cell Designated</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    officer
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Overall Assessment</b>",
                body_style,
            ),
            Paragraph(
                _safe(
                    care_verdict
                ),
                body_style,
            ),
        ],
    ]

    care_table = Table(
        care_rows,
        colWidths=[
            190,
            385,
        ],
    )

    care_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#f8fafc"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    elements.append(
        care_table
    )

    # =========================================================================
    # RULE 7 FONT
    # =========================================================================

    elements.append(
        Paragraph(
            "Rule 7 Font Assessment",
            heading_style,
        )
    )

    font_audit = _as_dict(
        scan_data.get(
            "font_audit"
        )
    )

    font_required = font_audit.get(
        "required_mm"
    )

    font_detected = font_audit.get(
        "detected_mm"
    )

    font_status = font_audit.get(
        "status"
    )

    if not font_status:

        if is_inconclusive:

            font_status = (
                "NOT ASSESSED"
            )

        elif font_audit.get(
            "compliant"
        ) is True:

            font_status = (
                "VERIFIED"
            )

        elif font_audit.get(
            "compliant"
        ) is False:

            font_status = (
                "NON-COMPLIANT"
            )

        else:

            font_status = (
                "NOT ASSESSED"
            )

    font_rows = [
        [
            Paragraph(
                "Required Minimum",
                body_style,
            ),
            Paragraph(
                _safe(
                    (
                        f"{font_required} mm"
                        if font_required
                        is not None
                        else "NOT ASSESSED"
                    )
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "Detected / Estimated",
                body_style,
            ),
            Paragraph(
                _safe(
                    (
                        f"{font_detected} mm"
                        if font_detected
                        is not None
                        else "NOT ASSESSED"
                    )
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "Assessment",
                body_style,
            ),
            Paragraph(
                _safe(
                    font_status
                ),
                body_style,
            ),
        ],
    ]

    font_table = Table(
        font_rows,
        colWidths=[
            190,
            385,
        ],
    )

    font_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#f8fafc"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    elements.append(
        font_table
    )

    # =========================================================================
    # BARCODE / GS1
    # =========================================================================

    elements.append(
        Paragraph(
            "GS1 Barcode Country Verification",
            heading_style,
        )
    )

    if is_inconclusive:

        barcode_code = (
            "NOT ASSESSED"
        )

        gs1_registered = (
            "NOT ASSESSED"
        )

        origin_match = (
            "NOT ASSESSED"
        )

    else:

        barcode_code = barcode_data.get(
            "code",
            "N/A",
        )

        if barcode_data.get(
            "detected"
        ):

            gs1_registered = (
                "YES / GS1 India"
                if barcode_data.get(
                    "is_gs1_india"
                )
                else "NO / International"
            )

        else:

            gs1_registered = (
                "NO / NOT DETECTED"
            )

        origin_match = barcode_data.get(
            "origin_verified",
            "NOT ASSESSED",
        )

    barcode_rows = [
        [
            Paragraph(
                "Decoded Code",
                body_style,
            ),
            Paragraph(
                _safe(
                    barcode_code
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "GS1 India Registered (890)",
                body_style,
            ),
            Paragraph(
                _safe(
                    gs1_registered
                ),
                body_style,
            ),
        ],
        [
            Paragraph(
                "Origin Reconciliation",
                body_style,
            ),
            Paragraph(
                _safe(
                    origin_match
                ),
                body_style,
            ),
        ],
    ]

    barcode_table = Table(
        barcode_rows,
        colWidths=[
            190,
            385,
        ],
    )

    barcode_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#f8fafc"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    elements.append(
        barcode_table
    )

    # =========================================================================
    # VIOLATIONS
    # =========================================================================

    elements.append(
        Paragraph(
            "Detected Compliance Deficiencies",
            heading_style,
        )
    )

    # VERY IMPORTANT:
    # Always normalize this value.
    #
    # Old records may contain:
    #     list
    #     dict
    #     string
    #     None
    #
    # We only iterate a list here.
    raw_violations = scan_data.get(
        "violations"
    )

    violations = _as_list(
        raw_violations
    )

    if (
        is_inconclusive
        or not violations
    ):

        if is_inconclusive:

            message = (
                "No deficiencies were assessed "
                "because extraction was unavailable."
            )

        else:

            message = (
                "No confirmed compliance deficiencies "
                "are reported for this assessment."
            )

        elements.append(
            Paragraph(
                message,
                body_style,
            )
        )

    else:

        violation_rows = [
            [
                Paragraph(
                    "<b>Code</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Rule</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Severity</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Description</b>",
                    small_style,
                ),
            ]
        ]

        for violation in violations:

            # -----------------------------------------------------------------
            # Handle dictionary violation
            # -----------------------------------------------------------------

            if isinstance(
                violation,
                dict,
            ):

                code = (
                    violation.get(
                        "code"
                    )
                    or violation.get(
                        "violation_code"
                    )
                    or "N/A"
                )

                rule = (
                    violation.get(
                        "rule"
                    )
                    or violation.get(
                        "rule_reference"
                    )
                    or "N/A"
                )

                severity = (
                    violation.get(
                        "severity"
                    )
                    or "HIGH"
                )

                description = (
                    violation.get(
                        "detail"
                    )
                    or violation.get(
                        "description"
                    )
                    or "N/A"
                )

            # -----------------------------------------------------------------
            # Handle malformed legacy list/string/etc.
            # -----------------------------------------------------------------

            else:

                code = "N/A"
                rule = "N/A"
                severity = "HIGH"

                description = str(
                    violation
                )

            violation_rows.append(
                [
                    Paragraph(
                        _safe(
                            code
                        ),
                        small_style,
                    ),
                    Paragraph(
                        _safe(
                            rule
                        ),
                        small_style,
                    ),
                    Paragraph(
                        _safe(
                            severity
                        ),
                        small_style,
                    ),
                    Paragraph(
                        _safe(
                            description
                        ),
                        small_style,
                    ),
                ]
            )

        violation_table = Table(
            violation_rows,
            colWidths=[
                105,
                105,
                65,
                300,
            ],
            repeatRows=1,
        )

        violation_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#0f172a"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor(
                            "#cbd5e1"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        elements.append(
            violation_table
        )

    # =========================================================================
    # REVIEW / ACKNOWLEDGEMENT
    # =========================================================================

    elements.append(
        Spacer(
            1,
            14,
        )
    )

    elements.append(
        Paragraph(
            "Review / Acknowledgement",
            heading_style,
        )
    )

    signature_table = Table(
        [
            [
                Paragraph(
                    "<b>Compliance Reviewer</b>",
                    body_style,
                ),
                Paragraph(
                    "<b>Package Owner / Authorized Representative</b>",
                    body_style,
                ),
            ],
            [
                "\n\n________________________________________",
                "\n\n________________________________________",
            ],
            [
                "Signature / Review Note",
                "Signature / Review Note",
            ],
        ],
        colWidths=[
            287,
            287,
        ],
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#cbd5e1"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(
        signature_table
    )

    # =========================================================================
    # DISCLAIMER
    # =========================================================================

    elements.append(
        Spacer(
            1,
            10,
        )
    )

    elements.append(
        Paragraph(
            (
                "<b>Assessment Notice:</b> This document is an "
                "AI-assisted compliance assessment generated "
                "from package-image extraction and deterministic "
                "project rules. It is not a government certificate, "
                "statutory approval, or substitute for inspection "
                "by an authorized Legal Metrology officer."
            ),
            small_style,
        )
    )

    elements.append(
        Spacer(
            1,
            5,
        )
    )

    elements.append(
        Paragraph(
            (
                "System Note: The compliance verdict and score "
                "shown in this assessment are generated by the "
                "project's compliance assessment pipeline using "
                "extracted package declarations and the applicable "
                "assessment context."
            ),
            small_style,
        )
    )

    # =========================================================================
    # BUILD PDF
    # =========================================================================

    document.build(
        elements
    )

    buffer.seek(0)

    return buffer


# =============================================================================
# COMPATIBILITY ALIAS
# =============================================================================

generate_pdf = (
    generate_statutory_notice_pdf
)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "make_qr_code_image",
    "generate_statutory_notice_pdf",
    "generate_pdf",
]