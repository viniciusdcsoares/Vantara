import yt_dlp
import requests
import traceback
import os
import sys
import json
import time
import random
import urllib.request
from datetime import datetime, timedelta, timezone

from logger_configs import setup_logger
logger = setup_logger("scraping")

import streamlit as st

# ==========================================
# ANTI-BOT CONFIGURATION (edit freely)
# ==========================================
# Batch size range: each cycle processes a random number of videos between X and Y
BATCH_MIN_VIDEOS = 2         # X – minimum videos per batch
BATCH_MAX_VIDEOS = 5         # Y – maximum videos per batch

# Intra-video jitter: pause between videos INSIDE the same batch (seconds)
JITTER_MIN_SECONDS = 5.0 #6.0     # A
JITTER_MAX_SECONDS = 12.0 #14.0    # B

# Inter-batch cooldown: long pause BETWEEN batches (seconds)
COOLDOWN_MIN_SECONDS = 30.0  # C
COOLDOWN_MAX_SECONDS = 60.0  # D

# Path to the local YouTube cookies file
YOUTUBE_COOKIES_PATH = "youtube_cookies.txt"

from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound

# ### MODIFICATION: Importing libraries for Hard Vote
from langdetect import detect
import fasttext
from lingua import Language, LanguageDetectorBuilder

# ==========================================
# 1. LANGUAGE MODELS SETUP (Hard Vote)
# ==========================================
logger.info("Loading language models...")
languages = [Language.ENGLISH, Language.PORTUGUESE, Language.SPANISH, Language.CROATIAN]
lingua_detector = LanguageDetectorBuilder.from_languages(*languages).build()

model_path = "lid.176.ftz"
model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
if not os.path.exists(model_path):
    logger.info("Downloading FastText model (~900KB)...")
    urllib.request.urlretrieve(model_url, model_path)
fasttext_model = fasttext.load_model(model_path)
logger.info("Language models ready!")

# ==========================================
# 2. YOUTUBE API SETUP
# ==========================================
API_KEY = st.secrets['YOUTUBE_API_KEY']
youtube_service = build("youtube", "v3", developerKey=API_KEY)

# ### MODIFICATION: Helper function to handle and format dates
def format_br_date(iso_date, convert_to_local=True):
    try:
        # YouTube always delivers in UTC (Z at the end)
        dt = datetime.strptime(iso_date.replace('.000Z', 'Z'), "%Y-%m-%dT%H:%M:%SZ")
        
        if convert_to_local:
            # Subtract 3 hours to convert from UTC to Brasilia time
            dt = dt - timedelta(hours=3)
            
        return dt.strftime("%d/%m/%Y - %H:%M")
    except Exception:
        return iso_date

# ==========================================
# 3. EXTRACTION FUNCTIONS
# ==========================================
def fetch_recent_videos(topic, max_results=3, min_views=500, days=7):
    past_date = datetime.now(timezone.utc) - timedelta(days=days)
    formatted_date = past_date.isoformat().replace('+00:00', 'Z')

    found_videos = []
    page_token = None

    while len(found_videos) < max_results:
        request = youtube_service.search().list(
            q=topic,
            part="snippet",
            type="video",
            order="relevance",
            publishedAfter=formatted_date,
            maxResults=50, 
            regionCode="BR",
            relevanceLanguage="pt",
            pageToken=page_token
        )
        response = request.execute()

        items = response.get("items", [])
        if not items:
            break 

        video_ids = [item["id"]["videoId"] for item in items]

        # ### MODIFICATION 1: Requesting the "Full Profile" of the video (statistics, snippet, and contentDetails)
        stats_request = youtube_service.videos().list(
            part="statistics,snippet,contentDetails", 
            id=",".join(video_ids)
        )
        stats_response = stats_request.execute()

        # ### MODIFICATION 2: Creating a rich map with all the new data
        video_details_map = {}
        for item in stats_response.get("items", []):
            vid = item["id"]
            video_details_map[vid] = {
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "total_comments": int(item["statistics"].get("commentCount", 0)),
                "full_description": item["snippet"].get("description", ""),
                "channel_tags": item["snippet"].get("tags", []),
                "iso_duration": item["contentDetails"].get("duration", "") # Ex: PT15M33S (15 min and 33 sec)
            }

        # ### MODIFICATION 3: Appending everything to the final dictionary
        for item in items:
            vid_id = item["id"]["videoId"]
            details = video_details_map.get(vid_id, {})
            views = details.get("views", 0)

            if views >= min_views:
                found_videos.append({
                    "_temp_id": vid_id, 
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "link": f"https://www.youtube.com/watch?v={vid_id}",
                    "publication_date": format_br_date(item["snippet"]["publishedAt"]),
                    # Structuring to match your Bluesky clipping:
                    "statistics": {
                        "views": views,
                        "likes": details.get("likes", 0),
                        "total_comments": details.get("total_comments", 0)
                    },
                    "video_metadata": {
                        "duration": details.get("iso_duration"),
                        "hidden_tags": details.get("channel_tags", [])
                    },
                    "description": details.get("full_description", "")
                })

                if len(found_videos) >= max_results:
                    break

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return found_videos

