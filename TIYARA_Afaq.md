# TIYARA — Afaq (آفاق)

> *Where the platform stands today, and where it is going*

---

## 1. Executive Summary

Tiyara is an AI-native MRO (Maintenance, Repair & Overhaul) copilot built specifically for commercial aviation. It bridges the gap between raw maintenance data, technical documentation (AMM), institutional knowledge stored in resolved case histories, and the engineer or technician standing in front of a faulty engine. By combining Retrieval-Augmented Generation, semantic vector search, real-time AI streaming, and automated bilingual document generation, Tiyara compresses hours of manual cross-referencing into a structured, auditable conversation — and ends every session with a complete set of shop-ready PDF documents.

---

## 2. The Problem Tiyara Solves

Aircraft maintenance today is document-heavy, time-critical, and dangerously reliant on tribal knowledge. A licensed technician diagnosing a CFM56 fault must simultaneously:

- Cross-reference hundreds of AMM pages across ATA chapters
- Recall similar cases from memory or informal note-sharing
- Interpret and normalise maintenance logs that rarely follow a standard format
- Produce formal shop documentation (finding input, work order, KCC letters) by hand

When knowledge walks out the door with a retiring engineer, or when an airline operates across multiple languages, diagnostic quality drops and risk rises. Tiyara addresses this directly.

---

## 3. Core Technology Stack

### 3.1 AI Backbone — Streaming Large Language Model

- **Model:** GPT-4o (via OpenAI-compatible API endpoint) with a deterministic, role-constrained system prompt
- **Streaming output:** Server-Sent Events (SSE) deliver token-by-token responses so technicians see the diagnosis build in real time — no loading spinners, no waiting for a full response
- **Structured output enforcement:** The system prompt mandates a fixed markdown schema (`## Diagnosis`, `## Risk Level`, `## Procedure`, `## Parts & Tooling`, `## Follow-up`, `## Sources`) on every response, making downstream parsing reliable
- **Inline citation discipline:** Every claim is annotated with `[AMM XX-XX-XX]`, `[Case #N]`, or `[History]` — making the AI's reasoning traceable and auditable

### 3.2 Retrieval-Augmented Generation (RAG)

Tiyara implements a two-track RAG pipeline that fires before every AI response:

**Track A — AMM Semantic Search**
- AMM PDFs are ingested page-by-page using `pdfplumber`
- Each page's ATA chapter is auto-detected via regex (`ATA 72`, `CHAPTER 72-30`, etc.)
- Text is split into 500-token overlapping chunks using `RecursiveCharacterTextSplitter`
- Each chunk is embedded with `BAAI/bge-base-en-v1.5` (768-dimensional dense vectors, L2-normalised)
- At query time, the user's message is embedded with the same model and cosine-similarity ranked against all chunks filtered by engine type
- Top-8 chunks are injected into the system prompt with full ATA + page provenance

**Track B — Resolved Case History Search**
- Past resolved sessions are stored as structured JSON summaries (fault, root cause, steps applied, outcome)
- Each case is embedded and retrieved exactly like AMM chunks
- Top-3 similar historical cases are surfaced to the model so it can reason from institutional precedent, not just documentation

This dual-track approach means the AI's answer is always grounded in **the actual manual for this specific engine** and **what worked before on the same kind of fault** — not generic aviation knowledge alone.

### 3.3 AI-Powered Excel Normalisation

Maintenance log files in the industry come in dozens of ad-hoc formats. Tiyara's `ExcelParser` pipeline eliminates manual column mapping:

1. **Sheet identification** — when a workbook has multiple sheets, the AI reads a 4-row preview of each and identifies the maintenance log sheet by semantic understanding
2. **Column mapping** — arbitrary column headers (`"Date of Fault"`, `"Dt_Panne"`, `"EVENT_DATE"`) are mapped to a canonical schema (`fault_date`, `ata_chapter`, `fault_code`, etc.) by the AI
3. **Pattern analysis** — a second AI pass analyses up to 50 normalised records and returns a structured JSON summary: top recurring faults, flagged components, unresolved patterns, average recurrence interval, and a one-sentence risk summary

This pattern summary is injected into the system prompt, giving the AI a statistical picture of the engine's history before the first question is even asked.

