import os
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from google import genai
import streamlit as st
from sklearn.cluster import KMeans, HDBSCAN
from sklearn.manifold import TSNE
import umap
from datetime import datetime

EMBEDDING_MODEL = "gemini-embedding-001"

def get_latest_item_files_per_topic() -> List[Path]:
    """
    1. Agregação de Dados ("Mixed Dataset"):
    Vasculha a pasta de outputs/analysis e seleciona apenas o arquivo mais recente
    de cada tema disponível.
    """
    base_dir = Path(__file__).parent
    analysis_dir = base_dir / "outputs" / "analysis"
    if not analysis_dir.exists():
        return []
    
    files = list(analysis_dir.glob("items_for_embedding_*.json"))
    topics = {}
    for f in files:
        stem = f.name.replace("items_for_embedding_", "")
        # Fallback de inferência do tópico: isolar tudo antes de '_202'
        topic = stem.split("_202")[0] if "_202" in stem else stem
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(f)
    
    latest_files = []
    for t, f_list in topics.items():
        f_list.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest_files.append(f_list[0])
        print(f"Dataset Mixed incluira: {t} -> {f_list[0].name}")
        
    return latest_files

def generate_embeddings(client, texts: List[str]) -> List[np.ndarray]:
    embeddings = []
    print(f"Gerando {len(texts)} embeddings via Gemini...")
    for i, text in enumerate(texts):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )
            emb = np.array(result.embeddings[0].values)
            embeddings.append(emb)
        except Exception as e:
            print(f"Erro ao gerar embedding {i}: {e}")
            embeddings.append(np.zeros(768))
    return embeddings

def perform_clustering(embeddings: np.ndarray, k_fallback: int = 3):
    X = np.array(embeddings)
    if len(X) < 3:
        return np.zeros(len(X), dtype=int), "Fallback-Small", X

    n_neighbors = min(15, len(X) - 1)
    n_neighbors = max(2, n_neighbors)
    n_components = min(50, len(X) - 2) if len(X) > 2 else 2
    n_components = max(2, n_components)

    try:
        reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=0.1, metric='cosine', n_components=n_components, random_state=42)
        X_reduced = reducer.fit_transform(X)
    except Exception as e:
        print(f"UMAP falhou, usando embeddings crus: {e}")
        X_reduced = X

    try:
        # AQUI É A RESTRIÇÃO ESTRITA: OS PARÂMETROS ABAIXO SERÃO USADOS EM AMBAS AS CAMADAS.
        hdbscan = HDBSCAN(min_cluster_size=min(3, len(X)), min_samples=2)
        clusters = hdbscan.fit_predict(X_reduced)
        alg_used = "HDBSCAN"
        
        # Fallback se encontrar apenas ruído ou muito pouco
        if len(set(clusters)) <= 1 or (set(clusters) == {-1}):
            raise ValueError("HDBSCAN não encontrou agrupamentos.")

    except Exception as e:
        print(f"Fallback para KMeans: {e}")
        kmeans = KMeans(n_clusters=min(k_fallback, len(X)), random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_reduced)
        alg_used = "KMeans"

    return clusters, alg_used, X_reduced

def sample_and_name_cluster(client, cluster_id: int, subset_items: List[dict], X_reduced_subset: np.ndarray, layer: str = "Macro") -> tuple:
    n_items = len(subset_items)
    centroid = X_reduced_subset.mean(axis=0)
    from scipy.spatial.distance import cdist
    distances = cdist(X_reduced_subset, centroid.reshape(1, -1), metric='euclidean').flatten()
    
    medoid_idx = np.argmin(distances)
    
    # Amostragem
    if n_items < 3: S = n_items
    else: S = max(3, min(15, int(n_items * 0.1)))
        
    closest_local_indices = np.argsort(distances)[:S]
    
    sample_texts = []
    for idx_amostra in closest_local_indices:
        item = subset_items[idx_amostra]
        sample_texts.append(f"Claim: {item.get('canonical_claim', 'N/A')} | Rationale: {item.get('argument_rationale', 'N/A')}")
        
    amostra_text = "\n".join(f"- {txt}" for txt in sample_texts)
    
    if layer.lower() == "macro":
        prompt = f"""Com base nesta amostra de múltiplos tópicos misturados, gere um NOME GERAL MACRO (até 4 palavras) que sintetize o grande tema deste cluster, e um RESUMO ANALÍTICO (uma frase).\n\nAmostra:\n{amostra_text}\n\nRetorne ESTRITAMENTE um JSON no formato: {{"name": "Nome", "summary": "Resumo"}}"""
    else:
        prompt = f"""Esta amostra é um SUB-GRUPO Específico dentro de uma grande narrativa. Avalie o viés ou sub-tema exato (Zoom In). Gere um NOME MICRO (até 4 palavras) focando no viés/postura, e um RESUMO (uma frase).\n\nAmostra:\n{amostra_text}\n\nRetorne ESTRITAMENTE um JSON no formato: {{"name": "Nome", "summary": "Resumo"}}"""
        
    try:
        resp = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
        text_resp = resp.text.strip()
        if text_resp.startswith("```json"): text_resp = text_resp.split("```json")[-1].split("```")[0].strip()
        elif text_resp.startswith("```"): text_resp = text_resp.split("```")[-1].split("```")[0].strip()
        
        data_llm = json.loads(text_resp)
        name = data_llm.get("name", f"{layer} Cluster {cluster_id}")
        summary = data_llm.get("summary", "")
        return name, summary, medoid_idx
    except Exception as e:
        print(f"Erro LLM em camada {layer} para cluster {cluster_id}: {e}")
        return f"{layer} Cluster {cluster_id}", "Amostra insuficiente.", medoid_idx


