"""Vector similarity retrieval — SQLite edition.

Because SQLite has no native vector operator, embeddings are loaded into
memory (filtered by engine_type first) and ranked with numpy cosine
similarity.  This is fast enough for the dataset sizes that SQLite is
suited for (tens of thousands of chunks).
"""

from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import embed_query


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a single vector and a matrix of row
    vectors.  Both are assumed to be already L2-normalised (which
    sentence-transformers does when normalize_embeddings=True), so this
    reduces to a simple dot product.
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    normalised = matrix / norms
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        query_norm = 1e-10
    return normalised @ (query_vec / query_norm)


async def retrieve_amm_chunks(
    query: str,
    engine_type: str,
    db: AsyncSession,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Return top-k AMM chunks most similar to *query* for *engine_type*."""
    from app.documents.models import DocumentChunk

    # Pull only rows that have an embedding and match the engine type
    result = await db.execute(
        select(DocumentChunk).where(
            DocumentChunk.engine_type_tag == engine_type,
            DocumentChunk.embedding.is_not(None),
        )
    )
    rows = result.scalars().all()
    if not rows:
        return []

    query_vec = np.array(await embed_query(query), dtype=np.float32)
    matrix = np.array([r.embedding for r in rows], dtype=np.float32)
    scores = _cosine_similarity(query_vec, matrix)

    # Pair each row with its score, sort descending, take top-k
    ranked = sorted(zip(scores.tolist(), rows), key=lambda x: x[0], reverse=True)
    return [
        {
            "id": str(row.id),
            "chunk_text": row.chunk_text,
            "ata_chapter": row.ata_chapter,
            "source_filename": row.source_filename,
            "page_number": row.page_number,
            "similarity": round(score, 4),
        }
        for score, row in ranked[:top_k]
    ]


async def retrieve_case_history(
    query: str,
    engine_type: str,
    db: AsyncSession,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return top-k resolved cases most similar to *query* for *engine_type*."""
    from app.documents.models import CaseHistory

    result = await db.execute(
        select(CaseHistory).where(
            CaseHistory.engine_type == engine_type,
            CaseHistory.embedding.is_not(None),
        )
    )
    rows = result.scalars().all()
    if not rows:
        return []

    query_vec = np.array(await embed_query(query), dtype=np.float32)
    matrix = np.array([r.embedding for r in rows], dtype=np.float32)
    scores = _cosine_similarity(query_vec, matrix)

    ranked = sorted(zip(scores.tolist(), rows), key=lambda x: x[0], reverse=True)
    return [
        {
            "id": str(row.id),
            "resolution_summary": row.resolution_summary,
            "ata_chapter": row.ata_chapter,
            "similarity": round(score, 4),
        }
        for score, row in ranked[:top_k]
    ]
