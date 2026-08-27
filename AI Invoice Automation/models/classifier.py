"""
classifier.py
--------------
The "Classification" stage from the dashboard. Trains a TF-IDF +
Logistic Regression model on invoice line-item text to predict the
invoice category, and returns a calibrated confidence score.

Swap-in point: replace TfidfVectorizer + LogisticRegression with a
transformer (e.g. BERT via PyTorch/HuggingFace) for production-grade
accuracy without changing the pipeline interface — predict() still
returns (label, confidence).
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH = os.path.join(os.path.dirname(__file__), "invoice_classifier.joblib")


class InvoiceClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, C=8.0)),
        ])
        self.is_trained = False

    def train(self, csv_path="data/invoices.csv", test_size=0.2, verbose=True):
        df = pd.read_csv(csv_path)
        X = df["line_item_text"]
        y = df["category"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        self.pipeline.fit(X_train, y_train)
        self.is_trained = True

        if verbose:
            preds = self.pipeline.predict(X_test)
            print("=== Classification report (held-out test set) ===")
            print(classification_report(y_test, preds))

        return self

    def predict(self, text: str):
        """Returns (predicted_category, confidence_score 0-1)."""
        if not self.is_trained:
            raise RuntimeError("Model not trained/loaded. Call train() or load().")

        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        best_idx = proba.argmax()
        return classes[best_idx], float(proba[best_idx])

    def save(self, path=MODEL_PATH):
        joblib.dump(self.pipeline, path)
        print(f"Model saved -> {path}")

    def load(self, path=MODEL_PATH):
        self.pipeline = joblib.load(path)
        self.is_trained = True
        return self


if __name__ == "__main__":
    clf = InvoiceClassifier()
    clf.train()
    clf.save()

    sample = "limestone consignment delivery - Shree Minerals Ltd"
    label, conf = clf.predict(sample)
    print(f"\nSample: '{sample}'\nPredicted: {label}  (confidence {conf:.1%})")
