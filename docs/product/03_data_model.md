# Data Model — Political Intelligence Platform

## Data Modeling Goal

The data model must support:

- candidate strategy setup
- source monitoring
- normalized content storage
- performance analysis
- narrative generation
- strategic recommendations
- delivery history

The model should stay relational and clear in the MVP.

---

## Core Political Entities

### candidates
Stores the main candidate profile.

Suggested fields:
- id
- name
- party
- state
- office
- ideological_position
- communication_tone
- political_archetype
- campaign_thesis
- desired_perception
- created_at
- updated_at

### candidate_themes
Stores priority themes.

Suggested fields:
- id
- candidate_id
- theme_name
- priority_level
- position_summary
- preferred_angle
- preferred_formats
- notes

### candidate_sensitive_topics
Stores sensitive themes and framing rules.

Suggested fields:
- id
- candidate_id
- topic_name
- handling_mode
- allowed_framing
- prohibited_framing
- notes

### candidate_audiences
Stores target audience segments.

Suggested fields:
- id
- candidate_id
- segment_name
- main_concern
- language_style
- priority_level
- notes

### allies
Stores main political allies.

Suggested fields:
- id
- candidate_id
- name
- party
- state
- office
- political_weight
- alignment_notes
- amplification_triggers

### competitors
Stores key political competitors.

Suggested fields:
- id
- candidate_id
- name
- party
- state
- office
- strategic_risk
- dominant_themes
- known_strengths
- known_vulnerabilities
- response_strategy

---

## Accounts and Sources

### social_accounts
Candidate-owned accounts.

Suggested fields:
- id
- candidate_id
- platform
- handle
- url
- account_type
- active

### monitored_sources
Public sources monitored by the system.

Suggested fields:
- id
- candidate_id
- source_type
- platform
- display_name
- external_identifier
- url
- category
- owner_type
- active

Categories may include:
- candidate
- competitor
- ally
- influencer
- news
- journalist
- institution

### source_sync_logs
Tracks collection health.

Suggested fields:
- id
- source_id
- started_at
- finished_at
- status
- items_collected
- error_message

---

## Content Storage

### content_items
Stores normalized content across platforms.

Suggested fields:
- id
- source_id
- candidate_id nullable
- platform
- external_id
- author_name
- author_handle
- title
- text_content
- content_type
- url
- published_at
- fetched_at
- raw_payload_ref

### content_metrics
Stores captured metrics for each content item.

Suggested fields:
- id
- content_item_id
- views
- likes
- comments
- shares
- saves nullable
- follower_count nullable
- captured_at

### content_embeddings
Stores vector references.

Suggested fields:
- id
- content_item_id
- embedding_model
- embedding_vector
- created_at

### content_topics
Stores assigned topics.

Suggested fields:
- id
- content_item_id
- topic_name
- confidence
- assigned_by
- assigned_at

---

## Narrative and Intelligence Entities

### narratives
Stores synthesized narrative records.

Suggested fields:
- id
- candidate_id
- topic_name
- narrative_summary
- dominant_position
- volume_score
- growth_rate
- key_actors_json
- opportunity_score
- risk_score
- window_start
- window_end
- created_at

### narrative_clusters
Stores grouped content behind a narrative.

Suggested fields:
- id
- narrative_id
- cluster_label
- cluster_summary
- item_count
- representative_items_json
- created_at

### strategic_opportunities
Stores opportunity records derived from narrative + candidate fit.

Suggested fields:
- id
- candidate_id
- narrative_id
- topic_name
- opportunity_level
- urgency_level
- rationale
- recommended_position
- created_at

### strategic_alerts
Stores alerts such as risk spikes, competitor dominance, or urgent reaction needs.

Suggested fields:
- id
- candidate_id
- alert_type
- topic_name
- severity
- summary
- recommended_action
- created_at

### missed_opportunities
Stores topics the candidate should likely have addressed but did not.

Suggested fields:
- id
- candidate_id
- topic_name
- narrative_volume
- last_candidate_post_at nullable
- priority_level
- rationale
- created_at

---

## Social Performance Entities

### post_performance
Stores enriched performance analysis per owned post.

Suggested fields:
- id
- candidate_id
- content_item_id
- platform
- theme_name nullable
- format_type
- engagement_count
- engagement_rate
- velocity_score
- performance_band
- created_at

Performance bands can be:
- high
- medium
- low

### theme_performance
Aggregates performance by theme.

Suggested fields:
- id
- candidate_id
- platform
- theme_name
- period_start
- period_end
- total_posts
- avg_views
- avg_engagement_rate
- avg_velocity
- performance_score

### format_performance
Aggregates performance by content format.

Suggested fields:
- id
- candidate_id
- platform
- format_type
- period_start
- period_end
- total_posts
- avg_views
- avg_engagement_rate
- avg_velocity
- performance_score

### performance_insights
Stores human-readable insights derived from platform performance.

Suggested fields:
- id
- candidate_id
- insight_type
- platform nullable
- topic_name nullable
- format_type nullable
- summary
- confidence
- created_at

Examples of insight_type:
- top_theme
- weak_theme
- top_format
- low_format
- narrative_fit

---

## Competitor and Ally Monitoring

### competitor_activity
Stores normalized competitor content and risk evaluation.

Suggested fields:
- id
- competitor_id
- content_item_id
- topic_name
- engagement_count
- risk_level
- strategic_note
- recommended_response
- created_at

### competitor_alerts
Stores more urgent competitor-related alerts.

Suggested fields:
- id
- candidate_id
- competitor_id
- topic_name
- severity
- summary
- recommended_action
- created_at

### ally_activity
Stores monitored ally content.

Suggested fields:
- id
- ally_id
- content_item_id
- topic_name
- engagement_count
- created_at

### ally_amplification_suggestions
Stores suggestions to amplify allies.

Suggested fields:
- id
- candidate_id
- ally_id
- topic_name
- rationale
- suggested_action
- urgency_level
- created_at

---

## Recommendations and Delivery

### content_recommendations
Stores content suggestions.

Suggested fields:
- id
- candidate_id
- topic_name
- recommended_platform
- recommended_format
- message_direction
- strategic_reason
- urgency_level
- narrative_id nullable
- created_at

### daily_briefings
Stores generated daily briefings.

Suggested fields:
- id
- candidate_id
- briefing_date
- content_markdown
- summary_json
- status
- created_at

### whatsapp_messages
Stores delivery history.

Suggested fields:
- id
- candidate_id
- message_type
- content
- delivery_status
- sent_at
- external_message_id nullable

---

## Data Model Notes

### Keep it normalized first
The MVP should prioritize clarity and operational reliability.

### Raw payloads should be preserved
Raw content responses should be stored in object storage or a referenceable payload table for debugging and reprocessing.

### Derived tables are allowed
Performance tables and insight tables are useful denormalizations because they speed up dashboard rendering.

### Candidate isolation matters
Every derived object should always remain clearly linked to the candidate context whenever applicable.
