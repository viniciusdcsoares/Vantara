
# 12_bootstrap_repo_tasks.md

## Purpose

Define the exact sequence of steps to bootstrap the repository and begin implementation of the platform using an **AI coding‑first workflow**.

This document converts the architecture into a **practical execution plan**.

Goals:

- start development immediately
- prevent architectural drift during early commits
- ensure AI tools generate code in the correct structure
- reduce ambiguity for developers and coding agents
- reach a **demoable MVP as quickly as possible**

This plan assumes:

- Claude Code used for planning/refinement
- Codex used for code generation
- Human developers reviewing and integrating

---

# Phase 0 — Repository Creation

Create the main repository.

Recommended name:

```
vantara-intelligence-platform
```

or

```
paradoxa-narrative-engine
```

Inside the repo initialize:

```
/docs
/prompts
/backend
/frontend
/scripts
/tests
```

Then move all documentation files into `/docs`.

Final structure:

```
/docs
/prompts
/backend
/frontend
/scripts
/tests
```

---

# Phase 1 — Backend Foundation

Enter the backend directory.

```
/backend
```

Initialize Python project.

Recommended stack:

- Python 3.11+
- FastAPI
- SQLAlchemy or SQLModel
- Alembic
- Redis
- RQ

Install dependencies:

```
fastapi
uvicorn
pydantic
sqlalchemy
alembic
redis
rq
python-dotenv
httpx
openai
```

Create structure:

```
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    jobs/
    connectors/
    repositories/
    utils/
    prompts/
    ops/
  alembic/
  tests/
  main.py
```

---

# Phase 2 — Core Infrastructure

Implement foundational modules.

## Settings

File:

```
app/core/settings.py
```

Responsible for:

- environment variables
- API keys
- database URL
- redis URL

Example variables:

```
DATABASE_URL
REDIS_URL
OPENAI_API_KEY
APIFY_TOKEN
TWILIO_TOKEN
```

---

## Database

Create:

```
app/db/session.py
app/db/base.py
```

Set up:

- SQLAlchemy engine
- session factory
- metadata base

---

## Logging

Create:

```
app/core/logging.py
```

Provide structured logs for:

- API calls
- jobs
- connectors

---

# Phase 3 — First Database Models

Create essential models first.

### Candidate

```
candidates
```

Fields:

- id
- name
- party
- state
- office
- ideological_position
- communication_tone
- created_at

---

### Monitored Sources

```
monitored_sources
```

Fields:

- id
- platform
- source_type
- external_identifier
- url
- owner_type
- candidate_id

---

### Content Items

```
content_items
```

Fields:

- id
- platform
- source_id
- author_name
- text_content
- published_at
- url

---

### Content Metrics

```
content_metrics
```

Fields:

- content_id
- views
- likes
- comments
- shares
- collected_at

---

Run migration:

```
alembic revision --autogenerate
alembic upgrade head
```

---

# Phase 4 — Basic API

Implement minimal API.

Start with:

```
GET /health
GET /candidates
POST /candidates
GET /content-items
```

Router structure:

```
app/api/candidates.py
app/api/content_items.py
```

Keep routes thin.

All logic goes in services.

---

# Phase 5 — Source Collection

Implement connectors.

Start with easiest sources first.

### RSS Connector

File:

```
connectors/rss_connector.py
```

Capabilities:

- fetch feed
- parse entries
- normalize to content_items

---

### YouTube Connector

File:

```
connectors/youtube_connector.py
```

Capabilities:

- fetch recent videos
- normalize metadata
- store metrics

---

### Apify Connectors

Later add:

```
connectors/apify_instagram.py
connectors/apify_tiktok.py
connectors/apify_x.py
```

---

# Phase 6 — First Jobs

Create worker queue using Redis + RQ.

Jobs folder:

```
jobs/
```

Implement first jobs.

### sync_single_source

```
jobs/collection.py
```

Steps:

1. load source
2. call connector
3. normalize content
4. store items
5. record sync log

---

### normalize_new_content

```
jobs/normalization.py
```

Clean text and metadata.

---

### compute_content_embeddings

```
jobs/embeddings.py
```

Generate embeddings using OpenAI.

---

# Phase 7 — Performance Engine

Create metrics analysis.

File:

```
services/performance_service.py
```

Compute:

- engagement_count
- engagement_rate
- velocity_score

Store in:

```
post_performance
```

---

# Phase 8 — Narrative Engine

Implement narrative pipeline.

Steps:

1. topic assignment
2. embedding clustering
3. narrative creation
4. narrative summarization

Files:

```
services/narrative_service.py
jobs/narratives.py
```

Tables:

```
narratives
content_narrative_edges
```

---

# Phase 9 — Strategy Engine

Create intelligence layer.

File:

```
services/strategy_service.py
```

Responsibilities:

- detect opportunities
- detect threats
- analyze competitor narratives

Output tables:

```
strategic_opportunities
strategic_alerts
```

---

# Phase 10 — Recommendation Engine

Generate actionable outputs.

File:

```
services/recommendation_service.py
```

Outputs:

```
content_recommendations
```

Example recommendation:

- topic
- platform
- format
- reasoning

---

# Phase 11 — Daily Briefing

Implement briefing generation.

File:

```
services/briefing_service.py
```

Sections:

- top narratives
- opportunities
- competitor alerts
- performance insight
- recommended actions

Store:

```
daily_briefings
```

---

# Phase 12 — Messaging

Add delivery.

Example provider:

Twilio WhatsApp API.

File:

```
jobs/delivery.py
```

Function:

```
send_daily_briefing()
```

---

# Phase 13 — Frontend Bootstrap

Initialize frontend.

Recommended stack:

- Next.js
- React
- MUI

Structure:

```
frontend/
  src/
    app/
    components/
    features/
    services/
    theme/
```

---

# Phase 14 — First Dashboard Screens

Build minimal screens.

### Candidate Overview

Displays:

- basic profile
- latest briefing
- quick metrics

---

### Content Performance

Charts:

- top posts
- engagement trends

---

### Narrative Radar

List:

- active narratives
- growth rate

---

### Recommendations

List:

- suggested posts
- reasoning

---

# Phase 15 — Admin Tools

Add internal admin screens.

Capabilities:

- trigger jobs
- edit prompts
- view connector health
- regenerate briefings

---

# Phase 16 — Demo Readiness

Before presenting MVP ensure:

- at least one candidate configured
- 5–10 monitored sources
- at least 100 content items collected
- narratives generated
- recommendations generated
- briefing generated

This allows full system demonstration.

---

# AI Coding Workflow

Recommended sequence per feature.

1. Claude Code plans module
2. Codex generates code
3. developer reviews
4. tests executed
5. commit merged

Never merge AI code without review.

---

# MVP Success Criteria

The MVP is successful when the platform can:

- ingest social content
- analyze performance
- detect narratives
- generate strategy insights
- produce recommendations
- send a daily briefing

If these work reliably, the product is already valuable.
