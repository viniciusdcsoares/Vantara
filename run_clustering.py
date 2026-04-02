"""
run_clustering.py — Argument Clustering Stage
================================================
Reads the embeddings parquet produced by run_llm_analysis.py and performs
clustering on canonical_claim representations (2D t-SNE projection).

Usage examples:
    python run_clustering.py
    python run_clustering.py --topic "Fundo Eleitoral"
    python run_clustering.py --embeddings-file outputs/embeddings/embeddings_fundo_eleitoral_....parquet
    python run_clustering.py --algorithm kmeans --min-cluster-size 3
    python run_clustering.py --include-descriptive

Author: Vantara pipeline — MVP script-first, no FastAPI/DB/Redis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

# ── Centralised logger (same module used by scrapers) ────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger_configs import setup_logger

logger = setup_logger("clustering")

# ── Repository root (always resolved relative to this file) ──────────────────
REPO_ROOT = Path(__file__).resolve().parent
ANALYSIS_DIR  = REPO_ROOT / "outputs" / "analysis"
EMBEDDINGS_DIR = REPO_ROOT / "outputs" / "embeddings"
CLUSTERS_DIR   = REPO_ROOT / "outputs" / "clusters"


# =============================================================================
# CLI
# =============================================================================

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Cluster canonical claims from embeddings parquet."
    )
    p.add_argument("--analysis-file",    type=Path, default=None,
                   help="Path to items_for_embedding_*.json file (optional)")
    p.add_argument("--embeddings-file",  type=Path, default=None,
                   help="Path to embeddings_*.parquet (or .json) file (optional)")
    p.add_argument("--topic", type=str, default=None,
                   help="Topic label (used if cannot be inferred from filename)")
    p.add_argument("--algorithm", choices=["auto", "hdbscan", "kmeans"],
                   default="auto",
                   help="Clustering algorithm (default: auto → HDBSCAN then KMeans fallback)")
    p.add_argument("--output-dir", type=Path, default=CLUSTERS_DIR,
                   help="Base output directory (default: outputs/clusters)")
    p.add_argument("--min-cluster-size", type=int, default=None,
                   help="Minimum cluster size (HDBSCAN). Auto-computed if omitted.")
    p.add_argument("--include-descriptive", action="store_true",
                   help="Include items with claim_type='descriptive' in clustering.")
    return p


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def _glob_recursive(directory: Path, pattern: str) -> list[Path]:
    """Glob a directory recursively, returning sorted list."""
    return sorted(directory.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


def discover_files(
    analysis_file: Optional[Path],
    embeddings_file: Optional[Path],
    topic: Optional[str],
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Resolve the best (analysis_file, embeddings_file) pair to use.
    Rules (in priority order):
      1. Both provided by CLI — use as-is.
      2. Only embeddings provided — find matching analysis by run_id.
      3. Only analysis provided — find matching embeddings by run_id.
      4. Neither provided + topic given — find most recent pair matching topic slug.
      5. Neither provided — use the globally most recent pair.
    """
    logger.info("Discovering input files...")

    # Case 1: both explicit
    if analysis_file and embeddings_file:
        logger.info(f"Using explicit paths: analysis={analysis_file.name}, embeddings={embeddings_file.name}")
        return analysis_file, embeddings_file

    # Helper: extract run_id from filename stems like
    #   embeddings_<slug>_<timestamp>_<variant>  →  <slug>_<timestamp>_<variant>
    def run_id_from_stem(stem: str, prefix: str) -> str:
        return stem[len(prefix):].lstrip("_")

    # Discover all candidate files
    all_emb = (
        _glob_recursive(EMBEDDINGS_DIR, "embeddings_*.parquet") +
        _glob_recursive(EMBEDDINGS_DIR, "embeddings_*.json")
    )
    all_ana = _glob_recursive(ANALYSIS_DIR, "items_for_embedding_*.json")

    if not all_emb:
        logger.error(f"No embeddings files found under {EMBEDDINGS_DIR}")
        return None, None

    def filter_by_topic(files: list[Path], slug: str) -> list[Path]:
        return [f for f in files if slug in f.stem]

    # Case 2 or 3: one side is explicit
    if embeddings_file and not analysis_file:
        run_id = run_id_from_stem(embeddings_file.stem, "embeddings")
        matches = [f for f in all_ana if run_id in f.stem]
        analysis_file = matches[0] if matches else None
        logger.info(f"Resolved analysis file: {analysis_file}")
        return analysis_file, embeddings_file

    if analysis_file and not embeddings_file:
        run_id = run_id_from_stem(analysis_file.stem, "items_for_embedding")
        pq_matches = [f for f in all_emb if run_id in f.stem and f.suffix == ".parquet"]
        embeddings_file = pq_matches[0] if pq_matches else None
        logger.info(f"Resolved embeddings file: {embeddings_file}")
        return analysis_file, embeddings_file

    # Case 4 + 5: nothing explicit
    if topic:
        slug = topic.replace(" ", "_").lower()
        all_emb = filter_by_topic(all_emb, slug) or all_emb
        all_ana = filter_by_topic(all_ana, slug) or all_ana
        logger.info(f"Filtered by topic slug '{slug}'")

    # Pick most recent parquet
    pq_files = [f for f in all_emb if f.suffix == ".parquet"] or all_emb
    best_emb = pq_files[0] if pq_files else None

    # Try to match analysis by run_id
    best_ana = None
    if best_emb:
        run_id = run_id_from_stem(best_emb.stem, "embeddings")
        matches = [f for f in all_ana if run_id in f.stem]
        best_ana = matches[0] if matches else (all_ana[0] if all_ana else None)

    logger.info(f"Auto-selected embeddings: {best_emb}")
    logger.info(f"Auto-selected analysis:   {best_ana}")
    return best_ana, best_emb


