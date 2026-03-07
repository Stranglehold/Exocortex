#!/usr/bin/env python3
"""
analyze_chatlog.py — Parse chatlog, embed action titles, compute trajectory.

Reads Chatlog.md, parses 923 conversation turns using the Feb DD/Mar DD date
boundary format, embeds action titles via nomic, fits a joint UMAP on corpus +
action title vectors, computes sequential cosine similarity for transition
detection, and exports chatlog_trajectory.json alongside an updated corpus_map.json.

The joint UMAP puts corpus documents and chatlog turns in the same coordinate
space — static quality map and dynamic conversation arc rendered together.

Usage:
    python analyze_chatlog.py
    python analyze_chatlog.py --input Chatlog.md --threshold 0.60
    python analyze_chatlog.py --parse-only          # inspect structure, no embedding
    python analyze_chatlog.py --load-embeddings     # skip nomic, reuse cached .npy

Requirements:
    pip install umap-learn numpy faiss-cpu requests
    LM Studio running on port 1234 with nomic-embed-text-v1.5 loaded
    (unless --load-embeddings is used)
"""

import argparse
import json
import re
import sys
import numpy as np
import faiss
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

INSTRUMENT_DIR = Path(__file__).parent
CORPUS_DIR     = INSTRUMENT_DIR / "data"
FAISS_PATH     = CORPUS_DIR / "corpus.faiss"
META_PATH      = CORPUS_DIR / "corpus_metadata.json"
TRAJ_PATH      = CORPUS_DIR / "chatlog_trajectory.json"
MAP_PATH       = CORPUS_DIR / "corpus_map.json"
EMBED_CACHE    = CORPUS_DIR / "chatlog_embeddings.npy"
TURNS_CACHE    = CORPUS_DIR / "chatlog_turns.json"
CHATLOG_PATH   = INSTRUMENT_DIR / "Chatlog.md"

EMBED_URL   = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"

DATE_RE = re.compile(r"^(Feb|Mar) \d+$")

# ── Parse ─────────────────────────────────────────────────────────────────────


