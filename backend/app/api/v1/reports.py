from __future__ import annotations

import io

from fastapi import (
    APIRouter,
    HTTPException,
    Response,
)

from app.services.pdf_generator import (
    generate_statutory_notice_pdf,
)
from services.scan_repository import (
    get_all_scans,
    get_scan,
)


router = APIRouter()


# ============================================================================
# REPORT LIST
# ============================================================================

@router.get("/")
async def list_reports():
    return get_all_scans()


# ============================================================================
# REPORT BY ID
# ============================================================================

@router.get("/{scan_id}")
async def get_report_by_id(
    scan_id: str,
):

    scan = get_scan(
        scan_id
    )

    if not scan:

        raise HTTPException(
            status_code=404,
            detail=(
                "Statutory audit report "
                "not found"
            ),
        )

    return scan


# ============================================================================
# REPORT PDF
# ============================================================================

@router.get("/{scan_id}/pdf")
async def export_report_pdf(
    scan_id: str,
):

    scan = get_scan(
        scan_id
    )

    if not scan:

        raise HTTPException(
            status_code=404,
            detail=(
                "Statutory report "
                "not found"
            ),
        )

    try:

        pdf_buffer = (
            generate_statutory_notice_pdf(
                scan
            )
        )

        if isinstance(
            pdf_buffer,
            io.BytesIO,
        ):

            pdf_bytes = (
                pdf_buffer.getvalue()
            )

        elif isinstance(
            pdf_buffer,
            (bytes, bytearray),
        ):

            pdf_bytes = bytes(
                pdf_buffer
            )

        else:

            raise TypeError(
                "PDF generator returned "
                "an unsupported object."
            )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    (
                        "attachment; "
                        f'filename="Legal_Metrology_Notice_'
                        f'{scan_id}.pdf"'
                    ),
                "Content-Length":
                    str(
                        len(pdf_bytes)
                    ),
            },
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate "
                f"report PDF: {str(exc)}"
            ),
        ) from exc