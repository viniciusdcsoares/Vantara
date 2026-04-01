# IMPLEMENTATION STATUS

> **Last updated:** 2026-04-01  
> **Authority level:** Group A — Authoritative Now  
> **Purpose:** This is the **single most important document** for any coding agent operating in this repository. It maps the real, living codebase against the aspirational architecture, provides strict operational instructions, and defines what exists today.  
> **For historical divergence details:** See [DIVERGENCE_LOG.md](./DIVERGENCE_LOG.md).

---

## 1. Current Implementation Profile

### 1.1 System Identity

| Property | Value |
|---|---|
| **Profile** | Experimental MVP — standalone Python scripts + Streamlit UI |
| **Runtime** | Local execution, no server infrastructure, no containers |
| **Language** | Python 3.12 |
| **LLM Provider** | Google Gemini (`gemini-2.5-flash`) via `google-genai` SDK |
| **UI Framework** | Streamlit (parameter configuration + output visualization) |
| **Database** | None — all data persisted as flat JSON files in `outputs/` |
| **Queue System** | None — all processing is synchronous and sequential |
| **Deployment** | Local-only; secrets managed via `st.secrets` (Streamlit TOML) |

### 1.2 Repository Structure (Actual)

```
/Vantara (root)
  ├── run_scraping.py                # New Scraping orchestrator (YouTube + Bluesky + NewsAPI)
  ├── run_llm_analysis.py            # New LLM analysis & embedding orchestrator (per-item + clustering)
  ├── audit_nearest_neighbors.py     # Embedding quality auditor (cosine similarity)
  ├── prepare_manual_review.py       # Human review prep (CSV for manual labeling)
  ├── requirements.txt               # Updated dependencies (added fasttext, lingua, etc.)
  ├── README.md                      # Project description, tech stack, quick start
  │
  ├── /scraping                      # Source connectors
  │     ├── youtube.py               # Anti-bot + Cookie auth + Hard Vote lang filter
  │     ├── bluesky.py               # AT Protocol client (search + thread extraction)
  │     └── news.py                  # NewsAPI.org client (source-diversity filter)
  │
  ├── /llm_configs                   # LLM infrastructure
  │     ├── functions.py             # generate_gemini_json() — core LLM call wrapper
  │     ├── /prompts
  │     │     └── narrative_detection.py   # System instructions + prompt templates (per-item)
  │     └── /schemas
  │           └── narrative_detection.py   # Pydantic per-item schemas (YoutubeAnalysis, etc.)
  │
  ├── /outputs
  │     ├── /scraping                # Raw JSON clippings from run_scraping.py
  │     ├── /analysis                # Per-item LLM analysis and items-for-embedding results
  │     └── /embeddings              # Parquet/JSON embeddings and clustering metadata
  │
  └── /docs                          # Documentation hub
        ├── README.md                # Documentation governance and taxonomy
        ├── /architecture            # Group B — Target Architecture
        ├── /product                 # Group C — Product & Domain Context
        ├── /implementation          # Group A — Active conventions
        ├── /adr                     # Group A — Architecture Decision Records
        └── /reconciliation
              ├── IMPLEMENTATION_STATUS.md   ← You are here
              ├── DIVERGENCE_LOG.md          ← Historical divergence appendix
              └── SPRINT_PLAN.md             ← Lean MVP sprint schedule
```

### 1.3 Current Data Flow

The implemented pipeline is a **three-phase synchronous and semi-automated sequence**:

```
Phase 1: Collection (run_scraping.py)
┌─────────────────────────────────────────────────────────────────────────┐
│  Topic String (user input)                                              │
│       │                                                                 │
│       ├──→ YouTube Connector ──→ search + metadata + transcript         │
│       │         uses: YouTube Data API v3, youtube-transcript-api       │
│       │         feat: Anti-bot jitter (3–7s), Cookie auth support       │
│       │         filter: Hard Vote language detection (3 models)         │
│       │                                                                 │
│       ├──→ Bluesky Connector ──→ search + thread replies                │
│       │         uses: AT Protocol (atproto)                             │
│       │                                                                 │
│       └──→ NewsAPI Connector ──→ article search                         │
│                 uses: NewsAPI.org (source diversity filter)             │
│                                                                         │
│  Output: outputs/scraping/{topic}_{timestamp}.json                      │
└─────────────────────────────────────────────────────────────────────────┘

Phase 2: Per-Item Analysis & Embedding (run_llm_analysis.py)
┌─────────────────────────────────────────────────────────────────────────┐
│  Latest JSON from outputs/scraping/                                     │
│       │                                                                 │
│       ├──→ Per-Item Analysis (LLM)                                      │
│       │     → Each video/post/article analyzed individually             │
│       │     → Extraction of `canonical_claim`, `claim_type`, etc.       │
│       │                                                                 │
│       ├──→ Embedding Generation                                         │
│       │     → Model: `gemini-embedding-001`                             │
│       │     → Input: `argument_claim_canonical` (or fallback)           │
│       │                                                                 │
│       └──→ Clustering & Visualization                                   │
│             → K-Means (k=3) + t-SNE (2D)                                │
│             → Semantic anchors (Pro/Con/Neutral) injected               │
│                                                                         │
│  Output: outputs/analysis/narrative_detection_{run_id}.json             │
│          outputs/embeddings/embeddings_{run_id}.parquet                 │
└─────────────────────────────────────────────────────────────────────────┘

Phase 3: Audit & Review (audit_nearest_neighbors.py, prepare_manual_review.py)
┌─────────────────────────────────────────────────────────────────────────┐
│  Embeddings and Item Artifacts                                          │
│       │                                                                 │
│       ├──→ Nearest Neighbors Audit                                      │
│       │     → Cosine similarity check for embedding quality             │
│       │                                                                 │
│       └──→ Manual Review Prep                                           │
│             → CSV generation for human labeling                         │
│             → Priority flagging for cross-source/high-similarity cases  │
│                                                                         │
│  Output: outputs/embeddings/nearest_neighbors_{run_id}.json             │
│          outputs/embeddings/manual_review_priority_{run_id}.csv         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 LLM Integration Details

| Component | Implementation |
|---|---|
| **Client** | `google.genai.Client` initialized with `GEMINI_API_KEY` from `st.secrets` |
| **Model** | `gemini-2.5-flash` (configured in `generate_gemini_json()` default param) |
| **Output mode** | `response_mime_type="application/json"` with `response_schema=<PydanticModel>` |
| **Validation** | Response parsed via `PydanticModel.model_validate_json(response.text)` |
| **Observability** | `@measure_time` decorator captures duration; token counts extracted from `usage_metadata` (input, reasoning, output, total) |
| **Prompt strategy** | Per-source system instructions + dynamically formatted user prompts (full JSON payload injected) |

### 1.5 Pydantic Output Schemas (Implemented)

**Shared types:**
- `GrowthStatus` (Enum): `growing`, `stable`, `declining`, `unclear`
- `KeyActor`: `handle`, `role`, `stance`

**Per-source analysis models:**

| Model | Fields |
|---|---|
| `YoutubeAnalysis` | `core_narrative`, `dominant_framing`, `key_actors[]`, `audience_reception`, `engagement_analysis`, `growth_status`, `notable_quotes[]` |
| `BlueskyAnalysis` | `core_narrative`, `dominant_framing`, `key_actors[]`, `engagement_analysis`, `growth_status`, `notable_quotes[]` |
| `NewsAnalysis` | `core_narrative`, `journalistic_framing`, `overall_tone` (ArticleTone enum), `key_entities[]` (NewsEntity), `inferred_impact`, `media_sources_analysis`, `notable_quotes[]` |

### 1.6 Key Technical Details per Connector

**YouTube (`scraping/youtube.py`):**
- Uses YouTube Data API v3 (`googleapiclient`) for search and video metadata
- Extracts full Portuguese transcripts via `youtube-transcript-api`
- **Hard Vote language filter**: 3 independent detectors (`langdetect`, `lingua`, `fasttext`)
- **Anti-bot measures**: randomized jitter (3–7s) between processing steps
- **Authentication**: supports local cookie auth via `youtube_cookies.txt` (to bypass transcript availability blocks)
- Captures: title, channel, link, stats (views, likes, comments), duration, hidden tags, full description, transcript, and most-liked comments

**Bluesky (`scraping/bluesky.py`):**
- Uses AT Protocol client (`atproto`) with login authentication
- Searches with `lang:pt since:{date}` filter, sorted by `top`
- Enters each post's thread to extract reply comments
- Extracts external links (e.g., shared news articles) from embed metadata
- Captures: text, author handle, publication date, link, cited external URL, likes, reposts, total replies, most-liked comments

**NewsAPI (`scraping/news.py`):**
- REST client hitting `newsapi.org/v2/everything`
- **Source diversity filter**: max 1 article per news outlet (prevents portal monopoly)
- Sorted by `publishedAt`, filtered by `language=pt`
- Captures: title, author, source name, description, publication date, URL, content snippet

---

## 2. Active Architecture Decisions (ADRs)

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](../adr/ADR-001-per-item-analysis-foundation.md) | Per-item granular analysis as pipeline foundation. Each content item analyzed individually producing `canonical_claim` + `claim_type`. | **Accepted** |
| [ADR-002](../adr/ADR-002-canonical-claim-over-framing.md) | `canonical_claim` as the sole embedding input. Framing deprecated from the clustering dimension — used for display only. | **Accepted** |
| [ADR-003](../adr/ADR-003-streamlit-mvp-runtime.md) | Streamlit + flat Python scripts as MVP runtime. No FastAPI/PostgreSQL/Redis until pipeline intelligence logic is validated with real data. | **Accepted** |
| [ADR-004](../adr/ADR-004-youtube-anti-bot-measures.md) | YouTube anti-bot measures: randomized jitter (3-7s), batch processing, and local cookie authentication via `youtube_cookies.txt`. | **Accepted** |

---

## 3. Key Convergence Decisions

These decisions document the **intentional divergences** between the target architecture and the current code. They are the reconciliation layer — explaining what the docs say, what the code does, why they differ, and what happens next.

### 3.1 Intelligence Pipeline

| Dimension | Target Architecture (Group B) | Current Code (MVP) |
|---|---|---|
| **Pipeline** | 9 stages, async, queue-driven | 2 stages, synchronous, file-driven |
| **Granularity** | Per-argument with embeddings | Per-source cluster with holistic LLM analysis |
| **Persistence** | PostgreSQL with pgvector | Flat JSON files |
| **LLM usage** | Targeted: argument extraction + narrative summarization | Broad: full analytical reasoning per source cluster |

**Next convergence step:** Implement per-item analysis (ADR-001) → embeddings → clustering. See [SPRINT_PLAN.md](./SPRINT_PLAN.md) for the schedule.

### 3.2 Data Models & Embedding Strategy

- **`canonical_claim`** is the selected embedding input (ADR-002).
- **Framing** is deprecated from the clustering dimension — it may be extracted for display but will not be embedded.
- **`claim_type`** classification (`factual` / `argumentative`) must be implemented in schemas before generating embeddings.

### 3.3 Infrastructure & Runtime

Full infrastructure divergence is intentional (ADR-003). Infrastructure convergence begins **only** after the intelligence pipeline is validated with real data. Trigger conditions:
- Per-item analysis produces meaningful `canonical_claim` values
- Embedding + clustering produces meaningful cross-source narrative groups
- The team needs multi-user access or scheduled execution

### 3.4 Prompt Architecture

The Pydantic + structured output approach in the current code is **superior** to the markdown-based prompt templates in the target architecture. Future prompts should follow the current pattern: Python function for prompt construction + Pydantic model for output schema + `generate_gemini_json()` as the execution wrapper.

---

## 4. Safe Instructions for Coding Agents

These rules are **mandatory and non-negotiable** for any LLM or AI agent operating in this repository.

### 4.1 Do NOT globally align the repository to Group B documents

The target architecture describes 15+ database tables, 8 job queues, 7 prompt types, FastAPI backend, Next.js frontend, and Docker infrastructure. **None of this exists.** Do not scaffold, generate, or migrate toward this full architecture unless explicitly instructed for a specific, scoped component.

### 4.2 Implement only scoped slices

When given a task, implement **only** the specific feature or change requested. Do not:
- Create adjacent services, models, or APIs "because the architecture says they should exist"
- Refactor existing working code to match architectural naming conventions
- Add infrastructure dependencies not required by the immediate task

### 4.3 Follow the source of truth hierarchy

```
1. Current user prompt (highest priority)
2. This IMPLEMENTATION_STATUS.md
3. Latest ADRs in /docs/adr/
4. docs/README.md (governance rules)
5. Group A documents in /docs/implementation/
   ─────────────────────────────────────────
