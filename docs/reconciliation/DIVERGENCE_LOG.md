# DIVERGENCE LOG — Historical Record

> **Created:** 2026-03-31  
> **Purpose:** Historical context appendix. Lists and details all divergences between the legacy documentation (Group B/C/D) and the actual MVP code. This file keeps the main operational rules (`IMPLEMENTATION_STATUS.md`) clean — it serves as the reference for *why* things differ.  
> **Active reference:** For implementation rules and current state, see [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md).

---

## Classification Criteria

A divergence is classified as **critical** when it blocks the advancement of the MVP pipeline. It is **structural** when it involves infrastructure that was intentionally deferred. It is **cosmetic** when it affects naming or organization without functional impact.

---

## 1. Infrastructure Divergences (Structural)

### DIV-001 — Web Framework

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Backend** | FastAPI with versioned routes `/api/v1/` | No server — local Python scripts executed manually |
| **Frontend** | Next.js + React + MUI with route-based pages | Streamlit (single-file UI for parameter config + output visualization) |
| **Source docs** | `02_system_architecture.md`, `08_api_spec.md`, `10_repo_blueprint.md` |

**Decision:** Intentionally deferred. No value in standing up FastAPI until the intelligence pipeline logic is validated. See [ADR-003](../adr/ADR-003-streamlit-mvp-runtime.md).

### DIV-002 — Data Persistence

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Database** | PostgreSQL 16 + pgvector extension (15+ tables defined) | Flat JSON files in `outputs/` directory |
| **Vector storage** | `pgvector` column on `arguments` table | No vector storage whatsoever |
| **Migrations** | Alembic-managed schema migrations | N/A — no database to migrate |
| **Source docs** | `18_database_schema_final.md` |

**Decision:** Intentionally deferred. JSON file persistence is sufficient for MVP-scale data validation. The cost of maintaining a database (schema management, connection pooling, DevOps) exceeds the benefit at this stage.

### DIV-003 — Processing & Queues

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Queues** | Redis + RQ with 8 named queues (`ingestion_queue`, `embedding_queue`, etc.) | None — all processing is synchronous and sequential |
| **Workers** | Dedicated workers per pipeline stage, horizontally scalable | Direct function calls in `main.py` and `run_analysis.py` |
| **Cron jobs** | Scheduled cadences (every 15min to 4h depending on source type) | Manual execution only — user triggers scripts |
| **Retry logic** | Exponential backoff with 3 retries per job | Basic `try/except` blocks with error logging |
| **Source docs** | `09_jobs_and_crons.md`, `17_ai_processing_pipeline.md` |

**Decision:** Deferred. Synchronous processing works at the current MVP scale (minutes per run, not hours). Queue infrastructure becomes necessary only when the system needs to process hundreds of items concurrently or run on a schedule.

---

## 2. Intelligence Pipeline Divergences (Critical)

### DIV-004 — Pipeline Structure

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Stages** | 9 asynchronous stages: `content → relevance filter → argument extraction → embedding → clustering → narrative inference → scoring → recommendation → briefing` | 3 synchronous phases: `scrape → per-item analysis & embedding → audit & review` |
| **Orchestration** | Queue-driven, each stage publishes jobs to the next queue | Direct sequential function calls in `run_scraping.py` and `run_llm_analysis.py` |
| **Source docs** | `17_ai_processing_pipeline.md` |
| **Status** | **Partially Converged** (Simplified MVP path implemented) |

**Impact:** This is the most critical divergence in the entire project. The 7 missing stages represent the core value proposition of the platform — cross-source narrative detection. `ADR-001` defines the convergence path starting from per-item analysis as the first vertical slice.

### DIV-005 — Processing Granularity

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Analysis unit** | Per-argument: each content item produces extracted claims, each claim gets an independent embedding vector | Per-item: Each YouTube video, Bluesky post, or news article is analyzed individually producing a `canonical_claim`. |
| **Output schema** | `ItemAnalysis` with `canonical_claim`, `claim_type`, `topic_tags`, `sentiment`, `key_actors` | `YoutubeAnalysis`, `BlueskyAnalysis`, `NewsAnalysis` (per-item schemas) |
| **Cross-source capability** | All items share the same schema → source-agnostic downstream processing | **Converged**: All sources produce `canonical_claim` allowing cross-source clustering. |
| **Source docs** | `14_narrative_scoring_and_argument_model.md`, `17_ai_processing_pipeline.md` |
| **Status** | **Converged** |

