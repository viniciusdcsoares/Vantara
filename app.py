import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.express as px
from run_scraping import run_all_scrapers
from run_llm_analysis import run_analysis

st.set_page_config(page_title="Pragma MVP", layout="wide")

# Inicializando varáveis no session_state para não as perdermos durante a re-renderização
if 'prompts_enviados' not in st.session_state:
    st.session_state.prompts_enviados = None
if 'last_run_updated' not in st.session_state:
    st.session_state.last_run_updated = False

st.title("Pragma - Pipeline Analítico")
st.markdown("Orquestrador para scraping e análise via LLM com visualização Histórica.")

# Criando as 5 abas exigidas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ Configuração e Execução", 
    "📊 Resultados da Coleta (Scraping)", 
    "📝 Auditoria de Prompts", 
    "🧠 Análise Consolidada (LLM)",
    "🌌 Análise de Clusters"
])

def get_latest_file_index(options: list) -> int:
    return 0


AUDIT_COLUMNS = [
    "item_id",
    "source",
    "cluster",
    "cluster_name",
    "claim_type",
    "argument_target",
    "target_type",
    "stance_polarity",
    "relation_direction",
    "canonical_claim",
    "argument_rationale",
    "included_in_argument_embedding",
    "text_used_for_embedding",
]


def _safe_options(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    values = (
        df[column]
        .fillna("unknown")
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    return values


def _apply_cluster_filters(
    df: pd.DataFrame,
    *,
    claim_types: list[str],
    stance_polarities: list[str],
    argument_targets: list[str],
    clusters: list[str],
) -> pd.DataFrame:
    filtered_df = df.copy()

    if claim_types and "claim_type" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["claim_type"].fillna("unknown").astype(str).isin(claim_types)
        ]

    if stance_polarities and "stance_polarity" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["stance_polarity"].fillna("unknown").astype(str).isin(stance_polarities)
        ]

    if argument_targets and "argument_target" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["argument_target"].fillna("unknown").astype(str).isin(argument_targets)
        ]

    if clusters and "cluster" in filtered_df.columns:
        cluster_map = filtered_df.apply(
            lambda row: "Ruído (-1)" if row['cluster'] == -1 else row.get('cluster_name', f"Cluster {row['cluster']}"),
            axis=1
        )
        filtered_df = filtered_df[cluster_map.isin(clusters)]

    return filtered_df


def _summarize_top_values(series: pd.Series, top_n: int = 3) -> str:
    if series is None:
        return "Sem dados"
    counts = (
        series.fillna("unknown")
        .astype(str)
        .value_counts()
        .head(top_n)
    )
    if counts.empty:
        return "Sem dados"
    return " | ".join(f"{label}: {count}" for label, count in counts.items())


def _sample_non_empty(series: pd.Series, sample_size: int = 3) -> list[str]:
    if series is None:
        return []
    values = [str(value).strip() for value in series.fillna("").tolist() if str(value).strip()]
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)
        if len(seen) >= sample_size:
            break
    return seen

