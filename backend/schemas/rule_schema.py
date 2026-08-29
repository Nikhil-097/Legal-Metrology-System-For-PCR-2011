from typing import List, Optional
from pydantic import BaseModel, Field


class LegalRuleSummary(BaseModel):
    rule_number: str
    title: str


class RuleRequirementOut(BaseModel):
    code: str
    rule: str
    field: str
    severity: str
    machine_checkable: bool = True
    effective_from: Optional[str] = None
    allowed_units: Optional[List[str]] = None
    regex_pattern: Optional[str] = None
    description: str


class FontSizeMatrixEntry(BaseModel):
    pdp_area_cm2_min: float
    pdp_area_cm2_max: Optional[float] = None
    min_font_height_mm_small_pack: float
    min_font_height_mm_large_pack: float
    min_font_height_mm_blown_moulded: Optional[float] = None


class FontSizeCalculationRequest(BaseModel):
    pdp_area_cm2: float = Field(..., gt=0)
    net_quantity: float = Field(..., gt=0)
    unit: str = Field(..., description="Measurement unit (e.g., g, kg, ml, l)")


class FontSizeCalculationResponse(BaseModel):
    pdp_area_cm2: float
    required_min_font_height_mm: float


class LegalExemptionOut(BaseModel):
    code: str
    rule: str
    category: str
    max_quantity: Optional[float] = None
    min_quantity: Optional[float] = None
    unit: Optional[str] = None
    exempt_fields: List[str]
    notes: Optional[str] = None


class MPEThresholdEntry(BaseModel):
    min: float
    max: Optional[float] = None
    percentage: Optional[float] = None
    absolute: Optional[float] = None