"""
In-memory vector store for retrieval-augmented generation (RAG).
Uses a simple cosine-similarity approach with deterministic embeddings.
No external dependencies required beyond what's already installed.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any


def _hash_embedding(text: str, dim: int = 384) -> list[float]:
    """Generate a deterministic pseudo-embedding via token hashing."""
    embedding = [0.0] * dim
    tokens = text.lower().split()

    for token in tokens:
        hash_value = hashlib.md5(token.encode()).hexdigest()
        index = int(hash_value[:4], 16) % dim
        embedding[index] += 1.0

    return embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class VectorStore:
    """In-memory vector store for document chunks."""

    def __init__(self) -> None:
        self.collections: dict[str, dict[str, dict[str, Any]]] = {}

    def add_collection(self, collection_name: str) -> None:
        if collection_name not in self.collections:
            self.collections[collection_name] = {}

    def add_document(
        self,
        collection_name: str,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> None:
        """Add document chunks to a collection."""
        self.add_collection(collection_name)

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id") or str(uuid.uuid4())
            text = chunk.get("text", "")
            embedding = _hash_embedding(text)

            self.collections[collection_name][chunk_id] = {
                "text": text,
                "embedding": embedding,
                "document_id": document_id,
                "chunk_id": chunk_id,
                "page_number": chunk.get("page_number", 1),
                "start_pos": chunk.get("start_pos", 0),
                "end_pos": chunk.get("end_pos", 0),
                "metadata": chunk.get("metadata", {}),
            }

    def query(
        self,
        collection_name: str,
        query_text: str | None = None,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query the collection for the most relevant chunks."""
        if collection_name not in self.collections:
            return []

        query_embedding = _hash_embedding(query_text) if query_text else None
        results = []

        for chunk in self.collections[collection_name].values():
            if document_id and chunk.get("document_id") != document_id:
                continue

            similarity = 0.0
            if query_embedding:
                similarity = _cosine_similarity(query_embedding, chunk["embedding"])
            else:
                similarity = 0.0

            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "document_id": chunk["document_id"],
                    "page_number": chunk["page_number"],
                    "start_pos": chunk["start_pos"],
                    "end_pos": chunk["end_pos"],
                    "similarity": similarity,
                    "metadata": chunk["metadata"],
                }
            )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def clear_collection(self, collection_name: str) -> None:
        """Clear a collection (for session cleanup)."""
        if collection_name in self.collections:
            self.collections[collection_name] = {}


# Global in-memory vector store
vector_store = VectorStore()