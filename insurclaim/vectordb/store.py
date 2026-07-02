"""Vector store abstraction for RAG (retrieval-augmented generation).

Two uses in this project:
1. Ground answers in policy documents.
2. Find "similar past claims" - especially prior known-fraud claims that closely
   match the current claim's narrative.

Chroma is used for local development. The VectorStore class is deliberately thin
so a Pinecone implementation can be swapped in for the AWS phase without changing
any calling code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb

# Where Chroma keeps its files on disk (ignored by git via the data/ rule).
DEFAULT_PERSIST_DIR = os.getenv(
    "CHROMA_DIR", str(Path(__file__).resolve().parents[2] / "data" / "chroma")
)


class VectorStore:
    """A small wrapper around a Chroma collection."""

    def __init__(self, collection: str, persist_dir: str | None = None) -> None:
        self._client = chromadb.PersistentClient(path=persist_dir or DEFAULT_PERSIST_DIR)
        # get_or_create keeps the store idempotent across runs.
        self._collection = self._client.get_or_create_collection(name=collection)

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Embed and store a batch of documents."""
        self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    def query(self, text: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Return the n most similar documents to the given text."""
        result = self._collection.query(query_texts=[text], n_results=n_results)
        matches: list[dict[str, Any]] = []
        # Chroma returns parallel lists nested one level deep (one per query).
        ids = result["ids"][0]
        documents = result["documents"][0]
        distances = result["distances"][0]
        metadatas = result["metadatas"][0]
        for doc_id, document, distance, metadata in zip(ids, documents, distances, metadatas):
            matches.append(
                {
                    "id": doc_id,
                    "document": document,
                    # Chroma returns a distance; convert to a rough similarity score.
                    "similarity": round(1.0 - distance, 4),
                    "metadata": metadata or {},
                }
            )
        return matches

    def similar_claims(self, narrative: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Return prior claims similar to this narrative, most similar first."""
        return self.query(narrative, n_results=n_results)


def policy_store() -> VectorStore:
    """Vector store holding policy documents."""
    return VectorStore("policy_docs")


def claim_store() -> VectorStore:
    """Vector store holding prior-claim narratives."""
    return VectorStore("prior_claims")
