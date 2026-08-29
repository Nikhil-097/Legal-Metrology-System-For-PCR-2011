import logging
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.text_parser import StatutoryTextParser

logger = logging.getLogger(__name__)


class LegalMetrologyVerifier:
    """Verifies extracted declarations against PCR 2011 statutory rules."""

    def extract_and_verify(
        self,
        tokens: List[Dict[str, Any]],
        pdp_area_cm2: float = 85.0,
        ppm_scale: float = 3.78,
        brand_name: Optional[str] = None,
        commodity_name: Optional[str] = None,
        image: Optional[np.ndarray] = None,
        image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Always run high-precision multimodal parsing first
        declarations = StatutoryTextParser.parse_all_declarations(
            tokens=tokens,
            image_path=image_path,
        )

        violations = []
        score = 100

        # Rule 6(1)(a): Brand / Commodity Name
        b_name = brand_name or declarations.get("brand_name", "MISSING")
        c_name = commodity_name or declarations.get("commodity_name", "MISSING")
        if b_name == "MISSING" and c_name == "MISSING":
            violations.append({
                "rule": "Rule 6(1)(a)",
                "description": "Commodity name or identity not clearly declared on the principal display panel.",
                "severity": "CRITICAL"
            })
            score -= 15

        # Rule 6(1)(b) & Rule 13: Net Quantity
        if declarations.get("net_quantity") == "MISSING":
            violations.append({
                "rule": "Rule 6(1)(b) / Rule 13",
                "description": "Mandatory Net Quantity declaration is missing.",
                "severity": "CRITICAL"
            })
            score -= 30

        # Rule 6(1)(e): Maximum Retail Price (MRP)
        if declarations.get("mrp") == "MISSING":
            violations.append({
                "rule": "Rule 6(1)(e)",
                "description": "Maximum Retail Price (MRP) is absent or illegible.",
                "severity": "CRITICAL"
            })
            score -= 25

        # Rule 6(1)(e): Tax Inclusivity Phrase
        if not declarations.get("has_tax_clause"):
            violations.append({
                "rule": "Rule 6(1)(e)",
                "description": "Mandatory tax inclusivity statement ('inclusive of all taxes') is missing.",
                "severity": "MAJOR"
            })
            score -= 15

        # Rule 6(1)(f): Manufacturing / Packaging Date
        if declarations.get("mfg_date") == "MISSING":
            violations.append({
                "rule": "Rule 6(1)(f)",
                "description": "Date of manufacture or packaging is missing.",
                "severity": "MAJOR"
            })
            score -= 15

        # Rule 6(11): Unit Sale Price (USP)
        if declarations.get("unit_sale_price") == "MISSING":
            violations.append({
                "rule": "Rule 6(11)",
                "description": "Unit Sale Price (USP) declaration is absent.",
                "severity": "MINOR"
            })
            score -= 5

        # Rule 6(1)(d): Country of Origin
        if declarations.get("country_of_origin") == "MISSING":
            violations.append({
                "rule": "Rule 6(1)(d)",
                "description": "Country of origin declaration is missing.",
                "severity": "MAJOR"
            })
            score -= 10

        compliance_score = max(0, score)
        is_compliant = compliance_score >= 80 and len([v for v in violations if v["severity"] == "CRITICAL"]) == 0

        raw_tokens_text = [t.get("text", "") for t in tokens] if tokens else []

        return {
            "compliance_score": compliance_score,
            "is_compliant": is_compliant,
            "violations": violations,
            "extracted_declarations": declarations,
            "raw_text_extracted": raw_tokens_text,
        }