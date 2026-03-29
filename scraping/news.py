import requests
import json
import streamlit as st
import time
import random
from datetime import datetime, timedelta

# ==========================================
# 1. CREDENTIALS AND SETUP
# ==========================================
API_KEY = st.secrets['NEWS_API_KEY'] # 

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def format_br_date(iso_date):
    """Converts NewsAPI date (UTC) to DD/MM/YYYY - HH:MM (Brasilia time)"""
    if not iso_date:
        return "Unknown date"
    try:
        # NewsAPI sends in the format: 2026-03-25T14:30:00Z
        dt = datetime.strptime(iso_date.replace('.000Z', 'Z'), "%Y-%m-%dT%H:%M:%SZ")
        dt = dt - timedelta(hours=3) # Adjustment for Brazil (UTC-3)
        return dt.strftime("%d/%m/%Y - %H:%M")
    except Exception:
        return iso_date

def fetch_newsapi_articles(topic):
    """Hits the API and fetches raw articles"""
    #print(f"🔍 Searching for news about '{topic}'...")
    
    #url = f"https://newsapi.org/v2/everything?q={topic}&language=pt&sortBy=relevancy&pageSize=100&apiKey={API_KEY}"
    url = f"https://newsapi.org/v2/everything?q={topic}&language=pt&sortBy=publishedAt&pageSize=100&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        # Triggers a clear error if the key is wrong or quota is exceeded
        response.raise_for_status() 
        data = response.json()
        
        return data.get("articles", [])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error with NewsAPI: {e}")
        try:
            print(f"   Detail: {response.json().get('message')}")
        except:
            pass
        return []

# ==========================================
# 3. MAIN ENGINE (ORCHESTRATOR)
# ==========================================
def generate_newsapi_clipping_json(topic, max_articles=5):
    
    print(f"🚀 Starting News scraping for the topic '{topic}'")

    raw_articles = fetch_newsapi_articles(topic)
    #print(f"✅ Search completed. Evaluating {len(raw_articles)} results...\n")

    complete_data = []
    
    # ### NEW: Stores the name of the portals that have already entered the list
    seen_sources = set() 

    for article in raw_articles:
        if len(complete_data) >= max_articles:
            break

        title = article.get("title", "")
        if not title or title == "[Removed]": 
            continue

        source_name = article.get("source", {}).get("name", "Unknown Source")
        
        # ### NEW: Diversity Filter (Prevents monopoly from a single site)
        if source_name in seen_sources:
            print(f"   ⏭️ Skipping article from '{source_name}' (we already have a source from this site).")
            continue

        print(f"🔄 Processing article from 'new' channel ({source_name}): {title[:40]}...")

        #delay = random.uniform(1.0, 2.0)
        #time.sleep(delay)

        # Builds the clean and safe dictionary using .get() with default values (or "...")
        complete_data.append({
            "title": title,
            "author": article.get("author") or "Unknown Author",
            "source": article.get("source", {}).get("name", "Unknown Source"), 
            "description": article.get("description") or "No description available.",
            "publication_date": format_br_date(article.get("publishedAt")),
            "url": article.get("url", ""),
            "content": article.get("content")
        })
        
        seen_sources.add(source_name)

    if not complete_data:
        print("\n❌ No valid articles found.")
        return None

    # Standardized JSON structure identical to YouTube and Bluesky
    final_output = {
        "newsapi_clipping_metadata": {
            "searched_topic": topic,
            "generation_date": datetime.now().strftime("%d/%m/%Y - %H:%M"),
            "total_processed_articles": len(complete_data)
        },
        "articles": complete_data
    }

    file_name = f"news_clipping_{topic.replace(' ', '_').lower()}.json"
    #with open(file_name, "w", encoding="utf-8") as f:
    #    json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Success! {len(complete_data)} articles saved in: {file_name}")
    return final_output

# ==========================================
# SCRIPT EXECUTION
# ==========================================
if __name__ == "__main__":
    test_data = generate_newsapi_clipping_json(
        topic="Guerra no Irã",
        max_articles=5
    )
    print(test_data)