6. Group C documents (domain context, consulted as needed)
7. Group B documents (directional only, never implemented wholesale)
8. Group D documents (never used for implementation)
```

### 4.4 Respect the current tech stack

The active tech stack is:
- **Python 3.12** with `requirements.txt` dependency management
- **Google Gemini** (`google-genai`) for LLM calls, not OpenAI
- **Streamlit** for UI interactions and secret management
- **Pydantic** for structured output validation
- **Flat JSON files** for data persistence

Do not introduce FastAPI, SQLAlchemy, Alembic, Redis, RQ, Next.js, or any other infrastructure component unless the user's prompt explicitly requests it.

### 4.5 Preserve working patterns

The current codebase has established patterns that work:
- `generate_gemini_json()` as the universal LLM call wrapper (with timing + token tracking)
- Pydantic models as LLM output schemas (validated via `model_validate_json`)
- Per-source prompt functions (`create_youtube_prompt()`, etc.) that inject raw JSON data
- Connector functions that return standardized dictionaries with `{source}_clipping_metadata` + content arrays
- File-based I/O: `outputs/scraping/` for raw data, `outputs/analysis/` for processed results

Extend these patterns; do not replace them without explicit instruction.

### 4.6 When in doubt, ask

If a requested change appears to conflict with this document, the target architecture, or existing code patterns, **ask the user for clarification** rather than making assumptions.
