from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class BoundingBoxPolygon(BaseModel):
    points: List[List[float]] = Field(..., description="Array of [x, y] vertex coordinate pairs")


class OCRTextElement(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]
    height_px: float
    height_mm: float


class ExtractedDeclarations(BaseModel):
    net_quantity: str = "MISSING"
    mrp: str = "MISSING"
    has_tax_clause: bool = False
    unit_sale_price: str = "MISSING"
    mfg_date: str = "MISSING"
    country_of_origin: str = "India (Presumed / Domestic)"


class ViolationDetail(BaseModel):
    rule: str
    code: str
    severity: str = "HIGH"
    detail: str


class ScanAnalysisRequest(BaseModel):
    height_cm: float = Field(default=10.0, gt=0, description="Package physical height in cm")
    width_cm: float = Field(default=10.0, gt=0, description="Package physical width or circumference in cm")
    pdp_type: str = Field(default="rectangular", pattern="^(rectangular|cylindrical)$")
    brand_name: Optional[str] = "Unknown Brand"
    commodity_name: Optional[str] = "Packaged Good"
    inspector_id: Optional[str] = "INSP-DEFAULT"


class ScanAnalysisResponse(BaseModel):
    scan_id: str
    inspector_id: str
    brand_name: str
    commodity_name: str
    barcode: Optional[str] = None
    dimensions: Dict[str, Any]
    pdp_area_cm2: float
    scale_ratio_px_mm: float
    required_min_font_height_mm: float
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    is_compliant: bool
    violations: List[ViolationDetail]
    extracted_declarations: ExtractedDeclarations
    raw_text_extracted: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    filename: Optional[str] = None


class ScanRecordSummary(BaseModel):
    scan_id: str
    brand_name: str
    commodity_name: str
    compliance_score: float
    is_compliant: bool
    violations_count: int
    created_at: Optional[str] = None


class ScanHistoryResponse(BaseModel):
    status: str = "success"
    total: int
    scans: List[Dict[str, Any]]