from services.scan_repository import save_scan, get_all_scans, get_scan


TEST_SCAN = {
    "scan_id": "SCN-DBTEST1",
    "id": "SCN-DBTEST1",
    "filename": "database_test.jpg",
    "product_name": "Test Biscuit",
    "brand_name": "Test Brand",
    "category": "Food",
    "compliance_score": 82,
    "score": 82,
    "is_compliant": True,
    "status": "WARNING",
    "pdp_surface": "150.0 cm² (Rectangular)",
    "declarations": {
        "commodity_name": "Test Biscuit",
        "brand_name": "Test Brand",
        "net_quantity": "100 g",
        "mrp": "₹50",
        "country_of_origin": "India",
    },
    "violations": [
        {
            "rule": "Rule 6 Statutory Advisory",
            "detail": "Declaration 'Brand Name' is missing or not clearly indicated.",
            "severity": "MEDIUM",
        }
    ],
    "barcode_data": {
        "detected": True,
        "code": "8901234567890",
        "origin_verified": "MATCH",
    },
    "consumer_care": {
        "is_fully_compliant": True,
    },
    "bounding_boxes": {},
    "font_audit": {
        "required_mm": 1.0,
        "detected_mm": 1.5,
        "compliant": True,
    },
    "usp_math": {
        "verified": True,
        "expected": "₹0.50/g",
    },
}


if __name__ == "__main__":
    print("Saving test scan...")

    saved = save_scan(TEST_SCAN)

    print("Saved:")
    print(saved)

    print("\nFetching by ID...")

    fetched = get_scan("SCN-DBTEST1")

    print(fetched)

    print("\nFetching history...")

    history = get_all_scans()

    print(f"Total scans: {len(history)}")

    assert fetched is not None
    assert fetched["scan_id"] == "SCN-DBTEST1"
    assert fetched["product_name"] == "Test Biscuit"
    assert len(fetched["violations"]) == 1

    print("\nDATABASE REPOSITORY TEST PASSED")