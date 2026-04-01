# Engineering Backlog MVP — Political Intelligence Platform

## Purpose

This document translates the product vision into an executable MVP backlog for an AI coding-first workflow.

It is designed to support:
- human developers
- coding agents
- prompt-driven implementation
- sprint planning
- module-by-module delivery

The MVP goal is to produce a sellable system that can:
1. collect relevant political and social data
2. analyze candidate-owned social performance
3. detect narratives
4. generate strategic recommendations
5. deliver a daily briefing

---

## Delivery Philosophy

This MVP should be built in the fastest viable order.

Priority rule:
- first make data exist
- then make data readable
- then make data strategic
- then make data deliverable

Do not build advanced abstractions early.

---

## MVP Scope Lock

The first sellable version should include:

### Candidate setup
- candidate profile
- themes
- sensitive topics
- audiences
- allies
- competitors
- owned accounts
- monitored sources

### Data ingestion
- YouTube
- RSS / news
- Instagram
- TikTok
- X / Twitter, if feasible
- platform metrics collection

### Intelligence
- topic tagging
- narrative grouping
- strategic opportunity generation
- competitor alerts
- ally amplification suggestions
- missed opportunity detection

### Social analysis
- best-performing posts
- low-performing posts
- theme performance
- format performance
- platform performance insights

### Delivery
- dashboard
- daily briefing
- WhatsApp sending

Anything beyond this should be treated as post-MVP.

---

## Sprint Structure

Recommended sprint sequence:

1. Sprint 0 — repository, conventions, infra foundation
2. Sprint 1 — candidate setup + basic data model + admin CRUD
3. Sprint 2 — ingestion pipelines + normalized content storage
4. Sprint 3 — social performance analytics
5. Sprint 4 — narrative engine
6. Sprint 5 — strategic engine + recommendations
7. Sprint 6 — competitor, allies, missed opportunities
8. Sprint 7 — daily briefing + WhatsApp delivery
9. Sprint 8 — polish, internal QA, demo mode

The team can compress this into 4 calendar weeks if needed by running some tasks in parallel.

---

## Sprint 0 — Project Foundation

### Goal
Set the project up so AI-generated code can be produced consistently.

### Tasks

#### Repo structure
- create `/backend`
- create `/frontend`
- create `/docs`
- create `/prompts`
- create `/scripts`
- create `/tests`

#### Coding standards
- define naming conventions
- define folder structure
- define backend module pattern
- define front-end page/component pattern
- define migration workflow
- define prompt versioning rules

#### Core tooling
- initialize FastAPI project
- initialize Next.js project
- configure MUI theme base
- configure PostgreSQL connection
- configure Redis
- configure RQ worker
- configure Alembic
- configure env management
- add linting and formatting

#### Minimal CI
- backend lint
- frontend lint
- migration validation
- test execution

### Definition of done
- projects boot locally
- worker runs
- DB migrations run
- theme compiles
- repo structure is stable

---

## Sprint 1 — Candidate Setup and Admin Foundation

### Goal
Make candidate strategy configurable in the system.

### Backend tasks

#### Models
- candidates
- candidate_themes
- candidate_sensitive_topics
- candidate_audiences
- allies
- competitors
- social_accounts
- monitored_sources

#### Schemas
- create request/response schemas for all entities

#### CRUD endpoints
- create candidate
- update candidate
- get candidate detail
- list candidates
- CRUD for themes
- CRUD for sensitive topics
- CRUD for audiences
- CRUD for allies
- CRUD for competitors
- CRUD for social accounts
- CRUD for monitored sources

#### Validation rules
- enforce candidate ownership relation
- validate platform types
- validate priority ranges
- validate monitored source categories

### Front-end tasks

#### Pages
- candidates list page
- candidate detail page
- candidate form page

#### Candidate detail sections
- identity
- campaign objective
- themes
- sensitive topics
- audiences
- allies
- competitors
- owned accounts
- monitored sources

### AI usage tasks
- use AI to scaffold SQLAlchemy models
- use AI to scaffold Pydantic schemas
- use AI to scaffold CRUD routes
- use AI to scaffold MUI forms and tables

### Definition of done
- candidate can be fully configured in UI
- data persists correctly
- forms are usable
- all main setup entities can be edited

---

## Sprint 2 — Ingestion Pipelines and Normalized Content Storage

### Goal
Collect and store useful content from monitored sources.

### Backend tasks

#### New models
- source_sync_logs
- content_items
- content_metrics

#### Normalized content schema
Every content source should map into:
- source_id
- candidate_id nullable
- platform
- external_id
- author_name
- author_handle
- title
- text_content
- content_type
- url
- published_at
- fetched_at
- raw_payload_ref

#### Ingestion modules
- YouTube collector
- RSS collector
- Instagram collector
- TikTok collector
- X collector if feasible
- manual sync trigger

#### Jobs
- sync_youtube_sources
- sync_rss_sources
- sync_instagram_sources
- sync_tiktok_sources
- sync_x_sources
- sync_single_source

#### Logging
- write collection status to source_sync_logs
- store item counts
- store errors

### Front-end tasks
- content items table
- filters by platform
- filters by source
- filters by time range
- sync status view

