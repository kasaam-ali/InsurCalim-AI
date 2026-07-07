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

# Fallback list used only when the selected policy does not itself specify the
# documents required to file a motor claim.
STANDARD_REQUIRED_DOCUMENTS = [
    "Claim form",
    "CNIC / ID proof",
    "Driving licence",
    "Vehicle registration certificate (RC)",
    "Police report / FIR",
    "Medical report (if any injury is claimed)",
    "Repair estimate",
    "Workshop invoice",
    "Surveyor report",
    "Damage photos",
]

DOCUMENTS_SYSTEM = """
You are an insurance claims-processing analyst. You are given (a) an insurer's own
policy text and (b) the full claim file the claimant submitted (all documents
concatenated). First determine which documents THIS policy requires to file a
claim - use the policy's own "documents required / claims procedure" section if it
has one; otherwise use this standard motor-claim checklist:
{standard}

Then check the claim file and classify each required document as present, missing,
or incomplete (present but partial/unsigned/illegible/inconsistent). Return strict
JSON:
{{
  "required": ["..."],
  "present": ["..."],
  "missing": ["..."],
  "incomplete": [{{"document": "...", "issue": "..."}}],
  "notes": "one or two sentences on overall completeness"
}}
Base every judgement on the provided text only. Return ONLY the JSON object.
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


def remove_policy_document(doc_id: int) -> None:
    """Delete a policy document from the database and the vector store."""
    repo.delete_policy_document(doc_id)
    try:
        policy_store().delete([f"policy-{doc_id}"])
    except Exception:
        # Vector store may be unavailable; the DB row is already gone.
        pass


def _selected_policy_text(doc_ids: list[int] | None, cap: int = 24000) -> str:
    """Fetch and concatenate the full text of the selected policy documents."""
    if not doc_ids:
        return ""
    parts: list[str] = []
    for doc_id in doc_ids:
        doc = repo.get_policy_document(doc_id)
        if doc and doc.get("content"):
            header = f"POLICY: {doc.get('company','')} - {doc.get('doc_name','')}"
            parts.append(f"{header}\n{doc['content']}")
    return "\n\n=====\n\n".join(parts)[:cap]


def check_coverage(
    description: str, doc_ids: list[int] | None = None, n_results: int = 3
) -> dict[str, Any]:
    """Check whether a claim is covered by the insurer's policies.

    When doc_ids are given, the claim is judged against exactly those selected
    policies' text. Otherwise the most relevant clauses are retrieved via RAG over
    all uploaded policies. Degrades gracefully when no policies exist or the LLM is
    unavailable.
    """
    citations: list[dict[str, Any]] = []
    selected_text = _selected_policy_text(doc_ids)

    if selected_text:
        clauses = selected_text
        for doc_id in doc_ids or []:
            doc = repo.get_policy_document(doc_id)
            if doc:
                citations.append(
                    {"doc_id": doc_id, "company": doc.get("company"),
                     "doc_name": doc.get("doc_name")}
                )
    else:
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
        citations = [
            {**m.get("metadata", {}), "similarity": m.get("similarity")} for m in matches
        ]

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
            "clause": clauses[:300],
        }

    result["citations"] = citations
    return result


def check_documents(
    claim_text: str, doc_ids: list[int] | None = None
) -> dict[str, Any]:
    """Check whether the claim file has the documents the selected policy requires.

    Reads the selected policy text to derive its required-document list (falling
    back to a standard motor-claim checklist), then classifies each as present,
    missing, or incomplete. Returns an empty-ish result if the LLM is unavailable.
    """
    if not claim_text or not claim_text.strip():
        return {"required": [], "present": [], "missing": [], "incomplete": [], "notes": ""}

    policy_text = _selected_policy_text(doc_ids)
    prompt = (
        f"POLICY TEXT:\n{policy_text or '(no specific policy selected)'}\n\n"
        f"CLAIM FILE:\n{claim_text[:24000]}"
    )
    system = DOCUMENTS_SYSTEM.format(
        standard="; ".join(STANDARD_REQUIRED_DOCUMENTS)
    )
    try:
        result = call_llm_json(prompt=prompt, system=system, reasoning=True)
    except Exception:
        return {
            "required": STANDARD_REQUIRED_DOCUMENTS,
            "present": [],
            "missing": [],
            "incomplete": [],
            "notes": "Document-completeness model unavailable.",
        }

    # Normalise the shape so the UI/report can rely on it.
    result.setdefault("required", [])
    result.setdefault("present", [])
    result.setdefault("missing", [])
    result.setdefault("incomplete", [])
    result.setdefault("notes", "")
    return result
