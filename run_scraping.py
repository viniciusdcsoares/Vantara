import logging
import os
import json
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Importing generator functions from each scraper
from scraping.youtube import generate_youtube_clipping_json, fetch_recent_videos
from scraping.bluesky import generate_bluesky_clipping_json
from scraping.news import generate_newsapi_clipping_json

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def update_scraping_ledger(consolidated_data: dict):
    new_records = []
    now = datetime.now()
    
    if consolidated_data.get("youtube_data") and "videos" in consolidated_data["youtube_data"]:
        for v in consolidated_data["youtube_data"]["videos"]:
            if "id" in v: new_records.append({"item_id": v["id"], "scraped_at": now})
            
    if consolidated_data.get("bluesky_data") and "posts" in consolidated_data["bluesky_data"]:
        for p in consolidated_data["bluesky_data"]["posts"]:
            if "id" in p: new_records.append({"item_id": p["id"], "scraped_at": now})
            
    if consolidated_data.get("news_data") and "articles" in consolidated_data["news_data"]:
        for a in consolidated_data["news_data"]["articles"]:
            if "id" in a: new_records.append({"item_id": a["id"], "scraped_at": now})
            
    if not new_records:
        logging.info("Nenhum ID novo para adicionar ao ledger.")
        return
        
    ledger_path = os.path.join("outputs", "scraping_ledger.parquet")
    df_new = pd.DataFrame(new_records)
    
    if os.path.exists(ledger_path):
        try:
            df_old = pd.read_parquet(ledger_path)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["item_id"], keep="last")
        except Exception as e:
            logging.error(f"Erro lendo ledger: {e}")
            df_combined = df_new
    else:
        df_combined = df_new
        
    df_combined.to_parquet(ledger_path, index=False)
    logging.info(f"Ledger Parquet atualizado! {len(new_records)} registros injetados. Total no Ledger: {len(df_combined)}")

def run_interleaved_strategy(topic: str, youtube_cfg: Optional[Dict] = None, bluesky_cfg: Optional[Dict] = None, news_cfg: Optional[Dict] = None) -> dict:
    """
    Experimental strategy to avoid IP blocking by interleaving YouTube extraction 
    with Bluesky and NewsAPI requests.
    """
    output_dir = os.path.join("outputs", "scraping")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_topic = topic.replace(" ", "_").lower()
    final_path = os.path.join(output_dir, f"{safe_topic}_{timestamp}.json")

    youtube_cfg = youtube_cfg or {}
    bluesky_cfg = bluesky_cfg or {}
    news_cfg = news_cfg or {}

    max_yt = youtube_cfg.get("max_videos", 100)
    
    logging.info(f"--- INTERLEAVED STRATEGY FOR: {topic} ---")

    # STEP 0: Fetch ALL candidate video metadata via API (Safe)
    logging.info(f"Step 0: Pre-fetching {max_yt} YouTube video candidates via API...")
    all_video_candidates = fetch_recent_videos(
        topic, 
        max_results=max_yt, 
        min_views=youtube_cfg.get("min_views", 500), 
        days=youtube_cfg.get("days", 7)
    )
    
    if not all_video_candidates:
        logging.warning("No YouTube videos found. Aborting strategy.")
        return None

    # Dynamic splitting into 3 chunks
    total_found = len(all_video_candidates)
    chunk_size = total_found // 3
    
    chunk1 = all_video_candidates[:chunk_size]
    chunk2 = all_video_candidates[chunk_size : 2 * chunk_size]
    chunk3 = all_video_candidates[2 * chunk_size:]

    consolidated_data = {
        "youtube_data": {"youtube_clipping_metadata": {}, "videos": []},
        "bluesky_data": None,
        "news_data": None
    }

    # PASS 1: YouTube Chunk 1
    if chunk1:
        logging.info(f"Pass 1: Extracting transcripts for YouTube Chunk 1 (1-{len(chunk1)})...")
        yt_res1 = generate_youtube_clipping_json(topic, pre_fetched_videos=chunk1, **youtube_cfg)
        if yt_res1:
            consolidated_data["youtube_data"]["videos"].extend(yt_res1.get("videos", []))
    
    # PASS 2: Bluesky (Natural Cooldown for YT IP)
    logging.info("Pass 2: Running Bluesky (Super Cooldown for YouTube IP)...")
    consolidated_data["bluesky_data"] = generate_bluesky_clipping_json(topic, **bluesky_cfg)

    # PASS 3: YouTube Chunk 2
    if chunk2:
        start_idx = len(chunk1) + 1
        end_idx = len(chunk1) + len(chunk2)
        logging.info(f"Pass 3: Extracting transcripts for YouTube Chunk 2 ({start_idx}-{end_idx})...")
        yt_res2 = generate_youtube_clipping_json(topic, pre_fetched_videos=chunk2, **youtube_cfg)
        if yt_res2:
            consolidated_data["youtube_data"]["videos"].extend(yt_res2.get("videos", []))

    # PASS 4: NewsAPI (Another Cooldown for YT IP)
    logging.info("Pass 4: Running NewsAPI (Second Cooldown for YouTube IP)...")
    consolidated_data["news_data"] = generate_newsapi_clipping_json(topic, **news_cfg)

    # PASS 5: YouTube Chunk 3
    if chunk3:
        start_idx = len(chunk1) + len(chunk2) + 1
        end_idx = total_found
        logging.info(f"Pass 5: Extracting transcripts for YouTube Chunk 3 ({start_idx}-{end_idx})...")
        yt_res3 = generate_youtube_clipping_json(topic, pre_fetched_videos=chunk3, **youtube_cfg)
        if yt_res3:
            consolidated_data["youtube_data"]["videos"].extend(yt_res3.get("videos", []))

    # Finalize YT Metadata
    consolidated_data["youtube_data"]["youtube_clipping_metadata"] = {
        "searched_topic": topic,
        "generation_date": datetime.now().strftime("%d/%m/%Y - %H:%M"),
        "total_processed_videos": len(consolidated_data["youtube_data"]["videos"])
    }

    update_scraping_ledger(consolidated_data)

    # Save
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(consolidated_data, f, indent=4, ensure_ascii=False)

    logging.info(f"Interleaved strategy finished! File saved at: {final_path}")
    return consolidated_data

