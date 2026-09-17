"""
Pydantic models shared across API endpoints.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size_bytes: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "analyzing", "completed", "failed"]
    created_at: float
    error: str | None = None
    result: dict[str, Any] | None = None


class ComparisonJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "analyzing", "completed", "failed"]
    created_at: float
    document_ids: list[str]
    error: str | None = None
    result: dict[str, Any] | None = None
