"""Pluggable storage backend.

Set STORAGE_BACKEND=local    → saves files to ./uploads/ (default, no credentials needed)
Set STORAGE_BACKEND=s3       → uploads go to AWS S3
Set STORAGE_BACKEND=supabase → uploads go to Supabase Storage
"""

import io
import os
from typing import Protocol

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class StorageBackend(Protocol):
    async def upload(self, content: bytes, path: str) -> str:
        """Upload bytes and return the storage path / public URL."""
        ...


# ── Local filesystem implementation ─────────────────────────────────────────

class LocalStorage:
    def __init__(self, base_dir: str = "uploads") -> None:
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    async def upload(self, content: bytes, path: str) -> str:
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path


# ── S3 implementation ────────────────────────────────────────────────────────

class S3Storage:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.S3_BUCKET_NAME

    async def upload(self, content: bytes, path: str) -> str:
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.upload_fileobj(
                io.BytesIO(content), self.bucket, path
            ),
        )
        return f"s3://{self.bucket}/{path}"


# ── Supabase implementation ──────────────────────────────────────────────────

class SupabaseStorage:
    def __init__(self) -> None:
        from supabase import create_client

        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    async def upload(self, content: bytes, path: str) -> str:
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.storage.from_(self.bucket).upload(path, content),
        )
        public_url = (
            self._client.storage.from_(self.bucket).get_public_url(path)
        )
        return public_url


# ── Factory ──────────────────────────────────────────────────────────────────

_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _backend
    if _backend is None:
        if settings.STORAGE_BACKEND == "supabase":
            _backend = SupabaseStorage()
        elif settings.STORAGE_BACKEND == "s3":
            _backend = S3Storage()
        else:
            _backend = LocalStorage()
    return _backend
