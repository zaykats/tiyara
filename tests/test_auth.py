"""Tests for /auth endpoints: signup, signin, refresh."""

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_USER = {
    "full_name": "Jane Doe",
    "role": "engineer",
    "company": "AeroFix",
    "email": "jane@aerofix.com",
    "password": "SecurePass!99",
}


async def _signup(client: AsyncClient, payload: dict = VALID_USER) -> dict:
    resp = await client.post("/auth/signup", json=payload)
    return resp


# ── Sign-up ───────────────────────────────────────────────────────────────────

async def test_signup_returns_201_with_tokens(client: AsyncClient):
    resp = await _signup(client)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_signup_returns_user_fields(client: AsyncClient):
    resp = await _signup(client)
    user = resp.json()["user"]
    assert user["email"] == VALID_USER["email"]
    assert user["full_name"] == VALID_USER["full_name"]
    assert user["role"] == VALID_USER["role"]
    assert user["company"] == VALID_USER["company"]
    assert "id" in user
    assert "created_at" in user
    # Password must never appear in response
    assert "password" not in user
    assert "hashed_password" not in user


async def test_signup_duplicate_email_returns_409(client: AsyncClient):
    await _signup(client)  # first signup
    resp = await _signup(client)  # same email
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()


async def test_signup_invalid_role_returns_422(client: AsyncClient):
    payload = {**VALID_USER, "role": "pilot"}  # not in enum
    resp = await _signup(client, payload)
    assert resp.status_code == 422


async def test_signup_invalid_email_returns_422(client: AsyncClient):
    payload = {**VALID_USER, "email": "not-an-email"}
    resp = await _signup(client, payload)
    assert resp.status_code == 422


async def test_signup_missing_fields_returns_422(client: AsyncClient):
    resp = await client.post("/auth/signup", json={"email": "x@x.com"})
    assert resp.status_code == 422


# ── Sign-in ───────────────────────────────────────────────────────────────────

async def test_signin_success(client: AsyncClient):
    await _signup(client)
    resp = await client.post(
        "/auth/signin",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_signin_wrong_password_returns_401(client: AsyncClient):
    await _signup(client)
    resp = await client.post(
        "/auth/signin",
        json={"email": VALID_USER["email"], "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


async def test_signin_unknown_email_returns_401(client: AsyncClient):
    resp = await client.post(
        "/auth/signin",
        json={"email": "nobody@nowhere.com", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_signin_returns_correct_user(client: AsyncClient):
    await _signup(client)
    resp = await client.post(
        "/auth/signin",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert resp.json()["user"]["email"] == VALID_USER["email"]


# ── Refresh ───────────────────────────────────────────────────────────────────

async def test_refresh_returns_new_tokens(client: AsyncClient):
    signup_resp = await _signup(client)
    refresh_token = signup_resp.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401


async def test_refresh_with_access_token_returns_401(client: AsyncClient):
    """Passing an access token to the refresh endpoint must be rejected."""
    signup_resp = await _signup(client)
    access_token = signup_resp.json()["access_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


# ── Protected endpoints ───────────────────────────────────────────────────────

async def test_protected_endpoint_no_token_returns_403(client: AsyncClient):
    resp = await client.get("/sessions")
    assert resp.status_code == 403


async def test_protected_endpoint_bad_token_returns_401(client: AsyncClient):
    # HTTPBearer accepts the header format but the JWT decode fails → 401
    resp = await client.get(
        "/sessions", headers={"Authorization": "Bearer garbage.token.here"}
    )
    assert resp.status_code == 401


async def test_access_token_authenticates_protected_endpoint(client: AsyncClient):
    signup_resp = await _signup(client)
    token = signup_resp.json()["access_token"]
    resp = await client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
