# System Architecture — Political Intelligence Platform

## Architecture Goal

The architecture must support:

1. fast MVP delivery
2. manageable operations with a small team
3. narrative intelligence generation
4. social performance analysis
5. dashboard and WhatsApp delivery

The architecture should be simple, monolithic, and job-oriented in the beginning.

---

## Core Principle

The system should be:

- batch-first
- dashboard-first
- WhatsApp-first
- AI-assisted, not AI-chaotic
- operationally simple

Do not start with microservices.

---

## High-Level Flow

```text
Data Sources
    ↓
Ingestion Workers
    ↓
Normalization Layer
    ↓
PostgreSQL + pgvector
    ↓
Narrative Engine
    ↓
Strategic Engine
    ↓
Recommendation Engine
    ↓
Delivery Layer
  ├ Dashboard
  └ WhatsApp / Telegram
```

---

## Recommended Stack

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy or SQLModel
- Alembic

### Database
- PostgreSQL
- pgvector

### Workers and jobs
- Redis
- RQ

### Front-end
- Next.js
- MUI
- charts library such as Recharts

### Messaging
- Twilio WhatsApp API or Z-API

### Hosting
- Railway or Render initially
- AWS later if needed

### Scraping / collection
- YouTube Data API
- RSS parser
- Apify for Instagram, TikTok, X when needed
- Playwright only as a fallback

### LLM provider
- OpenAI API
- optional second provider later

---

## Logical Services

### 1. Ingestion Service

Responsibilities:
- pull content from monitored sources
- collect metadata
- collect available engagement metrics
- store raw payloads and normalized records

Input sources:
- candidate-owned accounts
- competitor accounts
- ally accounts
- news feeds
- political influencers
- public monitored channels

Frequency:
- RSS: 15 to 30 minutes
- YouTube: 1 to 3 hours
- Instagram / TikTok / X: 1 to 4 hours depending on stability and cost

### 2. Normalization Service

Responsibilities:
- unify field names
- clean text
- normalize metrics
- calculate derived indicators

Derived metrics:
- engagement_count
- engagement_rate
- velocity_score
- recency_score

### 3. Narrative Engine

Responsibilities:
- assign topics
- cluster related content
- summarize cluster meaning
- generate narrative records

Pipeline:
```text
content
→ embedding
→ grouping / clustering
→ summarization
→ narrative record
```

### 4. Strategic Engine

Responsibilities:
- compare narratives against candidate profile
- evaluate opportunity and risk
- determine recommended strategic positioning
- consider competitors and allies

Outputs:
- strategic opportunities
- strategic alerts
- missed-opportunity signals

### 5. Social Performance Engine

Responsibilities:
- analyze candidate-owned accounts
- identify top and low performers
- identify winning themes
- identify winning formats
- connect external narrative trends to internal performance data

### 6. Recommendation Engine

Responsibilities:
- generate content directions
- choose recommended format
- justify recommendation
- set urgency

### 7. Competitor Monitor

Responsibilities:
- track adversary content
- detect when a competitor dominates a narrative
- classify risk
- suggest response or strategic silence

### 8. Ally Amplification Engine

Responsibilities:
- track allied content
- suggest amplification when aligned with strategy
- identify shared messaging opportunities

### 9. Briefing Builder

Responsibilities:
- compile all relevant outputs into a clear daily briefing
- prepare delivery payloads for dashboard and WhatsApp

---

## Delivery Architecture

### Dashboard

The dashboard is the command center.

Primary sections:
- overview
- narrative radar
- social media performance
- competitor monitor
- ally opportunities
- daily recommendations
- missed narratives

### WhatsApp / Telegram

The messaging layer delivers:
- daily briefing
- urgent alerts
- competitor alerts
- missed-topic notifications
- recommended posting direction

This should be the highest-frequency touchpoint.

---

## Processing Strategy

Prefer batch jobs over real-time processing.

Suggested schedules:

### Content ingestion
- RSS: every 15–30 minutes
- YouTube: every 1–3 hours
- Instagram / TikTok / X: every 1–4 hours

### Narrative recalculation
- every 3 hours
- or 2 to 4 times per day in early stages

### Recommendation generation
- after narrative updates
- and once for the daily briefing cycle

### Daily briefing
- once per morning

---

## Scaling Strategy

### Phase 1 — MVP
- single API app
- single worker pool
- single Postgres database
- single front-end app

### Phase 2 — Early growth
- separate workers by workload
- better scheduling
- object storage for raw payloads
- improved monitoring

### Phase 3 — Larger operation
- platform-specific ingestion workers
- more robust observability
- caching
- heavier job isolation

---

## Infrastructure Cost Logic

Main cost centers:
1. scraping and collection
2. LLM usage
3. job reprocessing

Control rules:
- do not monitor too many sources per client initially
- use embeddings and heuristics before LLM calls
- cache outputs aggressively
- do not recalculate everything too often

---

## Operational Risks

### Scraping instability
Mitigation:
- prioritize YouTube and RSS first
- treat Instagram / TikTok / X as complementary layers

### Generic AI outputs
Mitigation:
- strong candidate profile
- tightly scoped prompts
- store reusable strategic context

### Dashboard fatigue
Mitigation:
- keep WhatsApp as the primary operational surface
- make dashboard insight-heavy, not metric-heavy

### Over-customization per client
Mitigation:
- standardized onboarding schema
- configurable fields, not bespoke logic everywhere