### 3.4 Automated Bilingual Document Generation

Every session culminates in six PDF documents, generated on demand via ReportLab:

| Document | Reference Format | Purpose |
|---|---|---|
| Full Diagnostic Report | `RPT-XXXXXXXX` | Complete session record with AI transcript and procedure steps |
| Finding Input Form | `FI-XXXXXXXX` | Structured fault intake form |
| AI Analysis Sheet | `AA-XXXXXXXX` | ESM search result, historical cases, AI decision flow |
| Capability Analysis | `CA-XXXXXXXX` | Methods department assessment (replace / external / scrap / KCC) |
| Service Order | `OS-XXXXXXXX` | Step-by-step work order extracted from AI procedure |
| KCC Draft | `KCC-XXXXXXXX` | Keepership Concern Communication to manufacturer |

All six documents are fully bilingual (English / French). The language is passed as a `?lang=en|fr` query parameter to each endpoint, and all labels, section headers, and static text are served from a centralised translation registry. This means the same session data renders into a complete French-language documentation package or an English one — with zero manual re-work.

### 3.5 Role-Aware Access Control

The platform enforces a three-tier user model:

- **Technician** — creates sessions, runs diagnoses, downloads documents
- **Engineer** — full technician access plus document generation and session oversight
- **Supervisor** — full access including AMM document ingestion (upload privileges)

JWT-based authentication with access token + refresh token rotation ensures sessions are secure and stateless.

### 3.6 Frontend Architecture

- **React 18 + TypeScript + Vite** — typed, fast, zero-config build
- **Tailwind CSS with custom aerospace design tokens** — a dark, precision-instrument aesthetic appropriate for a technical tool used in hangars and workshops
- **Framer Motion** — fluid but purposeful animations (message streaming, step guide reveals, file upload feedback)
- **Global i18n via React Context** — language preference stored in `localStorage`, propagated through `LanguageContext` to every page and component; toggled from the sidebar and landing page navbar
- **Lucide React icons** — consistent, lightweight icon set

---

## 4. What Makes Tiyara Technically Differentiated

| Capability | Traditional MRO Software | Tiyara |
|---|---|---|
| AMM lookup | Manual search, PDF reader | Semantic vector retrieval, auto-cited in response |
| Historical cases | Email threads, spreadsheets, memory | Embedded, ranked, injected into AI context |
| Excel log analysis | Manual review | AI column mapping + pattern analysis in seconds |
| Diagnosis quality | Engineer-dependent | GPT-4o grounded in AMM + case history |
| Documentation | Manual forms, hours of work | Auto-generated PDFs at session close, bilingual |
| Language support | Single language | Full EN/FR UI + documents, extensible to any language |
| Knowledge retention | Leaves with the engineer | Persisted in case history, searchable forever |

---

## 5. Future Vision

### 5.1 Multi-Lingual Expansion

The translation architecture is designed for extension. Adding Arabic, Spanish, or Portuguese is a matter of adding a key-value map in `i18n.ts` and `translations.py`. Given that Tiyara's target market spans North Africa, the Middle East, Francophone Africa, and Latin America, full multilingual support is a near-term priority with a low engineering cost.

### 5.2 Predictive Maintenance Module

The pattern data already collected per session (top faults, recurring components, unresolved patterns, recurrence intervals) is the raw material for a predictive layer. A future module could:

- Aggregate pattern summaries across all sessions for a given engine type
- Identify fleet-wide fault trends before they become AOG events
- Push proactive alerts when a pattern crosses a risk threshold (e.g., "EGT exceedance recurred 3 times in 90 days — recommend borescope inspection before next flight")

This transforms Tiyara from reactive (diagnose after the fault) to proactive (prevent the next one).

### 5.3 Vector Database Migration for Scale

The current RAG engine uses SQLite with in-memory cosine similarity (NumPy). This is appropriate for single-operator or small-fleet deployments. As the document corpus and case history grow into millions of chunks, migrating to a dedicated vector database (pgvector on PostgreSQL, Pinecone, or Qdrant) would allow:

- Sub-millisecond approximate nearest-neighbor search at billion-vector scale
- Multi-tenant isolation between airlines sharing the same infrastructure
- Hybrid search combining semantic similarity with metadata filters (engine serial number, registration, date range)

