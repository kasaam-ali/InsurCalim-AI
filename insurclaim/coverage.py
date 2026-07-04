"""Policy coverage engine.

Lets an insurer upload their own policy documents / rules, indexes them into the
policy vector store, and checks whether an incoming claim is actually covered by
those policies - grounded in the cited clause. This is the "is this even our
policy / is it covered?" capability requested for the product.
"""

from __future__ import annotations

from typing import Any

from insurclaim.db import repo
from insurclaim.llm import call_llm_json
from insurclaim.vectordb.store import policy_store

COVERAGE_SYSTEM = """
You are an insurance coverage analyst. You are given excerpts from an insurer's
own policy documents and a claim description. Decide whether the claim appears to
be covered. Return strict JSON:
{
  "decision": "covered" | "not_covered" | "needs_review",
  "rationale": "one or two sentences grounded in the clauses",
  "clause": "the single most relevant clause text you relied on"
}
Only use the provided clauses. If they do not clearly settle it, return
needs_review. Return ONLY the JSON object.
"""


def add_policy_document(company: str, doc_name: str, text: str) -> int:
    """Store a policy document and index it for retrieval. Returns its id."""
    doc_id = repo.insert_policy_document(company, doc_name, text)
    policy_store().add_documents(
        ids=[f"policy-{doc_id}"],
        texts=[text],
        metadatas=[{"company": company, "doc_name": doc_name, "doc_id": doc_id}],
    )
    return doc_id


def check_coverage(description: str, n_results: int = 3) -> dict[str, Any]:
    """Check whether a claim is covered by the uploaded policies.

    Retrieves the most relevant policy clauses (RAG) and lets the LLM judge, then
    attaches the source citations. Degrades gracefully when no policies exist or
    the LLM is unavailable.
    """
    try:
        matches = policy_store().query(description, n_results=n_results)
    except Exception:
        matches = []

    if not matches:
        return {
            "decision": "needs_review",
            "rationale": "No policy documents on file. Upload the insurer's policies to enable coverage checks.",
            "clause": "",
            "citations": [],
        }

    clauses = "\n---\n".join(m["document"][:800] for m in matches)
    try:
        result = call_llm_json(
            prompt=f"POLICY CLAUSES:\n{clauses}\n\nCLAIM:\n{description}",
            system=COVERAGE_SYSTEM,
            reasoning=True,
        )
    except Exception:
        result = {
            "decision": "needs_review",
            "rationale": "Coverage reasoning model unavailable; showing the most relevant clause.",
            "clause": matches[0]["document"][:300],
        }

    result["citations"] = [
        {**m.get("metadata", {}), "similarity": m.get("similarity")} for m in matches
    ]
    return result
