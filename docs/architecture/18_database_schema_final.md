
# 18_database_schema_final.md

## Purpose

Define the **final logical database schema for the MVP**, consolidating all prior architectural decisions, including:

- content ingestion
- actor modeling
- argument extraction
- narrative clustering
- temporal signals
- candidate configuration
- scoring systems
- recommendations
- briefing outputs

The schema is designed for:

- analytical consistency
- fast querying
- compatibility with vector search
- horizontal scalability
- minimal schema drift during early development

The schema assumes **PostgreSQL + pgvector** for embeddings.

---

# Core Entities

The platform revolves around these primary entities:

```
sources
actors
content_items
arguments
argument_clusters
narratives
narrative_scores
candidates
candidate_config
competitors
allies
recommendations
briefings
```

---

# Table: sources

Represents monitored channels.

Fields:

```
source_id (PK)
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

Indexes:

```
platform
owner_type
source_priority
```

---

# Table: actors

Represents content creators.

Fields:

```
actor_id (PK)
platform
platform_handle
display_name
actor_type
followers_count
verified_status
influence_score
created_at
updated_at
```

Indexes:

```
platform_handle
actor_type
influence_score
```

---

# Table: content_items

Stores collected posts/videos/articles.

Fields:

```
content_id (PK)
platform
source_id (FK)
actor_id (FK)
content_text
content_url
content_type
published_at
fetched_at
first_seen_at
metrics_captured_at
like_count
comment_count
share_count
view_count
created_at
```

Indexes:

```
published_at
actor_id
source_id
platform
```

---

# Table: arguments

Stores extracted claims.

Fields:

```
argument_id (PK)
content_id (FK)
argument_text
embedding_vector (vector)
created_at
```

Indexes:

```
content_id
embedding_vector (vector index)
```

---

# Table: argument_clusters

Clusters of semantically similar arguments.

Fields:

```
cluster_id (PK)
representative_argument
created_at
updated_at
```

---

# Table: argument_cluster_members

Mapping arguments to clusters.

Fields:

```
cluster_member_id (PK)
cluster_id (FK)
argument_id (FK)
```

Indexes:

```
cluster_id
argument_id
```

---

# Table: narratives

Narrative frames inferred from clusters.

Fields:

```
narrative_id (PK)
cluster_id (FK)
topic
narrative_summary
counter_narrative_id (nullable)
lifecycle_stage
created_at
updated_at
```

Indexes:

```
topic
lifecycle_stage
```

Lifecycle stages:

```
emerging
growing
dominant
contested
declining
resurfacing
```

---

# Table: narrative_scores

Stores computed narrative metrics.

Fields:

```
score_id (PK)
narrative_id (FK)
volume_score
growth_score
engagement_score
actor_diversity_score
candidate_relevance_score
competitor_dominance_score
opportunity_score
risk_score
priority_index
computed_at
```

Indexes:

```
narrative_id
priority_index
```

---

# Table: candidates

Basic candidate data.

Fields:

```
candidate_id (PK)
name
party
office_type
state
region
term_status
created_at
```

---

# Table: candidate_config

Stores candidate strategy configuration.

Fields:

```
config_id (PK)
candidate_id (FK)
ideology_position
communication_style
created_at
updated_at
```

---

# Table: candidate_themes

Priority campaign themes.

Fields:

```
theme_id (PK)
candidate_id (FK)
theme_name
priority_weight
```

---

# Table: candidate_sensitive_topics

Sensitive issues requiring caution.

Fields:

```
sensitive_id (PK)
candidate_id (FK)
topic
sensitivity_level
handling_strategy
```

---

# Table: candidate_audiences

Target voter groups.

Fields:

```
audience_id (PK)
candidate_id (FK)
audience_segment
priority_weight
key_concerns
```

---

# Table: competitors

Maps candidate competitors.

Fields:

```
competitor_id (PK)
candidate_id (FK)
actor_id (FK)
relevance_weight
```

---

# Table: allies

Maps allied actors.

Fields:

```
ally_id (PK)
candidate_id (FK)
actor_id (FK)
alignment_strength
```

---

# Table: recommendations

Stores suggested strategic actions.

Fields:

```
recommendation_id (PK)
candidate_id (FK)
narrative_id (FK)
content_idea
recommended_platform
recommended_format
strategic_reason
created_at
```

Indexes:

```
candidate_id
narrative_id
```

---

# Table: briefings

Stores daily campaign briefings.

Fields:

```
briefing_id (PK)
candidate_id (FK)
headline
top_narrative
strategic_opportunity
competitor_alert
recommended_actions
performance_insight
generated_at
```

Indexes:

```
candidate_id
generated_at
```

---

# Vector Storage

Embeddings are stored using pgvector.

Example column:

```
embedding_vector VECTOR(1536)
```

Indexes:

```
ivfflat index for similarity search
```

Used for:

- argument clustering
- semantic search
- narrative detection

---

# Key Relationships

```
sources → content_items
actors → content_items
content_items → arguments
arguments → argument_clusters
argument_clusters → narratives
narratives → narrative_scores
narratives → recommendations
candidates → configurations
candidates → themes
candidates → competitors
candidates → allies
candidates → briefings
```

---

# Indexing Strategy

Critical indexes:

```
published_at
priority_index
actor_id
candidate_id
embedding_vector
```

These support:

- narrative queries
- briefing generation
- clustering operations
- candidate-specific intelligence

---

# Schema Evolution Policy

Schema changes must follow:

1. migration scripts
2. backward compatibility checks
3. index review
4. production migration validation

Avoid schema drift during MVP.

---

# Final Principle

The database schema must support:

- narrative intelligence
- candidate-specific analysis
- scalable ingestion
- efficient AI processing
- fast dashboard queries

This schema forms the **data backbone of the platform MVP**.
