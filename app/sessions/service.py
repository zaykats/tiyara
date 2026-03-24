import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.sessions.models import Message, Session
from app.sessions.schemas import CreateSessionRequest, UpdateSessionRequest


async def create_session(
    db: AsyncSession, user_id: uuid.UUID, payload: CreateSessionRequest
) -> Session:
    session = Session(
        user_id=user_id,
        engine_type=payload.engine_type,
        problem_description=payload.problem_description,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
) -> Session:
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
        .options(selectinload(Session.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if user_id and session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return session


async def list_sessions(db: AsyncSession, user_id: uuid.UUID) -> list[Session]:
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
    )
    return list(result.scalars().all())


async def update_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UpdateSessionRequest,
) -> Session:
    session = await get_session(db, session_id, user_id)
    if payload.status is not None:
        session.status = payload.status
    if payload.problem_description is not None:
        session.problem_description = payload.problem_description
    await db.commit()
    await db.refresh(session)
    return session


async def save_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    structured_content: Optional[dict] = None,
) -> Message:
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        structured_content=structured_content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_message_history(
    db: AsyncSession, session_id: uuid.UUID
) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())
