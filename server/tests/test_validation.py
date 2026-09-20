"""Regression tests for upload and API boundary validation."""

from fastapi.testclient import TestClient

from app.main import app
from app.core import settings as settings_module


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


def test_delete_missing_document_returns_not_found() -> None:
    client = TestClient(app)

    response = client.delete("/api/v1/documents/missing")

    assert response.status_code == 404