def extract_video_text(video_id, languages=['pt', 'en']):
    """
    Extrai a transcrição usando yt-dlp para contornar bloqueios e aplicar cookies com eficiência.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
  
    ydl_opts = {
        'skip_download': True,        
        'writesubtitles': True,       
        'writeautomaticsub': True,    
        'subtitleslangs': languages,  
        'cookiefile': YOUTUBE_COOKIES_PATH, 
        'quiet': True,
        'no_warnings': True,
        'ignore_no_formats_error': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ydl.extract_info gives us a dictionary of all video metadata
            info = ydl.extract_info(url, download=False)
            
        # Get subtitles (manual first, then automatic)
        subs = info.get('subtitles', {})
        if not subs:
            subs = info.get('automatic_captions', {})
            
        if not subs:
            logger.warning("DISCARD | No subtitles found for this video.")
            return None
            
        # Find available requested language
        available_lang = next((lang for lang in languages if lang in subs), None)
        
        if not available_lang:
            # Fallback check for pt-BR or similar if only pt was requested
            available_lang = next((l for l in subs.keys() if l.startswith('pt')), None)
            
        if not available_lang:
            logger.warning(f"DISCARD | No subtitles available in languages={languages}")
            return None
            
        # We prefer 'json3' format for clean text extraction
        sub_tracks = subs[available_lang]
        json3_track = next((track for track in sub_tracks if track.get('ext') == 'json3'), None)
        
        if json3_track:
            res = requests.get(json3_track['url'], timeout=15)
            
            # Anti-block check: if we get a 403 or 429 here, it means the signature expired or we're blocked
            if res.status_code in [403, 429]:
                raise RuntimeError("IP_BLOCKED")

            if not res.ok or not res.text.strip():
                logger.warning(f"DISCARD | Failed to download subtitle JSON (status={res.status_code})")
                return None
            
            try:
                events = res.json().get('events', [])
            except Exception:
                logger.error("Failed to decode subtitle JSON — JSONDecodeError.")
                return None
            
            text_lines = []
            for ev in events:
                segs = ev.get('segs', [])
                for seg in segs:
                    text_lines.append(seg.get('utf8', '').strip())
                    
            final_text = " ".join(filter(None, text_lines)).replace('\n', ' ')
            return final_text
        else:
            logger.warning("DISCARD | json3 subtitle format not available for this video.")
            return None

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if any(sig in error_msg for sig in ["429", "too many requests", "blocked", "sign in to confirm"]):
            raise RuntimeError("IP_BLOCKED")
            
        logger.error(f"Caption DownloadError: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected caption error: {type(e).__name__} — {e}")
        return None



def extract_comments(video_id, max_comments=5):
    try:
        request = youtube_service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments,
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()

        comments = []
        for item in response.get("items", []):
            info = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": info["authorDisplayName"],
                "text": info["textDisplay"],
                "likes": info["likeCount"],
                # ### MODIFICATION: Formatted comment date
                "date": format_br_date(info["publishedAt"])
            })
        return comments
    except Exception:
        return []

# ### MODIFICATION: Hard Vote Logic Integration
def approve_pt_language(title):
    """Returns True if at least 2 out of 3 models detect PT"""
    clean_title = title.replace('\n', ' ').strip()
    if not clean_title:
        return False

    try:
        v_lang = detect(clean_title) in ['pt', 'pt-br']
    except:
        v_lang = False

    try:
        res = lingua_detector.detect_language_of(clean_title)
        v_ling = (res is not None) and (res.name == 'PORTUGUESE')
    except:
        v_ling = False

    try:
        v_fast = fasttext_model.predict(clean_title)[0][0] == '__label__pt'
    except:
        v_fast = False

    total_votes = sum([v_lang, v_ling, v_fast])
    logger.debug(f"Language votes | LangDetect={v_lang} | Lingua={v_ling} | FastText={v_fast}")
    if total_votes < 2:
        logger.warning(f"DISCARD | Hard Vote failed | LangDetect={v_lang} | Lingua={v_ling} | FastText={v_fast}")
    return total_votes >= 2

# ==========================================
# 4. MAIN ENGINE (ORCHESTRATOR)
# ==========================================
def generate_youtube_clipping_json(topic, max_videos=5, max_comments=5, min_views=500, days=7):
    
    logger.info(f"Scraping started | topic='{topic}'")

    raw_videos = fetch_recent_videos(topic, max_results=max_videos, min_views=min_views, days=days)
    logger.info(f"Initial search complete | {len(raw_videos)} candidate videos found")

    complete_data = []
    ip_blocked    = False

    # ── Random Batch Loop ──────────────────────────────────────────────────────
    video_queue = list(raw_videos)  # mutable working copy
    batch_number = 0

    while video_queue and len(complete_data) < max_videos and not ip_blocked:
        batch_number += 1

        # Rule 1a – pick a random batch size
        batch_size  = random.randint(BATCH_MIN_VIDEOS, BATCH_MAX_VIDEOS)
        current_batch = video_queue[:batch_size]
        video_queue   = video_queue[batch_size:]

        logger.info(f"Batch #{batch_number} | Processing {len(current_batch)} video(s)")

        for idx, video in enumerate(current_batch):
            if len(complete_data) >= max_videos:
                break

            logger.debug(f"Evaluating: '{video['title'][:60]}'")

            # ### MODIFICATION: Using Hard Vote instead of simple detect
            if not approve_pt_language(video["title"]):
                # warning is already emitted inside approve_pt_language
                continue

            # Rule 1b – intra-video jitter (skip sleep before the very first video)
            if idx > 0 or batch_number > 1:
                jitter = random.uniform(JITTER_MIN_SECONDS, JITTER_MAX_SECONDS)
                logger.debug(f"Intra-video jitter: {jitter:.1f}s")
                time.sleep(jitter)
            else:
                logger.debug("Title approved — starting extraction (no jitter for first video).")

            # Rule 2 – cookie-based transcript extraction
            # Rule 3 & 4 handled inside extract_video_text
            try:
                transcript = extract_video_text(video["_temp_id"])
            except RuntimeError as e:
                if str(e) == "IP_BLOCKED":
                    logger.critical(
                        "IP_BLOCKED detected — aborting extraction to prevent ban. "
                        "Switch network or wait for cooldown."
                    )
                    ip_blocked = True
                    break
                raise

            if transcript is None:
                # Rule 3 – no captions: skip without breaking the loop
                continue

            logger.debug(f"Transcript extracted ({len(transcript)} chars) — fetching comments...")
            video["full_transcript"] = transcript

            # ### MODIFICATION: Changed the key 'top_comentarios' to 'most_liked_comments'
            video["most_liked_comments"] = extract_comments(video["_temp_id"], max_comments)

            # ### MODIFICATION: Removing the redundant ID before saving to the final JSON
            del video["_temp_id"]

            complete_data.append(video)

        # Rule 1c – inter-batch cooldown (only if more work remains)
        if video_queue and len(complete_data) < max_videos and not ip_blocked:
            cooldown = random.uniform(COOLDOWN_MIN_SECONDS, COOLDOWN_MAX_SECONDS)
            logger.debug(f"Inter-batch cooldown: {cooldown:.1f}s")
            time.sleep(cooldown)

    if ip_blocked:
        sys.exit(1)

    # ### MODIFICATION: Main JSON structure adjustment
    final_output = {
        "youtube_clipping_metadata": {
            "searched_topic": topic,
            "generation_date": datetime.now().strftime("%d/%m/%Y - %H:%M"), # formatted date
            "total_processed_videos": len(complete_data)
        },
        "videos": complete_data
    }

    file_name = f"youtube_clipping_{topic.replace(' ', '_').lower()}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    logger.info(f"DONE | {len(complete_data)} videos saved | file='{file_name}'")
    return final_output

# ==========================================
# SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":

    test_data = generate_youtube_clipping_json(
        topic="Legalização do Aborto",
        max_videos=3, 
        max_comments=5,
        min_views=1000,
        days=30
    )
    #print(test_data)
