"""Command-line entry point for InsurClaim AI.

Runs the full agent pipeline on a single claim and prints the resulting report.

Examples:
    python -m insurclaim.main --claim 1
    python -m insurclaim.main --text "On 12 May the insured rear-ended a car..."
"""

from __future__ import annotations

import argparse
import json

from insurclaim.db import repo
from insurclaim.graph import run_claim


def _run_by_id(claim_id: int) -> dict:
    """Load a claim from the database and run the pipeline on it."""
    claim = repo.get_claim(claim_id)
    if claim is None:
        raise SystemExit(f"No claim found with id {claim_id}.")
    final_state = run_claim({"claim": claim})
    # Persist the pipeline's decision back onto the claim record.
    report = final_state.get("report", {})
    repo.update_claim_result(
        claim_id,
        risk_score=report.get("risk_score", 0),
        recommended_action=report.get("recommended_action", ""),
    )
    return final_state


def _run_by_text(text: str) -> dict:
    """Run the pipeline on raw claim text (no database needed)."""
    return run_claim({"raw_documents": text})


def _run_real_claim(claim_id: int) -> dict:
    """Score a real (structured) claim with the tabular fraud classifier."""
    from insurclaim.ml.predict_tabular import predict_fraud_tabular
    from insurclaim.ml.train_tabular import DECISION_THRESHOLD

    claim = repo.get_real_claim(claim_id)
    if claim is None:
        raise SystemExit(f"No real claim found with id {claim_id}.")

    probability = predict_fraud_tabular(claim)
    if probability is None:
        raise SystemExit(
            "Tabular model not trained yet. Run: python -m insurclaim.ml.train_tabular"
        )

    if probability >= DECISION_THRESHOLD:
        action = "route_to_investigator"
    elif probability < 0.10:
        action = "fast_track_approve"
    else:
        action = "request_more_info"

    return {
        "report": {
            "claim_id": claim_id,
            "fraud_probability": round(probability, 3),
            "risk_score": round(probability * 100, 1),
            "recommended_action": action,
            "key_facts": {
                "incident_type": claim.get("incident_type"),
                "incident_severity": claim.get("incident_severity"),
                "total_claim_amount": claim.get("total_claim_amount"),
                "authorities_contacted": claim.get("authorities_contacted"),
            },
            "ground_truth_is_fraud": claim.get("is_fraud"),
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate one insurance claim.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--claim", type=int, help="synthetic claim id (runs the full agent pipeline)")
    group.add_argument("--text", type=str, help="raw claim text to investigate")
    group.add_argument("--real-claim", type=int, help="real dataset claim id (tabular ML score)")
    args = parser.parse_args()

    if args.claim:
        final_state = _run_by_id(args.claim)
    elif args.real_claim:
        final_state = _run_real_claim(args.real_claim)
    else:
        final_state = _run_by_text(args.text)

    # default=str lets us print dates and decimals without a custom encoder.
    print(json.dumps(final_state.get("report", {}), indent=2, default=str))


if __name__ == "__main__":
    main()
