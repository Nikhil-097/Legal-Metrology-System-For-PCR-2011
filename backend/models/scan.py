import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class ScanRecord(Base):
    __tablename__ = "scan_records"

    id = Column(Integer, primary_key=True, index=True)
    scan_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Product & Packaging Information
    brand_name = Column(String(255), default="Unknown Brand", nullable=False)
    commodity_name = Column(String(255), default="Packaged Good", nullable=False)
    barcode_value = Column(String(50), nullable=True, index=True)
    pdp_type = Column(String(50), default="rectangular", nullable=False)  # 'rectangular' or 'cylindrical'
    height_cm = Column(Float, nullable=False, default=10.0)
    width_cm = Column(Float, nullable=False, default=10.0)
    pdp_area_cm2 = Column(Float, nullable=False)
    ppm_scale = Column(Float, nullable=False)  # Pixels per millimeter
    required_min_font_height_mm = Column(Float, nullable=False, default=1.0)

    # Compliance Results
    compliance_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 100.0%
    is_compliant = Column(Boolean, default=False, nullable=False, index=True)

    # AI & OCR JSON Payloads
    extracted_data = Column(JSON, nullable=False, default=dict)  # Parsed MRP, USP, Net Qty, Dates
    raw_ocr_payload = Column(JSON, nullable=True)               # Full bounding boxes and confidence
    image_storage_url = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    # Relationships
    inspector = relationship("User", back_populates="scans")
    violations = relationship("DetectedViolation", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("InspectionReport", back_populates="scan", cascade="all, delete-orphan")


class DetectedViolation(Base):
    __tablename__ = "detected_violations"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scan_records.id", ondelete="CASCADE"), nullable=False)
    violation_code = Column(String(100), nullable=False, index=True)
    rule_reference = Column(String(100), nullable=False)  # e.g., 'Rule 6(1)(e)', 'Rule 7'
    severity = Column(String(20), default="HIGH", nullable=False)  # 'HIGH', 'MEDIUM', 'LOW'
    description = Column(String(500), nullable=False)
    remedial_action = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    scan = relationship("ScanRecord", back_populates="violations")