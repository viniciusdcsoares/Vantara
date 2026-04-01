# Vantara — Documentation Hub

> **Last updated:** 2026-04-01  
> **Maintained by:** Human lead + AI agents  
> **Governance:** This file defines the documentation taxonomy. All coding agents **must** read this before acting on the repository.

---

## 1. Purpose

This directory is the **single source of truth** for the Vantara Political Intelligence Platform project. It reconciles the gap between a comprehensive architectural blueprint (22 design documents) and the actual codebase — a lean, experimental MVP built with Python scripts and Streamlit.

The documentation is organized into **four authority classes**, each with clear rules about how coding agents should treat them. Understanding these classes is **mandatory** before generating or modifying any code.

---

## 2. Directory Structure

```
/docs
  ├── /architecture        Group B — Target Architecture
  │     Full-scale system blueprint: services, queues, database schemas,
  │     API specs, job orchestration, narrative graph, scoring models.
  │
  ├── /product             Group C — Product & Domain Context
  │     Business logic, product vision, data models, collection strategy,
  │     AI agent philosophy, engineering backlog.
  │
  ├── /implementation      Group A — Authoritative Now
  │     Documents that describe the *current* code and active conventions.
  │     AI coding playbook, prompt governance in use today.
  │
  ├── /adr                 Group A — Authoritative Now
  │     Architecture Decision Records: immutable, timestamped decisions
  │     that override any conflicting target architecture document.
  │
  └── /reconciliation      The Bridge
        IMPLEMENTATION_STATUS.md — current code state, agent instructions.
        DIVERGENCE_LOG.md — historical divergence context appendix.
        SPRINT_PLAN.md — lean MVP sprint schedule.
```

---

## 3. Documentation Classes

### Group A — Authoritative Now

Documents that reflect the **current state of the code** or **immutable active decisions**. When any other document conflicts with a Group A document, **Group A wins**.

| Location | Contents |
|---|---|
| `/docs/reconciliation/IMPLEMENTATION_STATUS.md` | Live project state — what the code does today, LLM details, connector specs, agent instructions |
| `/docs/reconciliation/DIVERGENCE_LOG.md` | Historical divergence appendix — all gaps between legacy docs and code |
| `/docs/reconciliation/SPRINT_PLAN.md` | Lean MVP sprint schedule — 4-sprint critical path |
| `/docs/implementation/20_ai_coding_playbook.md` | Active operational rules for AI-assisted development |
| `/docs/implementation/11_runtime_and_prompt_governance.md` | Prompt versioning, secret management, cost control policies |
| `/docs/adr/` | All Architecture Decision Records |
| `/docs/README.md` | This file (governance taxonomy) |

**Rule:** These are the hard constraints for code generation. Never violate them.

### Group B — Target Architecture

The **ideal end-state** blueprint. These documents describe a full-scale platform with FastAPI microservices, PostgreSQL/pgvector, Redis/RQ job queues, an async 9-stage AI pipeline, a Next.js + MUI dashboard, and WhatsApp delivery. They are aspirational — the destination, not the current position. **Massive divergences exist** with the current MVP code. See [DIVERGENCE_LOG.md](./reconciliation/DIVERGENCE_LOG.md) for the complete list.

| Location | What It Describes |
|---|---|
| `/docs/architecture/00_vantara_architecture.md` | Foundational technical architecture and platform modules |
| `/docs/architecture/02_system_architecture.md` | Logical services, batch-first processing, component diagram |
| `/docs/architecture/06_collection_architecture.md` | Collection orchestrator with replaceable connectors |
| `/docs/architecture/07_narrative_graph_architecture.md` | Full narrative graph: Topics → Narratives → Arguments → Actors |
| `/docs/architecture/08_api_spec.md` | RESTful API with resource-oriented paths |
| `/docs/architecture/09_jobs_and_crons.md` | Background jobs, Redis/RQ orchestration, cron schedules |
| `/docs/architecture/10_repo_blueprint.md` | Repository structure: `backend/app/{api,services,models,...}` |
| `/docs/architecture/14_narrative_scoring_and_argument_model.md` | Scoring formulas: NPI, opportunity score, risk score |
| `/docs/architecture/16_candidate_configuration_and_relevance_model.md` | Candidate context model (themes, audiences, positioning) |
| `/docs/architecture/17_ai_processing_pipeline.md` | 9-stage async pipeline: filter → extract → embed → cluster → infer → score → recommend → brief |
| `/docs/architecture/18_database_schema_final.md` | 15+ PostgreSQL tables with pgvector |

**Rule:** Use these for directional guidance and long-term planning. **Never** attempt to implement the full blueprint in a single pass. Always check `IMPLEMENTATION_STATUS.md` to understand which slices have been authorized for implementation.

### Group C — Product & Domain Context

Business context, product vision, domain knowledge, and strategic planning documents used for understanding **why** the system exists and **what** it should ultimately do.

| Location | What It Provides |
|---|---|
| `/docs/product/01_product_overview.md` | Product vision, value proposition, AI-coding-first operating principle |
| `/docs/product/03_data_model.md` | Conceptual data model: political entities, content, intelligence entities |
| `/docs/product/04_ai_agents.md` | AI agent philosophy: jobs + services + prompts, not autonomous agents |
| `/docs/product/05_engineering_backlog_mvp.md` | MVP sprint structure and delivery milestones (theoretical sequence) |
| `/docs/product/15_data_collection_strategy_v2.md` | Source prioritization, argument extraction concepts, signal quality principles |
| `/docs/product/19_mvp_build_sequence.md` | 4-week build plan (flexibilized — MVP took a faster script-first approach) |

**Rule:** Consult these when you need domain context for a decision (e.g., "what is a narrative?", "how should candidate relevance work?"). They do not directly dictate code structure.

### Group D — Historical / Superseded / Legacy

Documents that have been **superseded** by active decisions or are outdated relative to the current MVP approach. They remain in the repository as historical reference only. See [DIVERGENCE_LOG.md § 6](./reconciliation/DIVERGENCE_LOG.md) for detailed rationale.

| Document | Why Superseded |
|---|---|
| `00_master_documentation_index.md` | Replaced by this README + `IMPLEMENTATION_STATUS.md` |
| `12_bootstrap_repo_tasks.md` | FastAPI/Alembic/Redis bootstrap was never executed |
| `13_prompt_library.md` | Superseded by actual Python implementation in `llm_configs/` |
| `21_first_repo_setup_script.md` | Setup described doesn't match actual repo |

**Rule:** Do **not** use these as implementation guides. They exist only for archaeological reference.

---

## 4. The Golden Rule

> **"When implementation and target architecture differ during MVP convergence, `IMPLEMENTATION_STATUS.md` and the latest ADRs govern what coding agents should implement next."**

This rule is absolute. No exceptions. Every coding agent — human or AI — must internalize it before writing a single line of code.

---

## 5. Quick Start for Coding Agents

1. **Read** `docs/reconciliation/IMPLEMENTATION_STATUS.md` — understand the current code state.
2. **Read** `docs/README.md` (this file) — understand the documentation hierarchy.
3. **Check** `/docs/adr/` for any ADRs relevant to your task.
4. **Consult** Group B or C documents **only** for directional context.
5. **Implement** only the specific scoped slice requested in the current prompt.
6. **Never** refactor the repository to match Group B documents globally.

---

## 6. File Migration Reference

The original flat-file documentation (`00_` through `21_`) has been classified and migrated into the structure above. See `DIVERGENCE_LOG.md` for the complete nominal mapping with rationale for each classification.
