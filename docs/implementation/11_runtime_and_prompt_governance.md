
# 11_runtime_and_prompt_governance.md

## Purpose

Define how the platform executes AI agents, manages prompts, protects secrets, and governs runtime behavior.

This document exists to prevent operational chaos in an AI‑coding‑first system and ensure:

- predictable AI execution
- safe credential handling
- controlled prompt evolution
- platform security
- traceable outputs
- zero prompt drift across clients

This document should be treated as the **operational governance layer of the AI runtime**.

---

# 1. AI Agent Runtime Model

The platform does **not use autonomous AI agents**.

Instead, agents are implemented as:

**Jobs + Services + Prompts + Context Data**

Each “agent” is a deterministic orchestration pipeline.

Example:

```
build_daily_briefing
    ↓
collect narratives
collect performance insights
collect competitor alerts
collect opportunities
    ↓
assemble context
    ↓
run prompt
    ↓
store structured output
    ↓
optional delivery
```

This model ensures:

- debuggability
- reproducibility
- lower cost
- predictable system behavior

---

# 2. Types of Agent Activation

Agents can be triggered in three ways.

## 2.1 Scheduled Execution (Cron)

Used for recurring intelligence generation.

Examples:

- narrative updates every 3 hours
- social performance insights every 6 hours
- daily briefing every morning
- competitor analysis every 3 hours

Scheduled execution is defined in:

`09_jobs_and_crons.md`

---

## 2.2 Event‑Driven Execution

Triggered when signals exceed thresholds.

Examples:

- narrative growth rate spike
- competitor dominating a narrative
- high engagement post by competitor
- emerging topic aligned with candidate themes

Example:

```
if narrative_growth_rate > threshold:
    generate_strategic_alert()
```

---

## 2.3 Manual Execution (Admin Trigger)

Admin panel allows manual triggering for:

- testing
- debugging
- demonstrations
- reprocessing data
- recalculating insights

Examples:

- regenerate briefing
- rerun narrative clustering
- test prompt with candidate context

Manual triggers are essential for MVP operations.

---

# 3. Prompt Architecture

Prompts are treated as **versioned system assets**, not ad‑hoc text blobs.

Prompt storage is structured as:

```
/prompts
    narrative_detection.md
    narrative_cluster_summary.md
    strategic_opportunity.md
    content_recommendation.md
    competitor_risk.md
    ally_amplification.md
    missed_opportunity.md
    daily_briefing.md
```

Each prompt file includes metadata.

Example structure:

```
name: strategic_opportunity
version: v1
purpose: detect candidate opportunity from narrative signals

input_contract:
    narratives
    candidate_profile
    theme_priorities

output_contract:
    opportunity_summary
    reasoning
    urgency_level
```

---

# 4. Prompt Versioning

Every AI output should record:

- prompt_name
- prompt_version
- generation_timestamp
- candidate_id
- job_id

Example stored metadata:

```
prompt_name: strategic_opportunity
prompt_version: v1
generated_at: 2026-03-20T10:30:22
job_id: job_8821
```

This guarantees:

- traceability
- reproducibility
- easier debugging
- safe iteration

---

# 5. Admin Prompt Editing Policy

Prompts **can be edited by internal admins**, but not by clients.

Admin editing is subject to guardrails.

## Editable Areas

Admins may modify:

- phrasing improvements
- tone adjustments
- output structure hints
- reasoning instructions
- verbosity

## Non‑Editable Foundations

Admins should not change:

- input schema
- output schema
- structural reasoning logic
- safety constraints

If those change, a **new prompt version must be created**.

---

# 6. Prompt Editing Workflow

When admins edit prompts:

1. clone existing version
2. increment version number
3. test prompt in staging
4. validate outputs
5. deploy

Example:

```
strategic_opportunity.v1
strategic_opportunity.v2
```

Production jobs always reference a specific version.

---

# 7. Prompt Drift Prevention

Prompt drift is dangerous in AI‑driven systems.

To prevent drift:

- prompt versions must be recorded
- prompts must be stored centrally
- no prompts inside random code files
- no client‑side prompt manipulation
- no runtime prompt mutation by agents

All prompts must originate from the `/prompts` directory.

---

# 8. Prompt Parameterization

Prompts receive context parameters instead of editing prompt text.

Example variables:

```
candidate_name
priority_themes
sensitive_topics
tone_preference
platform_focus
time_window
```

Example template:

```
Candidate: {candidate_name}

Priority themes:
{priority_themes}

Sensitive topics to avoid:
{sensitive_topics}
```

This allows flexible behavior without altering core prompt logic.

---

# 9. Secret Management

Secrets include:

- OpenAI API key
- Apify token
- YouTube API key
- Twilio token
- database credentials
- JWT secret

Secrets **must never be exposed to frontend code**.

---

## 9.1 MVP Secret Storage

Secrets stored as environment variables.

Example:

```
OPENAI_API_KEY
APIFY_TOKEN
YOUTUBE_API_KEY
TWILIO_AUTH_TOKEN
JWT_SECRET
```

Local development uses `.env` files (ignored by git).

---

## 9.2 Production Secret Handling

Production environments must use:

- environment variables
- platform secret managers
- restricted access

Recommended options:

- AWS Secrets Manager
- Doppler
- Railway secrets
- Render secrets

---

## 9.3 Secret Exposure Prevention

The system must ensure:

- no tokens in frontend code
- no tokens in logs
- no tokens in database unless encrypted
- no tokens committed to git

If a secret leaks, it must be rotated immediately.

---

# 10. Token Access Model

Tokens should only be accessed inside backend connectors.

Example:

```
/app/connectors/youtube_connector.py
/app/connectors/apify_connector.py
```

Front‑end never communicates directly with providers.

Frontend → Backend → Provider

---

# 11. Runtime Observability

Each AI job must record:

- start_time
- end_time
- candidate_scope
- items_processed
- output_records
- error_reason (if failure)

This enables operational dashboards for:

- failed jobs
- stale data
- connector failures
- messaging failures

---

# 12. AI Cost Control

AI usage must remain predictable.

Strategies:

- batch processing where possible
- avoid repeated prompt calls
- reuse embeddings
- cache narrative clusters
- limit prompt input size

AI jobs should never run inside tight loops.

---

# 13. Fail‑Safe Behavior

If AI generation fails:

- job retries up to defined limit
- fallback summary may be generated
- system logs error
- platform continues operating

AI failures should **never crash the pipeline**.

---

# 14. Testing AI Outputs

Testing focuses on:

- output schema validity
- presence of required fields
- acceptable length ranges
- JSON parseability
- no hallucinated fields

The system validates outputs before storing them.

---

# 15. Admin Control Panel Capabilities

Admin interface should allow:

- prompt editing
- job triggering
- connector health monitoring
- briefing regeneration
- candidate configuration edits
- source sync control

Clients do not receive prompt editing access.

---

# 16. Strategic Governance Principle

AI should assist decision making, not obscure it.

The platform must always allow operators to answer:

- why this recommendation was generated
- which narrative triggered this insight
- which actors influenced this conclusion
- which prompt version produced this output

Transparency builds trust in the intelligence layer.

---

# Conclusion

The runtime architecture prioritizes:

- deterministic pipelines
- safe prompt evolution
- strong secret management
- controlled AI execution
- operational transparency

This ensures the system remains stable while still leveraging AI as a strategic engine.
