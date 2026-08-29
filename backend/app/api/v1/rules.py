from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_rule_matrix

router = APIRouter()

@router.get("/summary")
async def get_all_rules_summary(rule_matrix: dict = Depends(get_rule_matrix)):
    """Returns dataset metadata, active amendments, and all 34 primary statutory rules."""
    return {
        "dataset": rule_matrix.get("dataset"),
        "sources": rule_matrix.get("sources"),
        "total_rules": len(rule_matrix.get("rules", [])),
        "rules": rule_matrix.get("rules", [])
    }

@router.get("/requirements")
async def get_mandatory_requirements(
    severity: Optional[str] = Query(None, description="Filter by severity: HIGH, MEDIUM, LOW"),
    rule_matrix: dict = Depends(get_rule_matrix)
):
    """Fetches mandatory Rule 6 field declarations, permitted regex patterns, and units."""
    requirements = rule_matrix.get("requirements", [])
    if severity:
        requirements = [r for r in requirements if r.get("severity", "").upper() == severity.upper()]
    return {"total": len(requirements), "requirements": requirements}

@router.get("/font-size-matrix")
async def get_font_size_matrix(rule_matrix: dict = Depends(get_rule_matrix)):
    """Fetches Rule 7 Principal Display Panel area vs font height threshold lookup table."""
    return {"font_size_matrix": rule_matrix.get("font_size_matrix", [])}

@router.get("/calculate-min-font")
async def calculate_required_font(
    pdp_area_cm2: float = Query(..., description="Surface area of PDP in cm²"),
    net_quantity: float = Query(..., description="Net declared numeric quantity"),
    unit: str = Query(..., description="Unit of measurement (g, kg, ml, l, etc.)"),
    rule_matrix: dict = Depends(get_rule_matrix)
):
    """Calculates the statutory minimum font height required for specific package dimensions."""
    font_matrix = rule_matrix.get("font_size_matrix", [])
    is_large = False
    if unit.lower() in ["g", "ml"] and net_quantity > 200:
        is_large = True
    elif unit.lower() in ["kg", "l"]:
        is_large = True

    for entry in font_matrix:
        p_min = entry["pdp_area_cm2_min"]
        p_max = entry["pdp_area_cm2_max"]
        if p_max is None:
            if pdp_area_cm2 > p_min:
                min_h = entry["min_font_height_mm_large_pack"] if is_large else entry["min_font_height_mm_small_pack"]
                return {"pdp_area_cm2": pdp_area_cm2, "required_min_font_height_mm": min_h}
        elif p_min <= pdp_area_cm2 <= p_max:
            min_h = entry["min_font_height_mm_large_pack"] if is_large else entry["min_font_height_mm_small_pack"]
            return {"pdp_area_cm2": pdp_area_cm2, "required_min_font_height_mm": min_h}

    return {"pdp_area_cm2": pdp_area_cm2, "required_min_font_height_mm": 1.0}

@router.get("/exemptions")
async def get_statutory_exemptions(rule_matrix: dict = Depends(get_rule_matrix)):
    """Fetches statutory exemptions under Rule 26 (small packs, bulk packs, DPCO drugs, etc.)."""
    return {"exemptions": rule_matrix.get("exemptions", [])}

@router.get("/mpe-table")
async def get_maximum_permissible_error_table(rule_matrix: dict = Depends(get_rule_matrix)):
    """Fetches the First Schedule Maximum Permissible Error (MPE) weight/volume thresholds."""
    return {"mpe_table": rule_matrix.get("mpe_weight_volume_table", [])}