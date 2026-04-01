# 09_jobs_and_crons.md

## Purpose

Define all background jobs, scheduled tasks, and processing cadence for the MVP.

This document exists to:
- keep worker design consistent
- avoid duplicated processing logic
- support AI-generated worker code
- make orchestration explicit
- separate collection, processing, and delivery clearly

The system should be worker-heavy and batch-oriented.

---

## Job Design Principles

- jobs should do one thing well
- every job must have clear inputs and outputs
- jobs must be retryable
- jobs must write logs and status
- jobs should be idempotent when possible
- orchestration should be explicit, not hidden

Recommended worker stack:
- Redis
- RQ

---

## Job Categories

The MVP needs four major job groups:

1. Collection jobs
2. Processing jobs
3. Intelligence jobs
4. Delivery jobs

---

# 1. Collection Jobs

These jobs pull raw data from monitored sources.

## sync_single_source

### Purpose
Run collection for one monitored source.

### Input
- source_id

### Steps
- load source
- select connector by platform/source_type
- collect raw payload
- store raw payload
- normalize items
- insert new content
- insert metrics
- write sync log

### Output
- source_sync_log record
- new content_items
- new content_metrics

### Retry
Yes

---

## sync_youtube_sources

### Purpose
Run batch sync for all active YouTube sources.

### Input
- optional candidate_id
- optional source_ids

### Output
- triggers `sync_single_source` for matching sources

---

## sync_rss_sources

Same pattern as YouTube batch sync.

---

## sync_instagram_sources

Same pattern.

---

## sync_tiktok_sources

Same pattern.

---

## sync_x_sources

Same pattern.

---

# 2. Normalization and Content Processing Jobs

These jobs enrich content after collection.

## normalize_new_content

### Purpose
Ensure recently collected content is fully normalized.

### Input
- optional content_ids
- optional time window

### Steps
- load raw content
- clean text
- standardize metadata
- validate content type
- update normalized fields

### Output
- normalized content_items ready for downstream processing

---

## compute_content_embeddings

### Purpose
Generate embeddings for new or updated content.

### Input
- optional content_ids
- optional candidate_id
- optional time window

### Steps
- select content without embeddings
- generate embeddings
- store in content_embeddings

### Output
- new embedding rows

### Retry
Yes

---

## assign_content_topics

### Purpose
Assign one or more topics to content items.

### Input
- content_ids or recent window

### Steps
- apply rules and/or embedding similarity
- optionally run topic classification prompt
- store content_topics

### Output
- topic assignments

---

## calculate_post_performance

### Purpose
Compute post-level derived performance metrics for candidate-owned content.

### Input
- candidate_id optional
- content_ids optional
- time window optional

### Steps
- load owned social content
- load latest metrics
- compute engagement_count
- compute engagement_rate
- compute velocity_score
- assign performance_band

### Output
- post_performance rows

---

## aggregate_theme_performance

### Purpose
Aggregate performance by theme.

### Input
- candidate_id
- platform optional
- date window

### Output
- theme_performance rows

---

## aggregate_format_performance

### Purpose
Aggregate performance by content format.

### Input
- candidate_id
- platform optional
- date window

### Output
- format_performance rows

---

## generate_performance_insights

### Purpose
Produce human-readable insights from post/theme/format performance.

### Input
- candidate_id
- date window

### Output
- performance_insights rows

Examples:
- top theme
- weak theme
- top format
- low-performing format
- narrative fit insight

---

# 3. Narrative and Graph Jobs

These jobs create the narrative layer.

## build_narrative_clusters

### Purpose
Group relevant content into narrative candidate clusters.

### Input
- candidate_id
- time window
- optional topic_name

### Steps
- load recent monitored content
- group by topic
- cluster semantically similar items
- create/update cluster records

### Output
- narrative_clusters

---

## generate_narratives

### Purpose
Create or update narrative records from clusters.

