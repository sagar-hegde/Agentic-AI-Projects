"""
generate_sample_data.py
------------------------
Creates a synthetic invoice dataset for a cement-division Accounts Payable
scenario (Adani-style AP automation). Each row simulates one invoice with
free-text fields an OCR engine would typically extract, plus the ground
truth category used to train the classifier.

Run directly to regenerate data/invoices.csv:
    python data/generate_sample_data.py
"""

import random
import csv
import os
import uuid
from datetime import datetime, timedelta

random.seed(42)

VENDORS = {
    "Raw Material": ["Shree Minerals Ltd", "Rajputana Aggregates", "Gujarat Limestone Co",
                      "Bharat Gypsum Supplies", "Konkan Silica Traders"],
    "Logistics": ["BlueDart Freight", "Adani Logistics", "National Transport Corp",
                  "Speedway Carriers", "Indus Rail Cargo"],
    "Utility": ["Adani Power Distribution", "Gujarat Gas Ltd", "State Electricity Board",
                "AquaFlow Water Supply", "GreenGrid Energy"],
    "Maintenance & Spares": ["Precision Bearings Pvt Ltd", "KilnTech Spares", "Larsen Engg Works",
                              "MotorTech Industries", "Conveyor Systems India"],
    "Professional Services": ["Deloitte Advisory", "KPMG Consulting", "SafetyFirst Auditors",
                               "LegalEdge Associates", "EnviroCheck Labs"],
    "Packaging": ["PolyPack Industries", "Jute Bags Co", "Sundar Packaging Solutions",
                  "Crown Sack Manufacturers", "EcoWrap Pvt Ltd"],
}

ITEM_PHRASES = {
    "Raw Material": ["limestone supply", "gypsum consignment", "silica sand delivery",
                      "fly ash procurement", "clinker raw material batch"],
    "Logistics": ["freight charges for clinker transport", "road transportation of cement bags",
                  "rail freight for raw material", "container handling charges", "fuel surcharge on transport"],
    "Utility": ["electricity consumption charges", "industrial water supply bill",
                "natural gas supply for kiln", "power distribution charges", "diesel generator fuel bill"],
    "Maintenance & Spares": ["kiln bearing replacement", "conveyor belt spare parts",
                              "motor overhaul service", "crusher liner replacement", "preventive maintenance service"],
    "Professional Services": ["statutory audit fees", "safety compliance audit",
                               "legal advisory retainer", "environmental impact assessment", "tax consulting services"],
    "Packaging": ["HDPE cement bags supply", "jute packaging material", "laminated pouches order",
                  "printed sack bundles", "poly liner rolls"],
}

GST_RATES = [5, 12, 18, 28]


def random_date():
    start = datetime(2026, 6, 1)
    return (start + timedelta(days=random.randint(0, 85))).strftime("%Y-%m-%d")


def make_invoice(category, force_duplicate_of=None):
    vendor = random.choice(VENDORS[category])
    phrase = random.choice(ITEM_PHRASES[category])
    amount = round(random.uniform(8000, 950000), 2)
    gst_rate = random.choice(GST_RATES)
    invoice_no = force_duplicate_of["invoice_no"] if force_duplicate_of else f"INV-{uuid.uuid4().hex[:8].upper()}"
    gstin = force_duplicate_of["vendor_gstin"] if force_duplicate_of else f"24{random.randint(10**9,10**10-1)}Z{random.randint(1,9)}"
    po_number = f"PO-{random.randint(100000,999999)}" if random.random() > 0.15 else ""

    return {
        "invoice_no": invoice_no,
        "invoice_date": force_duplicate_of["invoice_date"] if force_duplicate_of else random_date(),
        "vendor_name": vendor,
        "vendor_gstin": gstin,
        "po_number": po_number,
        "line_item_text": f"{phrase} - {vendor}",
        "amount": force_duplicate_of["amount"] if force_duplicate_of else amount,
        "gst_rate": gst_rate,
        "category": category,
    }


def generate(n_per_category=40, duplicate_rate=0.05, out_path="data/invoices.csv"):
    rows = []
    for category in VENDORS:
        for _ in range(n_per_category):
            rows.append(make_invoice(category))

    # Inject a few duplicate invoices (same invoice_no + vendor_gstin + amount)
    n_dupes = int(len(rows) * duplicate_rate)
    for _ in range(n_dupes):
        original = random.choice(rows)
        rows.append(make_invoice(original["category"], force_duplicate_of=original))

    random.shuffle(rows)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} invoices ({n_dupes} duplicates injected) -> {out_path}")
    return out_path


if __name__ == "__main__":
    generate()
