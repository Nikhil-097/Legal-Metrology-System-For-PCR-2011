import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserRole(str, enum.Enum):
    FIELD_INSPECTOR = "FIELD_INSPECTOR"
    LEGAL_OFFICER = "LEGAL_OFFICER"
    SUPER_ADMIN = "SUPER_ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    designation = Column(String(150), nullable=True)
    department = Column(String(200), default="Department of Consumer Affairs")
    jurisdiction_zone = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.FIELD_INSPECTOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    scans = relationship("ScanRecord", back_populates="inspector", cascade="all, delete-orphan")
    reports_issued = relationship("InspectionReport", back_populates="officer")