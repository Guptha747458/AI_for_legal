"""Regression tests for upload and API boundary validation."""

from fastapi.testclient import TestClient

from app.main import app
from app.core import settings as settings_module
from app.models.jobs import AnalysisJob, ComparisonJob, DocumentStatus, jobs, prune_jobs, remove_jobs_for_document


def test_upload_rejects_content_that_does_not_match_extension() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("contract.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]


def test_upload_does_not_leave_temporary_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings_module.settings, "upload_dir", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("contract.txt", b"1. Payment terms\nAmount due: $5,000.", "text/plain")},
    )

    assert response.status_code == 200
    assert list(tmp_path.iterdir()) == []


def test_qa_rejects_unbounded_question() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/analyze/qa",
        json={"document_id": "missing", "question": "x" * 2001},
    )

    assert response.status_code == 422


def test_upload_rejects_file_over_size_limit() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("contract.txt", b"x" * (20 * 1024 * 1024 + 1), "text/plain")},
    )

    assert response.status_code == 413


def test_delete_missing_document_returns_not_found() -> None:
    client = TestClient(app)

    response = client.delete("/api/v1/documents/missing")

    assert response.status_code == 404


def test_job_registry_is_bounded_and_document_cleanup_handles_comparisons() -> None:
    jobs.clear()
    jobs["analysis"] = AnalysisJob("analysis", "doc-1", DocumentStatus.COMPLETED, 1)
    jobs["comparison"] = ComparisonJob("comparison", ["doc-1", "doc-2"], DocumentStatus.COMPLETED, 2)

    remove_jobs_for_document("doc-1")
    assert jobs == {}

    for index in range(3):
        jobs[str(index)] = AnalysisJob(str(index), f"doc-{index}", DocumentStatus.COMPLETED, index)
    prune_jobs(max_jobs=2)
    assert set(jobs) == {"1", "2"}
    jobs.clear()