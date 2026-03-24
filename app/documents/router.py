from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db, require_admin
from app.documents.schemas import DocumentResponse, IngestResponse
from app.documents.service import create_document, list_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_amm(
    engine_type_tag: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin-only: upload and ingest an AMM PDF into the vector store."""
    from app.ingestion.pdf_ingestion import ingest_pdf
    from app.ingestion.service import upload_file_to_storage

    content = await file.read()
    filename = file.filename or "document.pdf"

    storage_path = await upload_file_to_storage(
        content, filename, f"amm/{engine_type_tag}"
    )

    doc = await create_document(
        db,
        filename=filename,
        engine_type_tag=engine_type_tag,
        storage_path=storage_path,
        uploaded_by=current_user.id,
    )

    chunks_created = await ingest_pdf(content, doc, db)

    return IngestResponse(
        document_id=doc.id,
        filename=doc.filename,
        engine_type_tag=doc.engine_type_tag,
        chunks_created=chunks_created,
        storage_path=doc.storage_path,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_docs(
    engine_type_tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_documents(db, engine_type_tag)
