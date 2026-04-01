# 07_narrative_graph_architecture.md

## Purpose

Define the Narrative Graph architecture for the platform.

This is one of the most strategic layers of the system because it transforms the product from a social listening dashboard into a narrative intelligence platform.

The Narrative Graph should support both:
- Vantara: political communication intelligence
- Paradoxa: global discourse and narrative mapping

Its function is to represent how narratives emerge, spread, evolve, conflict, and get amplified across actors, platforms, and time.

---

## Core Concept

The Narrative Graph models discourse as a graph made of:

1. actors
2. content nodes
3. narratives
4. relationships between them

Instead of treating content as isolated posts, the system understands content as part of a larger narrative structure.

---

## Main Node Types

### 1. Actors

Actors are entities that participate in discourse.

Examples:
- politicians
- journalists
- influencers
- media outlets
- institutions
- think tanks
- public channels
- allied candidates
- competitor candidates

Suggested table:
`actors`

Suggested fields:
- id
- name
- actor_type
- platform_primary
- affiliation
- influence_score
- active

Possible actor_type values:
- politician
- journalist
- influencer
- media
- institution
- channel
- analyst
- campaign
- unknown

---

### 2. Content Nodes

Each content item becomes a discourse node.

Examples:
- YouTube video
- Instagram reel
- TikTok video
- tweet
- news article
- post
- thread

This reuses the existing:
`content_items`

Important additional traits:
- author_actor_id
- narrative_relevance_score
- discourse_role_hint

---

### 3. Narrative Nodes

Narratives are clustered discourse objects.

A narrative is not just a topic.
It is a meaningful discourse formation with direction and framing.

Examples:
- crime is increasing in major cities
- tax reform harms small business
- inflation is hurting working families
- public safety requires stronger policing
- AI regulation will slow innovation

Suggested table:
`narratives`

Suggested fields:
- id
- topic_name
- narrative_summary
- dominant_position
- volume_score
- growth_rate
- risk_score
- opportunity_score
- created_at
- updated_at

---

## Main Edge Types

### 1. Actor → Content

Represents authorship or publication.

Suggested relation:
`actor_content_edges`

Fields:
- id
- actor_id
- content_item_id
- relation_type
- created_at

Typical relation_type:
- authored
- published
- reposted
- quoted

---

### 2. Content → Narrative

Represents narrative membership.

Suggested relation:
`content_narrative_edges`

Fields:
- id
- content_item_id
- narrative_id
- confidence
- primary_membership
- created_at

This allows the system to map content to one or more narratives.

---

### 3. Actor → Narrative

Represents the actor's role in the narrative.

Suggested relation:
`actor_narrative_edges`

Fields:
- id
- actor_id
- narrative_id
- role_type
- contribution_score
- created_at

Possible role_type values:
- originator
- amplifier
- responder
- critic
- counter_narrative
- observer
- ally_amplifier
- competitor_dominator

This is one of the most important relations in the entire graph.

---

### 4. Narrative → Narrative

Represents relationships between discourse structures.

Suggested relation:
`narrative_relations`

Fields:
- id
- source_narrative_id
- target_narrative_id
- relation_type
- confidence
- created_at

Possible relation_type values:
- supports
- contradicts
- evolves_from
- amplifies
- fragments
- competes_with

---

## Optional Edge Types for Later

### Actor → Actor
Influence, reaction, co-amplification, opposition

### Content → Content
Replies, references, same-event linkage

These can be added later, not required for the MVP.

---

## Why the Graph Matters

Without the Narrative Graph, the system mostly answers:
- what is being said
- what is trending
- what performed well

With the graph, the system can answer:
- who started a narrative
- who amplified it
- how it spread
- which actors dominate it
- which counter-narratives emerged
- how the discourse evolved over time
- whether a competitor captured the narrative
- whether an ally is strengthening the same narrative

This is what turns the product into true narrative intelligence.

---

## Narrative Graph for Political Use Cases

For Vantara, the graph enables:

### 1. Narrative origin detection
Who first pushed a message or frame?

### 2. Narrative amplification mapping
Which journalists, influencers, media pages, or politicians are amplifying it?

### 3. Competitive dominance detection
Is a competitor becoming the dominant political voice on this narrative?

### 4. Ally reinforcement detection
Are allies already supporting the same discourse cluster?

### 5. Counter-narrative detection
Is there a strong response forming against the current dominant frame?

### 6. Strategic urgency
Should the candidate answer now, ignore, or reinforce?

---

## Narrative Graph for Paradoxa

For Paradoxa, the same graph generalizes to:

- intellectual discourse
- ideology spread
- media framing
- topic polarization
- narrative ecosystems
- argument clusters

This is why the graph architecture should be general and not overly campaign-specific.

---

## MVP Graph Scope

Do not overengineer the graph at first.

The MVP only needs:

### Node types
- actors
- content_items
- narratives

### Edge types
- actor_content_edges
- content_narrative_edges
- actor_narrative_edges
- narrative_relations

That is enough to provide a very strong strategic layer.

---

## Storage Strategy

For the MVP, store the graph in relational tables inside PostgreSQL.

This is simpler and faster than adopting a dedicated graph database too early.

Recommended stack:
- PostgreSQL
- pgvector for similarity
- relational edge tables for graph traversal logic

