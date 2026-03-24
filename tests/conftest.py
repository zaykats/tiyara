"""
Shared fixtures for the Tiyara test suite.

Strategy
--------
* Each test function gets its own fresh SQLite file (isolated, no bleed-over).
* The FastAPI dependency get_db is overridden to point at that file.
* Redis is mocked (AsyncMock) — no Redis server required.
* The sentence-transformers model is mocked — no GPU / download during CI.
* The Anthropic client is mocked per-test where needed.
* Storage uploads are mocked so S3/Supabase credentials are not required.
"""

import io
import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import openpyxl
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# ── Embedding model mock ──────────────────────────────────────────────────────

def _make_mock_model():
    """Returns a mock that behaves like SentenceTransformer.encode()."""
    model = MagicMock()

    def _encode(texts, **kwargs):
        n = len(texts) if isinstance(texts, (list, tuple)) else 1
        return np.random.rand(n, 768).astype(np.float32)

    model.encode = MagicMock(side_effect=_encode)
    return model


# ── Per-test isolated database ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    db_path = f"./test_{uuid.uuid4().hex}.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    # Register all models so Base.metadata knows about them
    from app.database import Base
    import app.auth.models       # noqa: F401
    import app.sessions.models   # noqa: F401
    import app.documents.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()
    try:
        os.remove(db_path)
    except FileNotFoundError:
        pass


# ── Redis mock ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.exists = AsyncMock(return_value=0)
    r.setex = AsyncMock(return_value=True)
    return r


# ── HTTP test client ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.database import get_db
    from app.dependencies import get_redis

    async def _override_db():
        yield db_session

    async def _override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    mock_model = _make_mock_model()

    with (
        patch("app.embeddings._load_model", return_value=mock_model),
        patch("app.database.create_all_tables", new=AsyncMock()),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ── Signed-in user helpers ────────────────────────────────────────────────────

TECHNICIAN = {
    "full_name": "Test Tech",
    "role": "technician",
    "company": "Acme Air",
    "email": "tech@acme.com",
    "password": "TestPass123!",
}

SUPERVISOR = {
    "full_name": "Admin User",
    "role": "supervisor",
    "company": "Acme Air",
    "email": "admin@acme.com",
    "password": "AdminPass123!",
}


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    resp = await client.post("/auth/signup", json=TECHNICIAN)
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict:
    resp = await client.post("/auth/signup", json=SUPERVISOR)
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── Helper: create a session via API ─────────────────────────────────────────

async def create_test_session(client: AsyncClient, headers: dict) -> dict:
    resp = await client.post(
        "/sessions",
        json={"engine_type": "CFM56-7B", "problem_description": "Vibration on takeoff"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Helper: in-memory Excel file ─────────────────────────────────────────────

def make_excel_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Maintenance Log"
    ws.append(["Date", "ATA Chapter", "Fault Code", "Fault Description",
               "Action Taken", "Part Number", "Flight Hours", "Status"])
    ws.append(["2024-01-01", "72-30", "E001", "Engine vibration high",
               "Replaced fan bearing", "PN-12345", 1500, "Resolved"])
    ws.append(["2024-01-15", "72-30", "E001", "Engine vibration recurred",
               "Balanced fan blades", "PN-12345", 1600, "Resolved"])
    ws.append(["2024-02-01", "72-30", "E001", "Vibration still present",
               "Replaced fan disk", "PN-12346", 1700, "Open"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ── Helper: minimal PDF bytes ─────────────────────────────────────────────────

def make_pdf_bytes() -> bytes:
    """Minimal valid PDF with one page of text."""
    content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (ATA CHAPTER 72 Engine) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000368 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""
    return content
