"""Singleton wrapper around a sentence-transformers embedding model.

The model is downloaded on first access and cached in memory for the
lifetime of the process.  Encoding is CPU-bound, so public helpers run
the call in a thread-pool executor to keep the async event loop free.
"""

import asyncio
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def get_embedding_model() -> SentenceTransformer:
    return _load_model()


def embed_texts_sync(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


async def embed_texts(texts: List[str]) -> List[List[float]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, embed_texts_sync, texts)


async def embed_query(query: str) -> List[float]:
    results = await embed_texts([query])
    return results[0]
