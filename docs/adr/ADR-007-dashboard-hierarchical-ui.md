# ADR-007: Hierarchical Dashboard and History Auto-Load

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-09 |
| **Relates To** | `app.py`, `IMPLEMENTATION_STATUS.md` |

---

## Context

With the introduction of the Mixed Dataset and Hierarchical Clustering (ADR-005), the Streamlit MVP Dashboard (`app.py`) could no longer efficiently display all data points on a single flat Scatter Plot. Dense areas became visually muddy, and users couldn't separate macro themes from micro biases cleanly. Additionally, previously, users were forced to run the pipeline to populate the UI.

## Decision

**Re-architect the Streamlit Cluster UI to support Drill-down (Zoom In/Out) and enable auto-loading of historical runs.**

Specific implementations include:
1. **Auto-Load History:** The dashboard now reads directly from `outputs/clusters/` on initialization, plotting historical executions without requiring a live run.
2. **Dynamic UI Detection:** The system detects if the data structure contains `micro_cluster` columns indicating a hierarchical run.
3. **Macro View (Bubble Chart):** By default, the main map groups all data points into their parent Macro Clusters. It plots the exact centroid (mathematical mean of X and Y coordinate stances) with the bubble `size` tied to the total number of segments representing that theme.
4. **Micro View (Drill-down):** A dropdown control overrides the view, filtering the dataset to a single chosen Macro Cluster. The chart responds by fragmenting the bubble into its constituent points, re-coloring them by their Micro Cluster identifiers, and dynamically altering hover text to show sub-group metrics.

## Consequences

### Positive
- Tremendously improves UI performance by reducing DOM rendering nodes on the Macro view.
- Provides an intuitive, analytical user experience ("Tell me the big picture, then let me zoom in").
- Historic state restoration streamlines iteration speed.

### Negative
- Increased complexity in Plotly rendering loops and pandas `groupby` logic directly tied to the frontend script.
