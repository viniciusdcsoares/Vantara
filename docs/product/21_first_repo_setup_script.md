# 21_first_repo_setup_script.md

## Purpose

Provide the exact initial setup steps to bootstrap the repository with minimal friction.

This document is meant to be executed by developers and used by coding agents as the canonical startup sequence for the project.

It covers:

- repository creation
- folder structure
- backend initialization
- frontend initialization
- environment files
- initial dependencies
- database and Redis setup
- first migrations
- first workers
- optional Docker setup

The goal is to get the team from zero to a runnable local development environment as fast as possible.

---

# 1. Repository Creation

Recommended repository name:

```text
vantara-intelligence-platform
```

Alternative (not for real use now):

```text
paradoxa-narrative-engine
```

Create the root folders:

```bash
mkdir -p vantara-intelligence-platform/{docs,prompts,backend,frontend,scripts,tests}
cd vantara-intelligence-platform
```

Move all existing markdown documentation into:

```text
/docs
```

---

# 2. Backend Initialization

## 2.1 Create Python environment

Recommended Python version:

```text
3.11+
```

Commands:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

## 2.2 Install backend dependencies

Recommended initial dependencies:

```bash
pip install fastapi uvicorn sqlalchemy alembic pydantic python-dotenv redis rq httpx psycopg[binary] pgvector openai feedparser
```

Optional useful packages:

```bash
pip install pytest pytest-asyncio black isort ruff
```

Freeze dependencies:

```bash
pip freeze > requirements.txt
```

---

# 3. Backend Folder Structure

Create the backend structure:

```bash
mkdir -p app/{api,core,db,models,schemas,services,jobs,connectors,repositories,utils,prompts,ops}
mkdir -p tests
touch app/main.py
```

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
  /tests
  requirements.txt
```

---

# 4. Environment Configuration

Create `.env.example` in `/backend`:

```env
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/vantara
REDIS_URL=redis://localhost:6379/0

OPENAI_API_KEY=
APIFY_TOKEN=
YOUTUBE_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=

JWT_SECRET=
```

Create `.env` from it:

```bash
cp .env.example .env
```

Add to `.gitignore`:

```text
.env
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
dist/
build/
```

---

# 5. Minimal Backend App

Create `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Vantara Intelligence Platform API", version="0.1.0")

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
```

Run locally:

```bash
uvicorn app.main:app --reload
```

Expected endpoint:

```text
GET http://localhost:8000/api/v1/health
```

---

# 6. Database Setup

## 6.1 Local PostgreSQL

If using local Postgres, create database:

```sql
CREATE DATABASE vantara;
```

Enable pgvector in the database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 6.2 Alembic init

Inside `/backend`:

```bash
alembic init alembic
```

This creates:

```text
/backend/alembic
/backend/alembic.ini
```

Configure `alembic.ini` and env settings to use `DATABASE_URL`.

---

# 7. Initial Models and Migrations

Create initial model files for:

- candidates
- monitored_sources
- actors
- content_items
- content_metrics
- source_sync_logs

After models exist, generate first migration:

```bash
alembic revision --autogenerate -m "initial core tables"
alembic upgrade head
```

---

# 8. Redis and Worker Setup

## 8.1 Local Redis

If installed locally:

```bash
redis-server
```

Or via Docker:

```bash
docker run -p 6379:6379 redis:7
```

## 8.2 RQ worker bootstrap

Create `app/jobs/worker.py`:

```python
from redis import Redis
from rq import Worker, Queue, Connection
import os

