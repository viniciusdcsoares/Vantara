# ADR-003: Streamlit + Flat Scripts as MVP Runtime

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-03-31 |
| **Relates To** | DIVERGENCE_LOG DIV-001/DIV-002/DIV-003 |

---

## Context

The target architecture specifies FastAPI, PostgreSQL, Redis/RQ, and Next.js. The MVP was built with Python scripts and Streamlit instead. This was an intentional decision, not an accident.

## Decision

**The MVP runtime is Streamlit + flat Python scripts + JSON file persistence.** This stack remains in place until the intelligence pipeline (per-item analysis → embeddings → clustering) is validated with real data.

### Rationale

1. **Speed over ceremony:** Standing up FastAPI + PostgreSQL + Redis for an unvalidated pipeline wastes time.
2. **Iteration velocity:** Changing a Python script and re-running it is faster than managing migration files, API routes, and queue workers.
3. **Secrets simplicity:** `st.secrets` works for a single-developer MVP.
4. **Zero infrastructure cost:** No Docker, no database server, no Redis instance.

### Migration trigger

Infrastructure convergence begins **only** when:
- Per-item analysis (ADR-001) is validated
- Embedding + clustering produces meaningful cross-source narratives
- The team needs multi-user access or scheduled execution

## Consequences

- **Positive:** Maximum development speed, zero ops overhead, easy debugging.
- **Negative:** No API for external integrations, no concurrent processing, no data durability guarantees.
- **Accepted risk:** JSON files can be lost. At MVP scale, re-running the pipeline is cheaper than building backup infrastructure.