**Impact:** Blocking. Without a `canonical_claim` extracted per content item, there is no discrete unit of text to embed. Without embeddings, there is no clustering. Without clustering, there is no cross-source narrative detection. `ADR-001` (status: Proposed) directly addresses this divergence as the highest-priority convergence step.

### DIV-006 — Embeddings

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Embedding input** | Extracted argument text (`canonical_claim`) — one embedding per claim | `argument_claim_canonical` (or fallback) produced per item. |
| **Embedding model** | OpenAI `text-embedding-ada-002` | Google `gemini-embedding-001` integrated. |
| **Vector storage** | `pgvector` column with cosine similarity queries | Local NumPy arrays + Parquet/JSON persistence. Audit via `audit_nearest_neighbors.py`. |
| **Dimensionality** | Not specified in docs | 768 dimensions (Gemini standard) |
| **Source docs** | `17_ai_processing_pipeline.md`, `18_database_schema_final.md` |
| **Status** | **Converged** |

**Impact:** Blocking. Embeddings are a hard prerequisite for semantic clustering across sources. This divergence is sequentially dependent on DIV-005 — per-item analysis must exist before embeddings can be generated. See [ADR-002](../adr/ADR-002-canonical-claim-over-framing.md) for the decision to use `canonical_claim` (not framing) as the embedding input.

### DIV-007 — Clustering & Narrative Detection

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Clustering algorithm** | K-Means or HDBSCAN over embedding vectors | K-Means (k=3) implemented in `run_llm_analysis.py`. |
| **Narrative inference** | LLM call per cluster to infer the overarching narrative frame | Partially implemented: clustering exists; narrative inference per cluster is the next step for human-in-the-loop validation. |
| **Narrative graph** | Full relational model with temporal tracking | Flat JSON/Parquet with `item_id` and `cluster` mapping. |
| **Cross-source detection** | YouTube, Bluesky, and News items share the same embedding space. | **Converged**: Cross-source clustering is now functional. |
| **Source docs** | `07_narrative_graph_architecture.md`, `14_narrative_scoring_and_argument_model.md` |
| **Status** | **Converged** |

**Impact:** Blocking for MVP v1. Cross-source narrative clustering is the central differentiator of the Vantara platform. This is sequentially dependent on DIV-006 (embeddings).

---

## 3. Domain Model Divergences (Structural)

### DIV-008 — Candidate Entity

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Candidate model** | Full configuration: political profile, strategic themes, sensitive topics, target audiences, geographic context, communication style, competitor/ally mapping — with dedicated database tables and CRUD APIs | **Does not exist** — the system is purely topic-based, not candidate-scoped |
| **Relevance scoring** | Multi-factor formula: theme match (0.30) + actor importance (0.20) + engagement (0.15) + growth velocity (0.15) + geographic match (0.10) + audience match (0.10) | No scoring — the LLM produces qualitative assessments (`growth_status` enum) |
| **Candidate isolation** | Multi-tenant: each candidate sees only their own data and analyses | Single-user: one topic at a time, no concept of "whose analysis is this" |
| **Source docs** | `16_candidate_configuration_and_relevance_model.md`, `01_product_overview.md` |

**Decision:** Intentionally deferred to after pipeline stabilization. The topic-based approach was chosen to validate the scraping + analysis flow before adding the complexity of candidate-scoping. Adding a candidate model presupposes working narratives to score against.

### DIV-009 — Narrative Scoring

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Scoring formulas** | Narrative Priority Index (NPI), opportunity score, risk score — all numeric with defined factor weights | None — LLM produces `growth_status` as a qualitative enum (`growing`, `stable`, `declining`, `unclear`) |
| **Temporal analysis** | Recency weighting, velocity detection, lifecycle stage identification, resurgence detection | No temporal analysis — each analysis run is independent with no cross-run comparison |
| **Score persistence** | `narrative_scores` table with historical snapshots | N/A — no persistence beyond flat JSON files |
| **Source docs** | `14_narrative_scoring_and_argument_model.md` |

**Decision:** Deferred. Numeric scoring requires clustered narrative data as input. Without clustering (DIV-007), scoring formulas have nothing to compute against.

---

## 4. Prompt & LLM Divergences (Partially Convergent)

