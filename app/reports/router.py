"""Report generation router.

GET /sessions/{session_id}/report
  → streams back a PDF maintenance report for the given session.
"""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import get_user_by_id
from app.dependencies import get_current_user, get_db
from app.documents.models import CaseHistory
from app.reports.generator import generate_session_report
from app.sessions.models import Message
from app.sessions.service import get_session

router = APIRouter(prefix="/sessions", tags=["reports"])


@router.get("/{session_id}/report")
async def download_session_report(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a PDF maintenance report for a session.

    Accessible by the session owner, engineers, and supervisors.
    """
    owner_filter = None if current_user.role == "supervisor" else current_user.id
    session = await get_session(db, session_id, owner_filter)

    # Load ordered message history
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = list(msg_result.scalars().all())

    # Resolve the session owner (may differ from current_user for supervisors)
    technician = await get_user_by_id(db, session.user_id)
    if not technician:
        technician = current_user

    # Pull AI resolution summary if it exists
    case_history = None
    if session.status == "resolved":
        ch_result = await db.execute(
            select(CaseHistory)
            .where(CaseHistory.session_id == session_id)
            .order_by(CaseHistory.created_at.desc())
            .limit(1)
        )
        case_history = ch_result.scalar_one_or_none()

    pdf_bytes = generate_session_report(session, messages, technician, case_history)

    report_number = f"TIY-{str(session_id).upper()[:8]}"
    filename = f"Tiyara_Report_{report_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
