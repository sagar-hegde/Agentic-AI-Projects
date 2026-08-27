"""
main.py
--------
Entry point. Generates sample data (if needed), trains/loads the
classifier, runs the full AP automation pipeline over a batch of
invoices, and prints a dashboard-style summary in the console
(mirroring the "AI Invoice Automation" screen).

Usage:
    python main.py
"""

import os
import csv
import sys

sys.path.append(os.path.dirname(__file__))

from data.generate_sample_data import generate
from models.classifier import InvoiceClassifier
from pipeline.orchestrator import InvoicePipeline, summarize

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "invoices.csv")


def load_invoices(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def print_dashboard(stats: dict):
    print("\n" + "=" * 60)
    print("  ADANI | AI INVOICE AUTOMATION — Accounts Payable, Cement Div.")
    print("=" * 60)
    print(f"  Invoices Processed Today : {stats['invoices_processed']}")
    print(f"  Touchless (straight-through) : {stats['touchless_pct']}%")
    print(f"  Human Review (exceptions)    : {stats['human_review_pct']}%")
    print(f"  AI Confidence (avg)          : {stats['avg_ai_confidence_pct']}%")
    print(f"  Avg Process Time             : {stats['avg_process_time_sec']} s")
    print("=" * 60 + "\n")


def main():
    if not os.path.exists(DATA_PATH):
        print("No dataset found — generating synthetic invoices...")
        generate(out_path=DATA_PATH)

    print("Training classifier...")
    clf = InvoiceClassifier()
    clf.train(csv_path=DATA_PATH)
    clf.save()

    print("\nRunning pipeline over full invoice batch...")
    invoices = load_invoices(DATA_PATH)
    pipeline = InvoicePipeline(clf)
    results = pipeline.run_batch(invoices)

    stats = summarize(results)
    print_dashboard(stats)

    print("Sample of flagged invoices (routed to Human Review):\n")
    flagged = [r for r in results if r["route"] == "human_review"][:8]
    for r in flagged:
        print(f"  [{r['invoice_no']}] {r['vendor_name']} | amount={r['amount']:.2f} | "
              f"category={r['predicted_category']} ({r['classification_confidence']:.1%}) | "
              f"reasons={r['reasons']}")

    print("\nSample of touchless invoices (auto-posted to ERP):\n")
    touchless = [r for r in results if r["route"] == "touchless"][:8]
    for r in touchless:
        print(f"  [{r['invoice_no']}] {r['vendor_name']} | amount={r['amount']:.2f} | "
              f"category={r['predicted_category']} ({r['classification_confidence']:.1%}) -> ERP Posted")


if __name__ == "__main__":
    main()
