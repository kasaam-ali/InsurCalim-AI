"""Deterministic fraud/validity checks - pure code, never the LLM.

Policy, math, and velocity logic must be exact and auditable, so it lives here
instead of being left to a language model. Each check returns a "signal" dict
with a code, a human-readable message, and an evidence pointer, so the report
agent can cite exactly why a claim was flagged.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from insurclaim.db import repo

# Above how many prior claims a repeat claimant / VIN becomes a flag.
VELOCITY_THRESHOLD = 1


def _signal(code: str, message: str, evidence: str, severity: str = "medium") -> dict[str, Any]:
    """Build a standard signal dict used across all checks."""
    return {"code": code, "message": message, "evidence": evidence, "severity": severity}


def check_policy_active(claim: dict[str, Any]) -> dict[str, Any] | None:
    """Flag if the incident happened outside the policy's coverage dates."""
    policy = claim.get("policy")
    incident = claim.get("incident_date")
    if not policy or not incident:
        return None
    if not (policy["start_date"] <= incident <= policy["end_date"]):
        return _signal(
            "policy_inactive",
            "Incident date falls outside the policy coverage window.",
            f"incident_date={incident}, coverage={policy['start_date']}..{policy['end_date']}",
            severity="high",
        )
    return None


def check_amount_vs_limit(claim: dict[str, Any]) -> dict[str, Any] | None:
    """Flag if the claimed amount exceeds the policy coverage limit."""
    policy = claim.get("policy")
    amount = claim.get("claimed_amount")
    if not policy or amount is None:
        return None
    if amount > policy["coverage_limit"]:
        return _signal(
            "amount_over_limit",
            "Claimed amount is greater than the policy coverage limit.",
            f"claimed_amount={amount}, coverage_limit={policy['coverage_limit']}",
            severity="high",
        )
    return None


def check_report_delay(claim: dict[str, Any], max_days: int = 30) -> dict[str, Any] | None:
    """Flag claims reported long after the incident (a weak fraud signal)."""
    incident = claim.get("incident_date")
    reported = claim.get("report_date")
    if not incident or not reported:
        return None
    delay = (reported - incident).days
    if delay > max_days:
        return _signal(
            "late_report",
            f"Claim reported {delay} days after the incident (limit {max_days}).",
            f"incident_date={incident}, report_date={reported}",
            severity="low",
        )
    return None


def check_claimant_velocity(claim: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag parties who appear in several other claims (repeat claimant)."""
    signals: list[dict[str, Any]] = []
    claim_id = claim.get("id")
    for party in claim.get("parties", []):
        national_id = party.get("national_id")
        if not national_id:
            continue
        others = repo.count_claims_by_national_id(national_id, exclude_claim_id=claim_id)
        if others > VELOCITY_THRESHOLD:
            signals.append(
                _signal(
                    "repeat_claimant",
                    f"Party '{party['full_name']}' appears in {others} other claims.",
                    f"national_id={national_id}, other_claims={others}",
                    severity="medium",
                )
            )
    return signals


def check_vehicle_velocity(claim: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag VINs that appear in several other claims (repeat vehicle)."""
    signals: list[dict[str, Any]] = []
    claim_id = claim.get("id")
    for vehicle in claim.get("vehicles", []):
        vin = vehicle.get("vin")
        if not vin:
            continue
        others = repo.count_claims_by_vin(vin, exclude_claim_id=claim_id)
        if others > VELOCITY_THRESHOLD:
            signals.append(
                _signal(
                    "repeat_vin",
                    f"Vehicle VIN {vin} appears in {others} other claims.",
                    f"vin={vin}, other_claims={others}",
                    severity="medium",
                )
            )
    return signals


def check_physics_sanity(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Light kinematic sanity check on timeline events (NOT a physics engine).

    Uses the simple relation distance = speed * time. If an event provides a
    speed, a distance, and a duration that clearly contradict each other, flag it.
    """
    signals: list[dict[str, Any]] = []
    for event in events:
        speed_kmh = event.get("speed_kmh")
        distance_m = event.get("distance_m")
        duration_s = event.get("duration_s")
        if not (speed_kmh and distance_m and duration_s):
            continue
        speed_ms = speed_kmh / 3.6
        expected_distance = speed_ms * duration_s
        # Flag when reported distance is off by more than 50% from expectation.
        if abs(expected_distance - distance_m) > 0.5 * distance_m:
            signals.append(
                _signal(
                    "physics_mismatch",
                    "Reported speed, distance, and duration do not agree.",
                    f"speed={speed_kmh}km/h, distance={distance_m}m, "
                    f"duration={duration_s}s, expected~{expected_distance:.0f}m",
                    severity="medium",
                )
            )
    return signals


def run_all(claim: dict[str, Any], events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Run every deterministic check and return the combined list of signals."""
    signals: list[dict[str, Any]] = []
    for single_check in (check_policy_active, check_amount_vs_limit, check_report_delay):
        result = single_check(claim)
        if result:
            signals.append(result)
    signals.extend(check_claimant_velocity(claim))
    signals.extend(check_vehicle_velocity(claim))
    if events:
        signals.extend(check_physics_sanity(events))
    return signals
