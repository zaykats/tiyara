from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.schemas import ChatRequest
from app.chat.service import stream_chat_response
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stream a chat response via Server-Sent Events (SSE).

    The client should consume the response as an event stream.
    Each event has the shape:
        data: {"type": "content", "text": "<token>"}
        data: {"type": "done"}
    """
    return StreamingResponse(
        stream_chat_response(request, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
