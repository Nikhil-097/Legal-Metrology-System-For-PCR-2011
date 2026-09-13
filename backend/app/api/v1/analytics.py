from collections import Counter

from fastapi import APIRouter
from sqlalchemy import select, func

from db.session import SessionLocal
from models.scan import ScanRecord, DetectedViolation

router = APIRouter()


@router.get("/dashboard-stats")
async def get_dashboard_analytics():
    """
    Computes real-time compliance metrics directly from PostgreSQL.
    """

    db = SessionLocal()

    try:
        total_scans = db.scalar(
            select(func.count(ScanRecord.id))
        ) or 0

        if total_scans == 0:
            return {
                "total_scans": 0,
                "compliant_count": 0,
                "non_compliant_count": 0,
                "compliance_rate_percentage": 0.0,
                "average_score": 0.0,
                "violation_frequency": {},
                "severity_distribution": {
                    "HIGH": 0,
                    "MEDIUM": 0,
                    "LOW": 0
                }
            }

        compliant_count = db.scalar(
            select(func.count(ScanRecord.id))
            .where(ScanRecord.is_compliant.is_(True))
        ) or 0

        non_compliant_count = total_scans - compliant_count

        avg_score = db.scalar(
            select(func.avg(ScanRecord.compliance_score))
        ) or 0.0

        compliance_rate = round(
            (compliant_count / total_scans) * 100,
            2
        )

        violations = db.execute(
            select(
                DetectedViolation.violation_code,
                DetectedViolation.severity
            )
        ).all()

        violation_counter = Counter()
        severity_counter = Counter({
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        })

        for violation_code, severity in violations:
            violation_counter[violation_code] += 1

            severity = (severity or "HIGH").upper()

            if severity not in severity_counter:
                severity_counter[severity] = 0

            severity_counter[severity] += 1

        return {
            "total_scans": total_scans,
            "compliant_count": compliant_count,
            "non_compliant_count": non_compliant_count,
            "compliance_rate_percentage": compliance_rate,
            "average_score": round(float(avg_score), 2),
            "violation_frequency": dict(
                violation_counter.most_common(10)
            ),
            "severity_distribution": dict(severity_counter)
        }

    finally:
        db.close()


@router.get("/top-violations")
async def get_top_violations():
    """
    Returns the most frequently breached Legal Metrology clauses
    directly from PostgreSQL.
    """

    db = SessionLocal()

    try:
        rows = db.execute(
            select(
                DetectedViolation.violation_code,
                DetectedViolation.rule_reference,
                DetectedViolation.description,
                func.count(DetectedViolation.id).label("count")
            )
            .group_by(
                DetectedViolation.violation_code,
                DetectedViolation.rule_reference,
                DetectedViolation.description
            )
            .order_by(
                func.count(DetectedViolation.id).desc()
            )
            .limit(5)
        ).all()

        top_items = [
            {
                "code": row.violation_code,
                "count": row.count,
                "rule": row.rule_reference,
                "detail": row.description
            }
            for row in rows
        ]

        return {
            "top_violations": top_items
        }

    finally:
        db.close()