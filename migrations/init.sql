-- ============================================================
-- Tiyara – SQLite schema
-- Run with:  sqlite3 tiyara.db < migrations/init.sql
--
-- NOTE: SQLAlchemy's create_all_tables() (called on startup) will
-- create these tables automatically.  This file is provided as a
-- reference / manual bootstrap option.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── users ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,          -- UUID stored as text
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('technician', 'engineer', 'supervisor')),
    company         TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ── sessions ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id                      TEXT PRIMARY KEY,
    user_id                 TEXT     NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    engine_type             TEXT     NOT NULL,
    problem_description     TEXT     NOT NULL,
    excel_pattern_summary   TEXT,              -- JSON
    excel_normalized_data   TEXT,              -- JSON
    status                  TEXT     NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'resolved', 'closed')),
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status   ON sessions (status);

-- Auto-update updated_at
CREATE TRIGGER IF NOT EXISTS sessions_updated_at
AFTER UPDATE ON sessions
BEGIN
    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ── messages ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id                 TEXT PRIMARY KEY,
    session_id         TEXT     NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    role               TEXT     NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content            TEXT     NOT NULL,
    structured_content TEXT,                   -- JSON
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);

-- ── documents ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id               TEXT PRIMARY KEY,
    filename         TEXT NOT NULL,
    engine_type_tag  TEXT NOT NULL,
    storage_path     TEXT NOT NULL,
    uploaded_by      TEXT NOT NULL REFERENCES users (id),
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_engine_type ON documents (engine_type_tag);

-- ── document_chunks ───────────────────────────────────────────────────────────
-- Embeddings stored as JSON float arrays in TEXT columns.
-- Similarity search is performed in Python (numpy cosine distance).
CREATE TABLE IF NOT EXISTS document_chunks (
    id               TEXT PRIMARY KEY,
    document_id      TEXT     NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    engine_type_tag  TEXT     NOT NULL,
    ata_chapter      TEXT,
    chunk_text       TEXT     NOT NULL,
    embedding        TEXT,                     -- JSON float array
    page_number      INTEGER,
    source_filename  TEXT     NOT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_engine_type ON document_chunks (engine_type_tag);
CREATE INDEX IF NOT EXISTS idx_chunks_ata_chapter ON document_chunks (ata_chapter);

-- ── case_history ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS case_history (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT REFERENCES sessions (id) ON DELETE SET NULL,
    engine_type         TEXT NOT NULL,
    ata_chapter         TEXT,
    resolution_summary  TEXT NOT NULL,
    embedding           TEXT,                  -- JSON float array
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_case_engine_type ON case_history (engine_type);
CREATE INDEX IF NOT EXISTS idx_case_ata_chapter ON case_history (ata_chapter);
