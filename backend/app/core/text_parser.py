import os
import re
import json
import cv2
import tempfile
import uuid
import traceback
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def _clean_val(val: Any) -> str:
    if val is None:
        return "MISSING"
    if isinstance(val, bool):
        return val
    text = str(val).strip()
    if not text or text.lower() in ["none", "null", "n/a", "na", "missing", "nil", "unknown", ""]:
        return "MISSING"
    cleaned = re.sub(r"^(?:e\.g\.?|eg\.?|example:?|value:?)\s*", "", text, flags=re.IGNORECASE)
    return cleaned.strip("\"' `") or "MISSING"


def _extract_json_dict(text: str) -> Dict[str, Any]:
    """Extracts valid JSON dictionary from raw model text output."""
    if not text:
        return {}
    
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


class StatutoryTextParser:

    @classmethod
    def _prepare_optimized_image(cls, image_path: str) -> str:
        img = cv2.imread(image_path)
        if img is None:
            return image_path

        h, w = img.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1400:
            scale = 1400.0 / max_dim
            resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            temp_path = os.path.join(tempfile.gettempdir(), f"vlm_opt_{uuid.uuid4().hex}.jpg")
            cv2.imwrite(temp_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 88])
            return temp_path
        return image_path

    @classmethod
    def parse_with_gemini(cls, image_path: str) -> Optional[Dict[str, Any]]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not HAS_GEMINI or not api_key:
            print("[!] GEMINI_API_KEY missing or google-genai library not installed.")
            return None

        prompt = (
            "You are a strict Legal Metrology (Packaged Commodities) Rules compliance auditor.\n"
            "Analyze this packaging image carefully across all visible panels, stickers, and inkjet markings.\n"
            "Extract every statutory declaration into a complete JSON object with these exact keys:\n"
            "{\n"
            '  "brand_name": "extracted brand name or MISSING",\n'
            '  "commodity_name": "extracted commodity/product identity name or MISSING",\n'
            '  "net_quantity": "extracted net quantity with unit (e.g. 75 g) or MISSING",\n'
            '  "mrp": "extracted MRP with symbol (e.g. ₹ 10.00) or MISSING",\n'
            '  "has_tax_clause": true if taxes included phrase is visible else false,\n'
            '  "unit_sale_price": "extracted USP (e.g. Rs.0.13 Per g) or MISSING",\n'
            '  "mfg_date": "extracted Mfd/Pkd date (e.g. 07/02/26) or MISSING",\n'
            '  "expiry_date": "extracted Use By/Exp date (e.g. 06/02/28) or MISSING",\n'
            '  "batch_number": "extracted batch number (e.g. G76B07C) or MISSING",\n'
            '  "fssai_license": "extracted FSSAI number or MISSING",\n'
            '  "country_of_origin": "India or country name"\n'
            "}\n"
            "Ensure the entire JSON is complete and valid."
        )

        opt_path = cls._prepare_optimized_image(image_path)

        try:
            client = genai.Client(api_key=api_key)
            with open(opt_path, "rb") as f:
                img_bytes = f.read()

            part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[part, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                    max_output_tokens=2048,
                ),
            )

            raw_text = ""
            if hasattr(response, "text") and response.text:
                raw_text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    raw_text = "".join([p.text for p in candidate.content.parts if hasattr(p, "text")])

            data = _extract_json_dict(raw_text)

            if data:
                print(">>> [✓] Declarations parsed successfully via Gemini 3.6 Flash!")
                return {
                    "brand_name": _clean_val(data.get("brand_name")),
                    "commodity_name": _clean_val(data.get("commodity_name")),
                    "net_quantity": _clean_val(data.get("net_quantity")),
                    "mrp": _clean_val(data.get("mrp")),
                    "has_tax_clause": bool(data.get("has_tax_clause", False)),
                    "unit_sale_price": _clean_val(data.get("unit_sale_price")),
                    "mfg_date": _clean_val(data.get("mfg_date")),
                    "expiry_date": _clean_val(data.get("expiry_date")),
                    "batch_number": _clean_val(data.get("batch_number")),
                    "fssai_license": _clean_val(data.get("fssai_license")),
                    "country_of_origin": _clean_val(data.get("country_of_origin")) or "India",
                }
            else:
                print(f"[!] Unable to decode JSON from Gemini output: {raw_text}")

        except Exception as e:
            print(f"[!] Gemini Extraction Error: {e}")
            traceback.print_exc()
        finally:
            if opt_path != image_path and os.path.exists(opt_path):
                try:
                    os.remove(opt_path)
                except OSError:
                    pass

        return None

    @classmethod
    def parse_all_declarations(cls, tokens: List[Dict[str, Any]] = None, image_path: str = None) -> Dict[str, Any]:
        if image_path and os.path.exists(image_path):
            gemini_res = cls.parse_with_gemini(image_path)
            if gemini_res:
                return gemini_res

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
            "fssai_license": "MISSING",
            "country_of_origin": "India",
        }


TextParser = StatutoryTextParser