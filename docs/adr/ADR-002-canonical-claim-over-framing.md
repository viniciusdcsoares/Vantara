# ADR-002: Canonical Claim as Primary Embedding Input (Framing Deprecated)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-03-31 |
| **Relates To** | ADR-001, DIVERGENCE_LOG DIV-005/DIV-006 |

---

## Context

The target architecture documents describe embedding "arguments" for cross-source clustering. Two candidates for the embedding input were considered:

1. **`canonical_claim`** — the core factual/argumentative assertion made by the content
2. **`framing`** — how the content frames or positions the issue (e.g., "alarmist", "economic opportunity")

Embedding both creates a multi-dimensional space that is hard to cluster meaningfully. A single, clean semantic dimension produces better cluster coherence.

## Decision

**`canonical_claim` is the primary and only embedding input.**

- Framing may still be extracted by Gemini prompts for display/analysis purposes
- Framing will **not** be used as a clustering dimension
- The embedding space will contain one vector per content item, representing "what claim is being made"

## Consequences

- **Positive:** Cleaner embedding space. Cross-source grouping works on shared assertions, not on shared editorial tone.
- **Negative:** We lose the ability to cluster by framing strategy — acceptable because framing is better analyzed *within* a cluster, not used *to form* clusters.
- **Neutral:** No code changes yet (embeddings not implemented). This ADR pre-constrains the embedding design for when ADR-001 is implemented.
