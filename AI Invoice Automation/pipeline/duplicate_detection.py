"""
duplicate_detection.py
-----------------------
The "Duplicate Detection" stage from the dashboard. Flags invoices
that look like a repeat submission using an exact-match key
(vendor GSTIN + invoice number + amount) plus a fuzzy near-duplicate
check (same vendor + amount within 1% + date within 3 days) to catch
re-numbered resubmissions.
"""

from datetime import datetime


class DuplicateDetector:
    def __init__(self):
        self._seen_exact = set()
        self._seen_fuzzy = []  # list of (vendor_gstin, amount, date)

    def _exact_key(self, invoice):
        return (invoice["vendor_gstin"], invoice["invoice_no"], round(invoice["amount"], 2))

    def check(self, invoice: dict) -> dict:
        exact_key = self._exact_key(invoice)
        if exact_key in self._seen_exact:
            return {"is_duplicate": True, "duplicate_type": "exact_match"}

        try:
            inv_date = datetime.strptime(invoice["invoice_date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            inv_date = None

        for gstin, amount, date in self._seen_fuzzy:
            same_vendor = gstin == invoice["vendor_gstin"]
            amount_close = abs(amount - invoice["amount"]) / max(amount, 1) <= 0.01
            date_close = (
                inv_date is not None and date is not None and abs((inv_date - date).days) <= 3
            )
            if same_vendor and amount_close and date_close:
                return {"is_duplicate": True, "duplicate_type": "near_duplicate"}

        # Not a duplicate — register it as seen for future checks
        self._seen_exact.add(exact_key)
        self._seen_fuzzy.append((invoice["vendor_gstin"], invoice["amount"], inv_date))
        return {"is_duplicate": False, "duplicate_type": None}
