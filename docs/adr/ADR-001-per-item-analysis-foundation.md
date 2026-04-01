# ADR-001: Per-Item Granular Analysis as the Pipeline Foundation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-03-31 |
| **Decision Makers** | Project lead |
| **Relates To** | `IMPLEMENTATION_STATUS.md` §3.1 (Intelligence Pipeline), §3.2 (Embedding Strategy) |

---

## Context

The current MVP pipeline processes scraped content at the **source-cluster level**: all YouTube videos for a topic are analyzed in a single LLM call, producing one `YoutubeAnalysis` object. Same for Bluesky posts and news articles.

This was the right choice for initial validation — it proved that:
- The scraping connectors produce usable data
- Gemini can produce structured, Pydantic-validated political analysis
- The prompt + schema pattern works reliably

However, the cluster-level approach **blocks the entire downstream pipeline** described in the target architecture:

1. **No embeddings are possible** — there is no discrete unit of text to embed. The LLM output is a summary, not a per-item claim.
2. **No cross-source clustering** — a YouTube video and a Bluesky post expressing the same argument cannot be grouped together because they are analyzed in separate, source-scoped calls.
3. **No argument tracking** — we cannot trace a narrative back to its constituent arguments and original content items.
4. **No temporal analysis** — we cannot track how a specific claim evolves across time because individual items are collapsed into cluster summaries.

The target architecture defines a 9-stage pipeline: `content → filter → argument extraction → embedding → clustering → narrative inference → scoring → recommendation → briefing`. The **first convergence step** toward this pipeline is to produce per-item structured output that can feed into embedding and clustering stages.

---

## Decision

**Adopt per-item granular LLM analysis as the foundational processing unit.**

Each individual content item (one YouTube video, one Bluesky post, one news article) will be analyzed independently by the LLM, producing a structured output that includes:

- **`canonical_claim`** — the core argument or assertion made by the content (1-2 sentences). This becomes the **primary embedding input** for downstream clustering.
- **`claim_type`** — classification as `factual` or `argumentative`, enabling semantically coherent embedding spaces.
- **`topic_tags`** — extracted topic labels for filtering and grouping.
- **`sentiment`** — sentiment toward the claim's subject.
- **`key_actors`** — actors mentioned or involved (reusing the existing `KeyActor` schema).
- **`source_context`** — source-specific metadata (engagement metrics, audience reception, etc.).

### What This Changes

| Dimension | Before (cluster-level) | After (per-item) |
|---|---|---|
| LLM call granularity | 1 call per source type per topic | 1 call per content item |
| Output structure | `YoutubeAnalysis` (summary of N videos) | `ItemAnalysis` (analysis of 1 item) |
| Embedding readiness | ❌ No discrete text to embed | ✅ `canonical_claim` is the embedding unit |
| Cross-source grouping | ❌ Source-siloed | ✅ All items share the same schema |
| Cost profile | Lower (fewer calls) | Higher (more calls, but smaller prompts) |

### What This Does NOT Change

- The existing cluster-level analysis (`YoutubeAnalysis`, `BlueskyAnalysis`, `NewsAnalysis`) is **not removed**. It remains available as an optional high-level summary mode.
- The scraping pipeline (`main.py`, `scraping/`) is untouched.
- The LLM infrastructure (`generate_gemini_json()`, `@measure_time`) is reused as-is.
- The file-based I/O convention (`outputs/`) is preserved.

---

## Implementation Approach

### New Files

```
llm_configs/
  schemas/
    item_analysis.py          # ItemAnalysis Pydantic model
  prompts/
    item_analysis.py          # Per-item system instruction + prompt builder

run_item_analysis.py          # Orchestrator: iterates items, calls LLM, saves results
```

### Schema Design (Draft)

```python
class ClaimType(str, Enum):
    FACTUAL = "factual"
    ARGUMENTATIVE = "argumentative"
    DESCRIPTIVE = "descriptive"

class ItemAnalysis(BaseModel):
    canonical_claim: str          # The core claim — PRIMARY EMBEDDING INPUT
    claim_type: ClaimType         # Factual vs. argumentative classification
    topic_tags: List[str]         # Topic labels (e.g., "public safety", "AI regulation")
    sentiment: str                # Sentiment toward the claim's subject
    key_actors: List[KeyActor]    # Actors involved (reuses existing schema)
    relevance_summary: str        # Why this item matters in the political landscape
    source_type: str              # "youtube" | "bluesky" | "news"
```

### Cost Mitigation

Per-item calls increase LLM usage. Mitigation strategies:
1. **Smaller prompts** — each call sends one item, not a full cluster. Input tokens per call drop significantly.
2. **Batching** — group 3-5 items per call where the schema supports it (future optimization).
3. **Pre-filtering** — skip items below an engagement threshold before calling the LLM.
4. **Caching** — store results keyed by content hash to avoid re-analyzing identical items.

---

## Consequences

### Positive
- Unlocks the entire downstream pipeline (embeddings → clustering → cross-source narrative detection)
- Creates the data granularity needed for temporal tracking
- Enables candidate-scoped relevance scoring per item
- Produces the `canonical_claim` field that was decided as the preferred embedding input (per `IMPLEMENTATION_STATUS.md` §3.2)
- Maintains a unified schema across all source types, enabling source-agnostic downstream processing

### Negative
- Higher LLM cost per analysis run (mitigated by smaller prompts and future batching)
- More files in `outputs/analysis/` (manageable at MVP scale)
- The cluster-level analytical richness (e.g., `audience_reception` comparing video vs. comments) is harder to capture at the item level — this is acceptable because it can be recovered as a secondary analysis pass over clusters

### Neutral
- No infrastructure changes required (still file-based, still synchronous, still Streamlit)
- No changes to the scraping pipeline

---

## Alternatives Considered

### Alternative 1: Jump directly to the full 9-stage pipeline
Rejected. Standing up argument extraction → embedding → clustering → narrative inference in one pass introduces too many untested components. Per-item analysis is the minimal first step that validates the data shape before adding embeddings.

### Alternative 2: Keep cluster-level analysis and add embeddings of the summary text
Rejected. Embedding a summary of 5 videos produces one vector per source type — not enough granularity for meaningful clustering. The embedding space needs per-item resolution to detect cross-source narrative convergence.

### Alternative 3: Hybrid — cluster analysis + per-item claim extraction in the same call
Considered but deferred. A single LLM call that returns both the cluster summary and per-item claims is possible but makes the prompt complex and the output schema harder to validate. Better to implement per-item analysis cleanly first, then consider hybrid calls as an optimization.