with tab1:
    st.header("Configurações do Pipeline")
    
    # Entradas do usuário
    topic = st.text_input("Tópico para pesquisa", value="Uso de Inteligencia Artificial")
    embedding_variant = st.selectbox(
        "Campo usado para embedding",
        options=[
            "framing",
            "core_narrative",
            "canonical_claim",
            "embedding_ready_text",
            "argument_claim_canonical",
            "argument_claim_raw",
        ],
        index=3,
        help="Para a trilha de clusterização argumentativa, o pipeline sempre grava `text_used_for_embedding` a partir de `embedding_ready_text`. As demais opções ficam visíveis para auditoria e compatibilidade histórica.",
    )
    st.caption("A unidade argumentativa usada no clustering segue o formato fixo: Target, TargetType, Stance, Relation, Claim e Rationale.")
    
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
        st.subheader("News")
        max_articles = st.number_input("Máx Artigos", min_value=1, max_value=50, value=3)
        
    run_btn = st.button("Iniciar Pipeline Analítico", use_container_width=True, type="primary")
    
    if run_btn:
        if not topic.strip():
            st.error("Por favor, defina um tópico válido!")
        else:
            scraped_data = None
            # 1. Scraping
            with st.spinner("Coletando dados... (Isso pode demorar alguns minutos)"):
                yt_config = {"max_videos": max_videos, "max_comments": max_comments, "min_views": min_views, "days": days_yt}
                bsky_config = {"max_posts": max_posts, "max_comments": max_comments_bsky, "days": days_bsky}
                ns_config = {"max_articles": max_articles}
                
                try:
                    scraped_data = run_all_scrapers(
                        topic=topic,
                        scrapers_to_run=['youtube', 'bluesky', 'news'],
                        youtube_config=yt_config,
                        bluesky_config=bsky_config,
                        news_config=ns_config
                    )
                except Exception as e:
                    st.error(f"Erro durante a etapa de scraping: {e}")

            # 2. LLM Analysis
            if scraped_data:
                with st.spinner("Analisando com LLM e formatando Embeddings..."):
                    try:
                        llm_results, prompts_used, embedding_artifacts = run_analysis(
                            data=scraped_data,
                            topic=topic,
                            embedding_variant=embedding_variant,
                        )
                        st.session_state.prompts_enviados = prompts_used
                        
                        # Trigger run_clustering automatically
                        from run_clustering import run_mixed_hierarchical_clustering
                        from google import genai
                        api_key = st.secrets.get("GEMINI_API_KEY")
                        if api_key:
                            client = genai.Client(api_key=api_key)
                            run_mixed_hierarchical_clustering(client)

                        st.session_state.last_run_updated = True
                        st.success("✅ Pipeline executado com sucesso! Navegue pelas abas acima para ver os resultados.")
                    except Exception as e:
                        st.error(f"Erro durante a análise LLM: {e}")

with tab2:
    st.header("Resultados do Scraping")
    scraping_dir = Path("outputs/scraping")
    
    if not scraping_dir.exists() or not any(scraping_dir.iterdir()):
        st.info("Nenhum dado de scraping encontrado no histórico.")
    else:
        scrape_files = list(scraping_dir.glob("*.json"))
        if not scrape_files:
            st.info("Nenhum resultado de scraping JSON encontrado.")
        else:
            # Sort files by modification time descending
            scrape_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            scrape_names = [f.name for f in scrape_files]
            
            selected_scrape = st.selectbox("Selecione o arquivo de coleta histórica:", scrape_names, index=get_latest_file_index(scrape_names))
            
            if selected_scrape:
                file_path = scraping_dir / selected_scrape
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                json_data = json.dumps(data, indent=4, ensure_ascii=False)
                st.download_button(
                    label="Baixar scraping_results.json",
                    data=json_data,
                    file_name=selected_scrape,
                    mime="application/json",
                    key="download_scrape"
                )
                
                for source, content in data.items():
                    if content:
                        with st.expander(f"📦 Dados Consolidados: {source.upper()}", expanded=False):
                            st.json(content)

with tab3:
    st.header("Auditoria: Base de Conhecimento (Prompts & Schemas)")
    st.markdown(
        "Esta seção exibe o esqueleto base de extração que é utilizado por baixo dos panos na **Análise Consolidada (LLM)**. "
        "Não reflete dados processados de um run específico, mas sim as regras que ensinam o Gemini a pensar."
    )
    
    col_p, col_s = st.columns(2)
    base_dir = Path(__file__).parent
    
    prompt_file = base_dir / "llm_configs" / "prompts" / "narrative_detection.py"
    schema_file = base_dir / "llm_configs" / "schemas" / "narrative_detection.py"
    
    with col_p:
        st.subheader("📝 Prompts (Instruções Base)")
        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="python")
        else:
            st.warning(f"Não encontrado: {prompt_file.relative_to(base_dir)}")
            
    with col_s:
        st.subheader("🧩 Schemas (Pydantic)")
        if schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                st.code(f.read(), language="python")
        else:
            st.warning(f"Não encontrado: {schema_file.relative_to(base_dir)}")

