import traceback
import os
import streamlit as st
import json
import time
import random
from datetime import datetime, timedelta

from atproto import Client

# ==========================================
# 1. BLUESKY CREDENTIALS
# ==========================================
BSKY_HANDLE = st.secrets['BSKY_HANDLE'] # change to username
BSKY_APP_PASSWORD = st.secrets['BSKY_APP_PASSWORD'] # Remember to use the new app password!

# ==========================================
# 2. HELPER AND EXTRACTION FUNCTIONS
# ==========================================
def format_br_date(iso_date):
    """Converts Bluesky date (UTC) to DD/MM/YYYY - HH:MM (Brasilia time)"""
    try:
        # Bluesky dates come as '2026-03-25T20:04:57.199Z'
        dt_str = iso_date.replace('Z', '').split('.')[0]
        dt = datetime.fromisoformat(dt_str)
        # Adjustment for Brasilia (UTC-3)
        dt = dt - timedelta(hours=3)
        return dt.strftime("%d/%m/%Y - %H:%M")
    except:
        return iso_date

def fetch_bluesky_posts(topic, max_posts=3, max_comments=3, days=7):
    """
    Fetches relevant posts on Bluesky, enters them and pulls replies.
    """
    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    except Exception as e:
        print(f"❌ Error logging into Bluesky: {e}")
        return []
    
    try:
        # Calculates the date 7 days ago in YYYY-MM-DD format
        date_7_days_ago = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Search filtered by language (lang:pt), date (since:) and relevance
        search_query = f"{topic} lang:pt since:{date_7_days_ago}"
        response = client.app.bsky.feed.search_posts({
            'q': search_query, 
            'limit': 100, 
            'sort': 'top' 
        })

        sorted_posts = sorted(response.posts, key=lambda p: p.like_count or 0, reverse=True)

        extracted_posts = []
        
        for post in sorted_posts[:max_posts]:
            # I believe we won't need this for this API
            #delay = random.uniform(2.0, 5.0)
            #print(f"   ⏱️ Post from @{post.author.handle} found. Anti-bot pause of {delay:.2f}s...")
            #time.sleep(delay)
            print(f"   🔎 Post from @{post.author.handle} found.")
            post_id = post.uri.split('/')[-1]
            
            # Extraction of external links (e.g., G1, UOL articles shared in the post)
            external_link = None
            if hasattr(post.record, 'embed') and post.record.embed:
                if hasattr(post.record.embed, 'external'):
                    external_link = post.record.embed.external.uri
            
            # Enters the post thread to fetch comments
            print("   🔄 Extracting comments from the post...")
            comments = []
            try:
                thread = client.app.bsky.feed.get_post_thread({'uri': post.uri})
                if hasattr(thread.thread, 'replies') and thread.thread.replies:
                    for reply in thread.thread.replies[:max_comments]:
                        if hasattr(reply, 'post'):
                            comments.append({
                                "author": reply.post.author.handle,
                                "text": reply.post.record.text,
                                "likes": reply.post.like_count,
                                "date": format_br_date(reply.post.record.created_at)
                            })
            except Exception as e:
                print(f"   ⚠️ Warning: Could not load comments: {e}")

            # Building the clean and optimized dictionary for AI
            extracted_posts.append({
                "text": post.record.text,
                "author": post.author.handle,
                "publication_date": format_br_date(post.record.created_at),
                "link": f"https://bsky.app/profile/{post.author.handle}/post/{post_id}",
                "cited_external_link": external_link,
                "statistics": {
                    "likes": post.like_count,
                    "reposts": post.repost_count,
                    "total_replies": post.reply_count 
                },
                "most_liked_comments": comments
            })
            
        return extracted_posts
    except Exception as e:
        print(f"❌ Error searching Bluesky: {e}")
        return []

# ==========================================
# 3. MAIN ENGINE (ORCHESTRATOR)
# ==========================================
def generate_bluesky_clipping_json(topic, max_posts=5, max_comments=3, days=7):
    
    print(f"🔍 Starting Bluesky scraping for the topic '{topic}'")

    complete_data = fetch_bluesky_posts(topic, max_posts=max_posts, max_comments=max_comments, days=days)
    
    if not complete_data:
        print("\n❌ No data returned. Check the topic or your connection.")
        return None

    # Adjustment of the main JSON structure
    final_output = {
        "bluesky_clipping_metadata": {
            "searched_topic": topic,
            "generation_date": datetime.now().strftime("%d/%m/%Y - %H:%M"), 
            "total_processed_posts": len(complete_data)
        },
        "posts": complete_data
    }

    file_name = f"bluesky_clipping_{topic.replace(' ', '_').lower()}.json"
    #with open(file_name, "w", encoding="utf-8") as f:
    #    json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Success! {len(complete_data)} posts saved in: {file_name}")
    return final_output

# ==========================================
# SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":
    test_data = generate_bluesky_clipping_json(
        topic="Aborto",
        max_posts=2, 
        max_comments=2,
        days=7
    )
    print(test_data)