import os
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from google import genai
import streamlit as st
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.manifold import TSNE
import umap
from datetime import datetime

EMBEDDING_MODEL = "gemini-embedding-001"

# ============================================================
# 1. AGGREGATION: Selects the most recent file per topic.
#    Optional: restrict to files modified on or after a cutoff date.
# ============================================================
def get_latest_item_files_per_topic(
    topic_filter: Optional[str] = None,
    cutoff_date: Optional[str] = None  # "YYYY-MM-DD" format
) -> List[Path]:
    """
    Vasculha outputs/analysis/ e retorna o arquivo mais recente de cada tema.
    - topic_filter: substring para filtrar pelo nome do tema (ex: 'stf')
    - cutoff_date: se fornecido, restringe aos arquivos modificados >= esta data.
    """
    base_dir = Path(__file__).parent
    analysis_dir = base_dir / "outputs" / "analysis"
    if not analysis_dir.exists():
        return []

    files = list(analysis_dir.glob("items_for_embedding_*.json"))
    topics: Dict[str, List[Path]] = {}
    for f in files:
        stem = f.name.replace("items_for_embedding_", "")
        topic = stem.split("_202")[0] if "_202" in stem else stem

        if topic_filter and topic_filter.lower() not in topic.lower():
            continue

        if cutoff_date:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d")
            if mtime < cutoff:
                continue

        topics.setdefault(topic, []).append(f)

    latest_files = []
    for t, f_list in topics.items():
        f_list.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest_files.append(f_list[0])
        print(f"  [Dataset] Incluindo tema: '{t}' -> {f_list[0].name}")

    return latest_files


# ============================================================
# 2. STRENGTH INDEX helpers
# ============================================================
def compute_item_strength_index(df: pd.DataFrame) -> pd.Series:
    """
    Calcula o Índice de Força por Item (0-100) usando log(nps_narrative_power_score).
    Items sem NPS ou com valor 0 recebem strength_index = 0.
    """
    nps = df.get("nps_narrative_power_score", pd.Series(dtype=float)).fillna(0.0)
    # Log escalonado: só itens com NPS > 0
    positive_nps = nps.clip(lower=1)
    log_nps = np.log1p(positive_nps)
    max_log = log_nps.max()
    if max_log > 0:
        strength = (log_nps / max_log * 100).round(2)
    else:
        strength = pd.Series(0.0, index=df.index)
    # Items originalmente <= 0 zeram
    strength[nps <= 0] = 0.0
    return strength


def compute_cluster_strength(df: pd.DataFrame, cluster_col: str, strength_col: str) -> pd.DataFrame:
    """
    Agrega o Índice de Força por Cluster: mediana + total.
    """
    return (
        df.groupby(cluster_col, dropna=False)[strength_col]
        .agg(
            cluster_strength_median="median",
            cluster_strength_total="sum",
            cluster_item_count="count",
        )
        .reset_index()
    )


def compute_topic_view_force(items: List[dict]) -> pd.DataFrame:
    """
    Agrega nps_attention_volume e nps_narrative_power_score por tema (topic),
    gerando o 'View Force' do tema.
    """
    rows = []
    for item in items:
        rows.append(
            {
                "topic": item.get("topic", "unknown"),
                "nps_attention_volume": item.get("nps_attention_volume", 0) or 0,
                "nps_narrative_power_score": item.get("nps_narrative_power_score", 0) or 0,
                "source": item.get("source", "unknown"),
            }
        )
    df = pd.DataFrame(rows)
    topic_stats = (
        df.groupby("topic")
        .agg(
            total_attention_volume=("nps_attention_volume", "sum"),
            median_attention_volume=("nps_attention_volume", "median"),
            total_nps=("nps_narrative_power_score", "sum"),
            item_count=("nps_attention_volume", "count"),
        )
        .reset_index()
    )
    # Força de Views normalizada 0-100
    max_vol = topic_stats["total_attention_volume"].max()
    topic_stats["view_force"] = (
        (topic_stats["total_attention_volume"] / max_vol * 100).round(2)
        if max_vol > 0
        else 0.0
    )
    return topic_stats.sort_values("total_attention_volume", ascending=False)


