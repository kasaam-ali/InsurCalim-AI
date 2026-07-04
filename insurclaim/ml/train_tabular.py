"""Train a tabular fraud classifier on the real dataset (scikit-learn).

The real dataset is structured/tabular, so a gradient-style ensemble is a better
fit than a text transformer. This trains a class-balanced Random Forest on the
numeric and categorical features and reports precision/recall/F1 plus a confusion
matrix on a held-out split. The model is saved for reuse.

This is the project's classic-ML fraud scorer for structured data; the fine-tuned
DistilBERT (ml/train.py) handles free-text claim narratives instead.

Run as a script:  python -m insurclaim.ml.train_tabular
"""

from __future__ import annotations

from pathlib import Path

from insurclaim.db import repo

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "fraud_tabular.joblib"

# Fraud is rare (~11% of claims), so the default 0.5 cutoff is too conservative
# and misses most fraud. We flag a claim when its fraud probability crosses this
# lower threshold, trading precision for recall (flagged claims go to a human).
DECISION_THRESHOLD = 0.25

NUMERIC_FEATURES = [
    "policy_deductible", "policy_annual_premium", "insured_age",
    "incident_hour_of_the_day", "number_of_vehicles_involved", "bodily_injuries",
    "witnesses", "claim_amount", "total_claim_amount",
]
CATEGORICAL_FEATURES = [
    "policy_state", "insured_sex", "insured_education_level", "insured_occupation",
    "insured_hobbies", "incident_type", "collision_type", "incident_severity",
    "authorities_contacted", "incident_state", "police_report_available",
]


def _load_frame():
    """Load real_claims into a DataFrame with numeric columns coerced."""
    import pandas as pd

    rows = repo.list_real_claims()
    if not rows:
        raise RuntimeError("No real claims found. Run 'python -m insurclaim.data.load_real' first.")

    frame = pd.DataFrame(rows)
    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def train() -> Path:
    """Fit the model, print held-out metrics, and save the pipeline."""
    import joblib
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import (
        average_precision_score,
        classification_report,
        confusion_matrix,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    frame = _load_frame()
    features = frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    labels = frame["is_fraud"].astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced",  # counter the ~75/25 imbalance
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, stratify=labels, random_state=42
    )
    model.fit(x_train, y_train)
    fraud_proba = model.predict_proba(x_test)[:, 1]
    y_pred = (fraud_proba >= DECISION_THRESHOLD).astype(int)

    # Threshold-free quality: how well the model ranks fraud above legit overall.
    print(f"PR-AUC (average precision): {average_precision_score(y_test, fraud_proba):.3f}")
    print(f"ROC-AUC:                    {roc_auc_score(y_test, fraud_proba):.3f}")

    print(f"\nOperating point at threshold {DECISION_THRESHOLD}:")
    print("Confusion matrix (rows = actual, cols = predicted):")
    print(confusion_matrix(y_test, y_pred))
    print(f"\nPrecision: {precision_score(y_test, y_pred, zero_division=0):.3f}")
    print(f"Recall:    {recall_score(y_test, y_pred, zero_division=0):.3f}")
    print("\n" + classification_report(y_test, y_pred, target_names=["legit", "fraud"]))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return MODEL_PATH


if __name__ == "__main__":
    saved_to = train()
    print(f"Tabular fraud classifier saved to {saved_to}")
