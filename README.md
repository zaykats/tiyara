# Tiyara AI — Aviation Maintenance Assistant

Tiyara is a full-stack AI-powered maintenance assistant for certified aircraft technicians. It combines a FastAPI backend, a React frontend, RAG-based knowledge retrieval, and GPT-4o to deliver structured fault diagnoses with full traceability — and generates professional PDF maintenance reports at the end of every session.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), SQLite (aiosqlite) |
| AI Model | **GPT-4o** (or any OpenAI-compatible provider) |
| Embeddings | `BAAI/bge-base-en-v1.5` (sentence-transformers, 768-dim) |
| Frontend | React + Vite + TypeScript + Tailwind CSS + shadcn/ui |
| Auth | JWT (access + refresh tokens) + Redis token revocation |
| PDF Reports | ReportLab — professional MRO-style maintenance reports |
| File Storage | Local / S3 / Supabase (configurable) |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Redis | 7+ (optional — used only for token refresh revocation) |

---

## Quick Start

### 1. Clone & install backend

```bash
git clone https://github.com/zaykats/tiyara.git
cd tiyara

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> `sentence-transformers` downloads `BAAI/bge-base-en-v1.5` (~440 MB) on first run. Cached locally after that.

### 2. Configure environment

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./tiyara.db

# JWT
SECRET_KEY=change-me-to-a-long-random-string

# AI provider (OpenAI or any OpenAI-compatible endpoint)
API_KEY=your-api-key-here
API_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o

# Storage
STORAGE_BACKEND=local

# Redis (optional)
REDIS_URL=redis://localhost:6379
```

> The AI client uses the OpenAI SDK with a configurable `base_url`, so any OpenAI-compatible provider works (OpenAI, Azure, custom proxy, etc.).

### 3. Run the backend

```bash
# Windows (PowerShell)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# macOS / Linux
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://localhost:8000/docs

> **Corporate networks:** If HuggingFace is blocked by SSL, the app automatically loads the embedding model from local cache (`TRANSFORMERS_OFFLINE=1` is set in code).

### 4. Run the frontend

```bash
cd frontend/tiyara-smarter-skies
npm install
npm run dev
```

Frontend: http://localhost:8080

---

## Information Flow & Pipeline

```
User (Browser)
     │
     │  1. Sign up / Sign in
     ▼
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│  Pages: Dashboard · Sessions · Chat · Upload AMM     │
│  Auth: JWT stored in localStorage                    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / SSE
                     ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                     │
│  POST /auth/signup|signin                           │
│  GET|POST|PATCH /sessions                           │
│  POST /sessions/{id}/upload-excel                   │
│  GET  /sessions/{id}/report          ◄── NEW        │
│  POST /documents/ingest                             │
│  POST /chat  ──────────────────────────────────►   │
└──────────┬──────────────────────────────────────────┘
           │
           │  2. New Diagnosis Flow
           ▼
┌─────────────────────────────┐
│  Create Session             │  engine_type + problem_description
│  (optional) Upload Excel    │  → parsed + pattern-analyzed by AI
│  Navigate to Chat           │
└──────────┬──────────────────┘
           │
           │  3. Chat Request (POST /chat)
           ▼
┌─────────────────────────────────────────────────────┐
│  RAG Retrieval (app/rag/retrieval.py)               │
│                                                     │
│  User message → embed (BAAI/bge-base-en-v1.5)       │
│       ├─► Top-8 AMM chunks  (cosine similarity,     │
│       │       filtered by engine_type)              │
│       └─► Top-3 Case History matches                │
│               (resolved sessions, same engine)      │
└──────────┬──────────────────────────────────────────┘
           │
           │  4. System Prompt Assembly (app/chat/agent.py)
           ▼
┌─────────────────────────────────────────────────────┐
│  build_system_prompt()                              │
│                                                     │
│  Base instructions (structured markdown format)     │
│  + Session context (engine type, reported fault)    │
│  + Excel pattern summary (if uploaded)              │
│  + Relevant AMM sections (RAG)                      │
│  + Similar resolved cases (RAG)                     │
└──────────┬──────────────────────────────────────────┘
           │
           │  5. AI Inference
           ▼
