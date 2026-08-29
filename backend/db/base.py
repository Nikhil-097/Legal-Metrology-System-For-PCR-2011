from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in the Legal Metrology system.
    Provides table metadata and common declarative behavior.
    """
    pass


# Import all ORM models so Base.metadata contains all table definitions
from app.models.user import User  # noqa: F401
from app.models.scan import ScanRecord, DetectedViolation  # noqa: F401
from app.models.rule import LegalRule, RuleVersion, RuleRequirement, FontSizeRule, LegalExemption  # noqa: F401
from app.models.report import InspectionReport, ShowCauseNotice  # noqa: F401