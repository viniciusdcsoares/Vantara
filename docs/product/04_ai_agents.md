# AI Agents and AI Coding-First Development Model

## Purpose

This document defines:

1. the minimal AI agent structure for the product
2. how AI should be used inside the platform
3. how AI should be used to develop the codebase itself

The goal is not to create a chaotic agent swarm. The goal is to use AI as leverage.

---

## Product-Side AI Agents

The recommended MVP agent structure is intentionally small.

### 1. Narrative Radar Agent

Purpose:
- read recent collected content
- identify narrative clusters
- summarize what is rising

Inputs:
- normalized content
- topic assignments
- engagement and velocity signals

Outputs:
- narrative summaries
- dominant angle
- relevant actors
- growth indication

This agent should run as a scheduled job.

---

### 2. Strategic Reasoning Agent

Purpose:
- compare detected narratives against the candidate profile
- evaluate fit, risk, and opportunity
- determine whether a candidate should react, reinforce, ignore, or delegate

Inputs:
- narratives
- candidate themes
- sensitive topics
- target audiences
- competitor and ally context

Outputs:
- strategic opportunities
- strategic alerts
- missed narrative warnings

This is the heart of the product.

---

### 3. Recommendation Agent

Purpose:
- generate recommended content direction
- select format and platform
- justify recommendation

Inputs:
- current narrative state
- strategic outputs
- social performance data

Outputs:
- actionable content suggestions
- urgency
- reason why this is recommended now

Important:
This should produce direction, not generic copy spam.

---

### 4. Competitor Monitoring Agent

Purpose:
- classify competitor content relevance
- determine risk level
- identify when a competitor is dominating a topic

Inputs:
- competitor content
- candidate strategic profile
- current narrative state

Outputs:
- competitor alerts
- suggested response or silence
- topic-level risk signals

---

### 5. Daily Briefing Agent

Purpose:
- compile outputs from all engines
- organize them into a readable and useful briefing

Briefing sections:
- narrative radar
- key opportunities
- competitor warning
- missed opportunities
- social performance insight
- recommended action for today

This should be the highest-trust output in the system.

---

## Product-Side AI Design Rules

### Rule 1 — Few agents, clear responsibilities
Do not build many overlapping agents.

### Rule 2 — Agents are jobs first
At the MVP stage, agents should be implemented as:
- prompt templates
- deterministic pipelines
- scheduled jobs

Do not overengineer autonomous loops.

### Rule 3 — AI should interpret, not own the whole stack
Use conventional software for:
- storage
- orchestration
- scheduling
- metrics
- dashboard delivery

Use AI for:
- summarization
- interpretation
- recommendation
- structured reasoning

### Rule 4 — Outputs must be explainable
Every important AI output should preserve:
- source references
- context window used
- generation timestamp
- confidence when possible

---

## Prompting Strategy

Prompts should be modular.

Recommended prompt families:

### Narrative prompts
Used to summarize clusters and detect what is emerging.

### Strategic prompts
Used to compare narrative state with the candidate's communication strategy.

### Recommendation prompts
Used to recommend what to do today.

### Competitor prompts
Used to classify risk from competitor activity.

### Briefing prompts
Used to format and synthesize the daily briefing.

All prompts should be:
- versioned
- stored in the codebase
- easy to revise
- tested against real campaign examples

---

## AI Coding-First Development Model

This project should be built in an AI coding-first way.

That means AI is part of the development workflow from day one.

The internal engineering team should focus more on:
- reviewing
- adapting
- simplifying
- debugging
- polishing front-end
- solving edge cases
- ensuring business fit

AI should generate a large share of the first-pass implementation.

---

## Division of Labor

### AI should be used for
- boilerplate generation
- CRUD endpoints
- schema and migration drafts
- worker scaffolds
- normalization functions
- parser generation
- prompt implementation
- unit test drafts
- front-end component scaffolds
- chart component scaffolds
- internal documentation drafts

### Human developers should focus on
- architecture decisions
- code review
- integration quality
- fixing brittle logic
- front-end refinement
- product consistency
- bug fixing
- operational resilience
- client-specific fit

---

## Recommended Development Workflow

### 1. Document-first
Before coding a module, write:
- purpose
- inputs
- outputs
- tables involved
- endpoint or job behavior

### 2. AI-first implementation draft
Use AI to generate the initial code.

### 3. Human simplification
Developers reduce unnecessary abstraction and fix quality issues.

### 4. Test with real data
Use real or semi-real campaign examples quickly.

### 5. Lock patterns
Once a pattern works, reuse it consistently.

---

## Prompt Guidance for Coding Agents

When using coding models, instruct them to:

- prefer simple architecture
- avoid microservices
- avoid unnecessary abstractions
- use clear naming
- write code that is easy to debug
- generate complete files when possible
- keep business logic explicit
- avoid rare dependencies

Example guidance:

“Generate production-simple code for an MVP using Python, FastAPI, PostgreSQL, Redis, RQ, Next.js, and MUI. Prefer readability and low coupling over clever abstractions. Avoid enterprise-style architecture.”

---

## Documentation Structure for AI-Assisted Coding

Recommended project docs:

- product_overview.md
- system_architecture.md
- data_model.md
- ai_agents.md
- engineering_backlog_mvp.md
- prompts/
- api_specs/
- jobs_specs/

This makes the codebase much easier for AI tools to navigate and extend.

---

## Rules to Prevent AI-Coding Chaos

### 1. No code without module intent
Every generated piece of code must map to a documented module.

### 2. No parallel competing patterns
Do not let multiple AI sessions create three different styles for the same thing.

### 3. Review generated migrations carefully
AI is useful here, but schema quality matters a lot.

### 4. Keep prompts under version control
Prompt changes are product changes.

### 5. Prefer deterministic jobs over conversational magic
The product must feel reliable.

---

## What Not to Do

- do not build a huge multi-agent system at the start
- do not let AI invent the architecture on the fly
- do not accept generated code without cleanup
- do not optimize for elegance over speed
- do not allow front-end inconsistency across modules

---

## Practical Next Step

After these documents, the next document should be:
- engineering_backlog_mvp.md

That file should define:
- sprint order
- modules
- endpoints
- workers
- cron jobs
- delivery milestones

That becomes the execution layer for both humans and coding AIs.
