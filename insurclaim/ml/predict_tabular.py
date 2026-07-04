"""Score a single claim with the trained tabular fraud classifier.

Loads the saved Random Forest pipeline (see ml/train_tabular.py) and returns a
fraud probability in [0, 1] for one claim's structured features. Returns None if
the model has not been trained yet, so callers can degrade gracefully.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from insurclaim.ml.train_tabular import (
    CATEGORICAL_FEATURES,
    MODEL_PATH,
    NUMERIC_FEATURES,
)


@lru_cache(maxsize=1)
def _load_model():
    """Load and cache the saved pipeline once."""
    import joblib

    return joblib.load(MODEL_PATH)


def predict_fraud_tabular(row: dict[str, Any]) -> float | None:
    """Return the fraud probability for one claim's structured features.

    Returns None if the model has not been trained/saved yet.
    """
    if not MODEL_PATH.exists():
        return None

    import pandas as pd

    model = _load_model()
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    # Build a one-row frame with exactly the columns the model was trained on.
    frame = pd.DataFrame([{name: row.get(name) for name in features}])
    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    probability = model.predict_proba(frame)[0][1]  # column 1 = fraud
    return float(probability)
