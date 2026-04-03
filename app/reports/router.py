"""Report generation router.

Endpoints:
  GET /sessions/{session_id}/report               — Diagnostic report (PDF)
  GET /sessions/{session_id}/report/finding-input — Finding Input Form (PDF)
  GET /sessions/{session_id}/report/ai-analysis   — AI Analysis & Recommendations (PDF)
  GET /sessions/{session_id}/report/capability    — Capability Analysis (PDF)
  GET /sessions/{session_id}/report/service-order — Service Order / Ordre de Service (PDF)
  GET /sessions/{session_id}/report/kcc           — KCC Draft (PDF)

All endpoints accept an optional `?lang=en` (default) or `?lang=fr` query param.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import get_user_by_id
from app.dependencies import get_current_user, get_db
from app.documents.models import CaseHistory
from app.reports.ai_analysis import generate_ai_analysis
from app.reports.capability import generate_capability
from app.reports.finding_input import generate_finding_input
from app.reports.generator import generate_session_report
from app.reports.kcc import generate_kcc
from app.reports.service_order import generate_service_order
from app.reports.translations import Lang
from app.sessions.models import Message
from app.sessions.service import get_session

router = APIRouter(prefix="/sessions", tags=["reports"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


async def _load_session_data(
    db: AsyncSession,
    session_id: uuid.UUID,
    current_user: User,
) -> tuple:
    """Load session, messages, technician, and case_history."""
    owner_filter = None if current_user.role == "supervisor" else current_user.id
    session = await get_session(db, session_id, owner_filter)

    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = list(msg_result.scalars().all())

    technician = await get_user_by_id(db, session.user_id)
    if not technician:
        technician = current_user

    case_history = None
    if session.status == "resolved":
        ch_result = await db.execute(
            select(CaseHistory)
            .where(CaseHistory.session_id == session_id)
            .order_by(CaseHistory.created_at.desc())
            .limit(1)
        )
        case_history = ch_result.scalar_one_or_none()

    return session, messages, technician, case_history


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{session_id}/report")
async def download_diagnostic_report(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return the main diagnostic PDF report."""
    session, messages, technician, case_history = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_session_report(session, messages, technician, case_history, lang=lang)
    ref = f"TIY-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_Report_{ref}{suffix}.pdf")


@router.get("/{session_id}/report/finding-input")
async def download_finding_input(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate Finding Input Form PDF."""
    session, messages, technician, _ = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_finding_input(session, technician, lang=lang)
    ref = f"FI-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_FindingInput_{ref}{suffix}.pdf")


@router.get("/{session_id}/report/ai-analysis")
async def download_ai_analysis(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate AI Analysis & Recommendations PDF."""
    session, messages, technician, case_history = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_ai_analysis(session, messages, technician, case_history, lang=lang)
    ref = f"AA-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_AIAnalysis_{ref}{suffix}.pdf")


@router.get("/{session_id}/report/capability")
async def download_capability(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate Capability Analysis PDF."""
    session, messages, technician, _ = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_capability(session, messages, technician, lang=lang)
    ref = f"CA-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_Capability_{ref}{suffix}.pdf")


@router.get("/{session_id}/report/service-order")
async def download_service_order(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate Service Order (Ordre de Service) PDF."""
    session, messages, technician, _ = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_service_order(session, messages, technician, lang=lang)
    ref = f"OS-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_ServiceOrder_{ref}{suffix}.pdf")


@router.get("/{session_id}/report/kcc")
async def download_kcc(
    session_id: uuid.UUID,
    lang: Lang = Query(default="en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate KCC (Keepership Concern Communication) Draft PDF."""
    session, messages, technician, _ = await _load_session_data(
        db, session_id, current_user
    )
    pdf = generate_kcc(session, messages, technician, lang=lang)
    ref = f"KCC-{str(session_id).upper()[:8]}"
    suffix = "_FR" if lang == "fr" else ""
    return _pdf_response(pdf, f"Tiyara_KCC_{ref}{suffix}.pdf")
