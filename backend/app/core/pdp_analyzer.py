from typing import Dict, Any, List, Optional

class PDPAnalyzer:
    """Calculates Principal Display Panel (PDP) surface area and Rule 7 statutory font requirements."""

    @staticmethod
    def calculate_pdp_area(
        image_shape: tuple,
        dimensions: Optional[Dict[str, float]] = None,
        pdp_type: str = "rectangular"
    ) -> float:
        """
        Calculates PDP Area in cm² according to Legal Metrology Rule 7 formulas:
        - Rectangular container: Height x Width of one side.
        - Cylindrical container: 40% of (Height x Circumference).
        """
        if dimensions and "height_cm" in dimensions and "width_cm" in dimensions:
            h = dimensions["height_cm"]
            w = dimensions["width_cm"]
            if pdp_type.lower() == "cylindrical":
                return round(0.40 * h * w, 2)
            return round(h * w, 2)

        # Fallback estimation from image pixel dimensions
        h_px, w_px = image_shape[:2]
        estimated_area = (h_px * w_px) / (100 * 100)
        return round(estimated_area, 2)

    @staticmethod
    def get_min_font_requirement(
        font_matrix: List[Dict[str, Any]],
        pdp_area_cm2: float,
        net_quantity: float,
        unit: str
    ) -> float:
        """
        Looks up statutory minimum font height (mm) from Rule 7 matrix.
        Packages > 200g/200ml have higher minimum font thresholds.
        """
        is_large = False
        norm_unit = unit.lower().strip()
        if norm_unit in ["g", "ml"] and net_quantity > 200:
            is_large = True
        elif norm_unit in ["kg", "l"]:
            is_large = True

        for entry in font_matrix:
            p_min = entry["pdp_area_cm2_min"]
            p_max = entry["pdp_area_cm2_max"]

            if p_max is None:
                if pdp_area_cm2 > p_min:
                    return float(entry["min_font_height_mm_large_pack"] if is_large else entry["min_font_height_mm_small_pack"])
            elif p_min <= pdp_area_cm2 <= p_max:
                return float(entry["min_font_height_mm_large_pack"] if is_large else entry["min_font_height_mm_small_pack"])

        return 1.0  # Statutory minimum baseline