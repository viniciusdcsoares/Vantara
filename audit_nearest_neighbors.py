import json
from pathlib import Path
from typing import Optional

import numpy as np
import streamlit as st
from google import genai


EMBEDDING_MODEL = "gemini-embedding-001"
SIMILARITY_METRIC = "cosine_similarity"


def _cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    safe_norms = np.where(norms == 0, 1.0, norms)
    normalized = vectors / safe_norms
    return normalized @ normalized.T


def audit_nearest_neighbors(
    items_artifact_path: str,
    top_k: int = 3,
    output_path: Optional[str] = None,
) -> dict:
    artifact_path = Path(items_artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {artifact_path}")

    with artifact_path.open("r", encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        raise ValueError("Artefato de itens para embedding esta vazio.")

    items = [item for item in items if item.get("included_in_argument_embedding", True)]
    if not items:
        raise ValueError("Nao ha itens incluidos na trilha principal de embedding argumentativo.")

    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY nao encontrada em st.secrets.")

    client = genai.Client(api_key=api_key)

    texts = [item["text_used_for_embedding"] for item in items]
    vectors = []
    fallback_zero_vector_count = 0

    for i, text in enumerate(texts):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
            )
            vectors.append(np.array(result.embeddings[0].values, dtype=float))
        except Exception:
            vectors.append(np.zeros(768, dtype=float))
            fallback_zero_vector_count += 1

    all_vectors = np.vstack(vectors)
    similarity = _cosine_similarity_matrix(all_vectors)

    rows = []
    for i, item in enumerate(items):
        neighbor_indices = np.argsort(similarity[i])[::-1]
        top_neighbors = []
        for idx in neighbor_indices:
            if idx == i:
                continue
            neighbor = items[idx]
            top_neighbors.append({
                "neighbor_item_id": neighbor["item_id"],
                "neighbor_source": neighbor["source"],
                "neighbor_canonical_claim": neighbor.get("canonical_claim"),
                "neighbor_argument_claim_canonical": neighbor.get("argument_claim_canonical"),
                "neighbor_argument_claim_raw": neighbor.get("argument_claim_raw"),
                "neighbor_text_used_for_embedding": neighbor.get("text_used_for_embedding"),
                "neighbor_embedding_text_source": neighbor.get("embedding_text_source"),
                "similarity_score": float(similarity[i, idx]),
            })
            if len(top_neighbors) >= top_k:
                break

        rows.append({
            "item_id": item["item_id"],
            "topic": item["topic"],
            "source": item["source"],
            "canonical_claim": item.get("canonical_claim"),
            "argument_claim_canonical": item.get("argument_claim_canonical"),
            "argument_claim_raw": item.get("argument_claim_raw"),
            "text_used_for_embedding": item.get("text_used_for_embedding"),
            "embedding_text_source": item.get("embedding_text_source"),
            "top_neighbors": top_neighbors,
        })

    run_id = artifact_path.stem.replace("items_for_embedding_", "")
    final_output_path = Path(output_path) if output_path else (
        artifact_path.parent.parent / "embeddings" / f"nearest_neighbors_{run_id}.json"
    )
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "run_id": run_id,
        "items_artifact_path": str(artifact_path),
        "embedding_model": EMBEDDING_MODEL,
        "similarity_metric": SIMILARITY_METRIC,
        "top_k": top_k,
        "item_count": len(items),
        "fallback_zero_vector_count": fallback_zero_vector_count,
        "neighbors": rows,
    }

    with final_output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    return {
        "run_id": run_id,
        "output_path": str(final_output_path),
        "embedding_model": EMBEDDING_MODEL,
        "similarity_metric": SIMILARITY_METRIC,
        "top_k": top_k,
        "item_count": len(items),
        "fallback_zero_vector_count": fallback_zero_vector_count,
    }


if __name__ == "__main__":
    default_items_path = (
        Path(__file__).parent
        / "outputs"
        / "analysis"
        / "items_for_embedding_legalização_do_aborto_2026-03-30_12-35_canonical_claim.json"
    )
    result = audit_nearest_neighbors(str(default_items_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