# ============================================================
# 3. EMBEDDING AND CLUSTERING
# ============================================================
def generate_embeddings(client, texts: List[str]) -> List[np.ndarray]:
    embeddings = []
    print(f"  [Embeddings] Gerando {len(texts)} embeddings via Gemini...")
    for i, text in enumerate(texts):
        try:
            result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
            emb = np.array(result.embeddings[0].values)
            embeddings.append(emb)
        except Exception as e:
            print(f"  [Embeddings] Erro no item {i}: {e}")
            embeddings.append(np.zeros(768))
    return embeddings


def perform_clustering(embeddings: np.ndarray, k_fallback: int = 3):
    X = np.array(embeddings)
    if len(X) < 3:
        return np.zeros(len(X), dtype=int), "Fallback-Small", X

    n_neighbors = max(2, min(15, len(X) - 1))
    n_components = max(2, min(50, len(X) - 2))

    try:
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=0.1,
            metric="cosine",
            n_components=n_components,
            random_state=42,
        )
        X_reduced = reducer.fit_transform(X)
    except Exception as e:
        print(f"  [UMAP] Falhou, usando embeddings crus: {e}")
        X_reduced = X

    try:
        hdbscan = HDBSCAN(min_cluster_size=min(3, len(X)), min_samples=2)
        clusters = hdbscan.fit_predict(X_reduced)
        alg_used = "HDBSCAN"
        if len(set(clusters)) <= 1 or set(clusters) == {-1}:
            raise ValueError("HDBSCAN não encontrou agrupamentos.")
    except Exception as e:
        print(f"  [Cluster] Fallback para KMeans: {e}")
        kmeans = KMeans(n_clusters=min(k_fallback, len(X)), random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_reduced)
        alg_used = "KMeans"

    return clusters, alg_used, X_reduced


def sample_and_name_cluster(
    client,
    cluster_id: int,
    subset_items: List[dict],
    X_reduced_subset: np.ndarray,
    layer: str = "Macro",
) -> tuple:
    from scipy.spatial.distance import cdist

    n_items = len(subset_items)
    centroid = X_reduced_subset.mean(axis=0)
    distances = cdist(
        X_reduced_subset, centroid.reshape(1, -1), metric="euclidean"
    ).flatten()
    medoid_idx = np.argmin(distances)

    S = max(3, min(15, int(n_items * 0.1))) if n_items >= 3 else n_items
    closest_local_indices = np.argsort(distances)[:S]

    # Sample arguments: use canonical_claim + argument_rationale + stance_polarity
    sample_texts = []
    for i in closest_local_indices:
        item = subset_items[i]
        stance = item.get("stance_polarity", "?")
        direction = item.get("relation_direction", "?")
        claim = item.get("canonical_claim") or item.get("argument_claim_canonical") or "N/A"
        rationale = item.get("argument_rationale", "N/A")
        target = item.get("argument_target", "N/A")
        sample_texts.append(
            f"- [{stance.upper()} / {direction}] Alvo: {target}\n"
            f"  Argumento: {claim}\n"
            f"  Justificativa: {rationale}"
        )
    amostra_text = "\n".join(sample_texts)

    if layer.lower() == "macro":
        prompt = (
            "Você é um analista político especializado em mapeamento de narrativas.\n"
            "Os argumentos abaixo pertencem a um único cluster temático.\n"
            "Com base nas posturas (stance), alvos (target) e justificativas (rationale) dos argumentos,\n"
            "identifique o GRANDE TEMA que une este grupo e gere:\n"
            "  - 'name': um rótulo conciso (até 5 palavras) que capture a essência narrativa dominante\n"
            "  - 'summary': uma frase analítica explicando o que o cluster representa\n\n"
            f"Argumentos do cluster:\n{amostra_text}\n\n"
            'Retorne ESTRITAMENTE um JSON: {"name": "...", "summary": "..."}'
        )
    else:
        prompt = (
            "Você é um analista político especializado em mapeamento de viéses narrativos.\n"
            "Os argumentos abaixo pertencem a um SUB-GRUPO específico dentro de uma narrativa maior.\n"
            "Com base nas posturas (stance), alvos (target) e justificativas (rationale),\n"
            "identifique o VIÉS ou SUB-POSICIONAMENTO específico deste grupo e gere:\n"
            "  - 'name': um rótulo de viés (até 5 palavras) que distinga este sub-grupo dos demais\n"
            "  - 'summary': uma frase descrevendo o sub-posicionamento específico\n\n"
            f"Argumentos do sub-cluster:\n{amostra_text}\n\n"
            'Retorne ESTRITAMENTE um JSON: {"name": "...", "summary": "..."}'
        )
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash-lite", contents=prompt
        )
        text_resp = resp.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp.split("```json")[-1].split("```")[0].strip()
        elif text_resp.startswith("```"):
            text_resp = text_resp.split("```")[-1].split("```")[0].strip()
        data_llm = json.loads(text_resp)
        name = data_llm.get("name", f"{layer} Cluster {cluster_id}")
        summary = data_llm.get("summary", "")
        return name, summary, medoid_idx
    except Exception as e:
        print(f"  [LLM] Erro em {layer} cluster {cluster_id}: {e}")
        return f"{layer} Cluster {cluster_id}", "Amostra insuficiente.", medoid_idx


