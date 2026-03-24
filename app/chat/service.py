"""Core chat logic: RAG retrieval, prompt construction, SSE streaming,
and post-resolution knowledge enrichment.
"""

import json
import uuid
from typing import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.agent import build_system_prompt
from app.chat.schemas import ChatRequest
from app.config import settings
from app.database import AsyncSessionLocal
from app.embeddings import embed_texts
from app.rag.retrieval import retrieve_amm_chunks, retrieve_case_history
from app.sessions.service import get_message_history, get_session, save_message


_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _try_parse_structured(text: str) -> dict | None:
    """If the assistant response contains a JSON step_guide, extract it."""
    try:
        if "```json" in text:
            raw = text.split("```json")[1].split("```")[0].strip()
        elif text.strip().startswith("{"):
            raw = text.strip()
        else:
            return None
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and parsed.get("type") == "step_guide":
            return parsed
    except (json.JSONDecodeError, IndexError):
        pass
    return None


async def stream_chat_response(
    request: ChatRequest,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Retrieve context → build prompt → stream Claude response via SSE.

    Each yielded value is a raw SSE line, e.g.:
        data: {"type": "content", "text": "..."}\n\n
        data: {"type": "done"}\n\n
    """
    # ── Load session ──────────────────────────────────────────────────────────
    session = await get_session(db, request.session_id)
    query = f"{session.engine_type} {request.user_message}"

    # ── RAG retrieval ─────────────────────────────────────────────────────────
    amm_chunks = await retrieve_amm_chunks(query, session.engine_type, db)
    case_matches = await retrieve_case_history(query, session.engine_type, db)

    # ── Build system prompt ───────────────────────────────────────────────────
    system_prompt = build_system_prompt(
        amm_chunks=amm_chunks,
        case_history_matches=case_matches,
        excel_pattern_summary=session.excel_pattern_summary,
        session_problem_description=session.problem_description,
        engine_type=session.engine_type,
    )

    # ── Persist user message ──────────────────────────────────────────────────
    await save_message(db, request.session_id, "user", request.user_message)

    # ── Build messages list for Claude ────────────────────────────────────────
    history = [
        {"role": m.role, "content": m.content}
        for m in request.conversation_history
    ]
    # Always append the current user message
    history.append({"role": "user", "content": request.user_message})

    # ── Stream ────────────────────────────────────────────────────────────────
    full_response = ""
    stream = await _openai.chat.completions.create(
        model=settings.OPENAI_MODEL,
        max_tokens=4096,
        messages=[{"role": "system", "content": system_prompt}] + history,
        stream=True,
    )
    async for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        if text:
            full_response += text
            payload = json.dumps({"type": "content", "text": text})
            yield f"data: {payload}\n\n"

    # ── Persist assistant response ────────────────────────────────────────────
    structured = _try_parse_structured(full_response)
    await save_message(
        db,
        request.session_id,
        "assistant",
        full_response,
        structured_content=structured,
    )

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ── Knowledge enrichment on resolution ───────────────────────────────────────

async def enrich_resolved_session(session_id: uuid.UUID) -> None:
    """
    Background task: generate a structured resolution summary from the full
    chat log and store it in case_history with a vector embedding.
    """
    async with AsyncSessionLocal() as db:
        try:
            session = await get_session(db, session_id)
            messages = await get_message_history(db, session_id)

            if not messages:
                return

            # Build a transcript
            transcript = "\n".join(
                f"{m.role.upper()}: {m.content}" for m in messages
            )

            prompt = (
                "You are an aircraft maintenance documentation specialist. "
                "Based on the following maintenance troubleshooting chat session, "
                "generate a structured resolution summary as a JSON object with these fields:\n"
                "- fault_description: brief description of the fault\n"
                "- root_cause: identified root cause\n"
                "- steps_applied: array of the key steps taken\n"
                "- outcome: whether the fault was resolved and how\n"
                "- ata_chapter: the primary ATA chapter involved (string or null)\n\n"
                "Return only valid JSON.\n\n"
                f"Transcript:\n{transcript}"
            )

            resp = await _openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = resp.choices[0].message.content.strip()
            try:
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                summary_json = json.loads(raw_text)
            except json.JSONDecodeError:
                summary_json = {"raw": raw_text}

            summary_text = json.dumps(summary_json)

            # Embed the summary
            embeddings = await embed_texts([summary_text])
            embedding = embeddings[0]

            # Determine ATA chapter
            ata = summary_json.get("ata_chapter")

            # Store in case_history
            from app.documents.models import CaseHistory

            case = CaseHistory(
                session_id=session_id,
                engine_type=session.engine_type,
                ata_chapter=ata,
                resolution_summary=summary_text,
                embedding=embedding,
            )
            db.add(case)
            await db.commit()
        except Exception:
            # Background tasks must not crash silently — log and swallow
            import traceback

            traceback.print_exc()