Later, if needed, the graph can be migrated or mirrored into:
- Neo4j
- Memgraph
- another graph-oriented layer

But this is unnecessary for the first version.

---

## Graph Construction Pipeline

### Step 1 — Content ingestion
New content arrives from connectors.

### Step 2 — Actor resolution
The system resolves or creates the actor entity for the content author.

### Step 3 — Topic tagging
The content gets one or more candidate topics.

### Step 4 — Embedding and clustering
The content is embedded and matched into narrative clusters.

### Step 5 — Narrative assignment
The content is linked to one or more narratives.

### Step 6 — Actor role inference
The system infers whether the actor is:
- originating
- amplifying
- responding
- criticizing
- dominating
- countering

### Step 7 — Narrative relation inference
The system infers whether narratives:
- reinforce each other
- contradict each other
- evolved from another narrative
- are competing for the same topic space

### Step 8 — Graph update
Edges and scores are updated incrementally.

---

## Actor Resolution

The graph depends heavily on actor identity.

The system should maintain an `actors` table and try to resolve each content author into a stable actor identity.

### Inputs for actor resolution
- platform handle
- source URL
- normalized name
- account type
- known affiliation
- candidate / ally / competitor mapping

### Rules
- known candidate-related actors should be seeded manually
- media/influencer actors can be resolved semi-automatically
- ambiguous actors can remain unresolved initially

---

## Role Inference

This is a critical layer.

The graph should infer the role of an actor in a narrative.

### Inputs
- content semantics
- timing
- prior participation in the narrative
- engagement level
- narrative cluster membership

### Example role logic
- first high-signal participant → possible originator
- high-volume reposting/commentary → amplifier
- explicit opposition to main frame → critic or counter_narrative
- candidate rival dominating same topic → competitor_dominator

The initial version can rely on:
- heuristic rules
- prompt-based classification
- score thresholds

---

## Narrative Relation Inference

Narratives should not be treated as isolated.

Examples:
- one narrative may support another
- one narrative may emerge as a counter
- one narrative may fragment a broader one

### Inputs
- semantic similarity
- position difference
- temporal co-evolution
- actor overlap
- explicit opposition language

### Example relations
- “tax reform hurts small business” contradicts “tax reform stimulates investment”
- “crime in cities is rising” supports “public safety requires stronger policing”

---

## Scoring

The graph becomes much more useful with scores.

### Narrative-level scores
- volume_score
- growth_rate
- risk_score
- opportunity_score
- dominance_score

### Actor-level scores
- influence_score
- narrative_contribution_score
- amplification_score
- originality_score

### Edge-level scores
- confidence
- contribution_weight
- narrative_membership_strength

These scores do not need to be perfect in the MVP.
They need to be directionally useful.

---

## Time Dimension

The graph must be time-aware.

This is essential.

A narrative graph without time becomes much less valuable.

### Recommended fields
- created_at
- updated_at
- window_start
- window_end
- first_seen_at
- last_seen_at

This allows the system to answer:
- what emerged today
- what accelerated this week
- what is fading
- when a competitor took over a narrative

---

## Example MVP Queries

Once the graph exists, the system can answer queries like:

### Political examples
- Which narratives are growing around public safety in the last 48 hours?
- Which competitor is dominating the inflation narrative?
- Which allies are amplifying our preferred themes?
- Which missed narratives match our strongest engagement topics?

### Paradoxa examples
- Which creators dominate the AI regulation debate?
- What counter-narratives emerged against the dominant open-source AI discourse?
- Which arguments are amplifying each other?

---

## Dashboard Applications

The graph should power dashboard modules such as:

### Narrative Radar
List of active narratives and their growth.

### Narrative Flow
How a narrative moved across platforms and actors.

### Competitor Map
Which competitor is most active in which narrative.

### Ally Map
Which allies are reinforcing aligned discourse.

### Narrative Capture Alert
When a narrative relevant to the candidate is being captured by another actor.

### Cross-Platform Propagation
How discourse moved from TikTok to X to YouTube to news.

---

## WhatsApp / Briefing Applications

The graph should also power message outputs such as:

- “Competitor X is becoming the dominant voice on narrative Y”
- “Narrative Z emerged first in journalist accounts and is now being amplified by allied pages”
- “You have not posted on narrative A, which now overlaps with your highest-performing theme”
- “Counter-narrative B is gaining strength and may require positioning”

These are high-value outputs.

---

## AI Requirements

The graph depends on AI but should not become AI-chaotic.

Recommended AI tasks:
- topic extraction
- narrative summary
- actor role classification
- narrative relation classification
- narrative risk/opportunity scoring assistance

Keep the following outside the LLM whenever possible:
- scheduling
- storage
- base graph structure
- simple scoring
- deduplication
- author resolution heuristics

---

## Operational Recommendation

Treat the Narrative Graph as a first-class platform layer.

Do not leave it as an optional future enhancement.

Even if the MVP only implements a simple version, the data model and job architecture should already account for it.

This prevents painful rework later.

---

## Strategic Conclusion

The Narrative Graph is one of the most important assets of the entire platform.

For Vantara, it turns campaign monitoring into strategic narrative intelligence.

For Paradoxa, it becomes the backbone of a global map of discourse.

This means the graph should be treated not as a feature, but as a foundational system.
