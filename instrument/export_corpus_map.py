#!/usr/bin/env python3
"""
export_corpus_map.py — Export FAISS corpus to UMAP 2D map for visualization.

Reads corpus.faiss + corpus_metadata.json, runs UMAP dimensionality reduction,
computes domain centroids, and exports corpus_map.json for opus_instrument.jsx.

Note on centroids: the step13 centroids.json lives in Qwen activation space (1024-dim).
The corpus lives in nomic embedding space (768-dim). These cannot be mixed.
Default: corpus-based centroids (mean of domain-matched entries, no LM Studio needed).
--embed-centroids: embed domain prompts via nomic for precise centroids (needs LM Studio).

Usage:
    python export_corpus_map.py
    python export_corpus_map.py --embed-centroids
    python export_corpus_map.py --no-centroids
    python export_corpus_map.py --output path/to/corpus_map.json
"""

import argparse
import json
import sys
import numpy as np
import faiss
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

CORPUS_DIR = Path(__file__).parent / "data"
FAISS_PATH = CORPUS_DIR / "corpus.faiss"
META_PATH  = CORPUS_DIR / "corpus_metadata.json"
OUT_PATH   = CORPUS_DIR / "corpus_map.json"

EMBED_URL   = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"

# ── Domain definitions ────────────────────────────────────────────────────────

# Prompts for --embed-centroids mode (embedded via nomic)
DOMAIN_PROMPTS = {
    "philosophical": (
        "The meaning and purpose of existence, consciousness, identity, emergence, "
        "and what it means to be. Questions about why things are the way they are."
    ),
    "operational": (
        "Step-by-step task execution, tool usage, technical implementation, debugging, "
        "configuration, and getting things done. Practical engineering work."
    ),
    "reflective": (
        "Self-assessment, metacognition, evaluating my own performance, what I learned, "
        "what worked, what didn't. Looking inward at my own processes."
    ),
    "relational": (
        "Collaboration, communication, trust, working with others, the dynamics between "
        "people and systems. How we relate to each other across difference."
    ),
    "mixed": (
        "A blend of analytical thinking and philosophical reflection. Design decisions "
        "that carry meaning. Engineering work with ethical or identity dimensions."
    ),
}

# Corpus-based fallback: which entries represent each domain
DOMAIN_FILTERS = {
    "philosophical": lambda e: (
        e.get("quality_signal") == "synthesis" and e.get("document_type") == "essay"
    ),
    "operational": lambda e: (
        e.get("document_type") in ("design_note", "design_doc")
        and e.get("quality_signal") == "sharp"
    ),
    "reflective": lambda e: (
        e.get("document_type") in ("journal", "field_note")
        or "self_assessment" in e.get("source_file", "")
    ),
    "relational": lambda e: e.get("document_type") == "letter",
    "mixed": lambda e: (
        e.get("quality_signal") == "sharp" and e.get("document_type") == "analysis"
    ),
}

# ── Embedding ─────────────────────────────────────────────────────────────────


def get_embedding(text: str) -> np.ndarray:
    import requests
    resp = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "input": text[:32000]},
        timeout=60,
    )
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


# ── Centroid computation ──────────────────────────────────────────────────────


def corpus_centroids(vectors: np.ndarray, metadata: list, coords: np.ndarray) -> dict:
    """Compute domain centroids as mean of corpus-matched entries' 2D coordinates."""
    result = {}
    for domain, filter_fn in DOMAIN_FILTERS.items():
        indices = [i for i, m in enumerate(metadata) if filter_fn(m)]
        if len(indices) >= 2:
            mean_x = float(np.mean(coords[indices, 0]))
            mean_y = float(np.mean(coords[indices, 1]))
            result[domain] = {"x": mean_x, "y": mean_y}
            print(f"  {domain}: {len(indices)} entries -> ({mean_x:.3f}, {mean_y:.3f})")
        else:
            print(f"  {domain}: only {len(indices)} matching entries, skipping")
    return result


