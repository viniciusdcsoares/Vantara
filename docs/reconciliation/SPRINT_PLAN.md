# SPRINT PLAN — Lean MVP Critical Path

> **Created:** 2026-03-31  
> **Philosophy:** Minimum steps for a working end-to-end flow: `Collect → Extract Claims → Cluster → Report`.  
> **Deferred:** Database, API, frontend, candidate model, scoring formulas, WhatsApp delivery.

---

## Critical Path Overview

```
Sprint 1 (current) ──→ Sprint 2 ──→ Sprint 3 ──→ Sprint 4
Per-Item Analysis       Embeddings    Clustering    Simple Report
     │                      │              │              │
     ▼                      ▼              ▼              ▼
canonical_claim        embed claims    K-Means/       Streamlit
per content item       via Gemini      HDBSCAN        dashboard
+ claim_type           Embedding API   + t-SNE viz    with narratives
```

---

## Sprint 1 — Per-Item Analysis Foundation (~1 week)

> **Goal:** Move from "analyze N videos as a cluster" to "analyze each content item individually."  
> **ADR:** [ADR-001](../adr/ADR-001-per-item-analysis-foundation.md)  
> **Unblocks:** Everything downstream.

### Tasks

| # | Task | Files | Effort |
|---|---|---|---|
| 1.1 | Create `ItemAnalysis` Pydantic schema | `llm_configs/schemas/item_analysis.py` [NEW] | 1h |
| 1.2 | Create per-item prompt + system instruction | `llm_configs/prompts/item_analysis.py` [NEW] | 2h |
| 1.3 | Build item-level orchestrator | `run_item_analysis.py` [NEW] | 3h |
| 1.4 | Iterate items from scraped JSON, call LLM per item | ↑ same file | ↑ included |
| 1.5 | Save per-item results to `outputs/item_analysis/` | ↑ same file | ↑ included |
| 1.6 | Test against existing scraping data in `outputs/scraping/` | manual | 1h |
| 1.7 | Update ADR-001 status → Accepted | `docs/adr/ADR-001-*.md` | 15min |

### Schema Draft

```python
class ClaimType(str, Enum):
    FACTUAL = "factual"
    ARGUMENTATIVE = "argumentative"
    DESCRIPTIVE = "descriptive"

class ItemAnalysis(BaseModel):
    canonical_claim: str          # Core assertion — PRIMARY EMBEDDING INPUT
    claim_type: ClaimType         # Semantic classification
    topic_tags: List[str]         # Topic labels
    sentiment: str                # Toward claim's subject
    key_actors: List[KeyActor]    # Reuses existing schema
    relevance_summary: str        # Political landscape context
    source_type: str              # "youtube" | "bluesky" | "news"
```

### Validation Checkpoint
- [ ] Each item in a scraped JSON produces one `ItemAnalysis`
- [ ] `canonical_claim` is concise and embeddable (1-2 sentences)
- [ ] `claim_type` correctly distinguishes factual from argumentative
- [ ] Existing cluster-level analysis (`YoutubeAnalysis`, etc.) is NOT removed

---

## Sprint 2 — Embeddings (~1 week)

> **Goal:** Embed `canonical_claim` from Sprint 1 output so items can be compared mathematically.  
> **Prerequisite:** Sprint 1 completed and validated.

### Tasks

| # | Task | Files | Effort |
|---|---|---|---|
| 2.1 | Add embedding function to `llm_configs/functions.py` | [MODIFY] | 2h |
| 2.2 | Choose embedding model: Gemini `text-embedding-004` or equivalent | Research | 1h |
| 2.3 | Build embedding orchestrator | `run_embeddings.py` [NEW] | 3h |
| 2.4 | Read per-item analysis, embed `canonical_claim`, save vectors | ↑ same file | ↑ included |
| 2.5 | Store embeddings as JSON (numpy arrays serialized) | `outputs/embeddings/` [NEW dir] | ↑ included |
| 2.6 | Add `numpy`, `scikit-learn` to `requirements.txt` | [MODIFY] | 15min |

