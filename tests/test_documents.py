"""Tests for /documents endpoints: ingest (admin-only) and list."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import make_pdf_bytes


# ingest_pdf and upload_file_to_storage are lazy-imported inside the router
# endpoint function.  We must patch them at their source modules.
_PATCH_STORAGE = patch(
    "app.ingestion.service.upload_file_to_storage",
    new=AsyncMock(return_value="s3://bucket/amm/CFM56-7B/test.pdf"),
)
_PATCH_INGEST = patch(
    "app.ingestion.pdf_ingestion.ingest_pdf",
    new=AsyncMock(return_value=12),
)


# ── Ingestion (admin-only) ────────────────────────────────────────────────────

async def test_ingest_pdf_returns_201_for_admin(client: AsyncClient, admin_headers: dict):
    with _PATCH_STORAGE, _PATCH_INGEST:
        resp = await client.post(
            "/documents/ingest",
            data={"engine_type_tag": "CFM56-7B"},
            files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
            headers=admin_headers,
        )
    assert resp.status_code == 201


async def test_ingest_pdf_returns_correct_fields(client: AsyncClient, admin_headers: dict):
    with _PATCH_STORAGE, _PATCH_INGEST:
        resp = await client.post(
            "/documents/ingest",
            data={"engine_type_tag": "CFM56-7B"},
            files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
            headers=admin_headers,
        )
    body = resp.json()
    assert body["filename"] == "amm.pdf"
    assert body["engine_type_tag"] == "CFM56-7B"
    assert body["chunks_created"] == 12
    assert "document_id" in body
    assert "storage_path" in body


async def test_ingest_pdf_forbidden_for_technician(client: AsyncClient, auth_headers: dict):
    """auth_headers fixture is a technician — must be rejected."""
    with _PATCH_STORAGE, _PATCH_INGEST:
        resp = await client.post(
            "/documents/ingest",
            data={"engine_type_tag": "CFM56-7B"},
            files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 403


async def test_ingest_pdf_requires_auth(client: AsyncClient):
    with _PATCH_STORAGE, _PATCH_INGEST:
        resp = await client.post(
            "/documents/ingest",
            data={"engine_type_tag": "CFM56-7B"},
            files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
        )
    assert resp.status_code == 403


async def test_ingest_pdf_missing_engine_type_returns_422(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/documents/ingest",
        files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ── List documents ────────────────────────────────────────────────────────────

async def test_list_documents_empty_initially(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/documents", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_documents_returns_ingested_doc(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
):
    with _PATCH_STORAGE, _PATCH_INGEST:
        await client.post(
            "/documents/ingest",
            data={"engine_type_tag": "CFM56-7B"},
            files={"file": ("amm.pdf", make_pdf_bytes(), "application/pdf")},
            headers=admin_headers,
        )

    resp = await client.get("/documents", headers=auth_headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "amm.pdf"
    assert docs[0]["engine_type_tag"] == "CFM56-7B"


async def test_list_documents_filter_by_engine_type(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
):
    with _PATCH_STORAGE, _PATCH_INGEST:
        for tag in ("CFM56-7B", "V2500-A5"):
            await client.post(
                "/documents/ingest",
                data={"engine_type_tag": tag},
                files={"file": (f"{tag}.pdf", make_pdf_bytes(), "application/pdf")},
                headers=admin_headers,
            )

    resp = await client.get("/documents?engine_type_tag=CFM56-7B", headers=auth_headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["engine_type_tag"] == "CFM56-7B"


async def test_list_documents_requires_auth(client: AsyncClient):
    resp = await client.get("/documents")
    assert resp.status_code == 403


# ── RAG retrieval (unit) ──────────────────────────────────────────────────────

async def test_retrieve_amm_chunks_returns_empty_when_no_docs(db_session):
    from app.rag.retrieval import retrieve_amm_chunks

    results = await retrieve_amm_chunks("fan vibration", "CFM56-7B", db_session)
    assert results == []


async def test_retrieve_case_history_returns_empty_when_no_cases(db_session):
    from app.rag.retrieval import retrieve_case_history

    results = await retrieve_case_history("fan vibration", "CFM56-7B", db_session)
    assert results == []


async def test_retrieve_amm_chunks_returns_relevant_results(db_session):
    """Insert a real User + Document + Chunk, verify retrieval ranks it."""
    import numpy as np
    from unittest.mock import AsyncMock, patch

    from app.auth.models import User
    from app.auth.utils import hash_password
    from app.documents.models import Document, DocumentChunk
    from app.rag.retrieval import retrieve_amm_chunks

    # Create a real user so the FK constraint on Document.uploaded_by is satisfied
    user = User(
        id=uuid.uuid4(),
        full_name="Test",
        role="engineer",
        company="Acme",
        email="rag_test@acme.com",
        hashed_password=hash_password("pw"),
    )
    db_session.add(user)
    await db_session.commit()

    doc = Document(
        id=uuid.uuid4(),
        filename="amm_test.pdf",
        engine_type_tag="CFM56-7B",
        storage_path="s3://test",
        uploaded_by=user.id,
    )
    db_session.add(doc)
    await db_session.commit()

    embedding = np.random.rand(768).astype(np.float32).tolist()
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        engine_type_tag="CFM56-7B",
        ata_chapter="72-30",
        chunk_text="Fan blade FOD inspection procedure",
        embedding=embedding,
        page_number=1,
        source_filename="amm_test.pdf",
    )
    db_session.add(chunk)
    await db_session.commit()

    # Mock embed_query to return the same vector (perfect cosine similarity = 1.0)
    with patch("app.rag.retrieval.embed_query", new=AsyncMock(return_value=embedding)):
        results = await retrieve_amm_chunks("fan vibration CFM56-7B", "CFM56-7B", db_session)

    assert len(results) == 1
    assert results[0]["chunk_text"] == "Fan blade FOD inspection procedure"
    assert results[0]["ata_chapter"] == "72-30"
    assert "similarity" in results[0]
