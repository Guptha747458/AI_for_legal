"""LegalLens FastAPI backend — document ingestion, analysis, comparison, Q&A."""

from __future__ import annotations

import atexit
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.settings import settings
from app.core.processor import processor
from app.core.cleanup import cleanup_temp_files
from app.services.chunker import DocumentChunker
from app.services.documents import documents
from app.services.vector_store import vector_store
from app.services.llm import llm_service
from app.models.jobs import AnalysisJob, DocumentStatus, jobs
from app.models.responses import JobStatusResponse

ALLOWED_TYPES = {"pdf", "docx", "txt"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Clean any stale temporary files from previous runs
    cleanup_temp_files()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        # Immediately remove all temporary files when closing the app
        cleanup_temp_files()


# Ensure temporary files are removed when the Python process exits
atexit.register(cleanup_temp_files)


app = FastAPI(
    title="LegalLens API",
    version="0.1.0",
    description="AI-powered legal document assistant backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QARequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1, max_length=2000)
    jurisdiction: str = Field(default="not specified", max_length=200)


class ChecklistRequest(BaseModel):
    document_id: str
    jurisdiction: str = Field(default="not specified", max_length=200)


class GlossaryRequest(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    context: str = Field(default="", max_length=2000)
    jurisdiction: str = Field(default="not specified", max_length=200)


chunker = DocumentChunker()


def _validate_file_signature(file_type: str, content: bytes) -> None:
    """Reject files whose bytes do not match the declared supported format."""
    if file_type == "pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
    if file_type == "docx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid DOCX.")
    if file_type == "txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="The uploaded text file is not valid UTF-8.") from exc


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "LegalLens Backend",
        "mode": "live" if settings.is_available() else "demo",
    }


@app.get("/api/v1/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "live" if settings.is_available() else "demo",
        "model": settings.model if settings.is_available() else None,
    }


@app.post("/api/v1/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("contract"),
    jurisdiction: str = Form(""),
) -> dict[str, Any]:
    try:
        file_type = processor._get_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if file_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{file_type}'. Supported: PDF, DOCX, TXT.",
        )
    try:
        processor._get_text_extractor(file_type)
    except ImportError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20MB).")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    _validate_file_signature(file_type, content)

    # Re-wrap bytes so processor can stream them back out.
    class _BytesUpload:
        def __init__(self, data: bytes, filename: str | None) -> None:
            self._data = data
            self.filename = filename

        async def read(self) -> bytes:
            return self._data

    result = await processor.process_file(_BytesUpload(content, file.filename), content=content)  # type: ignore[arg-type]
    if result["total_chars"] > settings.max_document_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Document too long ({result['total_chars']} chars; max {settings.max_document_chars}).",
        )
    if result["chunk_count"] == 0 or result["total_chars"] == 0:
        raise HTTPException(status_code=422, detail="No readable text found in this file.")

    doc_id = result["document_id"]
    clauses = chunker.chunk_document(doc_id, result["chunks"])
    clause_dicts = [
        {
            "clause_id": c.clause_id,
            "document_id": c.document_id,
            "text": c.text,
            "char_count": c.char_count,
            "page_number": c.page_number,
            "start_pos": c.start_pos,
            "end_pos": c.end_pos,
            "clause_index": c.clause_index,
            "title": c.title,
        }
        for c in clauses
    ]

    evicted_id = documents.save(
        document_id=doc_id,
        filename=result["filename"],
        file_type=result["file_type"],
        document_type=document_type or "contract",
        jurisdiction=jurisdiction or "",
        chunks=result["chunks"],
        clauses=clause_dicts,
    )
    if evicted_id is not None:
        vector_store.clear_collection(f"doc_{evicted_id}")

    collection = f"doc_{doc_id}"
    vector_store.add_collection(collection)
    vector_store.add_document(collection, doc_id, result["chunks"][: settings.max_chunks])

    job_id = str(uuid.uuid4())
    job = AnalysisJob(job_id=job_id, document_id=doc_id, status=DocumentStatus.COMPLETED, created_at=time.time())
    job.result = {"clause_count": len(clause_dicts)}
    jobs[job_id] = job

    preview = [
        {k: c[k] for k in ("clause_id", "text", "page_number", "clause_index", "title") if k in c}
        for c in clause_dicts[:50]
    ]
    return {
        "document_id": doc_id,
        "filename": result["filename"],
        "file_type": result["file_type"],
        "document_type": document_type or "contract",
        "jurisdiction": jurisdiction or "",
        "chunk_count": result["chunk_count"],
        "clause_count": len(clause_dicts),
        "total_chars": result["total_chars"],
        "clauses": preview,
        "job_id": job_id,
        "status": "completed",
        "mode": "live" if settings.is_available() else "demo",
    }


