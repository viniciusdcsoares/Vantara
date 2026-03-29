import os
import json
from pathlib import Path

import streamlit as st
from google import genai

from llm_configs.functions import generate_gemini_json
from llm_configs.prompts.narrative_detection import (
    create_bluesky_prompt,
    create_youtube_prompt,
    create_news_prompt,
    system_instruction_bluesky,
    system_instruction_youtube,
    system_instruction_news,
)
from llm_configs.schemas.narrative_detection import (
    BlueskyAnalysis,
    YoutubeAnalysis,
    NewsAnalysis,
)

def get_latest_scraping_file(scraping_dir: str) -> str:
    path = Path(scraping_dir)
    if not path.exists():
        return None
    files = list(path.glob('*.json'))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return str(latest_file)

def clean_pydantic_output(response_dict: dict) -> dict:
    """Extrai os dados da classe Pydantic para dicionário, útil antes de salvar com json.dump."""
    if isinstance(response_dict, dict) and "result" in response_dict:
        result_content = response_dict["result"]
        if isinstance(result_content, dict) and "output" in result_content:
            output_obj = result_content["output"]
            if hasattr(output_obj, "model_dump"):
                result_content["output"] = output_obj.model_dump()
    return response_dict

def run_analysis(data=None, topic=None):
    # 1. Carrega a chave de API
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        print("Aviso: GEMINI_API_KEY não foi encontrada. Pode dar erro na inicialização caso GOOGLE_API_KEY falte.")

    # 2. Inicializa o client do Google GenAI
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Erro ao inicializar o client do Google GenAI: {e}")
        return None, None

    base_dir = Path(__file__).parent
    
    # 3. Lê arquivo JSON da pasta outputs/scraping/ (caso data não venha do Streamlit)
    if data is None:
        scraping_dir = base_dir / "outputs" / "scraping"
        
        # Pegamos o arquivo mais recente:
        latest_file = get_latest_scraping_file(scraping_dir)
        if not latest_file:
            print(f"Nenhum arquivo JSON encontrado em {scraping_dir}")
            return None, None

        print(f"Lendo dados raspados do arquivo: {latest_file}")
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        filename_stem = Path(latest_file).stem
    else:
        if topic:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            safe_topic = topic.replace(" ", "_").lower()
            filename_stem = f"{safe_topic}_{timestamp}"
        else:
            filename_stem = "from_streamlit"

    # 4. Garante que a pasta outputs/analysis exista
    analysis_dir = base_dir / "outputs" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"narrative_detection_{filename_stem}.json"
    output_filepath = analysis_dir / output_filename

    consolidated_results = {}
    prompts_enviados = {}

    # 5. Verifica as chaves e executa a análise
    
    # 5.1. Youtube
    if data and "youtube_data" in data and data["youtube_data"] and data["youtube_data"].get("videos"):
        print(">> Analisando YouTube...")
        try:
            prompt = create_youtube_prompt(data["youtube_data"])
            prompts_enviados["youtube"] = {"system_instruction": system_instruction_youtube, "user_prompt": prompt}
            result = generate_gemini_json(
                client=client,
                user_prompt=prompt,
                system_instruction=system_instruction_youtube,
                pydantic_schema=YoutubeAnalysis
            )
            consolidated_results["youtube_analysis"] = clean_pydantic_output(result)
            print("✓ Análise do YouTube finalizada com sucesso.")
        except Exception as e:
            print(f"Erro na análise de YouTube: {e}")
            consolidated_results["youtube_analysis"] = {"error": str(e)}

    # 5.2. Bluesky
    if data and "bluesky_data" in data and data["bluesky_data"] and data["bluesky_data"].get("posts"):
        print(">> Analisando Bluesky...")
        try:
            prompt = create_bluesky_prompt(data["bluesky_data"])
            prompts_enviados["bluesky"] = {"system_instruction": system_instruction_bluesky, "user_prompt": prompt}
            result = generate_gemini_json(
                client=client,
                user_prompt=prompt,
                system_instruction=system_instruction_bluesky,
                pydantic_schema=BlueskyAnalysis
            )
            consolidated_results["bluesky_analysis"] = clean_pydantic_output(result)
            print("✓ Análise do Bluesky finalizada com sucesso.")
        except Exception as e:
            print(f"Erro na análise do Bluesky: {e}")
            consolidated_results["bluesky_analysis"] = {"error": str(e)}

    # 5.3. News (Notícias)
    if data and "news_data" in data and data["news_data"] and data["news_data"].get("articles"):
        print(">> Analisando News...")
        try:
            prompt = create_news_prompt(data["news_data"])
            prompts_enviados["news"] = {"system_instruction": system_instruction_news, "user_prompt": prompt}
            result = generate_gemini_json(
                client=client,
                user_prompt=prompt,
                system_instruction=system_instruction_news,
                pydantic_schema=NewsAnalysis
            )
            consolidated_results["news_analysis"] = clean_pydantic_output(result)
            print("✓ Análise de News finalizada com sucesso.")
        except Exception as e:
            print(f"Erro na análise de News: {e}")
            consolidated_results["news_analysis"] = {"error": str(e)}

    # 6. Salva resultado consolidado
    print(f"Salvando resultados consolidados em: {output_filepath}")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(consolidated_results, f, ensure_ascii=False, indent=4)
        
    print("Processo finalizado!")
    return consolidated_results, prompts_enviados

if __name__ == "__main__":
    run_analysis()
