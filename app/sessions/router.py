import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.sessions.schemas import (
    CreateSessionRequest,
    SessionDetailResponse,
    SessionResponse,
    UpdateSessionRequest,
)
from app.sessions.service import (
    create_session,
    get_session,
    list_sessions,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_session(db, current_user.id, payload)


@router.get("", response_model=list[SessionResponse])
async def list_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_users = current_user.role == "supervisor"
    sessions = await list_sessions(db, current_user.id, all_users=all_users)

    if all_users:
        # Attach creator name for supervisor view
        from sqlalchemy import select as sa_select
        user_ids = list({s.user_id for s in sessions})
        result = await db.execute(sa_select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.full_name for u in result.scalars().all()}
        response = []
        for s in sessions:
            d = SessionResponse.model_validate(s)
            d.created_by = users_map.get(s.user_id)
            response.append(d)
        return response

    return sessions


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_one(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Supervisors can view any session
    owner_filter = None if current_user.role == "supervisor" else current_user.id
    return await get_session(db, session_id, owner_filter)


@router.patch("/{session_id}", response_model=SessionResponse)
async def patch(
    session_id: uuid.UUID,
    payload: UpdateSessionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only engineers and supervisors can mark sessions as resolved
    if payload.status == "resolved" and current_user.role == "technician":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only engineers and supervisors can mark sessions as resolved.")

    owner_filter = None if current_user.role == "supervisor" else current_user.id
    session = await update_session(db, session_id, owner_filter, payload)

    if payload.status == "resolved":
        from app.chat.service import enrich_resolved_session
        background_tasks.add_task(enrich_resolved_session, session_id)

    return session


@router.post("/{session_id}/upload-excel", response_model=SessionResponse)
async def upload_excel(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an Excel maintenance log and attach parsed data to the session."""
    from app.ingestion.excel_parser import ExcelParser
    from app.ingestion.service import upload_file_to_storage
    from app.sessions.service import get_session

    session = await get_session(db, session_id, current_user.id)

    content = await file.read()

    # Store raw file
    storage_path = await upload_file_to_storage(
        content, file.filename or "upload.xlsx", f"excel/{session_id}"
    )

    # Parse and analyse
    parser = ExcelParser()
    normalized_records, pattern_analysis = await parser.parse(content, file.filename or "upload.xlsx")

    session.excel_normalized_data = normalized_records
    session.excel_pattern_summary = pattern_analysis
    await db.commit()
    await db.refresh(session)
    return session
