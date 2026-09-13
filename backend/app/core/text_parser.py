from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageEnhance
from google import genai
from google.genai import types

from app.core.feedback_store import (
    get_few_shot_guidance,
)


logger = logging.getLogger(__name__)


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

raw_keys = (
    os.getenv("GEMINI_API_KEYS")
    or os.getenv("GEMINI_API_KEY")
    or ""
)

KEY_POOL: List[str] = [
    key.strip()
    for key in re.split(
        r"[,\n\r]+",
        raw_keys,
    )
    if key.strip()
]


def _parse_models() -> List[str]:

    configured = os.getenv(
        "GEMINI_MODELS",
        "",
    )

    if configured.strip():

        models = [
            model.strip()
            for model in re.split(
                r"[,\n\r]+",
                configured,
            )
            if model.strip()
        ]

        if models:
            return models

    return [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
    ]


MODELS_TO_TRY = _parse_models()

logger.info(
    "[*] Initialized Gemini client pool "
    "with %d key(s).",
    len(KEY_POOL),
)

_current_key_idx = 0


def get_next_client():

    global _current_key_idx

    if not KEY_POOL:

        raise ValueError(
            "No valid Gemini API keys configured."
        )

    key = KEY_POOL[
        _current_key_idx
        % len(KEY_POOL)
    ]

    _current_key_idx = (
        _current_key_idx + 1
    ) % len(KEY_POOL)

    client = genai.Client(
        api_key=key,
        http_options={
            "api_version": "v1beta",
            "timeout": 60000,
        },
    )

    return client, key


# ============================================================================
# IMAGE PREPROCESSING
# ============================================================================

def preprocess_image(
    image_bytes: bytes,
) -> bytes:

    try:

        image = Image.open(
            io.BytesIO(
                image_bytes
            )
        ).convert("RGB")

        max_dim = 1400

        width, height = image.size

        if max(
            width,
            height,
        ) > max_dim:

            scale = (
                max_dim
                / max(
                    width,
                    height,
                )
            )

            image = image.resize(
                (
                    int(width * scale),
                    int(height * scale),
                ),
                Image.Resampling.LANCZOS,
            )

        image = ImageEnhance.Contrast(
            image
        ).enhance(1.10)

        output = io.BytesIO()

        image.save(
            output,
            format="JPEG",
            quality=82,
            optimize=True,
        )

        return output.getvalue()

    except Exception as exc:

        logger.warning(
            "Image preprocessing fallback: %s",
            exc,
        )

        return image_bytes


# ============================================================================
# JSON PARSER
# ============================================================================

def clean_and_parse_json(
    raw_text: str,
) -> dict:

    if not raw_text:
        raise ValueError(
            "Empty response from Gemini."
        )

    text = raw_text.strip()

    if "```" in text:

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        text = text.strip()

    try:

        result = json.loads(
            text
        )

        if not isinstance(
            result,
            dict,
        ):
            raise ValueError(
                "Gemini response is not a JSON object."
            )

        return result

    except Exception:
        pass

    match = re.search(
        r"\{[\s\S]*\}",
        text,
    )

    if match:

        result = json.loads(
            match.group(0)
        )

        if not isinstance(
            result,
            dict,
        ):
            raise ValueError(
                "Extracted JSON is not an object."
            )

        return result

    raise ValueError(
        "No valid JSON object found "
        "in Gemini response."
    )


# ============================================================================
# CONSUMER CARE
# ============================================================================

def audit_consumer_care_details(
    text_corpus: str,
) -> dict:

    text = (
        text_corpus
        if isinstance(
            text_corpus,
            str,
        )
        else str(text_corpus)
    )

    email_match = re.search(
        r"[a-zA-Z0-9._%+-]+"
        r"@[a-zA-Z0-9.-]+\."
        r"[a-zA-Z]{2,}",
        text,
    )

    phone_match = re.search(
        r"(?:"
        r"1800[\s-]*\d{3}[\s-]*\d{3,4}"
        r"|"
        r"(?:\+91[\s-]*)?"
        r"[6-9]\d{9}"
        r")",
        text,
        flags=re.IGNORECASE,
    )

    lower = text.lower()

    # Look for an actual person/designation signal.
    designation_patterns = [
        r"\bmanager\b",
        r"\bofficer\b",
        r"\bexecutive\b",
        r"\bgrievance\s+officer\b",
        r"\bconsumer\s+care\s+officer\b",
        r"\bcustomer\s+care\s+officer\b",
        r"\bnodal\s+officer\b",
        r"\bcontact\s+person\b",
    ]

    has_person = any(
        re.search(
            pattern,
            lower,
        )
        for pattern in designation_patterns
    )

    result = {
        "has_care_email":
            bool(email_match),

        "extracted_email":
            (
                email_match.group(0)
                if email_match
                else "MISSING"
            ),

        "has_care_phone":
            bool(phone_match),

        "extracted_phone":
            (
                phone_match.group(0)
                if phone_match
                else "MISSING"
            ),

        "has_person_or_designation":
            has_person,

        "is_fully_compliant":
            bool(
                email_match
                and phone_match
                and has_person
            ),
    }

    return result


