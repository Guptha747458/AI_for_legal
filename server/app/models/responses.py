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


class SimplificationResponse(BaseModel):
    section_id: str
    simplified_text: str = Field(min_length=1)
    key_terms: list[str] = Field(default_factory=list)


class ClassificationResponse(BaseModel):
    clause_id: str
    category: Literal[
        "obligations", "rights", "deadlines", "penalties_fees", "termination",
        "auto_renewal", "liability_indemnification", "dispute_resolution",
        "data_privacy", "unusual_nonstandard",
    ]
    attention_level: Literal["low", "medium", "high"]
    rationale: str = Field(min_length=1)
    plain_explanation: str = Field(min_length=1)


class ComparisonChangeResponse(BaseModel):
    type: Literal["added", "removed", "modified"]
    clause_id_old: str | None = None
    clause_id_new: str | None = None
    explanation: str = Field(min_length=1)
    impact: str = Field(min_length=1)


class ComparisonResponse(BaseModel):
    changes: list[ComparisonChangeResponse]


class QAResponse(BaseModel):
    answer: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)
    disclaimer_needed: bool


class ChecklistActionItem(BaseModel):
    text: str = Field(min_length=1)
    clause_id: str
    urgency: Literal["low", "medium", "high"]


class LawyerQuestion(BaseModel):
    question: str = Field(min_length=1)
    related_clause_id: str


class ChecklistResponse(BaseModel):
    action_items: list[ChecklistActionItem]
    questions_for_lawyer: list[LawyerQuestion]


class ComparisonJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "analyzing", "completed", "failed"]
    created_at: float
    document_ids: list[str]
    error: str | None = None
    result: dict[str, Any] | None = None
