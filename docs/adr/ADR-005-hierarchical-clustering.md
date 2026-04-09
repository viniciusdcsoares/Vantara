# ADR-005: Hierarchical Clustering (Zoom In / Zoom Out)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-09 |
| **Relates To** | `run_clustering.py`, `IMPLEMENTATION_STATUS.md` |

---

## Context

As the volume of extracted narratives scaled across multiple topics, running flat analysis per topic failed to identify overarching, cross-topic themes. We needed a mechanism to discover "Macro" narratives encompassing multiple scraping topics, while retaining the ability to drill down into specific "Micro" biases or specific arguments within those larger themes.

## Decision

**Implement a two-layer "Zoom In / Zoom Out" hierarchical clustering architecture.**

Specific implementations include:
1. **Mixed Dataset Aggregation:** Before clustering, the pipeline now aggregates the most recently processed JSON artifacts from **all** available topics in `outputs/analysis/`, generating a consolidated `mixed_clusters` dataset.
2. **Layer 1 (Macro Clusters):** The entire mixed dataset is grouped using UMAP for dimensionality reduction and HDBSCAN for density clustering. The LLM evaluates a sample (medoids) of each resulting cluster to name the overarching theme.
3. **Layer 2 (Micro Clusters):** The pipeline iterates over every valid Macro cluster, isolating its specific embeddings, and runs them through HDBSCAN **again** to find sub-groups representing nuanced stances. The LLM names these specific biases independently.

### Important Engineering Constraint (Hyperparameters)
**We explicitly decided to keep the HDBSCAN hyperparameters (`min_cluster_size` and `min_samples`) completely identical across both Layer 1 and Layer 2.**

*Rationale:* Theoretically, running HDBSCAN on a much smaller subset (the Micro layer) requires lowering the minimum cluster size to prevent the algorithm from discarding valid groups as noise (-1). However, we opted to lock the hyperparameters mathematically to prioritize strict semantic purity. Rather than forcing the algorithm to find minor overlapping sub-clusters by aggressively lowering thresholds, we rely on the robustness of the `gemini-embedding-001` vectors and the initial UMAP projection.

## Consequences

### Positive
- Clearly identifies overarching narratives that span multiple user searches.
- Allows highly specific breakdown of biases without losing the big picture.
- Automates the hierarchical labeling via LLM in a single execution.

### Negative
- Slower execution time due to performing clustering and LLM inference twice scaling exponentially with the number of macro clusters.
- The strict hyperparameter rule results in a higher volume of "Local Noise" (-1) in the Micro layer, as small factions of 1 or 2 items are deliberately discarded.