# ============================================================================
# RULE 7 FONT MATRIX
# ============================================================================

def compute_rule_7_font_requirements(
    pdp_area_cm2: float,
) -> float:

    area = float(
        pdp_area_cm2
    )

    if area <= 50:
        return 1.0

    if area <= 100:
        return 1.5

    if area <= 500:
        return 2.5

    if area <= 2500:
        return 4.0

    return 6.0


# ============================================================================
# USP VERIFICATION
# ============================================================================

def _parse_money(
    value: str,
) -> Optional[float]:

    if not value:
        return None

    match = re.search(
        r"\d+(?:\.\d+)?",
        str(value).replace(
            ",",
            "",
        ),
    )

    if not match:
        return None

    return float(
        match.group(0)
    )


def _parse_quantity(
    value: str,
) -> Tuple[
    Optional[float],
    Optional[str],
]:

    if not value:
        return None, None

    text = str(
        value
    ).lower().strip()

    number_match = re.search(
        r"\d+(?:\.\d+)?",
        text,
    )

    if not number_match:
        return None, None

    quantity = float(
        number_match.group(0)
    )

    unit_match = re.search(
        r"\b("
        r"kg|g|mg|"
        r"litre|liter|litres|liters|l|ml|"
        r"metre|meter|m|"
        r"piece|pieces|unit|units"
        r")\b",
        text,
    )

    unit = (
        unit_match.group(1).lower()
        if unit_match
        else None
    )

    return quantity, unit


def verify_usp_math(
    mrp_str: str,
    qty_str: str,
    declared_usp: str,
) -> Tuple[
    bool,
    str,
]:

    mrp_value = _parse_money(
        mrp_str
    )

    quantity, unit = (
        _parse_quantity(
            qty_str
        )
    )

    if (
        mrp_value is None
        or quantity is None
        or quantity <= 0
    ):

        return (
            False,
            declared_usp
            if declared_usp
            else "MISSING",
        )

    if _is_missing_usp(
        declared_usp
    ):

        expected = _calculate_expected_usp(
            mrp_value,
            quantity,
            unit,
        )

        return (
            False,
            expected,
        )

    declared_value = _parse_money(
        declared_usp
    )

    if declared_value is None:

        expected = _calculate_expected_usp(
            mrp_value,
            quantity,
            unit,
        )

        return (
            False,
            expected,
        )

    expected_raw = (
        mrp_value
        / quantity
    )

    expected_rounded = round(
        expected_raw,
        2,
    )

    verified = (
        abs(
            declared_value
            - expected_rounded
        )
        < 0.005
    )

    expected = _calculate_expected_usp(
        mrp_value,
        quantity,
        unit,
    )

    return (
        verified,
        expected,
    )


def _is_missing_usp(
    value: Any,
) -> bool:

    if value is None:
        return True

    if not isinstance(
        value,
        str,
    ):
        return False

    return value.strip().upper() in {
        "",
        "MISSING",
        "N/A",
        "NA",
        "UNKNOWN",
    }


def _calculate_expected_usp(
    mrp_value: float,
    quantity: float,
    unit: Optional[str],
) -> str:

    expected = round(
        mrp_value
        / quantity,
        2,
    )

    display_unit = (
        unit
        if unit
        else "unit"
    )

    return (
        f"₹ {expected:.2f} "
        f"per {display_unit}"
    )


# ============================================================================
# BARCODE
# ============================================================================

def _gtin_check_digit_valid(code: str) -> bool:
    digits = re.sub(r"\D", "", str(code or ""))
    if len(digits) not in (8, 12, 13, 14):
        return False
    total = 0
    for i, ch in enumerate(reversed(digits[:-1])):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - (total % 10)) % 10 == int(digits[-1])


