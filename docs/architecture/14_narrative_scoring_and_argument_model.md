
# 14_narrative_scoring_and_argument_model.md

## Purpose

Define the **argument → narrative → strategic scoring system** used by the platform.

This document formalizes the analytical core that converts raw social content into:

- narratives
- strategic insights
- opportunities
- alerts
- briefing priorities

The model is intentionally designed to:

- maximize analytical accuracy
- remain operationally fast for campaigns
- avoid excessive reliance on LLM interpretation
- maintain compatibility with the future Paradoxa discourse mapping system

---

# Core Analytical Model

The platform analyzes discourse in **three structured layers**:

Topic → Narrative → Argument → Actor

```
Topic
   ↓
Narratives (frames)
   ↓
Arguments (claims supporting frames)
   ↓
Actors (who pushes which argument)
```

This layered structure improves both:

- clustering stability
- narrative accuracy

---

# Layer Definitions

## Topic

Topics are macro issue areas.

Examples:

- public safety
- taxation
- inflation
- housing
- healthcare
- AI regulation

Topics help group related narratives but do not contain interpretation.

---

## Narrative

A narrative is a **political frame about a topic**.

Examples:

Topic: Public Safety

Possible narratives:

- crime is rising in cities
- criminal justice system is too lenient
- police need more resources
- inequality drives crime

Narratives describe **how the issue is interpreted**.

---

## Argument

Arguments are **specific claims used to support a narrative**.

Example:

Narrative:

"crime is rising in cities"

Arguments:

- violent crime statistics increased
- police presence decreased
- criminal gangs expanded
- courts release criminals quickly

Arguments are extracted from posts and clustered.

---

## Actor

Actors are entities participating in the discourse.

Examples:

- politicians
- journalists
- influencers
- media outlets
- institutions

Actors may:

- originate narratives
- amplify arguments
- oppose narratives
- counter narratives

---

# Argument Extraction

Argument extraction is performed after content ingestion.

Each post is processed to extract the **primary claim**.

Example:

Post:

"Crime increased after police cuts."

Extracted argument:

"Reducing police presence increases crime."

Arguments should be normalized to abstract claims.

---

# Argument Clustering

Arguments are grouped using embedding similarity.

Cluster goal:

Group claims that represent the **same underlying reasoning**.

Example cluster:

- police cuts increased crime
- fewer officers led to higher violence
- reducing policing worsens crime rates

These belong to the same argument cluster.

---

# Narrative Inference

Narratives are inferred from argument clusters.

LLM summarizes the cluster into a **frame description**.

Example:

Cluster summary:

"crime increased after police cuts"

Narrative:

"reducing policing leads to increased crime"

This ensures narratives emerge from real discourse patterns.

---

# Narrative Scoring System

Each narrative receives multiple scores.

Scores allow prioritization and filtering.

---

## Volume Score

Measures how much discourse exists around the narrative.

Formula inputs:

- number of posts
- number of unique actors
- cross-platform presence

Example scale:

0–100

---

## Growth Score

Measures narrative acceleration.

Based on:

- post velocity
- engagement growth
- cluster expansion rate

Example:

Posts last 24h vs previous 24h.

---

## Engagement Score

Measures how strongly the narrative resonates.

Inputs:

- likes
- comments
- shares
- views

Normalized across platforms.

---

## Actor Diversity Score

Measures how many different actors are amplifying the narrative.

Higher diversity suggests:

- narrative spreading beyond origin group

---

## Candidate Relevance Score

Measures alignment with candidate themes.

Inputs:

- candidate priority themes
- campaign messaging focus
- geographic relevance

Example:

Crime narrative relevant to public safety candidate.

---

## Competitor Dominance Score

Measures whether competitors dominate the narrative.

Inputs:

- share of posts by competitor actors
- engagement captured by competitors

High score indicates narrative control by competitors.

---

## Opportunity Score

Measures potential benefit if the candidate engages.

Factors:

- candidate relevance
- narrative growth
- low competitor dominance
- high engagement potential

Example scoring model:

Opportunity Score =
(0.35 × relevance)
+ (0.30 × growth)
+ (0.20 × engagement)
+ (0.15 × actor diversity)

---

## Risk Score

Measures potential risk to candidate.

Factors:

- competitor dominance
- negative sentiment toward candidate
- sensitive topic overlap

Example:

Risk Score =
(0.40 × competitor dominance)
+ (0.30 × growth)
+ (0.30 × sentiment risk)

---

# Narrative Priority Index

The system calculates an overall priority score.

Example:

Priority Index =
(0.40 × opportunity)
+ (0.35 × growth)
+ (0.25 × engagement)

Narratives above threshold are surfaced.

---

# Alert Thresholds

Alerts are generated when thresholds are crossed.

Example triggers:

