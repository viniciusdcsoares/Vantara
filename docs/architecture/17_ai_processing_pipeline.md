
# 17_ai_processing_pipeline.md

## Purpose

Define the **AI processing pipeline** that transforms collected data into structured political intelligence.

This document specifies:

- processing stages
- job orchestration
- queue architecture
- LLM usage rules
- batching strategies
- failure handling
- cost control

The goal is to ensure the AI layer is:

- predictable
- scalable
- cost-efficient
- operationally robust

---

# Core Principle

AI processing must be **pipeline-driven and asynchronous**.

Never execute heavy AI tasks inline with ingestion.

All heavy processing must be executed through **job queues**.

This ensures:

- system stability
- scalability
- retry capability
- cost control

---

# High-Level Processing Flow

The full AI pipeline follows this structure:

```
Data Collection
↓
Normalization
↓
Content Relevance Pre-Filter
↓
Argument Extraction (LLM)
↓
Embedding Generation
↓
Argument Clustering
↓
Narrative Inference (LLM)
↓
Narrative Scoring
↓
Opportunity Detection
↓
Recommendation Engine
↓
Briefing Generation
```

Each stage runs as an independent job.

---

# Job Queue Architecture

Processing must be queue-based.

Recommended architecture:

```
ingestion_queue
argument_extraction_queue
embedding_queue
clustering_queue
narrative_inference_queue
scoring_queue
recommendation_queue
briefing_queue
```

Each queue has dedicated workers.

This prevents one stage from blocking others.

---

# Processing Stages

## Stage 1 — Content Relevance Pre-Filter

Purpose:

Reduce the amount of content sent to expensive AI processing.

Checks include:

- theme match
- actor importance
- engagement threshold
- geographic relevance

Only content above threshold proceeds.

---

## Stage 2 — Argument Extraction

LLM extracts the **core claim** of a piece of content.

Example:

Content:

"Crime increased after police cuts."

Argument:

"Reducing police presence increases crime."

This stage converts unstructured text into structured claims.

---

## Stage 3 — Embedding Generation

Extracted arguments are converted into vector embeddings.

Embeddings are used for:

- semantic similarity
- clustering
- cross-platform narrative detection

Embeddings must be cached to avoid duplication.

---

## Stage 4 — Argument Clustering

Arguments are grouped using embedding similarity.

Cluster goal:

Group arguments expressing the same reasoning.

Example cluster:

- "police cuts increased crime"
- "fewer officers raised violence"
- "reduced policing caused crime spike"

---

## Stage 5 — Narrative Inference

LLM analyzes argument clusters to infer the narrative frame.

Example:

Argument cluster:

"crime increased after police cuts"

Narrative:

"reducing policing leads to rising crime"

This creates the narrative layer.

---

## Stage 6 — Narrative Scoring

Narratives are scored using multiple signals:

- volume
- growth
- engagement
- actor diversity
- candidate relevance
- competitor dominance
- temporal signals

This produces the **Narrative Priority Index**.

---

## Stage 7 — Opportunity Detection

The system evaluates whether a narrative represents a strategic opportunity.

Factors:

- alignment with candidate themes
- growth velocity
- competitor dominance
- engagement potential

Outputs include:

- opportunity score
- strategic reasoning
- urgency level

---

## Stage 8 — Recommendation Generation

Narratives and opportunities are converted into suggested actions.

Examples:

- suggested posts
- narrative positioning
- amplification of allies
- contrast with competitors

This stage uses the candidate configuration model.

---

## Stage 9 — Briefing Generation

The system compiles a daily briefing.

Briefing includes:

- key narratives
- strategic opportunities
- competitor alerts
- performance insights
- recommended actions

---

# Queue Orchestration

Each processing stage publishes jobs to the next queue.

Example:

```
argument extraction → embedding queue
embedding → clustering queue
clustering → narrative inference queue
```

Workers should process jobs in batches.

---

# Batch Processing Strategy

LLM tasks should run in batches where possible.

Examples:

Argument extraction:

Batch multiple content items per request.

Narrative inference:

Analyze clusters rather than individual posts.

This reduces API cost.

---

# Cost Control Policies

The system must control LLM costs using:

- relevance pre-filtering
- batch processing
- caching embeddings
- deduplicating content

LLM usage should be reserved for:

- argument extraction
- narrative summarization
- strategic reasoning

---

# Retry and Failure Handling

Each queue must support retries.

Example policy:

```
retry_count = 3
retry_backoff = exponential
```

If failures persist:

- log error
- mark job as failed
- notify monitoring system

---

# Monitoring

The system must track:

- queue length
- processing latency
- LLM request counts
- failure rates

This allows early detection of pipeline issues.

---

# Scaling Strategy

Workers should scale horizontally.

Example:

High ingestion load → increase argument extraction workers.

High narrative activity → scale narrative inference workers.

Queue architecture allows flexible scaling.

---

# AI Governance Rules

AI must not generate outputs without structured inputs.

All prompts must use:

- validated schemas
- controlled prompt versions
- structured outputs

Prompt changes must follow the prompt governance policy.

---

# Final Principle

The AI pipeline must remain:

- deterministic in structure
- flexible in intelligence
- controlled in cost
- resilient to failure

The pipeline architecture ensures that the system scales from **MVP to full narrative intelligence platform**.