def _gs1_prefix_info(code: str) -> Tuple[str, bool]:
    digits = re.sub(r"\D", "", str(code or ""))
    prefix = digits[:3]
    if prefix == "890":
        return "India (GS1 India)", True
    # Common GS1 member prefixes; unknown ranges are deliberately not guessed.
    ranges = {
        "000-019": "United States / Canada", "030-039": "United States",
        "060-139": "United States / Canada", "300-379": "France",
        "400-440": "Germany", "450-459": "Japan", "490-499": "Japan",
        "500-509": "United Kingdom", "690-699": "China",
        "700-709": "Norway", "730-739": "Sweden", "760-769": "Switzerland",
        "800-839": "Italy", "840-849": "Spain", "870-879": "Netherlands",
        "880": "South Korea", "900-919": "Austria", "930-939": "Australia",
        "940-949": "New Zealand", "955": "Malaysia", "958": "Macau",
    }
    try:
        n = int(prefix)
        for key, country in ranges.items():
            a, b = (int(x) for x in key.split("-")) if "-" in key else (int(key), int(key))
            if a <= n <= b:
                return country, False
    except ValueError:
        pass
    return "Unknown", False


def _normalize_barcode(value: Any) -> Optional[str]:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) in (8, 12, 13, 14) and _gtin_check_digit_valid(digits):
        return digits
    return None


def extract_barcode_info(image_bytes: bytes) -> dict:
    """Decode package barcodes without changing the Gemini extraction pipeline."""
    result = {
        "detected": False, "code": "N/A", "country": "Unknown",
        "is_gs1_india": False, "origin_verified": "NOT ASSESSED",
    }
    if not image_bytes:
        return result

    candidates: List[str] = []
    try:
        import cv2
        import numpy as np
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is not None:
            detector = getattr(cv2, "barcode", None)
            if detector is not None and hasattr(detector, "BarcodeDetector"):
                bd = detector.BarcodeDetector()
                try:
                    ok, decoded, _points = bd.detectAndDecode(image)
                    if ok and decoded:
                        vals = decoded if isinstance(decoded, (list, tuple)) else [decoded]
                        candidates.extend(str(x) for x in vals if x)
                except Exception as exc:
                    logger.debug("OpenCV barcode decode failed: %s", exc)
            # Try rotated/upscaled image as a second pass.
            if not candidates and hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector"):
                try:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    bd = cv2.barcode.BarcodeDetector()
                    ok, decoded, _points = bd.detectAndDecode(gray)
                    if ok and decoded:
                        vals = decoded if isinstance(decoded, (list, tuple)) else [decoded]
                        candidates.extend(str(x) for x in vals if x)
                except Exception as exc:
                    logger.debug("OpenCV enhanced barcode decode failed: %s", exc)
    except Exception as exc:
        logger.debug("OpenCV barcode decoder unavailable: %s", exc)

    # pyzbar is a stronger fallback for EAN/UPC when native zbar is installed.
    if not candidates:
        try:
            from pyzbar.pyzbar import decode
            import cv2
            import numpy as np
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is not None:
                variants = [image, cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)]
                for variant in variants:
                    for item in decode(variant):
                        data = item.data.decode("utf-8", errors="ignore")
                        if data:
                            candidates.append(data)
                    if candidates:
                        break
        except Exception as exc:
            logger.debug("pyzbar barcode decoder unavailable/failed: %s", exc)

    for candidate in candidates:
        code = _normalize_barcode(candidate)
        if not code:
            continue
        country, is_india = _gs1_prefix_info(code)
        return {
            "detected": True, "code": code, "country": country,
            "is_gs1_india": is_india,
            "origin_verified": "MATCH" if is_india else "DETECTED",
        }

    return result


# ============================================================================
# DEFAULT EXTRACTION SCHEMA
# ============================================================================

def _default_schema() -> dict:

    return {
        "brand_name": "MISSING",
        "commodity_name": "MISSING",
        "net_quantity": "MISSING",
        "mrp": "MISSING",
        "has_tax_clause": False,
        "unit_sale_price": "MISSING",
        "mfg_date": "MISSING",
        "expiry_date": "MISSING",
        "batch_number": "MISSING",
        "country_of_origin": "MISSING",
        "fssai_license": "MISSING",
        "consumer_care_raw_text": "MISSING",
        "font_height_mm_estimate": None,
        "bounding_boxes": {},
    }


# ============================================================================
# GEMINI EXTRACTION
# ============================================================================

