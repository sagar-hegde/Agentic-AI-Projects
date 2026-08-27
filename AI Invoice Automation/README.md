# AI Invoice Automation — Accounts Payable (Cement Division)

A Python implementation of the invoice-automation pipeline shown on the
dashboard: **Split → Classification → OCR & Extraction → PO Matching →
GST Validation → Duplicate Detection → Business Rules → ERP Posting /
Human Review.**

## What it does

1. **Classification** (`models/classifier.py`) — a TF-IDF + Logistic
   Regression model reads the invoice's line-item text and predicts its
   category (Raw Material, Logistics, Utility, Maintenance & Spares,
   Professional Services, Packaging), along with a confidence score.
   This is the seam to swap in a transformer/BERT model later — the
   `predict()` interface stays the same.
2. **OCR & Extraction** (`pipeline/ocr_extraction.py`) — validates and
   normalizes the fields a real OCR engine (Tesseract/Textract/Form
   Recognizer) would return.
3. **PO Matching** (`pipeline/po_matching.py`) — 2-way match against a
   (simulated) ERP purchase-order table: vendor + amount within
   tolerance.
4. **GST Validation** (`pipeline/gst_validation.py`) — GSTIN format,
   valid tax slab, and a simulated GSTN portal cross-check.
5. **Duplicate Detection** (`pipeline/duplicate_detection.py`) — exact
   and near-duplicate detection (vendor + amount + date proximity).
6. **Business Rules** (`pipeline/business_rules.py`) — combines every
   upstream signal into a single **touchless vs. human review**
   decision, the same split the dashboard shows as 68% / 32%.
7. **Orchestrator** (`pipeline/orchestrator.py`) — runs every invoice
   through the full flow and produces the dashboard-style summary
   stats (touchless %, AI confidence, avg process time).

## Project structure

```
ai_invoice_automation/
├── main.py                      # entry point — trains model, runs pipeline, prints dashboard
├── requirements.txt
├── data/
│   └── generate_sample_data.py  # synthetic invoice dataset generator
├── models/
│   └── classifier.py            # ML classification stage
└── pipeline/
    ├── ocr_extraction.py
    ├── po_matching.py
    ├── gst_validation.py
    ├── duplicate_detection.py
    ├── business_rules.py
    └── orchestrator.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

This will:
- Generate a synthetic dataset of ~250 invoices (`data/invoices.csv`) if
  one doesn't exist yet
- Train the classifier and print a held-out accuracy report
- Run the full pipeline over every invoice
- Print a console "dashboard" (invoices processed, touchless %, human
  review %, avg AI confidence, avg process time) plus sample routed
  invoices

## Tuning the touchless/human-review split

The routing decision lives in `pipeline/business_rules.py`:

```python
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.90   # raise/lower to shift the split
HIGH_VALUE_AMOUNT_THRESHOLD = 500000         # invoices above this always get reviewed
```

## Going to production

- Replace `data/generate_sample_data.py` with a real historical-invoice
  export to train on.
- Replace `pipeline/ocr_extraction.py`'s pass-through with a real OCR
  call (Tesseract/AWS Textract/Azure Form Recognizer) that outputs the
  same field dict.
- Replace `pipeline/po_matching.py`'s mock table with a live ERP (SAP)
  PO lookup.
- Swap `models/classifier.py`'s TF-IDF+LogisticRegression for a
  fine-tuned BERT/DistilBERT model if you need higher accuracy on
  messier real-world text — `predict()` keeps the same
  `(category, confidence)` return shape, so nothing else changes.
