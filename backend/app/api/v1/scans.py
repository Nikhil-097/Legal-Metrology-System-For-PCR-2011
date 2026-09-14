from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from pydantic import BaseModel

from app.core.feedback_store import record_correction
from app.core.text_parser import (
    audit_consumer_care_details,
    compute_rule_7_font_requirements,
    extract_barcode_info,
    extract_declarations_with_boxes,
    verify_usp_math,
)
from app.services.pdf_generator import (
    generate_statutory_notice_pdf,
)
from services.scan_repository import (
    get_all_scans,
    get_scan,
    save_scan,
)


logger = logging.getLogger(__name__)

# IMPORTANT:
# Do NOT put "/api/v1/scans" here.
#
# app/main.py already does:
# app.include_router(scans.router, prefix="/api/v1/scans")
#
# Therefore this must remain a plain router.
router = APIRouter()


# ============================================================================
# HELPERS
# ============================================================================

def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip().upper() in {
            "",
            "MISSING",
            "N/A",
            "NA",
            "NONE",
            "NULL",
            "UNKNOWN",
        }

    return False


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _value(
    declarations: Dict[str, Any],
    *keys: str,
) -> Any:
    for key in keys:
        value = declarations.get(key)

        if not _is_missing(value):
            return value

    return "MISSING"


def _extract_status(data: Any) -> str:
    if not isinstance(data, dict):
        return "unavailable"

    meta = data.get("_meta")

    if not isinstance(meta, dict):
        return "success"

    return str(
        meta.get("status", "success")
    ).lower()


