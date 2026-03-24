from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.documents.router import router as documents_router
from app.sessions.router import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all SQLite tables (idempotent — safe to run every startup)
    from app.database import create_all_tables

    await create_all_tables()

    # Pre-load the embedding model so the first request isn't slow
    from app.embeddings import get_embedding_model

    get_embedding_model()
    yield


app = FastAPI(
    title="Tiyara API",
    description="Aviation maintenance AI backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
