# 10_repo_blueprint.md

## Purpose

Define the repository structure, engineering conventions, development guardrails, and AI coding-first rules for the platform.

This document exists to make sure:

1. the project can move fast without losing quality
2. coding agents do not introduce architectural drift
3. implementation remains consistent across modules
4. developers and AI systems work from the same operational model
5. the platform does not become fragile as features are added

This document should be treated as an engineering constitution for the MVP.

---

## Core Engineering Principles

### 1. Build for speed, not chaos
The objective is to move fast without creating a codebase that collapses under its own inconsistency.

### 2. Prefer explicitness over cleverness
This product handles business-critical logic. Code should be obvious, inspectable, and easy to debug.

### 3. One pattern per concern
There should not be three different ways to:
- define models
- define API routes
- define jobs
- structure services
- handle errors
- build dashboard data loaders

### 4. Keep the architecture monolithic for now
Do not introduce microservices.
Do not split into multiple deployables unless strictly necessary.

### 5. AI writes drafts, humans own the codebase
AI is a multiplier.
It is not the final source of truth.

### 6. Business logic must not hide in prompts only
Prompts are part of business logic, but critical rules must also exist in code where appropriate:
- thresholds
- cadence
- scoring formulas
- filtering rules
- candidate scoping
- platform mappings

### 7. Traceability over magic
The system should make it easy to answer:
- where this output came from
- what source generated this record
- what job produced this recommendation
- what prompt version was used

---

## Repository Structure

Recommended root structure:

```text
/docs
/prompts
/backend
/frontend
/scripts
/tests
```

### /docs
Project documentation and AI-operable specs.

Expected files:
- 01_product_overview.md
- 02_system_architecture.md
- 03_data_model.md
- 04_ai_agents.md
- 05_engineering_backlog_mvp.md
- 06_collection_architecture.md
- 07_narrative_graph_architecture.md
- 08_api_spec.md
- 09_jobs_and_crons.md
- 10_repo_blueprint.md

### /prompts
Versioned prompt files used by jobs and services.

Suggested files:
- narrative_detection.md
- narrative_cluster_summary.md
- strategic_opportunity.md
- content_recommendation.md
- competitor_risk.md
- ally_amplification.md
- missed_opportunity.md
- daily_briefing.md

### /backend
All API, jobs, models, services, connectors, and infrastructure logic.

### /frontend
Dashboard application.

### /scripts
Developer scripts and maintenance scripts.

### /tests
Automated tests.

---

## Backend Blueprint

Recommended structure:

```text
/backend
  /app
    /api
    /core
    /db
    /models
    /schemas
    /services
    /jobs
    /connectors
    /repositories
    /utils
    /prompts
    /ops
    main.py
  /alembic
  /tests
```

---

## Backend Folder Responsibilities

### /app/api
FastAPI routers only.

Contains:
- route registration
- request parsing
- response serialization
- minimal validation
- no heavy business logic

Suggested modules:
- candidates.py
- candidate_themes.py
- candidate_sensitive_topics.py
- candidate_audiences.py
- allies.py
- competitors.py
- social_accounts.py
- monitored_sources.py
- sync.py
- content_items.py
- performance.py
- narratives.py
- narrative_graph.py
- strategy.py
- recommendations.py
- briefings.py
- ops.py

### /app/core
Core app configuration.

Contains:
- settings
- environment loading
- constants
- logging config
- feature flags
- platform enums
- job names
- app-wide policy rules

### /app/db
Database setup.

Contains:
- engine
- session factory
- base metadata
- migration helpers

### /app/models
SQLAlchemy / SQLModel models only.

Contains persistence definitions, not service logic.

### /app/schemas
Pydantic request/response schemas.

Keep schemas explicit and versionable.

### /app/services
Business logic layer.

Contains:
- candidate services
- performance aggregation services
- narrative services
- strategic reasoning orchestration
- briefing composition
- graph operations
- recommendation assembly

This should be the main home of application logic.

### /app/jobs
Background job definitions.

Contains one module per job domain:
- collection.py
- normalization.py
- embeddings.py
- topics.py
- performance.py
- narratives.py
- graph.py
- strategy.py
- competitors.py
- allies.py
- briefings.py
- delivery.py

### /app/connectors
External data connectors.

Contains:
- base connector interface
- youtube connector
- rss connector
- apify instagram connector
- apify tiktok connector
- apify x connector
- future proprietary crawler connectors

### /app/repositories
Database access helpers or repository pattern if needed.