┌─────────────────────────────────────────────────────┐
│  GPT-4o (streaming SSE → frontend)                  │
│                                                     │
│  Response format (enforced by system prompt):       │
│  ## Diagnosis                                       │
│  ## Risk Level                                      │
│  ## History Patterns                                │
│  ## Procedure                                       │
│  ## Parts & Tooling                                 │
│  ## Follow-up                                       │
│  ## Sources                                         │
│  SUGGESTIONS: q1 | q2 | q3  ◄── parsed as chips    │
└──────────┬──────────────────────────────────────────┘
           │
           │  6. Knowledge Enrichment (on resolve)
           ▼
┌─────────────────────────────────────────────────────┐
│  PATCH /sessions/{id}  { status: "resolved" }       │
│                                                     │
│  Background task:                                   │
│  → AI reads full conversation history               │
│  → Generates structured JSON summary                │
│     (fault, root_cause, steps_applied, outcome)     │
│  → Summary embedded + stored in case_history table  │
│  → Available to future RAG queries for same engine  │
└──────────┬──────────────────────────────────────────┘
           │
           │  7. PDF Report (GET /sessions/{id}/report)
           ▼
┌─────────────────────────────────────────────────────┐
│  generate_session_report()  (app/reports/)          │
│                                                     │
│  Professional MRO-style PDF containing:             │
│  01 Work Order Information                          │
│  02 Fault Reported                                  │
│  03 Personnel On Record                             │
│  04 Maintenance History Patterns (if Excel)         │
│  05 AI Resolution Summary (if resolved)             │
│  06 Diagnostic Conversation Transcript              │
│     Sign-Off & Certification section                │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
tiyara/
├── app/
│   ├── main.py              # FastAPI app + lifespan (DB init)
│   ├── config.py            # Settings: API_KEY, MODEL, API_BASE_URL
│   ├── database.py          # Async SQLAlchemy engine & session
│   ├── dependencies.py      # get_current_user, get_db, get_redis
│   ├── embeddings.py        # sentence-transformers singleton (offline-safe)
│   │
│   ├── auth/                # JWT auth
│   │   ├── models.py        # User model (id, email, role, company)
│   │   ├── utils.py         # bcrypt + JWT helpers
│   │   ├── service.py
│   │   └── router.py        # POST /auth/signup|signin|refresh
│   │
│   ├── sessions/            # Maintenance sessions
│   │   ├── models.py        # Session, Message
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── router.py        # CRUD + Excel upload + role enforcement
│   │
│   ├── chat/                # Streaming AI agent
│   │   ├── agent.py         # build_system_prompt() — RAG context injector
│   │   ├── service.py       # SSE streaming + case enrichment
│   │   └── router.py        # POST /chat
│   │
│   ├── reports/             # PDF report generation  ◄── NEW
│   │   ├── generator.py     # ReportLab MRO-style PDF builder
│   │   └── router.py        # GET /sessions/{id}/report
│   │
│   ├── documents/           # AMM document management
│   │   ├── models.py        # Document, DocumentChunk, CaseHistory
│   │   ├── service.py
│   │   └── router.py        # POST /documents/ingest (engineer+)
│   │
│   ├── ingestion/           # File parsing
│   │   ├── excel_parser.py  # AI-powered Excel normalizer + pattern analyzer
│   │   ├── pdf_ingestion.py # ATA-aware PDF chunker + embedder
│   │   └── service.py       # upload_file_to_storage
│   │
│   └── rag/
│       └── retrieval.py     # Cosine similarity search (numpy, no pgvector)
│
├── frontend/
│   └── tiyara-smarter-skies/
│       └── src/
│           ├── pages/
│           │   ├── LandingPage.tsx
│           │   ├── SignInPage.tsx
│           │   ├── SignUpPage.tsx
│           │   ├── DashboardPage.tsx       # Stats + recent sessions
│           │   ├── NewDiagnosisPage.tsx    # Create session + Excel upload
│           │   ├── ChatPage.tsx            # Streaming chat + Download Report button
│           │   └── UploadAMMPage.tsx       # AMM PDF ingestion (engineer+)
│           ├── components/
│           │   ├── AppSidebar.tsx
│           │   └── DashboardLayout.tsx
│           └── contexts/
│               └── AuthContext.tsx
│
├── .env
├── requirements.txt
└── README.md
```

---

## API Reference

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/signin` | Get access + refresh tokens |
| POST | `/auth/refresh` | Rotate tokens |

### Sessions