### AI usage tasks
- generate API clients
- generate normalization functions
- generate parser helpers
- generate sync job boilerplates

### Definition of done
- system can ingest from at least YouTube + RSS
- content is visible in dashboard
- sync status is inspectable
- failed sources are visible

---

## Sprint 3 — Social Media Performance Analytics

### Goal
Turn owned social content into actionable performance insights.

### Backend tasks

#### New models
- post_performance
- theme_performance
- format_performance
- performance_insights

#### Derived metrics pipeline
For each owned post calculate:
- engagement_count
- engagement_rate
- velocity_score
- performance_band

#### Theme classification
- rule-based initial topic mapping
- optional embedding-based refinement later

#### Aggregations
- aggregate by theme
- aggregate by format
- aggregate by platform
- aggregate by time window

#### Insight generation
Generate insights such as:
- top-performing theme
- weakest-performing theme
- top-performing format
- weakest-performing format
- high-fit narrative area

### Front-end tasks

#### Pages
- performance overview
- top-performing posts
- low-performing posts
- theme performance view
- format performance view

#### Dashboard cards
- total posts
- total views
- average engagement
- follower growth if available

### Definition of done
- candidate-owned content performance can be ranked
- best and worst content is visible
- themes and formats are comparable
- basic human-readable insights exist

---

## Sprint 4 — Narrative Engine

### Goal
Detect useful narratives from external monitored content.

### Backend tasks

#### New models
- content_embeddings
- content_topics
- narratives
- narrative_clusters

#### Pipeline steps
1. assign topic tags
2. generate embeddings
3. group similar content
4. summarize cluster meaning
5. store narrative records

#### Jobs
- compute_content_embeddings
- assign_content_topics
- build_narrative_clusters
- generate_narratives

#### Narrative output fields
- topic_name
- narrative_summary
- dominant_position
- volume_score
- growth_rate
- key_actors
- opportunity_score
- risk_score

### Front-end tasks
- narrative radar page
- narrative list table
- narrative detail drawer/modal
- source references view

### AI usage tasks
- prompt for topic extraction
- prompt for cluster summary
- prompt for narrative label and interpretation

### Definition of done
- the system produces readable narrative records
- narratives are tied to candidate context
- narrative list is visible in UI
- cluster/source traceability exists

---

## Sprint 5 — Strategic Engine and Recommendations

### Goal
Translate narratives into candidate-specific strategy.

### Backend tasks

#### New models
- strategic_opportunities
- strategic_alerts
- content_recommendations

#### Strategic reasoning inputs
- narrative records
- candidate themes
- sensitive topics
- target audiences
- ally and competitor context
- social performance data

#### Outputs
- opportunity level
- urgency
- rationale
- recommended positioning
- content direction
- recommended platform
- recommended format

#### Jobs
- generate_strategic_opportunities
- generate_content_recommendations
- generate_strategic_alerts

### Front-end tasks
- opportunities page
- recommendations page
- recommendation cards
- rationale viewer

### AI usage tasks
- prompt for opportunity reasoning
- prompt for content recommendation
- prompt for strategic alert generation

### Definition of done
- narratives are translated into useful recommendations
- recommendations mention why they matter
- recommendations connect with candidate strategy
- dashboard shows actionable output, not just analysis

---

## Sprint 6 — Competitors, Allies, and Missed Opportunities

### Goal
Add the most commercially powerful strategic layers.

### Backend tasks

#### New models
- competitor_activity
- competitor_alerts
- ally_activity
- ally_amplification_suggestions
- missed_opportunities

#### Competitor logic
- detect competitor content relevance
- classify risk level
- detect narrative dominance
- suggest response or silence

#### Ally logic
- detect relevant allied content
- suggest amplification when aligned

#### Missed opportunity logic
- compare rising narratives vs candidate posting behavior
- flag relevant topics not addressed recently

#### Jobs
- analyze_competitor_activity
- analyze_ally_activity
- detect_missed_opportunities

### Front-end tasks
- competitor monitor page
- ally opportunities page
- missed opportunities page

### Definition of done
- main competitors can be monitored
- risk alerts are generated
- allied amplification opportunities appear
- missed narrative topics are visible

---

## Sprint 7 — Daily Briefing and WhatsApp Delivery

### Goal
Deliver the strategic value in the candidate's daily workflow.

### Backend tasks

#### New models
- daily_briefings
- whatsapp_messages

#### Briefing builder
Compile:
- top narratives
- top opportunities
- top competitor alert
- missed opportunity
- one social performance insight
- one or more content recommendations

#### Message builder
- text formatting for WhatsApp
- character control
- markdown-lite formatting if useful
- retry logic
- delivery status tracking

#### Jobs
- build_daily_briefing
- send_daily_briefing
- send_alert_message

### Front-end tasks
- briefing history page
- briefing preview page
- message status page

### AI usage tasks
- prompt for daily briefing compilation
- prompt for concise message formatting

### Definition of done
- a daily briefing can be generated and reviewed
- the system can send via WhatsApp
- delivery history is recorded
- the briefing is readable and useful

---

