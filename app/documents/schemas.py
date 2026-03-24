import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    engine_type_tag: str
    storage_path: str
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    engine_type_tag: str
    ata_chapter: Optional[str] = None
    chunk_text: str
    page_number: Optional[int] = None
    source_filename: str

    model_config = {"from_attributes": True}


class CaseHistoryResponse(BaseModel):
    id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    engine_type: str
    ata_chapter: Optional[str] = None
    resolution_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    engine_type_tag: str
    chunks_created: int
    storage_path: str