listen = ["default", "ingestion", "processing", "briefing"]
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        worker.work()
```

Run worker:

```bash
python app/jobs/worker.py
```

---

# 9. First Backend Modules to Create

Priority order for initial files:

```text
app/core/settings.py
app/core/logging.py
app/db/base.py
app/db/session.py
app/models/candidate.py
app/models/monitored_source.py
app/models/actor.py
app/models/content_item.py
app/models/content_metric.py
app/models/source_sync_log.py
app/schemas/candidate.py
app/api/candidates.py
app/api/content_items.py
app/api/monitored_sources.py
app/connectors/rss_connector.py
app/connectors/youtube_connector.py
app/jobs/collection.py
```

---

# 10. Frontend Initialization

## 10.1 Create Next.js app

From repo root:

```bash
cd frontend
npx create-next-app@latest . --ts --eslint --src-dir --app --import-alias "@/*"
```

## 10.2 Install frontend dependencies

Recommended:

```bash
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled recharts axios
```

Optional:

```bash
npm install @tanstack/react-query zod
```

---

# 11. Frontend Folder Structure

Inside `/frontend/src`, organize:

```text
/src
  /app
  /components
  /features
  /services
  /types
  /theme
  /lib
```

Suggested first files:

```text
src/theme/theme.ts
src/components/PageShell.tsx
src/components/SectionCard.tsx
src/components/MetricCard.tsx
src/components/DataTableShell.tsx
src/services/api.ts
src/app/page.tsx
src/app/candidates/page.tsx
src/app/content/page.tsx
```

---

# 12. Basic Frontend Environment

Create `.env.local` in `/frontend`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Add to `.gitignore`:

```text
.env.local
.next/
node_modules/
```

---

# 13. First Frontend Screens

Build these first:

1. Home / overview
2. Candidates list
3. Candidate detail
4. Monitored sources
5. Content list

These are enough to verify backend integration early.

---

# 14. Prompt Folder Setup

At the repo root, create `/prompts` files:

```text
/prompts
  narrative_detection.md
  narrative_cluster_summary.md
  strategic_opportunity.md
  content_recommendation.md
  competitor_analysis.md
  ally_amplification.md
  missed_opportunity.md
  daily_briefing.md
```

Initially, these can contain placeholders with:

- purpose
- input contract
- output contract
- version

---

# 15. Scripts Folder Setup

Create helper scripts in `/scripts`:

```text
/scripts
  start_backend.sh
  start_frontend.sh
  start_worker.sh
  run_migrations.sh
```

Example `start_backend.sh`:

```bash
#!/usr/bin/env bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Example `start_frontend.sh`:

```bash
#!/usr/bin/env bash
cd frontend
npm run dev
```

Example `start_worker.sh`:

```bash
#!/usr/bin/env bash
cd backend
source .venv/bin/activate
python app/jobs/worker.py
```

---

# 16. Optional Docker Compose Setup

If the team wants quick infra bootstrapping, create `docker-compose.yml` at repo root:

```yaml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vantara
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

Run:

```bash
docker compose up -d
```

This gives local Postgres + pgvector + Redis.

---

# 17. First AI Coding Tasks

Best initial tasks for Codex:

1. generate initial SQLAlchemy models
2. generate Pydantic schemas
3. scaffold candidate CRUD routes
4. scaffold monitored source CRUD routes
5. scaffold content list route
6. scaffold RSS connector
7. scaffold YouTube connector
8. scaffold basic MUI pages

Best initial tasks for Claude Code:

1. validate repo structure
2. review model coherence
3. review first migration
4. review connector design
5. review route organization

---

# 18. First Validation Checklist

Before moving beyond bootstrap, confirm:

- backend starts
- frontend starts
- Redis starts
- Postgres starts
- health endpoint works
- first migration runs
- one candidate can be inserted
- one monitored source can be inserted
- one content item can be listed
- worker starts without crashing

If these are true, the repo bootstrap is successful.

---

# 19. Recommended First Commit Sequence

Suggested commit order:

1. `chore: initialize repo structure`
2. `chore: bootstrap backend and frontend apps`
3. `feat: add core database setup and initial models`
4. `feat: add candidate and monitored source crud`
5. `feat: add rss and youtube connectors`
6. `feat: add collection worker scaffold`
7. `feat: add initial dashboard pages`

This produces a clean history and helps AI agents understand the progression.

---

# 20. Final Principle

The purpose of bootstrap is not to make the product complete.

It is to create the smallest runnable system with:

- stable structure
- correct conventions
- first data flow
- first UI flow
- first worker flow

Once that exists, the team can move into the MVP build sequence with much lower risk.
