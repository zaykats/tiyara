# Tiyara API

Aviation maintenance AI backend — FastAPI + PostgreSQL/pgvector + Claude.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| SQLite | 3.35+ (ships with Python) |
| Redis | 7+ |
| AWS S3 **or** Supabase | for file storage |

---

## Quick start

### 1. Clone & install

```bash
git clone <repo-url>
cd tiyara
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> **Note:** `sentence-transformers` will download the `BAAI/bge-base-en-v1.5` model
> (~440 MB) on first run.  This is cached locally for subsequent starts.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in every value
```

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./tiyara.db` (default, no config needed) |
| `REDIS_URL` | `redis://localhost:6379` |
| `SECRET_KEY` | Random string ≥ 32 chars |
| `ANTHROPIC_API_KEY` | Your Claude API key |
| `STORAGE_BACKEND` | `s3` or `supabase` |

### 3. Create the database schema

Tables are created **automatically** when the server starts (via SQLAlchemy
`create_all`).  You can also create them manually:

```bash
sqlite3 tiyara.db < migrations/init.sql
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: http://localhost:8000/docs

---

## Project structure

```
tiyara/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Pydantic settings (loads .env)
│   ├── database.py          # Async SQLAlchemy engine & session
│   ├── dependencies.py      # get_current_user, get_db, get_redis
│   ├── embeddings.py        # sentence-transformers singleton
│   │
│   ├── auth/                # JWT sign-up / sign-in / refresh
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── utils.py         # bcrypt + JWT helpers
│   │   ├── service.py
│   │   └── router.py        # POST /auth/signup|signin|refresh
│   │
│   ├── sessions/            # Maintenance sessions
│   │   ├── models.py        # Session, Message
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── router.py        # CRUD + Excel upload
│   │
│   ├── chat/                # Streaming AI chat agent
│   │   ├── schemas.py
│   │   ├── agent.py         # System prompt builder
│   │   ├── service.py       # SSE streaming + knowledge enrichment
│   │   └── router.py        # POST /chat (SSE)
│   │
│   ├── documents/           # AMM document management
│   │   ├── models.py        # Document, DocumentChunk, CaseHistory
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── router.py        # POST /documents/ingest (admin)
│   │
│   ├── ingestion/           # File parsing pipelines
│   │   ├── excel_parser.py  # Flexible Claude-powered Excel parser
│   │   ├── pdf_ingestion.py # ATA-aware PDF chunker + embedder
│   │   ├── storage.py       # S3 / Supabase storage backends
│   │   └── service.py       # upload_file_to_storage helper
│   │
│   └── rag/
│       └── retrieval.py     # pgvector similarity search
│
├── migrations/
│   └── init.sql             # Full schema + pgvector indexes
├── .env.example
├── requirements.txt
└── README.md
```

---

## API overview

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/signin` | Obtain access + refresh tokens |
| POST | `/auth/refresh` | Rotate tokens using a refresh token |

### Sessions

| Method | Path | Description |
|---|---|---|
| POST | `/sessions` | Create a new maintenance session |
| GET | `/sessions` | List all sessions for current user |
| GET | `/sessions/{id}` | Get session with message history |
| PATCH | `/sessions/{id}` | Update status / description |
| POST | `/sessions/{id}/upload-excel` | Parse & attach Excel maintenance log |

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/chat` | Stream an AI response (SSE) |

#### SSE event format

```
data: {"type": "content", "text": "<token>"}\n\n
data: {"type": "done"}\n\n
```

When the assistant produces a step-by-step guide the full `content`
accumulates into the structured `step_guide` JSON schema (stored in
`messages.structured_content`).

### Documents (admin only)

| Method | Path | Description |
|---|---|---|
| POST | `/documents/ingest` | Upload & ingest an AMM PDF |
| GET | `/documents` | List documents (filter by engine_type_tag) |

---

## How each pipeline works

### Excel parsing

1. Accept `.xlsx` / `.xls` upload
2. If multiple sheets exist → ask Claude to identify the maintenance log sheet
3. Extract headers + 10-row sample → ask Claude to map to standard fields
4. Normalise the full dataframe using the returned mapping
5. Ask Claude for pattern analysis (top faults, recurring components, risk)
6. Store `excel_normalized_data` and `excel_pattern_summary` on the session

### AMM ingestion

1. Extract text page-by-page with `pdfplumber`
2. Detect ATA chapter headings via regex
3. Group pages by chapter, split into 500-token overlapping chunks
4. Batch-embed all chunks with `BAAI/bge-base-en-v1.5`
5. Store in `document_chunks` with pgvector IVFFlat index

### RAG retrieval

Triggered automatically on every `/chat` request:

- Top-8 AMM chunks (cosine similarity, filtered by `engine_type_tag`)
- Top-3 resolved case histories (cosine similarity, filtered by `engine_type`)
- Both sets injected into the system prompt

### Knowledge enrichment

When `PATCH /sessions/{id}` sets `status = "resolved"`:

1. Background task reads full message history
2. Claude generates a structured resolution summary (JSON)
3. Summary is embedded and stored in `case_history`
4. Future RAG queries can retrieve this resolved case

---

## Roles and permissions

| Role | Permissions |
|---|---|
| `technician` | Create sessions, chat, upload Excel |
| `engineer` | All technician permissions + ingest AMM PDFs |
| `supervisor` | All engineer permissions |

---

## Embedding model

Default: `BAAI/bge-base-en-v1.5` (768-dimensional, MIT licence).

To switch models update `.env`:

```
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024
```

Then re-run `migrations/init.sql` with the new dimension and re-ingest all documents.

---

## Production notes

- Replace `allow_origins=["*"]` in `main.py` with your actual frontend origin.
- Use a process manager (e.g., `gunicorn` with `UvicornWorker`) for multi-worker deployments.
- For high-throughput knowledge enrichment, replace `BackgroundTasks` with Celery + Redis broker.
- Tune the IVFFlat `lists` parameter in `init.sql` based on your chunk count: ~`sqrt(total_rows)`.
