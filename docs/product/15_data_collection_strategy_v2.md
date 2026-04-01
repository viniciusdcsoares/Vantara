
# 15_data_collection_strategy_v2.md

## Purpose

Define the **updated data collection architecture** aligned with the latest system design, including:

- candidate-aware prioritization
- temporal intelligence
- argument extraction pipeline
- actor metadata capture
- cross-platform signals
- relevance pre-filtering

This document supersedes the initial `15_data_collection_strategy.md` and reflects the full analytical pipeline required by:

- narrative scoring model
- temporal layer
- candidate configuration model
- recommendation engine

The goal is to ensure that **data ingestion directly supports the intelligence layer**.

---

# Core Principles

The collection strategy must follow these principles:

1. **Signal quality over raw volume**
2. **Candidate-aware relevance**
3. **Temporal precision**
4. **Cross-platform comparability**
5. **Cost-aware processing**
6. **Structured inputs for AI pipelines**

The system must collect **only what improves narrative intelligence**.

---

# Candidate-Aware Source Prioritization

Sources are prioritized according to the candidate configuration model.

Each monitored source receives a priority classification.

### Source Priority Types

```
candidate_core
competitor_core
ally_core
regional_media
national_media
influencer_high
influencer_low
experimental_source
```

### Priority Influence

Source priority affects:

- collection frequency
- retry policies
- processing priority
- monitoring alerts

Example:

```
candidate_core → highest frequency
competitor_core → high frequency
regional_media → medium frequency
influencer_low → lower frequency
```

---

# Source Registry

All monitored sources are stored in the Source Registry.

Fields:

```
source_id
platform
source_type
external_identifier
url
owner_type
source_priority
approved_by_admin
created_at
updated_at
```

Owner types:

```
candidate
competitor
ally
media
influencer
institution
```

---

# Source Discovery System

The platform may suggest new sources based on narrative analysis.

Signals for suggestion:

- repeated appearance in narrative clusters
- high engagement actors entering narratives
- frequent amplification of competitor narratives

Suggested sources are not automatically monitored.

Workflow:

```
source detected
↓
suggestion generated
↓
admin review
↓
approved → added to source registry
```

---

# Supported Platforms (MVP)

Initial supported platforms:

```
YouTube (API)
Instagram (Apify actor)
TikTok (Apify actor)
RSS / News feeds
```

Additional platforms may be added later.

---

# Collection Frequency

Collection frequency is influenced by source priority.

Example policy:

Candidate Core

```
every 30–60 minutes
```

Competitors

```
every 1–2 hours
```

Regional Media

```
every 2 hours
```

Influencers

```
every 3–4 hours
```

RSS / News

```
every 15–30 minutes
```

---

# Data Collection Pipeline

Updated ingestion pipeline:

```
Source Sync
↓
Raw Payload Storage
↓
Normalization Layer
↓
Temporal Field Extraction
↓
Author Metadata Extraction
↓
Basic Content Filters
↓
Candidate Relevance Pre-Filter
↓
Argument Extraction
↓
Embedding Generation
↓
Content Storage
↓
Narrative Processing
```

---

# Temporal Field Layer

The ingestion layer must capture all temporal signals required by the scoring model.

Required fields:

```
published_at
fetched_at
first_seen_at
metrics_captured_at
```

These timestamps enable:

- lifecycle detection
- growth analysis
- engagement velocity
- narrative resurgence detection

---

# Author Metadata Extraction

Each collected content item must include author metadata.

Fields:

```
author_id
author_name
platform_handle
followers_count
verified_status
actor_type
```

Actor types may include:

```
politician
journalist
media_outlet
influencer
institution
citizen
```

This metadata feeds the **Actor Influence Score**.

---

# Basic Content Filters

Before entering deeper analysis, content must pass basic filters.

Filters include:

### Minimum Content Threshold

Content must contain sufficient text.

Example:

```
minimum 10 tokens
```

---

### Language Detection

Ensure the content matches campaign language context.

---

### Spam Filtering

Remove:

- commercial spam
- unrelated promotions
- automated bot noise

---

# Candidate Relevance Pre-Filter

Before heavy processing (LLM + embeddings), the system performs a relevance check.

This reduces computational cost.

Relevance factors:

```
theme_match
actor_relevance
platform importance
engagement threshold
candidate region relevance
```

Only content above the threshold proceeds to argument extraction.

---

# Argument Extraction Stage

Relevant content proceeds to argument extraction.

The system extracts the **core claim of the content**.

Example:

Content:

"Crime increased after police cuts."

Extracted argument:

"Reducing police presence increases crime."

This stage converts unstructured text into structured claims.

---

# Embedding Generation

Extracted arguments are converted into embeddings.

Embeddings support:

- argument clustering
- narrative inference
- cross-platform narrative detection

Embeddings should be generated only after relevance filtering.

---

# Cross-Platform Narrative Signals

Content must retain platform identity to support cross-platform analysis.

Required fields:

```
platform
content_type
canonical_url
source_id
```

This enables detection of:

- narrative propagation across platforms
- amplification patterns
- cross-platform narrative acceleration

---

# Content Storage Model

Each stored content item includes:

```
content_id
platform
source_id
author_id
content_text
content_url
published_at
fetched_at
metrics
argument_id
embedding_id
```

This structure supports downstream analytics.

---

# Duplicate Detection

Duplicate detection prevents repeated processing.

Methods:

- normalized text hashing
- URL matching
- semantic similarity checks

Duplicate content should map to the same argument cluster.

---

# Cost Control Strategy

The system must minimize unnecessary LLM usage.

Cost control strategies:

- relevance pre-filter
- batch argument extraction
- avoid duplicate embedding generation
- prioritize high-signal sources

---

# Fault Tolerance

Collection failures must not halt the system.

If a connector fails:

```
log error
retry scheduled
continue other pipelines
```

Each connector must have retry policies.

---

# Data Reliability Principle

Reliable data ingestion is more important than maximum coverage.

Monitoring **50 high-quality sources reliably** is preferable to monitoring **500 sources unreliably**.

The system must prioritize:

- stability
- clean inputs
- predictable processing load

---

# Long-Term Expansion

Future versions may include:

- automated creator discovery
- network-based actor detection
- deeper narrative propagation modeling
- discourse graph expansion (Paradoxa integration)

---

# Final Principle

The data collection layer must serve the intelligence engine.

Collection design must always support:

- narrative detection
- argument extraction
- candidate-specific relevance
- strategic recommendation generation
