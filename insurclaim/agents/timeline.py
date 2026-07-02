"""Timeline / Causal Reasoning agent - the showpiece.

Orders the described events into a sequence, annotates each with key facts
(speed, road, damage), and flags two kinds of problems:
  - inconsistencies: the narrative contradicts the evidence
  - gaps: unexplained missing steps or time jumps

A light, deterministic kinematic sanity check runs in code (rules layer), NOT in
the LLM - we do not claim to run a physics engine.
"""

from __future__ import annotations

from typing import Any

from insurclaim.llm import call_llm_json
from insurclaim.rules import deterministic

TIMELINE_SYSTEM = """
You are a claims timeline analyst. From the claim description, produce strict JSON:
{
  "events": [
    {"order": 1, "summary": "...", "speed_kmh": null, "distance_m": null,
     "duration_s": null, "facts": ["wet road", "airbag deployed late"]}
  ],
  "inconsistencies": [
    {"description": "...", "evidence": "which fields contradict each other"}
  ],
  "gaps": [
    {"description": "unexplained 3-second gap before impact"}
  ]
}
Only include speed_kmh/distance_m/duration_s when the text clearly implies them.
Return ONLY the JSON object.
"""


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Build the annotated timeline and attach any physics-sanity signals."""
    extracted = state.get("extracted", {})
    description = extracted.get("description", "")

    timeline = call_llm_json(prompt=description, system=TIMELINE_SYSTEM, reasoning=True)

    # Deterministic kinematic sanity check over the events (pure code).
    events = timeline.get("events", [])
    physics_signals = deterministic.check_physics_sanity(events)

    return {"timeline": timeline, "timeline_signals": physics_signals}