with tab4:
    st.header("Análise Consolidada (LLM)")
    analysis_dir = Path("outputs/analysis")
    
    if not analysis_dir.exists() or not any(analysis_dir.glob("narrative_detection_*.json")):
        st.info("Nenhum dado de análise consolidada encontrado no histórico.")
    else:
        analysis_files = list(analysis_dir.glob("narrative_detection_*.json"))
        analysis_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        analysis_names = [f.name for f in analysis_files]
        
        selected_analysis = st.selectbox("Selecione o arquivo de análise histórica:", analysis_names, index=get_latest_file_index(analysis_names))
        
        if selected_analysis:
            file_path = analysis_dir / selected_analysis
            with open(file_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)
            
            json_analysis = json.dumps(analysis_data, indent=4, ensure_ascii=False)
            st.download_button(
                label="Baixar analise_llm.json",
                data=json_analysis,
                file_name=selected_analysis,
                mime="application/json",
                key="download_analysis"
            )
            
            for platform, content in analysis_data.items():
                with st.expander(f"🧠 Resultado da IA: {platform.upper()}", expanded=True):
                    if 'error' in content:
                        st.error(f"Houve um erro nesta análise: {content['error']}")
                    else:
                        st.json(content)

            items_filename = selected_analysis.replace("narrative_detection_", "items_for_embedding_")
            items_path = analysis_dir / items_filename
            if items_path.exists():
                with st.expander("🔎 Auditoria da unidade argumentativa usada para embedding", expanded=False):
                    with open(items_path, "r", encoding="utf-8") as f:
                        items_data = json.load(f)

                    items_df = pd.DataFrame(items_data)
                    for column in AUDIT_COLUMNS:
                        if column not in items_df.columns:
                            items_df[column] = None

                    st.caption("Campos de auditoria por item para validar alvo, postura, direção relacional, racional e inclusão na trilha argumentativa.")
                    st.dataframe(items_df[AUDIT_COLUMNS], use_container_width=True)

def get_clusters_root() -> Path:
    return Path("outputs/clusters")

def list_cluster_themes(clusters_root: Path) -> list[str]:
    """Retorna os run_ids baseados nos arquivos diagnostic gerados na pasta."""
    if not clusters_root.exists():
        return []
    diag_files = list(clusters_root.glob("diagnostic_*.json"))
    return sorted([f.stem.replace("diagnostic_", "") for f in diag_files], reverse=True)

import re

def humanize_topic_slug(slug: str) -> str:
    """Embeleza a visualização do run_id voltando a exibir o formato simples ideal (ex: Atuação Da Stf - 01/04/2026 14:32)"""
    match = re.search(r'(.+)_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})', slug)
    if match:
        tema = match.group(1).replace("_", " ").title()
        ano = match.group(2)
        mes = match.group(3)
        dia = match.group(4)
        hora = match.group(5)
        minuto = match.group(6)
        return f"{tema} ({dia}/{mes}/{ano} {hora}:{minuto})"
    
    # Fallback apenas para data (se houver arquivos antigos)
    match_fallback = re.search(r'(.+)_(\d{4})-(\d{2})-(\d{2})_', slug)
    if match_fallback:
        tema = match_fallback.group(1).replace("_", " ").title()
        ano = match_fallback.group(2)
        mes = match_fallback.group(3)
        dia = match_fallback.group(4)
        return f"{tema} ({dia}/{mes}/{ano})"
        
    return slug.replace("_", " ").title()

