
# 00_master_documentation_index.md

## Purpose

This document serves as the **master index for the entire project documentation**.

It provides:

- recommended reading order
- purpose of each document
- which team member or AI agent should use each file
- when each document is relevant during development

This index is designed for:

- human developers
- AI coding agents (Codex / Claude Code)
- product operators
- future maintainers

---

# Documentation Structure Overview

The project documentation is organized into six layers:

1. Product Vision
2. System Architecture
3. Data & Intelligence Models
4. AI Behavior & Processing
5. Infrastructure & Engineering
6. Execution & Build Plan

Reading documents in this order ensures correct understanding.

---

# Layer 1 — Product Vision

## 01_product_overview.md

**Purpose**
Defines the product concept and high-level value proposition.

**Key Topics**

- what the platform does
- who the users are
- why the product exists
- core features of the MVP

**Used by**

- founders
- product managers
- sales team
- investors

---

# Layer 2 — System Architecture

## 02_system_architecture.md

**Purpose**

Defines the system at a high level.

**Key Topics**

- system components
- service boundaries
- interaction between modules

**Used by**

- backend engineers
- DevOps
- AI architects

---

## 03_data_model.md

**Purpose**

Explains the conceptual data model before the final schema.

**Key Topics**

- entities
- relationships
- analytical model

**Used by**

- backend engineers
- database designers

---

# Layer 3 — Intelligence Models

## 14_narrative_scoring_and_argument_model.md

**Purpose**

Defines how discourse is modeled:

```
Topic → Narrative → Argument → Actor
```

**Key Topics**

- narrative lifecycle
- scoring logic
- opportunity detection

**Used by**

- AI engineers
- backend developers
- data scientists

---

## 14_temporal_patch.md

**Purpose**

Adds temporal intelligence to narrative analysis.

**Key Topics**

- recency
- velocity
- lifecycle detection
- resurgence detection

---

## 16_candidate_configuration_and_relevance_model.md

**Purpose**

Defines how the system interprets narratives through the candidate's strategy.

**Key Topics**

- campaign themes
- sensitive topics
- audiences
- geographic context

---

# Layer 4 — AI Behavior

## 13_prompt_library.md

**Purpose**

Defines the core prompts powering the intelligence engine.

**Key Topics**

- narrative detection
- opportunity detection
- recommendation prompts
- briefing generation

**Used by**

- AI engineers
- operators adjusting prompts

---

## 17_ai_processing_pipeline.md

**Purpose**

Defines how AI jobs run in production.

**Key Topics**

- queue architecture
- job order
- batching
- retry logic
- cost control

---

# Layer 5 — Data Collection

## 15_data_collection_strategy_v2.md

**Purpose**

Defines the ingestion system.

**Key Topics**

- candidate-aware collection
- source prioritization
- temporal capture
- argument extraction pipeline

**Used by**

- backend engineers
- DevOps

---

# Layer 6 — Infrastructure

## 08_api_spec.md

Defines the API endpoints used by the frontend.

---

## 09_jobs_and_crons.md

Defines scheduled jobs and automated tasks.

---

## 10_repo_blueprint.md

Defines the repository structure.

---

## 11_runtime_and_prompt_governance.md

Defines how prompts, tokens, and runtime secrets are managed.

---

## 12_bootstrap_repo_tasks.md

Defines the initial repository setup tasks.

---

# Layer 7 — Data Storage

## 18_database_schema_final.md

**Purpose**

Defines the final database schema.

**Key Topics**

- tables
- relationships
- vector storage
- indexing strategy

**Used by**

- backend engineers
- database engineers

---

# Layer 8 — Execution

## 19_mvp_build_sequence.md

**Purpose**

Defines the **4-week MVP build plan**.

**Key Topics**

- weekly implementation plan
- vertical slices
- validation checkpoints

**Used by**

- engineering team
- product lead

---

# Recommended Reading Order

For new engineers or AI coding agents:

1. 01_product_overview.md
2. 02_system_architecture.md
3. 03_data_model.md
4. 15_data_collection_strategy_v2.md
5. 14_narrative_scoring_and_argument_model.md
6. 16_candidate_configuration_and_relevance_model.md
7. 13_prompt_library.md
8. 17_ai_processing_pipeline.md
9. 18_database_schema_final.md
10. 19_mvp_build_sequence.md

This order follows the actual system flow.

---

# For AI Coding Agents

Before generating code, AI agents should read:

```
02_system_architecture.md
15_data_collection_strategy_v2.md
17_ai_processing_pipeline.md
18_database_schema_final.md
19_mvp_build_sequence.md
```

These files contain the engineering constraints.

---

# Final Principle

This documentation set represents a **complete blueprint of the MVP**.

It should always be treated as the **single source of truth** for:

- architecture
- AI behavior
- database structure
- build order

Any architectural changes must update the corresponding document.
