from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select

from db.session import SessionLocal
from models.scan import ScanRecord, DetectedViolation


def _scan_to_dict(scan: ScanRecord) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy ScanRecord back into the legacy API response shape.

    The frontend currently expects fields such as:
    scan_id, product_name, declarations, violations, barcode_data, etc.

    Those values are stored inside extracted_data while the important
    searchable fields are also normalized into PostgreSQL columns.
    """
    data = dict(scan.extracted_data or {})

    # Always derive these from the canonical database row.
    data["scan_id"] = scan.scan_uuid
    data["id"] = scan.scan_uuid

    data["product_name"] = scan.commodity_name
    data["brand_name"] = scan.brand_name
    data["compliance_score"] = scan.compliance_score
    data["score"] = scan.compliance_score
    data["is_compliant"] = scan.is_compliant

    if scan.created_at:
        data["timestamp"] = scan.created_at.strftime(
            "%d %b %Y • %I:%M %p"
        )

    # Make sure violations always reflect the normalized child table.
    data["violations"] = [
        {
            "rule": violation.rule_reference,
            "detail": violation.description,
            "severity": violation.severity,
            "remedial_action": violation.remedial_action,
            "code": violation.violation_code,
        }
        for violation in scan.violations
    ]

    return data


def save_scan(
    scan_record: Dict[str, Any],
    *,
    raw_ocr_payload: Optional[Dict[str, Any]] = None,
    image_storage_url: Optional[str] = None,
    inspector_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Persist one completed scan into PostgreSQL.

    This replaces the old SQLite save_scan() implementation.
    """

    scan_id = str(scan_record["scan_id"])

    declarations = scan_record.get("declarations") or {}
    barcode_data = scan_record.get("barcode_data") or {}

    # Keep the complete API result in JSON so no information is lost
    # while the important queryable fields remain normalized.
    extracted_data = dict(scan_record)

    scan = ScanRecord(
        # The existing API uses SCN-XXXXXX identifiers.
        # scan_uuid is a String(36), so it can safely preserve that
        # externally visible identifier.
        scan_uuid=scan_id,

        inspector_id=inspector_id,

        brand_name=(
            scan_record.get("brand_name")
            or declarations.get("brand_name")
            or "Unknown Brand"
        ),

        commodity_name=(
            scan_record.get("product_name")
            or declarations.get("commodity_name")
            or "Packaged Good"
        ),

        barcode_value=(
            barcode_data.get("code")
            if barcode_data.get("code") not in ("", "N/A", None)
            else None
        ),

        pdp_type=str(
            scan_record.get("pdp_type")
            or "rectangular"
        )[:50],

        height_cm=_extract_dimension(
            scan_record.get("height_cm"),
            default=10.0,
        ),

        width_cm=_extract_dimension(
            scan_record.get("width_cm"),
            default=10.0,
        ),

        pdp_area_cm2=_extract_pdp_area(scan_record),

        # No genuine pixel/mm measurement is currently produced by
        # the pipeline, so do not invent one.
        ppm_scale=None,

        required_min_font_height_mm=_extract_required_font_height(
            scan_record
        ),

        compliance_score=float(
            scan_record.get("compliance_score", 0.0)
        ),

        is_compliant=bool(
            scan_record.get("is_compliant", False)
        ),

        extracted_data=extracted_data,

        raw_ocr_payload=raw_ocr_payload,

        image_storage_url=image_storage_url,
    )

    violations = scan_record.get("violations") or []

    for index, violation in enumerate(violations):
        rule_reference = str(
            violation.get("rule")
            or "Unknown Rule"
        )[:100]

        description = str(
            violation.get("detail")
            or "Compliance violation detected."
        )[:500]

        severity = _normalise_severity(
            violation.get("severity")
        )

        detected_violation = DetectedViolation(
            violation_code=_make_violation_code(
                violation,
                index,
            ),
            rule_reference=rule_reference,
            severity=severity,
            description=description,
            remedial_action=(
                str(violation.get("remedial_action"))[:500]
                if violation.get("remedial_action")
                else None
            ),
        )

        scan.violations.append(detected_violation)

    db = SessionLocal()

    try:
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Return the same shape that the API currently exposes.
        return _scan_to_dict(scan)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_all_scans() -> List[Dict[str, Any]]:
    """
    Fetch all scans from PostgreSQL.

    Newest scans are returned first.
    """

    db = SessionLocal()

    try:
        statement = (
            select(ScanRecord)
            .order_by(ScanRecord.created_at.desc())
        )

        scans = db.scalars(statement).all()

        return [
            _scan_to_dict(scan)
            for scan in scans
        ]

    finally:
        db.close()


def get_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch one scan using the externally visible SCN-XXXXXX identifier.
    """

    db = SessionLocal()

    try:
        statement = select(ScanRecord).where(
            ScanRecord.scan_uuid == str(scan_id)
        )

        scan = db.scalar(statement)

        if scan is None:
            return None

        return _scan_to_dict(scan)

    finally:
        db.close()


def delete_scan(scan_id: str) -> bool:
    """
    Delete one scan and its child violations.

    Not currently used by the API, but kept here so deletion remains
    a repository concern rather than leaking ORM logic into routers.
    """

    db = SessionLocal()

    try:
        statement = select(ScanRecord).where(
            ScanRecord.scan_uuid == str(scan_id)
        )

        scan = db.scalar(statement)

        if scan is None:
            return False

        db.delete(scan)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def _extract_dimension(
    value: Any,
    *,
    default: float,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_pdp_area(
    scan_record: Dict[str, Any],
) -> float:
    """
    Prefer an explicit PDP area.

    If it is not present, calculate it from height × width.
    """

    value = scan_record.get("pdp_area_cm2")

    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    height = _extract_dimension(
        scan_record.get("height_cm"),
        default=10.0,
    )

    width = _extract_dimension(
        scan_record.get("width_cm"),
        default=10.0,
    )

    return height * width


def _extract_required_font_height(
    scan_record: Dict[str, Any],
) -> float:
    font_audit = scan_record.get("font_audit") or {}

    try:
        return float(
            font_audit.get("required_mm", 1.0)
        )
    except (TypeError, ValueError):
        return 1.0


def _normalise_severity(
    severity: Any,
) -> str:
    value = str(severity or "").upper()

    if value in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
        return value

    # Existing scan results do not consistently provide severity.
    # Use HIGH as the conservative database default.
    return "HIGH"


def _make_violation_code(
    violation: Dict[str, Any],
    index: int,
) -> str:
    explicit_code = violation.get("code")

    if explicit_code:
        return str(explicit_code)[:100]

    rule = str(
        violation.get("rule")
        or "VIOLATION"
    )

    # Produce a deterministic, readable code without relying on
    # database-generated IDs.
    cleaned = "".join(
        character
        if character.isalnum()
        else "_"
        for character in rule.upper()
    )

    return f"{cleaned[:85]}_{index + 1}"