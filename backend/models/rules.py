from datetime import date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base


class LegalRule(Base):
    __tablename__ = "legal_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_number = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    principal_effective_from = Column(Date, default=date(2011, 4, 1), nullable=False)

    # Relationships
    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("legal_rules.id", ondelete="CASCADE"), nullable=False)
    version_label = Column(String(50), nullable=False)
    operative_text = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)  # NULL indicates active rule version
    legal_status = Column(String(50), default="active", nullable=False)

    # Relationships
    rule = relationship("LegalRule", back_populates="versions")
    requirements = relationship("RuleRequirement", back_populates="version", cascade="all, delete-orphan")


class RuleRequirement(Base):
    __tablename__ = "rule_requirements"

    id = Column(Integer, primary_key=True, index=True)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id", ondelete="CASCADE"), nullable=False)
    requirement_code = Column(String(100), unique=True, index=True, nullable=False)
    field_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    regex_pattern = Column(String(500), nullable=True)
    allowed_units = Column(JSON, nullable=True)  # e.g., ["g", "kg", "ml", "l", "N"]
    severity = Column(String(20), default="HIGH", nullable=False)
    machine_checkable = Column(Boolean, default=True, nullable=False)
    is_ecommerce_rule = Column(Boolean, default=False, nullable=False)
    is_multipack_rule = Column(Boolean, default=False, nullable=False)

    # Relationships
    version = relationship("RuleVersion", back_populates="requirements")


class FontSizeRule(Base):
    __tablename__ = "font_size_rules"

    id = Column(Integer, primary_key=True, index=True)
    pdp_area_min_cm2 = Column(Float, default=0.0, nullable=False)
    pdp_area_max_cm2 = Column(Float, nullable=True)  # NULL indicates open upper bound (> 500 cm2)
    weight_volume_threshold_g_ml = Column(Float, default=200.0, nullable=False)
    min_font_height_mm_small_pack = Column(Float, nullable=False)
    min_font_height_mm_large_pack = Column(Float, nullable=False)
    min_font_height_mm_blown_moulded = Column(Float, nullable=True)
    effective_from = Column(Date, default=date(2011, 4, 1), nullable=False)
    effective_to = Column(Date, nullable=True)


class LegalExemption(Base):
    __tablename__ = "legal_exemptions"

    id = Column(Integer, primary_key=True, index=True)
    exemption_code = Column(String(100), unique=True, index=True, nullable=False)
    rule_reference = Column(String(100), default="Rule 26", nullable=False)
    category_name = Column(String(200), nullable=False)
    condition_description = Column(String(500), nullable=False)
    min_quantity = Column(Float, nullable=True)
    max_quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    exempt_from_fields = Column(JSON, nullable=False, default=list)  # e.g. ["mrp", "mfg_date"]