Use only if it actually reduces duplication.
Do not force a heavy repository abstraction if services can directly use the session clearly.

### /app/utils
Helpers that are truly generic.

Examples:
- date helpers
- metric calculation helpers
- hash utilities
- retry helpers
- parsing helpers

Do not dump business logic here.

### /app/prompts
Prompt loading and version handling.

This may load prompt files from `/prompts` or reference packaged prompt assets.

### /app/ops
Operational helpers and internal admin functions.

Examples:
- job status query helpers
- connector health checks
- system diagnostics

---

## Frontend Blueprint

Recommended structure:

```text
/frontend
  /src
    /app
    /components
    /features
    /lib
    /services
    /types
    /theme
```

If using Next.js App Router:

```text
/frontend/src/app
```

should contain route entrypoints only.

---

## Frontend Folder Responsibilities

### /src/app
Page-level route files.

Minimal logic.

### /src/components
Reusable presentational components.

Examples:
- stat cards
- data tables
- chart wrappers
- filters
- drawers
- page headers

### /src/features
Domain-specific modules.

Suggested features:
- candidates
- sources
- content
- performance
- narratives
- narrative-graph
- strategy
- recommendations
- briefings
- ops

Each feature can contain:
- components
- hooks
- service calls
- local types
- page sections

### /src/lib
Low-level utilities:
- date formatting
- query param helpers
- shared constants

### /src/services
API client layer.

One service module per backend domain:
- candidates.ts
- themes.ts
- sources.ts
- content.ts
- performance.ts
- narratives.ts
- strategy.ts
- recommendations.ts
- briefings.ts
- ops.ts

### /src/types
Shared frontend types.

### /src/theme
MUI theme config:
- tokens
- typography
- spacing
- palette
- component overrides

---

## MUI Guardrails

Since the project uses MUI, the front-end must follow strict consistency rules.

### Required
- define a single app theme early
- use spacing rules consistently
- keep typography scale stable
- prefer reusable wrappers for cards, filters, tables, and metric blocks
- centralize color tokens

### Avoid
- random inline styling everywhere
- multiple visual patterns for the same concept
- inconsistent page layout widths
- overuse of MUI complexity when a simple component will do

### Recommendation
Create a lightweight internal UI layer on top of MUI:
- `PageShell`
- `SectionCard`
- `MetricCard`
- `DataTableShell`
- `FilterBar`
- `InsightCard`

This gives consistency without building a full design system.

---

## Module Design Rules

Every feature module should define:

1. purpose
2. inputs
3. outputs
4. tables involved
5. jobs involved
6. routes involved
7. prompt dependencies if any

No feature should be coded without this clarity.

---

## Coding Guardrails for AI Agents

This section is critical.

### Rule 1 — Do not invent architecture
AI must follow the documented repo and module structure exactly.

### Rule 2 — Do not create parallel abstractions
If there is already a `service` pattern, do not introduce:
- managers
- handlers
- use cases
- controllers
unless explicitly approved

### Rule 3 — Keep routes thin
Routers should not contain heavy business logic.

### Rule 4 — Keep jobs explicit
Jobs must:
- take clear args
- log start and finish
- catch expected failures
- write observable outcomes

### Rule 5 — No hidden cross-candidate leakage
All logic must preserve candidate scoping.
No query or aggregation should accidentally mix candidates unless explicitly intended.

### Rule 6 — Do not hardcode prompt text in random files
Prompts must be versioned and centralized.

### Rule 7 — Do not create database schema drift
Models, migrations, and schemas must remain aligned.

### Rule 8 — Prefer complete vertical slices
When implementing, finish a coherent module end-to-end rather than partially scaffolding ten modules.

### Rule 9 — Do not optimize prematurely
No premature caching layer, graph DB, event bus, or microservice split.

### Rule 10 — Every important AI output must be inspectable
When feasible, store:
- prompt version
- generation timestamp
- source references
- confidence or scoring basis

---

## Anti-Drift Rules

Drift is one of the biggest risks in an AI coding-first project.

### Architectural drift
Prevent by:
- keeping one documented folder structure
- reviewing PRs for new patterns
- not allowing ad hoc module placement

### Naming drift
Prevent by:
- standardizing domain names early
- using the same names across:
  - docs
  - models
  - API routes
  - services
  - front-end features

Example:
Use `narratives` everywhere, not:
- discourse_clusters in one place
- talking_points in another
- signals in another

### Style drift
Prevent by:
- formatting and linting
- code review
- example modules to copy from

