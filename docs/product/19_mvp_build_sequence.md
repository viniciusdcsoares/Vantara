# 19_mvp_build_sequence.md

## Purpose

Turn the full architecture into a concrete 4-week MVP build plan.

This document defines:
- weekly implementation order
- exact module priorities
- backend, frontend, and AI workstreams
- validation checkpoints
- recommended use of Claude Code and Codex
- what must exist before moving to the next stage

The goal is simple:

Build the smallest version of the platform that is:
- real
- demoable
- sellable
- extensible

---

# Build Philosophy

This MVP should be built as a sequence of **vertical slices**, not disconnected abstractions.

Priority rule:

1. Make the system ingest real data
2. Make the system show useful signals
3. Make the system reason about those signals
4. Make the system deliver clear recommendations
5. Make the system easy to demonstrate and operate

Do not optimize for elegance before usefulness.

---

# Team Assumption

Recommended operating model:

- Claude Code → planning, structure refinement, code review support
- Codex → implementation, scaffolding, repetitive code generation
- Human backend/devops → integration, review, debugging
- Human frontend dev → MUI dashboard, polish, interaction quality
- Human product/strategy → validation of outputs and political usefulness

---

# Week 1 — Foundation + Candidate Setup + Initial Collection

## Objective

By the end of Week 1, the team should be able to:

- run the backend and frontend
- create candidates
- configure sources
- collect real content from at least RSS and YouTube
- view collected content in a dashboard

---

## Backend Scope

### 1. Repo initialization
Create:

```text
/docs
/prompts
/backend
/frontend
/scripts
/tests
```

### 2. Backend base
Initialize:

- FastAPI
- SQLAlchemy or SQLModel
- Alembic
- Redis
- RQ
- environment config
- logging config

### 3. First database models
Implement and migrate:

- candidates
- candidate_config
- candidate_themes
- candidate_sensitive_topics
- candidate_audiences
- monitored_sources
- actors
- content_items
- content_metrics
- source_sync_logs

### 4. Basic APIs
Implement:
- GET /health
- CRUD candidates
- CRUD candidate themes
- CRUD sensitive topics
- CRUD audiences
- CRUD monitored sources
- GET content-items

### 5. First connectors
Implement:
- RSS connector
- YouTube connector

### 6. First jobs
Implement:
- sync_single_source
- sync_rss_sources
- sync_youtube_sources
- normalize_new_content

---

## Frontend Scope

### 1. Frontend base
Initialize:
- Next.js
- MUI
- base theme
- app shell
- routing structure
- API service layer

### 2. Screens
Build:
- candidates list
- candidate detail
- candidate setup sections
- monitored sources table
- content list table

### 3. Reusable components
Build:
- PageShell
- SectionCard
- DataTableShell
- FilterBar
- MetricCard

---

## AI Scope

### 1. Prompt infrastructure
Set up:
- prompt loading strategy
- prompt version metadata
- `/prompts` file structure

### 2. No heavy LLM usage yet
Week 1 should not depend heavily on prompts.
Focus on infrastructure and ingestion first.

---

## Validation Checkpoint — End of Week 1

The week is successful if the team can:

- create 1 real candidate
- configure themes and sensitive topics
- add 10–20 monitored sources
- ingest real RSS and YouTube content
- list collected content in UI
- inspect source sync logs

---

## Recommended Claude Code tasks
- validate repo structure
- refine API module plan
- review DB model coherence
- review connector architecture

## Recommended Codex tasks
- generate SQLAlchemy models
- generate Alembic migrations
- scaffold CRUD routers
- scaffold MUI pages and tables
- generate RSS/YouTube connector boilerplate

---

# Week 2 — Performance Engine + Argument Extraction + Narrative Pipeline

## Objective

By the end of Week 2, the team should be able to:

- analyze candidate-owned social performance
- extract arguments from content
- embed arguments
- cluster arguments
- generate first narratives

---

## Backend Scope

### 1. New tables
Implement and migrate:

- arguments
- argument_clusters
- argument_cluster_members
- narratives
- narrative_scores
- post_performance
- theme_performance
- format_performance
- performance_insights

### 2. Performance engine
Implement:
- calculate_post_performance
- aggregate_theme_performance
- aggregate_format_performance
- generate_performance_insights

### 3. AI pipeline base
Implement:
- content relevance pre-filter
- argument extraction service
- embedding generation service
- argument clustering service
- narrative inference service

### 4. Jobs
Implement:
- compute_content_embeddings
- assign_content_topics
- extract_arguments
- build_argument_clusters
- generate_narratives

---

## Frontend Scope

### 1. Performance pages
Build:
- performance overview
- top posts
- low-performing posts
- theme performance
- format performance
- performance insights

### 2. Narrative radar page
Build:
- narratives list
- narrative detail panel
- representative content section

---

## AI Scope

### 1. Activate first prompts
Use:
- narrative_detection
- narrative_cluster_summary

### 2. Output validation
Ensure:
- parseable outputs
- no schema drift
- prompt version captured

---

## Validation Checkpoint — End of Week 2

The week is successful if the team can:

- show best and worst posts for a candidate
- extract arguments from collected content
- cluster arguments
- generate 3–10 readable narratives
- display narratives in the UI
- verify prompts are versioned and logged

---

## Recommended Claude Code tasks
- refine argument extraction schema
- refine clustering workflow
- validate prompt contracts
- review performance aggregation logic

## Recommended Codex tasks
- generate argument models and services
- implement jobs for extraction and clustering
- generate performance endpoints
- scaffold performance dashboard screens

---

# Week 3 — Strategic Engine + Competitors + Recommendations

## Objective

By the end of Week 3, the team should be able to:

