import re

PIN = re.compile(r"\b[1-9][0-9]{5}\b")
MONEY = re.compile(r"(?:rs\.?|inr)\s*([0-9]+(?:\.[0-9]{1,2})?)", re.I)
QTY = re.compile(
    r"\b([0-9]+(?:\.[0-9]+)?)\s*"
    r"(kgs?|grams?|gms?|gm|g|mg|lit(?:re|er)s?|l|ml|m|cm|mm|"
    r"units?|nos?|numbers?)\b",
    re.I
)
DATE = re.compile(
    r"\b(?:0?[1-9]|1[0-2])\s*[/.-]\s*20\d{2}\b|"
    r"\b20\d{2}\s*[/.-]\s*(?:0?[1-9]|1[0-2])\b"
)
DECLARATION = re.compile(
    r"\b(?:manufactured(?:\s+and\s+packed)?\s+by|manufacturer|"
    r"packed\s+by|packer|imported\s+by)\b\s*[:.-]?\s*(.*)",
    re.I
)
GENERIC_NAME = re.compile(
    r"\b(?:product|commodity|generic|common)\s+name\b\s*[:.-]?\s*(.+)",
    re.I
)

def first(pattern, text):
    match = pattern.search(text)
    return match.group(0).strip() if match else None

def declaration_value(lines: list[str], index: int, value: str):
    """Use a declaration's value, or its following line when it is a heading."""
    value = value.strip(" :.-")
    if value:
        return value
    for line in lines[index + 1:]:
        candidate = line.strip()
        if candidate:
            return candidate
    return None

def extract_fields(text: str):
    lower = text.lower()
    lines = text.splitlines()
    manufacturer = None
    
    for index, line in enumerate(lines):
        match = DECLARATION.search(line)
        if match:
            manufacturer = declaration_value(lines, index, match.group(1))
            break
            
    generic_name = None
    for line in lines:
        match = GENERIC_NAME.search(line)
        if match and match.group(1).strip(" :.-"):
            generic_name = match.group(1).strip(".")
            break
            
    for line in lines:
        if generic_name:
            break
        value = line.strip()
        if manufacturer and value == manufacturer:
            continue
            
        excluded = (
            "mrp", "net qty", "manufact", "packer", "import", "email", "www.",
            "date", "mfg", "pkd", "batch", "address", "marketed", "ltd",
            "limited", "pvt", "private", "llp", "inc",
        )
        if (
            value
            and len(value.split()) <= 8
            and not any(item in value.lower() for item in excluded)
        ):
            generic_name = value
            break

    return {
        "manufacturer_or_packer": manufacturer,
        "generic_name": generic_name,
        "net_quantity": first(QTY, text),
        "mrp": first(MONEY, text),
        "date_or_month_year": first(DATE, text),
        "pincodes": PIN.findall(text),
        "has_tax_inclusive_wording": bool(
            re.search(r"inclusive of all taxes|incl\.?\s*of all taxes", text, re.I)
        ),
        "has_unit_sale_price": bool(
            re.search(
                r"unit\s*sale\s*price|price\s*per\s*(kg|g|l|ml|m|unit|number)",
                text, re.I
            )
        ),
        "has_consumer_care": bool(
            re.search(r"consumer\s*care|customer\s*care|helpline|toll[-]?free", text, re.I)
        ),
        "imported": any(
            keyword in lower
            for keyword in ("imported by", "country of origin", "made in")
        ),
    }