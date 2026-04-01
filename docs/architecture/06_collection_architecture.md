
# 06_collection_architecture.md

## Purpose

Define the **data collection architecture** for the platform.

This layer is critical because both **Vantara (political intelligence)** and **Paradoxa (global narrative mapping)** depend on reliable and scalable collection of public discourse.

The goal is:

- collect multi-platform data
- normalize it
- make providers replaceable
- avoid dependency lock-in (ex: Apify)
- support future proprietary crawlers

The architecture therefore separates:

1. Collection Orchestrator (proprietary core)
2. Source Connectors (replaceable providers)

---

# Architecture Overview

Collection Orchestrator
        │
        ▼
Source Connector Interface
        │
        ├ YouTube API connector
        ├ RSS connector
        ├ Apify Instagram connector
        ├ Apify TikTok connector
        ├ Apify X connector
        └ Future proprietary crawler connectors
        │
        ▼
Normalization Pipeline
        │
        ▼
Content Storage
(Postgres + pgvector)

---

# Core Principle

The system must **never depend directly on Apify or any external scraping tool**.

Instead:

Application → Connector Interface → Provider Implementation

Example:

collect_source(source_id)

The system does not know if the data came from:

- Apify
- API
- custom crawler
- RSS

This makes migration possible later.

---

# Collection Orchestrator

This is a **proprietary service** responsible for managing all data collection.

Responsibilities:

- scheduling source syncs
- triggering connector execution
- retries and failure handling
- rate limiting
- logging
- observability
- deduplication checks
- raw payload storage

---

# Initial Connectors

1. YouTube Connector (API)
2. RSS Connector
3. Apify Instagram Connector
4. Apify TikTok Connector
5. Apify X Connector

These connectors should implement the same interface.

---

# Example Connector Interface

class SourceConnector:

    def collect(self, source):
        pass

    def normalize(self, raw_payload):
        pass

---

# Suggested Sync Frequency

YouTube — 1–3 hours  
RSS — 15–30 minutes  
Instagram — 2–4 hours  
TikTok — 2–4 hours  
X — 1–3 hours

---

# Strategic Importance

This architecture allows the platform to evolve into:

- a political intelligence network
- a global narrative map

Because once the collection graph expands, the platform can map discourse across:

- politicians
- media
- influencers
- institutions
- public debate

This becomes the long‑term strategic asset of the system.
