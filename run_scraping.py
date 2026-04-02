import logging
import os
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional

# Importing generator functions from each scraper
from scraping.youtube import generate_youtube_clipping_json
from scraping.bluesky import generate_bluesky_clipping_json
from scraping.news import generate_newsapi_clipping_json

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_all_scrapers(
    topic: str,
    scrapers_to_run: Optional[List[str]] = None,
    youtube_config: Optional[Dict] = None,
    bluesky_config: Optional[Dict] = None,
    news_config: Optional[Dict] = None
) -> dict:
    """
    Orchestrator function to run scrapers and save results in outputs/scraping/.
    """
    
    # Default configurations
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
    
    # --- AJUSTE DE DIRETÓRIO ---
    # Define o caminho completo: outputs/scraping
    output_dir = os.path.join("outputs", "scraping")
    
    # Cria a pasta e as subpastas necessárias se não existirem
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename logic
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_topic = topic.replace(" ", "_").lower()
    file_name = f"{safe_topic}_{timestamp}.json"
    
    # Full path: outputs/scraping/topic_timestamp.json
    final_path = os.path.join(output_dir, file_name)
    # ---------------------------

    logging.info(f"Starting scraper orchestration for topic: '{topic}'")
    logging.info(f"File will be saved at: {final_path}")

    # 1. YouTube Scraper
    if 'youtube' in scrapers_to_run:
        logging.info("Running YouTube scraper...")
        try:
            youtube_results = generate_youtube_clipping_json(topic, **youtube_config)
            consolidated_data["youtube_data"] = youtube_results
        except Exception as e:
            logging.error(f"Error executing YouTube scraper: {e}")

    # 2. Bluesky Scraper
    if 'bluesky' in scrapers_to_run:
        logging.info("Running Bluesky scraper...")
        try:
            bluesky_results = generate_bluesky_clipping_json(topic, **bluesky_config)
            consolidated_data["bluesky_data"] = bluesky_results
        except Exception as e:
            logging.error(f"Error executing Bluesky scraper: {e}")

    # 3. NewsAPI Scraper
    if 'news' in scrapers_to_run:
        logging.info("Running NewsAPI scraper...")
        try:
            news_results = generate_newsapi_clipping_json(topic, **news_config)
            consolidated_data["news_data"] = news_results
        except Exception as e:
            logging.error(f"Error executing NewsAPI scraper: {e}")

    # Saving consolidated data
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(consolidated_data, f, indent=4, ensure_ascii=False)

    logging.info(f"Orchestration complete! File saved at: {final_path}")
    return consolidated_data

# ==========================================
# ORCHESTRATOR CONFIGURATION
# ==========================================
TOPICS_TO_SCRAPE = [
    "Fundo Eleitoral",
    "Reforma Tributária",
    "Reforma da Previdência",
    "Transição Energética",
    "Atuação do STF",
    "Guerra no Irã",
    "Segurança Pública",
    "Privatizações de Serviços",
    "IA nas Eleições",
    "Regulação das Redes Sociais"
]

TOPICS_TO_SCRAPE = ["Guerra no Irã", "Fundo Eleitoral"]


if __name__ == "__main__":
    # Configuration parameters for depth of scraping
    max_results = 10
    max_comments = 5
    days = 30
    
    youtube_cfg = {"max_videos": max_results, "max_comments": max_comments, "days": days, "min_views": 1000}
    bluesky_cfg = {"max_posts": max_results, "max_comments": max_comments, "days": days}
    news_cfg = {"max_articles": max_results}

    print(f"📡 [Orquestrador] Iniciando pipeline para {len(TOPICS_TO_SCRAPE)} temas...\n")

    for idx, topic in enumerate(TOPICS_TO_SCRAPE):
        print(f"▶️ Executando tema {idx+1}/{len(TOPICS_TO_SCRAPE)}: '{topic}'")
        
        run_all_scrapers(
            topic=topic,
            scrapers_to_run=['youtube', 'bluesky', 'news'],
            youtube_config=youtube_cfg,
            bluesky_config=bluesky_cfg,
            news_config=news_cfg
        )
        
        # Anti-bot cooldown between complete themes
        if idx < len(TOPICS_TO_SCRAPE) - 1:
            cooldown = random.uniform(120, 240)
            print(f"\n[Orquestrador] Tema '{topic}' finalizado. Pausando por {cooldown:.1f}s para evitar rate-limit...")
            time.sleep(cooldown)

    print(f"\n✅ Pipeline completo! Verifique a pasta outputs/scraping/.")