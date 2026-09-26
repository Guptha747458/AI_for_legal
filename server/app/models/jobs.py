"""
Shared data types between client and server.
These are duplicated in the client as TypeScript interfaces.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"




class AnalysisJob:
    """
    In-memory representation of a document analysis job.
    Jobs are lost on server restart (session-based processing).
    """

    def __init__(
        self,
        job_id: str,
        document_id: str,
        status: DocumentStatus,
        created_at: float,
    ) -> None:
        self.job_id = job_id
        self.document_id = document_id
        self.status = status
        self.created_at = created_at
        self.error: str | None = None
        self.result: dict[str, Any] | None = None


class ComparisonJob:
    """
    In-memory representation of a document comparison job.
    """

    def __init__(
        self,
        job_id: str,
        document_ids: list[str],
        status: DocumentStatus,
        created_at: float,
    ) -> None:
        self.job_id = job_id
        self.document_ids = document_ids
        self.status = status
        self.created_at = created_at
        self.error: str | None = None
        self.result: dict[str, Any] | None = None


# A simple in-memory registry. In production, use a database.
jobs: dict[str, AnalysisJob | ComparisonJob] = {}
