from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.db.database import get_all_scans, get_scan
from app.services.pdf_generator import generate_statutory_notice_pdf

router = APIRouter()

IN_MEMORY_SCAN_DB = []

@router.get("/")
async def list_reports():
    return get_all_scans()

@router.get("/{scan_id}")
async def get_report_by_id(scan_id: str):
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Statutory audit report not found")
    return scan

@router.get("/{scan_id}/pdf")
async def export_report_pdf(scan_id: str):
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Statutory report not found")
    pdf_buffer = generate_statutory_notice_pdf(scan)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Legal_Metrology_Notice_{scan_id}.pdf"}
    )