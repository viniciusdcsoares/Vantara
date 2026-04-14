import os
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
from google import genai

from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

from llm_configs.functions import generate_gemini_json
from llm_configs.prompts.narrative_detection import (
    create_youtube_single_prompt,
    create_bluesky_single_prompt,
    create_news_single_prompt,
    create_comment_alignment_prompt,
    system_instruction_youtube,
    system_instruction_bluesky,
    system_instruction_news,
    system_instruction_comment_alignment,
)
from llm_configs.schemas.narrative_detection import (
    BlueskyAnalysis,
    YoutubeAnalysis,
    NewsAnalysis,
    CommentAnalysis,
    EngagementMetrics,
)

VALID_EMBEDDING_VARIANTS = {
    "framing",
    "core_narrative",
    "canonical_claim",
    "embedding_ready_text",
    "argument_claim_canonical",
    "argument_claim_raw",
}
PRIMARY_ARGUMENT_EMBEDDING_VARIANT = "embedding_ready_text"
AUXILIARY_ARGUMENT_AUDIT_VARIANT = "argument_claim_raw"
ARGUMENT_EMBEDDING_VARIANTS = {
    "canonical_claim",  # legacy compatibility path
    PRIMARY_ARGUMENT_EMBEDDING_VARIANT,
    AUXILIARY_ARGUMENT_AUDIT_VARIANT,
}
EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_TEXT_FALLBACKS = {
    "framing": "Sem enquadramento identificado",
    "core_narrative": "Sem narrativa principal identificada",
    "canonical_claim": "Sem claim canonica identificada",
    "embedding_ready_text": "Target: unknown. TargetType: other. Stance: neutral. Relation: describe. Claim: Sem claim canonica identificada. Rationale: insufficient argumentative detail.",
    "argument_claim_canonical": "Sem argument claim canonical identificada",
    "argument_claim_raw": "Sem argument claim raw identificada",
}


# ==========================================
# HELPERS
# ==========================================

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


def _get_dominant_framing(clean_result: dict) -> str:
    """Extrai o dominant_framing (ou journalistic_framing para News) de um resultado limpo."""
    try:
        output = clean_result.get("result", {}).get("output", {})
        # YoutubeAnalysis e BlueskyAnalysis usam 'dominant_framing'
        framing = output.get("dominant_framing")
        # NewsAnalysis usa 'journalistic_framing'
        if not framing:
            framing = output.get("journalistic_framing", "")
        return framing or ""
    except Exception:
        return ""


def _get_output(clean_result: dict) -> dict:
    try:
        return clean_result.get("result", {}).get("output", {})
    except Exception:
        return {}


