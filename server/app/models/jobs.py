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


def prune_jobs(max_jobs: int = 1000) -> None:
    """Keep the in-memory registry bounded while retaining recent jobs."""
    while len(jobs) > max_jobs:
        oldest_id = min(jobs, key=lambda job_id: jobs[job_id].created_at)
        del jobs[oldest_id]


def remove_jobs_for_document(document_id: str) -> None:
    for job_id, job in list(jobs.items()):
        document_ids = job.document_ids if isinstance(job, ComparisonJob) else [job.document_id]
        if document_id in document_ids:
            del jobs[job_id]