## Sprint 8 — QA, Demo Mode, and Commercial Readiness

### Goal
Make the product usable for pilots and demos.

### Tasks

#### QA
- fix broken ingestion flows
- verify metric calculations
- verify candidate setup consistency
- verify narrative freshness
- verify recommendation quality
- verify briefing stability

#### Demo mode
- preload one demo candidate
- preload sample sources
- preload sample narratives and recommendations
- create a clean demo journey

#### UX polish
- improve empty states
- improve table readability
- improve card hierarchy
- improve mobile/responsive baseline for key views

#### Internal observability
- failed jobs view
- failed source sync view
- briefing build failures
- WhatsApp send failures

### Definition of done
- internal team can demo the full flow
- product feels coherent
- core pages are understandable
- a pilot client could use it

---

## Parallel Work Recommendations

To move fast, these can run in parallel:

### Track A — Backend foundation
- models
- endpoints
- jobs
- processing pipelines

### Track B — Front-end shell
- layout
- tables
- candidate setup
- dashboard pages

### Track C — Prompt library
- narrative prompts
- strategy prompts
- recommendation prompts
- briefing prompts

### Track D — Connectors
- YouTube
- RSS
- Instagram
- TikTok
- X if feasible

---

## API Backlog

These are the main endpoint groups the MVP should expose.

### Candidate setup
- GET /candidates
- POST /candidates
- GET /candidates/{id}
- PATCH /candidates/{id}

### Candidate related entities
- /candidates/{id}/themes
- /candidates/{id}/sensitive-topics
- /candidates/{id}/audiences
- /candidates/{id}/allies
- /candidates/{id}/competitors
- /candidates/{id}/social-accounts
- /candidates/{id}/monitored-sources

### Content and sync
- GET /content-items
- GET /content-items/{id}
- POST /sources/{id}/sync
- GET /source-sync-logs

### Performance
- GET /candidates/{id}/performance/overview
- GET /candidates/{id}/performance/top-posts
- GET /candidates/{id}/performance/low-posts
- GET /candidates/{id}/performance/themes
- GET /candidates/{id}/performance/formats
- GET /candidates/{id}/performance/insights

### Narratives
- GET /candidates/{id}/narratives
- GET /narratives/{id}

### Strategy
- GET /candidates/{id}/opportunities
- GET /candidates/{id}/alerts
- GET /candidates/{id}/recommendations
- GET /candidates/{id}/missed-opportunities

### Competitors and allies
- GET /candidates/{id}/competitor-alerts
- GET /candidates/{id}/ally-suggestions

### Briefings
- GET /candidates/{id}/briefings
- GET /briefings/{id}
- POST /briefings/{id}/send

---

## Worker and Cron Backlog

### Frequent jobs
- sync_rss_sources
- sync_youtube_sources
- sync_instagram_sources
- sync_tiktok_sources
- sync_x_sources

### Processing jobs
- normalize_new_content
- compute_content_embeddings
- assign_content_topics
- calculate_post_performance
- aggregate_theme_performance
- aggregate_format_performance
- build_narrative_clusters
- generate_narratives
- generate_strategic_opportunities
- generate_content_recommendations
- analyze_competitor_activity
- analyze_ally_activity
- detect_missed_opportunities

### Delivery jobs
- build_daily_briefing
- send_daily_briefing
- send_alert_message

### Suggested cron cadence
- ingestion: every 15 min to 4h depending on source
- performance aggregation: every 6h
- narratives: every 3h
- strategic jobs: every 3h or after narratives
- briefing: once every morning
- alerts: event-driven or every few hours

---

## Prompt Library Backlog

Create a `/prompts` folder with:

- narrative_detection.md
- narrative_cluster_summary.md
- strategic_opportunity.md
- content_recommendation.md
- competitor_risk.md
- ally_amplification.md
- missed_opportunity.md
- daily_briefing.md

Each prompt file should contain:
- purpose
- expected input
- expected output schema
- version
- known caveats

---

## AI Coding-First Execution Rules

### Rule 1
Every module must have a doc before AI generates code.

### Rule 2
Use AI to generate first drafts, not final truth.

### Rule 3
Humans must normalize code style after generation.

### Rule 4
Do not allow three different patterns for routes, models, or jobs.

### Rule 5
Prefer complete vertical slices over horizontal overengineering.

Example:
candidate setup end-to-end is better than half-building five engines at once.

---

## Practical MVP Order for a 4-Week Build

If time is compressed into 4 weeks:

### Week 1
- Sprint 0
- Sprint 1
- start Sprint 2

### Week 2
- finish Sprint 2
- Sprint 3
- start Sprint 4

### Week 3
- finish Sprint 4
- Sprint 5
- start Sprint 6

### Week 4
- finish Sprint 6
- Sprint 7
- critical Sprint 8 items

---

## Final Definition of MVP Success

The MVP is successful if the team can:

1. configure a real candidate
2. monitor real sources
3. ingest and display real content
4. show what performs well in the candidate's own channels
5. detect useful narratives
6. generate recommendations that make strategic sense
7. build and send a daily briefing
8. demo the full flow coherently to a pilot client

That is enough to start selling and iterating.
