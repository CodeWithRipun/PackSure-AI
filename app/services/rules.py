# Prototype rule catalog for SIH.
# Verify every requirement against the latest official Legal Metrology
# (Packaged Commodities) Rules and amendments before production use.

RULES = [
    (
        "LM-01",
        "Manufacturer / packer / importer details",
        "manufacturer_or_packer",
        "FAIL",
        15,
        "A responsible manufacturer, packer or importer declaration should be identifiable.",
    ),
    (
        "LM-02",
        "Generic / common product name",
        "generic_name",
        "FAIL",
        12,
        "A common or generic commodity name should be identifiable.",
    ),
    (
        "LM-03",
        "Net quantity",
        "net_quantity",
        "FAIL",
        15,
        "Net quantity should be declared using a recognizable unit or number.",
    ),
    (
        "LM-04",
        "MRP / retail sale price",
        "mrp",
        "FAIL",
        15,
        "A recognizable retail sale price / MRP should be present.",
    ),
    (
        "LM-05",
        "Tax-inclusive wording",
        "has_tax_inclusive_wording",
        "FAIL",
        10,
        "The label should indicate that the retail sale price is inclusive of all taxes.",
    ),
    (
        "LM-06",
        "Unit sale price",
        "has_unit_sale_price",
        "WARNING",
        8,
        "Check whether unit sale price is applicable and declared for this package.",
    ),
    (
        "LM-07",
        "Consumer-care details",
        "has_consumer_care",
        "WARNING",
        8,
        "Consumer-care contact information should be checked.",
    ),
]


def evaluate(extracted):
    results = []

    for code, name, field, missing_status, weight, explanation in RULES:
        value = extracted.get(field)

        if value:
            status = "PASS"
            message = "Declaration detected."
            severity = "INFO"
        else:
            status = missing_status
            message = explanation
            severity = missing_status

        results.append(
            {
                "code": code,
                "name": name,
                "status": status,
                "severity": severity,
                "message": message,
                "evidence": str(value) if value else "",
                "weight": weight,
            }
        )

    return results


def score_results(results):
    weighted = [item for item in results if item["weight"] > 0]
    total = sum(item["weight"] for item in weighted)
    earned = sum(
        item["weight"]
        for item in weighted
        if item["status"] == "PASS"
    )

    score = round(earned / total * 100, 1) if total else 0

    if any(item["status"] == "FAIL" for item in results):
        status = "FAIL"
    elif any(item["status"] == "WARNING" for item in results):
        status = "NEEDS_REVIEW"
    else:
        status = "PASS"

    return score, status
