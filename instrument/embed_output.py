#!/usr/bin/env python3
"""
embed_output.py — Add an Opus output to the instrument corpus.

Embeds a text file through the local nomic embedding model in LM Studio and
stores the result in FAISS with a JSON metadata sidecar. Foundation for the
Output Geometry Instrument described in the Prosthetic Cortex Design Note.

Usage:
    python embed_output.py --file path/to/output.md --session 49 --type journal
    python embed_output.py --file essay.md --session 49 --type essay \\
        --tags "bv_testing,qwen_profile" --quality sharp
"""

import argparse
import json
import sys
import numpy as np
import faiss
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

EMBED_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
EMBED_DIM = 768
MAX_CHARS = 32000  # rough ceiling; nomic supports ~8k tokens

CORPUS_DIR = Path(__file__).parent / "data"
FAISS_PATH = CORPUS_DIR / "corpus.faiss"
META_PATH = CORPUS_DIR / "corpus_metadata.json"

VALID_TYPES = {"journal", "design_note", "essay", "letter", "analysis", "conversation", "design_doc", "field_note", "log", "index"}
VALID_QUALITY = {"sharp", "flat", "synthesis", "routine"}
VALID_AUTHORS = {"opus_architect", "opus_agent_zero", "kestrel"}

# ── Embedding ────────────────────────────────────────────────────────────────


def get_embedding(text: str) -> np.ndarray:
    """Embed text via LM Studio. Returns a normalized float32 vector."""
    if len(text) > MAX_CHARS:
        print(f"  [warn] text truncated from {len(text):,} to {MAX_CHARS:,} chars")
        text = text[:MAX_CHARS]
    resp = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "input": text}, timeout=60)
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    # Normalize to unit length so FAISS inner product = cosine similarity
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


# ── Corpus I/O ───────────────────────────────────────────────────────────────


def load_corpus():
    """Load or create FAISS index and metadata list."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    if FAISS_PATH.exists() and META_PATH.exists():
        index = faiss.read_index(str(FAISS_PATH))
        with open(META_PATH, encoding="utf-8") as f:
            entries = json.load(f)
    else:
        index = faiss.IndexFlatIP(EMBED_DIM)
        entries = []
    return index, entries


def save_corpus(index, entries):
    faiss.write_index(index, str(FAISS_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Add an Opus output to the instrument corpus."
    )
    parser.add_argument("--file", required=True, help="Path to the text file to embed")
    parser.add_argument("--session", type=int, default=0, help="Session number (e.g. 49)")
    parser.add_argument(
        "--type",
        dest="doc_type",
        default="analysis",
        choices=sorted(VALID_TYPES),
        help="Document type",
    )
    parser.add_argument("--tags", default="", help="Comma-separated topic tags")
    parser.add_argument(
        "--quality",
        default=None,
        choices=sorted(VALID_QUALITY),
        help="Quality signal — fill now or update later with --update",
    )
    parser.add_argument(
        "--author",
        default=None,
        choices=sorted(VALID_AUTHORS),
        help="Author/instance that produced this output",
    )
    args = parser.parse_args()

    source = Path(args.file)
    if not source.exists():
        print(f"ERROR: File not found: {args.file}")
        return 1

    text = source.read_text(encoding="utf-8")
    if not text.strip():
        print("ERROR: File is empty")
        return 1

    print(f"Embedding: {source.name}  ({len(text):,} chars)")
    vec = get_embedding(text)
    print(f"  Vector: dim={len(vec)}, norm={np.linalg.norm(vec):.6f}")

    index, entries = load_corpus()

    faiss_id = index.ntotal
    session_entries = [e for e in entries if e.get("session") == args.session]
    doc_id = f"opus_output_{args.session:03d}_{len(session_entries) + 1:03d}"

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    entry = {
        "faiss_id": faiss_id,
        "id": doc_id,
        "text_preview": text[:200].replace("\n", " "),
        "source_file": source.name,
        "session": args.session,
        "document_type": args.doc_type,
        "topic_tags": tags,
        "quality_signal": args.quality,
        "author": args.author,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "embedding_model": EMBED_MODEL,
        "char_count": len(text),
    }

    index.add(vec.reshape(1, -1))
    entries.append(entry)
    save_corpus(index, entries)

    print(f"  Stored as {doc_id}  (faiss_id={faiss_id})")
    print(f"  Corpus: {index.ntotal} entries total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
