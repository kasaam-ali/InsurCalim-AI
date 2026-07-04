"""Generate synthetic auto-insurance claims with ground-truth labels.

We ask Claude to invent realistic claim records, deliberately injecting known
fraud patterns into a fraction of them. Every claim is stored with an is_fraud
label and a fraud_type, which serve two purposes:
  1. training data for the fine-tuned fraud classifier (ml/train.py)
  2. ground truth for the evaluation harness (eval/harness.py)

No real people or data are involved - everything here is invented.

Run as a script:  python -m insurclaim.data.generate --n 50
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta

from insurclaim.db import repo
from insurclaim.llm import call_llm_json

# Fraud patterns we inject, matching the story in PLAN.md.
FRAUD_TYPES = [
    "staged_collision",
    "duplicate_photo",
    "policy_lapsed_backdated",
    "impossible_timeline",
    "repeat_claimant",
]

# JSON schema (described in prose) that we ask the model to fill in.
CLAIM_INSTRUCTIONS = """
You generate a single synthetic auto-insurance claim as strict JSON with keys:
  policy_number (string), holder_name (string),
  incident_date (YYYY-MM-DD), report_date (YYYY-MM-DD),
  location (string), description (2-4 sentence narrative of the accident),
  claimed_amount (number),
  parties (list of {full_name, role, national_id, phone, email}),
  vehicles (list of {vin, make, model, year, plate}).
Return ONLY the JSON object, no extra text.
"""


def _system_prompt(fraud_type: str | None) -> str:
    """Build the instruction, adding a fraud pattern when required."""
    if fraud_type is None:
        return CLAIM_INSTRUCTIONS + "\nThis is a LEGITIMATE, consistent claim."
    hints = {
        "staged_collision": "Make the collision look staged: too-clean story, cooperative 'strangers'.",
        "duplicate_photo": "Describe damage identical to a common template (photo reused elsewhere).",
        "policy_lapsed_backdated": "Set incident_date just BEFORE the policy could have been active.",
        "impossible_timeline": "Include a physically impossible sequence or contradictory timing.",
        "repeat_claimant": "Reuse a national_id that looks like a frequent claimant.",
    }
    return CLAIM_INSTRUCTIONS + f"\nThis claim is FRAUDULENT. Pattern: {hints[fraud_type]}"


def _fake_policy(policy_number: str) -> dict:
    """Create a simple policy row so the claim has something to reference."""
    start = date.today() - timedelta(days=random.randint(60, 400))
    return {
        "policy_number": policy_number,
        "holder_name": "Policy Holder",
        "start_date": start,
        "end_date": start + timedelta(days=365),
        "coverage_limit": random.choice([10000, 25000, 50000]),
    }


def generate_one(is_fraud: bool) -> int:
    """Ask the model for one claim, store it, and return the new claim id."""
    fraud_type = random.choice(FRAUD_TYPES) if is_fraud else None
    data = call_llm_json(
        prompt="Generate one claim now.",
        system=_system_prompt(fraud_type),
    )

    repo.insert_policy(_fake_policy(data["policy_number"]))
    claim_id = repo.insert_claim(
        {
            "policy_number": data["policy_number"],
            "incident_date": data["incident_date"],
            "report_date": data["report_date"],
            "location": data.get("location"),
            "description": data.get("description"),
            "claimed_amount": data.get("claimed_amount"),
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
        }
    )
    for party in data.get("parties", []):
        repo.insert_party(claim_id, party)
    for vehicle in data.get("vehicles", []):
        repo.insert_vehicle(claim_id, vehicle)
    return claim_id


def generate(n: int, fraud_ratio: float = 0.4) -> list[int]:
    """Generate n claims with roughly fraud_ratio of them fraudulent."""
    repo.init_schema()
    ids: list[int] = []
    for i in range(n):
        is_fraud = random.random() < fraud_ratio
        try:
            ids.append(generate_one(is_fraud))
        except Exception as exc:  # keep going even if one generation fails
            print(f"[warn] claim {i} failed: {exc}")
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic labeled claims.")
    parser.add_argument("--n", type=int, default=50, help="how many claims to generate")
    parser.add_argument("--fraud-ratio", type=float, default=0.4, help="fraction that are fraud")
    args = parser.parse_args()

    created = generate(args.n, args.fraud_ratio)
    print(f"Generated and stored {len(created)} claims (ids: {created[:5]}...).")


if __name__ == "__main__":
    main()