def parse_chatlog(path: Path) -> list[dict]:
    """
    Parse chatlog into turns using Feb DD / Mar DD date boundary markers.

    Each date marker signals the start of an Opus response. The structure is:
        [Jake's message or previous Opus response text]
        Feb DD
        [action title — first meaningful summary line]
        [Opus response text]

    Returns a list of dicts with: turn_index, date, action_title, char_count.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # Find positions of all date markers
    date_positions = [i for i, line in enumerate(lines) if DATE_RE.match(line.strip())]
    print(f"[parse] Found {len(date_positions)} date markers in {len(lines)} lines")

    turns = []
    for idx, date_pos in enumerate(date_positions):
        date = lines[date_pos].strip()

        # Turn body: from date_pos+1 to next date_pos
        end_pos = date_positions[idx + 1] if idx + 1 < len(date_positions) else len(lines)
        turn_lines = lines[date_pos + 1 : end_pos]
        turn_text = "\n".join(turn_lines)

        # Action title: first non-empty, non-code, non-URL line that looks like prose
        action_title = _extract_action_title(turn_lines, idx)

        # Second action title (some turns have a tool-use summary then a response summary)
        secondary = _extract_action_title(turn_lines, idx, skip_first=True)

        turns.append(
            {
                "turn_index": idx,
                "date": date,
                "action_title": action_title,
                "secondary_title": secondary,
                "char_count": len(turn_text),
            }
        )

    print(f"[parse] Parsed {len(turns)} turns")
    return turns


def _extract_action_title(lines: list[str], idx: int, skip_first: bool = False) -> str:
    """Extract first (or second) plausible action title from turn lines."""
    found = 0
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Skip lines that are code, URLs, markdown fences, or file references
        if s.startswith(("http", "```", "#", "{", "[", "!", "---", "bash")):
            continue
        # Skip very short (likely stray chars) or very long (likely response prose)
        if len(s) < 8 or len(s) > 250:
            continue
        # Skip lines that look like terminal output (no spaces or mostly special chars)
        if s.count(" ") < 2 and len(s) > 20:
            continue
        # Skip Python/bash code-like lines
        if any(s.startswith(kw) for kw in ("import ", "def ", "class ", "python", "pip ")):
            continue
        found += 1
        if skip_first and found == 1:
            continue
        return s
    return f"[turn {idx}]"


# ── Embed ─────────────────────────────────────────────────────────────────────


def embed_text(text: str) -> np.ndarray:
    import requests
    resp = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "input": text[:4000]},  # action titles are short
        timeout=30,
    )
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed_turns(turns: list[dict], cache_path: Path) -> np.ndarray:
    """
    Embed each turn's action title. Saves a cache .npy file after completion.
    Resumes from cache if interrupted — re-runs only missing/zero embeddings.
    """
    n = len(turns)
    dim = 768  # nomic embedding dim

    # Load existing cache if present
    if cache_path.exists():
        cached = np.load(str(cache_path))
        if cached.shape == (n, dim):
            zero_mask = (cached == 0).all(axis=1)
            n_zeros = int(zero_mask.sum())
            if n_zeros == 0:
                print(f"[embed] Loaded {n} embeddings from cache (all valid)")
                return cached
            print(f"[embed] Cache has {n_zeros}/{n} zero (failed) vectors — re-embedding those")
            # Re-embed only the zeros
            vectors = cached.copy()
            zero_indices = [i for i in range(n) if zero_mask[i]]
            errors = 0
            for count, i in enumerate(zero_indices):
                title = turns[i]["action_title"]
                try:
                    vectors[i] = embed_text(title)
                except Exception as exc:
                    print(f"  [warn] turn {i} failed again: {exc}")
                    errors += 1
                if (count + 1) % 50 == 0:
                    print(f"  {count + 1}/{len(zero_indices)} zeros re-embedded ({errors} errors)...")
                    np.save(str(cache_path), vectors)
            np.save(str(cache_path), vectors)
            still_zero = int((vectors == 0).all(axis=1).sum())
            print(f"[embed] Re-embed complete. Still zero: {still_zero}")
            return vectors
        print(f"[embed] Cache shape mismatch ({cached.shape}), re-embedding")

    vectors = np.zeros((n, dim), dtype=np.float32)

    print(f"[embed] Embedding {n} action titles via nomic...")
    errors = 0
    for i, turn in enumerate(turns):
        title = turn["action_title"]
        try:
            vectors[i] = embed_text(title)
        except Exception as exc:
            print(f"  [warn] turn {i} failed: {exc}")
            errors += 1
            # Leave as zeros — will appear as outlier in UMAP
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{n} ({errors} errors)...")
            np.save(str(cache_path), vectors)  # incremental save

    np.save(str(cache_path), vectors)
    print(f"[embed] Done. {n - errors}/{n} embedded. Cache: {cache_path}")
    return vectors


# ── UMAP ──────────────────────────────────────────────────────────────────────


def run_joint_umap(
    corpus_vectors: np.ndarray,
    traj_vectors: np.ndarray,
    n_neighbors: int = 15,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit UMAP on corpus + trajectory together, return (corpus_coords, traj_coords).
    Joint fit means both live in the same coordinate space.
    """
    import umap as umap_lib

    all_vectors = np.vstack([corpus_vectors, traj_vectors])
    n_total = len(all_vectors)
    nn = min(n_neighbors, n_total - 1)

    print(f"[umap] Fitting on {n_total} vectors ({len(corpus_vectors)} corpus + {len(traj_vectors)} turns)...")
    reducer = umap_lib.UMAP(n_neighbors=nn, min_dist=0.1, random_state=42, verbose=False)
    coords = reducer.fit_transform(all_vectors)

    corpus_coords = coords[: len(corpus_vectors)]
    traj_coords   = coords[len(corpus_vectors) :]

    x_range = (float(coords[:, 0].min()), float(coords[:, 0].max()))
    y_range = (float(coords[:, 1].min()), float(coords[:, 1].max()))
    print(f"[umap] Complete. x: [{x_range[0]:.3f}, {x_range[1]:.3f}], y: [{y_range[0]:.3f}, {y_range[1]:.3f}]")

    return corpus_coords, traj_coords