### Input
- candidate_id
- cluster_ids optional
- time window optional

### Steps
- summarize cluster
- assign narrative label
- estimate volume_score
- estimate growth_rate
- identify key actors
- create/update narrative

### Output
- narratives rows

---

## resolve_actors

### Purpose
Resolve authors/sources into actor entities.

### Input
- content_ids or recent window

### Steps
- map author handles/names
- create missing actors if needed
- link author_actor_id back to content

### Output
- actors
- actor_content_edges

---

## assign_content_to_narratives

### Purpose
Link content items to narratives.

### Input
- candidate_id
- content_ids optional
- date window optional

### Output
- content_narrative_edges

---

## infer_actor_narrative_roles

### Purpose
Infer how actors participate in narratives.

### Roles may include:
- originator
- amplifier
- responder
- critic
- counter_narrative
- competitor_dominator
- ally_amplifier

### Output
- actor_narrative_edges

---

## infer_narrative_relations

### Purpose
Infer relationships between narrative nodes.

### Possible relation types
- supports
- contradicts
- evolves_from
- amplifies
- fragments
- competes_with

### Output
- narrative_relations

---

# 4. Strategic Intelligence Jobs

These jobs turn narrative signals into candidate-specific intelligence.

## generate_strategic_opportunities

### Purpose
Cross narratives with candidate profile and determine opportunities.

### Input
- candidate_id
- recent narratives

### Output
- strategic_opportunities

---

## generate_strategic_alerts

### Purpose
Create risk or urgency alerts.

### Alert examples
- competitor is dominating relevant narrative
- narrative is accelerating rapidly
- sensitive topic requires monitoring
- candidate is exposed to omission risk

### Output
- strategic_alerts

---

## generate_content_recommendations

### Purpose
Produce actionable content directions.

### Input
- candidate_id
- strategic opportunities
- performance insights
- narrative state

### Output
- content_recommendations

---

## detect_missed_opportunities

### Purpose
Detect high-value narratives not recently addressed by the candidate.

### Input
- candidate_id
- current narratives
- recent candidate content

### Output
- missed_opportunities

---

## analyze_competitor_activity

### Purpose
Evaluate competitor content against current narratives.

### Input
- candidate_id
- competitor content
- narrative state

### Output
- competitor_activity
- competitor_alerts

---

## analyze_ally_activity

### Purpose
Detect useful ally amplification opportunities.

### Input
- candidate_id
- ally content
- strategy state

### Output
- ally_activity
- ally_amplification_suggestions

---

# 5. Delivery Jobs

These jobs prepare and send outputs.

## build_daily_briefing

### Purpose
Compile a briefing for one candidate and one date.

### Input
- candidate_id
- briefing_date

### Sections
- top narratives
- top opportunities
- top competitor alert
- missed opportunity
- social performance insight
- recommended actions

### Output
- daily_briefings row

---

## send_daily_briefing

### Purpose
Send briefing through delivery channel.

### Input
- briefing_id
- channel (default: whatsapp)

### Steps
- load briefing
- format message
- call messaging provider
- store result in whatsapp_messages

### Output
- whatsapp_messages row
- updated briefing status

---

## send_alert_message

### Purpose
Send urgent messages outside the daily briefing cycle.

### Input
- candidate_id
- alert_id
- channel

### Output
- whatsapp_messages row

---

# 6. Recommended Cron Schedule

These are the suggested default cadences.

## Collection cadence

### RSS
Every 15 to 30 minutes

### YouTube
Every 1 to 3 hours

### Instagram
Every 2 to 4 hours

### TikTok
Every 2 to 4 hours

### X
Every 1 to 3 hours when enabled

---

## Processing cadence

### normalize_new_content
Every 30 minutes

### compute_content_embeddings
Every 1 hour

### assign_content_topics
Every 1 hour

### resolve_actors
Every 2 hours

### calculate_post_performance
Every 3 to 6 hours

