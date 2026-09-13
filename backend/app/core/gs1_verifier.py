"""
GS1 / Barcode Detection and Verification

Responsibilities:
- Detect barcodes from package images
- Decode EAN-13 / EAN-8 / UPC-A / Code128 where possible
- Validate GTIN check digits
- Identify GS1 India prefix 890
- Return a safe, structured verification result

Important:
A GS1 prefix identifies the GS1 Member Organisation responsible for
the prefix allocation. It does NOT by itself prove physical country
of manufacture/origin.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except Exception as exc:
    pyzbar_decode = None
    PYZBAR_AVAILABLE = False
    logger.warning("pyzbar unavailable: %s", exc)


GS1_PREFIXES = {
    "000-019": "United States / GS1 US",
    "020-029": "Restricted distribution",
    "030-039": "United States / GS1 US",
    "040-049": "Restricted distribution",
    "050-059": "Coupons",
    "060-139": "United States / GS1 US",
    "300-379": "France / GS1 France",
    "380": "Bulgaria",
    "383": "Slovenia",
    "385": "Croatia",
    "387": "Bosnia and Herzegovina",
    "400-440": "Germany",
    "450-459": "Japan",
    "460-469": "Russia",
    "470": "Kyrgyzstan",
    "471": "Taiwan",
    "474": "Estonia",
    "475": "Latvia",
    "476": "Azerbaijan",
    "477": "Lithuania",
    "478": "Uzbekistan",
    "479": "Sri Lanka",
    "480": "Philippines",
    "481": "Belarus",
    "482": "Ukraine",
    "484": "Moldova",
    "485": "Armenia",
    "486": "Georgia",
    "487": "Kazakhstan",
    "488": "Tajikistan",
    "489": "Hong Kong",
    "490-499": "Japan",
    "500-509": "United Kingdom",
    "520": "Greece",
    "528": "Lebanon",
    "529": "Cyprus",
    "530": "Albania",
    "531": "Macedonia",
    "535": "Malta",
    "539": "Ireland",
    "540-549": "Belgium / Luxembourg",
    "560": "Portugal",
    "569": "Iceland",
    "570-579": "Denmark",
    "590": "Poland",
    "594": "Romania",
    "599": "Hungary",
    "600-601": "South Africa",
    "603": "Ghana",
    "608": "Bahrain",
    "609": "Mauritius",
    "611": "Morocco",
    "613": "Algeria",
    "615": "Nigeria",
    "616": "Kenya",
    "617": "Cameroon",
    "618": "Ivory Coast",
    "619": "Tunisia",
    "620": "Tanzania",
    "621": "Syria",
    "622": "Egypt",
    "623": "Brunei",
    "624": "Libya",
    "625": "Jordan",
    "626": "Iran",
    "627": "Kuwait",
    "628": "Saudi Arabia",
    "629": "United Arab Emirates",
    "630": "Qatar",
    "631": "Namibia",
    "640-649": "Finland",
    "690-699": "China",
    "700-709": "Norway",
    "729": "Israel",
    "730-739": "Sweden",
    "740": "Guatemala",
    "741": "El Salvador",
    "742": "Honduras",
    "743": "Nicaragua",
    "744": "Costa Rica",
    "745": "Panama",
    "746": "Dominican Republic",
    "750": "Mexico",
    "754-755": "Canada",
    "759": "Venezuela",
    "760-769": "Switzerland",
    "770": "Colombia",
    "773": "Uruguay",
    "775": "Peru",
    "777": "Bolivia",
    "778-779": "Argentina",
    "780": "Chile",
    "784": "Paraguay",
    "786": "Ecuador",
    "789-790": "Brazil",
    "800-839": "Italy",
    "840-849": "Spain",
    "850": "Cuba",
    "858": "Slovakia",
    "859": "Czech Republic",
    "860": "Serbia",
    "865": "Mongolia",
    "867": "North Korea",
    "868-869": "Turkey",
    "870-879": "Netherlands",
    "880-881": "South Korea",
    "883": "Myanmar",
    "884": "Cambodia",
    "885": "Thailand",
    "888": "Singapore",
    "890": "India / GS1 India",
    "893": "Vietnam",
    "896": "Pakistan",
    "899": "Indonesia",
    "900-919": "Austria",
    "930-939": "Australia",
    "940-949": "New Zealand",
    "955": "Malaysia",
    "958": "Macau",
}


def _clean_digits(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\D", "", str(value))


def _gtin_check_digit_valid(code: str) -> bool:
    """
    Validate GTIN-8, GTIN-12, GTIN-13 or GTIN-14.
    """

    digits = _clean_digits(code)

    if len(digits) not in (8, 12, 13, 14):
        return False

    try:
        check_digit = int(digits[-1])
        body = digits[:-1]

        total = 0

        # Starting from the right side of the body:
        # 3, 1, 3, 1...
        multiplier = 3

        for digit in reversed(body):
            total += int(digit) * multiplier
            multiplier = 1 if multiplier == 3 else 3

        calculated = (10 - (total % 10)) % 10

        return calculated == check_digit

    except (ValueError, TypeError):
        return False


def _normalise_gtin(code: str) -> str:
    """
    Normalise common barcode values to a clean numeric GTIN.
    """

    digits = _clean_digits(code)

    if len(digits) == 14:
        return digits

    if len(digits) in (8, 12, 13):
        return digits

    return digits


def get_gs1_prefix(code: str) -> str:
    """
    Return the first three digits where applicable.
    """

    digits = _clean_digits(code)

    if len(digits) == 12:
        # GTIN-12 has an implied leading zero when represented
        # as a GTIN-14. GS1 prefix therefore starts from 0xx.
        return ("0" + digits)[:3]

    if len(digits) >= 3:
        return digits[:3]

    return ""


def identify_gs1_country(code: str) -> Dict[str, Any]:
    """
    Identify the GS1 Member Organisation based on the GS1 prefix.
    """

    prefix = get_gs1_prefix(code)

    if not prefix:
        return {
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
        }

    # India is the most important project-specific case.
    if prefix == "890":
        return {
            "prefix": "890",
            "country": "India",
            "gs1_member_organisation": "GS1 India",
            "is_gs1_india": True,
        }

    for key, country in GS1_PREFIXES.items():

        if "-" in key:
            start, end = key.split("-")

            try:
                number = int(prefix)
                if int(start) <= number <= int(end):
                    return {
                        "prefix": prefix,
                        "country": country,
                        "gs1_member_organisation": country,
                        "is_gs1_india": False,
                    }
            except ValueError:
                continue

        elif prefix == key:
            return {
                "prefix": prefix,
                "country": country,
                "gs1_member_organisation": country,
                "is_gs1_india": False,
            }

    return {
        "prefix": prefix,
        "country": "Unknown",
        "gs1_member_organisation": "Unknown",
        "is_gs1_india": False,
    }


def _decode_single_image(image: np.ndarray) -> List[Dict[str, Any]]:
    """
    Run pyzbar against one image representation.
    """

    if not PYZBAR_AVAILABLE or image is None:
        return []

    try:
        decoded = pyzbar_decode(image)
    except Exception as exc:
        logger.warning("Barcode decoding failed: %s", exc)
        return []

    results: List[Dict[str, Any]] = []

    for item in decoded:
        try:
            raw = item.data.decode("utf-8", errors="ignore")
        except Exception:
            raw = str(item.data)

        code = _clean_digits(raw)

        if not code:
            continue

        rect = getattr(item, "rect", None)

        bbox = None

        if rect is not None:
            bbox = {
                "x": int(getattr(rect, "left", 0)),
                "y": int(getattr(rect, "top", 0)),
                "width": int(getattr(rect, "width", 0)),
                "height": int(getattr(rect, "height", 0)),
            }

        results.append(
            {
                "raw": raw,
                "code": code,
                "type": getattr(item, "type", "UNKNOWN"),
                "bbox": bbox,
            }
        )

    return results


def _prepare_variants(image: np.ndarray) -> List[np.ndarray]:
    """
    Create multiple image variants because package photographs often
    contain low contrast, perspective, glare, or small barcodes.
    """

    variants: List[np.ndarray] = []

    if image is None:
        return variants

    variants.append(image)

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        variants.append(gray)

        # Upscale for small package barcodes.
        enlarged = cv2.resize(
            gray,
            None,
            fx=2.0,
            fy=2.0,
            interpolation=cv2.INTER_CUBIC,
        )
        variants.append(enlarged)

        # CLAHE improves local contrast.
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8),
        )
        enhanced = clahe.apply(gray)
        variants.append(enhanced)

        # Adaptive threshold.
        adaptive = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5,
        )
        variants.append(adaptive)

        # Otsu threshold.
        _, otsu = cv2.threshold(
            enhanced,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        variants.append(otsu)

    except Exception as exc:
        logger.warning("Unable to prepare barcode variants: %s", exc)

    return variants


def detect_barcodes_from_image(
    image: np.ndarray,
) -> List[Dict[str, Any]]:
    """
    Detect barcodes using multiple preprocessing passes.

    Returns unique decoded barcode values.
    """

    if image is None:
        return []

    candidates: List[Dict[str, Any]] = []
    seen = set()

    for variant in _prepare_variants(image):

        for result in _decode_single_image(variant):

            code = result.get("code", "")

            if not code:
                continue

            key = (code, result.get("type", "UNKNOWN"))

            if key in seen:
                continue

            seen.add(key)
            candidates.append(result)

    return candidates


def verify_barcode_value(
    code: str,
    barcode_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify a decoded barcode value.
    """

    clean_code = _normalise_gtin(code)

    if not clean_code:

        return {
            "detected": False,
            "code": "N/A",
            "format": barcode_type or "UNKNOWN",
            "valid_gtin": False,
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT_VERIFIABLE",
            "reason": "No numeric barcode value was decoded.",
        }

    valid = _gtin_check_digit_valid(clean_code)

    gs1 = identify_gs1_country(clean_code)

    if gs1["is_gs1_india"]:
        origin_status = "GS1_INDIA_PREFIX"
    elif gs1["country"] != "Unknown":
        origin_status = "GS1_PREFIX_IDENTIFIED"
    else:
        origin_status = "PREFIX_UNKNOWN"

    return {
        "detected": True,
        "code": clean_code,
        "format": barcode_type or "UNKNOWN",
        "valid_gtin": valid,
        "prefix": gs1.get("prefix", ""),
        "country": gs1.get("country", "Unknown"),
        "gs1_member_organisation": gs1.get(
            "gs1_member_organisation",
            "Unknown",
        ),
        "is_gs1_india": bool(
            gs1.get("is_gs1_india", False)
        ),
        "origin_verified": origin_status,
    }


