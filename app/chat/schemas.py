import uuid
from typing import Any, Optional

from pydantic import BaseModel


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    user_message: str
    conversation_history: list[ConversationMessage] = []
