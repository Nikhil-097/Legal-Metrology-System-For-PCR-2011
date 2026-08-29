from datetime import datetime, timezone
import html
from fastapi import APIRouter, HTTPException, Query, Response, status
from app.api.v1.scans import IN_MEMORY_SCAN_DB

router = APIRouter()


@router.get("/show-cause-notice/{scan_id}")
async def generate_show_cause_notice(
    scan_id: str,
    format: str = Query("json", pattern="^(json|html)$")
):
    """
    Generates a statutory Show-Cause Legal Notice under Rule 32 of Legal Metrology Rules, 2011.
    """
    scan = next((s for s in IN_MEMORY_SCAN_DB if s["scan_id"] == scan_id), None)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")

    if scan.get("is_compliant", False):
        return {
            "status": "not_applicable",
            "message": "Product is compliant with Legal Metrology Rules, 2011. No show-cause notice required."
        }

    violations_text = "".join(
        f"<li><strong>{html.escape(str(v.get('rule', 'Rule')))} ({html.escape(str(v.get('code', 'VIOLATION')))}):</strong> "
        f"{html.escape(str(v.get('detail', '')))}</li>"
        for v in scan.get("violations", [])
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Show Cause Notice - Legal Metrology</title>
    <style>
        body {{ font-family: 'Helvetica', Arial, sans-serif; padding: 40px; color: #1a202c; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 15px; }}
        .header h2 {{ margin: 0; font-size: 20px; }}
        .header h3 {{ margin: 5px 0; font-size: 15px; color: #4a5568; }}
        .title {{ font-size: 15px; font-weight: bold; text-transform: uppercase; margin-top: 12px; }}
        .meta-table {{ width: 100%; margin: 20px 0; border-collapse: collapse; }}
        .meta-table td {{ padding: 6px 0; font-size: 14px; }}
        .violations-box {{ background: #fff5f5; border-left: 4px solid #e53e3e; padding: 15px; margin: 20px 0; }}
        .violations-box ul {{ margin: 0; padding-left: 20px; }}
        .violations-box li {{ margin-bottom: 6px; }}
        .footer {{ margin-top: 50px; text-align: right; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>DEPARTMENT OF CONSUMER AFFAIRS</h2>
        <h3>LEGAL METROLOGY DIVISION — ENFORCEMENT WING</h3>
        <div class="title">NOTICE UNDER SECTION 15 OF THE LEGAL METROLOGY ACT, 2009 READ WITH RULE 32</div>
    </div>

    <table class="meta-table">
        <tr>
            <td><strong>Notice ID:</strong> SCN-{html.escape(str(scan['scan_id'][:8])).upper()}</td>
            <td><strong>Date:</strong> {datetime.now(timezone.utc).strftime('%d-%m-%Y')}</td>
        </tr>
        <tr>
            <td><strong>Product / Commodity:</strong> {html.escape(str(scan.get('commodity_name', 'N/A')))}</td>
            <td><strong>Brand:</strong> {html.escape(str(scan.get('brand_name', 'N/A')))}</td>
        </tr>
        <tr>
            <td><strong>Inspecting Officer:</strong> {html.escape(str(scan.get('inspector_id', 'INSP-AUTO')))}</td>
            <td><strong>Compliance Score:</strong> {scan.get('compliance_score', 0)}%</td>
        </tr>
    </table>

    <p>WHEREAS, an inspection of the commodity packaged by your establishment was conducted through digital scanning and automated statutory verification.</p>

    <p>WHEREAS, the analysis revealed prima-facie non-compliances under the Legal Metrology (Packaged Commodities) Rules, 2011 as listed below:</p>

    <div class="violations-box">
        <ul>{violations_text}</ul>
    </div>

    <p>NOW THEREFORE, you are hereby called upon to show cause within <strong>15 days</strong> from the receipt of this notice why appropriate penal proceedings under Section 36 of the Legal Metrology Act, 2009 should not be initiated against your establishment.</p>

    <div class="footer">
        <p><strong>Authorized Enforcement Officer</strong><br>Department of Consumer Affairs</p>
    </div>
</body>
</html>"""

    if format == "html":
        return Response(content=html_content, media_type="text/html")

    return {
        "notice_id": f"SCN-{scan['scan_id'][:8].upper()}",
        "date_issued": datetime.now(timezone.utc).isoformat(),
        "scan_id": scan_id,
        "brand_name": scan.get("brand_name"),
        "violations": scan.get("violations", []),
        "statutory_act": "Legal Metrology Act 2009 & Packaged Commodities Rules 2011",
        "action_required": "Submit reply within 15 days of notice issuance"
    }


@router.get("/summary/{scan_id}")
async def get_scan_report_json(scan_id: str):
    """Provides complete JSON audit report suitable for downstream PDF generation."""
    scan = next((s for s in IN_MEMORY_SCAN_DB if s["scan_id"] == scan_id), None)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")
    return {"status": "success", "report": scan}