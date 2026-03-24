"""Tests for POST /chat (SSE streaming)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import create_test_session


# ── SSE mock factory ──────────────────────────────────────────────────────────

def _make_stream_mock(tokens: list[str]):
    """Build a mock for anthropic.messages.stream() context manager."""

    async def _text_stream():
        for t in tokens:
            yield t

    stream_obj = MagicMock()
    stream_obj.text_stream = _text_stream()

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=stream_obj)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _parse_sse(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of JSON payloads."""
    events = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_chat_returns_200_sse(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)

    stream_mock = _make_stream_mock(["Hello ", "technician."])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        resp = await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "What is the likely cause?",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


async def test_chat_sse_contains_content_events(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)

    stream_mock = _make_stream_mock(["Check ", "the ", "fan."])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        resp = await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "How do I fix it?",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    events = _parse_sse(resp.text)
    content_events = [e for e in events if e.get("type") == "content"]
    assert len(content_events) == 3  # one per token
    assert content_events[0]["text"] == "Check "
    assert content_events[1]["text"] == "the "
    assert content_events[2]["text"] == "fan."


async def test_chat_sse_ends_with_done_event(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)

    stream_mock = _make_stream_mock(["Done."])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        resp = await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "Anything else?",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    events = _parse_sse(resp.text)
    assert events[-1] == {"type": "done"}


async def test_chat_saves_user_and_assistant_messages(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)

    stream_mock = _make_stream_mock(["Roger that."])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "Describe the issue",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    # Retrieve session and check messages were persisted
    detail_resp = await client.get(f"/sessions/{session['id']}", headers=auth_headers)
    messages = detail_resp.json()["messages"]

    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


async def test_chat_full_response_assembled_correctly(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)
    tokens = ["Step ", "1: ", "Inspect fan."]

    stream_mock = _make_stream_mock(tokens)

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "Give me steps",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    detail = await client.get(f"/sessions/{session['id']}", headers=auth_headers)
    assistant_msgs = [m for m in detail.json()["messages"] if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["content"] == "".join(tokens)


async def test_chat_detects_step_guide_json(client: AsyncClient, auth_headers: dict):
    """If assistant response is a step_guide JSON blob it should be stored in structured_content."""
    session = await create_test_session(client, auth_headers)

    step_guide = json.dumps({
        "type": "step_guide",
        "title": "Fault Isolation Procedure — Engine Vibration",
        "steps": [
            {
                "number": 1,
                "title": "Initial inspection",
                "instruction": "Inspect the fan blades for FOD damage.",
                "warning": None,
                "amm_reference": "AMM 72-30-00",
            }
        ],
        "closing_note": "Return aircraft to service only after supervisor sign-off.",
    })

    stream_mock = _make_stream_mock([step_guide])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "Give me the full procedure",
                "conversation_history": [],
            },
            headers=auth_headers,
        )

    detail = await client.get(f"/sessions/{session['id']}", headers=auth_headers)
    assistant_msgs = [m for m in detail.json()["messages"] if m["role"] == "assistant"]
    sc = assistant_msgs[0]["structured_content"]
    assert sc is not None
    assert sc["type"] == "step_guide"
    assert sc["title"] == "Fault Isolation Procedure — Engine Vibration"


async def test_chat_requires_auth(client: AsyncClient, auth_headers: dict):
    session = await create_test_session(client, auth_headers)
    resp = await client.post(
        "/chat",
        json={"session_id": session["id"], "user_message": "Hi", "conversation_history": []},
    )
    assert resp.status_code == 403


async def test_chat_with_conversation_history(client: AsyncClient, auth_headers: dict):
    """Conversation history should be forwarded to Claude."""
    session = await create_test_session(client, auth_headers)

    stream_mock = _make_stream_mock(["Understood."])

    with patch("app.chat.service._anthropic") as mock_client:
        mock_client.messages.stream.return_value = stream_mock
        resp = await client.post(
            "/chat",
            json={
                "session_id": session["id"],
                "user_message": "Clarify step 2",
                "conversation_history": [
                    {"role": "user", "content": "Give me the steps"},
                    {"role": "assistant", "content": "Step 1: Inspect. Step 2: Replace."},
                ],
            },
            headers=auth_headers,
        )

    assert resp.status_code == 200
    # Verify Claude was called and received history (2) + current message (1)
    assert mock_client.messages.stream.called
    messages_sent = mock_client.messages.stream.call_args.kwargs["messages"]
    assert len(messages_sent) == 3
