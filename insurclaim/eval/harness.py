"""Evaluation harness.

Runs the pipeline over every labeled claim, turns the risk score into a fraud /
legit prediction, and compares it against the ground-truth label. Prints
precision, recall, and a confusion matrix - the project's success metric.

Run as a script:  python -m insurclaim.eval.harness
"""

from __future__ import annotations

from insurclaim.db import repo
from insurclaim.graph import run_claim

# Risk score at or above this counts as a "fraud" prediction.
DECISION_THRESHOLD = 50


def _predict(claim_id: int) -> int:
    """Run the pipeline on a claim and return 1 (fraud) or 0 (legit)."""
    claim = repo.get_claim(claim_id)
    final_state = run_claim({"claim": claim})
    risk_score = final_state.get("report", {}).get("risk_score", 0)
    return 1 if risk_score >= DECISION_THRESHOLD else 0


def evaluate() -> None:
    """Score every labeled claim and print precision/recall/confusion."""
    from sklearn.metrics import (
        classification_report,
        confusion_matrix,
        precision_score,
        recall_score,
    )

    claims = repo.list_labeled_claims()
    if not claims:
        raise SystemExit("No labeled claims found. Generate synthetic data first.")

    y_true = [1 if c["is_fraud"] else 0 for c in claims]
    y_pred = [_predict(c["id"]) for c in claims]

    print("Confusion matrix (rows = actual, cols = predicted):")
    print(confusion_matrix(y_true, y_pred))
    print(f"\nPrecision: {precision_score(y_true, y_pred, zero_division=0):.3f}")
    print(f"Recall:    {recall_score(y_true, y_pred, zero_division=0):.3f}")
    print("\n" + classification_report(y_true, y_pred, target_names=["legit", "fraud"]))


if __name__ == "__main__":
    evaluate()
