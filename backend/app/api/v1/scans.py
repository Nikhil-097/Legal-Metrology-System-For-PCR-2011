from pydantic import BaseModel
import io
import csv
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.core.text_parser import (
    extract_declarations_with_boxes,
    extract_barcode_info,
    audit_consumer_care_details,
    compute_rule_7_font_requirements,
    verify_usp_math
)
from app.db.database import save_scan, get_all_scans, get_scan
from app.services.pdf_generator import generate_statutory_notice_pdf

router = APIRouter()

@router.get("/history")
async def get_scan_history():
    return get_all_scans()

@router.get("/export-csv")
async def export_batch_csv():
    """Generates an aggregated CSV export for enforcement officers & FMCG auditors."""
    scans = get_all_scans()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Scan ID", "Timestamp", "Brand", "Commodity", "Category",
        "Compliance Score", "Status", "Barcode", "GS1 Origin Match",
        "Net Qty Declared", "MRP Declared", "USP Declared", "Consumer Care Status",
        "Infractions Count", "Infraction Details"
    ])

    for s in scans:
        dec = s.get("declarations", {})
        bar = s.get("barcode_data", {})
        care = s.get("consumer_care", {})
        v_list = s.get("violations", [])
        v_summary = " | ".join([f"[{v.get('rule')}] {v.get('detail')}" for v in v_list])

        writer.writerow([
            s.get("scan_id"),
            s.get("timestamp"),
            s.get("brand_name"),
            s.get("product_name"),
            s.get("category"),
            f"{s.get('compliance_score')}%",
            s.get("status"),
            bar.get("code", "N/A"),
            bar.get("origin_verified", "N/A"),
            dec.get("net_quantity", "MISSING"),
            dec.get("mrp", "MISSING"),
            dec.get("unit_sale_price", "MISSING"),
            "COMPLIANT" if care.get("is_fully_compliant") else "DEFICIENT",
            len(v_list),
            v_summary
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Legal_Metrology_Batch_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.post("/analyze")
async def analyze_package(
    front_file: UploadFile = File(...),
    back_file: Optional[UploadFile] = File(None),
    category: str = Form("food"),
    height_cm: float = Form(15.0),
    width_cm: float = Form(10.0),
    pdp_type: str = Form("Rectangular (Height × Width)"),
    brand_name: Optional[str] = Form(None),
    commodity_name: Optional[str] = Form(None),
):
    try:
        front_bytes = await front_file.read()
        back_bytes = await back_file.read() if back_file else None

        # 1. Optical Extractions (Dual Surface Processing)
        front_data = await extract_declarations_with_boxes(front_bytes, surface_type="front")
        back_data = await extract_declarations_with_boxes(back_bytes, surface_type="back") if back_bytes else {}

        # Barcode extraction: Check back panel first, fallback to front
        barcode_info = extract_barcode_info(back_bytes) if back_bytes else {"detected": False}
        if not barcode_info.get("detected"):
            barcode_info = extract_barcode_info(front_bytes)

        # Merge declarations across surfaces (Back panel fills gaps of Front panel)
        declarations = {}
        all_keys = set(list(front_data.keys()) + list(back_data.keys()))
        for k in all_keys:
            val = front_data.get(k)
            if not val or val == "MISSING":
                val = back_data.get(k, "MISSING")
            declarations[k] = val

        if brand_name and (declarations.get("brand_name") in ["MISSING", None, ""]):
            declarations["brand_name"] = brand_name
        if commodity_name and (declarations.get("commodity_name") in ["MISSING", None, ""]):
            declarations["commodity_name"] = commodity_name

        is_food = (category.lower() == "food")
        if not is_food:
            declarations.pop("fssai_license", None)

        # 2. Rule 6(1)(h) Consumer Care Redressal Audit
        care_corpus = f"{front_data.get('consumer_care_raw_text', '')} {back_data.get('consumer_care_raw_text', '')}"
        consumer_care_audit = audit_consumer_care_details(care_corpus)

        # 3. Rule 7 Font Height Scaling Check
        pdp_surface_area = width_cm * height_cm
        required_font_height_mm = compute_rule_7_font_requirements(pdp_surface_area)
        detected_font_mm = declarations.get("font_height_mm_estimate", 2.0)
        font_compliant = detected_font_mm >= required_font_height_mm

        # 4. USP Math Verification
        has_math, computed_usp = verify_usp_math(
            declarations.get("mrp", ""),
            declarations.get("net_quantity", ""),
            declarations.get("unit_sale_price", "")
        )

        # 5. GS1 Barcode Cross-Check
        gs1_origin_match = True
        origin_country = (declarations.get("country_of_origin") or "India").lower()
        if barcode_info.get("detected") and barcode_info.get("is_gs1_india"):
            if "india" not in origin_country:
                gs1_origin_match = False
        barcode_info["origin_verified"] = "MATCH" if gs1_origin_match else "DISCREPANCY"

        score = 100
        violations = []

        critical_fields = {
            "net_quantity": "Declared Net Quantity (Rule 6(1)(e))",
            "mrp": "Maximum Retail Price (Rule 6(1)(d))",
            "mfg_date": "Date of Packing / Mfg (Rule 6(1)(c))",
            "commodity_name": "Generic Commodity Name (Rule 6(1)(b))"
        }
        advisory_fields = {
            "brand_name": "Brand Name",
            "batch_number": "Batch / Lot Serial Number",
            "unit_sale_price": "Unit Sale Price (USP)",
        }
        if is_food:
            advisory_fields["fssai_license"] = "FSSAI License / Registration No."

        for field, label in critical_fields.items():
            if declarations.get(field) in [None, "MISSING", ""]:
                score -= 15
                violations.append({
                    "rule": "Rule 6(1) Mandatory Omission",
                    "detail": f"Mandatory declaration '{label}' is missing or unreadable across packaging surfaces."
                })

        for field, label in advisory_fields.items():
            if declarations.get(field) in [None, "MISSING", ""]:
                score -= 10
                violations.append({
                    "rule": "Rule 6 Statutory Advisory",
                    "detail": f"Declaration '{label}' is missing or not clearly indicated."
                })

        if not declarations.get("has_tax_clause", True):
            score -= 10
            violations.append({
                "rule": "Rule 6(1)(e) Tax Clause",
                "detail": "MRP does not contain statutory 'Inclusive of all taxes' notice."
            })

        if not font_compliant:
            score -= 10
            violations.append({
                "rule": "Rule 7 Font Size Contravention",
                "detail": f"Estimated font height ({detected_font_mm} mm) is below the minimum required ({required_font_height_mm} mm) for PDP area {pdp_surface_area:.1f} cm²."
            })

        if not consumer_care_audit["is_fully_compliant"]:
            score -= 10
            missing_parts = []
            if not consumer_care_audit["has_care_email"]: missing_parts.append("Email ID")
            if not consumer_care_audit["has_care_phone"]: missing_parts.append("Helpline Phone")
            if not consumer_care_audit["has_person_or_designation"]: missing_parts.append("Designated Officer Name")
            violations.append({
                "rule": "Rule 6(1)(h) Consumer Care Grievance Defect",
                "detail": f"Missing redressal components: {', '.join(missing_parts)}."
            })

        if not gs1_origin_match:
            score -= 10
            violations.append({
                "rule": "GS1 Country of Origin Discrepancy",
                "detail": f"Barcode specifies GS1 India (Prefix 890), but artwork claims origin '{declarations.get('country_of_origin')}'."
            })

        compliance_score = max(0, min(100, score))
        status = "COMPLIANT" if compliance_score >= 85 else "WARNING" if compliance_score >= 70 else "NON-COMPLIANT"
        scan_id = f"SCN-{uuid.uuid4().hex[:6].upper()}"
        timestamp_str = datetime.now().strftime("%d %b %Y • %I:%M %p")

        scan_record = {
            "scan_id": scan_id,
            "id": scan_id,
            "filename": front_file.filename,
            "product_name": declarations.get("commodity_name") or commodity_name or "Packaged Commodity",
            "brand_name": declarations.get("brand_name") or brand_name or "Unknown Brand",
            "category": "Food" if is_food else "Drugs & Commodities",
            "timestamp": timestamp_str,
            "compliance_score": compliance_score,
            "score": compliance_score,
            "is_compliant": compliance_score >= 70,
            "status": status,
            "pdp_surface": f"{pdp_surface_area:.1f} cm² ({pdp_type})",
            "declarations": declarations,
            "violations": violations,
            "barcode_data": barcode_info,
            "consumer_care": consumer_care_audit,
            "bounding_boxes": front_data.get("bounding_boxes", {}),
            "font_audit": {
                "required_mm": required_font_height_mm,
                "detected_mm": detected_font_mm,
                "compliant": font_compliant
            },
            "usp_math": {
                "verified": has_math,
                "expected": computed_usp
            }
        }

        save_scan(scan_record)
        return scan_record

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failure: {str(e)}")

@router.get("/{scan_id}/export-pdf")
async def export_scan_pdf(scan_id: str):
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found.")

    pdf_buffer = generate_statutory_notice_pdf(scan)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Legal_Metrology_Notice_{scan_id}.pdf"}
    )
# Backwards compatibility export for reports.py and legacy routers
IN_MEMORY_SCAN_DB: List[Dict[str, Any]] = []

def sync_in_memory_db():
    global IN_MEMORY_SCAN_DB
    IN_MEMORY_SCAN_DB = get_all_scans()

# --- Human-in-the-Loop Feedback Learning Endpoint ---

from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.feedback_store import record_correction

class CorrectionPayload(BaseModel):
    brand_name: Optional[str] = "General"
    corrected_fields: Dict[str, Any]
    previous_mistake: Optional[Dict[str, Any]] = None

@router.post("/correct")
async def save_scan_correction(payload: CorrectionPayload):
    record_correction(
        brand_name=payload.brand_name,
        corrected_fields=payload.corrected_fields,
        raw_mistake=payload.previous_mistake
    )
    return {"status": "success", "message": "Correction committed to system memory."}