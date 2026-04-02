import requests
import json
import streamlit as st
import time
import random
from datetime import datetime, timedelta

from logger_configs import setup_logger
logger = setup_logger("scraping")

# ==========================================
# 1. CREDENTIALS AND SETUP
# ==========================================
API_KEY = st.secrets['NEWS_API_KEY']
JINA_API_KEY = st.secrets['JINA_API_KEY'] # 

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

def ler_noticia_com_jina(link_da_noticia):
    """
    Extrai o texto completo da notícia em formato Markdown utilizando a Jina AI Reader API.
    """
    logger.debug(f"Jina fetching: {link_da_noticia[:70]}")

    url_jina = f"https://r.jina.ai/{link_da_noticia}"

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "X-Engine": "browser",          
        "X-Return-Format": "markdown"   
    }

    try:
        response = requests.get(url_jina, headers=headers, timeout=30)
        response.raise_for_status() 
        return response.text # Retorna diretamente o texto em Markdown
    except Exception as e:
        logger.error(f"Jina fetch failed for {link_da_noticia[:50]}: {e}")
        return None

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
        logger.error(f"NewsAPI connection error: {e}")
        try:
            logger.error(f"NewsAPI detail: {response.json().get('message')}")
        except:
            pass
        return []

# ==========================================
# 3. MAIN ENGINE (ORCHESTRATOR)
# ==========================================
def generate_newsapi_clipping_json(topic, max_articles=5):
    
    logger.info(f"Scraping started | topic='{topic}'")

    raw_articles = fetch_newsapi_articles(topic)

    complete_data = []
    seen_sources = set() 

    for article in raw_articles:
        if len(complete_data) >= max_articles:
            break

        title = article.get("title", "")
        if not title or title == "[Removed]": 
            continue

        source_name = article.get("source", {}).get("name", "Unknown Source")
        
        if source_name in seen_sources:
            logger.warning(f"DISCARD | Source already captured: '{source_name}' | title='{title[:50]}'")
            continue

        logger.debug(f"Processing article | source='{source_name}' | title='{title[:50]}'")

        url = article.get("url", "")
        full_content = ler_noticia_com_jina(url) if url else None

        complete_data.append({
            "title": title,
            "author": article.get("author") or "Unknown Author",
            "source": article.get("source", {}).get("name", "Unknown Source"), 
            "description": article.get("description") or "No description available.",
            "publication_date": format_br_date(article.get("publishedAt")),
            "url": url,
            "content": full_content or ""
        })
        
        seen_sources.add(source_name)

    if not complete_data:
        logger.warning(f"No valid articles found for topic='{topic}'.")
        return None

    final_output = {
        "newsapi_clipping_metadata": {
            "searched_topic": topic,
            "generation_date": datetime.now().strftime("%d/%m/%Y - %H:%M"),
            "total_processed_articles": len(complete_data)
        },
        "articles": complete_data
    }

    file_name = f"news_clipping_{topic.replace(' ', '_').lower()}.json"

    logger.info(f"DONE | {len(complete_data)} articles saved | file='{file_name}'")
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