def _make_inconclusive_result(
    scan_id: str,
    filename: Optional[str],
    front_data: Dict[str, Any],
    back_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extraction failure must NOT be converted into dozens of fake
    missing-label violations.

    The correct state is INCONCLUSIVE / NOT ASSESSED.
    """

    return {
        "scan_id": scan_id,
        "id": scan_id,
        "filename": filename,

        "product_name": "Extraction Unavailable",
        "brand_name": "Extraction Unavailable",
        "category": "Unknown",

        "timestamp": datetime.now().strftime(
            "%d %b %Y • %I:%M %p"
        ),

        "compliance_score": 0.0,
        "score": 0.0,

        "is_compliant": False,
        "status": "INCONCLUSIVE",

        "pdp_surface": "Not Assessed",
        "pdp_area_cm2": 0.0,

        "declarations": {},

        "extracted_data": {},

        "violations": [],

        "barcode_data": {
            "detected": False,
            "code": "N/A",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT ASSESSED",
        },

        "consumer_care": {
            "has_care_email": False,
            "extracted_email": "NOT ASSESSED",
            "has_care_phone": False,
            "extracted_phone": "NOT ASSESSED",
            "has_person_or_designation": False,
            "is_fully_compliant": False,
            "assessment_status": "NOT ASSESSED",
        },

        "bounding_boxes": {},

        "font_audit": {
            "required_mm": None,
            "detected_mm": None,
            "compliant": None,
            "status": "NOT ASSESSED",
        },

        "usp_math": {
            "verified": None,
            "expected": None,
            "status": "NOT ASSESSED",
        },

        "compliance_checks": {},

        "assessment_context": {
            "status": "INCONCLUSIVE",
            "reason": (
                "The package image could not be reliably "
                "processed by the extraction service."
            ),
        },

        "extraction_status": "unavailable",

        "raw_ocr_payload": {
            "front": front_data,
            "back": back_data,
        },

        "message": (
            "Package image could not be reliably processed. "
            "Compliance was not assessed."
        ),
    }


# ============================================================================
# HISTORY
# ============================================================================

@router.get("/history")
async def get_scan_history():
    """
    Return all persisted scans from PostgreSQL.
    """

    try:
        return get_all_scans()

    except Exception as exc:
        logger.exception(
            "Failed to retrieve scan history"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve scan history: "
                f"{str(exc)}"
            ),
        ) from exc


# ============================================================================
# SINGLE SCAN
# ============================================================================

@router.get("/{scan_id}")
async def get_scan_details(
    scan_id: str,
):
    scan = get_scan(scan_id)

    if not scan:
        raise HTTPException(
            status_code=404,
            detail=f"Scan {scan_id} not found.",
        )

    return scan


# ============================================================================
# CSV EXPORT
# ============================================================================

@router.get("/export-csv")
async def export_batch_csv():
    """
    Export persisted scan history as CSV.
    """

    try:
        scans = get_all_scans()

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow(
            [
                "Scan ID",
                "Timestamp",
                "Brand",
                "Commodity",
                "Category",
                "Compliance Score",
                "Status",
                "Barcode",
                "GS1 Origin Match",
                "Net Quantity",
                "MRP",
                "USP",
                "Consumer Care",
                "Violation Count",
                "Violation Details",
            ]
        )

        for scan in scans:

            declarations = (
                scan.get("declarations")
                or scan.get("extracted_data")
                or {}
            )

            barcode = (
                scan.get("barcode_data")
                or {}
            )

            consumer_care = (
                scan.get("consumer_care")
                or {}
            )

            violations = (
                scan.get("violations")
                or []
            )

            violation_details = " | ".join(
                (
                    f"[{v.get('rule', 'N/A')}] "
                    f"{v.get('detail', v.get('description', 'N/A'))}"
                )
                for v in violations
            )

            writer.writerow(
                [
                    scan.get("scan_id"),
                    scan.get("timestamp"),
                    scan.get("brand_name"),
                    scan.get("product_name"),
                    scan.get("category"),
                    f"{scan.get('compliance_score', 0)}%",
                    scan.get("status"),
                    barcode.get(
                        "code",
                        "N/A",
                    ),
                    barcode.get(
                        "origin_verified",
                        "N/A",
                    ),
                    declarations.get(
                        "net_quantity",
                        "MISSING",
                    ),
                    declarations.get(
                        "mrp",
                        "MISSING",
                    ),
                    declarations.get(
                        "unit_sale_price",
                        "MISSING",
                    ),
                    (
                        "COMPLIANT"
                        if consumer_care.get(
                            "is_fully_compliant"
                        )
                        else "DEFICIENT"
                    ),
                    len(violations),
                    violation_details,
                ]
            )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    "attachment; "
                    f"filename=Legal_Metrology_Batch_Audit_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
            },
        )

    except Exception as exc:
        logger.exception(
            "CSV export failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to export CSV: "
                f"{str(exc)}"
            ),
        ) from exc


# ============================================================================
# PACKAGE ANALYSIS
# ============================================================================

@router.post("/analyze")
async def analyze_package(
    front_file: UploadFile = File(...),
    back_file: Optional[UploadFile] = File(None),

    category: str = Form("food"),

    height_cm: float = Form(15.0),
    width_cm: float = Form(10.0),

    pdp_type: str = Form(
        "Rectangular (Height × Width)"
    ),

    brand_name: Optional[str] = Form(None),
    commodity_name: Optional[str] = Form(None),
):
    """
    Complete package analysis pipeline.

    Image
      ↓
    Gemini extraction
      ↓
    Declaration merge
      ↓
    Barcode audit
      ↓
    Consumer-care audit
      ↓
    Rule 7 font assessment
      ↓
    USP calculation
      ↓
    Compliance assessment
      ↓
    PostgreSQL
    """

    scan_id = (
        f"SCN-{uuid.uuid4().hex[:6].upper()}"
    )

    try:

        # ------------------------------------------------------------------
        # 1. READ FILES
        # ------------------------------------------------------------------

        front_bytes = await front_file.read()

        back_bytes = (
            await back_file.read()
            if back_file
            else None
        )

        if not front_bytes:
            raise HTTPException(
                status_code=400,
                detail="Front package image is empty.",
            )

        # ------------------------------------------------------------------
        # 2. GEMINI EXTRACTION
        # ------------------------------------------------------------------

        try:

            front_data = (
                await extract_declarations_with_boxes(
                    front_bytes,
                    surface_type="front",
                )
            )

        except Exception as exc:

            logger.exception(
                "Front extraction failed for %s",
                scan_id,
            )

            front_data = {
                "_meta": {
                    "status": "unavailable",
                    "error": str(exc),
                }
            }

        if not isinstance(
            front_data,
            dict,
        ):
            front_data = {
                "_meta": {
                    "status": "unavailable"
                }
            }

        front_status = _extract_status(
            front_data
        )

        # ------------------------------------------------------------------
        # 3. BACK EXTRACTION
        # ------------------------------------------------------------------

        if back_bytes:

            try:

                back_data = (
                    await extract_declarations_with_boxes(
                        back_bytes,
                        surface_type="back",
                    )
                )

            except Exception as exc:

                logger.warning(
                    "Back extraction failed for %s: %s",
                    scan_id,
                    exc,
                )

                back_data = {
                    "_meta": {
                        "status": "unavailable",
                        "error": str(exc),
                    }
                }

        else:

            back_data = {}

        # ------------------------------------------------------------------
        # 4. EXTRACTION FAILURE HANDLING
        # ------------------------------------------------------------------

        #
        # If the front image cannot be extracted at all, do not fabricate
        # "missing" declarations.
        #

        if front_status in {
            "unavailable",
            "failed",
            "error",
            "inconclusive",
        }:

            result = _make_inconclusive_result(
                scan_id=scan_id,
                filename=front_file.filename,
                front_data=front_data,
                back_data=back_data,
            )

            try:
                persisted = save_scan(
                    result,
                    raw_ocr_payload={
                        "front": front_data,
                        "back": back_data,
                    },
                )

                return persisted

            except TypeError:
                # Compatibility with repository versions that don't accept
                # raw_ocr_payload.
                persisted = save_scan(
                    result
                )

                return persisted

        # ------------------------------------------------------------------
        # 5. BARCODE
        # ------------------------------------------------------------------

        barcode_info = {
            "detected": False,
            "code": "N/A",
            "country": "Unknown",
            "is_gs1_india": False,
        }

        try:

            if back_bytes:

                barcode_info = (
                    extract_barcode_info(
                        back_bytes
                    )
                )

            if not barcode_info.get(
                "detected",
                False,
            ):

                barcode_info = (
                    extract_barcode_info(
                        front_bytes
                    )
                )

        except Exception as exc:

            logger.warning(
                "Barcode extraction failed for %s: %s",
                scan_id,
                exc,
            )

        if not isinstance(
            barcode_info,
            dict,
        ):
            barcode_info = {
                "detected": False,
                "code": "N/A",
                "country": "Unknown",
                "is_gs1_india": False,
            }

        # ------------------------------------------------------------------
        # 6. MERGE DECLARATIONS
        # ------------------------------------------------------------------

        declarations: Dict[str, Any] = {}

        front_clean = {
            k: v
            for k, v in front_data.items()
            if k != "_meta"
        }

        back_clean = {
            k: v
            for k, v in back_data.items()
            if k != "_meta"
        }

        all_keys = set(
            front_clean.keys()
        ).union(
            back_clean.keys()
        )

        for key in all_keys:

            front_value = front_clean.get(
                key
            )

            back_value = back_clean.get(
                key
            )

            if not _is_missing(
                front_value
            ):
                declarations[key] = (
                    front_value
                )

            elif not _is_missing(
                back_value
            ):
                declarations[key] = (
                    back_value
                )

            else:
                declarations[key] = (
                    front_value
                    if front_value is not None
                    else "MISSING"
                )

        # ------------------------------------------------------------------
        # 7. USER FALLBACKS
        # ------------------------------------------------------------------

        if (
            brand_name
            and _is_missing(
                declarations.get(
                    "brand_name"
                )
            )
        ):
            declarations[
                "brand_name"
            ] = brand_name

        if (
            commodity_name
            and _is_missing(
                declarations.get(
                    "commodity_name"
                )
            )
        ):
            declarations[
                "commodity_name"
            ] = commodity_name

        # ------------------------------------------------------------------
        # 8. CATEGORY
        # ------------------------------------------------------------------

        is_food = (
            category.strip().lower()
            == "food"
        )

        if not is_food:
            declarations.pop(
                "fssai_license",
                None,
            )

        # ------------------------------------------------------------------
        # 9. CONSUMER CARE
        # ------------------------------------------------------------------

        care_corpus = " ".join(
            [
                str(
                    front_clean.get(
                        "consumer_care_raw_text",
                        "",
                    )
                ),
                str(
                    back_clean.get(
                        "consumer_care_raw_text",
                        "",
                    )
                ),
            ]
        )

        try:

            consumer_care_audit = (
                audit_consumer_care_details(
                    care_corpus
                )
            )

        except Exception as exc:

            logger.warning(
                "Consumer care audit failed: %s",
                exc,
            )

            consumer_care_audit = {
                "has_care_email": False,
                "extracted_email": "MISSING",
                "has_care_phone": False,
                "extracted_phone": "MISSING",
                "has_person_or_designation": False,
                "is_fully_compliant": False,
            }

        # ------------------------------------------------------------------
        # 10. RULE 7
        # ------------------------------------------------------------------

        pdp_surface_area = (
            max(0.0, height_cm)
            * max(0.0, width_cm)
        )

        required_font_height_mm = (
            compute_rule_7_font_requirements(
                pdp_surface_area
            )
        )

        detected_font_mm = declarations.get(
            "font_height_mm_estimate"
        )

        if _is_missing(
            detected_font_mm
        ):
            detected_font_mm = None

        if detected_font_mm is not None:

            detected_font_mm = _safe_float(
                detected_font_mm,
                default=0.0,
            )

            font_compliant = (
                detected_font_mm
                >= required_font_height_mm
            )

            font_status = (
                "VERIFIED"
                if font_compliant
                else "NON-COMPLIANT"
            )

        else:

            font_compliant = None
            font_status = "NOT ASSESSED"

        # ------------------------------------------------------------------
        # 11. USP
        # ------------------------------------------------------------------

        mrp = declarations.get(
            "mrp"
        )

        net_quantity = declarations.get(
            "net_quantity"
        )

        declared_usp = declarations.get(
            "unit_sale_price"
        )

        usp_verified: Optional[bool] = None
        computed_usp: Optional[str] = None

        if (
            not _is_missing(mrp)
            and not _is_missing(net_quantity)
            and not _is_missing(declared_usp)
        ):

            try:

                usp_verified, computed_usp = (
                    verify_usp_math(
                        mrp,
                        net_quantity,
                        declared_usp,
                    )
                )

            except Exception as exc:

                logger.warning(
                    "USP verification failed for %s: %s",
                    scan_id,
                    exc,
                )

                usp_verified = None
                computed_usp = None

        elif (
            not _is_missing(mrp)
            and not _is_missing(net_quantity)
            and _is_missing(declared_usp)
        ):

            # A computable expected USP exists, but the package declaration
            # itself is missing.
            try:

                _, computed_usp = (
                    verify_usp_math(
                        mrp,
                        net_quantity,
                        "MISSING",
                    )
                )

            except Exception:
                computed_usp = None

            usp_verified = False

        # ------------------------------------------------------------------
        # 12. GS1 COUNTRY RECONCILIATION
        # ------------------------------------------------------------------

        origin = declarations.get(
            "country_of_origin"
        )

        gs1_origin_match = True

        if (
            barcode_info.get(
                "detected"
            )
            and barcode_info.get(
                "is_gs1_india"
            )
            and not _is_missing(origin)
        ):

            if "india" not in str(
                origin
            ).lower():

                gs1_origin_match = False

        barcode_info[
            "origin_verified"
        ] = (
            "MATCH"
            if gs1_origin_match
            else "DISCREPANCY"
        )

        # ------------------------------------------------------------------
        # 13. COMPLIANCE SCORING
        # ------------------------------------------------------------------

        score = 100.0

        violations: List[
            Dict[str, Any]
        ] = []

        def add_violation(
            code: str,
            rule: str,
            detail: str,
            severity: str,
            remedial_action: str,
        ):

            violations.append(
                {
                    "code": code,
                    "rule": rule,
                    "detail": detail,
                    "severity": severity,
                    "remedial_action":
                        remedial_action,
                }
            )

        # Mandatory declarations

        mandatory_fields = {
            "net_quantity": (
                "Declared Net Quantity "
                "(Rule 6(1)(b))"
            ),
            "mrp": (
                "Maximum Retail Price "
                "(Rule 6(1)(e))"
            ),
            "mfg_date": (
                "Date of Packing / Mfg"
            ),
            "commodity_name": (
                "Generic Commodity Name"
            ),
        }

        for field, label in (
            mandatory_fields.items()
        ):

            if _is_missing(
                declarations.get(field)
            ):

                score -= 15

                add_violation(
                    "MANDATORY_DECLARATION_MISSING",
                    "Rule 6 Mandatory Declaration",
                    (
                        f"Mandatory declaration "
                        f"'{label}' is missing "
                        "or unreadable."
                    ),
                    "HIGH",
                    (
                        f"Ensure '{label}' "
                        "is clearly declared "
                        "on the package."
                    ),
                )

        # Brand

        if _is_missing(
            declarations.get(
                "brand_name"
            )
        ):

            score -= 10

            add_violation(
                "STATUTORY_ADVISORY_MISSING",
                "Package Declaration",
                "Brand name is missing or unreadable.",
                "MEDIUM",
                "Review the package artwork and declare the brand name.",
            )

        # Batch

        if _is_missing(
            declarations.get(
                "batch_number"
            )
        ):

            score -= 10

            add_violation(
                "STATUTORY_ADVISORY_MISSING",
                "Rule 6",
                "Batch / lot identification is missing or unreadable.",
                "MEDIUM",
                "Declare the applicable batch or lot identification.",
            )

        # FSSAI

        if is_food:

            if _is_missing(
                declarations.get(
                    "fssai_license"
                )
            ):

                score -= 10

                add_violation(
                    "STATUTORY_ADVISORY_MISSING",
                    "Food-category declaration",
                    "FSSAI License / Registration No. is missing or unreadable.",
                    "MEDIUM",
                    "Declare the applicable FSSAI licence/registration number.",
                )

        # Tax clause

        has_tax_clause = declarations.get(
            "has_tax_clause"
        )

        if has_tax_clause is False:

            score -= 10

            add_violation(
                "MRP_TAX_CLAUSE_MISSING",
                "Rule 6 MRP Tax Clause",
                (
                    "The required MRP tax "
                    "inclusivity declaration "
                    "could not be verified."
                ),
                "HIGH",
                (
                    "Ensure the applicable "
                    "MRP declaration contains "
                    "the required tax statement."
                ),
            )

        # USP

        if usp_verified is False:

            score -= 10

            add_violation(
                "UNIT_SALE_PRICE_INVALID",
                "Rule 6(11)",
                (
                    "Unit Sale Price is "
                    "missing or does not "
                    "match the MRP/net "
                    "quantity calculation."
                ),
                "HIGH",
                (
                    "Declare the correct "
                    "Unit Sale Price rounded "
                    "as prescribed."
                ),
            )

        # Consumer care

        if not consumer_care_audit.get(
            "is_fully_compliant",
            False,
        ):

            score -= 10

            missing_parts = []

            if not consumer_care_audit.get(
                "has_care_email",
                False,
            ):
                missing_parts.append(
                    "Email ID"
                )

            if not consumer_care_audit.get(
                "has_care_phone",
                False,
            ):
                missing_parts.append(
                    "Helpline Phone"
                )

            if not consumer_care_audit.get(
                "has_person_or_designation",
                False,
            ):
                missing_parts.append(
                    "Designated Officer / Contact"
                )

            add_violation(
                "CONSUMER_CARE_DEFICIENCY",
                "Rule 6(1)(h)",
                (
                    "Missing redressal "
                    "components: "
                    + ", ".join(
                        missing_parts
                    )
                ),
                "HIGH",
                (
                    "Provide the required "
                    "consumer grievance "
                    "redressal contact details."
                ),
            )

        # Rule 7

        if font_compliant is False:

            score -= 10

            add_violation(
                "RULE_7_FONT_SIZE",
                "Rule 7 Font Size",
                (
                    f"Estimated font height "
                    f"({detected_font_mm} mm) "
                    f"is below the required "
                    f"{required_font_height_mm} mm."
                ),
                "HIGH",
                (
                    "Increase the relevant "
                    "declaration font size "
                    "to meet the applicable "
                    "Rule 7 requirement."
                ),
            )

        # GS1

        if not gs1_origin_match:

            score -= 10

            add_violation(
                "GS1_ORIGIN_DISCREPANCY",
                "GS1 Country of Origin",
                (
                    "GS1 India barcode "
                    "information conflicts "
                    "with the declared "
                    "country of origin."
                ),
                "MEDIUM",
                (
                    "Verify barcode assignment "
                    "and declared country "
                    "of origin."
                ),
            )

        # ------------------------------------------------------------------
        # 14. SCORE
        # ------------------------------------------------------------------

        compliance_score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        # ------------------------------------------------------------------
        # 15. STATUS
        # ------------------------------------------------------------------

        if compliance_score >= 85:

            status = "COMPLIANT"

        elif compliance_score >= 70:

            status = "WARNING"

        else:

            status = "NON-COMPLIANT"

        # IMPORTANT:
        # 70 is NOT COMPLIANT.
        # COMPLIANT starts at 85.

        is_compliant = (
            status == "COMPLIANT"
        )

        # ------------------------------------------------------------------
        # 16. STRUCTURED COMPLIANCE CHECKS
        # ------------------------------------------------------------------

        def declaration_check(
            field: str,
            rule: str,
        ):

            value = declarations.get(
                field
            )

            passed = not _is_missing(
                value
            )

            return {
                "passed": passed,
                "status": (
                    "VERIFIED"
                    if passed
                    else "NON-COMPLIANT"
                ),
                "rule_reference": rule,
                "evidence": {
                    "detected_value": value
                },
            }

        compliance_checks = {
            "net_quantity":
                declaration_check(
                    "net_quantity",
                    "Rule 6(1)(b)",
                ),

            "mrp":
                declaration_check(
                    "mrp",
                    "Rule 6(1)(e)",
                ),

            "mfg_date":
                declaration_check(
                    "mfg_date",
                    "Rule 6",
                ),

            "commodity_name":
                declaration_check(
                    "commodity_name",
                    "Rule 6",
                ),

            "brand_name":
                declaration_check(
                    "brand_name",
                    "Package Declaration",
                ),

            "batch_number":
                declaration_check(
                    "batch_number",
                    "Rule 6",
                ),

            "mrp_tax_clause": {
                "passed": (
                    True
                    if has_tax_clause is not False
                    else False
                ),
                "status": (
                    "VERIFIED"
                    if has_tax_clause is not False
                    else "NON-COMPLIANT"
                ),
                "rule_reference":
                    "Rule 6(1)(e)",
                "evidence": {
                    "verified":
                        has_tax_clause
                },
            },

            "usp_math": {
                "passed": usp_verified,
                "status": (
                    "VERIFIED"
                    if usp_verified is True
                    else (
                        "NON-COMPLIANT"
                        if usp_verified is False
                        else "NOT ASSESSABLE"
                    )
                ),
                "rule_reference":
                    "Rule 6(11)",
                "evidence": {
                    "declared":
                        declared_usp,
                    "expected":
                        computed_usp,
                    "verified":
                        usp_verified,
                },
            },

            "consumer_care": {
                "passed":
                    consumer_care_audit.get(
                        "is_fully_compliant",
                        False,
                    ),
                "status": (
                    "VERIFIED"
                    if consumer_care_audit.get(
                        "is_fully_compliant",
                        False,
                    )
                    else "NON-COMPLIANT"
                ),
                "rule_reference":
                    "Rule 6(1)(h)",
                "evidence":
                    consumer_care_audit,
            },

            "font_size": {
                "passed":
                    font_compliant,
                "status":
                    font_status,
                "rule_reference":
                    "Rule 7",
                "evidence": {
                    "required_mm":
                        required_font_height_mm,
                    "detected_mm":
                        detected_font_mm,
                },
            },

            "country_of_origin": {
                "passed":
                    True,
                "status":
                    "NOT_APPLICABLE",
                "rule_reference":
                    "Rule 6(1)",
                "evidence": {
                    "required":
                        False,
                    "detected_value":
                        declarations.get(
                            "country_of_origin"
                        ),
                },
            },
        }

        if is_food:

            fssai_value = declarations.get(
                "fssai_license"
            )

            fssai_passed = (
                not _is_missing(
                    fssai_value
                )
            )

            compliance_checks[
                "fssai"
            ] = {
                "passed":
                    fssai_passed,
                "status": (
                    "VERIFIED"
                    if fssai_passed
                    else "NON-COMPLIANT"
                ),
                "rule_reference":
                    "Food-category declaration",
                "evidence": {
                    "detected_value":
                        fssai_value,
                },
            }

        # ------------------------------------------------------------------
        # 17. RESULT
        # ------------------------------------------------------------------

        scan_record = {
            "scan_id": scan_id,
            "id": scan_id,

            "filename":
                front_file.filename,

            "product_name":
                declarations.get(
                    "commodity_name"
                )
                or commodity_name
                or "Packaged Commodity",

            "brand_name":
                declarations.get(
                    "brand_name"
                )
                or brand_name
                or "Unknown Brand",

            "category":
                "Food"
                if is_food
                else "Drugs & Commodities",

            "timestamp":
                datetime.now().strftime(
                    "%d %b %Y • %I:%M %p"
                ),

            "compliance_score":
                compliance_score,

            "score":
                compliance_score,

            "status":
                status,

            "is_compliant":
                is_compliant,

            "pdp_surface":
                (
                    f"{pdp_surface_area:.1f} cm² "
                    f"({pdp_type})"
                ),

            "pdp_area_cm2":
                pdp_surface_area,

            "height_cm":
                height_cm,

            "width_cm":
                width_cm,

            "pdp_type":
                pdp_type,

            "declarations":
                declarations,

            "extracted_data":
                declarations,

            "violations":
                violations,

            "barcode_data":
                barcode_info,

            "consumer_care":
                consumer_care_audit,

            "bounding_boxes":
                front_clean.get(
                    "bounding_boxes",
                    {},
                ),

            "font_audit": {
                "required_mm":
                    required_font_height_mm,
                "detected_mm":
                    detected_font_mm,
                "compliant":
                    font_compliant,
                "status":
                    font_status,
            },

            "usp_math": {
                "verified":
                    usp_verified,
                "expected":
                    computed_usp,
                "declared":
                    declared_usp,
            },

            "compliance_checks":
                compliance_checks,

            "assessment_context": {
                "category":
                    category,
                "is_food":
                    is_food,
                "is_imported":
                    False,
                "is_wholesale_package":
                    False,
                "is_retail_package":
                    True,
            },

            "extraction_status":
                "success",

            "raw_ocr_payload": {
                "front":
                    front_data,
                "back":
                    back_data,
            },
        }

        # ------------------------------------------------------------------
        # 18. POSTGRESQL
        # ------------------------------------------------------------------

        try:

            persisted_scan = save_scan(
                scan_record,
                raw_ocr_payload={
                    "front":
                        front_data,
                    "back":
                        back_data,
                },
            )

        except TypeError:

            # Compatibility with an older repository signature.

            persisted_scan = save_scan(
                scan_record
            )

        return persisted_scan

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            "Analysis pipeline failure for %s",
            scan_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis pipeline failure: "
                f"{str(exc)}"
            ),
        ) from exc


# ============================================================================
# PDF EXPORT
# ============================================================================

@router.get("/{scan_id}/export-pdf")
async def export_scan_pdf(
    scan_id: str,
):
    """
    Generate PDF from the persisted scan.

    IMPORTANT:
    generate_statutory_notice_pdf returns a BytesIO object.
    Convert it to raw bytes before giving it to FastAPI Response.
    """

    scan = get_scan(
        scan_id
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan record not found.",
        )

    try:

        pdf_buffer = (
            generate_statutory_notice_pdf(
                scan
            )
        )

        # The generator returns BytesIO.
        if isinstance(
            pdf_buffer,
            io.BytesIO,
        ):

            pdf_bytes = (
                pdf_buffer.getvalue()
            )

        elif isinstance(
            pdf_buffer,
            (bytes, bytearray),
        ):

            pdf_bytes = bytes(
                pdf_buffer
            )

        else:

            raise TypeError(
                "PDF generator returned "
                f"unsupported type: "
                f"{type(pdf_buffer).__name__}"
            )

        filename = (
            f"Legal_Metrology_Notice_"
            f"{scan_id}.pdf"
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"',
                "Content-Length":
                    str(len(pdf_bytes)),
            },
        )

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            "PDF generation failed for %s",
            scan_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate PDF: "
                f"{str(exc)}"
            ),
        ) from exc


# ============================================================================
# HUMAN-IN-THE-LOOP CORRECTION
# ============================================================================

class CorrectionPayload(BaseModel):
    brand_name: Optional[str] = "General"
    corrected_fields: Dict[str, Any]
    previous_mistake: Optional[
        Dict[str, Any]
    ] = None


@router.post("/correct")
async def save_scan_correction(
    payload: CorrectionPayload,
):
    """
    Record a human correction for future
    extraction improvement.
    """

    try:

        record_correction(
            brand_name=payload.brand_name,
            corrected_fields=payload.corrected_fields,
            raw_mistake=payload.previous_mistake,
        )

        return {
            "status": "success",
            "message": (
                "Correction committed "
                "to system memory."
            ),
        }

    except Exception as exc:

        logger.exception(
            "Correction recording failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save correction: "
                f"{str(exc)}"
            ),
        ) from exc