- connect narratives to candidate context
- score opportunities
- detect competitor dominance
- detect missed opportunities
- generate actionable recommendations

---

## Backend Scope

### 1. New tables
Implement and migrate:

- competitors
- allies
- competitor_activity
- competitor_alerts
- ally_activity
- ally_amplification_suggestions
- strategic_opportunities
- strategic_alerts
- missed_opportunities
- recommendations

### 2. Strategic engine
Implement:
- candidate relevance scoring
- opportunity score calculation
- risk score calculation
- priority index logic

### 3. Competitor and ally jobs
Implement:
- analyze_competitor_activity
- analyze_ally_activity
- detect_missed_opportunities

### 4. Recommendation engine
Implement:
- generate_strategic_opportunities
- generate_strategic_alerts
- generate_content_recommendations

---

## Frontend Scope

### 1. Strategic pages
Build:
- opportunities page
- strategic alerts page
- recommendations page
- competitor monitor page
- ally suggestions page
- missed opportunities page

### 2. Narrative prioritization indicators
Add:
- score chips
- urgency badges
- risk/opportunity indicators

---

## AI Scope

### 1. Activate prompts
Use:
- strategic_opportunity
- content_recommendation
- competitor_analysis
- ally_amplification
- missed_opportunity

### 2. Start admin prompt testing
Enable internal operators to:
- run prompt tests
- compare versions
- preview outputs

---

## Validation Checkpoint — End of Week 3

The week is successful if the team can:

- show competitor-related alerts
- show missed narratives
- generate recommendations linked to candidate strategy
- explain why a recommendation exists
- demonstrate narrative → opportunity → recommendation flow

---

## Recommended Claude Code tasks
- review scoring formulas
- review relevance model implementation
- review strategic output shape
- challenge weak recommendation logic

## Recommended Codex tasks
- generate strategy services
- generate competitor/allies routes and jobs
- generate recommendation routes and screens
- implement score calculations from spec

---

# Week 4 — Briefing, WhatsApp Delivery, Ops, Demo Readiness

## Objective

By the end of Week 4, the team should be able to:

- generate a daily briefing
- send it through WhatsApp
- inspect operational failures
- run a polished demo with one real candidate

---

## Backend Scope

### 1. New tables
Implement and migrate:

- briefings
- whatsapp_messages
- optional raw_payloads if not already added

### 2. Briefing service
Implement:
- build_daily_briefing
- briefing formatter
- briefing history retrieval

### 3. Delivery
Implement:
- send_daily_briefing
- send_alert_message
- messaging provider integration

### 4. Ops layer
Implement:
- failed jobs endpoint
- connector health endpoint
- recent job runs endpoint
- delivery failures endpoint

### 5. Admin controls
Implement:
- manual job trigger
- regenerate briefing
- rerun narrative generation
- rerun recommendations

---

## Frontend Scope

### 1. Briefing pages
Build:
- latest briefing
- briefing history
- briefing detail
- delivery status view

### 2. Ops pages
Build:
- connector health
- failed jobs
- recent sync logs
- prompt test/admin page

### 3. Demo polish
Improve:
- empty states
- dashboard hierarchy
- quick summary cards
- narrative urgency clarity

---

## AI Scope

### 1. Activate briefing prompt
Use:
- daily_briefing

### 2. Validate briefing quality
Check:
- executive clarity
- medium length
- useful prioritization
- no repetitive phrasing
- no vague recommendation wording

---

## Validation Checkpoint — End of Week 4

The MVP is successful if the team can:

- configure a real candidate
- monitor real sources
- ingest real content
- analyze performance
- detect narratives
- detect strategic opportunities
- generate recommendations
- generate and send a briefing
- demonstrate the full flow coherently

This is enough for:
- pilot client demos
- early sales conversations
- first paid tests

---

# Daily Work Pattern Recommendation

Each build day should roughly follow:

### Morning
- review backlog and blockers
- use Claude Code for planning/refinement
- generate implementation tasks

### Midday
- use Codex for code generation
- integrate backend/frontend modules
- run jobs locally

### Afternoon
- human review
- fix drift
- test with real data
- update docs if needed

This reduces accumulation of AI-generated entropy.

---

# Definition of Done per Module

A module is only “done” when:

1. route/service/job exists
2. schema is migrated
3. output appears in UI or logs
4. candidate scoping is correct
5. basic failure path is handled
6. output can be explained by a human

Do not mark modules done just because code was generated.

---

# Hard Guardrails During Build

### 1. No undocumented tables
Every new table must exist in the schema docs.

### 2. No prompt hardcoding in random files
Prompt references must stay centralized.

### 3. No frontend-only business logic
Core scoring and intelligence must live in backend services.

### 4. No silent schema changes
All model changes require migrations.

### 5. No mixing of candidate contexts
Candidate isolation is mandatory.

### 6. No “we will clean this later” sprawl
If AI generates junk patterns, stop and normalize early.

---

# Recommended First Vertical Slice

If the team wants the most motivating first slice, implement this path first:

1. candidate setup
2. monitored source creation
3. RSS + YouTube sync
4. content list page
5. argument extraction for synced content
6. first narratives page
7. first simple recommendation

This produces visible value early.

---

# Recommended Pilot Setup

Before demoing externally, configure:

- 1 real candidate
- 3 key competitors
- 3 relevant allies
- 20–50 monitored sources
- 1–2 weeks of collected content if possible

This makes outputs feel much more credible.

---

# Final Principle

The MVP should not try to look complete.

It should try to be:
- coherent
- operational
- strategically useful
- reliable enough to sell

A smaller working intelligence engine is far more valuable than a larger unstable product.
