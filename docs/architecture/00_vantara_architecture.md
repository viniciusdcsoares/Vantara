# Vantara Political Intelligence Platform -- Technical Architecture & Development Blueprint

## 1. Product Objective

The system must deliver five core capabilities:

1.  Collect data from social media and monitored sources
2.  Transform raw content into narrative intelligence
3.  Cross narratives with the candidate's strategic profile
4.  Generate strategic recommendations and content suggestions
5.  Deliver insights via dashboard and WhatsApp briefing

The system is designed to launch in 3--4 weeks and support early
commercial clients (5--20).

------------------------------------------------------------------------

## 2. Architectural Principles

The architecture follows these principles:

• Batch-first processing\
• Human-readable outputs\
• Dashboard-first intelligence\
• WhatsApp-first delivery\
• Minimal infrastructure complexity

Core value chain:

Data collection → Processing → Narrative synthesis → Strategic reasoning
→ Delivery

------------------------------------------------------------------------

## 3. System Architecture Overview

Pipeline:

Data Sources\
↓\
Ingestion Workers\
↓\
Normalization Layer\
↓\
PostgreSQL + pgvector\
↓\
Narrative Engine\
↓\
Strategic Engine\
↓\
Recommendation Engine\
↓\
Delivery Layer (Dashboard + WhatsApp)

------------------------------------------------------------------------

## 4. Infrastructure Diagram

Data Sources: - YouTube API - RSS / News - Instagram - TikTok - X /
Twitter - Google Trends

Processing Stack: - Python - FastAPI - Redis - RQ Workers

Storage: - PostgreSQL - pgvector extension

Front-end: - Next.js - MUI (Material UI)

Messaging: - Twilio WhatsApp API or Z‑API

Hosting: - Railway / Render (MVP) - AWS (later stage)

------------------------------------------------------------------------

## 5. Core Platform Modules

### 5.1 Ingestion Service

Responsible for collecting data from external sources.

Sources: - Social media accounts - Competitor channels - Ally channels -
News feeds - Political influencers

Outputs: - content_items - content_metrics - source_sync_logs

Collection frequency: - RSS: every 15--30 minutes - YouTube: every 1--3
hours - Instagram/TikTok/X: every 1--4 hours

------------------------------------------------------------------------

### 5.2 Normalization Service

Transforms heterogeneous data into unified schema.

Key derived metrics: - engagement_count - engagement_rate -
velocity_score - recency_score

This makes content comparable across platforms.

------------------------------------------------------------------------

### 5.3 Narrative Engine

Detects and summarizes narrative clusters.

Pipeline: content → embeddings → clustering → summarization → narrative
detection

Outputs stored in:

narratives table: - topic - narrative_summary - dominant_position -
volume - growth_rate - key_actors - opportunity_score - risk_score

------------------------------------------------------------------------

### 5.4 Strategic Engine

Crosses narrative signals with candidate strategy.

Inputs: - narrative clusters - candidate positioning - competitor
activity - ally activity - social performance

Outputs: - strategic opportunities - strategic alerts - narrative risks

Tables: - strategic_opportunities - strategic_alerts

------------------------------------------------------------------------

### 5.5 Recommendation Engine

Generates actionable suggestions.

Outputs: - post ideas - recommended format - narrative angle - urgency
level - strategic justification

Table: content_recommendations

------------------------------------------------------------------------

### 5.6 Competitor Monitor

Tracks competitor activity and narrative influence.

Pipeline: competitor content → topic detection → narrative comparison →
risk classification

Tables: - competitor_activity - competitor_alerts

------------------------------------------------------------------------

### 5.7 Ally Amplification Engine

Detects opportunities to amplify allied messaging.

Tables: - ally_activity - ally_amplification_suggestions

------------------------------------------------------------------------

### 5.8 Social Media Performance Engine

Analyzes the candidate's own social media performance.

Platforms: - YouTube - Instagram - TikTok

Core metrics: - views - likes - comments - shares - follower growth

Derived metrics: - engagement_rate - velocity - consistency - theme
performance - format performance

Key insights generated: • Top performing posts\
• Low performing posts\
• Themes with strongest engagement\
• Formats with strongest engagement\
• Narrative alignment opportunities

Tables: - post_performance - theme_performance - format_performance -
performance_insights

------------------------------------------------------------------------

### 5.9 Briefing Builder

Creates the daily strategic briefing.

Briefing structure:

1.  Narrative radar
2.  Strategic opportunities
3.  Competitor alerts
4.  Missed narrative opportunities
5.  Social performance insight
6.  Content recommendation

Table: daily_briefings

------------------------------------------------------------------------

### 5.10 Delivery Layer

Outputs insights to two surfaces:

Dashboard (Next.js + MUI) WhatsApp messaging

Message types: - daily_briefing - narrative_alert - competitor_alert -
strategic_suggestion

Table: whatsapp_messages

------------------------------------------------------------------------

## 6. Candidate Strategic Profile

Setup fields must only include actionable information.

### Identity

-   name
-   party
-   state
-   office
-   ideological spectrum
-   communication tone
-   political archetype

### Campaign Objective

-   campaign thesis
-   main narrative goal
-   desired perception

### Priority Themes

For each theme: - priority level - position summary - preferred argument
angle - preferred formats

### Sensitive Topics

-   avoid
-   respond if provoked
-   allowed framing
-   prohibited framing

### Target Audiences

-   segment
-   main concern
-   messaging tone

### Allies

-   political weight
-   alignment themes
-   amplification triggers

### Competitors

-   strategic risk
-   themes dominated
-   vulnerabilities
-   response strategy

### Owned Channels

-   YouTube
-   Instagram
-   TikTok
-   X
-   Telegram
-   Website

------------------------------------------------------------------------

## 7. Database Structure

Political Core: - candidates - candidate_themes -
candidate_sensitive_topics - candidate_audiences - allies - competitors

Data Collection: - monitored_sources - social_accounts - content_items -
content_metrics - source_sync_logs

Intelligence: - content_embeddings - content_topics - narratives -
narrative_clusters - strategic_opportunities - strategic_alerts

Recommendations: - content_recommendations

Delivery: - daily_briefings - whatsapp_messages

Competitive Monitoring: - competitor_activity - competitor_alerts

Allies: - ally_activity - ally_amplification_suggestions

Performance: - post_performance - theme_performance -
format_performance - performance_insights

------------------------------------------------------------------------

## 8. AI Agent Structure

Recommended minimal agent set:

1.  Narrative Radar Agent
    -   detects emerging narratives
2.  Strategic Reasoning Agent
    -   interprets narratives against candidate profile
3.  Recommendation Agent
    -   suggests actions and content ideas
4.  Competitor Monitoring Agent
    -   evaluates adversary messaging risk
5.  Daily Briefing Agent
    -   compiles final briefing

These can initially be implemented as prompt-driven jobs rather than
full autonomous agents.

------------------------------------------------------------------------

## 9. Processing Strategy

The system should rely primarily on batch processing.

Recommended intervals:

Content ingestion: - RSS: 15--30 min - YouTube: 1--3h - Social scraping:
1--4h

Narrative recalculation: - every 3 hours

Strategic recommendations: - 2--4 times daily

Daily briefing: - once per day (morning)

------------------------------------------------------------------------

## 10. Infrastructure Cost Estimates

MVP (1--5 clients):

Infrastructure: \$200--\$600/month

Scraping / API usage: \$100--\$800/month

LLM usage: \$200--\$1,000/month

Estimated total: \$500--\$2,400/month

For a product priced at \$3k/month+ per client, this remains
sustainable.

------------------------------------------------------------------------

## 11. Major Cost Drivers

Primary risks:

1.  Social media scraping instability
2.  Excessive LLM usage
3.  Reprocessing entire datasets too frequently

Mitigations:

• Limit monitored sources per candidate\
• Cache narrative results\
• Use embeddings before LLM reasoning

------------------------------------------------------------------------

## 12. Scaling Phases

Phase 1 -- MVP (1--10 clients) Single backend + workers + database.

Phase 2 -- Early growth (10--50 clients) Separate ingestion workers and
analytics jobs.

Phase 3 -- Mature platform (50+ clients) Dedicated pipelines per
platform and distributed job queues.

------------------------------------------------------------------------

## 13. Development Order

Phase 1 - candidate setup - source monitoring - ingestion pipelines

Phase 2 - narrative detection - social analytics

Phase 3 - strategic engine - recommendations

Phase 4 - daily briefing - WhatsApp delivery

Phase 5 - competitor monitoring - ally amplification - missed narrative
detection

------------------------------------------------------------------------

## 14. Key Risks

Risk: platform scraping instability\
Mitigation: rely heavily on YouTube + RSS early.

Risk: generic AI outputs\
Mitigation: strong candidate profile setup.

Risk: dashboard fatigue\
Mitigation: WhatsApp-first intelligence delivery.

Risk: excessive client customization\
Mitigation: standardized onboarding schema.

------------------------------------------------------------------------

## 15. MVP Deployment Architecture

Minimal deployment stack:

FastAPI backend\
RQ workers\
Redis\
PostgreSQL + pgvector\
Next.js + MUI frontend\
Object storage for raw payloads\
Twilio or Z‑API messaging service

This architecture prioritizes speed of launch, maintainability, and
operational simplicity.
