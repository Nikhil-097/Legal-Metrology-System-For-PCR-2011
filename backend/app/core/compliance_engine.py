from __future__ import annotations

from typing import Any, Dict, List

from app.core.compliance_context import ComplianceContext


class ComplianceEngine:
    """
    Deterministic Legal Metrology compliance engine.

    Gemini/OCR is responsible for extracting evidence.
    This engine is responsible for evaluating that evidence
    against the applicable compliance context.

    Important:
    This is an AI-assisted compliance assessment engine.
    It is not a government certification authority.
    """

    MANDATORY_FIELDS = {
        "net_quantity": "Declared Net Quantity (Rule 6(1)(b))",
        "mrp": "Maximum Retail Price (Rule 6(1)(e))",
        "mfg_date": "Date of Packing / Mfg",
        "commodity_name": "Generic Commodity Name",
    }

    ADVISORY_FIELDS = {
        "brand_name": "Brand Name",
        "batch_number": "Batch / Lot Serial Number",
    }

    @staticmethod
    def _missing(value: Any) -> bool:
        """
        Return True when an extracted declaration is missing.
        """
        return value is None or value == "" or value == "MISSING"

    @staticmethod
    def _normalise_declarations(
        declarations: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """
        Ensure declarations is always a dictionary.
        """
        if not isinstance(declarations, dict):
            return {}

        return declarations

    @classmethod
    def evaluate(
        cls,
        *,
        declarations: Dict[str, Any],
        context: ComplianceContext | None = None,
        is_food: bool = False,
        pdp_surface_area: float = 0,
        required_font_height_mm: float = 0,
        detected_font_height_mm: float | None = None,
        consumer_care: Dict[str, Any] | None = None,
        usp_math: Dict[str, Any] | None = None,
        barcode_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Evaluate package declarations using deterministic rules.

        Returns:
            compliance_score
            is_compliant
            status
            violations
            checks
        """

        declarations = cls._normalise_declarations(declarations)
        consumer_care = (
            consumer_care
            if isinstance(consumer_care, dict)
            else {}
        )
        barcode_data = (
            barcode_data
            if isinstance(barcode_data, dict)
            else {}
        )

        # ---------------------------------------------------------
        # DEFAULT CONTEXT
        # ---------------------------------------------------------

        if context is None:
            context = ComplianceContext(
                category="food" if is_food else "general",
                is_wholesale_package=False,
                is_retail_package=True,
                is_imported=False,
                is_food=is_food,
                is_liquid=False,
                net_quantity_value=None,
                net_quantity_unit=None,
                is_perishable_or_consumable=False,
                dimensions_relevant=False,
                consumer_care_required=True,
                unit_sale_price_required=True,
            )

        # ---------------------------------------------------------
        # SCORE / OUTPUT CONTAINERS
        # ---------------------------------------------------------

        score = 100.0

        violations: List[Dict[str, Any]] = []
        checks: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # VIOLATION HELPER
        # ---------------------------------------------------------

        def add_violation(
            *,
            code: str,
            rule: str,
            severity: str,
            description: str,
            remedial_action: str,
            deduction: float,
        ) -> None:
            nonlocal score

            score -= deduction

            violations.append(
                {
                    "rule": rule,
                    "detail": description,
                    "severity": severity,
                    "remedial_action": remedial_action,
                    "code": code,
                }
            )

        # =========================================================
        # 1. RULE 6 MANDATORY DECLARATIONS
        # =========================================================

        for field, rule_description in cls.MANDATORY_FIELDS.items():
            value = declarations.get(field)

            passed = not cls._missing(value)

            checks.append(
                {
                    "check": field,
                    "rule": "Rule 6 Mandatory Declaration",
                    "required": True,
                    "passed": passed,
                    "evidence": (
                        value
                        if value is not None
                        else "MISSING"
                    ),
                }
            )

            if not passed:
                add_violation(
                    code="MANDATORY_DECLARATION_MISSING",
                    rule="Rule 6 Mandatory Declaration",
                    severity="HIGH",
                    description=(
                        f"Mandatory declaration "
                        f"'{rule_description}' is missing "
                        "or unreadable across packaging surfaces."
                    ),
                    remedial_action=(
                        f"Ensure '{rule_description}' is clearly "
                        "declared on the package."
                    ),
                    deduction=15,
                )

        # =========================================================
        # 2. FOOD-SPECIFIC FSSAI
        # =========================================================

        if context.is_food:
            fssai_value = declarations.get("fssai_license")

            fssai_passed = not cls._missing(fssai_value)

            checks.append(
                {
                    "check": "fssai_license",
                    "rule": "Food-category declaration",
                    "required": True,
                    "passed": fssai_passed,
                    "evidence": (
                        fssai_value
                        if fssai_value is not None
                        else "MISSING"
                    ),
                }
            )

            if not fssai_passed:
                add_violation(
                    code="STATUTORY_ADVISORY_MISSING",
                    rule="Food-category declaration",
                    severity="MEDIUM",
                    description=(
                        "FSSAI License / Registration No. "
                        "is missing or not clearly indicated."
                    ),
                    remedial_action=(
                        "Clearly indicate the applicable FSSAI "
                        "License / Registration number."
                    ),
                    deduction=10,
                )

        # =========================================================
        # 3. BRAND NAME
        # =========================================================

        brand_value = declarations.get("brand_name")

        brand_passed = not cls._missing(brand_value)

        checks.append(
            {
                "check": "brand_name",
                "rule": "Rule 6 Package Declaration",
                "required": True,
                "passed": brand_passed,
                "evidence": (
                    brand_value
                    if brand_value is not None
                    else "MISSING"
                ),
            }
        )

        if not brand_passed:
            add_violation(
                code="STATUTORY_ADVISORY_MISSING",
                rule="Rule 6 Package Declaration",
                severity="MEDIUM",
                description=(
                    "Brand name is missing or not clearly "
                    "identified on the package."
                ),
                remedial_action=(
                    "Clearly declare the applicable brand name."
                ),
                deduction=10,
            )

        # =========================================================
        # 4. BATCH / LOT NUMBER
        # =========================================================

        batch_value = declarations.get("batch_number")

        batch_passed = not cls._missing(batch_value)

        checks.append(
            {
                "check": "batch_number",
                "rule": "Rule 6 Package Declaration",
                "required": True,
                "passed": batch_passed,
                "evidence": (
                    batch_value
                    if batch_value is not None
                    else "MISSING"
                ),
            }
        )

        if not batch_passed:
            add_violation(
                code="STATUTORY_ADVISORY_MISSING",
                rule="Rule 6 Package Declaration",
                severity="MEDIUM",
                description=(
                    "Batch / Lot / Serial identification is "
                    "missing or not clearly identified."
                ),
                remedial_action=(
                    "Clearly declare the applicable batch, lot, "
                    "or serial identification."
                ),
                deduction=10,
            )

        # =========================================================
        # 5. MRP TAX INCLUSIVITY
        # =========================================================

        tax_clause = declarations.get("has_tax_clause")

        tax_passed = bool(tax_clause)

        checks.append(
            {
                "check": "mrp_tax_clause",
                "rule": "Rule 6 MRP",
                "required": True,
                "passed": tax_passed,
                "evidence": tax_clause,
            }
        )

        if not tax_passed:
            add_violation(
                code="MRP_TAX_CLAUSE_MISSING",
                rule="Rule 6 MRP",
                severity="HIGH",
                description=(
                    "MRP tax inclusivity indication was not "
                    "detected."
                ),
                remedial_action=(
                    "Ensure the MRP is declared inclusive of "
                    "all applicable taxes."
                ),
                deduction=10,
            )

        # =========================================================
        # 6. RULE 7 FONT SIZE
        # =========================================================

        if detected_font_height_mm is None:
            checks.append(
                {
                    "check": "font_height",
                    "rule": "Rule 7 Font Size",
                    "required": required_font_height_mm,
                    "detected": None,
                    "pdp_area_cm2": pdp_surface_area,
                    "passed": None,
                    "status": "NOT_ASSESSABLE",
                }
            )
        else:
            font_passed = (
                detected_font_height_mm
                >= required_font_height_mm
            )

            checks.append(
                {
                    "check": "font_height",
                    "rule": "Rule 7 Font Size",
                    "required": required_font_height_mm,
                    "detected": detected_font_height_mm,
                    "pdp_area_cm2": pdp_surface_area,
                    "passed": font_passed,
                }
            )

            if not font_passed:
                add_violation(
                    code="RULE_7_FONT_SIZE",
                    rule="Rule 7 Font Size",
                    severity="HIGH",
                    description=(
                        "Detected declaration font height is "
                        "below the required minimum."
                    ),
                    remedial_action=(
                        "Increase the relevant declaration font "
                        "height to meet the applicable Rule 7 "
                        "minimum."
                    ),
                    deduction=10,
                )

        # =========================================================
        # 7. CONSUMER CARE / REDRESSAL
        # =========================================================

        if context.consumer_care_required:

            consumer_passed = bool(
                consumer_care.get("is_fully_compliant")
            )

            checks.append(
                {
                    "check": "consumer_care",
                    "rule": "Consumer Care / Redressal",
                    "required": True,
                    "passed": consumer_passed,
                    "evidence": consumer_care,
                }
            )

            if not consumer_passed:

                missing_components = []

                if not consumer_care.get(
                    "has_care_email",
                    False,
                ):
                    missing_components.append("Email ID")

                if not consumer_care.get(
                    "has_care_phone",
                    False,
                ):
                    missing_components.append("Helpline Phone")

                if not consumer_care.get(
                    "has_person_or_designation",
                    False,
                ):
                    missing_components.append(
                        "Designated Officer Name"
                    )

                missing_text = (
                    ", ".join(missing_components)
                    if missing_components
                    else "required consumer redressal details"
                )

                add_violation(
                    code="CONSUMER_CARE_DEFICIENCY",
                    rule="Consumer Care / Redressal Requirement",
                    severity="HIGH",
                    description=(
                        f"Missing redressal components: "
                        f"{missing_text}."
                    ),
                    remedial_action=(
                        "Provide the required consumer grievance "
                        "redressal contact details."
                    ),
                    deduction=10,
                )

        else:

            checks.append(
                {
                    "check": "consumer_care",
                    "rule": "Consumer Care / Redressal",
                    "required": False,
                    "passed": True,
                    "status": "NOT_APPLICABLE",
                }
            )

        # =========================================================
        # 8. USP / UNIT SALE PRICE
        # =========================================================
        #
        # IMPORTANT:
        # A mathematically calculable expected USP does NOT mean
        # that the package actually declared a USP.
        #
        # First check declaration presence.
        # Then perform mathematical verification.
        # =========================================================

        if context.requires_unit_sale_price():

            declared_usp = declarations.get(
                "unit_sale_price"
            )

            # -----------------------------------------------------
            # USP REQUIRED BUT MISSING
            # -----------------------------------------------------

            if cls._missing(declared_usp):

                checks.append(
                    {
                        "check": "usp_math",
                        "rule": "Unit Sale Price Verification",
                        "required": True,
                        "passed": False,
                        "status": "NON-COMPLIANT",
                        "evidence": {
                            "declared": "MISSING",
                            "reason": (
                                "Required Unit Sale Price "
                                "declaration is missing."
                            ),
                        },
                    }
                )

                add_violation(
                    code="UNIT_SALE_PRICE_MISSING",
                    rule="Rule 6(11) Unit Sale Price",
                    severity="HIGH",
                    description=(
                        "Required Unit Sale Price (USP) is "
                        "missing or unreadable on the package."
                    ),
                    remedial_action=(
                        "Declare the applicable Unit Sale Price "
                        "clearly on the retail package."
                    ),
                    deduction=10,
                )

            # -----------------------------------------------------
            # USP EXISTS BUT MATHEMATICAL VERIFICATION UNAVAILABLE
            # -----------------------------------------------------

            elif usp_math is None:

                checks.append(
                    {
                        "check": "usp_math",
                        "rule": "Unit Sale Price Verification",
                        "required": True,
                        "passed": None,
                        "status": "NOT_ASSESSABLE",
                        "evidence": {
                            "declared": declared_usp,
                            "reason": (
                                "USP was declared, but "
                                "mathematical verification "
                                "was unavailable."
                            ),
                        },
                    }
                )

            # -----------------------------------------------------
            # USP EXISTS BUT MATH IS WRONG
            # -----------------------------------------------------

            elif usp_math.get("verified") is False:

                checks.append(
                    {
                        "check": "usp_math",
                        "rule": "Unit Sale Price Verification",
                        "required": True,
                        "passed": False,
                        "status": "NON-COMPLIANT",
                        "evidence": {
                            "declared": declared_usp,
                            "expected": usp_math.get("expected"),
                            "verified": False,
                        },
                    }
                )

                add_violation(
                    code="UNIT_SALE_PRICE_MISMATCH",
                    rule="Rule 6(11) Unit Sale Price",
                    severity="HIGH",
                    description=(
                        "Declared Unit Sale Price does not "
                        "match the expected value based on "
                        "the package declaration."
                    ),
                    remedial_action=(
                        "Correct the Unit Sale Price declaration "
                        "according to the applicable net "
                        "quantity and unit-sale-price rules."
                    ),
                    deduction=10,
                )

            # -----------------------------------------------------
            # USP EXISTS AND MATH IS CORRECT
            # -----------------------------------------------------

            else:

                checks.append(
                    {
                        "check": "usp_math",
                        "rule": "Unit Sale Price Verification",
                        "required": True,
                        "passed": True,
                        "status": "VERIFIED",
                        "evidence": {
                            "declared": declared_usp,
                            "expected": usp_math.get("expected"),
                            "verified": True,
                        },
                    }
                )

        # ---------------------------------------------------------
        # USP NOT APPLICABLE
        # ---------------------------------------------------------

        else:

            checks.append(
                {
                    "check": "usp_math",
                    "rule": "Unit Sale Price Verification",
                    "required": False,
                    "passed": True,
                    "status": "NOT_APPLICABLE",
                    "evidence": {
                        "reason": (
                            "Unit Sale Price is not applicable "
                            "to this package context."
                        ),
                    },
                }
            )

        # =========================================================
        # 9. COUNTRY OF ORIGIN
        # =========================================================

        if context.requires_country_of_origin():

            origin = declarations.get(
                "country_of_origin"
            )

            origin_passed = not cls._missing(origin)

            checks.append(
                {
                    "check": "country_of_origin",
                    "rule": "Country of Origin",
                    "required": True,
                    "passed": origin_passed,
                    "evidence": (
                        origin
                        if origin is not None
                        else "MISSING"
                    ),
                }
            )

            if not origin_passed:
                add_violation(
                    code="COUNTRY_OF_ORIGIN_MISSING",
                    rule="Country of Origin",
                    severity="HIGH",
                    description=(
                        "Country of origin is missing or "
                        "unreadable for an imported package."
                    ),
                    remedial_action=(
                        "Clearly declare the country of origin "
                        "on the package."
                    ),
                    deduction=10,
                )

        else:

            checks.append(
                {
                    "check": "country_of_origin",
                    "rule": "Country of Origin",
                    "required": False,
                    "passed": True,
                    "status": "NOT_APPLICABLE",
                    "evidence": {
                        "reason": (
                            "Country of origin declaration is "
                            "not required by the current "
                            "assessment context."
                        ),
                    },
                }
            )

        # =========================================================
        # 10. DIMENSIONS WHERE RELEVANT
        # =========================================================

        if context.requires_dimensions():

            dimensions_present = (
                declarations.get("dimensions")
                or declarations.get("dimension")
            )

            dimensions_passed = not cls._missing(
                dimensions_present
            )

            checks.append(
                {
                    "check": "dimensions",
                    "rule": "Dimensions Declaration",
                    "required": True,
                    "passed": dimensions_passed,
                    "evidence": (
                        dimensions_present
                        if dimensions_present is not None
                        else "MISSING"
                    ),
                }
            )

            if not dimensions_passed:
                add_violation(
                    code="DIMENSIONS_MISSING",
                    rule="Dimensions Declaration",
                    severity="MEDIUM",
                    description=(
                        "Required dimensions declaration "
                        "was not detected."
                    ),
                    remedial_action=(
                        "Clearly declare the applicable "
                        "dimensions."
                    ),
                    deduction=10,
                )

        # =========================================================
        # 11. BEST BEFORE / USE BY
        # =========================================================

        if context.requires_best_before():

            expiry_value = declarations.get(
                "expiry_date"
            )

            expiry_passed = not cls._missing(
                expiry_value
            )

            checks.append(
                {
                    "check": "expiry_date",
                    "rule": "Best Before / Use By",
                    "required": True,
                    "passed": expiry_passed,
                    "evidence": (
                        expiry_value
                        if expiry_value is not None
                        else "MISSING"
                    ),
                }
            )

            if not expiry_passed:
                add_violation(
                    code="BEST_BEFORE_MISSING",
                    rule="Best Before / Use By",
                    severity="HIGH",
                    description=(
                        "Required Best Before / Use By "
                        "declaration was not detected."
                    ),
                    remedial_action=(
                        "Clearly declare the applicable "
                        "Best Before / Use By information."
                    ),
                    deduction=10,
                )

        # =========================================================
        # 12. GS1 / BARCODE ORIGIN CROSS-CHECK
        # =========================================================

        if barcode_data:

            gs1_origin_status = barcode_data.get(
                "origin_verified"
            )

            if gs1_origin_status == "MISMATCH":

                checks.append(
                    {
                        "check": "gs1_origin",
                        "rule": (
                            "GS1 Country of Origin "
                            "Cross-Check"
                        ),
                        "passed": False,
                        "evidence": barcode_data,
                    }
                )

                add_violation(
                    code="GS1_ORIGIN_MISMATCH",
                    rule=(
                        "GS1 Country of Origin "
                        "Cross-Check"
                    ),
                    severity="HIGH",
                    description=(
                        "Barcode-derived country information "
                        "does not reconcile with the declared "
                        "country of origin."
                    ),
                    remedial_action=(
                        "Review the barcode information and "
                        "declared country of origin."
                    ),
                    deduction=10,
                )

            else:

                checks.append(
                    {
                        "check": "gs1_origin",
                        "rule": (
                            "GS1 Country of Origin "
                            "Cross-Check"
                        ),
                        "passed": True,
                        "evidence": barcode_data,
                    }
                )

        # =========================================================
        # 13. FINAL SCORE
        # =========================================================

        score = max(
            0.0,
            min(100.0, score),
        )

        # =========================================================
        # FINAL STATUS
        # =========================================================

        if score >= 85:
            status = "COMPLIANT"
        elif score >= 70:
            status = "WARNING"
        else:
            status = "NON-COMPLIANT"

        is_compliant = status == "COMPLIANT"

        # =========================================================
        # RETURN
        # =========================================================

        return {
            "compliance_score": round(score, 2),
            "is_compliant": is_compliant,
            "status": status,
            "violations": violations,
            "checks": checks,
        }


# =============================================================
# BACKWARD-COMPATIBILITY ALIASES
# =============================================================

LegalMetrologyVerifier = ComplianceEngine
RuleEvaluator = ComplianceEngine