"""LangGraph wiring for the 4-agent claim pipeline.

A single shared state (ClaimState) flows through the agents in order:

    intake -> timeline -> fraud -> report

Each agent reads what it needs from the state and returns the keys it adds.
LangGraph merges those returned keys back into the shared state and passes it on.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from insurclaim.agents import fraud, intake, report, timeline


class ClaimState(TypedDict, total=False):
    """Everything that flows between the agents. total=False = all keys optional."""

    claim: dict[str, Any]           # claim record loaded from the database
    raw_documents: str              # raw text inputs (when not loading from DB)
    extracted: dict[str, Any]       # structured claim from the intake agent
    timeline: dict[str, Any]        # events, inconsistencies, gaps
    timeline_signals: list[dict]    # physics-sanity signals from the timeline step
    fraud_signals: list[dict]       # all deterministic + image + RAG signals
    fraud_probability: float        # score from the fine-tuned ML classifier
    similar_claims: list[dict]      # matches from the vector store
    fraud_reasoning: dict[str, Any] # LLM narrative red flags
    report: dict[str, Any]          # final ranked, explainable report


def build_graph():
    """Wire the agents into a compiled LangGraph application."""
    graph = StateGraph(ClaimState)

    graph.add_node("intake", intake.run)
    graph.add_node("timeline", timeline.run)
    graph.add_node("fraud", fraud.run)
    graph.add_node("report", report.run)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "timeline")
    graph.add_edge("timeline", "fraud")
    graph.add_edge("fraud", "report")
    graph.add_edge("report", END)

    return graph.compile()


# Compile once and reuse (compiling on every call would be wasteful).
_APP = None


def run_claim(initial_state: ClaimState) -> ClaimState:
    """Run the full pipeline for one claim and return the final state."""
    global _APP
    if _APP is None:
        _APP = build_graph()
    return _APP.invoke(initial_state)
