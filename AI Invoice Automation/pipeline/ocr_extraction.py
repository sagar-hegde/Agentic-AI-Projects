"""
ocr_extraction.py
------------------
The "OCR & Extraction" stage from the dashboard.

In this demo, invoices already arrive as structured rows (simulating a
document already OCR'd by an engine like Tesseract / AWS Textract /
Azure Form Recognizer). extract() is written so it's a drop-in seam:
point it at real OCR output later without touching the rest of the
pipeline.
"""

import re


REQUIRED_FIELDS = ["invoice_no", "invoice_date", "vendor_name", "vendor_gstin", "amount"]

GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z0-9]{10}[A-Z0-9]{1}[A-Z0-9]{1}$", re.IGNORECASE)


def extract(raw_invoice: dict) -> dict:
    """
    Normalizes/validates fields pulled off the document.
    Returns a dict with the extracted fields plus an 'extraction_ok' flag
    and any field-level issues found.
    """
    issues = []

    for field in REQUIRED_FIELDS:
        value = raw_invoice.get(field)
        if value is None or str(value).strip() == "":
            issues.append(f"missing_field:{field}")

    gstin = str(raw_invoice.get("vendor_gstin", "")).strip()
    if gstin and not GSTIN_PATTERN.match(gstin):
        issues.append("invalid_gstin_format")

    try:
        amount = float(raw_invoice.get("amount", 0))
        if amount <= 0:
            issues.append("non_positive_amount")
    except (TypeError, ValueError):
        issues.append("unparseable_amount")
        amount = 0.0

    extracted = {
        "invoice_no": str(raw_invoice.get("invoice_no", "")).strip(),
        "invoice_date": str(raw_invoice.get("invoice_date", "")).strip(),
        "vendor_name": str(raw_invoice.get("vendor_name", "")).strip(),
        "vendor_gstin": gstin,
        "po_number": str(raw_invoice.get("po_number", "")).strip(),
        "amount": amount,
        "gst_rate": raw_invoice.get("gst_rate"),
        "line_item_text": raw_invoice.get("line_item_text", ""),
        "extraction_ok": len(issues) == 0,
        "extraction_issues": issues,
    }
    return extracted
