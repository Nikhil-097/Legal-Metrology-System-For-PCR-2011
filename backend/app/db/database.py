import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "legal_metrology.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY,
            filename TEXT,
            product_name TEXT,
            brand_name TEXT,
            category TEXT,
            timestamp TEXT,
            compliance_score REAL,
            status TEXT,
            is_compliant INTEGER,
            pdp_surface TEXT,
            declarations TEXT,
            violations TEXT,
            barcode_data TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_scan(scan_dict: Dict[str, Any]):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO scans (
            scan_id, filename, product_name, brand_name, category,
            timestamp, compliance_score, status, is_compliant,
            pdp_surface, declarations, violations, barcode_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        scan_dict["scan_id"],
        scan_dict.get("filename", ""),
        scan_dict.get("product_name", "Packaged Product"),
        scan_dict.get("brand_name", "Unknown Brand"),
        scan_dict.get("category", "Food"),
        scan_dict.get("timestamp", ""),
        scan_dict.get("compliance_score", 100),
        scan_dict.get("status", "COMPLIANT"),
        1 if scan_dict.get("is_compliant") else 0,
        scan_dict.get("pdp_surface", ""),
        json.dumps(scan_dict.get("declarations", {})),
        json.dumps(scan_dict.get("violations", [])),
        json.dumps(scan_dict.get("barcode_data", {}))
    ))
    conn.commit()
    conn.close()

def get_all_scans() -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        results.append({
            "scan_id": r["scan_id"],
            "id": r["scan_id"],
            "filename": r["filename"],
            "product_name": r["product_name"],
            "brand_name": r["brand_name"],
            "category": r["category"],
            "timestamp": r["timestamp"],
            "compliance_score": r["compliance_score"],
            "score": r["compliance_score"],
            "status": r["status"],
            "is_compliant": bool(r["is_compliant"]),
            "pdp_surface": r["pdp_surface"],
            "declarations": json.loads(r["declarations"]) if r["declarations"] else {},
            "violations": json.loads(r["violations"]) if r["violations"] else [],
            "barcode_data": json.loads(r["barcode_data"]) if r["barcode_data"] else {}
        })
    conn.close()
    return results

def get_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "scan_id": row["scan_id"],
        "id": row["scan_id"],
        "filename": row["filename"],
        "product_name": row["product_name"],
        "brand_name": row["brand_name"],
        "category": row["category"],
        "timestamp": row["timestamp"],
        "compliance_score": row["compliance_score"],
        "score": row["compliance_score"],
        "status": row["status"],
        "is_compliant": bool(row["is_compliant"]),
        "pdp_surface": row["pdp_surface"],
        "declarations": json.loads(row["declarations"]) if row["declarations"] else {},
        "violations": json.loads(row["violations"]) if row["violations"] else [],
        "barcode_data": json.loads(row["barcode_data"]) if row["barcode_data"] else {}
    }