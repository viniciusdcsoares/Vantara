
# 20_ai_coding_playbook.md

## Purpose

This document defines **how AI coding agents should be used in this project**.

It establishes:

- when to use Claude Code vs Codex
- how prompts for AI coding should be structured
- guardrails to prevent architectural drift
- review procedures for AI‑generated code
- safe iteration workflows

The goal is to make **AI-assisted development predictable, fast, and safe**.

This document should be followed by:

- developers
- AI coding agents
- technical leads
- operators supervising AI-assisted builds.

---

# Core Development Philosophy

The system is **AI Coding–First but Architecture‑Constrained**.

This means:

AI generates most of the code.

But:

Architecture and constraints come **from the documentation layer**.

The following rule must always hold:

```
Architecture → constrains AI output
AI → generates implementation
Human → validates coherence
```

Never allow AI to invent architecture that contradicts the docs.

---

# AI Roles

## Claude Code

Claude Code should be used primarily for:

- architectural reasoning
- reviewing code structure
- validating logic
- suggesting improvements
- detecting architectural drift
- designing modules before implementation

Claude should **not** be used for bulk repetitive code generation.

Think of Claude as the **technical architect assistant**.

---

## Codex

Codex should be used primarily for:

- scaffolding services
- generating boilerplate
- generating models
- generating API routes
- generating UI components
- implementing repetitive patterns

Think of Codex as the **implementation engine**.

---

# Recommended Workflow

Every new feature should follow this sequence.

Step 1 — Planning

Use Claude Code to:

- interpret the architecture docs
- design the module
- define interfaces
- define inputs/outputs
- list implementation tasks

Output:

```
module plan
data flow
functions required
files to create
dependencies
```

---

Step 2 — Code Generation

Use Codex to generate:

- models
- services
- routers
- workers
- frontend components

Provide Codex with:

- schema definitions
- architectural constraints
- examples

---

Step 3 — Human Review

Developer verifies:

- code matches architecture
- naming conventions are consistent
- no unnecessary abstractions were introduced
- security practices are respected

---

Step 4 — Claude Code Review

Claude Code should then:

- analyze generated code
- detect architectural violations
- suggest refactors
- confirm adherence to system design

---

Step 5 — Integration

Human developer integrates:

- backend routes
- services
- queues
- UI components

and runs tests.

---

# Prompt Structure for Coding Tasks

When asking an AI agent to generate code, always include:

1. context
2. constraints
3. schema
4. expected output
5. files to modify

Example structure:

```
Context:
We are implementing the argument extraction stage.

Constraints:
Must follow the AI pipeline defined in 17_ai_processing_pipeline.md.

Schema:
arguments table structure (see 18_database_schema_final.md)

Task:
Generate the service that extracts arguments and stores them.

Output:
Python service file compatible with FastAPI backend.
```

---

# Guardrails Against Architectural Drift

AI must **never change core system structures** unless explicitly instructed.

Prohibited AI actions:

- inventing new tables without schema update
- altering database schema implicitly
- creating hidden services
- embedding prompts in random code files
- bypassing job queues

Any architectural change must be:

```
documented
reviewed
approved
```

before implementation.

---

# Code Organization Rules

AI-generated code must follow repository structure defined in:

```
10_repo_blueprint.md
```

Typical structure:

```
backend/
    api/
    services/
    models/
    jobs/
    connectors/
frontend/
    components/
    pages/
prompts/
docs/
```

Do not allow AI to scatter files randomly.

---

# AI Prompt Management

Prompts must live in:

```
/prompts
```

They must:

- be versioned
- have clear names
- return structured outputs

Never hardcode prompts inside service files.

---

# AI Testing Strategy

When AI generates code:

1. run unit tests
2. run integration tests
3. test with real data when possible

AI-generated code should **never be trusted without execution**.

---

# Recommended AI Tasks

AI agents are excellent for:

- writing CRUD APIs
- generating database models
- generating migrations
- generating connectors
- generating job workers
- generating UI tables and forms

These tasks benefit most from automation.

---

# Tasks Requiring Human Oversight

Humans should lead:

- scoring logic
- strategic reasoning
- prompt design
- architecture decisions
- data model evolution

These require deeper contextual judgment.

---

# AI Code Review Checklist

Before accepting AI-generated code, verify:

- schema compatibility
- consistent naming conventions
- no hidden dependencies
- correct async usage in workers
- correct queue usage
- safe error handling
- proper logging

---

# Iteration Philosophy

AI-generated code should be treated as **draft implementations**.

The development cycle should be:

```
generate → review → refine → test → stabilize
```

Avoid assuming the first output is correct.

---

# Final Principle

AI coding dramatically accelerates development.

But the system succeeds only if:

- architecture remains stable
- documentation remains authoritative
- AI output remains supervised

The documentation layer must always remain the **single source of truth** for the project.