# =============================================================================
# DATA LOADING & NORMALISATION
# =============================================================================

def load_embeddings(emb_file: Path) -> pd.DataFrame:
    """
    Load the embeddings parquet/json produced by run_llm_analysis.py.
    Expected columns (subset used here):
        item_id, source, topic, argument_claim_canonical, canonical_claim,
        text_used_for_embedding, claim_type, dominant_framing,
        journalistic_framing, conteudo_original, tsne_x, tsne_y, is_anchor,
        included_in_argument_embedding, argument_embedding_exclusion_reason
    """
    logger.info(f"Loading embeddings from {emb_file.name}")
    if emb_file.suffix == ".parquet":
        df = pd.read_parquet(emb_file)
    else:
        df = pd.read_json(emb_file, orient="records")

    logger.info(f"Loaded {len(df)} rows, columns: {df.columns.tolist()}")
    return df


def load_analysis_items(ana_file: Optional[Path]) -> pd.DataFrame:
    """
    Load items_for_embedding_*.json if available.
    Returns empty DataFrame if file not found — the embeddings parquet alone
    has enough metadata for the clustering pipeline.
    """
    if not ana_file or not ana_file.exists():
        logger.warning("No analysis items file found; proceeding with embeddings parquet only.")
        return pd.DataFrame()

    logger.info(f"Loading analysis items from {ana_file.name}")
    data = json.loads(ana_file.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} analysis items")
    return df


