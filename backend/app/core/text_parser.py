import os
import io
import re
import json
import asyncio
import logging
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageEnhance
from google import genai
from google.genai import types
from app.core.feedback_store import get_few_shot_guidance

logger = logging.getLogger(__name__)

raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
KEY_POOL: List[str] = [k.strip() for k in raw_keys.replace("\n", "").replace("\r", "").split(",") if k.strip()]

logger.info(f"[*] Initialized Gemini client pool with {len(KEY_POOL)} key(s).")

_current_key_idx = 0

def get_next_client():
    global _current_key_idx
    if not KEY_POOL:
        raise ValueError("No valid Gemini API keys configured.")
    key = KEY_POOL[_current_key_idx % len(KEY_POOL)]
    _current_key_idx = (_current_key_idx + 1) % len(KEY_POOL)
    client = genai.Client(api_key=key, http_options={"api_version": "v1beta", "timeout": 60000})
    return client, key

MODELS_TO_TRY = [
    "gemini-3.7-flash",
    "gemini-3.6-flash"
]

def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        max_dim = 1100
        w, h = image.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.15)
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=75, optimize=True)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"Preprocessing fallback: {e}")
        return image_bytes

def clean_and_parse_json(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response text from model.")
    text = raw_text.strip()
    if "```" in text:
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        return json.loads(match.group(1))
    raise ValueError("No valid JSON structure found.")

def audit_consumer_care_details(text_corpus: str) -> dict:
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text_corpus)
    phone_match = re.search(r"(?:(?:\+|0{0,2})91(\s*[-]\s*)?|[0]?)?[6789]\d{9}|1800\s*\d{3}\s*\d{3,4}", text_corpus)
    has_person = any(kw in text_corpus.lower() for kw in ["manager", "officer", "executive", "grievance", "consumer care cell", "customer care"])
    return {
        "has_care_email": bool(email_match),
        "extracted_email": email_match.group(0) if email_match else "MISSING",
        "has_care_phone": bool(phone_match),
        "extracted_phone": phone_match.group(0) if phone_match else "MISSING",
        "has_person_or_designation": has_person,
        "is_fully_compliant": bool(email_match and phone_match and has_person)
    }

def compute_rule_7_font_requirements(pdp_area_cm2: float) -> float:
    if pdp_area_cm2 <= 50: return 1.0
    elif pdp_area_cm2 <= 100: return 1.5
    elif pdp_area_cm2 <= 500: return 2.5
    elif pdp_area_cm2 <= 2500: return 4.0
    else: return 6.0

def verify_usp_math(mrp_str: str, qty_str: str, declared_usp: str) -> Tuple[bool, str]:
    try:
        mrp_val = float(re.sub(r"[^\d.]", "", mrp_str))
        qty_val = float(re.sub(r"[^\d.]", "", qty_str))
        if mrp_val > 0 and qty_val > 0:
            expected_usp = mrp_val / qty_val
            unit_match = re.search(r"(g|kg|ml|l|m|piece|units?)", qty_str, re.I)
            unit = unit_match.group(1).lower() if unit_match else "unit"
            return True, f"₹ {expected_usp:.2f} per {unit}"
    except Exception:
        pass
    return False, declared_usp

def extract_barcode_info(image_bytes: bytes) -> dict:
    return {"detected": False, "code": "N/A", "country": "Unknown", "is_gs1_india": False}

async def extract_declarations_with_boxes(image_bytes: bytes, surface_type: str = "front") -> dict:
    if not image_bytes:
        return {}

    optimized_bytes = preprocess_image(image_bytes)
    guidance_context = get_few_shot_guidance()

    prompt = f"""
You are a Legal Metrology compliance verification auditor in India ({surface_type} packaging view).
Extract statutory parameters strictly under Rule 6 and Rule 7 of the Legal Metrology (Packaged Commodities) Rules, 2011.
Return ONLY a valid JSON object without conversational text.

Schema:
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
  "country_of_origin": "India",
  "fssai_license": "string or MISSING",
  "consumer_care_raw_text": "string or MISSING",
  "font_height_mm_estimate": 2.5,
  "bounding_boxes": {{
    "brand_name": [0, 0, 0, 0],
    "net_quantity": [0, 0, 0, 0],
    "mrp": [0, 0, 0, 0],
    "mfg_date": [0, 0, 0, 0],
    "batch_number": [0, 0, 0, 0],
    "fssai_license": [0, 0, 0, 0]
  }}
}}
{guidance_context}
"""

    for model_name in MODELS_TO_TRY:
        if not KEY_POOL:
            break
        for _ in range(len(KEY_POOL)):
            client, full_key = get_next_client()
            key_prefix = full_key[:8] + "..."
            try:
                logger.info(f"[*] Calling Gemini ({model_name}) with key {key_prefix}...")
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=optimized_bytes, mime_type="image/jpeg"),
                            prompt
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.0,
                            response_mime_type="application/json"
                        )
                    )
                )

                parsed_data = clean_and_parse_json(res.text)
                logger.info(f"[✓] Extracted declarations using {model_name}")
                return parsed_data

            except Exception as e:
                logger.warning(f"[!] {model_name} error: {e}")
                continue

    logger.error("[!] All Gemini models and keys exhausted.")
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
        "country_of_origin": "India",
        "fssai_license": "MISSING",
        "consumer_care_raw_text": "MISSING",
        "font_height_mm_estimate": 0.0,
        "bounding_boxes": {}
    }

async def extract_declarations(image_bytes: bytes) -> dict:
    return await extract_declarations_with_boxes(image_bytes, "front")

class StatutoryTextParser:
    async def extract_declarations(self, image_bytes: bytes) -> dict:
        return await extract_declarations_with_boxes(image_bytes)

class TextParser(StatutoryTextParser):
    pass

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