### Validation Checkpoint
- [ ] Each `canonical_claim` produces a vector of consistent dimensionality
- [ ] Embedding results are persisted and loadable
- [ ] Semantically similar claims produce similar vectors (manual spot-check)

---

## Sprint 3 — Clustering & Narrative Inference (~1 week)

> **Goal:** Group similar claims across sources and generate narrative summaries per cluster.  
> **Prerequisite:** Sprint 2 completed.

### Tasks

| # | Task | Files | Effort |
|---|---|---|---|
| 3.1 | Implement K-Means or HDBSCAN clustering on embedding vectors | `run_clustering.py` [NEW] | 3h |
| 3.2 | Determine optimal k (Elbow method or silhouette) | ↑ same file | 1h |
| 3.3 | Create `NarrativeInference` Pydantic schema | `llm_configs/schemas/narrative_inference.py` [NEW] | 1h |
| 3.4 | Create narrative inference prompt (takes cluster of claims → narrative) | `llm_configs/prompts/narrative_inference.py` [NEW] | 2h |
| 3.5 | LLM call per cluster to generate narrative label + summary | ↑ same orchestrator | 2h |
| 3.6 | Save cluster results + narrative output | `outputs/clusters/` [NEW dir] | ↑ included |
| 3.7 | (Opcional) t-SNE visualization with Plotly | `run_clustering.py` | 2h |

### Validation Checkpoint
- [ ] Claims from different sources (YouTube + Bluesky + News) that express the same argument land in the same cluster
- [ ] Each cluster has a readable narrative summary
- [ ] Cluster count is reasonable (not 1 giant cluster, not N=items clusters)

---

## Sprint 4 — Simple Report / Dashboard (~1 week)

> **Goal:** Present the narrative intelligence in a consumable format.  
> **Prerequisite:** Sprint 3 completed.

### Tasks

| # | Task | Files | Effort |
|---|---|---|---|
| 4.1 | Build/update Streamlit `app.py` | `app.py` [NEW or MODIFY] | 4h |
| 4.2 | Tab 1: Scraping config + run trigger | ↑ | ↑ included |
| 4.3 | Tab 2: Per-item analysis results table | ↑ | ↑ included |
| 4.4 | Tab 3: Cluster visualization (t-SNE scatter plot) | ↑ | 2h |
| 4.5 | Tab 4: Narrative summaries per cluster | ↑ | ↑ included |
| 4.6 | Generate simple text report (Markdown or PDF) | `generate_report.py` [NEW] | 3h |

### Validation Checkpoint
- [ ] End-to-end flow works: Topic → Scrape → Item Analysis → Embed → Cluster → View Narratives
- [ ] A non-technical person can read the output and understand "what narratives are growing"
- [ ] The report is exportable

---

## What's Intentionally Deferred to v2

| Feature | Why Deferred |
|---|---|
| PostgreSQL / pgvector | No value until pipeline logic is proven |
| FastAPI / API routes | No external consumers yet |
| Redis / job queues | Processing is fast enough synchronously at MVP scale |
| Candidate model (themes, audiences, competitors) | Topic-based approach validates the core before adding candidate-scoping |
| Narrative Priority Index (NPI) scoring | Requires clustering data to score meaningfully |
| Strategic prompts (opportunity, competitor, ally, briefing) | Blocked until narratives exist |
| WhatsApp delivery | Blocked until briefing generation exists |
| Next.js frontend | Streamlit is sufficient for internal use |
| Instagram / TikTok / X connectors | YouTube + Bluesky + News cover enough sources for MVP |

---

## Timeline Summary

| Sprint | Duration | Output |
|---|---|---|
| **Sprint 1** | Week of Apr 1-7 | Per-item analysis with `canonical_claim` |
| **Sprint 2** | Week of Apr 8-14 | Embedding vectors for all claims |
| **Sprint 3** | Week of Apr 15-21 | Cross-source narrative clusters |
| **Sprint 4** | Week of Apr 22-28 | Streamlit dashboard + simple report |

**Total: ~4 weeks to end-to-end MVP.**

After Sprint 4, the team has a working intelligence engine that can demonstrate: *"Here are the top 5 political narratives from this week, detected across YouTube, Bluesky, and news — here's who's driving them and how they cluster."*
