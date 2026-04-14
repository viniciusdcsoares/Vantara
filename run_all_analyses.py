import os
import json
import re
from pathlib import Path
from google import genai
import streamlit as st

from run_llm_analysis import run_analysis


def main():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        print("Aviso: GEMINI_API_KEY não foi encontrada.")

    scraping_dir = Path("outputs/scraping")
    if not scraping_dir.exists():
        print(f"Diretório {scraping_dir} não encontrado.")
        return

    DATE_FILTER = "2026-04-09"   # ← mude aqui para processar outro dia
    all_files = list(scraping_dir.glob("*.json"))
    scraping_files = [f for f in all_files if DATE_FILTER in f.name]
    print(f"Encontrados {len(scraping_files)} arquivo(s) para '{DATE_FILTER}' (de {len(all_files)} total).")

    for file_path in scraping_files:
        print(f"\n=======================================================")
        print(f" INICIANDO ANÁLISE LLM: {file_path.name}")
        print(f"=======================================================")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                scraped_data = json.load(f)

            topic_str = file_path.stem
            topic_clean = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$', '', topic_str)
            topic_display = topic_clean.replace("_", " ").title()

            print(f"\nRodando Análise LLM para o tema '{topic_display}'...")
            llm_results, prompts_used, embedding_artifacts = run_analysis(
                data=scraped_data,
                topic=topic_display,
                embedding_variant="embedding_ready_text"
            )

            if not embedding_artifacts or "items_artifact_path" not in embedding_artifacts:
                print(f"Erro: Falha ao gerar artefatos de embedding para {file_path.name}")
                continue

            items_path = Path(embedding_artifacts["items_artifact_path"])
            print(f"✓ Análise concluída. Itens salvos em: {items_path}")

        except Exception as e:
            print(f"ERRO CRÍTICO no processamento de {file_path.name}: {e}")

    print("\n✅ Análise LLM em lote finalizada! Rode run_clustering.py para agrupar os resultados.")


if __name__ == "__main__":
    main()