### Prompt drift
Prevent by:
- versioning prompts
- tracking prompt purpose
- not letting each agent invent a new prompt style in-line

---

## Data and Business Logic Guardrails

### Candidate scoping
Every domain object should clearly indicate whether it is:
- global
- source-level
- candidate-specific

Default to candidate-specific unless clearly global.

### Source normalization
Never bypass normalization and insert platform-specific content directly into higher-level logic.

### Metrics consistency
Metric formulas must be centralized.

Example:
- engagement_count
- engagement_rate
- velocity_score

These should not be recalculated differently in multiple places.

### Narrative consistency
Narratives should be built from consistent pipeline steps:
1. collect
2. normalize
3. embed
4. topic-tag
5. cluster
6. summarize
7. strategize

Do not short-circuit this with random one-off logic.

### Briefing consistency
Daily briefing structure must stay stable enough that users build trust in it.

---

## Prompt Management Rules

Prompt files should have a consistent format:

- title
- purpose
- input contract
- output contract
- version
- notes
- failure modes

Suggested prompt front-matter pattern:

```text
name: strategic_opportunity
version: v1
purpose: determine candidate-specific strategic opportunity from narratives
input_schema: ...
output_schema: ...
```

Prompt execution code should:
- reference prompt by name
- record version
- validate output schema where possible

---

## Testing Blueprint

Testing must be pragmatic.

### Minimum automated test coverage should include:

#### Backend
- model creation
- key service functions
- route smoke tests
- metric formula tests
- job idempotency for core jobs
- prompt output parsing where applicable

#### Frontend
- page render smoke tests
- key component rendering
- API client integration tests where useful

### Priority test targets
1. candidate setup
2. source sync
3. performance aggregation
4. narrative generation pipeline
5. briefing build pipeline

---

## Logging and Observability Rules

Every important job should log:
- started_at
- finished_at
- candidate scope if applicable
- source scope if applicable
- number of items processed
- failure reason if error

Every delivery action should log:
- channel
- payload type
- delivery status

Operational dashboards must exist for:
- connector health
- failed jobs
- stale briefings
- failed sends

---

## Migration Rules

### Schema changes
- every schema change requires migration
- no silent model drift
- migration names must be descriptive

### AI guardrail
Never allow coding agents to modify models without:
- migration draft
- schema update
- API impact awareness

---

## Dependency Rules

Approved stack for MVP:

### Backend
- FastAPI
- Pydantic
- SQLAlchemy or SQLModel
- Alembic
- Redis
- RQ

### Frontend
- Next.js
- React
- MUI
- chart library

### Collection
- YouTube API
- RSS parser
- Apify connectors where needed

### AI
- OpenAI API
- optional second provider later

Do not introduce new core dependencies casually.

Particularly avoid:
- LangChain-heavy abstractions unless clearly justified
- graph database early
- heavy workflow engines early
- complex event systems early

---

## Definition of a Good AI-Generated Contribution

A generated code contribution is acceptable if it:

- follows the repo structure
- uses existing patterns
- is readable
- avoids unnecessary abstraction
- preserves candidate scoping
- keeps business logic explicit
- is testable
- includes reasonable error handling

A generated contribution is not acceptable if it:

- invents new architecture
- duplicates logic in a new pattern
- hides rules in magic helpers
- increases coupling without reason
- creates unreviewed schema changes
- ignores existing docs

---

## Recommended Development Sequence

The repo should be built in this order:

1. foundation and conventions
2. candidate setup
3. monitored sources and sync logs
4. content ingestion
5. performance analytics
6. narratives
7. strategic engine
8. recommendations
9. competitors and allies
10. narrative graph
11. briefings and WhatsApp delivery
12. ops and QA

This order reduces integration risk and keeps AI-generated code grounded in stable structures.

---

## Human Review Checklist

Before merging AI-generated code, reviewers should check:

- Does it follow the documented folder structure?
- Does it preserve candidate scoping?
- Does it duplicate existing logic?
- Does it introduce a new pattern without justification?
- Are metrics calculated consistently?
- Are prompt references centralized?
- Are migrations included if models changed?
- Is the code easy to debug later?
- Would another AI session understand this file easily?

If the answer to several of these is no, the code should be revised.

---

## Strategic Conclusion

This repo blueprint is not just about organization.
It is a protection layer against the two biggest risks of an AI coding-first project:

1. speed turning into entropy
2. generated code turning into architectural drift

If this blueprint is respected, the team can move quickly while still building a platform that remains coherent, debuggable, and extensible.