Opportunity Alert

Opportunity Score > 70

---

Competitor Capture Alert

Competitor Dominance > 65

---

Narrative Surge Alert

Growth Score > 75

---

# Actor Role Classification

Actors can play different roles in narratives.

Possible roles:

- originator
- amplifier
- responder
- critic
- counter narrative

Roles are inferred based on:

- post timing
- content framing
- engagement influence

---

# Strategic Output Mapping

Narratives feed into strategic outputs.

Pipeline:

Argument → Narrative → Score → Strategy Engine

Outputs:

- opportunity detection
- competitor alert
- recommendation
- briefing inclusion

---

# Briefing Inclusion Criteria

Narratives enter daily briefing when:

Priority Index > 60

OR

Competitor Dominance > 65

OR

Opportunity Score > 70

Maximum narratives per briefing:

3–5

---

# Long-Term Compatibility With Paradoxa

This model supports future expansion.

Future layers may include:

- counter argument mapping
- ideology clustering
- discourse networks
- argument lineage

The argument layer becomes the basis for the **Paradoxa discourse graph**.

---

# Final Principle

The system must avoid relying solely on LLM interpretation.

Instead:

LLMs assist with:

- argument extraction
- narrative summarization

Quantitative signals drive prioritization.

This hybrid model maximizes both:

- analytical accuracy
- operational reliability

# Patch — Temporal Layer Integration

This section extends the narrative scoring model with **temporal intelligence**.

Temporal signals are required to correctly evaluate:

- narrative lifecycle
- narrative growth
- narrative saturation
- narrative resurgence
- briefing freshness

Time is not used as an isolated signal.  
Instead, it feeds derived metrics that combine:

- recency
- engagement
- growth
- actor diversity
- platform behavior

---

# Required Temporal Fields

All collected content items must store the following timestamps.

## published_at

When the content was originally published on the platform.

This is the most important temporal signal.

---

## fetched_at

When the system collected the content.

Used for:

- ingestion diagnostics
- collection latency monitoring

---

## first_seen_at

When the platform first detected the content in the system.

In MVP this may be equal to fetched_at.

Future versions may differentiate.

---

## metrics_captured_at

Timestamp indicating when engagement metrics were read.

Important because engagement values evolve over time.

---

# Derived Temporal Signals

Temporal fields are used to generate derived signals.

These signals are used in scoring and lifecycle detection.

---

## hours_since_published

```
hours_since_published =
current_time - published_at
```

---

## engagement_velocity

Measures engagement relative to content age.

Example:

```
engagement_velocity =
total_engagement / hours_since_published
```

Higher velocity suggests stronger narrative traction.

---

## recency_score

Measures how recent the content is relative to platform behavior.

Recency is adjusted using platform decay profiles.

Example concept:

```
recency_score =
platform_weight × f(hours_since_published)
```

---

## growth_window

Narrative growth is measured across temporal windows.

Recommended windows:

```
12h → emergence
48h → trend detection
7d → consolidation
```

Growth score compares narrative activity across these windows.

---

# Platform Temporal Profiles

Different platforms have different narrative lifecycles.

The system applies platform-aware weighting.

Example conceptual model:

TikTok
- short narrative half-life
- recency strongly weighted
- velocity highly important

Instagram
- medium narrative lifecycle
- recency moderately weighted

YouTube
- longer lifecycle
- engagement accumulation over time

News / RSS
- high short-term impact
- legitimacy amplification

These profiles influence:

- recency_score
- velocity interpretation

---

# Narrative Lifecycle Model

Narratives are classified by lifecycle stage.

Lifecycle stage is derived from:

- growth_score
- engagement_velocity
- actor diversity
- temporal signals

Lifecycle states:

```
emerging
growing
dominant
contested
declining
resurfacing
```

---

# Resurfacing Detection

Old narratives may reappear.

A narrative is classified as resurfacing when:

```
historical narrative cluster exists
AND
new growth spike occurs
```

Example:

Old narrative from months ago reappears due to new political event.

Resurfacing should trigger alerts.

---

# Saturation Detection

Narrative saturation occurs when:

- volume remains high
- growth slows
- same actors repeat arguments

Conceptual signal:

```
saturation_score =
high volume
+ low growth
+ repeated actor patterns
```

High saturation reduces opportunity score.

---

# Temporal Use in Briefing

Daily briefing prioritization must favor:

- high growth narratives
- emerging narratives
- resurfacing narratives
- competitor narrative capture

Temporal freshness ensures briefing relevance.

---

# Key Design Principle

Time alone must never determine narrative importance.

Instead:

```
importance =
recency
+ velocity
+ growth
+ engagement
+ candidate relevance
+ actor influence
```

Temporal signals provide **context for narrative dynamics**, not absolute value.

