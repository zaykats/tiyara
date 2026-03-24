"""AMM PDF ingestion pipeline.

Flow:
  1. Extract text page-by-page with pdfplumber
  2. Detect ATA chapter headings to tag each page
  3. Group pages by chapter, split into ~500-token overlapping chunks
  4. Generate embeddings in batch
  5. Persist DocumentChunk rows (with pgvector embeddings)
"""

import re
import uuid
from io import BytesIO
from typing import Optional

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document, DocumentChunk
from app.embeddings import embed_texts

# ATA chapter patterns:  "ATA 72", "ATA 72-30", "CHAPTER 72", "72-00-00"
_ATA_PATTERN = re.compile(
    r"""
    (?:
        ATA\s+(?:CHAPTER\s+)?  # "ATA" optionally followed by "CHAPTER"
        | CHAPTER\s+            # just "CHAPTER"
    )
    (\d{2}(?:[-\s]\d{2})?)     # capture "72" or "72-30"
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _detect_ata_chapter(text: str) -> Optional[str]:
    m = _ATA_PATTERN.search(text)
    if m:
        return m.group(1).strip().replace(" ", "-")
    return None


def _extract_pages(pdf_bytes: bytes) -> list[dict]:
    """Return list of {page_number, text, ata_chapter}."""
    pages: list[dict] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        current_ata: Optional[str] = None
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            ata = _detect_ata_chapter(text)
            if ata:
                current_ata = ata
            pages.append(
                {
                    "page_number": i + 1,
                    "text": text,
                    "ata_chapter": current_ata,
                }
            )
    return pages


_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


async def ingest_pdf(
    pdf_bytes: bytes,
    document: Document,
    db: AsyncSession,
) -> int:
    """Chunk and embed the PDF, persist DocumentChunks. Returns chunk count."""
    pages = _extract_pages(pdf_bytes)

    # Group pages by ATA chapter
    chapter_groups: dict[Optional[str], list[dict]] = {}
    for page in pages:
        key = page["ata_chapter"]
        chapter_groups.setdefault(key, []).append(page)

    all_texts: list[str] = []
    all_meta: list[dict] = []

    for ata_chapter, chapter_pages in chapter_groups.items():
        combined = "\n".join(p["text"] for p in chapter_pages)
        if not combined.strip():
            continue
        chunks = _SPLITTER.split_text(combined)
        first_page = chapter_pages[0]["page_number"]
        for chunk in chunks:
            all_texts.append(chunk)
            all_meta.append(
                {
                    "ata_chapter": ata_chapter,
                    "page_number": first_page,
                }
            )

    if not all_texts:
        return 0

    # Embed in one batch (async, runs in thread pool)
    embeddings = await embed_texts(all_texts)

    for chunk_text, meta, embedding in zip(all_texts, all_meta, embeddings):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            engine_type_tag=document.engine_type_tag,
            ata_chapter=meta["ata_chapter"],
            chunk_text=chunk_text,
            embedding=embedding,
            page_number=meta["page_number"],
            source_filename=document.filename,
        )
        db.add(chunk)

    await db.commit()
    return len(all_texts)