# ============================================================
# 4. MAIN PIPELINE — intra-topic clustering
# ============================================================
def run_per_topic_clustering(
    client,
    topic_filter: Optional[str] = None,
    cutoff_date: Optional[str] = None,
):
    print(
        f"\n[Clustering] Iniciando pipeline INTRA-TEMA"
        f" | Filtro: {topic_filter or 'Todos'}"
        f" | Data mínima: {cutoff_date or 'Sem restrição'}"
    )

    files = get_latest_item_files_per_topic(
        topic_filter=topic_filter, cutoff_date=cutoff_date
    )
    if not files:
        print("[Clustering] Nenhum arquivo encontrado com os parâmetros informados.")
        return

    # ------ Aggregate all items (needed for View Force cross-topic) ------
    all_items_for_analytics: List[dict] = []

    all_records: List[dict] = []
    topics_stats: List[dict] = []

    for f in files:
        # Derive topic slug from filename
        stem = f.name.replace("items_for_embedding_", "")
        topic_slug = stem.split("_202")[0] if "_202" in stem else stem

        try:
            with open(f, "r", encoding="utf-8") as fh:
                raw_items = json.load(fh)
        except Exception as e:
            print(f"  [Load] Ignorando {f.name}: {e}")
            continue

        items = [i for i in raw_items if i.get("included_in_argument_embedding", False)]
        all_items_for_analytics.extend(raw_items)

        if not items:
            print(f"  [Skip] {topic_slug}: sem itens elegíveis.")
            continue

        print(f"\n{'='*60}")
        print(f"  [Tema] '{topic_slug}' — {len(items)} itens elegíveis")

        texts = [item["text_used_for_embedding"] for item in items]
        embeddings = np.array(generate_embeddings(client, texts))

        # --- Macro layer ---
        print(f"  [Macro] Rodando clusterização...")
        macro_clusters, macro_alg, X_reduced_macro = perform_clustering(embeddings)
        unique_macro = set(macro_clusters)
        n_macro = len(unique_macro) - (1 if -1 in unique_macro else 0)
        print(f"  [Macro] {n_macro} cluster(s) via {macro_alg}")

        macro_names: dict = {}
        macro_summaries: dict = {}
        macro_medoids_global: dict = {}
        micro_clusters_global = np.full(len(items), -1)
        micro_names_global: dict = {}
        micro_medoids_global: dict = {}

        for c_mac in sorted(unique_macro):
            idx_mac = np.where(macro_clusters == c_mac)[0]

            if c_mac == -1:
                macro_names[c_mac] = "Ruído (-1)"
                macro_summaries[c_mac] = "Itens não agrupados."
                continue

            subset_items = [items[i] for i in idx_mac]
            X_sub = X_reduced_macro[idx_mac]
            m_name, m_sum, local_medoid = sample_and_name_cluster(
                client, c_mac, subset_items, X_sub, layer="Macro"
            )
            macro_names[c_mac] = m_name
            macro_summaries[c_mac] = m_sum
            macro_medoids_global[c_mac] = idx_mac[local_medoid]
            print(f"    -> Macro {c_mac+1}: {m_name} ({len(idx_mac)} itens)")

            # --- Micro layer ---
            sub_embeddings = embeddings[idx_mac]
            micro_clusters_local, micro_alg, X_reduced_micro = perform_clustering(sub_embeddings)
            unique_micro = set(micro_clusters_local)
            n_micro = len(unique_micro) - (1 if -1 in unique_micro else 0)
            print(f"       [Micro] {n_micro} sub-cluster(s) via {micro_alg}")

            for local_m_id in sorted(unique_micro):
                idx_mic_local = np.where(micro_clusters_local == local_m_id)[0]
                global_indices = idx_mac[idx_mic_local]

                for g_idx in global_indices:
                    micro_clusters_global[g_idx] = local_m_id

                if local_m_id == -1:
                    micro_names_global[f"{c_mac+1}.-1"] = "Ruído local do grupo"
                    continue

                mic_items = [items[i] for i in global_indices]
                X_mic_sub = X_reduced_micro[idx_mic_local]
                mic_name, mic_sum, mic_med_loc = sample_and_name_cluster(
                    client, local_m_id, mic_items, X_mic_sub, layer="Micro"
                )
                micro_key = f"{c_mac+1}.{local_m_id+1}"
                micro_names_global[micro_key] = mic_name
                micro_medoids_global[micro_key] = global_indices[mic_med_loc]
                print(f"         -> Micro {micro_key}: {mic_name}")

        # --- Build records for this topic ---
        topic_records: List[dict] = []
        for i, item in enumerate(items):
            item_copy = item.copy()
            c = int(macro_clusters[i])
            m_c = int(micro_clusters_global[i])

            if c == -1:
                item_copy["cluster"] = -1
                item_copy["cluster_name"] = "Ruído (-1)"
                item_copy["cluster_summary"] = macro_summaries.get(-1, "")
                item_copy["micro_cluster"] = -1
                item_copy["micro_cluster_name"] = "Ruído (-1)"
                item_copy["is_macro_medoid"] = False
                item_copy["is_micro_medoid"] = False
            else:
                item_copy["cluster"] = c + 1
                item_copy["cluster_name"] = macro_names.get(c, f"Macro {c+1}")
                item_copy["cluster_summary"] = macro_summaries.get(c, "")
                item_copy["is_macro_medoid"] = i == macro_medoids_global.get(c, -1)
                item_copy["micro_cluster"] = m_c + 1 if m_c != -1 else -1
                if m_c == -1:
                    item_copy["micro_cluster_name"] = "Ruído Local (-1)"
                    item_copy["is_micro_medoid"] = False
                else:
                    micro_key = f"{c+1}.{m_c+1}"
                    item_copy["micro_cluster_name"] = micro_names_global.get(
                        micro_key, f"Micro {micro_key}"
                    )
                    item_copy["is_micro_medoid"] = i == micro_medoids_global.get(micro_key, -1)

            if "stance_score" not in item_copy:
                item_copy["stance_score"] = 0.0
            if "tone_score" not in item_copy:
                item_copy["tone_score"] = item_copy.get("authority_score", 0.0)

            topic_records.append(item_copy)

        # Strength index for this topic
        df_topic = pd.DataFrame(topic_records)
        df_topic["strength_index"] = compute_item_strength_index(df_topic)

        # Cluster strength
        macro_strength = compute_cluster_strength(df_topic, "cluster", "strength_index")
        macro_strength.rename(
            columns={
                "cluster_strength_median": "macro_strength_median",
                "cluster_strength_total": "macro_strength_total",
            },
            inplace=True,
        )
        df_topic = df_topic.merge(
            macro_strength[["cluster", "macro_strength_median", "macro_strength_total"]],
            on="cluster",
            how="left",
        )

        all_records.extend(df_topic.to_dict(orient="records"))
        topics_stats.append({
            "topic": topic_slug,
            "n_items": len(items),
            "n_macro_clusters": n_macro,
            "algorithm": macro_alg,
            "total_attention_volume": int(df_topic["nps_attention_volume"].sum()) if "nps_attention_volume" in df_topic.columns else 0,
        })

    if not all_records:
        print("[Clustering] Nenhum registro gerado.")
        return

    df_all = pd.DataFrame(all_records)

    # ------ View Force por Tema ------
    print("\n[Analytics] Calculando View Force por Tema...")
    topic_view_force_df = compute_topic_view_force(all_items_for_analytics)
    print(topic_view_force_df[["topic", "total_attention_volume", "view_force", "item_count"]].to_string(index=False))

    # ------ Strength index global (re-normalize across all topics) ------
    df_all["strength_index"] = compute_item_strength_index(df_all)

    # ------ Save outputs ------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    base_name = f"per_topic_clusters_{timestamp}"

    base_dir = Path(__file__).parent
    clusters_dir = base_dir / "outputs" / "clusters"
    clusters_dir.mkdir(parents=True, exist_ok=True)
    embeddings_dir = base_dir / "outputs" / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    # Main Parquet + JSON
    parquet_path = embeddings_dir / f"embeddings_{base_name}.parquet"
    json_path = embeddings_dir / f"embeddings_{base_name}.json"
    df_all.to_parquet(parquet_path, index=False)
    df_all.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"\n[Saved] Parquet: {parquet_path.name}")
    print(f"[Saved] JSON:    {json_path.name}")

    # Topic View Force
    tvf_path = clusters_dir / f"topic_view_force_{base_name}.json"
    topic_view_force_df.to_json(tvf_path, orient="records", force_ascii=False, indent=2)
    print(f"[Saved] Topic View Force: {tvf_path.name}")

    # Cluster Strength summary
    cs_path = clusters_dir / f"cluster_strength_{base_name}.json"
    cluster_strength_summary = (
        df_all.groupby(["topic", "cluster", "cluster_name"])
        .agg(
            strength_median=("strength_index", "median"),
            strength_total=("strength_index", "sum"),
            item_count=("item_id", "count"),
            total_attention_volume=("nps_attention_volume", "sum"),
        )
        .reset_index()
        .sort_values(["topic", "strength_total"], ascending=[True, False])
    )
    cluster_strength_summary.to_json(cs_path, orient="records", force_ascii=False, indent=2)
    print(f"[Saved] Cluster Strength: {cs_path.name}")

    # Diagnostic
    diag_data = {
        "run_mode": "per_topic",
        "n_items_total": len(df_all),
        "n_topics": len(topics_stats),
        "n_macro_clusters_total": sum(t["n_macro_clusters"] for t in topics_stats),
        "mixed_run": True,
        "cutoff_date": cutoff_date,
        "topic_filter": topic_filter,
        "topics": topics_stats,
    }
    diagnostic_path = clusters_dir / f"diagnostic_{base_name}.json"
    with open(diagnostic_path, "w", encoding="utf-8") as fout:
        json.dump(diag_data, fout, ensure_ascii=False, indent=2)
    print(f"[Saved] Diagnostic: {diagnostic_path.name}")

    print(f"\n✅ Pipeline Intra-Tema completo!")
    print(f"   Temas: {len(topics_stats)} | Total de itens: {len(df_all)} | Base: {base_name}")



# ============================================================
# 5. ENTRY POINT
# ============================================================
def main(
    topic_filter: Optional[str] = None,
    cutoff_date: Optional[str] = None,
):
    print(
        f"Iniciando clustering Intra-Tema"
        f" | topic_filter={topic_filter} | cutoff_date={cutoff_date}"
    )
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        print("Aviso: GEMINI_API_KEY não encontrada nos secrets do Streamlit.")
        return
    client = genai.Client(api_key=api_key)
    run_per_topic_clustering(
        client, topic_filter=topic_filter, cutoff_date=cutoff_date
    )


if __name__ == "__main__":
    import sys

    # Usage:
    #   python run_clustering.py                    <- todos os temas mais recentes
    #   python run_clustering.py stf                <- filtro de tema
    #   python run_clustering.py stf 2026-04-11     <- STF a partir de 11/04
    #   python -c "from run_clustering import main; main(cutoff_date='2026-04-11')"
    t_filter = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    c_date = sys.argv[2] if len(sys.argv) > 2 else None
    main(topic_filter=t_filter, cutoff_date=c_date)