def _get_core_narrative(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("core_narrative", "") or ""
    except Exception:
        return ""


def _get_canonical_claim(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("canonical_claim", "") or ""
    except Exception:
        return ""


def _get_claim_type(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("claim_type", "") or ""
    except Exception:
        return ""


def _get_factual_claim(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("factual_claim", "") or ""
    except Exception:
        return ""


def _get_argument_claim_canonical(clean_result: dict) -> str:
    try:
        output = _get_output(clean_result)
        return (
            output.get("argument_claim_canonical")
            or output.get("argument_claim")
            or ""
        )
    except Exception:
        return ""


def _get_argument_claim_raw(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("argument_claim_raw", "") or ""
    except Exception:
        return ""


def _build_item_id(source: str, index: int) -> str:
    return f"{source.lower()}_{index + 1:04d}"


def _normalize_text(value: Optional[str], fallback: str = "") -> str:
    normalized = (value or "").strip()
    return normalized or fallback


def _get_argument_target(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("argument_target", "") or ""
    except Exception:
        return ""


def _get_target_type(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("target_type", "") or ""
    except Exception:
        return ""


def _get_stance_polarity(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("stance_polarity", "") or ""
    except Exception:
        return ""


def _get_relation_direction(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("relation_direction", "") or ""
    except Exception:
        return ""


def _get_argument_rationale(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("argument_rationale", "") or ""
    except Exception:
        return ""


def _get_embedding_ready_text(clean_result: dict) -> str:
    try:
        return _get_output(clean_result).get("embedding_ready_text", "") or ""
    except Exception:
        return ""


def _build_embedding_ready_text(
    *,
    canonical_claim: str,
    claim_type: str,
    argument_target: str,
    target_type: str,
    stance_polarity: str,
    relation_direction: str,
    argument_rationale: str,
    argument_claim_canonical: str,
) -> str:
    claim_text = _normalize_text(
        canonical_claim,
        _normalize_text(argument_claim_canonical, "Sem claim canonica identificada"),
    )
    target_text = _normalize_text(argument_target, "unknown")
    target_type_text = _normalize_text(target_type, "other")
    stance_text = _normalize_text(stance_polarity, "neutral")

    if claim_type == "factual":
        relation_fallback = "report"
    elif claim_type == "descriptive":
        relation_fallback = "describe"
    else:
        relation_fallback = "state"

    relation_text = _normalize_text(relation_direction, relation_fallback)
    rationale_text = _normalize_text(
        argument_rationale,
        "insufficient argumentative detail" if claim_type in {"factual", "descriptive"} else "implicit justification",
    )

    return (
        f"Target: {target_text}. "
        f"TargetType: {target_type_text}. "
        f"Stance: {stance_text}. "
        f"Relation: {relation_text}. "
        f"Claim: {claim_text}. "
        f"Rationale: {rationale_text}."
    )


def _select_embedding_text(
    embedding_variant: str,
    core_narrative: str,
    framing_text: str,
    canonical_claim: str,
    embedding_ready_text: str,
    argument_claim_canonical: str,
    argument_claim_raw: str,
) -> tuple[str, bool, str]:
    del embedding_variant, core_narrative, framing_text, canonical_claim, argument_claim_canonical, argument_claim_raw
    selected_text = (embedding_ready_text or "").strip()
    selected_field = "embedding_ready_text"
    missing_selected_text = not bool(selected_text)
    if missing_selected_text:
        selected_text = DEFAULT_TEXT_FALLBACKS["embedding_ready_text"]
        selected_field = "embedding_ready_text_fallback"
    return selected_text, missing_selected_text, selected_field


def _should_include_in_argument_embedding(
    *,
    claim_type: str,
    argument_target: str,
    stance_polarity: str,
    argument_rationale: str,
) -> tuple[bool, Optional[str]]:
    return True, None


def _get_original_content(item: dict, source: str) -> str:
    """Retorna um resumo legível do conteúdo original do item conforme a fonte."""
    if source == "YouTube":
        title = item.get("title", "")
        channel = item.get("channel", "")
        desc = (item.get("description") or "")[:300]
        return f"[{channel}] {title} — {desc}"
    elif source == "Bluesky":
        author = item.get("author", "")
        text = (item.get("text") or "")[:400]
        return f"@{author}: {text}"
    elif source == "News":
        title = item.get("title", "")
        src = item.get("source", "")
        desc = (item.get("description") or "")[:300]
        return f"[{src}] {title} — {desc}"
    return str(item)[:400]


def _build_embedding_item(
    *,
    item_id: str,
    source: str,
    topic: str,
    original: str,
    output: dict,
    core_narrative: str,
    framing: str,
    canonical_claim: str,
    claim_type: str,
    factual_claim: str,
    argument_target: str,
    target_type: str,
    stance_polarity: str,
    relation_direction: str,
    argument_rationale: str,
    embedding_ready_text: str,
    argument_claim_canonical: str,
    argument_claim_raw: str,
    embedding_variant: str,
    nps: dict | None = None,
) -> dict:
    # Preferred operational rule:
    # - main embedding unit: embedding_ready_text
    # - auxiliary audit trail: argument_claim_raw
    # - factual/descriptive items: stored, but excluded from the main argument vector space
    text_used_for_embedding, missing_selected_text, embedding_text_source = _select_embedding_text(
        embedding_variant=embedding_variant,
        core_narrative=core_narrative,
        framing_text=framing,
        canonical_claim=canonical_claim,
        embedding_ready_text=embedding_ready_text,
        argument_claim_canonical=argument_claim_canonical,
        argument_claim_raw=argument_claim_raw,
    )
    included_in_argument_embedding, exclusion_reason = _should_include_in_argument_embedding(
        claim_type=claim_type,
        argument_target=argument_target,
        stance_polarity=stance_polarity,
        argument_rationale=argument_rationale,
    )
    claim_missing = not bool((canonical_claim or "").strip())
    claim_fallback_used = embedding_text_source.endswith("_fallback")

    return {
        "item_id": item_id,
        "source": source,
        "topic": topic,
        "conteudo_original": original,
        "core_narrative": core_narrative,
        "dominant_framing": output.get("dominant_framing"),
        "journalistic_framing": output.get("journalistic_framing"),
        "claim_type": claim_type,
        "factual_claim": factual_claim or None,
        "argument_target": argument_target or None,
        "target_type": target_type or None,
        "stance_polarity": stance_polarity or None,
        "relation_direction": relation_direction or None,
        "argument_rationale": argument_rationale or None,
        "embedding_ready_text": embedding_ready_text or None,
        "argument_claim_canonical": argument_claim_canonical or None,
        "argument_claim_raw": argument_claim_raw or None,
        "canonical_claim": canonical_claim or None,
        "text_used_for_embedding": text_used_for_embedding,
        "embedding_text_source": embedding_text_source,
        "embedding_variant": embedding_variant,
        "claim_missing": claim_missing,
        "claim_fallback_used": claim_fallback_used,
        "missing_selected_text": missing_selected_text,
        "included_in_argument_embedding": included_in_argument_embedding,
        "argument_embedding_exclusion_reason": exclusion_reason,
        "stance_score": float(output.get("stance_score", 0.0)),
        "tone_score": float(output.get("tone_score", 0.0)),
        # NPS fields — populated for YouTube and Bluesky, zero for News
        "nps_stage_level": (nps or {}).get("stage_level", 0.0),
        "nps_passive_force": (nps or {}).get("passive_force", 0.0),
        "nps_directional_juice": (nps or {}).get("directional_juice", 0.0),
        "nps_active_force": (nps or {}).get("active_force", 0.0),
        "nps_narrative_power_score": (nps or {}).get("narrative_power_score", 0.0),
        "nps_attention_volume": (nps or {}).get("attention_volume", 0.0),
    }

# ==========================================
# NPS: COMMENT ALIGNMENT + ENGAGEMENT METRICS
# ==========================================

def _compute_nps_for_item(
    *,
    client,
    platform: str,
    raw_comments: list[dict],
    core_narrative: str,
    views: int = 0,
    post_likes: int = 0,
    reposts: int = 0,
    total_comments: int = 0,
) -> dict:
    """
    Orchestrates the full NPS computation for a single post.

    Steps:
      1. If the post has sampled comments, send their texts to the LLM to
         obtain one alignment float per comment (the LLM returns a JSON
         array of floats, nothing else).
      2. Inject the scraper's `likes` alongside each LLM alignment to build
         a List[CommentAnalysis].
      3. Instantiate EngagementMetrics with the combined data — all five
         computed fields (stage_level, passive_force, directional_juice,
         active_force, narrative_power_score) resolve automatically.
      4. Return a flat dict of the five NPS fields, ready to be merged into
         the embedding item record.

    Args:
        client: Initialized Google GenAI client.
        platform: "youtube" or "bluesky".
        raw_comments: List of raw comment dicts from the scraper, each
            containing at least 'text' and 'likes' keys.
        core_narrative: LLM-extracted core narrative of the parent post,
            used as the reference frame for alignment scoring.
        views: YouTube view count (ignored for Bluesky).
        post_likes: Likes on the post itself.
        reposts: Repost / share count.
        total_comments: Macro comment volume (may exceed len(raw_comments)
            since raw_comments is only the sampled top-N).

    Returns:
        Dict with keys: stage_level, passive_force, directional_juice,
        active_force, narrative_power_score.
        Returns zeros for all fields on any error.
    """
    _zero = {
        "stage_level": 0.0,
        "passive_force": 0.0,
        "directional_juice": 0.0,
        "active_force": 0.0,
        "narrative_power_score": 0.0,
    }

    try:
        top_comments: list[CommentAnalysis] = []

        if raw_comments and core_narrative:
            prompt = create_comment_alignment_prompt(raw_comments, core_narrative)
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    config={
                        "system_instruction": system_instruction_comment_alignment,
                        "response_mime_type": "application/json",
                    },
                    contents=prompt,
                )
                import json as _json
                alignments: list[float] = _json.loads(response.text)

                # Zip scraper likes with LLM alignments (guard against length mismatch)
                for raw_c, alignment in zip(raw_comments, alignments):
                    likes = int(raw_c.get("likes", 0))
                    # Clamp alignment to [-1.0, 1.0] in case LLM drifts slightly
                    alignment = max(-1.0, min(1.0, float(alignment)))
                    top_comments.append(CommentAnalysis(likes=likes, alignment=alignment))
            except Exception as e:
                print(f"    [NPS] Erro ao obter alinhamentos dos comentarios: {e}")
                # Fall back to zero alignment so passive_force still computes
                for raw_c in raw_comments:
                    top_comments.append(
                        CommentAnalysis(likes=int(raw_c.get("likes", 0)), alignment=0.0)
                    )

        metrics = EngagementMetrics(
            platform=platform,
            views=views,
            post_likes=post_likes,
            reposts=reposts,
            total_comments=total_comments,
            top_comments=top_comments,
        )

        return {
            "stage_level": metrics.stage_level,
            "passive_force": metrics.passive_force,
            "directional_juice": metrics.directional_juice,
            "active_force": metrics.active_force,
            "narrative_power_score": metrics.narrative_power_score,
            "attention_volume": metrics.attention_volume,
        }

    except Exception as e:
        print(f"    [NPS] Erro inesperado no calculo do NPS: {e}")
        return _zero


# ==========================================
# CORE: ANÁLISE INDIVIDUAL POR ITEM/FONTE
# ==========================================

def run_analysis(data=None, topic=None, embedding_variant="framing"):
    if embedding_variant not in VALID_EMBEDDING_VARIANTS:
        raise ValueError(
            f"embedding_variant invalido: {embedding_variant}. "
            f"Use um de {sorted(VALID_EMBEDDING_VARIANTS)}."
        )

    # 1. Carrega a chave de API
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        print("Aviso: GEMINI_API_KEY não foi encontrada.")

    # 2. Inicializa o client do Google GenAI
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Erro ao inicializar o client do Google GenAI: {e}")
        return None, None, None

    base_dir = Path(__file__).parent

    # 3. Lê arquivo JSON da pasta outputs/scraping/ (caso data não venha do Streamlit)
    if data is None:
        scraping_dir = base_dir / "outputs" / "scraping"
        latest_file = get_latest_scraping_file(scraping_dir)
        if not latest_file:
            print(f"Nenhum arquivo JSON encontrado em {scraping_dir}")
            return None, None, None

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

    # Extrair tópico dos metadados para os prompts individuais
    searched_topic = topic or "Unknown"
    if not topic:
        for meta_key in ["youtube_clipping_metadata", "bluesky_clipping_metadata", "newsapi_clipping_metadata"]:
            for src_key in ["youtube_data", "bluesky_data", "news_data"]:
                if data and src_key in data and data[src_key]:
                    t = data[src_key].get(meta_key, {}).get("searched_topic")
                    if t:
                        searched_topic = t
                        break

    # 4. Garante que as pastas de output existam
    analysis_dir = base_dir / "outputs" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    embeddings_dir = base_dir / "outputs" / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"{filename_stem}_{embedding_variant}"
    output_filename = f"narrative_detection_{run_id}.json"
    output_filepath = analysis_dir / output_filename
    items_output_filepath = analysis_dir / f"items_for_embedding_{run_id}.json"

    consolidated_results = {}
    prompts_enviados = {}

    # Lista para coletar dados para embeddings
    items_for_embedding = []  # cada entrada: {fonte, conteudo_original, dominant_framing}

    # ==========================================
    # 5. ANÁLISE INDIVIDUAL POR ITEM
    # ==========================================

    # 5.1. YouTube – cada vídeo individualmente
    if data and "youtube_data" in data and data["youtube_data"] and data["youtube_data"].get("videos"):
        youtube_results = []
        for i, video in enumerate(data["youtube_data"]["videos"]):
            print(f">> Analisando YouTube vídeo {i+1}/{len(data['youtube_data']['videos'])}: {video.get('title', 'N/A')}")
            try:
                prompt = create_youtube_single_prompt(video, searched_topic)
                if i == 0:
                    prompts_enviados["youtube"] = {"system_instruction": system_instruction_youtube, "user_prompt": prompt}

                result = generate_gemini_json(
                    client=client,
                    user_prompt=prompt,
                    system_instruction=system_instruction_youtube,
                    pydantic_schema=YoutubeAnalysis
                )
                clean = clean_pydantic_output(result)
                youtube_results.append(clean)

                item_id = _build_item_id("youtube", i)
                output = _get_output(clean)
                framing = _get_dominant_framing(clean)
                core_narrative = _get_core_narrative(clean)
                canonical_claim = _get_canonical_claim(clean)
                claim_type = _get_claim_type(clean)
                factual_claim = _get_factual_claim(clean)
                argument_target = _get_argument_target(clean)
                target_type = _get_target_type(clean)
                stance_polarity = _get_stance_polarity(clean)
                relation_direction = _get_relation_direction(clean)
                argument_rationale = _get_argument_rationale(clean)
                embedding_ready_text = _get_embedding_ready_text(clean)
                argument_claim_canonical = _get_argument_claim_canonical(clean)
                argument_claim_raw = _get_argument_claim_raw(clean)
                embedding_ready_text = _normalize_text(
                    embedding_ready_text,
                    _build_embedding_ready_text(
                        canonical_claim=canonical_claim,
                        claim_type=claim_type,
                        argument_target=argument_target,
                        target_type=target_type,
                        stance_polarity=stance_polarity,
                        relation_direction=relation_direction,
                        argument_rationale=argument_rationale,
                        argument_claim_canonical=argument_claim_canonical,
                    ),
                )
                original = _get_original_content(video, "YouTube")
                nps = _compute_nps_for_item(
                    client=client,
                    platform="youtube",
                    raw_comments=video.get("most_liked_comments", []),
                    core_narrative=core_narrative,
                    views=video.get("statistics", {}).get("views", 0),
                    post_likes=video.get("statistics", {}).get("likes", 0),
                    reposts=0,
                    total_comments=video.get("statistics", {}).get("total_comments", 0),
                )
                items_for_embedding.append(_build_embedding_item(
                    item_id=item_id,
                    source="youtube",
                    topic=searched_topic,
                    original=original,
                    output=output,
                    core_narrative=core_narrative,
                    framing=framing,
                    canonical_claim=canonical_claim,
                    claim_type=claim_type,
                    factual_claim=factual_claim,
                    argument_target=argument_target,
                    target_type=target_type,
                    stance_polarity=stance_polarity,
                    relation_direction=relation_direction,
                    argument_rationale=argument_rationale,
                    embedding_ready_text=embedding_ready_text,
                    argument_claim_canonical=argument_claim_canonical,
                    argument_claim_raw=argument_claim_raw,
                    embedding_variant=embedding_variant,
                    nps=nps,
                ))
                print(f"  ✓ Vídeo {i+1} analisado com sucesso.")
            except Exception as e:
                print(f"  ✗ Erro no vídeo {i+1}: {e}")
                youtube_results.append({"error": str(e)})

        consolidated_results["youtube_analysis"] = youtube_results

    # 5.2. Bluesky – cada post individualmente
    if data and "bluesky_data" in data and data["bluesky_data"] and data["bluesky_data"].get("posts"):
        bluesky_results = []
        for i, post in enumerate(data["bluesky_data"]["posts"]):
            print(f">> Analisando Bluesky post {i+1}/{len(data['bluesky_data']['posts'])}: @{post.get('author', 'N/A')}")
            try:
                prompt = create_bluesky_single_prompt(post, searched_topic)
                if i == 0:
                    prompts_enviados["bluesky"] = {"system_instruction": system_instruction_bluesky, "user_prompt": prompt}

                result = generate_gemini_json(
                    client=client,
                    user_prompt=prompt,
                    system_instruction=system_instruction_bluesky,
                    pydantic_schema=BlueskyAnalysis
                )
                clean = clean_pydantic_output(result)
                bluesky_results.append(clean)

                item_id = _build_item_id("bluesky", i)
                output = _get_output(clean)
                framing = _get_dominant_framing(clean)
                core_narrative = _get_core_narrative(clean)
                canonical_claim = _get_canonical_claim(clean)
                claim_type = _get_claim_type(clean)
                factual_claim = _get_factual_claim(clean)
                argument_target = _get_argument_target(clean)
                target_type = _get_target_type(clean)
                stance_polarity = _get_stance_polarity(clean)
                relation_direction = _get_relation_direction(clean)
                argument_rationale = _get_argument_rationale(clean)
                embedding_ready_text = _get_embedding_ready_text(clean)
                argument_claim_canonical = _get_argument_claim_canonical(clean)
                argument_claim_raw = _get_argument_claim_raw(clean)
                embedding_ready_text = _normalize_text(
                    embedding_ready_text,
                    _build_embedding_ready_text(
                        canonical_claim=canonical_claim,
                        claim_type=claim_type,
                        argument_target=argument_target,
                        target_type=target_type,
                        stance_polarity=stance_polarity,
                        relation_direction=relation_direction,
                        argument_rationale=argument_rationale,
                        argument_claim_canonical=argument_claim_canonical,
                    ),
                )
                original = _get_original_content(post, "Bluesky")
                nps = _compute_nps_for_item(
                    client=client,
                    platform="bluesky",
                    raw_comments=post.get("most_liked_comments", []),
                    core_narrative=core_narrative,
                    views=0,
                    post_likes=post.get("likes", 0),
                    reposts=post.get("reposts", 0),
                    total_comments=post.get("reply_count", 0),
                )
                items_for_embedding.append(_build_embedding_item(
                    item_id=item_id,
                    source="bluesky",
                    topic=searched_topic,
                    original=original,
                    output=output,
                    core_narrative=core_narrative,
                    framing=framing,
                    canonical_claim=canonical_claim,
                    claim_type=claim_type,
                    factual_claim=factual_claim,
                    argument_target=argument_target,
                    target_type=target_type,
                    stance_polarity=stance_polarity,
                    relation_direction=relation_direction,
                    argument_rationale=argument_rationale,
                    embedding_ready_text=embedding_ready_text,
                    argument_claim_canonical=argument_claim_canonical,
                    argument_claim_raw=argument_claim_raw,
                    embedding_variant=embedding_variant,
                    nps=nps,
                ))
                print(f"  ✓ Post {i+1} analisado com sucesso.")
            except Exception as e:
                print(f"  ✗ Erro no post {i+1}: {e}")
                bluesky_results.append({"error": str(e)})

        consolidated_results["bluesky_analysis"] = bluesky_results

    # 5.3. News – cada artigo individualmente
    if data and "news_data" in data and data["news_data"] and data["news_data"].get("articles"):
        news_results = []
        for i, article in enumerate(data["news_data"]["articles"]):
            print(f">> Analisando News artigo {i+1}/{len(data['news_data']['articles'])}: {article.get('title', 'N/A')}")
            try:
                prompt = create_news_single_prompt(article, searched_topic)
                if i == 0:
                    prompts_enviados["news"] = {"system_instruction": system_instruction_news, "user_prompt": prompt}

                result = generate_gemini_json(
                    client=client,
                    user_prompt=prompt,
                    system_instruction=system_instruction_news,
                    pydantic_schema=NewsAnalysis
                )
                clean = clean_pydantic_output(result)
                news_results.append(clean)

                item_id = _build_item_id("news", i)
                output = _get_output(clean)
                framing = _get_dominant_framing(clean)
                core_narrative = _get_core_narrative(clean)
                canonical_claim = _get_canonical_claim(clean)
                claim_type = _get_claim_type(clean)
                factual_claim = _get_factual_claim(clean)
                argument_target = _get_argument_target(clean)
                target_type = _get_target_type(clean)
                stance_polarity = _get_stance_polarity(clean)
                relation_direction = _get_relation_direction(clean)
                argument_rationale = _get_argument_rationale(clean)
                embedding_ready_text = _get_embedding_ready_text(clean)
                argument_claim_canonical = _get_argument_claim_canonical(clean)
                argument_claim_raw = _get_argument_claim_raw(clean)
                embedding_ready_text = _normalize_text(
                    embedding_ready_text,
                    _build_embedding_ready_text(
                        canonical_claim=canonical_claim,
                        claim_type=claim_type,
                        argument_target=argument_target,
                        target_type=target_type,
                        stance_polarity=stance_polarity,
                        relation_direction=relation_direction,
                        argument_rationale=argument_rationale,
                        argument_claim_canonical=argument_claim_canonical,
                    ),
                )
                original = _get_original_content(article, "News")
                items_for_embedding.append(_build_embedding_item(
                    item_id=item_id,
                    source="news",
                    topic=searched_topic,
                    original=original,
                    output=output,
                    core_narrative=core_narrative,
                    framing=framing,
                    canonical_claim=canonical_claim,
                    claim_type=claim_type,
                    factual_claim=factual_claim,
                    argument_target=argument_target,
                    target_type=target_type,
                    stance_polarity=stance_polarity,
                    relation_direction=relation_direction,
                    argument_rationale=argument_rationale,
                    embedding_ready_text=embedding_ready_text,
                    argument_claim_canonical=argument_claim_canonical,
                    argument_claim_raw=argument_claim_raw,
                    embedding_variant=embedding_variant,
                ))
                print(f"  ✓ Artigo {i+1} analisado com sucesso.")
            except Exception as e:
                print(f"  ✗ Erro no artigo {i+1}: {e}")
                news_results.append({"error": str(e)})

        consolidated_results["news_analysis"] = news_results

    # 6. Salva análise consolidada (por item)
    print(f"Salvando resultados consolidados em: {output_filepath}")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(consolidated_results, f, ensure_ascii=False, indent=4)

    with open(items_output_filepath, "w", encoding="utf-8") as f:
        json.dump(items_for_embedding, f, ensure_ascii=False, indent=4)

    # ==========================================
    # 7. EMBEDDINGS, CLUSTERIZAÇÃO E t-SNE
    # ==========================================

    embeddings_dataset = None
    fallback_zero_vector_count = 0
    items_for_argument_embedding = [
        item for item in items_for_embedding if item["included_in_argument_embedding"]
    ]
    clustering_metadata_path = embeddings_dir / f"clustering_metadata_{run_id}.json"
    clustering_metadata = {
        "run_id": run_id,
        "topic": searched_topic,
        "embedding_variant": embedding_variant,
        "primary_argument_embedding_variant": PRIMARY_ARGUMENT_EMBEDDING_VARIANT,
        "auxiliary_argument_audit_variant": AUXILIARY_ARGUMENT_AUDIT_VARIANT,
        "factual_routing_rule": "include_only_when_claim_type_is_argumentative_or_mixed_and_target_stance_rationale_are_present",
        "embedding_model": EMBEDDING_MODEL,
        "clustering_algorithm": "kmeans",
        "n_clusters": 3,
        "item_count": len(items_for_embedding),
        "included_in_argument_embedding_count": len(items_for_argument_embedding),
        "excluded_from_argument_embedding_count": len(items_for_embedding) - len(items_for_argument_embedding),
        "excluded_factual_count": sum(
            1 for item in items_for_embedding if item["argument_embedding_exclusion_reason"] == "claim_type_factual"
        ),
        "excluded_descriptive_count": sum(
            1 for item in items_for_embedding if item["argument_embedding_exclusion_reason"] == "claim_type_descriptive"
        ),
        "excluded_missing_target_count": sum(
            1 for item in items_for_embedding if item["argument_embedding_exclusion_reason"] == "missing_argument_target"
        ),
        "excluded_missing_stance_count": sum(
            1 for item in items_for_embedding if item["argument_embedding_exclusion_reason"] in {"missing_stance_polarity", "stance_not_interpretive_enough"}
        ),
        "excluded_missing_rationale_count": sum(
            1 for item in items_for_embedding if item["argument_embedding_exclusion_reason"] == "missing_argument_rationale"
        ),
        "fallback_zero_vector_count": 0,
        "claim_missing_count": sum(1 for item in items_for_embedding if item["claim_missing"]),
        "claim_fallback_used_count": sum(1 for item in items_for_embedding if item["claim_fallback_used"]),
        "items_artifact_path": str(items_output_filepath),
    }

    if items_for_argument_embedding:
        print(f"\n>> Gerando embeddings para {len(items_for_argument_embedding)} itens...")

        # 7.1. Gerar embeddings do campo selecionado
        texts_to_embed = [item["text_used_for_embedding"] for item in items_for_argument_embedding]
        item_embeddings = []

        for i, text_to_embed in enumerate(texts_to_embed):
            try:
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text_to_embed
                )
                emb = np.array(result.embeddings[0].values)
                item_embeddings.append(emb)
            except Exception as e:
                print(f"  ✗ Erro ao gerar embedding do item {i+1}: {e}")
                # Fallback: vetor de zeros
                item_embeddings.append(np.zeros(768))
                fallback_zero_vector_count += 1

        # 7.2. Gerar embeddings das 3 âncoras semânticas
        anchors_text = [
            "Favorável à legalização do aborto",
            "Contrário a legalização do aborto",
            "Neutro a legalização do aborto"
        ]
        anchor_embeddings = []
        for anchor in anchors_text:
            try:
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=anchor
                )
                anchor_embeddings.append(np.array(result.embeddings[0].values))
            except Exception as e:
                print(f"  ✗ Erro ao gerar embedding da âncora '{anchor}': {e}")
                anchor_embeddings.append(np.zeros(768))

        # 7.3. K-Means nos embeddings dos itens (k=3)
        # print(">> Aplicando K-Means (k=3) nos embeddings dos itens...") # LOG MUDO P/ NÃO CONFUNDIR O DEV
        all_item_embs = np.array(item_embeddings)

        if len(all_item_embs) >= 3:
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(all_item_embs)
        else:
            # Se menos de 3 itens, atribuí-los ao cluster 0
            clusters = np.zeros(len(all_item_embs), dtype=int)

        # 7.4. t-SNE — todos juntos (itens + âncoras)
        # print(">> Aplicando t-SNE (2D) para redução de dimensionalidade...") # LOG MUDO P/ NÃO CONFUNDIR O DEV
        all_embeddings = np.vstack([all_item_embs] + [e.reshape(1, -1) for e in anchor_embeddings])

        # Ajustar perplexity se houver poucos pontos
        n_samples = len(all_embeddings)
        perplexity = min(15, max(2, n_samples - 1))

        tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, init='pca')
        reduced_tsne = tsne.fit_transform(all_embeddings)

        # Separar coordenadas
        item_tsne = reduced_tsne[:len(items_for_argument_embedding)]
        anchor_tsne = reduced_tsne[len(items_for_argument_embedding):]

        # 7.5. Montar dataset final
        records = []
        for i, item in enumerate(items_for_argument_embedding):
            records.append({
                "item_id": item["item_id"],
                "source": item["source"],
                "topic": item["topic"],
                "conteudo_original": item["conteudo_original"],
                "core_narrative": item["core_narrative"],
                "dominant_framing": item["dominant_framing"],
                "journalistic_framing": item["journalistic_framing"],
                "claim_type": item["claim_type"],
                "factual_claim": item["factual_claim"],
                "argument_target": item["argument_target"],
                "target_type": item["target_type"],
                "stance_polarity": item["stance_polarity"],
                "relation_direction": item["relation_direction"],
                "argument_rationale": item["argument_rationale"],
                "embedding_ready_text": item["embedding_ready_text"],
                "argument_claim_canonical": item["argument_claim_canonical"],
                "argument_claim_raw": item["argument_claim_raw"],
                "canonical_claim": item["canonical_claim"],
                "text_used_for_embedding": item["text_used_for_embedding"],
                "embedding_text_source": item["embedding_text_source"],
                "embedding_variant": item["embedding_variant"],
                "claim_missing": item["claim_missing"],
                "claim_fallback_used": item["claim_fallback_used"],
                "missing_selected_text": item["missing_selected_text"],
                "included_in_argument_embedding": item["included_in_argument_embedding"],
                "argument_embedding_exclusion_reason": item["argument_embedding_exclusion_reason"],
                "cluster": int(clusters[i]),
                "tsne_x": float(item_tsne[i, 0]),
                "tsne_y": float(item_tsne[i, 1]),
                "is_anchor": False
            })

        for i, anchor in enumerate(anchors_text):
            records.append({
                "item_id": f"anchor_{i + 1}",
                "source": "anchor",
                "topic": searched_topic,
                "conteudo_original": anchor,
                "core_narrative": None,
                "dominant_framing": anchor,
                "journalistic_framing": None,
                "claim_type": None,
                "factual_claim": None,
                "argument_target": None,
                "target_type": None,
                "stance_polarity": None,
                "relation_direction": None,
                "argument_rationale": None,
                "embedding_ready_text": None,
                "argument_claim_canonical": None,
                "argument_claim_raw": None,
                "canonical_claim": None,
                "text_used_for_embedding": anchor,
                "embedding_text_source": "anchor",
                "embedding_variant": embedding_variant,
                "claim_missing": False,
                "claim_fallback_used": False,
                "missing_selected_text": False,
                "included_in_argument_embedding": False,
                "argument_embedding_exclusion_reason": None,
                "cluster": -1,
                "tsne_x": float(anchor_tsne[i, 0]),
                "tsne_y": float(anchor_tsne[i, 1]),
                "is_anchor": True
            })

        embeddings_dataset = pd.DataFrame(records)

        # 7.6. Salvar em parquet e JSON
        parquet_path = embeddings_dir / f"embeddings_{run_id}.parquet"
        json_emb_path = embeddings_dir / f"embeddings_{run_id}.json"

        embeddings_dataset.to_parquet(parquet_path, index=False)
        embeddings_dataset.to_json(json_emb_path, orient="records", force_ascii=False, indent=4)
        clustering_metadata.update({
            "fallback_zero_vector_count": fallback_zero_vector_count,
            "embeddings_parquet_path": str(parquet_path),
            "embeddings_json_path": str(json_emb_path),
        })
        with open(clustering_metadata_path, "w", encoding="utf-8") as f:
            json.dump(clustering_metadata, f, ensure_ascii=False, indent=4)

        print(f"✓ Dataset de embeddings salvo em: {parquet_path}")
        print(f"✓ Dataset de embeddings salvo em: {json_emb_path}")
        print(f"✓ Metadados de clustering salvos em: {clustering_metadata_path}")
    else:
        print("\n>> Nenhum item elegivel para embedding argumentativo nesta rodada.")
        with open(clustering_metadata_path, "w", encoding="utf-8") as f:
            json.dump(clustering_metadata, f, ensure_ascii=False, indent=4)

    print("Processo finalizado!")
    return consolidated_results, prompts_enviados, clustering_metadata


TOPICS_TO_ANALYZE = [
    "Fundo Eleitoral",
    "Reforma da Previdência",
    "Transição Energética",
    "Atuação do STF",
    "Guerra no Irã",
    "Segurança Pública",
]

if __name__ == "__main__":
    import time, random, sys

    scraping_dir = Path("outputs") / "scraping"
    
    # PARAMETRO NOVO: Defina o nome do arquivo exato para rodar apenas ele.
    # Exemplo: SPECIFIC_FILE_TO_ANALYZE = "atuação_do_stf_2026-04-08_15-09.json"
    # Se deixar como None, o script roda o fluxo normal para todos os tópicos.
    SPECIFIC_FILE_TO_ANALYZE = "atuação_do_stf_2026-04-08_15-09.json"

    if SPECIFIC_FILE_TO_ANALYZE:
        print(f"[LLM Analysis] Analisando apenas o arquivo especifico: {SPECIFIC_FILE_TO_ANALYZE}")
        target_file = scraping_dir / SPECIFIC_FILE_TO_ANALYZE
        if not target_file.exists():
            print(f"Erro: Arquivo nao encontrado -> {target_file}")
            sys.exit(1)
        else:
            with open(target_file, "r", encoding="utf-8") as f:
                import json
                data = json.load(f)
            topic_guess = " ".join(SPECIFIC_FILE_TO_ANALYZE.split("_202")[0].split("_")).title()
            print(f"-> Assumindo topico: '{topic_guess}'")
            run_analysis(data=data, topic=topic_guess, embedding_variant="argument_claim_canonical")
            print("Analise especifica concluida!")
            sys.exit(0)

    print(f"[LLM Analysis] Iniciando analise para {len(TOPICS_TO_ANALYZE)} temas...\n")

    for idx, topic in enumerate(TOPICS_TO_ANALYZE):
        slug = topic.replace(" ", "_").lower()
        matching_files = sorted(
            scraping_dir.glob(f"{slug}_*.json"),
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not matching_files:
            print(f"[{idx+1}/{len(TOPICS_TO_ANALYZE)}] Nenhum arquivo para topic='{topic}'. Pulando.")
            continue
        latest_file = matching_files[0]
        print(f"[{idx+1}/{len(TOPICS_TO_ANALYZE)}] Analisando '{topic}' -> {latest_file.name}")
        with open(latest_file, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
        run_analysis(data=data, topic=topic, embedding_variant="argument_claim_canonical")
        print(f"Tema '{topic}' concluido.\n")
        if idx < len(TOPICS_TO_ANALYZE) - 1:
            cooldown = random.uniform(10, 20)
            print(f"[LLM] Pausando {cooldown:.1f}s...")
            time.sleep(cooldown)

    print("Pipeline de analise LLM completo!")