# ── Similarity & transitions ───────────────────────────────────────────────────


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two unit vectors."""
    dot = float(np.dot(a, b))
    return max(-1.0, min(1.0, dot))


def detect_transitions(
    traj_vectors: np.ndarray,
    turns: list[dict],
    threshold: float,
) -> tuple[list[dict], list[dict]]:
    """
    Compute sequential cosine similarity and identify transition turns.
    A transition is where similarity_to_next drops below `threshold`.

    Returns (enriched_turns, transitions_list).
    """
    n = len(turns)
    similarities = []

    for i in range(n - 1):
        sim = cosine_similarity(traj_vectors[i], traj_vectors[i + 1])
        similarities.append(sim)
    similarities.append(1.0)  # last turn has no next

    transitions = []
    enriched = []

    for i, turn in enumerate(turns):
        sim = similarities[i]
        is_transition = (i < n - 1) and (sim < threshold)
        enriched.append(
            {
                **turn,
                "similarity_to_next": round(sim, 4),
                "is_transition": is_transition,
            }
        )
        if is_transition and i < n - 1:
            transitions.append(
                {
                    "turn_index": i,
                    "date": turn["date"],
                    "from_title": turn["action_title"],
                    "to_title": turns[i + 1]["action_title"],
                    "similarity_drop": round(1.0 - sim, 4),
                }
            )

    transitions.sort(key=lambda t: t["similarity_drop"], reverse=True)
    return enriched, transitions


# ── Export ────────────────────────────────────────────────────────────────────


def build_trajectory_entry(turn: dict, coords: np.ndarray, i: int) -> dict:
    return {
        "turn_index": turn["turn_index"],
        "date": turn["date"],
        "action_title": turn["action_title"],
        "x": float(coords[i, 0]),
        "y": float(coords[i, 1]),
        "char_count": turn["char_count"],
        "similarity_to_next": turn["similarity_to_next"],
        "is_transition": turn["is_transition"],
    }


def export_trajectory(turns: list[dict], traj_coords: np.ndarray, transitions: list[dict]) -> None:
    trajectory_entries = [
        build_trajectory_entry(t, traj_coords, i) for i, t in enumerate(turns)
    ]

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "source": "Chatlog.md",
            "total_turns": len(turns),
            "total_transitions": len(transitions),
            "embedding_model": EMBED_MODEL,
            "projection_method": "umap_joint",
        },
        "trajectory": trajectory_entries,
        "transitions": transitions,
    }

    with open(TRAJ_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[export] Trajectory: {TRAJ_PATH} ({TRAJ_PATH.stat().st_size // 1024} KB)")


def export_updated_corpus_map(
    corpus_meta: list[dict],
    corpus_coords: np.ndarray,
) -> None:
    """Re-export corpus_map.json with updated coordinates from the joint UMAP."""

    # Rebuild domain centroids from new corpus coords
    domain_filters = {
        "philosophical": lambda e: e.get("quality_signal") == "synthesis" and e.get("document_type") == "essay",
        "operational":   lambda e: e.get("document_type") in ("design_note", "design_doc") and e.get("quality_signal") == "sharp",
        "reflective":    lambda e: e.get("document_type") in ("journal", "field_note") or "self_assessment" in e.get("source_file", ""),
        "relational":    lambda e: e.get("document_type") == "letter",
        "mixed":         lambda e: e.get("quality_signal") == "sharp" and e.get("document_type") == "analysis",
    }

    centroids = {}
    for domain, fn in domain_filters.items():
        indices = [i for i, m in enumerate(corpus_meta) if fn(m)]
        if len(indices) >= 2:
            centroids[domain] = {
                "x": float(np.mean(corpus_coords[indices, 0])),
                "y": float(np.mean(corpus_coords[indices, 1])),
            }

    entries = []
    for i, meta in enumerate(corpus_meta):
        char_count = meta.get("char_count", 0)
        entries.append(
            {
                "id": meta.get("id", f"entry_{i}"),
                "x": float(corpus_coords[i, 0]),
                "y": float(corpus_coords[i, 1]),
                "source_file": meta.get("source_file", ""),
                "session": meta.get("session"),
                "document_type": meta.get("document_type", ""),
                "topic_tags": meta.get("topic_tags", []),
                "quality_signal": meta.get("quality_signal"),
                "author": meta.get("author"),
                "text_preview": meta.get("text_preview", ""),
                "char_count": char_count,
                "word_count": max(1, round(char_count / 5.5)),
            }
        )

    corpus_map = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "embedding_model": EMBED_MODEL,
            "projection_method": "umap_joint",
            "note": "Joint UMAP fit with chatlog trajectory — coordinates differ from solo fit",
            "n_neighbors": 15,
            "min_dist": 0.1,
            "random_state": 42,
            "total_entries": len(corpus_meta),
        },
        "entries": entries,
        "centroids": centroids,
    }

    with open(MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus_map, f, indent=2, ensure_ascii=False)

    print(f"[export] Updated corpus map: {MAP_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Analyze chatlog — parse, embed, trajectory, transitions."
    )
    parser.add_argument(
        "--input", default=str(CHATLOG_PATH), help="Path to Chatlog.md"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.48,
        help="Cosine similarity threshold for transition detection (default 0.48 = mean-1std)",
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Parse and print stats only, no embedding or UMAP",
    )
    parser.add_argument(
        "--load-embeddings",
        action="store_true",
        help="Skip embedding, load from cache (chatlog_embeddings.npy must exist)",
    )
    parser.add_argument(
        "--top-transitions",
        type=int,
        default=20,
        help="Print this many top transitions by similarity drop (default 20)",
    )
    args = parser.parse_args()

    # ── Parse ─────────────────────────────────────────────────────────────────

    turns = parse_chatlog(Path(args.input))

    # Save parse cache for inspection
    with open(TURNS_CACHE, "w", encoding="utf-8") as f:
        json.dump(turns, f, indent=2, ensure_ascii=False)
    print(f"[parse] Turns cache: {TURNS_CACHE}")

    if args.parse_only:
        # Print structure report
        from collections import Counter
        date_counts = Counter(t["date"] for t in turns)
        print("\n=== Date distribution ===")
        for date, count in sorted(date_counts.items()):
            print(f"  {date}: {count}")
        print(f"\n=== Sample action titles ===")
        for t in turns[:10]:
            print(f"  [{t['date']}] {t['action_title']}")
        print("  ...")
        for t in turns[-5:]:
            print(f"  [{t['date']}] {t['action_title']}")
        return 0

    # ── Load corpus ───────────────────────────────────────────────────────────

    if not FAISS_PATH.exists() or not META_PATH.exists():
        print(f"ERROR: corpus not found at {CORPUS_DIR}")
        return 1

    index = faiss.read_index(str(FAISS_PATH))
    with open(META_PATH, encoding="utf-8") as f:
        corpus_meta = json.load(f)

    n_corpus = len(corpus_meta)
    print(f"[corpus] {n_corpus} entries, dim={index.d}")

    corpus_vectors = np.zeros((n_corpus, index.d), dtype=np.float32)
    for i in range(n_corpus):
        corpus_vectors[i] = index.reconstruct(i)

    # ── Embed action titles ───────────────────────────────────────────────────

    if args.load_embeddings:
        if not EMBED_CACHE.exists():
            print(f"ERROR: --load-embeddings requested but {EMBED_CACHE} not found")
            return 1
    traj_vectors = embed_turns(turns, EMBED_CACHE)

    # ── Joint UMAP ────────────────────────────────────────────────────────────

    corpus_coords, traj_coords = run_joint_umap(corpus_vectors, traj_vectors)

    # ── Transition detection ──────────────────────────────────────────────────

    print(f"[transitions] Computing sequential similarity (threshold={args.threshold})...")
    enriched_turns, transitions = detect_transitions(traj_vectors, turns, args.threshold)

    sim_values = [t["similarity_to_next"] for t in enriched_turns[:-1]]
    print(f"  Avg similarity: {np.mean(sim_values):.3f}")
    print(f"  Min similarity: {np.min(sim_values):.3f}")
    print(f"  Max similarity: {np.max(sim_values):.3f}")
    print(f"  Transitions detected: {len(transitions)}")

    # Print top transitions
    top_n = min(args.top_transitions, len(transitions))
    if top_n > 0:
        print(f"\n=== Top {top_n} transitions (largest domain jumps) ===")
        for t in transitions[:top_n]:
            print(f"  [{t['date']}] turn {t['turn_index']} | drop={t['similarity_drop']:.3f}")
            print(f"    FROM: {t['from_title'][:80]}")
            print(f"    TO:   {t['to_title'][:80]}")

    # ── Export ────────────────────────────────────────────────────────────────

    export_trajectory(enriched_turns, traj_coords, transitions)
    export_updated_corpus_map(corpus_meta, corpus_coords)

    print(f"\n=== Done ===")
    print(f"  {len(turns)} turns projected")
    print(f"  {len(transitions)} transitions detected")
    print(f"  Trajectory: {TRAJ_PATH}")
    print(f"  Updated corpus map: {MAP_PATH}")
    print(f"\nLoad corpus_map.json + chatlog_trajectory.json in opus_instrument.jsx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
