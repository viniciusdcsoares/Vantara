# ADR-004: YouTube Anti-Bot Measures and Local Cookies

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-01 |
| **Decision Makers** | Project lead, Antigravity |
| **Relates To** | `scraping/youtube.py`, `IMPLEMENTATION_STATUS.md` §1.6 |

---

## Context

The YouTube extraction process, when scaling to multiple videos or frequent requests, is highly vulnerable to being flagged as bot activity. This leads to HTTP 429 (Too Many Requests) errors, IP bans, or the inability to fetch transcripts.
Additionally, some transcripts or comments are restricted, requiring authentication to access reliably or to bypass certain rate limits.

The goal is to make the YouTube connector (`scraping/youtube.py`) more robust, human-like, and persistent against detection.

---

## Decision

**Implement localized anti-bot measures and cookie-based authentication for the YouTube scraping pipeline.**

Specific implementations include:

1.  **Randomized Jitter/Delays**: Replace fixed pauses with random intervals (e.g., 3-7 seconds) between video metadata and transcript fetch attempts to mimic human browsing behavior.
2.  **Batch Processing & Interleaved Cooldowns**: Structure the extraction loop to process videos in small, non-deterministic batches. Critically, to protect IP reputation, extraction is interleaved with execution of Bluesky and NewsAPI requests, creating "natural cooldown periods" for the connection before hitting YouTube again.
3.  **Local Cookie Integration**: Support reading from a `youtube_cookies.txt` file (Netscape format) to initialize the `YouTubeTranscriptApi`. This allows the script to leverage an authenticated session, significantly reducing "not available" or rate-limit errors.
4.  **Circuit Breaker (429 Handling)**: Implement a mechanism to detect recurring IP blocks and gracefully halt execution rather than hammering the API, which could lead to permanent bans.
5.  **Strict Operational Quotas**: Discovered and implemented a hard operational threshold: the pipeline limits YouTube extractions to roughly 70 requests per IP per day (bursting to an absolute maximum of 120) to prevent shadowbans and 429 locks.

### What This Changes

| Feature | Before | After |
|---|---|---|
| Wait Intervals | Fixed or none | Randomized (3-10s range) |
| Authentication | Anonymous only | Local cookie support via `youtube_cookies.txt` |
| Robustness | High risk of IP blocking | Human-like behavior reduces detection risk |
| Error Handling | Basic try/except | Specific 429 detection and circuit breaking |

---

## Implementation Approach

### Key Code Updates (`scraping/youtube.py`)

- Use `random.uniform()` for delays.
- Integrate `cookies` parameter in `YouTubeTranscriptApi.get_transcript(video_id, cookies='youtube_cookies.txt')`.
- Add language hard-vote (already partially implemented) as a pre-filter before the more expensive transcript calls.

### Required Secrets/Files
- `youtube_cookies.txt` needs to be present in the repository root (added as a requirement for human review).

---

## Consequences

### Positive
- Much higher success rate for transcript extraction.
- Reduced likelihood of IP banning.
- Better "stealth" during mass extraction runs.

### Negative
- Slower scraping speed due to mandatory delays.
- Maintenance overhead: cookies expire and must be manually refreshed by the user.

### Neutral
- Still uses the same `youtube-transcript-api` library.
