"""Load the fine-tuned fraud classifier and score a claim.

Returns a fraud probability in [0, 1] for a claim narrative. Used as one layer
inside the fraud agent. If the model has not been trained yet, predict_fraud
returns None so the pipeline can continue without it.
"""

from __future__ import annotations

from functools import lru_cache

from insurclaim.ml.train import MODEL_DIR


@lru_cache(maxsize=1)
def _load_model():
    """Load the tokenizer and model once and cache them in memory."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return tokenizer, model, torch


def predict_fraud(text: str) -> float | None:
    """Return the model's fraud probability for a claim narrative.

    Returns None if the model has not been trained/saved yet.
    """
    if not MODEL_DIR.exists():
        return None

    tokenizer, model, torch = _load_model()
    inputs = tokenizer(text, truncation=True, padding=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
        probabilities = torch.softmax(logits, dim=-1)
    # Label 1 is "fraud" (see train.py).
    return float(probabilities[0][1])
