from app.services.rules import evaluate, score_results

def test_complete_label():
    data = {
        "manufacturer_or_packer": "ABC Foods",
        "generic_name": "Potato Chips",
        "net_quantity": "100 g",
        "mrp": "150",
        "has_tax_inclusive_wording": True,
        "has_unit_sale_price": True,
        "has_consumer_care": True,
    }
    results = evaluate(data)
    score, status = score_results(results)
    
    assert score == 100.0
    assert status == "PASS"

def test_missing_mrp():
    data = {
        "manufacturer_or_packer": "ABC Foods",
        "generic_name": "Potato Chips",
        "net_quantity": "100 g",
        "mrp": None,
        "has_tax_inclusive_wording": True,
        "has_unit_sale_price": True,
        "has_consumer_care": True,
    }
    results = evaluate(data)
    score, status = score_results(results)
    
    assert status == "FAIL"
    assert score < 100

def test_ocr_warning_does_not_change_compliance_score():
    data = {
        "manufacturer_or_packer": "ABC Foods",
        "generic_name": "Potato Chips",
        "net_quantity": "100 g",
        "mrp": "450",
        "has_tax_inclusive_wording": True,
        "has_unit_sale_price": True,
        "has_consumer_care": True,
    }
    results = evaluate(data)
    results.append(
        {
            "code": "OCR-01",
            "name": "OCR quality",
            "status": "WARNING",
            "severity": "WARNING",
            "message": "Manual review recommended.",
            "evidence": "",
            "weight": 0,
        }
    )
    score, status = score_results(results)
    
    assert score == 100.0
    assert status == "NEEDS REVIEW"