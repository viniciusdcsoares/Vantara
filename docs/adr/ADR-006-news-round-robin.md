# ADR-006: Round-Robin Source Distribution (NewsAPI)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-09 |
| **Relates To** | `scraping/news.py`, `IMPLEMENTATION_STATUS.md` |

---

## Context

When querying NewsAPI, standard relevance or chronological sorting often results in a massive overlap of articles originating from a single high-output portal (e.g., heavily weighting "Globo" or "UOL" over other regional outlets). Previously, a strict filter of "max 1 article per news outlet" was implemented to force diversity, but this created a "glass ceiling" where it was mathematically impossible to hit the requested `max_articles` volume if the number of unique outlets available was smaller than the `max_articles` requested.

## Decision

**Implement a Round-Robin distribution algorithm for News extraction.**

Instead of blindly taking the top `N` articles or strictly discarding duplicates, the News scraper now:
1. Groups all fetched candidate articles by their source domain (outlet).
2. Iterates through the sources in a circular Round-Robin fashion, pulling exactly one article from each source per cycle.
3. Continues looping until the user-defined `max_articles` quota is met or the candidate pool is fully exhausted.

## Consequences

### Positive
- **Guaranteed Diversity:** Prevents monopolization of the narrative by high-volume news aggregators.
- **Volume Fulfillment:** Eliminates the arbitrary "glass ceiling", allowing multiple articles from the same source *only* if required to meet the total sample size requested, while still keeping their distribution equitable.
- Increases the semantic richness of the resulting data for LLM analysis.

### Negative
- Slightly higher memory overhead in Python to group and partition the initial payload.