def run_mixed_hierarchical_clustering(client):
    print("\n[Hierarchical] Agregando arquivos recentes da Camada 1...")
    files = get_latest_item_files_per_topic()
    if not files:
        print("Nenhum arquivo elegivel encontrado em outputs/analysis/.")
        return

    # Construindo o dataset unificado Mixed
    mixed_items = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as f_in:
                items = json.load(f_in)
                valid_items = [i for i in items if i.get("included_in_argument_embedding", False)]
                mixed_items.extend(valid_items)
        except Exception as e:
            print(f"Ignorando arquivo {f.name} devido a erro: {e}")

    if not mixed_items:
        print("Dataset Mixed não contém itens elegíveis para embedding após o parse.")
        return

    print(f"[Hierarchical] Dataset Mixed Agregado! Total de Argumentos: {len(mixed_items)}")
    texts = [item["text_used_for_embedding"] for item in mixed_items]
    
    # 2. Camada 1: Clusterização Macro (Zoom Out)
    embeddings = np.array(generate_embeddings(client, texts))
    macro_clusters, macro_alg, X_reduced_macro = perform_clustering(embeddings)
    
    print(f"\n[Hierarchical] Camada MACRO (Zoom Out) concluída via {macro_alg}. Encontrados {len(set(macro_clusters))} clusters.")

    macro_names = {}
    macro_summaries = {}
    macro_medoids_global = {} # Para UI
    
    # Prepara array para micro clusters
    micro_clusters_global = np.full(len(mixed_items), -1)
    micro_names_global = {} # Map "MACRO.MICRO" -> Name
    micro_medoids_global = {}

    for c_mac in set(macro_clusters):
        idx_mac = np.where(macro_clusters == c_mac)[0]
        
        if c_mac == -1:
            macro_names[c_mac] = "Ruído (-1)"
            macro_summaries[c_mac] = "Itens não agrupados no zoom global."
            continue
            
        subset_items = [mixed_items[i] for i in idx_mac]
        X_sub = X_reduced_macro[idx_mac]
        
        m_name, m_sum, local_medoid = sample_and_name_cluster(client, c_mac, subset_items, X_sub, layer="Macro")
        macro_names[c_mac] = m_name
        macro_summaries[c_mac] = m_sum
        macro_medoids_global[c_mac] = idx_mac[local_medoid]
        print(f"-> MACRO {c_mac+1}: {m_name}")

        # 3. Camada 2: Clusterização Micro (Zoom In)
        # ==============================================================================
        # ATENÇÃO REDOBRADA / REGISTRO ARQUITETURAL:
        # Teoricamente, ao efetuarmos um Zoom In em uma sub-população de dados (o Macro Cluster), 
        # a densidade global é perdida e a nova projeção lida com um quantitativo 'N' severamente menor.
        # Em aplicações tradicionais, os hiperparâmetros (especialmente min_cluster_size e min_samples no HDBSCAN)
        # DEVERIAM ser recalibrados e atenuados para capturar nuanças menores, senão a segunda 
        # passagem enxergará boa parte como ruído puro (-1). 
        # Contudo, conforme restrição direta das regras de negócio desta implementação:
        # **Os algoritmos são instanciados identicamente via perform_clustering()**
        # Se min_cluster_size for inflexível (como min(3, len(X))), a granularidade pode virar gargalo em N pequenos.
        # ==============================================================================
        
        sub_embeddings = embeddings[idx_mac]
        micro_clusters_local, micro_alg, X_reduced_micro = perform_clustering(sub_embeddings)
        
        print(f"   [Camada MICRO] Clusters em Macro {c_mac+1}: {len(set(micro_clusters_local))} encontrados via {micro_alg}.")
        
        # Mapeando os Micro da visão local de volta para o Array Global
        for local_m_id in set(micro_clusters_local):
            idx_mic_local = np.where(micro_clusters_local == local_m_id)[0]
            global_indices = idx_mac[idx_mic_local]
            
            # Repassando a Id do micro cluster para o array global
            for g_idx in global_indices:
                micro_clusters_global[g_idx] = local_m_id
                
            if local_m_id == -1:
                micro_key = f"{c_mac+1}.-1"
                micro_names_global[micro_key] = "Ruído local do grupo"
                continue
                
            mic_subset_items = [mixed_items[i] for i in global_indices]
            X_mic_sub = X_reduced_micro[idx_mic_local]
            
            mic_name, mic_sum, mic_medoid_loc = sample_and_name_cluster(client, local_m_id, mic_subset_items, X_mic_sub, layer="Micro")
            
            micro_key = f"{c_mac+1}.{local_m_id+1}"
            micro_names_global[micro_key] = mic_name
            micro_medoids_global[micro_key] = global_indices[mic_medoid_loc]
            print(f"      -> MICRO {micro_key}: {mic_name}")


    # Mesclagem nos JSON finais
    records = []
    for i, item in enumerate(mixed_items):
        item_copy = item.copy()
        
        c = int(macro_clusters[i])
        m_c = int(micro_clusters_global[i])

        if c == -1:
            item_copy["cluster"] = -1
            item_copy["cluster_name"] = "Ruído (-1)"
            item_copy["cluster_summary"] = macro_summaries.get(-1, "")
            item_copy["micro_cluster"] = -1
            item_copy["micro_cluster_name"] = "Ruído (-1)"
        else:
            item_copy["cluster"] = c + 1
            item_copy["cluster_name"] = macro_names.get(c, f"Macro Cluster {c+1}")
            item_copy["cluster_summary"] = macro_summaries.get(c, "")
            item_copy["is_macro_medoid"] = (i == macro_medoids_global.get(c, -1))
            
            item_copy["micro_cluster"] = m_c + 1 if m_c != -1 else -1
            if m_c == -1:
                item_copy["micro_cluster_name"] = "Ruído Local (-1)"
                item_copy["is_micro_medoid"] = False
            else:
                micro_key = f"{c+1}.{m_c+1}"
                item_copy["micro_cluster_name"] = micro_names_global.get(micro_key, f"Micro Cluster {micro_key}")
                item_copy["is_micro_medoid"] = (i == micro_medoids_global.get(micro_key, -1))

        if "stance_score" not in item_copy: item_copy["stance_score"] = 0.0
        if "tone_score" not in item_copy: item_copy["tone_score"] = item_copy.get("authority_score", 0.0)
            
        records.append(item_copy)

    df = pd.DataFrame(records)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    base_name = f"mixed_clusters_{timestamp}"
    
    base_dir = Path(__file__).parent
    clusters_dir = base_dir / "outputs" / "clusters"
    clusters_dir.mkdir(parents=True, exist_ok=True)
    embeddings_dir = base_dir / "outputs" / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = embeddings_dir / f"embeddings_{base_name}.parquet"
    json_path = embeddings_dir / f"embeddings_{base_name}.json"
    df.to_parquet(parquet_path, index=False)
    df.to_json(json_path, orient="records", force_ascii=False, indent=4)

    # Diagnóstico da nova arquitetura
    diag_data = {
        "algorithm": macro_alg,
        "n_items": len(mixed_items),
        "n_macro_clusters": len(set(macro_clusters)) - (1 if -1 in macro_clusters else 0),
        "mixed_run": True
    }
    diagnostic_path = clusters_dir / f"diagnostic_{base_name}.json"
    with open(diagnostic_path, "w", encoding="utf-8") as f:
        json.dump(diag_data, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Pipeline Misto e Hierárquico completo! Salvo: {base_name}")

def main():
    print("Iniciando arquitetura de clustering Hierárquico Zoom In / Zoom Out...")
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        print("Aviso: GEMINI_API_KEY não foi encontrada.")
        return
    client = genai.Client(api_key=api_key)
    run_mixed_hierarchical_clustering(client)

if __name__ == "__main__":
    main()
