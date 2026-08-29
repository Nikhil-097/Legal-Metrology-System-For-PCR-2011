import pytest
from app.core.text_parser import StatutoryTextParser
from app.core.pdp_analyzer import PDPAnalyzer


def test_text_parser_compliant_package():
    raw_ocr_tokens = [
        {"text": "BRITANNIA GOOD DAY BISCUITS"},
        {"text": "Net Wt: 250 g"},
        {"text": "MRP: Rs. 45.00 incl. of all taxes"},
        {"text": "USP: Rs. 0.18 per g"},
        {"text": "Mfg Date: 05/2026"},
        {"text": "Country of Origin: India"}
    ]
    parsed = StatutoryTextParser.parse_all_declarations(raw_ocr_tokens)

    assert parsed.get("net_quantity") == "250 g"
    assert parsed.get("mrp") == "₹ 45.00"
    assert parsed.get("has_tax_clause") is True
    assert parsed.get("unit_sale_price") == "₹ 0.18 per g"
    assert parsed.get("mfg_date") == "05/2026"
    assert "India" in parsed.get("country_of_origin")


def test_text_parser_flags_non_standard_metric_units():
    raw_ocr_tokens = [
        {"text": "PREMIUM ALMONDS"},
        {"text": "Net Weight: 500 gm"},
        {"text": "MRP: Rs 499.00"}
    ]
    parsed = StatutoryTextParser.parse_all_declarations(raw_ocr_tokens)

    assert "gm" in parsed.get("net_quantity").lower()
    assert parsed.get("has_tax_clause") is False


def test_pdp_area_calculation():
    rect_area = PDPAnalyzer.calculate_pdp_area(
        image_shape=(1000, 800, 3),
        dimensions={"height_cm": 15.0, "width_cm": 10.0},
        pdp_type="rectangular"
    )
    assert rect_area == 150.0

    cyl_area = PDPAnalyzer.calculate_pdp_area(
        image_shape=(1000, 800, 3),
        dimensions={"height_cm": 20.0, "width_cm": 10.0},
        pdp_type="cylindrical"
    )
    assert cyl_area == 80.0


def test_min_font_requirement_lookup():
    font_matrix = [
        {"pdp_area_cm2_min": 0, "pdp_area_cm2_max": 50, "min_font_height_mm_small_pack": 1.0, "min_font_height_mm_large_pack": 1.5},
        {"pdp_area_cm2_min": 50, "pdp_area_cm2_max": 100, "min_font_height_mm_small_pack": 1.5, "min_font_height_mm_large_pack": 2.0},
        {"pdp_area_cm2_min": 100, "pdp_area_cm2_max": 500, "min_font_height_mm_small_pack": 2.5, "min_font_height_mm_large_pack": 4.0},
        {"pdp_area_cm2_min": 500, "pdp_area_cm2_max": None, "min_font_height_mm_small_pack": 4.0, "min_font_height_mm_large_pack": 6.0}
    ]

    font_req_large = PDPAnalyzer.get_min_font_requirement(
        font_matrix=font_matrix,
        pdp_area_cm2=120.0,
        net_quantity=500.0,
        unit="g"
    )
    assert font_req_large == 4.0

    font_req_small = PDPAnalyzer.get_min_font_requirement(
        font_matrix=font_matrix,
        pdp_area_cm2=40.0,
        net_quantity=50.0,
        unit="g"
    )
    assert font_req_small == 1.0