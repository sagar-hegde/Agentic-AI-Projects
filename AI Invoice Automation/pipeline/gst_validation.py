"""
gst_validation.py
------------------
The "GST Validation" stage from the dashboard. Checks GSTIN format,
valid GST rate slab, and (simulated) GSTN portal match — mirroring
what a real integration with the GST Network / e-invoice API would do.
"""

import re

GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z0-9]{10}[A-Z0-9]{1}[A-Z0-9]{1}$", re.IGNORECASE)
VALID_GST_RATES = {0, 5, 12, 18, 28}


def validate(invoice: dict) -> dict:
    issues = []

    gstin = invoice.get("vendor_gstin", "")
    if not GSTIN_PATTERN.match(gstin):
        issues.append("invalid_gstin_format")

    rate = invoice.get("gst_rate")
    try:
        rate = int(rate)
        if rate not in VALID_GST_RATES:
            issues.append(f"unrecognized_gst_rate:{rate}")
    except (TypeError, ValueError):
        issues.append("missing_gst_rate")

    # Simulated GSTN portal cross-check (state code prefix sanity check)
    state_code = gstin[:2] if len(gstin) >= 2 else ""
    if not state_code.isdigit() or not (1 <= int(state_code or 0) <= 38):
        issues.append("invalid_state_code")

    return {
        "gst_valid": len(issues) == 0,
        "gst_issues": issues,
    }
