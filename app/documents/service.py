import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document, DocumentChunk


async def create_document(
    db: AsyncSession,
    filename: str,
    engine_type_tag: str,
    storage_path: str,
    uploaded_by: uuid.UUID,
) -> Document:
    doc = Document(
        filename=filename,
        engine_type_tag=engine_type_tag,
        storage_path=storage_path,
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(
    db: AsyncSession, engine_type_tag: Optional[str] = None
) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if engine_type_tag:
        query = query.where(Document.engine_type_tag == engine_type_tag)
    result = await db.execute(query)
    return list(result.scalars().all())
