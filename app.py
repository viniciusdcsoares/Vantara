import streamlit as st
import json
from run_scraping import run_all_scrapers
from run_llm_analysis import run_analysis

st.set_page_config(page_title="Vantara Pipeline MVP", layout="wide")

# Inicializando varáveis no session_state para não as perdermos durante a re-renderização
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None
if 'prompts_enviados' not in st.session_state:
    st.session_state.prompts_enviados = None
if 'analise_llm' not in st.session_state:
    st.session_state.analise_llm = None

st.title("Vantara - Pipeline Analítico")
st.markdown("Orquestrador para scraping e análise via LLM.")

# Criando as 4 abas exigidas
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ Configuração e Execução", 
    "📊 Resultados da Coleta (Scraping)", 
    "📝 Auditoria de Prompts", 
    "🧠 Análise Consolidada (LLM)"
])

with tab1:
    st.header("Configurações do Pipeline")
    
    # Entradas do usuário
    topic = st.text_input("Tópico para pesquisa", value="Uso de Inteligencia Artificial")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("YouTube")
        max_videos = st.number_input("Máx Vídeos", min_value=1, max_value=50, value=3)
        max_comments = st.number_input("Máx Comentários/Vídeo", min_value=1, max_value=100, value=3)
        min_views = st.number_input("Min Views", min_value=0, max_value=1000000, value=1000)
        days_yt = st.number_input("Dias (Retroativo YT)", min_value=1, max_value=30, value=5)
        
    with col2:
        st.subheader("Bluesky")
        max_posts = st.number_input("Máx Posts", min_value=1, max_value=100, value=3)
        max_comments_bsky = st.number_input("Máx Comentários/Post", min_value=1, max_value=50, value=3)
        days_bsky = st.number_input("Dias (Retroativo Bluesky)", min_value=1, max_value=30, value=7)
        
    with col3:
        st.subheader("NewsAPI")
        max_articles = st.number_input("Máx Artigos", min_value=1, max_value=50, value=3)
        
    run_btn = st.button("Iniciar Pipeline Analítico", use_container_width=True, type="primary")
    
    if run_btn:
        if not topic.strip():
            st.error("Por favor, defina um tópico válido!")
        else:
            # 1. Scraping
            with st.spinner("Coletando dados... (Isso pode demorar alguns minutos)"):
                yt_config = {"max_videos": max_videos, "max_comments": max_comments, "min_views": min_views, "days": days_yt}
                bsky_config = {"max_posts": max_posts, "max_comments": max_comments_bsky, "days": days_bsky}
                ns_config = {"max_articles": max_articles}
                
                # Executa scrape diretamente
                try:
                    scraped_data = run_all_scrapers(
                        topic=topic,
                        scrapers_to_run=['youtube', 'bluesky', 'news'],
                        youtube_config=yt_config,
                        bluesky_config=bsky_config,
                        news_config=ns_config
                    )
                    st.session_state.scraping_results = scraped_data
                except Exception as e:
                    st.error(f"Erro durante a etapa de scraping: {e}")
                    scraped_data = None

            # 2. LLM Analysis
            if scraped_data:
                with st.spinner("Analisando com LLM..."):
                    try:
                        llm_results, prompts_used = run_analysis(data=scraped_data, topic=topic)
                        st.session_state.analise_llm = llm_results
                        st.session_state.prompts_enviados = prompts_used
                        
                        st.success("✅ Pipeline executado com sucesso! Navegue pelas abas acima para ver os resultados.")
                    except Exception as e:
                        st.error(f"Erro durante a análise LLM: {e}")

with tab2:
    st.header("Resultados do Scraping")
    data = st.session_state.scraping_results
    
    if data is None:
        st.info("Rode o pipeline primeiro na aba 'Configuração e Execução'.")
    else:
        # Fornecer botão de Download
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        st.download_button(
            label="Baixar scraping_results.json",
            data=json_data,
            file_name="scraping_results.json",
            mime="application/json"
        )
        
        # Caixas visuais
        for source, content in data.items():
            if content:
                with st.expander(f"📦 Dados Consolidados: {source.upper()}", expanded=False):
                    st.json(content)

with tab3:
    st.header("Auditoria de Prompts")
    prompts = st.session_state.prompts_enviados
    
    if prompts is None:
        st.info("Rode o pipeline primeiro na aba 'Configuração e Execução'.")
    else:
        # Fornecer botão de Download
        json_prompts = json.dumps(prompts, indent=4, ensure_ascii=False)
        st.download_button(
            label="Baixar prompts_enviados.json",
            data=json_prompts,
            file_name="prompts_enviados.json",
            mime="application/json"
        )
        
        for platform, prompt_data in prompts.items():
            with st.container():
                st.subheader(f"🗂️ Plataforma: {platform.title()}")
                col_sys, col_user = st.columns(2)
                with col_sys:
                    st.markdown("**System/Instruction Prompt:**")
                    st.code(prompt_data.get("system_instruction", ""), language="markdown")
                with col_user:
                    st.markdown("**User Prompt (com dados injetados):**")
                    st.code(prompt_data.get("user_prompt", ""), language="markdown")
                st.divider()

with tab4:
    st.header("Análise Consolidada (LLM)")
    analysis = st.session_state.analise_llm
    
    if analysis is None:
        st.info("Rode o pipeline primeiro na aba 'Configuração e Execução'.")
    else:
        # Fornecer botão de Download
        json_analysis = json.dumps(analysis, indent=4, ensure_ascii=False)
        st.download_button(
            label="Baixar analise_llm.json",
            data=json_analysis,
            file_name="analise_llm.json",
            mime="application/json"
        )
        
        for platform, content in analysis.items():
            with st.expander(f"🧠 Resultado da IA: {platform.upper()}", expanded=True):
                if 'error' in content:
                    st.error(f"Houve um erro nesta análise: {content['error']}")
                else:
                    st.json(content)