def infer_topic_slug(emb_file: Path, cli_topic: Optional[str]) -> str:
    """Derive a URL-safe topic slug from the filename or CLI argument."""
    if cli_topic:
        return cli_topic.replace(" ", "_").lower()
    # Stem: embeddings_<slug>_<date>_<time>_<variant>
    # Strip known prefix and suffix portions
    stem = emb_file.stem  # e.g. "embeddings_fundo_eleitoral_2026-04-01_18-21_argument_claim_canonical"
    parts = stem[len("embeddings_"):] if stem.startswith("embeddings_") else stem
    # Remove trailing variant (argument_claim_canonical, framing, …)
    for suffix in ["_argument_claim_canonical", "_argument_claim_raw", "_framing", "_core_narrative", "_canonical_claim"]:
        if parts.endswith(suffix):
            parts = parts[: -len(suffix)]
            break
    # Remove trailing timestamp  _YYYY-MM-DD_HH-MM
    import re
    parts = re.sub(r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$", "", parts)
    return parts or "global"


def build_canonical_df(
    emb_df: pd.DataFrame,
    ana_df: pd.DataFrame,
    topic_slug: str,
    include_descriptive: bool,
) -> pd.DataFrame:
    """
    Merge, filter and normalise into a canonical dataframe for clustering.

    Key invariants:
        • Anchors are removed.
        • Rows without a usable canonical_claim are discarded (WARNING logged).
        • 2D coordinates (tsne_x, tsne_y) are kept as the embedding proxy.
        • claim_type filtering is applied.
    """
    logger.info("Building canonical dataframe...")

    # ── 1. Drop anchors ───────────────────────────────────────────────────────
    if "is_anchor" in emb_df.columns:
        n_anchors = emb_df["is_anchor"].sum()
        emb_df = emb_df[~emb_df["is_anchor"]].copy()
        logger.debug(f"Removed {n_anchors} anchor rows")

    # ── 2. Resolve canonical_claim text ──────────────────────────────────────
    # The parquet stores it under "argument_claim_canonical" or "canonical_claim"
    # or as "text_used_for_embedding"
    for col_candidate in ["argument_claim_canonical", "canonical_claim", "text_used_for_embedding"]:
        if col_candidate in emb_df.columns:
            emb_df["_canonical_claim"] = emb_df[col_candidate].fillna("")
            break
    else:
        emb_df["_canonical_claim"] = ""

    # ── 3. Merge with analysis items (best-effort, non-blocking) ─────────────
    if not ana_df.empty and "item_id" in emb_df.columns and "item_id" in ana_df.columns:
        # Limit to columns not already in emb_df to avoid conflicts
        extra_cols = [c for c in ana_df.columns if c not in emb_df.columns and c != "item_id"]
        df = emb_df.merge(ana_df[["item_id"] + extra_cols], on="item_id", how="left")
        logger.debug(f"Merged analysis items; added cols: {extra_cols}")
    else:
        df = emb_df.copy()

    # ── 4. Normalise columns ──────────────────────────────────────────────────
    def _get(col, default=""):
        return df[col] if col in df.columns else default

    df["item_id"]        = _get("item_id", pd.Series(range(len(df))).astype(str))
    df["canonical_claim"] = df["_canonical_claim"]
    df["claim_type"]     = _get("claim_type", "unknown")
    df["source_type"]    = _get("source", "unknown")
    df["topic_slug"]     = topic_slug
    df["source_file"]    = str(emb_df.index.name or "")  # patched below
    df["title"]          = _get("conteudo_original", "")
    df["author"]         = ""
    df["url"]            = ""
    df["published_at"]   = ""

    df.drop(columns=["_canonical_claim"], inplace=True, errors="ignore")

    # ── 5. Filter claim_type ──────────────────────────────────────────────────
    allowed_types = {"argumentative", "factual"}
    if include_descriptive:
        allowed_types.add("descriptive")

    n_before = len(df)
    mask_type = df["claim_type"].str.lower().isin(allowed_types) | df["claim_type"].isin(["unknown", ""])
    discarded_type = df[~mask_type]
    if len(discarded_type):
        for _, row in discarded_type.iterrows():
            logger.warning(f"DISCARD | claim_type='{row['claim_type']}' not in allowed set | item_id={row['item_id']}")
    df = df[mask_type].copy()

    # ── 6. Drop rows with empty canonical_claim ───────────────────────────────
    mask_empty = df["canonical_claim"].str.strip() == ""
    discarded_empty = df[mask_empty]
    for _, row in discarded_empty.iterrows():
        logger.warning(f"DISCARD | empty canonical_claim | item_id={row['item_id']}")
    df = df[~mask_empty].copy()

    # ── 7. Check 2D coordinates ───────────────────────────────────────────────
    has_tsne = "tsne_x" in df.columns and "tsne_y" in df.columns
    if has_tsne:
        mask_nan = df["tsne_x"].isna() | df["tsne_y"].isna()
        if mask_nan.any():
            logger.warning(f"DISCARD | {mask_nan.sum()} rows with NaN tsne coordinates")
            df = df[~mask_nan].copy()

    # ── 8. Deduplicate by canonical_claim hash ────────────────────────────────
    df["_claim_hash"] = df["canonical_claim"].apply(
        lambda x: hashlib.md5(x.strip().lower().encode()).hexdigest()
    )
    n_dupes = df.duplicated(subset=["_claim_hash"]).sum()
    if n_dupes:
        logger.warning(f"Deduplicating {n_dupes} exact-match canonical_claims")
    df = df.drop_duplicates(subset=["_claim_hash"]).copy()
    df.drop(columns=["_claim_hash"], inplace=True, errors="ignore")
    df = df.reset_index(drop=True)

    discarded_total = n_before - len(df)
    logger.info(f"Canonical DF ready | {len(df)} valid items | {discarded_total} discarded from {n_before}")
    return df


# =============================================================================
# CLUSTERING ALGORITHMS
# =============================================================================

def _embedding_matrix(df: pd.DataFrame) -> np.ndarray:
    """Return the 2D t-SNE coordinates as the clustering feature matrix."""
    X = df[["tsne_x", "tsne_y"]].to_numpy(dtype=float)
    return X


def _dynamic_min_cluster_size(n: int, cli_value: Optional[int]) -> int:
    if cli_value:
        return cli_value
    return max(2, int(round(n ** 0.5)))


def cluster_hdbscan(X: np.ndarray, min_cluster_size: int) -> tuple[np.ndarray, bool]:
    """
    Run HDBSCAN. Returns (labels, success).
    Labels contain -1 for noise points.
    """
    try:
        import hdbscan
    except ImportError:
        logger.warning("hdbscan package not installed — will fall back to KMeans.")
        return np.array([]), False

    n = len(X)
    mcs = min(min_cluster_size, n - 1)
    mcs = max(2, mcs)
    min_samples = max(1, mcs // 2)

    logger.info(f"HDBSCAN | n={n} | min_cluster_size={mcs} | min_samples={min_samples}")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        min_samples=min_samples,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(X)

    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    noise_ratio = n_noise / max(n, 1)

    logger.info(f"HDBSCAN result | clusters={n_clusters} | noise={n_noise} ({noise_ratio:.1%})")

    # Degenerate result: 0 clusters or >60% noise → fallback
    if n_clusters == 0 or noise_ratio > 0.6:
        logger.warning(f"HDBSCAN degenerate (clusters={n_clusters}, noise={noise_ratio:.1%}) → falling back to KMeans")
        return labels, False

    return labels, True


def cluster_kmeans(X: np.ndarray) -> tuple[np.ndarray, int, float]:
    """
    Run KMeans with automatic k selection via silhouette score.
    Returns (labels, best_k, best_silhouette).
    """
    n = len(X)
    k_max = min(10, n - 1)
    k_min = 2

    if n < 2:
        return np.zeros(n, dtype=int), 1, 0.0

    if n == 2:
        return np.array([0, 1]), 2, 0.0

    best_k, best_score, best_labels = k_min, -1.0, None
    k_range = range(k_min, k_max + 1)

    logger.info(f"KMeans | evaluating k in [{k_min}, {k_max}]")
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        try:
            score = silhouette_score(X, labels)
        except Exception:
            score = -1.0
        logger.debug(f"  k={k} | silhouette={score:.4f}")
        if score > best_score:
            best_score, best_k, best_labels = score, k, labels

    if best_labels is None:
        best_labels = np.zeros(n, dtype=int)
        best_k = 1

    logger.info(f"KMeans selected k={best_k} | silhouette={best_score:.4f}")
    return best_labels, best_k, best_score


def run_clustering(
    df: pd.DataFrame,
    algorithm: str,
    min_cluster_size: Optional[int],
) -> tuple[np.ndarray, str, dict]:
    """
    Dispatch to the chosen algorithm.
    Returns (labels, algo_used, algo_params).
    Labels: -1 = noise (HDBSCAN), ≥0 = cluster_id.
    """
    n = len(df)
    X = _embedding_matrix(df)
    algo_params: dict = {}

    logger.info(f"Starting clustering | n={n} | algorithm='{algorithm}'")

    # ── Edge cases ──────────────────────────────────────────────────────────
    if n == 0:
        return np.array([], dtype=int), algorithm, {}
    if n == 1:
        return np.array([0]), "single", {"note": "only 1 item"}
    if n == 2:
        # Cosine similarity on 2-vector set
        sim = float(np.dot(X[0], X[1]) / (np.linalg.norm(X[0]) * np.linalg.norm(X[1]) + 1e-9))
        labels = np.array([0, 0]) if sim > 0.85 else np.array([0, 1])
        return labels, "similarity_pair", {"cosine_sim": round(sim, 4)}

    mcs = _dynamic_min_cluster_size(n, min_cluster_size)

    if algorithm == "hdbscan":
        labels, ok = cluster_hdbscan(X, mcs)
        if not ok:
            labels, k, sil = cluster_kmeans(X)
            algo_params = {"k": int(k), "silhouette": round(sil, 4), "reason": "hdbscan_fallback"}
            return labels, "kmeans_fallback", algo_params
        algo_params = {"min_cluster_size": mcs}
        return labels, "hdbscan", algo_params

    if algorithm == "kmeans":
        labels, k, sil = cluster_kmeans(X)
        algo_params = {"k": int(k), "silhouette": round(sil, 4)}
        return labels, "kmeans", algo_params

    # algorithm == "auto": try HDBSCAN, fallback to KMeans
    labels, ok = cluster_hdbscan(X, mcs)
    if ok:
        algo_params = {"min_cluster_size": mcs}
        return labels, "hdbscan", algo_params
    labels, k, sil = cluster_kmeans(X)
    algo_params = {"k": int(k), "silhouette": round(sil, 4), "reason": "auto_fallback"}
    return labels, "kmeans", algo_params


# =============================================================================
# CLUSTER ANALYSIS
# =============================================================================

def analyse_clusters(
    df: pd.DataFrame,
    labels: np.ndarray,
    algo: str,
    emb_file: Path,
    ana_file: Optional[Path],
    topic_slug: str,
) -> tuple[list[dict], list[dict]]:
    """
    Build cluster_centers and cluster_diagnostics structures.
    Returns (centers, diagnostics_per_cluster).
    """
    X = _embedding_matrix(df)
    unique_clusters = sorted(set(labels) - {-1})

    centers = []
    diagnostics = []

    for cid in unique_clusters:
        mask = labels == cid
        cluster_df = df[mask]
        cluster_X = X[mask]

        # Representative item: closest to centroid (or medoid for HDBSCAN)
        centroid = cluster_X.mean(axis=0)
        dists = np.linalg.norm(cluster_X - centroid, axis=1)
        rep_idx = int(np.argmin(dists))
        rep_row = cluster_df.iloc[rep_idx]

        center_type = "medoid" if "hdbscan" in algo else "centroid"
        centers.append({
            "cluster_id": int(cid),
            "center_type": center_type,
            "representative_item_id": str(rep_row.get("item_id", "")),
            "representative_claim": str(rep_row.get("canonical_claim", ""))[:300],
            "centroid_tsne_x": float(centroid[0]),
            "centroid_tsne_y": float(centroid[1]),
            "cluster_size": int(mask.sum()),
        })

        src_counts = cluster_df["source_type"].value_counts().to_dict()
        ct_counts  = cluster_df["claim_type"].value_counts().to_dict()
        diagnostics.append({
            "cluster_id": int(cid),
            "cluster_size": int(mask.sum()),
            "source_breakdown": {str(k): int(v) for k, v in src_counts.items()},
            "claim_type_breakdown": {str(k): int(v) for k, v in ct_counts.items()},
        })

    return centers, diagnostics


# =============================================================================
# OUTPUT WRITERS
# =============================================================================

def _run_id(emb_file: Path) -> str:
    """Derive run_id from embeddings filename (strips 'embeddings_' prefix)."""
    stem = emb_file.stem
    return stem[len("embeddings_"):] if stem.startswith("embeddings_") else stem


def make_output_dir(base_dir: Path, topic_slug: str) -> Path:
    out = base_dir / topic_slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_manifest(
    out_dir: Path, run_id: str, *,
    topic_slug: str, algorithm: str, algo_params: dict,
    emb_file: Path, ana_file: Optional[Path],
    n_total: int, n_valid: int, n_clusters: int, n_noise: int,
    silhouette: Optional[float], status: str,
    generated_at: str,
) -> Path:
    manifest = {
        "run_id": run_id,
        "generated_at": generated_at,
        "topic_slug": topic_slug,
        "status": status,
        "algorithm_selected": algorithm,
        "algorithm_params": algo_params,
        "input_files": {
            "embeddings": str(emb_file),
            "analysis": str(ana_file) if ana_file else None,
        },
        "counts": {
            "total_items_loaded": n_total,
            "valid_items_clustered": n_valid,
            "n_clusters": n_clusters,
            "n_noise_points": n_noise,
        },
        "silhouette_score": round(silhouette, 4) if silhouette is not None else None,
    }
    path = out_dir / f"cluster_manifest_{run_id}.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Manifest written → {path}")
    return path


def write_members_csv(
    out_dir: Path, run_id: str,
    df: pd.DataFrame, labels: np.ndarray,
    emb_file: Path,
) -> Path:
    X = _embedding_matrix(df)
    path = out_dir / f"cluster_members_{run_id}.csv"

    with path.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = [
            "item_id", "cluster_id", "is_noise",
            "canonical_claim", "claim_type", "source_type",
            "topic_slug", "source_file",
            "title", "author", "url", "published_at",
            "distance_to_center",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        # Pre-compute centroids per cluster for distance calculation
        unique_clusters = sorted(set(labels) - {-1})
        centroids: dict[int, np.ndarray] = {}
        for cid in unique_clusters:
            mask = labels == cid
            centroids[cid] = X[mask].mean(axis=0)

        for i, (_, row) in enumerate(df.iterrows()):
            cid = int(labels[i])
            is_noise = cid == -1
            if is_noise:
                dist = None
            else:
                dist = float(np.linalg.norm(X[i] - centroids[cid]))

            writer.writerow({
                "item_id": str(row.get("item_id", i)),
                "cluster_id": cid,
                "is_noise": is_noise,
                "canonical_claim": str(row.get("canonical_claim", ""))[:400],
                "claim_type": str(row.get("claim_type", "")),
                "source_type": str(row.get("source_type", "")),
                "topic_slug": str(row.get("topic_slug", "")),
                "source_file": emb_file.name,
                "title": str(row.get("title", ""))[:200],
                "author": str(row.get("author", "")),
                "url": str(row.get("url", "")),
                "published_at": str(row.get("published_at", "")),
                "distance_to_center": round(dist, 6) if dist is not None else "",
            })

    logger.info(f"Members CSV written → {path}")
    return path


def write_centers(out_dir: Path, run_id: str, centers: list[dict]) -> Path:
    path = out_dir / f"cluster_centers_{run_id}.json"
    path.write_text(json.dumps(centers, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Centers written → {path}")
    return path


def write_diagnostics(
    out_dir: Path, run_id: str,
    cluster_diags: list[dict],
    discarded_items: list[dict],
) -> Path:
    size_dist = {str(d["cluster_id"]): d["cluster_size"] for d in cluster_diags}
    payload = {
        "cluster_size_distribution": size_dist,
        "per_cluster": cluster_diags,
        "discarded_items": discarded_items,
    }
    path = out_dir / f"cluster_diagnostics_{run_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Diagnostics written → {path}")
    return path


def write_projection_csv(
    out_dir: Path, run_id: str,
    df: pd.DataFrame, labels: np.ndarray,
) -> Path:
    path = out_dir / f"cluster_projection_{run_id}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "item_id", "tsne_x", "tsne_y", "cluster_id", "source_type",
            "claim_type", "canonical_claim_preview",
        ])
        writer.writeheader()
        for i, (_, row) in enumerate(df.iterrows()):
            writer.writerow({
                "item_id": str(row.get("item_id", i)),
                "tsne_x": float(row.get("tsne_x", 0)),
                "tsne_y": float(row.get("tsne_y", 0)),
                "cluster_id": int(labels[i]),
                "source_type": str(row.get("source_type", "")),
                "claim_type": str(row.get("claim_type", "")),
                "canonical_claim_preview": str(row.get("canonical_claim", ""))[:120],
            })
    logger.info(f"Projection CSV written → {path}")
    return path


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    logger.info("=" * 60)
    logger.info(f"run_clustering.py started at {generated_at}")

    # ── 1. Discover files ─────────────────────────────────────────────────────
    try:
        ana_file, emb_file = discover_files(args.analysis_file, args.embeddings_file, args.topic)
    except Exception:
        logger.error(f"File discovery failed:\n{traceback.format_exc()}")
        sys.exit(1)

    if emb_file is None or not emb_file.exists():
        logger.error("No valid embeddings file found. Aborting.")
        sys.exit(1)

    # ── 2. Derive topic slug ──────────────────────────────────────────────────
    topic_slug = infer_topic_slug(emb_file, args.topic)
    logger.info(f"Topic slug: '{topic_slug}'")

    # ── 3. Load data ──────────────────────────────────────────────────────────
    try:
        emb_df = load_embeddings(emb_file)
    except Exception:
        logger.error(f"Failed to load embeddings:\n{traceback.format_exc()}")
        sys.exit(1)

    n_total = len(emb_df)

    try:
        ana_df = load_analysis_items(ana_file)
    except Exception:
        logger.error(f"Failed to load analysis items (non-fatal, continuing):\n{traceback.format_exc()}")
        ana_df = pd.DataFrame()

    # ── 4. Build canonical dataframe ─────────────────────────────────────────
    try:
        df = build_canonical_df(emb_df, ana_df, topic_slug, args.include_descriptive)
    except Exception:
        logger.error(f"Failed to build canonical dataframe:\n{traceback.format_exc()}")
        sys.exit(1)

    n_valid = len(df)
    run_id = _run_id(emb_file)
    out_dir = make_output_dir(args.output_dir, topic_slug)

    if n_valid == 0:
        logger.error("No valid items remain after filtering. Aborting.")
        write_manifest(
            out_dir, run_id,
            topic_slug=topic_slug, algorithm=args.algorithm, algo_params={},
            emb_file=emb_file, ana_file=ana_file,
            n_total=n_total, n_valid=0, n_clusters=0, n_noise=0,
            silhouette=None, status="failed",
            generated_at=generated_at,
        )
        sys.exit(1)

    # ── 5. Cluster ────────────────────────────────────────────────────────────
    try:
        labels, algo_used, algo_params = run_clustering(df, args.algorithm, args.min_cluster_size)
    except Exception:
        logger.error(f"Clustering failed:\n{traceback.format_exc()}")
        sys.exit(1)

    n_clusters = int(len(set(labels) - {-1}))
    n_noise    = int((labels == -1).sum())
    silhouette: Optional[float] = algo_params.get("silhouette")

    # ── 6. Analyse clusters ───────────────────────────────────────────────────
    try:
        centers, cluster_diags = analyse_clusters(
            df, labels, algo_used, emb_file, ana_file, topic_slug
        )
    except Exception:
        logger.error(f"Cluster analysis failed:\n{traceback.format_exc()}")
        centers, cluster_diags = [], []

    # ── 7. Write outputs ──────────────────────────────────────────────────────
    try:
        write_manifest(
            out_dir, run_id,
            topic_slug=topic_slug, algorithm=algo_used, algo_params=algo_params,
            emb_file=emb_file, ana_file=ana_file,
            n_total=n_total, n_valid=n_valid, n_clusters=n_clusters, n_noise=n_noise,
            silhouette=silhouette, status="success",
            generated_at=generated_at,
        )
        write_members_csv(out_dir, run_id, df, labels, emb_file)
        write_centers(out_dir, run_id, centers)
        write_diagnostics(out_dir, run_id, cluster_diags, discarded_items=[])
        write_projection_csv(out_dir, run_id, df, labels)
    except Exception:
        logger.error(f"Failed to write outputs:\n{traceback.format_exc()}")
        sys.exit(1)

    # ── 8. Summary ────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"DONE | topic='{topic_slug}'")
    logger.info(f"  embeddings file : {emb_file.name}")
    logger.info(f"  analysis file   : {ana_file.name if ana_file else 'N/A'}")
    logger.info(f"  algorithm       : {algo_used}")
    logger.info(f"  clusters        : {n_clusters}")
    logger.info(f"  noise points    : {n_noise}")
    logger.info(f"  output dir      : {out_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
