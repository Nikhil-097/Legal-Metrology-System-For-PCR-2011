from collections import Counter
from fastapi import APIRouter
from app.api.v1.scans import IN_MEMORY_SCAN_DB

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_analytics():
    """
    Computes real-time compliance metrics, violation frequency distribution,
    and average compliance scores for the officer enforcement dashboard.
    """
    total_scans = len(IN_MEMORY_SCAN_DB)
    if total_scans == 0:
        return {
            "total_scans": 0,
            "compliant_count": 0,
            "non_compliant_count": 0,
            "compliance_rate_percentage": 0.0,
            "average_score": 0.0,
            "violation_frequency": {},
            "severity_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }

    compliant_count = sum(1 for s in IN_MEMORY_SCAN_DB if s.get("is_compliant", False))
    non_compliant_count = total_scans - compliant_count
    compliance_rate = round((compliant_count / total_scans) * 100, 2)
    avg_score = round(sum(s.get("compliance_score", 0.0) for s in IN_MEMORY_SCAN_DB) / total_scans, 2)

    # Calculate violation breakdown
    violation_counter = Counter()
    severity_counter = Counter({"HIGH": 0, "MEDIUM": 0, "LOW": 0})

    for s in IN_MEMORY_SCAN_DB:
        for v in s.get("violations", []):
            violation_counter[v.get("code", "UNKNOWN")] += 1
            severity = v.get("severity", "HIGH").upper()
            severity_counter[severity] += 1

    return {
        "total_scans": total_scans,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "compliance_rate_percentage": compliance_rate,
        "average_score": avg_score,
        "violation_frequency": dict(violation_counter.most_common(10)),
        "severity_distribution": dict(severity_counter)
    }

@router.get("/top-violations")
async def get_top_violations():
    """Returns the most frequently breached Legal Metrology clauses across all scans."""
    violation_counter = Counter()
    rule_mapping = {}

    for s in IN_MEMORY_SCAN_DB:
        for v in s.get("violations", []):
            code = v.get("code")
            violation_counter[code] += 1
            rule_mapping[code] = {"rule": v.get("rule"), "detail": v.get("detail")}

    top_items = [
        {
            "code": code,
            "count": count,
            "rule": rule_mapping[code]["rule"],
            "detail": rule_mapping[code]["detail"]
        }
        for code, count in violation_counter.most_common(5)
    ]
    return {"top_violations": top_items}