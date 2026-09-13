from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in the Legal Metrology system.
    """
    pass


# Import all ORM models so Base.metadata contains all table definitions.
from models.user import User  # noqa: F401, E402
from models.scan import ScanRecord, DetectedViolation  # noqa: F401, E402
from models.rules import (  # noqa: F401, E402
    LegalRule,
    RuleVersion,
    RuleRequirement,
    FontSizeRule,
    LegalExemption,
)
from models.reports import (  # noqa: F401, E402
    InspectionReport,
    ShowCauseNotice,
)