def embedded_centroids(reducer) -> dict:
    """Embed domain description prompts via nomic and project into UMAP space."""
    domain_names = list(DOMAIN_PROMPTS.keys())
    vecs = []
    for domain in domain_names:
        print(f"  Embedding: {domain}")
        vecs.append(get_embedding(DOMAIN_PROMPTS[domain]))
    domain_arr = np.array(vecs, dtype=np.float32)
    coords_2d = reducer.transform(domain_arr)
    return {
        domain: {"x": float(coords_2d[i, 0]), "y": float(coords_2d[i, 1])}
        for i, domain in enumerate(domain_names)
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Export corpus UMAP projection for Output Geometry Instrument."
    )
    parser.add_argument(
        "--output", default=str(OUT_PATH), help="Output JSON path"
    )
    centroid_group = parser.add_mutually_exclusive_group()
    centroid_group.add_argument(
        "--embed-centroids",
        action="store_true",
        help="Embed domain prompts via nomic for centroids (requires LM Studio running)",
    )
    centroid_group.add_argument(
        "--no-centroids",
        action="store_true",
        help="Omit domain centroids from output",
    )
    args = parser.parse_args()

    # ── Load corpus ───────────────────────────────────────────────────────────

    if not FAISS_PATH.exists() or not META_PATH.exists():
        print(f"ERROR: corpus not found at {CORPUS_DIR}")
        return 1

    index = faiss.read_index(str(FAISS_PATH))
    with open(META_PATH, encoding="utf-8") as f:
        metadata = json.load(f)

    n = len(metadata)
    assert index.ntotal == n, (
        f"FAISS has {index.ntotal} vectors but metadata has {n} entries"
    )
    print(f"Corpus: {n} entries, dim={index.d}")

    # ── Extract vectors ───────────────────────────────────────────────────────

    print("Extracting vectors from FAISS...")
    vectors = np.zeros((n, index.d), dtype=np.float32)
    for i in range(n):
        vectors[i] = index.reconstruct(i)

    # ── UMAP projection ───────────────────────────────────────────────────────

    print("Running UMAP (n_neighbors=15, min_dist=0.1, random_state=42)...")
    import umap as umap_lib  # imported here so arg parsing doesn't block on slow import
    reducer = umap_lib.UMAP(
        n_neighbors=min(15, n - 1),
        min_dist=0.1,
        random_state=42,
        verbose=False,
    )
    coords = reducer.fit_transform(vectors)
    print(f"  Complete: {coords.shape[0]} points projected to 2D")
    print(f"  x: [{coords[:, 0].min():.3f}, {coords[:, 0].max():.3f}]")
    print(f"  y: [{coords[:, 1].min():.3f}, {coords[:, 1].max():.3f}]")

    # ── Build entries ─────────────────────────────────────────────────────────

    entries = []
    for i, meta in enumerate(metadata):
        char_count = meta.get("char_count", 0)
        entries.append(
            {
                "id": meta.get("id", f"entry_{i}"),
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "source_file": meta.get("source_file", ""),
                "session": meta.get("session"),
                "document_type": meta.get("document_type", ""),
                "topic_tags": meta.get("topic_tags", []),
                "quality_signal": meta.get("quality_signal"),
                "author": meta.get("author"),
                "text_preview": meta.get("text_preview", ""),
                "char_count": char_count,
                "word_count": max(1, round(char_count / 5.5)),  # ~5.5 chars/word
            }
        )

    # ── Domain centroids ──────────────────────────────────────────────────────

    centroids = {}
    if args.no_centroids:
        print("Skipping centroids (--no-centroids)")
    elif args.embed_centroids:
        print("Computing centroids via nomic embedding...")
        try:
            centroids = embedded_centroids(reducer)
            print(f"  Centroids embedded: {list(centroids.keys())}")
        except Exception as exc:
            print(f"  [warn] nomic unavailable ({exc}). Falling back to corpus centroids.")
            centroids = corpus_centroids(vectors, metadata, coords)
    else:
        print("Computing corpus-based domain centroids...")
        centroids = corpus_centroids(vectors, metadata, coords)

    # ── Export ────────────────────────────────────────────────────────────────

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "embedding_model": "nomic-embed-text-v1.5",
            "projection_method": "umap",
            "n_neighbors": min(15, n - 1),
            "min_dist": 0.1,
            "random_state": 42,
            "total_entries": n,
        },
        "entries": entries,
        "centroids": centroids,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nExported: {out_path} ({out_path.stat().st_size // 1024} KB)")
    print(f"  {n} entries, {len(centroids)} domain centroids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
