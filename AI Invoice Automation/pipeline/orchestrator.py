"""
orchestrator.py
-----------------
Runs every invoice through the full flow shown on the dashboard:

    Split -> Classification -> OCR & Extraction -> PO Matching ->
    GST Validation -> Duplicate Detection -> Business Rules ->
        -> Touchless -> ERP Posting
        -> Human Review -> (approve/correct) -> ERP Posting
"""

import time
from pipeline.ocr_extraction import extract
from pipeline.po_matching import POMatcher
from pipeline.gst_validation import validate as validate_gst
from pipeline.duplicate_detection import DuplicateDetector
from pipeline.business_rules import evaluate as evaluate_rules


class InvoicePipeline:
    def __init__(self, classifier):
        self.classifier = classifier
        self.po_matcher = POMatcher()
        self.dup_detector = DuplicateDetector()

    def run_one(self, raw_invoice: dict) -> dict:
        t0 = time.perf_counter()

        # 1. OCR & Extraction
        extraction = extract(raw_invoice)

        # 2. Classification
        category, confidence = self.classifier.predict(extraction["line_item_text"])

        # 3. PO Matching
        po_result = self.po_matcher.match(extraction)

        # 4. GST Validation
        gst_result = validate_gst(extraction)

        # 5. Duplicate Detection
        dup_result = self.dup_detector.check(extraction)

        # 6. Business Rules -> routing decision
        decision = evaluate_rules(extraction, confidence, extraction, po_result, gst_result, dup_result)

        elapsed = time.perf_counter() - t0

        return {
            "invoice_no": extraction["invoice_no"],
            "vendor_name": extraction["vendor_name"],
            "amount": extraction["amount"],
            "predicted_category": category,
            "classification_confidence": round(confidence, 4),
            "extraction_ok": extraction["extraction_ok"],
            "po_match": po_result["po_match"],
            "gst_valid": gst_result["gst_valid"],
            "is_duplicate": dup_result["is_duplicate"],
            "route": decision["route"],
            "reasons": decision["reasons"],
            "process_time_sec": round(elapsed, 4),
        }

    def run_batch(self, invoices: list) -> list:
        return [self.run_one(inv) for inv in invoices]


def summarize(results: list) -> dict:
    """Produces the dashboard-style stat block (touchless %, AI confidence, etc.)"""
    n = len(results)
    if n == 0:
        return {}

    touchless = sum(1 for r in results if r["route"] == "touchless")
    human_review = n - touchless
    avg_conf = sum(r["classification_confidence"] for r in results) / n
    avg_time = sum(r["process_time_sec"] for r in results) / n

    return {
        "invoices_processed": n,
        "touchless_pct": round(100 * touchless / n, 1),
        "human_review_pct": round(100 * human_review / n, 1),
        "avg_ai_confidence_pct": round(avg_conf * 100, 1),
        "avg_process_time_sec": round(avg_time, 3),
    }
