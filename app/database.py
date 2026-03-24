import json
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import Text, TypeDecorator

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # required for SQLite
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── SQLite: enable foreign-key enforcement on every new connection ────────────

@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Custom column type: stores float lists as JSON text ──────────────────────

class EmbeddingVector(TypeDecorator):
    """Stores a list[float] as a JSON string in a TEXT column."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> list[float] | None:
        if value is None:
            return None
        return json.loads(value)


# ── ORM base ─────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Session dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:  # type: ignore[override]
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Table creation helper (run once on startup) ───────────────────────────────

async def create_all_tables() -> None:
    """Create all tables defined via SQLAlchemy models (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