def load_cluster_manifest(clusters_root: Path, run_id: str) -> dict | None:
    """Extrai as métricas de diagnóstico."""
    diag_path = clusters_root / f"diagnostic_{run_id}.json"
    if diag_path.exists():
        with open(diag_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_cluster_members(run_id: str) -> pd.DataFrame | None:
    """Extrai a tabela Parquet que faz as vezes do mapping de members e tsne projection."""
    emb_path = Path("outputs/embeddings") / f"embeddings_{run_id}.parquet"
    if emb_path.exists():
        df = pd.read_parquet(emb_path)
        
        # --- CORRREÇÃO DE UI PARA DADOS ANTIGOS (Legacy Fix) ---
        if not df.empty and 'cluster' in df.columns:
            active_clusters = df[df['cluster'] != -1]['cluster']
            if not active_clusters.empty and active_clusters.min() == 0:
                # Caso o arquivo tenha começado em 0, deslocamos +1 na UI
                df['cluster'] = df['cluster'].apply(lambda x: x + 1 if x != -1 else -1)
                
                # Se o cluster_name persistido for puramente "Cluster 0", "Cluster 1", etc.
                # ajustamos para o novo ID para não confundir a legenda
                if 'cluster_name' in df.columns:
                    def _fix_name(row):
                        c_id = row['cluster']
                        c_name = str(row['cluster_name'])
                        if c_name == f"Cluster {c_id - 1}":
                            return f"Cluster {c_id}"
                        return c_name
                    df['cluster_name'] = df.apply(_fix_name, axis=1)
        # -------------------------------------------------------
        
        return df
    return None

def render_cluster_tab() -> None:
    st.header("Análise de Clusters (Narrativas)")
    clusters_root = get_clusters_root()

    run_ids = list_cluster_themes(clusters_root)
    if not run_ids:
        st.warning("Nenhum dado de clusterização encontrado no histórico.")
        return

    # Selectbox de execução
    options_map = {r: humanize_topic_slug(r) for r in run_ids}
    selected_run = st.selectbox(
        "Selecione a execução de clustering:",
        options=run_ids,
        format_func=lambda x: options_map[x],
        index=get_latest_file_index(run_ids),
    )

    if not selected_run:
        return

    diag_data = load_cluster_manifest(clusters_root, selected_run)
    df = load_cluster_members(selected_run)

    if df is None or df.empty:
        st.error("Arquivos de embeddings ou diagnóstico não encontrados para a seleção.")
        return

    for column in AUDIT_COLUMNS:
        if column not in df.columns:
            df[column] = None

    # ── Métricas gerais ──────────────────────────────────────────────
    if diag_data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Argumentos Analisados", diag_data.get("n_items_total", diag_data.get("n_items", 0)))
        c2.metric("Temas Incluídos", diag_data.get("n_topics", df["topic"].nunique() if "topic" in df.columns else "–"))
        c3.metric("Macro Clusters Total", diag_data.get("n_macro_clusters_total", diag_data.get("n_macro_clusters", 0)))
        c4.metric("Algoritmo Base", diag_data.get("algorithm", diag_data.get("topics", [{}])[0].get("algorithm", "–") if diag_data.get("topics") else "–"))

    st.divider()

    # ── Nível 0: Seleção de Tema ─────────────────────────────────────
    has_topic = "topic" in df.columns
    is_hierarchical = "micro_cluster" in df.columns

    if has_topic:
        topics_available = sorted(df["topic"].dropna().unique())
        topic_options = ["🌍 Visão Geral — Todos os Temas"] + [f"📌 {t}" for t in topics_available]
        topic_selection = st.selectbox("🗂️ Selecione um Tema ou veja a visão geral:", topic_options)
    else:
        topic_selection = "🌍 Visão Geral — Todos os Temas"
        topics_available = []

    # ── Filtrar por tema ─────────────────────────────────────────────
    if topic_selection == "🌍 Visão Geral — Todos os Temas":
        df_topic = df.copy()
        selected_topic_name = None
    else:
        selected_topic_name = topic_selection.replace("📌 ", "")
        df_topic = df[df["topic"] == selected_topic_name].copy()

    if df_topic.empty:
        st.warning("Nenhum item encontrado para o tema selecionado.")
        return

    # ── Nível 1: Seleção de Macro Cluster (apenas se um tema foi escolhido) ──
    selected_macro_id = None
    selected_macro_name = None

    if selected_topic_name is not None and is_hierarchical:
        macro_vals = df_topic[df_topic["cluster"] != -1][["cluster", "cluster_name"]].drop_duplicates().sort_values("cluster")
        macro_options_list = ["🔭 Visão Macro — Todos os Clusters do Tema"]
        macro_id_map = {}
        for _, r in macro_vals.iterrows():
            cname = r["cluster_name"] if pd.notna(r["cluster_name"]) else f"Cluster {r['cluster']}"
            opt = f"🔵 {cname}"
            macro_options_list.append(opt)
            macro_id_map[opt] = (int(r["cluster"]), cname)

        macro_selection = st.selectbox("📊 Selecione um Macro Cluster:", macro_options_list)

        if macro_selection != "🔭 Visão Macro — Todos os Clusters do Tema":
            selected_macro_id, selected_macro_name = macro_id_map[macro_selection]
            df_topic = df_topic[df_topic["cluster"] == selected_macro_id].copy()

            # ── Nível 2: Seleção de Micro Cluster ──
            if not df_topic.empty:
                micro_vals = df_topic[df_topic["micro_cluster"] != -1][["micro_cluster", "micro_cluster_name"]].drop_duplicates().sort_values("micro_cluster")
                micro_options_list = ["🔍 Todos os Micro Clusters"]
                micro_id_map = {}
                for _, r in micro_vals.iterrows():
                    mname = r["micro_cluster_name"] if pd.notna(r["micro_cluster_name"]) else f"Micro {r['micro_cluster']}"
                    opt = f"🟣 {mname}"
                    micro_options_list.append(opt)
                    micro_id_map[opt] = (int(r["micro_cluster"]), mname)

                if len(micro_options_list) > 1:
                    micro_selection = st.selectbox("🔬 Selecione um Micro Cluster:", micro_options_list)
                    if micro_selection != "🔍 Todos os Micro Clusters":
                        selected_micro_id, _ = micro_id_map[micro_selection]
                        df_topic = df_topic[df_topic["micro_cluster"] == selected_micro_id].copy()

    if df_topic.empty:
        st.warning("Nenhum item encontrado para o nível de navegação selecionado.")
        return

    st.divider()

    # ── Filtros de auditoria ─────────────────────────────────────────
    with st.expander("⚙️ Filtros de Auditoria", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            selected_claim_types = st.multiselect("Claim type", options=_safe_options(df_topic, "claim_type"), default=[])
        with fc2:
            selected_stances = st.multiselect("Stance polarity", options=_safe_options(df_topic, "stance_polarity"), default=[])
        with fc3:
            selected_targets = st.multiselect("Argument target", options=_safe_options(df_topic, "argument_target"), default=[])

    filtered_df = _apply_cluster_filters(
        df_topic,
        claim_types=selected_claim_types,
        stance_polarities=selected_stances,
        argument_targets=selected_targets,
        clusters=[],
    )

    if filtered_df.empty:
        st.warning("Nenhum item corresponde aos filtros selecionados.")
        return

    # ── Gráfico de dispersão ─────────────────────────────────────────
    df_scatter = filtered_df.copy()
    color_map = {"Ruído (-1)": "#D3D3D3", "Ruído Local (-1)": "#D3D3D3"}

    # Determinar o que será cor/agrupamento no plot:
    # • Visão Geral → agrupar por Tema (bolhas)
    # • Tema selecionado sem macro → agrupar por Macro Cluster (bolhas)
    # • Macro selecionado → pontos individuais coloridos por Micro Cluster

    if selected_topic_name is None:
        # Visão Geral: uma bolha por tema
        if "topic" in df_scatter.columns:
            df_scatter["plot_cluster"] = df_scatter["topic"]
            df_scatter2 = df_scatter.groupby("plot_cluster").agg(
                stance_score=("stance_score", "mean"),
                tone_score=("tone_score", "mean"),
                count=("item_id", "count"),
                total_volume=("nps_attention_volume", "sum"),
            ).reset_index()
            df_scatter2["custom_hover"] = df_scatter2.apply(
                lambda r: f"<b>{r['plot_cluster']}</b><br>Argumentos: {r['count']}<br>Volume de Atenção: {int(r['total_volume']):,}", axis=1
            )
            size_col, max_size = "total_volume", 60
        else:
            df_scatter2 = df_scatter
            df_scatter2["plot_cluster"] = "Sem Tema"
            df_scatter2["custom_hover"] = "item"
            size_col, max_size = None, 10
        plot_cat_orders = sorted(df_scatter2["plot_cluster"].unique())

    elif selected_macro_id is None:
        # Tema selecionado → bolhas por Macro Cluster
        df_scatter["plot_cluster"] = df_scatter.apply(
            lambda r: "Ruído (-1)" if r["cluster"] == -1 else (r["cluster_name"] if pd.notna(r.get("cluster_name")) else f"Cluster {r['cluster']}"), axis=1
        )
        df_scatter2 = df_scatter.groupby(["cluster", "plot_cluster"]).agg(
            stance_score=("stance_score", "mean"),
            tone_score=("tone_score", "mean"),
            count=("item_id", "count"),
            strength=("strength_index", "sum") if "strength_index" in df_scatter.columns else ("item_id", "count"),
        ).reset_index()
        df_scatter2["custom_hover"] = df_scatter2.apply(
            lambda r: f"<b>{r['plot_cluster']}</b><br><br>Argumentos: {r['count']}", axis=1
        )
        size_col, max_size = "count", 45
        plot_cat_orders = df_scatter2["plot_cluster"].tolist()

    else:
        # Macro selecionado → pontos individuais por Micro Cluster
        df_scatter["plot_cluster"] = df_scatter.apply(
            lambda r: "Ruído Local (-1)" if r.get("micro_cluster", -1) == -1 else (r.get("micro_cluster_name") or f"Micro {r['micro_cluster']}"), axis=1
        )
        df_scatter2 = df_scatter.copy()
        df_scatter2["custom_hover"] = df_scatter2.apply(
            lambda r: f"<b>{r['plot_cluster']}</b><br><br>{r.get('canonical_claim', 'N/A')}<br><br>Fonte: {r.get('source', '?')}", axis=1
        )
        df_scatter2["point_size"] = 1
        size_col, max_size = "point_size", 12
        micro_order = {row["plot_cluster"]: (999 if row.get("micro_cluster", -1) == -1 else row.get("micro_cluster", 0)) for _, row in df_scatter2.iterrows()}
        plot_cat_orders = sorted(micro_order.keys(), key=lambda x: micro_order[x])

    scatter_kwargs = dict(
        x="stance_score",
        y="tone_score",
        color="plot_cluster",
        custom_data=["custom_hover"],
        color_discrete_map=color_map,
        category_orders={"plot_cluster": plot_cat_orders},
        title="",
        labels={"plot_cluster": "Grupos"},
    )
    if size_col:
        scatter_kwargs["size"] = size_col
        scatter_kwargs["size_max"] = max_size

    fig = px.scatter(df_scatter2, **scatter_kwargs)
    fig.update_traces(
        hovertemplate='%{customdata[0]}<extra></extra>',
        marker=dict(opacity=0.85, line=dict(width=1, color="DarkSlateGrey")),
    )
    fig.update_xaxes(title_text="Posicionamento Político (-1 Crítica Severa a +1 Apoio Total)")
    fig.update_yaxes(title_text="Tom do Discurso (-1 Agressivo a +1 Analítico)")
    fig.update_layout(height=600, hovermode="closest", template="plotly_white")
    fig.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.3)
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.3)
    st.plotly_chart(fig, use_container_width=True)

    # ── Detalhamento textual ──────────────────────────────────────────
    st.divider()
    st.subheader("Detalhamento Textual dos Clusters")

    if "stance_polarity" in filtered_df.columns:
        stance_counts = filtered_df[filtered_df["cluster"] != -1]["stance_polarity"].fillna("unknown").value_counts()
        if not stance_counts.empty:
            st.caption("Distribuição de postura: " + " | ".join(f"{s}: {v}" for s, v in stance_counts.items()))

    # Agrupar por nível atual
    if selected_macro_id is not None:
        group_col = "micro_cluster"
        name_col = "micro_cluster_name"
    else:
        group_col = "cluster"
        name_col = "cluster_name"

    sorted_clusters = sorted(filtered_df[group_col].unique())
    if -1 in sorted_clusters:
        sorted_clusters.remove(-1)
        sorted_clusters.append(-1)

    for c_id in sorted_clusters:
        group = filtered_df[filtered_df[group_col] == c_id]
        if group.empty:
            continue
        if c_id == -1:
            label, icon = "Ruído / Desconsiderados", "⚠️"
        else:
            cname = group[name_col].iloc[0] if name_col in group.columns else None
            label = cname if pd.notna(cname) else f"Grupo {c_id}"
            icon = "💠"

        size = len(group)
        with st.expander(f"{icon} {label} — {size} argumentos", expanded=(c_id != -1 and size > 0)):
            sources = group["source"].value_counts()
            st.caption("**Fontes:** " + " | ".join(f"{s}: {v}" for s, v in sources.items()))
            st.markdown(f"**Total de itens:** {size}")
            st.markdown(f"**Polaridades dominantes:** {_summarize_top_values(group.get('stance_polarity'))}")

            table_data = []
            for _, row in group.iterrows():
                table_data.append({
                    "Fonte": row.get("source"),
                    "Alvo": row.get("argument_target", ""),
                    "Postura": row.get("stance_polarity", ""),
                    "Direção": row.get("relation_direction", ""),
                    "Tipo": row.get("claim_type", ""),
                    "Justificativa": row.get("argument_rationale", ""),
                    "Claim": row.get("canonical_claim") or row.get("text_used_for_embedding", ""),
                })
            df_table = pd.DataFrame(table_data)
            if not df_table.empty:
                df_table.set_index("Fonte", inplace=True)
            st.table(df_table)


with tab5:
    render_cluster_tab()

