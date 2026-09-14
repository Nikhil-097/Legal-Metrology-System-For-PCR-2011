import json
import os
from typing import List, Dict, Any

FEEDBACK_FILE = "data/compliance_corrections.json"

def _ensure_store():
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)

def record_correction(brand_name: str, corrected_fields: Dict[str, Any], raw_mistake: Dict[str, Any] = None):
    _ensure_store()
    try:
        with open(FEEDBACK_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = []

    correction_entry = {
        "brand_name": brand_name,
        "corrected_fields": corrected_fields,
        "previous_mistake": raw_mistake or {}
    }
    data.append(correction_entry)

    # Keep the most recent 50 high-value lessons to stay within token context limits
    if len(data) > 50:
        data = data[-50:]

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_few_shot_guidance() -> str:
    _ensure_store()
    try:
        with open(FEEDBACK_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return ""

    if not data:
        return ""

    guidance = "\n\nCRITICAL HISTORICAL LESSONS & PREVIOUS OCR CORRECTIONS (Do not repeat these prior mistakes):\n"
    for item in data[-5:]:
        guidance += f"- For brand '{item.get('brand_name', 'General')}': The verified accurate statutory parameters are: {json.dumps(item.get('corrected_fields'))}. Avoid previous misclassifications.\n"
    return guidance