def _require_clause(document_id: str, clause_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    doc = documents.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found. Re-upload it (sessions are in-memory).")
    clause = documents.get_clause(document_id, clause_id)
    if clause is None:
        raise HTTPException(status_code=404, detail="Clause not found in this document.")
    return doc, clause


@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str) -> dict[str, Any]:
    doc = documents.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "document_id": doc["document_id"],
        "filename": doc["filename"],
        "file_type": doc["file_type"],
        "document_type": doc["document_type"],
        "jurisdiction": doc["jurisdiction"],
        "clause_count": len(doc["clauses"]),
        "clauses": doc["clauses"],
    }


@app.post("/api/v1/analyze/classify/{clause_id}")
async def analyze_clause(
    clause_id: str,
    document_id: str,
    document_type: str = "contract",
    jurisdiction: str = "not specified",
) -> dict[str, Any]:
    doc, clause = _require_clause(document_id, clause_id)
    try:
        return await llm_service.generate_classification(
            document_type=document_type or doc["document_type"],
            jurisdiction=jurisdiction if jurisdiction != "not specified" else (doc["jurisdiction"] or jurisdiction),
            clause_id=clause["clause_id"],
            clause_text=clause["text"][: settings.max_context_chars],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/analyze/simplify/{section_id}")
async def simplify_section(
    section_id: str,
    document_id: str,
    document_type: str = "contract",
) -> dict[str, Any]:
    doc, clause = _require_clause(document_id, section_id)
    try:
        return await llm_service.generate_simplification(
            document_type=document_type or doc["document_type"],
            section_id=clause["clause_id"],
            original_text=clause["text"][: settings.max_context_chars],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/analyze/compare")
async def compare_documents(
    document_id_1: str = Query(...),
    document_id_2: str = Query(...),
    document_type: str = "contract",
    jurisdiction: str = "not specified",
) -> dict[str, Any]:
    doc1 = documents.get(document_id_1)
    doc2 = documents.get(document_id_2)
    if doc1 is None or doc2 is None:
        raise HTTPException(status_code=404, detail="One or both documents were not found. Re-upload them.")
    try:
        return await llm_service.generate_comparison(
            document_type=document_type or doc1["document_type"],
            jurisdiction=jurisdiction,
            original_text=doc1["full_text"][: settings.max_context_chars],
            revised_text=doc2["full_text"][: settings.max_context_chars],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/analyze/qa")
async def answer_question(request: QARequest) -> dict[str, Any]:
    doc = documents.get(request.document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found. Re-upload it.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    collection = f"doc_{request.document_id}"
    hits = vector_store.query(collection, query_text=request.question, top_k=5, document_id=request.document_id)
    context_parts = [h["text"] for h in hits if h.get("text")] or [c["text"] for c in doc["clauses"][:5]]
    context = "\n\n".join(context_parts)[: settings.max_context_chars]
    try:
        result = await llm_service.generate_qa(
            document_type=doc["document_type"],
            jurisdiction=request.jurisdiction or doc["jurisdiction"] or "not specified",
            context=context,
            question=request.question,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    # Attach source excerpts so the UI can show grounding.
    result.setdefault("sources", [
        {"chunk_id": h.get("chunk_id"), "text": h.get("text", "")[:400]} for h in hits[:3]
    ])
    return result


@app.post("/api/v1/analyze/checklist")
async def generate_checklist(request: ChecklistRequest) -> dict[str, Any]:
    doc = documents.get(request.document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found. Re-upload it.")
    summary = "\n".join(f"- {c['text'][:300]}" for c in doc["clauses"][:20])[: settings.max_context_chars]
    try:
        return await llm_service.generate_checklist(
            document_type=doc["document_type"],
            jurisdiction=request.jurisdiction or doc["jurisdiction"] or "not specified",
            analysis_summary=summary,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/v1/analyze/glossary")
async def explain_term(request: GlossaryRequest) -> dict[str, Any]:
    term = request.term.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Term must not be empty.")
    if llm_service.use_demo:
        from app.services.glossary import explain_term_offline

        return explain_term_offline(term, request.context)
    # Live mode: reuse QA-shaped tool via a small inline prompt through checklist? Use QA path.
    try:
        result = await llm_service.generate_qa(
            document_type="contract",
            jurisdiction=request.jurisdiction,
            context=request.context[:2000] or "No surrounding context provided.",
            question=f"Define the legal term '{term}' in plain language as used in this context.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"term": term, "definition": result.get("answer", ""), "demo": False}


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        error=job.error,
        result=job.result,
    )


@app.post("/api/v1/jobs/{job_id}/clear")
async def clear_job(job_id: str) -> dict[str, str]:
    if job_id in jobs:
        del jobs[job_id]
    return {"status": "cleared"}


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str) -> dict[str, str]:
    """Privacy: let users delete their session data."""
    if documents.get(document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    documents.clear(document_id)
    vector_store.clear_collection(f"doc_{document_id}")
    return {"status": "deleted"}
