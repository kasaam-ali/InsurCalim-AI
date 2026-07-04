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
import sys
from datetime import datetime, timedelta
from pathlib import Path

from insurclaim.db import repo

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "real" / "narratives.json"


def _policy_for(policy_number: str, incident_date: str, claimed_amount: float) -> dict:
    """Create a policy whose coverage window and limit fit the claim.

    Anchored to the incident date (active from 90 days before to well after) and
    a limit above the claimed amount, so deterministic policy/amount checks only
    fire on genuinely problematic claims rather than on random defaults.
    """
    incident = datetime.strptime(incident_date, "%Y-%m-%d").date()
    start = incident - timedelta(days=90)
    limit = max(50000, int((claimed_amount or 0) * 1.5))
    return {
        "policy_number": policy_number,
        "holder_name": "Policy Holder",
        "start_date": start,
        "end_date": start + timedelta(days=365),
        "coverage_limit": limit,
    }


def _extract_claims(text: str) -> list[dict]:
    """Pull every valid claim object out of possibly-messy JSON text.

    Tolerates multiple concatenated arrays and skips malformed objects, and
    de-duplicates by policy_number, so a large or partly-corrupted paste still
    loads all of its good, unique records.
    """
    decoder = json.JSONDecoder()
    claims: list[dict] = []
    seen: set[str] = set()
    index, length = 0, len(text)
    while index < length:
        start = text.find("{", index)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, start)
            index = end
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(obj, dict) and "description" in obj and "policy_number" in obj:
            key = str(obj["policy_number"])
            if key not in seen:
                seen.add(key)
                claims.append(obj)
    return claims


def load(path: str | Path = DEFAULT_PATH) -> list[int]:
    """Insert every claim from the JSON file and return the new claim ids."""
    repo.init_schema()
    claims = _extract_claims(Path(path).read_text(encoding="utf-8"))

    ids: list[int] = []
    for data in claims:
        repo.insert_policy(
            _policy_for(data["policy_number"], data["incident_date"], data.get("claimed_amount", 0))
        )
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


def seed_photo_hashes() -> int:
    """Attach a perceptual hash to each claim, reusing one hash across a few
    fraud claims so the duplicate-photo fraud check has something to detect.
    """
    import hashlib

    reused = "ffff0000ffff0000"  # the "same photo" reused across staged claims
    claims = repo.list_labeled_claims()
    reused_count = 0
    for claim in claims:
        is_staged = claim.get("fraud_type") == "staged_collision"
        if is_staged and reused_count < 4:
            phash = reused
            reused_count += 1
        else:
            phash = hashlib.md5(str(claim["id"]).encode()).hexdigest()[:16]
        repo.insert_photo_hash(
            claim["id"],
            {"file_name": f"claim_{claim['id']}_damage.jpg", "phash": phash, "captured_at": None},
        )
    return len(claims)


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    created = load(source)
    photos = seed_photo_hashes()

    from insurclaim.vectordb.ingest import ingest_prior_claims

    indexed = ingest_prior_claims()
    print(
        f"Loaded {len(created)} narrative claims; seeded {photos} photo hashes; "
        f"vector store now holds {indexed} claims."
    )
