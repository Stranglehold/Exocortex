#!/usr/bin/env python3
"""
query_corpus.py — Find nearest Opus outputs to a query in the instrument corpus.

Embeds a text query through the same model used to build the corpus and returns
the N nearest stored outputs by cosine similarity. Supports filtering by type,
quality signal, and session.

Usage:
    python query_corpus.py "why does getting this right matter" --top 5
    python query_corpus.py "bv testing philosophical depth" --top 3 --type essay
    python query_corpus.py "orientation session start" --quality sharp --top 10
"""

import argparse
import json
import sys
import numpy as np
import faiss
import requests
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

EMBED_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"

CORPUS_DIR = Path(__file__).parent / "data"
FAISS_PATH = CORPUS_DIR / "corpus.faiss"
META_PATH = CORPUS_DIR / "corpus_metadata.json"

# ── Embedding ────────────────────────────────────────────────────────────────


def get_embedding(text: str) -> np.ndarray:
    resp = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "input": text}, timeout=60)
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Query the instrument corpus by semantic similarity."
    )
    parser.add_argument("query", help="Query text")
    parser.add_argument("--top", type=int, default=5, help="Number of results (default 5)")
    parser.add_argument("--type", dest="doc_type", default=None, help="Filter by document type")
    parser.add_argument("--quality", default=None, help="Filter by quality signal")
    parser.add_argument("--session", type=int, default=None, help="Filter by session number")
    parser.add_argument(
        "--show-preview", action="store_true", help="Show full 200-char text preview"
    )
    args = parser.parse_args()

    if not FAISS_PATH.exists() or not META_PATH.exists():
        print("ERROR: Corpus not found. Run embed_output.py first.")
        return 1

    index = faiss.read_index(str(FAISS_PATH))
    with open(META_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    if index.ntotal == 0:
        print("Corpus is empty.")
        return 0

    print(f'Query: "{args.query}"')
    print(f"Corpus: {index.ntotal} entries\n")

    vec = get_embedding(args.query)

    # Search more than needed so filters don't starve the result set
    k = min(index.ntotal, max(args.top * 10, 50))
    scores, ids = index.search(vec.reshape(1, -1), k)

    results = []
    for score, faiss_id in zip(scores[0], ids[0]):
        if faiss_id < 0 or faiss_id >= len(entries):
            continue
        entry = entries[faiss_id]
        if args.doc_type and entry.get("document_type") != args.doc_type:
            continue
        if args.quality and entry.get("quality_signal") != args.quality:
            continue
        if args.session is not None and entry.get("session") != args.session:
            continue
        results.append((float(score), entry))
        if len(results) >= args.top:
            break

    if not results:
        print("No results match the query and filters.")
        return 0

    print(f"Top {len(results)} results (cosine similarity):\n")
    for i, (score, entry) in enumerate(results, 1):
        quality = entry.get("quality_signal") or "unrated"
        tags = ", ".join(entry.get("topic_tags", [])) or "none"
        print(f"  {i}. [{score:.4f}]  {entry['id']}")
        print(f"     File:    {entry['source_file']}")
        print(f"     Session: {entry['session']}  Type: {entry['document_type']}  Quality: {quality}")
        print(f"     Tags:    {tags}")
        if args.show_preview:
            print(f"     Preview: {entry['text_preview']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