| Method | Path | Description |
|---|---|---|
| POST | `/sessions` | Create a new maintenance session |
| GET | `/sessions` | List sessions (supervisors see all) |
| GET | `/sessions/{id}` | Get session + full message history |
| PATCH | `/sessions/{id}` | Update status (resolve requires engineer+) |
| POST | `/sessions/{id}/upload-excel` | Parse & attach Excel maintenance log |
| GET | `/sessions/{id}/report` | Download PDF maintenance report |

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/chat` | Stream AI diagnosis response (SSE) |

SSE event format:
```
data: {"type": "content", "text": "<token>"}
data: {"type": "done"}
```

### Documents

| Method | Path | Description |
|---|---|---|
| POST | `/documents/ingest` | Upload & ingest AMM PDF (engineer+) |
| GET | `/documents` | List ingested documents |

---

## PDF Maintenance Report

Every session can generate a professional PDF report — available via the **Download Report** button in the chat sidebar, or directly at `GET /sessions/{id}/report`.

The report follows standard MRO shop format and includes:

| Section | Content |
|---|---|
| Work Order Information | Report number, session ID, engine type, dates, status |
| Fault Reported | Original problem description |
| Personnel On Record | Technician name, role, company, email |
| Maintenance History Patterns | Top faults, recurring components, risk summary (if Excel uploaded) |
| AI Resolution Summary | Fault description, root cause, steps applied, outcome, ATA chapter (if resolved) |
| Diagnostic Conversation Transcript | Full chat log with timestamped TECHNICIAN / TIYARA AI entries |
| Sign-Off & Certification | Signature lines for Technician, Engineer/Supervisor, and QA |

---

## Roles & Permissions

| Role | Can Do |
|---|---|
| `technician` | Create sessions · Chat · Upload Excel · Download report |
| `engineer` | + Ingest AMM PDFs · Mark sessions resolved |
| `supervisor` | + View all users' sessions · Access/resolve any session |

---

## Excel Parsing Pipeline

1. Accept `.xlsx` / `.xls` upload
2. Sample 10 rows → AI maps columns to standard fields (date, ATA, fault, action, technician, etc.)
3. Normalize full dataset using the mapping
4. AI analyzes top 50 records → returns pattern summary (top faults, recurring components, risk level)
5. `excel_normalized_data` + `excel_pattern_summary` stored on session, injected into every chat prompt and PDF report

---

## AMM Ingestion Pipeline

1. Upload PDF via `POST /documents/ingest`
2. Extract text page-by-page with `pdfplumber`
3. Detect ATA chapter headings via regex
4. Split into 500-token overlapping chunks per chapter
5. Batch-embed all chunks with `BAAI/bge-base-en-v1.5`
6. Store in `document_chunks` table with engine_type tag
7. Available immediately for RAG retrieval in chat

---

## RAG Retrieval

On every `/chat` request:

1. Embed the user's message
2. Compute cosine similarity against all `document_chunks` (filtered by `engine_type`)
3. Return top-8 AMM chunks
4. Compute cosine similarity against `case_history` (filtered by `engine_type`)
5. Return top-3 resolved cases
6. Both injected into the system prompt before the AI responds

---

## Knowledge Enrichment (Self-Learning)

When a session is marked `resolved`:

1. Background task reads the full conversation history
2. AI generates a structured JSON summary: `{ fault_description, root_cause, steps_applied, outcome }`
3. Summary is embedded and stored in `case_history`
4. Future sessions with the same engine type will retrieve this case via RAG
5. The system gets smarter with every resolved session

---

## Response Format

Every AI response follows this exact structure (enforced by system prompt):

```
## Diagnosis
Root cause with source references [AMM XX-XX-XX] or [Case #N]

## Risk Level
🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low — one-line reason

## History Patterns
- Bullet points flagging recurrences

## Procedure
1. **Step title** — instruction [AMM ref]

## Parts & Tooling
- Parts (with P/N if known)
- Tooling required

## Follow-up
- Required next actions

## Sources
| Reference | Page | Notes |

SUGGESTIONS: question 1 | question 2 | question 3
```

The `SUGGESTIONS` line is parsed by the frontend and rendered as clickable chips above the input bar.

---

## Production Notes

- Replace `allow_origins=["*"]` in `main.py` with your actual frontend origin
- Use `gunicorn` with `UvicornWorker` for multi-worker deployments
- For high-volume enrichment, replace `BackgroundTasks` with Celery + Redis broker
- Redis is required for token refresh revocation in production; without it, sign-in still works
- The embedding model is loaded from local cache by default (`TRANSFORMERS_OFFLINE=1`) — run once with internet access to download it
