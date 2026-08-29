import os
import uuid
import tempfile
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import cv2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.preprocessor import ImagePreprocessor
from app.core.ocr_engine import OCREngine
from app.core.rule_evaluator import LegalMetrologyVerifier

router = APIRouter()

# Global in-memory storage required by reports.py and analytics.py
IN_MEMORY_SCAN_DB: List[Dict[str, Any]] = []

ocr_engine = OCREngine()
rule_evaluator = LegalMetrologyVerifier()


def _process_scan_pipeline(
    temp_file_path: str,
    brand_name: Optional[str],
    commodity_name: Optional[str],
    pdp_area_cm2: float,
    ppm_scale: float,
) -> Dict[str, Any]:
    cv_img = cv2.imread(temp_file_path)
    if cv_img is None:
        raise ValueError("Could not decode image.")

    preprocessed_img = ImagePreprocessor.enhance_for_ocr(cv_img)
    tokens = ocr_engine.extract_tokens(preprocessed_img, ppm_scale=ppm_scale)

    verification = rule_evaluator.extract_and_verify(
        tokens=tokens,
        pdp_area_cm2=pdp_area_cm2,
        ppm_scale=ppm_scale,
        brand_name=brand_name,
        commodity_name=commodity_name,
        image=cv_img,
        image_path=temp_file_path,
    )

    scan_id = f"SCAN_{uuid.uuid4().hex[:6].upper()}"
    scan_record = {
        "scan_id": scan_id,
        "timestamp": datetime.now().isoformat(),
        "brand_name": brand_name or verification.get("extracted_declarations", {}).get("brand_name", "General Goods"),
        "commodity_name": commodity_name or verification.get("extracted_declarations", {}).get("commodity_name", "Packaged Commodity"),
        "pdp_area_cm2": pdp_area_cm2,
        "compliance_score": verification.get("compliance_score", 0),
        "is_compliant": verification.get("is_compliant", False),
        "violations": verification.get("violations", []),
        "extracted_declarations": verification.get("extracted_declarations", {}),
        "raw_text_extracted": verification.get("raw_text_extracted", []),
    }

    IN_MEMORY_SCAN_DB.append(scan_record)
    return scan_record


@router.post("/analyze")
@router.post("/verify")
async def analyze_package(
    file: UploadFile = File(...),
    brand_name: Optional[str] = Form(None),
    commodity_name: Optional[str] = Form(None),
    pdp_area_cm2: Optional[float] = Form(85.0),
    ppm_scale: Optional[float] = Form(3.78),
):
    temp_dir = tempfile.gettempdir()
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    temp_file_path = os.path.join(temp_dir, f"scan_{uuid.uuid4().hex}{file_ext}")

    try:
        contents = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(contents)

        result = await asyncio.to_thread(
            _process_scan_pipeline,
            temp_file_path=temp_file_path,
            brand_name=brand_name or file.filename,
            commodity_name=commodity_name or "Packaged Commodity",
            pdp_area_cm2=pdp_area_cm2,
            ppm_scale=ppm_scale,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@router.get("/history")
async def get_scan_history(limit: int = 50):
    return sorted(IN_MEMORY_SCAN_DB, key=lambda x: x["timestamp"], reverse=True)[:limit]