import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


# ── Request schemas ──────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    full_name: str
    role: Literal["technician", "engineer", "supervisor"]
    company: str
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Response schemas ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    role: str
    company: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
