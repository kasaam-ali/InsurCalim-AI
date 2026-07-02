"""Command-line entry point for InsurCalim AI.

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate one insurance claim.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--claim", type=int, help="claim id to load from the database")
    group.add_argument("--text", type=str, help="raw claim text to investigate")
    args = parser.parse_args()

    final_state = _run_by_id(args.claim) if args.claim else _run_by_text(args.text)

    # default=str lets us print dates and decimals without a custom encoder.
    print(json.dumps(final_state.get("report", {}), indent=2, default=str))


if __name__ == "__main__":
    main()
