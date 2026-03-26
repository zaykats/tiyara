import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


# ── Request schemas ──────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    engine_type: str
    problem_description: str


class UpdateSessionRequest(BaseModel):
    status: Optional[Literal["active", "resolved", "closed"]] = None
    problem_description: Optional[str] = None


# ── Response schemas ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    structured_content: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    engine_type: str
    problem_description: str
    excel_pattern_summary: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    messages: list[MessageResponse] = []