### aggregate_theme_performance
Every 6 hours

### aggregate_format_performance
Every 6 hours

### generate_performance_insights
Every 6 hours

---

## Narrative cadence

### build_narrative_clusters
Every 3 hours

### generate_narratives
Every 3 hours

### assign_content_to_narratives
Every 3 hours

### infer_actor_narrative_roles
Every 6 hours

### infer_narrative_relations
Every 6 to 12 hours

---

## Strategic cadence

### generate_strategic_opportunities
Every 3 hours after narratives

### generate_strategic_alerts
Every 3 hours after opportunities

### generate_content_recommendations
Every 3 hours after strategy refresh

### detect_missed_opportunities
Every 6 hours

### analyze_competitor_activity
Every 3 hours

### analyze_ally_activity
Every 3 hours

---

## Delivery cadence

### build_daily_briefing
Once per morning, e.g. 06:30

### send_daily_briefing
Immediately after briefing build succeeds

### send_alert_message
Event-driven or every hour for queued urgent alerts

---

# 7. Orchestration Dependencies

Some jobs should only run after others.

Recommended dependency chain:

1. sync jobs
2. normalize_new_content
3. compute_content_embeddings
4. assign_content_topics
5. resolve_actors
6. build_narrative_clusters
7. generate_narratives
8. assign_content_to_narratives
9. infer_actor_narrative_roles
10. infer_narrative_relations
11. calculate_post_performance
12. aggregate_theme_performance
13. aggregate_format_performance
14. generate_performance_insights
15. generate_strategic_opportunities
16. generate_strategic_alerts
17. generate_content_recommendations
18. detect_missed_opportunities
19. analyze_competitor_activity
20. analyze_ally_activity
21. build_daily_briefing
22. send_daily_briefing

This does not mean everything must run serially all day.
It means job dependencies must be respected when data freshness matters.

---

# 8. Retry and Failure Policy

Each job should define:

- max retries
- retry backoff
- failure logging
- dead-letter handling if necessary

Suggested defaults:
- connector jobs: retry 3 times
- LLM jobs: retry 2 times
- delivery jobs: retry 2 times
- aggregation jobs: retry 1 or 2 times depending on cost

Failures must be visible in internal ops views.

---

# 9. Operational Visibility

The system should expose internal job health.

Suggested operational views:
- recent job runs
- failed job runs
- connector failure rates
- last successful sync per source
- last successful briefing per candidate
- WhatsApp send failures

This is critical for reliable pilot operations.

---

# 10. Suggested Worker File Structure

Recommended backend job organization:

- jobs/collection.py
- jobs/normalization.py
- jobs/embeddings.py
- jobs/topics.py
- jobs/performance.py
- jobs/narratives.py
- jobs/graph.py
- jobs/strategy.py
- jobs/competitors.py
- jobs/allies.py
- jobs/briefings.py
- jobs/delivery.py

This structure helps AI tools generate code consistently.

---

# 11. AI Coding-First Notes

When generating worker code with AI:
- define one job per file function clearly
- pass explicit arguments
- keep side effects visible
- log start/end/failure
- do not hide business logic in framework magic
- make jobs manually triggerable in development

Manual triggerability is very important during the MVP phase.

---

# 12. MVP Priority Order

If job implementation must be sequenced tightly, the order should be:

1. sync_single_source
2. sync_youtube_sources
3. sync_rss_sources
4. normalize_new_content
5. compute_content_embeddings
6. assign_content_topics
7. calculate_post_performance
8. aggregate_theme_performance
9. aggregate_format_performance
10. generate_performance_insights
11. build_narrative_clusters
12. generate_narratives
13. generate_strategic_opportunities
14. generate_content_recommendations
15. build_daily_briefing
16. send_daily_briefing

After this, add:
17. competitor jobs
18. ally jobs
19. graph enrichment jobs
20. missed-opportunity jobs

This ordering gives the fastest path to a sellable system.
