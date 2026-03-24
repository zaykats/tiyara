"""Tests for /sessions endpoints: CRUD + Excel upload."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import create_test_session, make_excel_bytes

SESSION_PAYLOAD = {
    "engine_type": "CFM56-7B",
    "problem_description": "High vibration N1 during takeoff roll",
}

MOCK_PATTERN_ANALYSIS = {
    "top_faults": ["Engine vibration high"],
    "recurring_components": ["fan bearing"],
    "unresolved_patterns": ["vibration persists after bearing replacement"],
    "time_between_recurrences": 14.5,
    "risk_summary": "Fan bearing failure pattern detected. Root cause not yet addressed.",
}


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_session_returns_201(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/sessions", json=SESSION_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201


async def test_create_session_returns_correct_fields(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/sessions", json=SESSION_PAYLOAD, headers=auth_headers)
    body = resp.json()
    assert body["engine_type"] == SESSION_PAYLOAD["engine_type"]
    assert body["problem_description"] == SESSION_PAYLOAD["problem_description"]
    assert body["status"] == "active"
    assert "id" in body
    assert "user_id" in body
    assert "created_at" in body


async def test_create_session_requires_auth(client: AsyncClient):
    resp = await client.post("/sessions", json=SESSION_PAYLOAD)
    assert resp.status_code == 403


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_sessions_empty_initially(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_sessions_returns_created_sessions(client: AsyncClient, auth_headers: dict):
    await client.post("/sessions", json=SESSION_PAYLOAD, headers=auth_headers)
    await client.post("/sessions", json=SESSION_PAYLOAD, headers=auth_headers)

    resp = await client.get("/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_sessions_only_returns_own_sessions(client: AsyncClient, auth_headers: dict):
    await client.post("/sessions", json=SESSION_PAYLOAD, headers=auth_headers)

    resp2 = await client.post(
        "/auth/signup",
        json={
            "full_name": "Other User",
            "role": "technician",
            "company": "Beta Air",
            "email": "other@beta.com",
            "password": "OtherPass99!",
        },
    )
    other_headers = {"Authorization": f"Bearer {resp2.json()['access_token']}"}

    resp = await client.get("/sessions", headers=other_headers)
    assert resp.json() == []


# ── Get one ───────────────────────────────────────────────────────────────────

async def test_get_session_returns_session(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    resp = await client.get(f"/sessions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_session_includes_messages_list(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    resp = await client.get(f"/sessions/{created['id']}", headers=auth_headers)
    assert "messages" in resp.json()
    assert isinstance(resp.json()["messages"], list)


async def test_get_session_not_found_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/sessions/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_other_users_session_returns_403(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)

    r = await client.post(
        "/auth/signup",
        json={
            "full_name": "Intruder",
            "role": "engineer",
            "company": "X",
            "email": "intruder@x.com",
            "password": "Intrude99!",
        },
    )
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    resp = await client.get(f"/sessions/{created['id']}", headers=other_headers)
    assert resp.status_code == 403


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_session_status_to_resolved(client: AsyncClient, auth_headers: dict):
    # enrich_resolved_session is a lazy import inside the router function;
    # patch it at the source module so the background task is a no-op.
    with patch("app.chat.service.enrich_resolved_session", new=AsyncMock()):
        created = await create_test_session(client, auth_headers)
        resp = await client.patch(
            f"/sessions/{created['id']}",
            json={"status": "resolved"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


async def test_update_session_problem_description(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    new_desc = "Updated: vibration worsens above FL300"
    resp = await client.patch(
        f"/sessions/{created['id']}",
        json={"problem_description": new_desc},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["problem_description"] == new_desc


async def test_update_session_invalid_status_returns_422(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    resp = await client.patch(
        f"/sessions/{created['id']}",
        json={"status": "unknown_status"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── Excel upload ──────────────────────────────────────────────────────────────

async def test_upload_excel_attaches_pattern_summary(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    excel_bytes = make_excel_bytes()

    mock_parse_result = (
        [{"fault_date": "2024-01-01", "fault_description": "Engine vibration high"}],
        MOCK_PATTERN_ANALYSIS,
    )

    # ExcelParser and upload_file_to_storage are lazy-imported inside the
    # endpoint function — patch at their source modules.
    with (
        patch("app.ingestion.excel_parser.ExcelParser") as MockParser,
        patch(
            "app.ingestion.service.upload_file_to_storage",
            new=AsyncMock(return_value="s3://bucket/test.xlsx"),
        ),
    ):
        MockParser.return_value.parse = AsyncMock(return_value=mock_parse_result)

        resp = await client.post(
            f"/sessions/{created['id']}/upload-excel",
            files={
                "file": (
                    "maintenance.xlsx",
                    excel_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers=auth_headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["excel_pattern_summary"] is not None
    assert body["excel_pattern_summary"]["risk_summary"] == MOCK_PATTERN_ANALYSIS["risk_summary"]


async def test_upload_excel_requires_auth(client: AsyncClient, auth_headers: dict):
    created = await create_test_session(client, auth_headers)
    resp = await client.post(
        f"/sessions/{created['id']}/upload-excel",
        files={"file": ("test.xlsx", b"data", "application/octet-stream")},
    )
    assert resp.status_code == 403
