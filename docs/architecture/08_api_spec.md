# 08_api_spec.md

## Purpose

Define the API contract for the MVP backend.

This document exists to:
- keep endpoint generation consistent
- make AI-generated backend code predictable
- reduce ambiguity for front-end integration
- establish stable request/response patterns

The API should stay simple, REST-oriented, and explicit.

---

## API Design Principles

- use clear resource-oriented paths
- prefer explicit nested candidate resources where relevant
- keep payloads predictable
- avoid overloading endpoints with too much magic
- return stable IDs and timestamps
- support pagination on list endpoints
- support filtering on analytics and content endpoints

Base path suggestion:

`/api/v1`

---

## Common Conventions

### Response envelope

Recommended response format:

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

For lists:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 120
  },
  "error": null
}
```

For errors:

```json
{
  "data": null,
  "meta": {},
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid platform value"
  }
}
```

### Pagination

Query params:
- `page`
- `page_size`

### Filtering

Use query params such as:
- `platform`
- `theme`
- `start_date`
- `end_date`
- `status`
- `candidate_id`

### Sorting

Use:
- `sort_by`
- `sort_order`

Example:
`?sort_by=created_at&sort_order=desc`

### Timestamps

All timestamps should be returned in ISO 8601 format.

---

## Auth and Access

MVP recommendation:
- simple internal auth first
- bearer token or session-based auth
- role handling can remain minimal

Possible roles later:
- admin
- operator
- strategist
- viewer

Do not overbuild RBAC in the MVP.

---

## Endpoint Groups

---

# 1. Candidates

## GET /api/v1/candidates

List candidates.

Query params:
- page
- page_size
- search
- state
- party

Response fields:
- id
- name
- party
- state
- office
- communication_tone
- ideological_position
- created_at

---

## POST /api/v1/candidates

Create candidate.

Request body:
```json
{
  "name": "Candidate Name",
  "party": "Party",
  "state": "SP",
  "office": "federal_deputy",
  "ideological_position": "center_right",
  "communication_tone": "direct",
  "political_archetype": "reformer",
  "campaign_thesis": "Public safety and economic relief",
  "desired_perception": "competent and practical"
}
```

---

## GET /api/v1/candidates/{candidate_id}

Return candidate detail.

Includes:
- main profile
- themes count
- allies count
- competitors count
- accounts count
- sources count

---

## PATCH /api/v1/candidates/{candidate_id}

Update candidate.

Accept partial updates.

---

# 2. Candidate Themes

## GET /api/v1/candidates/{candidate_id}/themes

List candidate themes.

## POST /api/v1/candidates/{candidate_id}/themes

Create theme.

Request body:
```json
{
  "theme_name": "public_safety",
  "priority_level": 5,
  "position_summary": "defend intelligence-driven policing",
  "preferred_angle": "practical public safety",
  "preferred_formats": ["short_video", "carousel"],
  "notes": "strongest engagement theme"
}
```

## PATCH /api/v1/candidate-themes/{theme_id}

## DELETE /api/v1/candidate-themes/{theme_id}

---

# 3. Candidate Sensitive Topics

## GET /api/v1/candidates/{candidate_id}/sensitive-topics

## POST /api/v1/candidates/{candidate_id}/sensitive-topics

Request body:
```json
{
  "topic_name": "abortion",
  "handling_mode": "respond_if_provoked",
  "allowed_framing": "institutional and brief",
  "prohibited_framing": "aggressive culture-war language",
  "notes": "avoid making it central"
}
```

## PATCH /api/v1/candidate-sensitive-topics/{topic_id}

## DELETE /api/v1/candidate-sensitive-topics/{topic_id}

---

# 4. Candidate Audiences

## GET /api/v1/candidates/{candidate_id}/audiences

## POST /api/v1/candidates/{candidate_id}/audiences

Request body:
```json
{
  "segment_name": "working_class_families",
  "main_concern": "cost of living",
  "language_style": "simple and practical",
  "priority_level": 5,
  "notes": "high sensitivity to inflation narrative"
}
```

## PATCH /api/v1/candidate-audiences/{audience_id}

## DELETE /api/v1/candidate-audiences/{audience_id}

---

# 5. Allies

## GET /api/v1/candidates/{candidate_id}/allies

## POST /api/v1/candidates/{candidate_id}/allies

Request body:
```json
{
  "name": "Ally Name",
  "party": "Party",
  "state": "SP",
  "office": "mayor",
  "political_weight": 4,
  "alignment_notes": "aligned on public safety and taxes",
  "amplification_triggers": "infrastructure and municipal results"
}
```

## PATCH /api/v1/allies/{ally_id}

## DELETE /api/v1/allies/{ally_id}

---

# 6. Competitors

## GET /api/v1/candidates/{candidate_id}/competitors

## POST /api/v1/candidates/{candidate_id}/competitors

Request body:
```json
{
  "name": "Competitor Name",
  "party": "Party",
  "state": "SP",
  "office": "federal_deputy",
  "strategic_risk": 5,
  "dominant_themes": ["public_safety", "anti_tax"],
  "known_strengths": "high-volume short video distribution",
  "known_vulnerabilities": "weak policy depth",
  "response_strategy": "respond selectively"
}
```

## PATCH /api/v1/competitors/{competitor_id}

## DELETE /api/v1/competitors/{competitor_id}

---

# 7. Social Accounts

## GET /api/v1/candidates/{candidate_id}/social-accounts

## POST /api/v1/candidates/{candidate_id}/social-accounts

Request body:
```json
{
  "platform": "instagram",
  "handle": "@candidate",
  "url": "https://instagram.com/candidate",
  "account_type": "owned",
  "active": true
}
```

## PATCH /api/v1/social-accounts/{account_id}

## DELETE /api/v1/social-accounts/{account_id}

---

# 8. Monitored Sources

## GET /api/v1/candidates/{candidate_id}/monitored-sources

Filters:
- platform
- category
- owner_type
- active

## POST /api/v1/candidates/{candidate_id}/monitored-sources

Request body:
```json
{
  "platform": "youtube",
  "source_type": "channel",
  "display_name": "Channel Name",
  "external_identifier": "UC123",
  "url": "https://youtube.com/...",
  "category": "influencer",
  "owner_type": "competitor",
  "active": true
}
```

## PATCH /api/v1/monitored-sources/{source_id}

## DELETE /api/v1/monitored-sources/{source_id}

---

# 9. Source Sync and Collection

## GET /api/v1/source-sync-logs

Filters:
- source_id
- status
- start_date
- end_date

## POST /api/v1/monitored-sources/{source_id}/sync

Trigger sync for one source.

Response:
```json
{
  "data": {
    "job_id": "job_123",
    "status": "queued"
  },
  "meta": {},
  "error": null
}
```

## POST /api/v1/sync/run

Trigger batch sync by connector type.

Request body:
```json
{
  "platform": "youtube"
}
```

---

# 10. Content Items

## GET /api/v1/content-items

Filters:
- candidate_id
- platform
- source_id
- owner_type
- start_date
- end_date
- topic_name

Fields:
- id
- platform
- author_name
- title
- text_content
- published_at
- url
- metrics_summary

## GET /api/v1/content-items/{content_id}

Return content detail, including:
- normalized content
- metrics history if available
- source reference
- topic assignments
- linked narratives if available

---

# 11. Performance Analytics

## GET /api/v1/candidates/{candidate_id}/performance/overview

Response example:
```json
{
  "data": {
    "total_posts": 42,
    "total_views": 3200000,
    "avg_engagement_rate": 0.082,
    "followers_growth": 0.051
  },
  "meta": {},
  "error": null
}
```

## GET /api/v1/candidates/{candidate_id}/performance/top-posts

Filters:
- platform
- start_date
- end_date
- limit

## GET /api/v1/candidates/{candidate_id}/performance/low-posts

Filters:
- platform
- start_date
- end_date
- limit

## GET /api/v1/candidates/{candidate_id}/performance/themes

Filters:
- platform
- start_date
- end_date

## GET /api/v1/candidates/{candidate_id}/performance/formats

Filters:
- platform
- start_date
- end_date

## GET /api/v1/candidates/{candidate_id}/performance/insights

Return human-readable insights.

---

# 12. Narratives

## GET /api/v1/candidates/{candidate_id}/narratives

Filters:
- topic_name
- start_date
- end_date
- min_growth_rate
- min_risk_score
- min_opportunity_score

Fields:
- id
- topic_name
- narrative_summary
- dominant_position
- volume_score
- growth_rate
- opportunity_score
- risk_score
- updated_at

## GET /api/v1/narratives/{narrative_id}

Return:
- narrative detail
- representative content
- key actors
- related narratives
- associated recommendations if applicable

---

# 13. Narrative Graph

## GET /api/v1/narratives/{narrative_id}/graph

Return graph payload for narrative view.

Suggested response:
```json
{
  "data": {
    "narrative": {},
    "actors": [],
    "content_nodes": [],
    "edges": []
  },
  "meta": {},
  "error": null
}
```

## GET /api/v1/candidates/{candidate_id}/narrative-capture-alerts

Return narratives being dominated or captured by competitors or external actors.

---

# 14. Strategic Opportunities and Alerts

## GET /api/v1/candidates/{candidate_id}/opportunities

Filters:
- topic_name
- urgency_level
- start_date
- end_date

## GET /api/v1/candidates/{candidate_id}/alerts

Filters:
- severity
- alert_type
- start_date
- end_date

## GET /api/v1/candidates/{candidate_id}/missed-opportunities

Filters:
- topic_name
- priority_level

---

# 15. Recommendations

## GET /api/v1/candidates/{candidate_id}/recommendations

Filters:
- topic_name
- platform
- urgency_level
- start_date
- end_date

Fields:
- id
- topic_name
- recommended_platform
- recommended_format
- message_direction
- strategic_reason
- urgency_level
- created_at

## POST /api/v1/candidates/{candidate_id}/recommendations/generate

Trigger recommendation generation manually.

Optional request body:
```json
{
  "topic_name": "public_safety"
}
```

---

# 16. Competitor and Ally Intelligence

## GET /api/v1/candidates/{candidate_id}/competitor-alerts

Filters:
- severity
- competitor_id
- topic_name

## GET /api/v1/candidates/{candidate_id}/ally-suggestions

Filters:
- ally_id
- topic_name
- urgency_level

---

# 17. Daily Briefings

## GET /api/v1/candidates/{candidate_id}/briefings

Filters:
- start_date
- end_date
- status

## GET /api/v1/briefings/{briefing_id}

Returns briefing detail.

## POST /api/v1/candidates/{candidate_id}/briefings/generate

Generate a new briefing.

Request body optional:
```json
{
  "briefing_date": "2026-03-17"
}
```

## POST /api/v1/briefings/{briefing_id}/send

Send briefing via WhatsApp.

Request body:
```json
{
  "channel": "whatsapp"
}
```

---

# 18. Operational and Health Endpoints

## GET /api/v1/health

Basic healthcheck.

## GET /api/v1/ops/jobs

List recent jobs.

## GET /api/v1/ops/jobs/{job_id}

Return job detail and state.

## GET /api/v1/ops/connectors/health

Return collection connector health summary.

This is mostly internal.

---

## API Implementation Notes

### Keep handlers thin
Business logic should live in services and jobs.

### Keep schemas explicit
Do not rely on vague polymorphic payloads.

### Separate internal operational endpoints
Everything under `/ops` can be protected separately.

### Prefer manual trigger endpoints during MVP
They help a lot with debugging and demos.

---

## Suggested File Organization

Backend API modules can be split into:

- candidates.py
- candidate_themes.py
- candidate_sensitive_topics.py
- candidate_audiences.py
- allies.py
- competitors.py
- social_accounts.py
- monitored_sources.py
- sync.py
- content_items.py
- performance.py
- narratives.py
- narrative_graph.py
- strategy.py
- recommendations.py
- briefings.py
- ops.py

This structure works well with AI-assisted code generation.
