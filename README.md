# Vantara — Political Intelligence Pipeline

A multi-source scraping and analysis orchestrator designed to collect, analyze, and cluster political data from YouTube, Bluesky, and NewsAPI using Google Gemini.

## 🚀 Pipeline Flow

The project is structured as a 3-phase automated sequence:

1.  **Collection (`run_scraping.py`)**: Orchestrates data extraction from YouTube, Bluesky, and NewsAPI. Saves consolidated raw data to `outputs/scraping/`.
2.  **Analysis & Embedding (`run_llm_analysis.py`)**: Performs per-item LLM analysis (Gemini 2.5 Flash), generates semantic embeddings, and clusters items via K-Means and t-SNE. Results in `outputs/analysis/` and `outputs/embeddings/`.
3.  **Audit & Review (`audit_nearest_neighbors.py`, `prepare_manual_review.py`)**: Validates embedding quality and prepares CSVs for human-in-the-loop review.

## ✨ Key Features
- **Anti-Bot YouTube Scraping**: Randomized jitter (3-7s) and local cookie support (`youtube_cookies.txt`) for robust extraction.
- **Per-Item Analysis**: Granular analysis producing `canonical_claim` for high-resolution narrative detection.
- **Cross-Source Clustering**: Maps arguments from different platforms into a shared semantic space.

## 🛠️ Setup
1.  **Environment**: Python 3.12+
2.  **Dependencies**: `pip install -r requirements.txt`
3.  **Secrets**: Configure `.streamlit/secrets.toml` with `GEMINI_API_KEY`, `YOUTUBE_API_KEY`, etc.
4.  **Cookies**: Place your Netscape-formatted `youtube_cookies.txt` in the root for better transcript throughput.

## 📖 Documentation
Detailed architectural blueprints and live implementation status can be found in the [docs/](./docs/) directory.
- [Implementation Status](./docs/reconciliation/IMPLEMENTATION_STATUS.md) (Authority A)
- [Architecture Blueprint](./docs/architecture/) (Authority B)