### DIV-010 — Prompt Architecture

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Storage format** | Markdown files in `/prompts` directory with YAML metadata headers (name, version, input/output contracts, known caveats) | Python files in `llm_configs/prompts/` with system instruction strings and prompt-builder functions |
| **Prompt count** | 7 prompt types defined: `narrative_detection`, `strategic_opportunity`, `content_recommendation`, `competitor_analysis`, `ally_amplification`, `missed_opportunity`, `daily_briefing` | 1 prompt type implemented: `narrative_detection` (with 3 source-specific variants for YouTube, Bluesky, News) |
| **Versioning** | Explicit version numbers in prompt metadata (e.g., `v1`, `v2`) with staging test requirements | No versioning — prompts are edited in-place in Python source files |
| **LLM provider** | OpenAI (implied throughout architecture docs) | Google Gemini `gemini-2.5-flash` via `google-genai` SDK |
| **Output validation** | Schema governance policy with prompt-schema contracts | Pydantic schema validation via `model_validate_json()` — **partially aligned and arguably superior** |
| **Source docs** | `13_prompt_library.md`, `11_runtime_and_prompt_governance.md` |

**Positive note:** The Pydantic-validated structured output approach in the current code is architecturally **superior** to the markdown-based prompt templates described in the target architecture. The current code uses `response_mime_type="application/json"` with `response_schema=<PydanticModel>`, which provides compile-time schema enforcement that markdown templates cannot. This is a case where the MVP code should inform the target architecture, not the other way around. Future prompts should follow the established pattern: Python function for prompt construction + Pydantic model for output schema.

---

## 5. Repository Structure Divergences (Cosmetic)

### DIV-011 — Repository Layout

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Expected** | `/backend/app/{api,services,models,...}`, `/frontend/`, `/prompts/`, `/scripts/`, `/tests/` | Flat: `scraping/`, `llm_configs/`, `outputs/`, `docs/` at repository root |
| **Test infrastructure** | `/tests` directory with pytest configuration | No tests whatsoever |
| **Source docs** | `10_repo_blueprint.md`, `12_bootstrap_repo_tasks.md` |

**Decision:** The flat structure is adequate for the MVP. Reorganization into a structured backend layout only makes sense when an API server is introduced.

### DIV-012 — Setup Script & Tooling

| Dimension | Legacy Docs | Current Code |
|---|---|---|
| **Expected setup** | Bootstrap script creating venv + FastAPI + Alembic + Next.js + Docker Compose + Redis | `pip install -r requirements.txt` + configure `st.secrets` |
| **Linting** | ESLint + Black/Ruff configured with CI | No linting configured |
| **CI/CD** | Backend lint, frontend lint, migration validation, test execution | No CI/CD pipeline |
| **Source docs** | `21_first_repo_setup_script.md` |

**Note:** Document `21_first_repo_setup_script.md` is completely obsolete — it describes a setup sequence that was never executed and does not match the current repository in any dimension.

---

## 6. Superseded Documents

These legacy documents have been explicitly superseded by active implementations or newer documentation:

| Document | Status | Reason |
|---|---|---|
| `00_master_documentation_index.md` | **Superseded** | Replaced by `docs/README.md` + `IMPLEMENTATION_STATUS.md` as the canonical documentation index. The original assumes all docs are authoritative, which conflicts with the Group A/B/C/D classification system. |
| `12_bootstrap_repo_tasks.md` | **Superseded** | Describes a FastAPI/Alembic/Redis/RQ bootstrap sequence that was never executed. The MVP chose a script-first approach (`main.py` + `run_analysis.py`) instead. Following this document would create a repository structure incompatible with the actual code. |
| `13_prompt_library.md` | **Superseded** | Contains 7 prompt templates in markdown format with placeholder schemas. Superseded by the actual Python implementation in `llm_configs/prompts/narrative_detection.py` and `llm_configs/schemas/narrative_detection.py` which use Pydantic-validated structured outputs — a more robust approach. |
| `21_first_repo_setup_script.md` | **Superseded** | Describes a setup sequence (venv, FastAPI, Alembic, Next.js, MUI) that does not match the current repository. The actual setup is: `pip install -r requirements.txt` + configure `.streamlit/secrets.toml`. |

---

## Impact Summary for MVP

| Priority | Divergences | What They Block | Action Required |
|---|---|---|---|
| ✅ **P0 — Blocking** | DIV-004, DIV-005 | — | **Converged** (Per-item analysis implemented) |
| ✅ **P1 — Required for v1** | DIV-006, DIV-007 | — | **Converged** (Embeddings & Clustering implemented) |
| 🟡 **P2 — Deferred** | DIV-001, DIV-002, DIV-003, DIV-008, DIV-009 | Multi-tenant, numeric scoring | After intelligence pipeline stabilization |
| ⚪ **P3 — Cosmetic** | DIV-010, DIV-011, DIV-012 | Nothing functional | Address during future major refactor |
