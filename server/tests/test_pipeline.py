"""End-to-end pipeline tests using the sample contract (demo mode, no API key)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.chunker import DocumentChunker
from app.services.documents import documents
from app.services.glossary import explain_term_offline
from app.services.llm import llm_service
from app.services.vector_store import vector_store
from app.core import settings as settings_module

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "sample-contract.txt"
SAMPLE_V2 = Path(__file__).resolve().parents[2] / "samples" / "sample-contract-v2.txt"


def test_chunker_splits_sample_contract() -> None:
    text = SAMPLE.read_text(encoding="utf-8")
    chunker = DocumentChunker()
    clauses = chunker.chunk_document("doc-test", [{"text": text, "page_number": 1, "start_pos": 0, "end_pos": len(text)}])
    assert len(clauses) >= 5
    assert all(c.text.strip() for c in clauses)
    # Offsets must be non-decreasing and within bounds.
    positions = [(c.start_pos, c.end_pos) for c in clauses]
    assert all(s < e for s, e in positions)


def test_demo_classify_flags_indemnification() -> None:
    out = asyncio.run(
        llm_service.generate_classification("contract", "", "c1", "Contractor shall indemnify and hold harmless Client.")
    )
    assert out["category"] == "liability_indemnification"
    assert out["attention_level"] == "high"


def test_demo_qa_out_of_scope() -> None:
    out = asyncio.run(llm_service.generate_qa("contract", "", "Payment is $5,000.", "Who won the World Cup?"))
    assert "couldn't find" in out["answer"]
    assert out["disclaimer_needed"] is True


def test_glossary_offline() -> None:
    assert "arbitrator" in explain_term_offline("arbitration")["definition"]


def test_document_registry_evicts_oldest_document_and_vector_collection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings_module.settings, "max_documents", 1)
    client = TestClient(app)

    first = client.post(
        "/api/v1/upload",
        files={"file": ("first.txt", b"First contract text", "text/plain")},
    ).json()
    vector_store.add_collection(f"doc_{first['document_id']}")

    second = client.post(
        "/api/v1/upload",
        files={"file": ("second.txt", b"Second contract text", "text/plain")},
    ).json()

    assert documents.get(first["document_id"]) is None
    assert vector_store.query(f"doc_{first['document_id']}") == []
    assert documents.get(second["document_id"]) is not None


def test_vector_store_returns_no_results_for_non_positive_limit() -> None:
    vector_store.add_document("test-limit", "doc-limit", [{"text": "contract terms"}])

    assert vector_store.query("test-limit", "contract", top_k=0) == []
    assert vector_store.query("test-limit", "contract", top_k=-1) == []
    vector_store.clear_collection("test-limit")


def test_upload_then_qa_checklist_compare() -> None:
    client = TestClient(app)
    with open(SAMPLE, "rb") as f:
        r1 = client.post(
            "/api/v1/upload",
            files={"file": ("sample-contract.txt", f, "text/plain")},
            data={"document_type": "contract", "jurisdiction": "California"},
        )
    assert r1.status_code == 200, r1.text
    doc1 = r1.json()["document_id"]
    assert r1.json()["clause_count"] >= 5

    with open(SAMPLE_V2, "rb") as f:
        r2 = client.post(
            "/api/v1/upload",
            files={"file": ("sample-contract-v2.txt", f, "text/plain")},
            data={"document_type": "contract", "jurisdiction": "California"},
        )
    assert r2.status_code == 200, r2.text
    doc2 = r2.json()["document_id"]

    clauses = client.get(f"/api/v1/documents/{doc1}").json()["clauses"]
    first_id = clauses[0]["clause_id"]
    simp = client.post(f"/api/v1/analyze/simplify/{first_id}", params={"document_id": doc1}).json()
    assert simp["simplified_text"]
    cls = client.post(
        f"/api/v1/analyze/classify/{first_id}", params={"document_id": doc1}
    ).json()
    assert cls["category"]

    qa = client.post(
        "/api/v1/analyze/qa",
        json={"document_id": doc1, "question": "What are my termination rights?"},
    ).json()
    assert qa["answer"]

    check = client.post(
        "/api/v1/analyze/checklist", json={"document_id": doc1}
    ).json()
    assert check["action_items"] and check["questions_for_lawyer"]

    comp = client.post(
        "/api/v1/analyze/compare", params={"document_id_1": doc1, "document_id_2": doc2}
    ).json()
    assert comp["changes"]

    assert client.delete(f"/api/v1/documents/{doc1}").status_code == 200
    assert documents.get(doc1) is None
    assert vector_store.query(f"doc_{doc1}", document_id=doc1) == []
