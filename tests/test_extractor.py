from app.services.extractor import extract_fields

def test_extracts_label_declarations_and_common_units():
    text = """Product Name: Spiced Potato Chips
Manufactured by: ABC Foods Private Limited
Net Qty: 100 grams
MRP: Rs. 50 (inclusive of all taxes)
Packed: 08/2026
Consumer Care: 1800-000-000
Price per kg: Rs. 500
Address: Bengaluru 560001"""
    
    fields = extract_fields(text)
    
    assert fields["generic_name"] == "Spiced Potato Chips"
    assert fields["manufacturer_or_packer"] == "ABC Foods Private Limited"
    assert fields["net_quantity"] == "100 grams"
    assert fields["mrp"] == "Rs. 50"
    assert fields["date_or_month_year"] == "08/2026"
    assert fields["pincodes"] == ["560001"]
    assert fields["has_tax_inclusive_wording"] is True
    assert fields["has_unit_sale_price"] is True
    assert fields["has_consumer_care"] is True

def test_uses_following_line_when_declaration_is_a_heading():
    fields = extract_fields("Manufacturer: \nABC Foods\nPotato Chips")
    assert fields["manufacturer_or_packer"] == "ABC Foods"