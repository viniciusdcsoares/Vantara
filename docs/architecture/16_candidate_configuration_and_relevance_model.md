
# 16_candidate_configuration_and_relevance_model.md

## Purpose

Define how the platform models the **candidate’s political context** and how that context influences:

- source prioritization
- content relevance scoring
- narrative prioritization
- opportunity detection
- recommendation generation

Without this layer, the system becomes generic social listening.  
With it, the system becomes **strategic intelligence tailored to a specific campaign**.

---

# Core Principle

The platform must interpret political discourse **through the lens of the candidate’s strategy**.

Every narrative, argument, and piece of content must be evaluated relative to:

- the candidate’s priorities
- the candidate’s risks
- the candidate’s electorate
- the candidate’s positioning

This context feeds directly into the scoring models described in:

- narrative scoring model
- opportunity detection
- recommendation engine

---

# Candidate Configuration Structure

The candidate configuration model contains the following components.

```
Candidate Profile
↓
Political Positioning
↓
Strategic Themes
↓
Sensitive Topics
↓
Target Audiences
↓
Geographic Context
↓
Communication Style
```

---

# Candidate Profile

Basic structural information about the candidate.

Fields:

```
candidate_id
name
office_type
party
state
region
term_status (incumbent / challenger)
```

This information is used for:

- geographic relevance scoring
- competitor identification
- actor classification

---

# Political Positioning

Defines the ideological orientation of the candidate.

Example fields:

```
ideology_position
policy_orientation
economic_position
security_position
social_position
```

Example values:

```
conservative
liberal
progressive
libertarian
centrist
```

This positioning helps interpret narratives.

Example:

A “law and order” narrative may be positive for a conservative candidate but negative for a progressive one.

---

# Strategic Themes

Themes that the campaign wants to emphasize.

Example:

```
public safety
economic growth
entrepreneurship
tax reduction
education reform
healthcare access
```

Each theme has a weight.

Example:

```
theme_name
priority_weight
```

Example weights:

```
1.0 = core theme
0.7 = important
0.4 = secondary
```

Themes influence:

- narrative relevance score
- opportunity detection
- content recommendations

---

# Sensitive Topics

Topics where communication risk is high.

Examples:

```
abortion
religion
gun policy
immigration
identity politics
```
Sensitive topics may trigger:

- risk score adjustments
- caution in recommendations
- alert generation

Fields:

```
topic
sensitivity_level
handling_strategy
```

---

# Target Audiences

Defines the key voter groups the campaign wants to reach.

Examples:

```
small business owners
urban workers
middle class families
students
farmers
```
Fields:

```
audience_segment
priority_weight
key_concerns
```

Audience alignment influences the **relevance score of narratives**.

Example:

A narrative about fuel prices may strongly impact rural voters.

---

# Geographic Context

Defines the territorial scope of relevance.

Fields:

```
state
major_cities
regional_issues
local_topics
```

Geographic matching influences relevance scoring.

Example:

A narrative about flooding in a candidate’s state should score higher.

---

# Communication Style

Defines how the candidate typically communicates.

Examples:

```
institutional
combative
educational
community-focused
```
Also includes preferred formats:

```
short video
carousel
speech clip
policy explanation
interview
```

This influences the **recommendation engine**.

Example:

A candidate with a strong TikTok presence may receive more video recommendations.

---

# Competitor Mapping

The candidate configuration also stores competitor relationships.

Fields:

```
competitor_id
competitor_name
competitor_party
competitor_relevance_weight
```

Competitors influence:

- competitor dominance scoring
- alert generation
- contrast recommendations

---

# Ally Mapping

Allied actors are also stored.

Fields:

```
ally_id
ally_name
ally_role
alignment_strength
```

Allies influence:

- amplification suggestions
- narrative coalition analysis

---

# Source Prioritization

Candidate configuration influences which sources matter most.

Example weighting factors:

```
candidate accounts → highest priority
competitors → very high priority
allies → high priority
regional media → high priority
national media → medium priority
influencers → variable priority
```

This influences the **source selection model** described in the data collection strategy.

---

# Content Relevance Scoring

Each collected content item receives a candidate-specific relevance score.

Example formula:

```
Relevance Score =
(0.30 × theme_match)
+ (0.20 × actor_importance)
+ (0.15 × engagement_level)
+ (0.15 × growth_velocity)
+ (0.10 × geographic_match)
+ (0.10 × audience_match)
```

Where:

- theme_match → overlap with strategic themes
- actor_importance → influence of the author
- engagement_level → social traction
- growth_velocity → narrative acceleration
- geographic_match → relevance to region
- audience_match → relevance to target voters

---

# Narrative Prioritization

Narratives receive additional weighting when they align with candidate priorities.

Example:

```
narrative_priority =
base_priority_index × theme_priority_weight
```

This ensures the system highlights narratives that matter most for the campaign.

---

# Opportunity Detection

Candidate configuration strongly influences opportunity scoring.

Example:

```
Opportunity Score =
(0.35 × candidate_relevance)
+ (0.30 × narrative_growth)
+ (0.20 × engagement)
+ (0.15 × actor_diversity)
```

Where candidate_relevance is derived from:

- theme match
- audience alignment
- geographic relevance

---

# Recommendation Personalization

Content recommendations must respect the candidate’s configuration.

Examples:

A candidate with a policy-focused profile may receive:

- explanatory videos
- policy breakdowns

A candidate with a populist style may receive:

- reaction videos
- direct commentary posts

---

# Configuration Governance

Candidate configuration should be editable only by:

- system admins
- campaign managers

Clients should not have unrestricted prompt editing.

Changes must be logged for auditing.

Fields to track:

```
updated_by
updated_at
change_reason
```

---

# Final Principle

The candidate configuration model ensures that:

The platform does not merely detect narratives.

It detects **which narratives matter for this specific campaign**.

This layer transforms the platform from:

generic monitoring

into

strategic political intelligence.
