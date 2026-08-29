import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class InspectionReport(Base):
    __tablename__ = "inspection_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    scan_id = Column(Integer, ForeignKey("scan_records.id", ondelete="CASCADE"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), default="Packaged Commodity Legal Metrology Inspection Report", nullable=False)
    pdf_file_path = Column(String(1000), nullable=True)
    is_finalized = Column(Boolean, default=False, nullable=False)
    summary_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    # Relationships
    scan = relationship("ScanRecord", back_populates="reports")
    officer = relationship("User", back_populates="reports_issued")
    notices = relationship("ShowCauseNotice", back_populates="report", cascade="all, delete-orphan")


class ShowCauseNotice(Base):
    __tablename__ = "show_cause_notices"

    id = Column(Integer, primary_key=True, index=True)
    notice_reference_no = Column(String(100), unique=True, index=True, nullable=False)
    report_id = Column(Integer, ForeignKey("inspection_reports.id", ondelete="CASCADE"), nullable=False)
    recipient_entity = Column(String(255), nullable=False)
    statutory_clause = Column(String(255), default="Rule 32 read with Section 36 of Legal Metrology Act, 2009", nullable=False)
    compliance_deadline_days = Column(Integer, default=15, nullable=False)
    issued_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(50), default="ISSUED", nullable=False)  # 'ISSUED', 'REPLIED', 'HEARING_SCHEDULED', 'COMPOUNDED'

    # Relationships
    report = relationship("InspectionReport", back_populates="notices")