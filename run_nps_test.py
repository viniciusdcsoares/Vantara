"""
run_nps_test.py
───────────────
Runs the full NPS pipeline on exactly ONE YouTube video from the latest
scraping file and pretty-prints the results.

Usage:
    python run_nps_test.py
"""

import json
import os
import sys
import textwrap
from pathlib import Path

# ── make sure project root is importable ──────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from google import genai
from llm_configs.functions import generate_gemini_json
from llm_configs.prompts.narrative_detection import (
    create_youtube_single_prompt,
    create_comment_alignment_prompt,
    system_instruction_youtube,
    system_instruction_comment_alignment,
)
from llm_configs.schemas.narrative_detection import (
    YoutubeAnalysis,
    CommentAnalysis,
    EngagementMetrics,
)

# ── load API key ───────────────────────────────────────────────────────────────
try:
    import toml  # type: ignore
    _secrets = toml.load(ROOT / ".streamlit" / "secrets.toml")
    API_KEY = _secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not API_KEY:
    sys.exit("[ERROR] GEMINI_API_KEY not found. Set it in .streamlit/secrets.toml or as env var.")

client = genai.Client(api_key=API_KEY)

# ── pick the scraping file ─────────────────────────────────────────────────────
scraping_dir = ROOT / "outputs" / "scraping"
files = sorted(scraping_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
if not files:
    sys.exit("[ERROR] No scraping files found in outputs/scraping/")

target_file = files[0]
print(f"\n📂  Scraping file : {target_file.name}")

with open(target_file, encoding="utf-8") as f:
    data = json.load(f)

videos = (data.get("youtube_data") or {}).get("videos", [])
if not videos:
    sys.exit("[ERROR] No YouTube videos in this scraping file.")

# take only the first video
video = videos[0]
topic = (
    (data.get("youtube_data") or {})
    .get("youtube_clipping_metadata", {})
    .get("searched_topic", "Unknown")
)

print(f"🎬  Video         : {video.get('title', 'N/A')}")
print(f"📺  Channel       : {video.get('channel', 'N/A')}")
stats = video.get("statistics", {})
print(f"📊  Stats         : views={stats.get('views',0):,}  likes={stats.get('likes',0):,}  comments={stats.get('total_comments',0):,}")
raw_comments = video.get("most_liked_comments", [])
print(f"💬  Top comments  : {len(raw_comments)}\n")

# ── STEP 1 — main narrative analysis ──────────────────────────────────────────
print("=" * 60)
print("STEP 1 · Narrative Analysis (YoutubeAnalysis)")
print("=" * 60)

prompt = create_youtube_single_prompt(video, topic)
result = generate_gemini_json(
    client=client,
    user_prompt=prompt,
    system_instruction=system_instruction_youtube,
    pydantic_schema=YoutubeAnalysis,
)

output = result.get("result", {}).get("output", {})
if hasattr(output, "model_dump"):
    output = output.model_dump()

core_narrative  = output.get("core_narrative", "")
canonical_claim = output.get("canonical_claim", "")
stance_score    = output.get("stance_score", 0.0)
tone_score      = output.get("tone_score", 0.0)

print(f"\n  core_narrative  : {textwrap.fill(core_narrative,  width=72, subsequent_indent='                    ')}")
print(f"  canonical_claim : {textwrap.fill(canonical_claim, width=72, subsequent_indent='                    ')}")
print(f"  stance_score    : {stance_score}")
print(f"  tone_score      : {tone_score}")

# ── STEP 2 — comment alignment (new LLM prompt) ────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 · Comment Alignment Prompt → LLM → alignment[]")
print("=" * 60)

alignments: list[float] = []
if raw_comments and core_narrative:
    alignment_prompt = create_comment_alignment_prompt(raw_comments, core_narrative)
    print(f"\n  Prompt sent (first 400 chars):\n  {alignment_prompt[:400]!r}\n")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config={
            "system_instruction": system_instruction_comment_alignment,
            "response_mime_type": "application/json",
        },
        contents=alignment_prompt,
    )
    alignments = json.loads(response.text)
    print(f"  Raw LLM response : {response.text}")
    print(f"  Parsed floats    : {alignments}")
else:
    print("  (no comments or no core_narrative — skipping alignment step)")

# ── STEP 3 — build List[CommentAnalysis] ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 · Inject scraper likes → List[CommentAnalysis]")
print("=" * 60)

top_comments: list[CommentAnalysis] = []
for raw_c, alignment in zip(raw_comments, alignments):
    likes     = int(raw_c.get("likes", 0))
    alignment = max(-1.0, min(1.0, float(alignment)))
    ca = CommentAnalysis(likes=likes, alignment=alignment)
    top_comments.append(ca)
    print(f"  likes={likes:>5}  alignment={alignment:+.2f}  text={raw_c.get('text','')[:60]!r}")

# ── STEP 4 — EngagementMetrics → all 5 NPS fields ─────────────────────────────
print("\n" + "=" * 60)
print("STEP 4 · EngagementMetrics → 5 NPS computed fields")
print("=" * 60)

metrics = EngagementMetrics(
    platform="youtube",
    views=stats.get("views", 0),
    post_likes=stats.get("likes", 0),
    reposts=0,
    total_comments=stats.get("total_comments", 0),
    top_comments=top_comments,
)

print(f"\n  stage_level             : {metrics.stage_level:.4f}")
print(f"  passive_force           : {metrics.passive_force:.4f}")
print(f"  directional_juice       : {metrics.directional_juice:.4f}")
print(f"  active_force            : {metrics.active_force:.4f}")
print(f"  narrative_power_score   : {metrics.narrative_power_score:.4f}")

print("\n✅  Pipeline complete.\n")
