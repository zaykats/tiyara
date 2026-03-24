"""Thin helpers that combine storage + DB operations."""

from app.ingestion.storage import get_storage


async def upload_file_to_storage(content: bytes, filename: str, prefix: str) -> str:
    """Upload raw bytes and return the canonical storage path."""
    import re

    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    path = f"{prefix}/{safe_name}"
    storage = get_storage()
    return await storage.upload(content, path)