def verify_barcode_from_image(
    image: np.ndarray,
) -> Dict[str, Any]:
    """
    Main entry point.

    Detect a barcode and return the best verification result.
    """

    if image is None:

        return {
            "detected": False,
            "code": "N/A",
            "format": "UNKNOWN",
            "valid_gtin": False,
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT_VERIFIABLE",
            "reason": "Image was not provided.",
        }

    if not PYZBAR_AVAILABLE:

        return {
            "detected": False,
            "code": "N/A",
            "format": "UNKNOWN",
            "valid_gtin": False,
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT_VERIFIABLE",
            "reason": "Barcode decoder is unavailable.",
        }

    candidates = detect_barcodes_from_image(image)

    if not candidates:

        return {
            "detected": False,
            "code": "N/A",
            "format": "UNKNOWN",
            "valid_gtin": False,
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT_VERIFIABLE",
            "reason": "No supported barcode could be decoded from the submitted image.",
        }

    verified_results = []

    for candidate in candidates:

        result = verify_barcode_value(
            candidate["code"],
            candidate.get("type"),
        )

        result["bbox"] = candidate.get("bbox")

        verified_results.append(result)

    # Prefer:
    # 1. Valid EAN/GTIN
    # 2. GS1 India
    # 3. Any detected barcode
    verified_results.sort(
        key=lambda x: (
            bool(x.get("valid_gtin")),
            bool(x.get("is_gs1_india")),
            bool(x.get("detected")),
        ),
        reverse=True,
    )

    return verified_results[0]


