import traceback
import os
import streamlit as st
import json
import time       
import random     
import urllib.request
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
print("🔄 Loading language models...")
languages = [Language.ENGLISH, Language.PORTUGUESE, Language.SPANISH, Language.CROATIAN]
lingua_detector = LanguageDetectorBuilder.from_languages(*languages).build()

model_path = "lid.176.ftz"
model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
if not os.path.exists(model_path):
    print("   Downloading FastText model (~900KB)...")
    urllib.request.urlretrieve(model_url, model_path)
fasttext_model = fasttext.load_model(model_path)
print("✅ Language models ready!\n")

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

def extract_video_text(video_id, languages=['pt', 'pt-BR']):
    try:
        api = YouTubeTranscriptApi()
        transcript_obj = api.fetch(video_id, languages=languages)
        
        if hasattr(transcript_obj, 'to_raw_data'):
            captions_list = transcript_obj.to_raw_data()
        else:
            captions_list = transcript_obj

        text_lines = []
        for item in captions_list:
            if isinstance(item, dict):
                text_lines.append(item.get('text', ''))
            else:
                text_lines.append(getattr(item, 'text', ''))
                
        full_text = " ".join(text_lines).replace('\n', ' ')
        return full_text

    except TranscriptsDisabled:
        print("   ❌ Warning: The channel owner disabled captions for this video.")
        return None
    except NoTranscriptFound:
        print("   ❌ Warning: The video does not have captions in 'pt' or 'pt-BR'.")
        return None
    except Exception as e:
        error_name = type(e).__name__
        print(f"   ❌ Warning: Caption error: {error_name}.")
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
    print(f"   📊 Votes for Portuguese -> LangDetect: {v_lang} | Lingua: {v_ling} | FastText: {v_fast}")
    
    return total_votes >= 2

# ==========================================
# 4. MAIN ENGINE (ORCHESTRATOR)
# ==========================================
def generate_youtube_clipping_json(topic, max_videos=5, max_comments=5, min_views=500, days=7):
    
    print(f"🔍 Starting YouTube scraping for the topic '{topic}'")

    raw_videos = fetch_recent_videos(topic, max_results=max_videos, min_views=min_views, days=days)
    print(f"✅ Initial search completed. Analyzing {len(raw_videos)} potential videos...\n")

    complete_data = []

    for video in raw_videos:
        if len(complete_data) >= max_videos:
            break

        print(f"🔄 Evaluating video: {video['title'][:40]}...")

        # ### MODIFICATION: Using Hard Vote instead of simple detect
        if not approve_pt_language(video["title"]):
            print("   ❌ Discarded (Failed the language Hard Vote).")
            continue

        delay = random.uniform(3.0, 7.0)
        print(f"   ⏱️ Title approved! Pausing for {delay:.2f}s...")
        time.sleep(delay)

        # Tries to extract the caption using the temporary ID
        transcript = extract_video_text(video["_temp_id"])

        print("   🔄 Extracting comments...")
        video["full_transcript"] = transcript
        
        # ### MODIFICATION: Changed the key 'top_comentarios' to 'most_liked_comments'
        video["most_liked_comments"] = extract_comments(video["_temp_id"], max_comments)

        # ### MODIFICATION: Removing the redundant ID before saving to the final JSON
        del video["_temp_id"]

        complete_data.append(video)

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
    #with open(file_name, "w", encoding="utf-8") as f:
    #    json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Success! {len(complete_data)} videos saved in: {file_name}")
    return final_output

# ==========================================
# SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":

    test_data = generate_youtube_clipping_json(
        topic="Aborto",
        max_videos=2, 
        max_comments=2,
        min_views=1000,
        days=7
    )
    print(test_data)