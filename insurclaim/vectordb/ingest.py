"""Index documents into the vector store.

Loads policy documents and prior-claim narratives from the database, then embeds
and stores them so the agents can retrieve relevant context and find similar
past claims. Run as a script:  python -m insurclaim.vectordb.ingest
"""

from __future__ import annotations

from pathlib import Path

from insurclaim.db import repo
from insurclaim.vectordb.store import claim_store, policy_store


def ingest_prior_claims() -> int:
    """Index every labeled claim narrative into the prior-claims store.

    The ground-truth label is stored as metadata so a match against a known-fraud
    claim can be surfaced to the fraud agent.
    """
    claims = repo.list_labeled_claims()
    if not claims:
        return 0

    store = claim_store()
    ids = [f"claim-{c['id']}" for c in claims]
    texts = [c["description"] or "" for c in claims]
    metadatas = [
        {"claim_id": c["id"], "is_fraud": bool(c["is_fraud"]), "fraud_type": c["fraud_type"] or ""}
        for c in claims
    ]
    store.add_documents(ids=ids, texts=texts, metadatas=metadatas)
    return len(claims)


def ingest_policy_documents(docs_dir: str | Path) -> int:
    """Index every .txt policy document found in a directory."""
    docs_dir = Path(docs_dir)
    files = sorted(docs_dir.glob("*.txt"))
    if not files:
        return 0

    store = policy_store()
    ids = [f.stem for f in files]
    texts = [f.read_text(encoding="utf-8") for f in files]
    metadatas = [{"source": f.name} for f in files]
    store.add_documents(ids=ids, texts=texts, metadatas=metadatas)
    return len(files)


if __name__ == "__main__":
    indexed = ingest_prior_claims()
    print(f"Indexed {indexed} prior claim narratives into the vector store.")