def verify_barcode_bytes(
    image_bytes: bytes,
) -> Dict[str, Any]:
    """
    Convenience function for uploaded image bytes.
    """

    if not image_bytes:
        return verify_barcode_from_image(None)

    try:
        buffer = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )

        image = cv2.imdecode(
            buffer,
            cv2.IMREAD_COLOR,
        )

        if image is None:
            return {
                "detected": False,
                "code": "N/A",
                "format": "UNKNOWN",
                "valid_gtin": False,
                "prefix": "",
                "country": "Unknown",
                "is_gs1_india": False,
                "origin_verified": "NOT_VERIFIABLE",
                "reason": "Uploaded image could not be decoded.",
            }

        return verify_barcode_from_image(image)

    except Exception as exc:

        logger.exception(
            "Barcode image processing failed"
        )

        return {
            "detected": False,
            "code": "N/A",
            "format": "UNKNOWN",
            "valid_gtin": False,
            "prefix": "",
            "country": "Unknown",
            "is_gs1_india": False,
            "origin_verified": "NOT_VERIFIABLE",
            "reason": str(exc),
        }


__all__ = [
    "detect_barcodes_from_image",
    "verify_barcode_from_image",
    "verify_barcode_from_bytes",
    "verify_barcode_bytes",
    "verify_barcode_value",
    "identify_gs1_country",
    "get_gs1_prefix",
]