def run_all_scrapers(
    topic: str,
    scrapers_to_run: Optional[List[str]] = None,
    youtube_config: Optional[Dict] = None,
    bluesky_config: Optional[Dict] = None,
    news_config: Optional[Dict] = None
) -> dict:
    """
    Standard orchestrator function to run scrapers sequentially.
    """
    
    if scrapers_to_run is None:
        scrapers_to_run = ['youtube', 'bluesky', 'news']
        
    youtube_config = youtube_config or {}
    bluesky_config = bluesky_config or {}
    news_config = news_config or {}
    
    consolidated_data = {
        "youtube_data": None,
        "bluesky_data": None,
        "news_data": None
    }
    
    output_dir = os.path.join("outputs", "scraping")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_topic = topic.replace(" ", "_").lower()
    final_path = os.path.join(output_dir, f"{safe_topic}_{timestamp}.json")

    logging.info(f"Starting standard orchestration for topic: '{topic}'")

    if 'youtube' in scrapers_to_run:
        logging.info("Running YouTube scraper...")
        try:
            youtube_results = generate_youtube_clipping_json(topic, **youtube_config)
            consolidated_data["youtube_data"] = youtube_results
        except Exception as e:
            logging.error(f"Error executing YouTube scraper: {e}")

    if 'bluesky' in scrapers_to_run:
        logging.info("Running Bluesky scraper...")
        try:
            bluesky_results = generate_bluesky_clipping_json(topic, **bluesky_config)
            consolidated_data["bluesky_data"] = bluesky_results
        except Exception as e:
            logging.error(f"Error executing Bluesky scraper: {e}")

    if 'news' in scrapers_to_run:
        logging.info("Running NewsAPI scraper...")
        try:
            news_results = generate_newsapi_clipping_json(topic, **news_config)
            consolidated_data["news_data"] = news_results
        except Exception as e:
            logging.error(f"Error executing NewsAPI scraper: {e}")

    update_scraping_ledger(consolidated_data)

    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(consolidated_data, f, indent=4, ensure_ascii=False)

    logging.info(f"Standard orchestration complete! File saved at: {final_path}")
    return consolidated_data

# ==========================================
# ORCHESTRATOR CONFIGURATION
# ==========================================
TOPICS_TO_SCRAPE = [
    "Atuação do STF",
    "Escala 6x1",
    "Guerra no Irã",
    "IA nas Eleições",
    "Fundo Eleitoral",
    "Reforma Tributária",
    "Reforma da Previdência",
    "Descriminalização das Drogas",
    "Israel e Palestina",
    "Porte de Armas",
    "Maioridade Penal",
    "Legalização do Aborto",
]

#TOPICS_TO_SCRAPE = ["Atuação do STF"]

if __name__ == "__main__":
    # Target 100 units for batch
    max_results = 100
    max_comments = 5
    days = 180
    
    youtube_cfg = {"max_videos": 25, "max_comments": max_comments, "days": days, "min_views": 1000}
    bluesky_cfg = {"max_posts": 50, "max_comments": max_comments, "days": days}
    news_cfg = {"max_articles": 50}

    print(f"📡 [Orquestrador] Iniciando pipeline INTERCALADO para {len(TOPICS_TO_SCRAPE)} temas...\n")

    for idx, topic in enumerate(TOPICS_TO_SCRAPE):
        print(f"▶️ Executando tema {idx+1}/{len(TOPICS_TO_SCRAPE)}: '{topic}'")
        
        # Ignoramos o YouTube devido ao bloqueio de IP no momento
        run_all_scrapers(
            topic=topic,
            scrapers_to_run=['bluesky', 'news', 'youtube'],
            bluesky_config=bluesky_cfg,
            news_config=news_cfg
        )
        
        if idx < len(TOPICS_TO_SCRAPE) - 1:
            # Pausa maior para proteção de IP entre temas
            cooldown = random.uniform(60, 120)
            print(f"\n[Orquestrador] Pausando {cooldown:.1f}s entre temas...")
            time.sleep(cooldown)

    print(f"\n✅ Pipeline intercalado completo! Verifique a pasta outputs/scraping/.")