async def extract_declarations_with_boxes(
    image_bytes: bytes,
    surface_type: str = "front",
) -> dict:

    if not image_bytes:

        return {
            "_meta": {
                "status": "unavailable",
                "error": "Empty image bytes.",
            }
        }

    optimized_bytes = (
        preprocess_image(
            image_bytes
        )
    )

    guidance_context = (
        get_few_shot_guidance()
    )

    prompt = f"""
You are an India-specific Legal Metrology
packaged-commodity inspection assistant.

Analyze the supplied {surface_type} package image.

Extract ONLY information that is visibly present
or reasonably readable from the package.

Do NOT invent values.

If a field cannot be read, return "MISSING".

If country of origin is not visibly declared,
return "MISSING". Do not assume India.

Return ONLY valid JSON.

Required schema:

{{
  "brand_name": "string or MISSING",
  "commodity_name": "string or MISSING",
  "net_quantity": "string or MISSING",
  "mrp": "string or MISSING",
  "has_tax_clause": true,
  "unit_sale_price": "string or MISSING",
  "mfg_date": "string or MISSING",
  "expiry_date": "string or MISSING",
  "batch_number": "string or MISSING",
  "country_of_origin": "string or MISSING",
  "fssai_license": "string or MISSING",
  "consumer_care_raw_text": "string or MISSING",
  "font_height_mm_estimate": null,
  "bounding_boxes": {{
    "brand_name": [0,0,0,0],
    "commodity_name": [0,0,0,0],
    "net_quantity": [0,0,0,0],
    "mrp": [0,0,0,0],
    "mfg_date": [0,0,0,0],
    "expiry_date": [0,0,0,0],
    "batch_number": [0,0,0,0],
    "fssai_license": [0,0,0,0]
  }}
}}

Rules:

1. Do not infer missing declarations.
2. Do not fabricate dates.
3. Do not fabricate FSSAI numbers.
4. Do not fabricate MRP.
5. Do not fabricate USP.
6. Preserve units exactly where possible.
7. Detect consumer-care text including phone,
   email and officer/designation information.
8. Include bounding boxes when reasonably available.
9. Return valid JSON only.

Additional project guidance:

{guidance_context}
"""

    if not KEY_POOL:

        logger.error(
            "No Gemini API key configured."
        )

        return {
            "_meta": {
                "status": "unavailable",
                "error": (
                    "No Gemini API key configured."
                ),
            }
        }

    # ------------------------------------------------------------------------
    # MODEL + KEY FALLBACK
    # ------------------------------------------------------------------------

    last_error: Optional[
        str
    ] = None

    for model_name in MODELS_TO_TRY:

        for key_attempt in range(
            len(KEY_POOL)
        ):

            try:

                client, full_key = (
                    get_next_client()
                )

                # Never log the actual key.
                key_prefix = (
                    full_key[:4]
                    + "..."
                )

                logger.info(
                    "[*] Calling Gemini (%s) with key %s",
                    model_name,
                    key_prefix,
                )

                loop = (
                    asyncio.get_running_loop()
                )

                def _call_model():

                    return (
                        client.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Part.from_bytes(
                                    data=optimized_bytes,
                                    mime_type="image/jpeg",
                                ),
                                prompt,
                            ],
                            config=types.GenerateContentConfig(
                                temperature=0.0,
                                response_mime_type=(
                                    "application/json"
                                ),
                            ),
                        )
                    )

                response = (
                    await loop.run_in_executor(
                        None,
                        _call_model,
                    )
                )

                raw_text = getattr(
                    response,
                    "text",
                    None,
                )

                parsed = (
                    clean_and_parse_json(
                        raw_text
                    )
                )

                # Add metadata for downstream processing.
                parsed["_meta"] = {
                    "status": "success",
                    "model": model_name,
                    "surface_type":
                        surface_type,
                }

                logger.info(
                    "[✓] Extracted declarations using %s",
                    model_name,
                )

                return parsed

            except Exception as exc:

                last_error = str(
                    exc
                )

                logger.warning(
                    "[!] %s extraction error: %s",
                    model_name,
                    exc,
                )

                continue

    logger.error(
        "[!] All Gemini models and keys exhausted."
    )

    return {
        "_meta": {
            "status": "unavailable",
            "error": last_error
            or "All Gemini extraction attempts failed.",
        }
    }


# ============================================================================
# COMPATIBILITY WRAPPERS
# ============================================================================

async def extract_declarations(
    image_bytes: bytes,
) -> dict:

    return await (
        extract_declarations_with_boxes(
            image_bytes,
            surface_type="front",
        )
    )


class StatutoryTextParser:

    async def extract_declarations(
        self,
        image_bytes: bytes,
    ) -> dict:

        return await (
            extract_declarations_with_boxes(
                image_bytes,
                surface_type="front",
            )
        )


class TextParser(
    StatutoryTextParser
):
    pass


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "extract_declarations",
    "extract_declarations_with_boxes",
    "extract_barcode_info",
    "audit_consumer_care_details",
    "compute_rule_7_font_requirements",
    "verify_usp_math",
    "StatutoryTextParser",
    "TextParser",
]