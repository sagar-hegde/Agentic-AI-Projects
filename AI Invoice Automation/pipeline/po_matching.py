"""
po_matching.py
---------------
The "PO Matching" stage from the dashboard. Performs a 2-way match
between the invoice and an (simulated) open Purchase Order table:
PO exists, vendor matches, and invoice amount is within tolerance
of the PO value.
"""

import random

AMOUNT_TOLERANCE_PCT = 0.05  # 5% variance allowed


def _mock_po_table():
    """Simulates an ERP PO master. In production, swap this for a live
    SAP/ERP lookup (e.g. via RFC/REST connector)."""
    return {}


class POMatcher:
    def __init__(self, po_table=None):
        self.po_table = po_table or _mock_po_table()

    def match(self, invoice: dict) -> dict:
        po_number = invoice.get("po_number", "")

        if not po_number:
            return {"po_match": False, "po_match_reason": "no_po_reference_on_invoice"}

        po_record = self.po_table.get(po_number)
        if po_record is None:
            # Demo fallback: simulate ERP PO lookup succeeding ~85% of the time
            # when a PO number is present, with amount variance.
            if random.random() < 0.85:
                variance = random.uniform(-0.03, 0.03)
                po_record = {
                    "vendor_name": invoice["vendor_name"],
                    "po_amount": round(invoice["amount"] * (1 - variance), 2),
                }
            else:
                return {"po_match": False, "po_match_reason": "po_not_found_in_erp"}

        vendor_ok = po_record["vendor_name"].strip().lower() == invoice["vendor_name"].strip().lower()
        amount_diff_pct = abs(invoice["amount"] - po_record["po_amount"]) / max(po_record["po_amount"], 1)
        amount_ok = amount_diff_pct <= AMOUNT_TOLERANCE_PCT

        if vendor_ok and amount_ok:
            return {"po_match": True, "po_match_reason": "matched", "po_amount": po_record["po_amount"]}

        reason = []
        if not vendor_ok:
            reason.append("vendor_mismatch")
        if not amount_ok:
            reason.append(f"amount_variance_{amount_diff_pct:.1%}")

        return {"po_match": False, "po_match_reason": ";".join(reason), "po_amount": po_record["po_amount"]}
