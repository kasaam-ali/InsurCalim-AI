"""Load externally-provided claim narratives into PostgreSQL and index them.

Reads a JSON array of claims (the same shape the synthetic generator produces)
from a file, inserts them into the claim tables, and indexes them into the
vector store so they become prior claims available for similar-claim retrieval.

Useful when higher-quality narratives are generated elsewhere and handed over as
a JSON file, instead of generating them through the in-app LLM.

Run as a script:  python -m insurclaim.data.load_narratives [path-to-json]
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from insurclaim.db import repo

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "real" / "narratives.json"


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


def load(path: str | Path = DEFAULT_PATH) -> list[int]:
    """Insert every claim from the JSON file and return the new claim ids."""
    repo.init_schema()
    claims = json.loads(Path(path).read_text(encoding="utf-8"))

    ids: list[int] = []
    for data in claims:
        repo.insert_policy(_fake_policy(data["policy_number"]))
        claim_id = repo.insert_claim(
            {
                "policy_number": data["policy_number"],
                "incident_date": data["incident_date"],
                "report_date": data["report_date"],
                "location": data.get("location"),
                "description": data.get("description"),
                "claimed_amount": data.get("claimed_amount"),
                "is_fraud": data.get("is_fraud", False),
                "fraud_type": data.get("fraud_type"),
            }
        )
        for party in data.get("parties", []):
            # Normalize to the columns our schema expects (fill any missing).
            repo.insert_party(
                claim_id,
                {
                    "full_name": party.get("full_name"),
                    "role": party.get("role"),
                    "national_id": party.get("national_id"),
                    "phone": party.get("phone"),
                    "email": party.get("email"),
                },
            )
        for vehicle in data.get("vehicles", []):
            # Accept either "plate" or "license_plate"; ignore extra keys (e.g. color).
            repo.insert_vehicle(
                claim_id,
                {
                    "vin": vehicle.get("vin"),
                    "make": vehicle.get("make"),
                    "model": vehicle.get("model"),
                    "year": vehicle.get("year"),
                    "plate": vehicle.get("plate") or vehicle.get("license_plate"),
                },
            )
        ids.append(claim_id)
    return ids


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    created = load(source)

    from insurclaim.vectordb.ingest import ingest_prior_claims

    indexed = ingest_prior_claims()
    print(f"Loaded {len(created)} narrative claims; vector store now holds {indexed} claims.")
