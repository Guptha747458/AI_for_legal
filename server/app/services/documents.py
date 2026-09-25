"""In-memory document registry (session-scoped, no persistence)."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from app.core.settings import settings


class DocumentRegistry:
    """Store parsed documents for the lifetime of the server process."""

    def __init__(self) -> None:
        self._docs: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def save(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        document_type: str,
        jurisdiction: str,
        chunks: list[dict[str, Any]],
        clauses: list[dict[str, Any]],
    ) -> str | None:
        evicted_id: str | None = None
        self._docs[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "document_type": document_type,
            "jurisdiction": jurisdiction,
            "chunks": chunks,
            "clauses": clauses,
            "clause_map": {c["clause_id"]: c for c in clauses},
            "chunk_map": {c["chunk_id"]: c for c in chunks},
            "full_text": "\n\n".join(c["text"] for c in clauses) or "\n".join(c["text"] for c in chunks),
        }
        self._docs.move_to_end(document_id)
        while len(self._docs) > settings.max_documents:
            evicted_id, _ = self._docs.popitem(last=False)
        return evicted_id

    def get(self, document_id: str) -> dict[str, Any] | None:
        return self._docs.get(document_id)

    def get_clause(self, document_id: str, clause_id: str) -> dict[str, Any] | None:
        doc = self._docs.get(document_id)
        if not doc:
            return None
        # Clause IDs and chunk IDs share one namespace for lookup simplicity.
        return doc["clause_map"].get(clause_id) or doc["chunk_map"].get(clause_id)

    def list_ids(self) -> list[str]:
        return list(self._docs.keys())

    def clear(self, document_id: str) -> None:
        self._docs.pop(document_id, None)


documents = DocumentRegistry()