The retrieval interface (`retrieve_amm_chunks`, `retrieve_case_history`) is already abstracted behind async functions — the migration would be a drop-in replacement with no changes to the AI layer.

### 5.4 Mobile Companion Application

Technicians work on the aircraft floor, not at a desk. A React Native companion app would allow:

- Voice-to-text fault description (particularly valuable with gloved hands)
- Camera integration for borescope image capture, attached directly to the session
- Offline AMM chunk cache for hangars with poor connectivity
- Push notifications when a supervisor approves a service order

The session API is already structured as REST + SSE — both are compatible with mobile clients without backend changes.

### 5.5 Digital Logbook & Airworthiness Integration

MRO documentation today still involves paper signatures and manual CAMP/TRAX entry. Tiyara could become the source of truth for digital airworthiness records:

- Session completion triggers an API push to CAMP, AMOS, or TRAX via integration adapters
- Digital signatures (EASA Part-145 / FAA 14 CFR Part 43 compliant) attached to the Service Order PDF
- Automatic deferred defect (DD) card generation from unresolved session findings
- ETOPS and MEL cross-checks flagged automatically based on ATA chapter and fault severity

### 5.6 Manufacturer Loop — KCC Intelligence

The KCC Draft document already generates a structured letter to the manufacturer. A future integration could:

- Parse manufacturer Service Bulletins (SBs) and Airworthiness Directives (ADs) as they are published and add them to the RAG corpus automatically
- Cross-reference open KCCs against new SBs and notify engineers when a manufacturer response has been received
- Build an anonymised, airline-agnostic fleet intelligence database that allows operators to see how common a given fault is across the industry

### 5.7 Fine-Tuned Aviation LLM

GPT-4o is a general-purpose model instructed to behave as an aviation expert. A longer-term differentiator would be fine-tuning a smaller open-source model (Mistral 7B, LLaMA 3) on:

- Thousands of resolved Tiyara sessions
- ATA-chapter-annotated AMM text
- Airbus and Boeing maintenance training materials (where licensing allows)

A fine-tuned model would be deployable on-premises (critical for airlines with strict data sovereignty requirements), faster, cheaper per token, and more reliably structured in its output.

### 5.8 Training and Certification Module

Tiyara's case library is inherently a training dataset. A future learning module could:

- Present trainee technicians with real anonymised fault scenarios and assess their diagnosis against the AI's recommendation
- Track competency per ATA chapter and flag knowledge gaps to the supervisor
- Generate training certificates automatically upon scenario completion
- Integrate with EASA Part-147 approved training organisation workflows

---

## 6. Market Opportunity

The global MRO market is valued at approximately **$100 billion** and is growing at 4–5% annually, driven by fleet expansion in Asia-Pacific and the Middle East. Within this market:

- **Line maintenance** (where Tiyara's real-time diagnosis is most impactful) represents ~$25B
- **Engine MRO** (Tiyara's current specialisation) represents ~$40B
- The shift from scheduled to **condition-based maintenance** is creating urgent demand for AI-assisted diagnostic tools

Tiyara's beachhead in engine fault diagnosis — the most technically complex and highest-value MRO segment — positions it to expand horizontally into airframe, avionics, and cabin systems using the same architecture.

---

## 7. Conclusion

Tiyara is not a chatbot with an aviation system prompt. It is a full-stack MRO intelligence platform that integrates:

- A RAG engine purpose-built for technical documentation retrieval
- An AI normalisation layer that eliminates the data-prep barrier for maintenance logs
- A structured diagnostic conversation model enforcing citation and auditability
- An automated documentation factory producing six formally-structured, bilingual PDFs per session
- A role-aware, secure multi-user platform with a professional aerospace-grade UI

The architecture is deliberately modular. Every major component — the vector store, the LLM provider, the PDF generators, the storage backend, the translation system — is behind an interface that can be upgraded independently as the product scales. The foundation is solid. The roadmap is clear. The market is ready.

---

*Document version: 1.0 — April 2026*
*Project: Tiyara — Smarter Skies*
*Repository: github.com/zaykats/tiyara*
