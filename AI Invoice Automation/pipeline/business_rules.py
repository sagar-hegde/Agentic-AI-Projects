"""
business_rules.py
-------------------
The "Business Rules" stage from the dashboard — the final gate before
deciding "touchless" (straight-through to ERP) vs "human review".

Combines every upstream signal into one decision, similar to the
68% / 32% split shown on the dashboard.
"""

CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.90
HIGH_VALUE_AMOUNT_THRESHOLD = 500000  # invoices above this always get a human look


def evaluate(invoice: dict, classification_conf: float, extraction: dict,
             po_result: dict, gst_result: dict, dup_result: dict) -> dict:
    """
    Returns a decision dict:
        {
          "route": "touchless" | "human_review",
          "reasons": [...]   # why it was flagged, if any
        }
    """
    reasons = []

    if not extraction["extraction_ok"]:
        reasons.append("extraction_incomplete")

    if classification_conf < CLASSIFICATION_CONFIDENCE_THRESHOLD:
        reasons.append("low_classification_confidence")

    if not po_result["po_match"]:
        reasons.append(f"po_mismatch:{po_result['po_match_reason']}")

    if not gst_result["gst_valid"]:
        reasons.append("gst_validation_failed")

    if dup_result["is_duplicate"]:
        reasons.append(f"possible_duplicate:{dup_result['duplicate_type']}")

    if invoice["amount"] >= HIGH_VALUE_AMOUNT_THRESHOLD:
        reasons.append("high_value_invoice")

    route = "human_review" if reasons else "touchless"
    return {"route": route, "reasons": reasons}
