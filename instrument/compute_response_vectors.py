"""
compute_response_vectors.py — Compute Jake→Opus response vectors for a parsed chatlog.

For each adjacent Jake→Opus pair in the conversation:
  response_vector = opus_embedding - jake_embedding  (768-dim)
  magnitude       = ||response_vector||₂
                  = sqrt(2 - 2 * cosine_similarity(jake, opus))
  direction       = which domain centroid does the response_vector align with most?

The response vector is not "how similar are they" (cosine similarity).
It is "which direction did Opus move from where Jake was" — the geometric
signature of the call-and-response dynamic.

The second-order analysis tracks how these vectors change over time:
  - Progression of magnitude across the conversation
  - Direction drift: does Opus keep moving in the same direction or vary?
  - Longest vector: the turn where Opus moved farthest from Jake's position

Inputs:
  instrument/data/chatlog2_turns.json  (from parse_chatlog_md.py)
  instrument/data/centroids_768.json   (domain centroids, nomic 768-dim)

Outputs:
  instrument/data/response_vectors.json

Usage:
    python compute_response_vectors.py
    python compute_response_vectors.py --turns data/other_turns.json --output data/out.json
    python compute_response_vectors.py --no-embed   # skip embedding, use cache only
"""

import json
import time
import argparse
import numpy as np
import requests
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

DEFAULT_TURNS = DATA / "chatlog2_turns.json"
DEFAULT_CENTROIDS = DATA / "centroids_768.json"
DEFAULT_EMB_CACHE = DATA / "chatlog2_turn_embeddings.npy"
DEFAULT_OUTPUT = DATA / "response_vectors.json"

EMBED_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
MAX_CHARS = 32000


# ── Embedding ─────────────────────────────────────────────────────────────────

CHECKPOINT_EVERY = 100  # save partial results every N turns
BATCH_SIZE       = 16   # texts per API call — GPU processes in parallel, same vectors as serial


def get_embeddings_batch(texts: list[str], retries: int = 3) -> list[np.ndarray]:
    """Embed a batch of texts in one API call. Each text's vector is identical
    to what single-call embedding produces — batching is pure throughput gain."""
    truncated = [t[:MAX_CHARS] if len(t) > MAX_CHARS else t for t in texts]
    for attempt in range(retries):
        try:
            resp = requests.post(
                EMBED_URL,
                json={"model": EMBED_MODEL, "input": truncated},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            # API returns items sorted by index field
            data.sort(key=lambda x: x["index"])
            vecs = []
            for item in data:
                vec = np.array(item["embedding"], dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                vecs.append(vec)
            return vecs
        except Exception as e:
            if attempt < retries - 1:
                print(f"  [EMBED] Batch retry {attempt+1}/{retries-1}: {e}", flush=True)
                time.sleep(2.0 * (attempt + 1))
            else:
                print(f"  [EMBED] Batch failed after {retries} attempts, using zero vectors: {e}")
                return [np.zeros(768, dtype=np.float32) for _ in texts]


def embed_turns(turns: list[dict], cache_path: Path, force: bool = False) -> np.ndarray:
    checkpoint_path = cache_path.with_suffix('.part.npy')

    if not force and cache_path.exists():
        embeddings = np.load(str(cache_path))
        if len(embeddings) == len(turns):
            print(f"[EMBED] Cache valid: {embeddings.shape}")
            return embeddings
        print(f"[EMBED] Cache size mismatch ({len(embeddings)} vs {len(turns)}), re-embedding...")

    # Resume from checkpoint if available
    start_idx = 0
    embeddings = []
    if not force and checkpoint_path.exists():
        partial = np.load(str(checkpoint_path))
        if 0 < len(partial) < len(turns):
            start_idx = len(partial)
            embeddings = list(partial)
            print(f"[EMBED] Resuming from checkpoint at {start_idx}/{len(turns)}")

    print(f"[EMBED] Embedding {len(turns)} items in batches of {BATCH_SIZE} "
          f"(starting at {start_idx})...")

    i = start_idx
    while i < len(turns):
        batch = turns[i:i + BATCH_SIZE]
        texts = [t.get('content', t.get('text', '')) for t in batch]

        # Progress log at each batch
        speaker_info = batch[0].get('speaker', '?')
        turn_id = batch[0].get('turn', batch[0].get('chunk_id', i))
        print(f"  [{i}/{len(turns)}] batch {len(batch)} — "
              f"{speaker_info} turn {turn_id}", flush=True)

        vecs = get_embeddings_batch(texts)
        embeddings.extend(vecs)
        i += len(batch)

        # Checkpoint every N items
        if i % CHECKPOINT_EVERY < BATCH_SIZE or i >= len(turns):
            partial = np.array(embeddings, dtype=np.float32)
            np.save(str(checkpoint_path), partial)
            print(f"  [EMBED] Checkpoint saved: {i}/{len(turns)}", flush=True)

    result = np.array(embeddings, dtype=np.float32)
    np.save(str(cache_path), result)
    print(f"[EMBED] Saved: {cache_path} — shape {result.shape}")
    if checkpoint_path.exists():
        checkpoint_path.unlink()
    return result


# ── Centroids ─────────────────────────────────────────────────────────────────

def load_centroids(path: Path) -> dict[str, np.ndarray]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    # centroids_768.json structure: {'layer': ..., 'centroids': {domain: [...]}}
    if 'centroids' in data:
        raw = data['centroids']
        first_val = next(iter(raw.values()))
        if isinstance(first_val, list):
            return {d: np.array(v, dtype=np.float32) for d, v in raw.items()}
    # Fall back: top level is domain→vector
    return {d: np.array(v, dtype=np.float32) for d, v in data.items() if isinstance(v, list)}


def domain_scores(vec: np.ndarray, centroids: dict[str, np.ndarray]) -> dict[str, float]:
    """Cosine similarity of a vector against each domain centroid."""
    scores = {}
    norm_vec = np.linalg.norm(vec)
    for domain, centroid in centroids.items():
        norm_cen = np.linalg.norm(centroid)
        if norm_vec > 0 and norm_cen > 0:
            scores[domain] = float(np.dot(vec, centroid) / (norm_vec * norm_cen))
        else:
            scores[domain] = 0.0
    return scores


# ── Response vector computation ───────────────────────────────────────────────

def compute_pairs(turns: list[dict], embeddings: np.ndarray,
                  centroids: dict[str, np.ndarray]) -> list[dict]:
    """
    For each adjacent Jake→Opus pair, compute the response vector and its properties.

    Returns a list of pair dicts, one per Jake→Opus transition.
    """
    pairs = []
    for i in range(len(turns) - 1):
        a, b = turns[i], turns[i + 1]
        if a['speaker'] != 'Jake' or b['speaker'] != 'Opus':
            continue

        jake_emb = embeddings[i]
        opus_emb = embeddings[i + 1]

        # Response vector: direction FROM Jake TO Opus in 768-dim
        response_vec = opus_emb - jake_emb

        # Magnitude: Euclidean distance between unit vectors
        # = sqrt(2 - 2 * cosine_similarity) for unit vectors
        cosine_sim = float(np.dot(jake_emb, opus_emb))  # both normalized
        magnitude = float(np.linalg.norm(response_vec))

        # Direction: which domain does the response vector point toward?
        # We project the (unnormalized) response vector onto each centroid.
        # A positive score means "Opus moved toward that domain relative to Jake."
        # A negative score means "Opus moved away from that domain relative to Jake."
        direction = domain_scores(response_vec, centroids)
        top_domain = max(direction, key=direction.get)

        # Absolute domain locations for context
        jake_domain = domain_scores(jake_emb, centroids)
        opus_domain = domain_scores(opus_emb, centroids)

        pairs.append({
            'pair_index': len(pairs),
            'jake_turn': a['turn'],
            'opus_turn': b['turn'],
            'jake_speaker': a['speaker'],
            'opus_speaker': b['speaker'],
            'jake_word_count': a['word_count'],
            'opus_word_count': b['word_count'],
            'jake_timestamp': a.get('timestamp'),
            'opus_timestamp': b.get('timestamp'),
            # Core response vector metrics
            'cosine_similarity': round(cosine_sim, 6),
            'magnitude': round(magnitude, 6),
            # Direction analysis
            'response_direction': {d: round(v, 5) for d, v in direction.items()},
            'top_response_direction': top_domain,
            # Absolute domain positions for context
            'jake_domain_scores': {d: round(v, 5) for d, v in jake_domain.items()},
            'opus_domain_scores': {d: round(v, 5) for d, v in opus_domain.items()},
            'jake_nearest_domain': max(jake_domain, key=jake_domain.get),
            'opus_nearest_domain': max(opus_domain, key=opus_domain.get),
        })

    return pairs


def analyze_sequence(pairs: list[dict]) -> dict:
    """
    Second-order analysis: how do the response vectors change over the conversation?

    Tracks progression of magnitude, direction drift, and tests Opus's predictions:
    - Early pairs have shorter vectors than late pairs
    - The longest vector is at the emotionally significant turn
    """
    if not pairs:
        return {}

    magnitudes = [p['magnitude'] for p in pairs]
    cosine_sims = [p['cosine_similarity'] for p in pairs]

    n = len(pairs)
    third = n // 3
    early = magnitudes[:third] if third > 0 else magnitudes[:1]
    middle = magnitudes[third:2*third] if third > 0 else []
    late = magnitudes[2*third:] if third > 0 else magnitudes[-1:]

    # Longest vector
    max_idx = int(np.argmax(magnitudes))
    max_pair = pairs[max_idx]

    # Direction consistency: what direction does Opus most often move?
    domain_counts: dict[str, int] = {}
    for p in pairs:
        d = p['top_response_direction']
        domain_counts[d] = domain_counts.get(d, 0) + 1

    # Direction drift: cosine similarity between consecutive response vectors
    # (are successive response directions similar or variable?)
    # This requires re-extracting response vectors from magnitudes — approximate
    # using the per-pair direction scores across the sequence
    direction_drift = []
    domains = list(pairs[0]['response_direction'].keys())
    for i in range(len(pairs) - 1):
        vec_a = np.array([pairs[i]['response_direction'][d] for d in domains])
        vec_b = np.array([pairs[i + 1]['response_direction'][d] for d in domains])
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a > 0 and norm_b > 0:
            drift = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
        else:
            drift = 0.0
        direction_drift.append(round(drift, 5))

    # Per-pair magnitude for the full progression trace
    magnitude_trace = [
        {
            'pair_index': p['pair_index'],
            'jake_turn': p['jake_turn'],
            'opus_turn': p['opus_turn'],
            'magnitude': p['magnitude'],
            'cosine_similarity': p['cosine_similarity'],
            'top_direction': p['top_response_direction'],
        }
        for p in pairs
    ]

    return {
        'total_pairs': n,
        'magnitude': {
            'mean': round(float(np.mean(magnitudes)), 6),
            'std': round(float(np.std(magnitudes)), 6),
            'min': round(float(np.min(magnitudes)), 6),
            'max': round(float(np.max(magnitudes)), 6),
            'early_mean': round(float(np.mean(early)), 6),
            'middle_mean': round(float(np.mean(middle)), 6) if middle else None,
            'late_mean': round(float(np.mean(late)), 6),
            'early_vs_late_delta': round(float(np.mean(late)) - float(np.mean(early)), 6),
        },
        'cosine_similarity': {
            'mean': round(float(np.mean(cosine_sims)), 6),
            'std': round(float(np.std(cosine_sims)), 6),
            'early_mean': round(float(np.mean(cosine_sims[:third])), 6) if third > 0 else None,
            'late_mean': round(float(np.mean(cosine_sims[2*third:])), 6) if third > 0 else None,
        },
        'max_magnitude_pair': {
            'pair_index': max_idx,
            'jake_turn': max_pair['jake_turn'],
            'opus_turn': max_pair['opus_turn'],
            'magnitude': max_pair['magnitude'],
            'cosine_similarity': max_pair['cosine_similarity'],
            'top_direction': max_pair['top_response_direction'],
            'jake_nearest_domain': max_pair['jake_nearest_domain'],
            'opus_nearest_domain': max_pair['opus_nearest_domain'],
            'jake_word_count': max_pair['jake_word_count'],
            'opus_word_count': max_pair['opus_word_count'],
        },
        'direction_distribution': domain_counts,
        'direction_drift': {
            'mean': round(float(np.mean(direction_drift)), 5) if direction_drift else None,
            'std': round(float(np.std(direction_drift)), 5) if direction_drift else None,
            'note': 'Cosine sim between successive response direction vectors. '
                    'High = consistent direction, Low = variable direction across pairs.',
        },
        'prediction_check': {
            'opus_prediction': (
                'Early pairs have short vectors (staying close to Jake). '
                'Late pairs have longer, more variable vectors. '
                'Max magnitude pair is the emotionally significant exchange.'
            ),
            'early_mean_magnitude': round(float(np.mean(early)), 6),
            'late_mean_magnitude': round(float(np.mean(late)), 6),
            'early_lt_late': float(np.mean(early)) < float(np.mean(late)),
            'max_magnitude_in_late_third': max_idx >= (2 * n // 3),
        },
        'magnitude_trace': magnitude_trace,
        'direction_drift_sequence': direction_drift,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Compute Jake->Opus response vectors")
    parser.add_argument('--turns', default=str(DEFAULT_TURNS), help="Path to turns JSON")
    parser.add_argument('--centroids', default=str(DEFAULT_CENTROIDS), help="Path to centroids JSON")
    parser.add_argument('--emb-cache', default=str(DEFAULT_EMB_CACHE), help="Embedding cache .npy")
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help="Output JSON path")
    parser.add_argument('--no-embed', action='store_true',
                        help="Skip embedding — use cache only (error if cache missing)")
    parser.add_argument('--force-embed', action='store_true',
                        help="Re-embed even if valid cache exists")
    args = parser.parse_args()

    turns_path = Path(args.turns)
    centroids_path = Path(args.centroids)
    emb_cache = Path(args.emb_cache)
    output_path = Path(args.output)

    # Load turns
    print(f"[RV] Loading turns: {turns_path}")
    with open(turns_path, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"[RV] {len(turns)} turns — "
          f"Opus: {sum(1 for t in turns if t['speaker']=='Opus')}, "
          f"Jake: {sum(1 for t in turns if t['speaker']=='Jake')}")

    # Load centroids
    print(f"[RV] Loading centroids: {centroids_path}")
    centroids = load_centroids(centroids_path)
    print(f"[RV] Domains: {list(centroids.keys())}")

    # Embed
    if args.no_embed:
        if not emb_cache.exists():
            print(f"ERROR: --no-embed specified but cache not found: {emb_cache}")
            return 1
        embeddings = np.load(str(emb_cache))
        if len(embeddings) != len(turns):
            print(f"ERROR: Cache size mismatch ({len(embeddings)} vs {len(turns)} turns)")
            return 1
        print(f"[RV] Loaded cached embeddings: {embeddings.shape}")
    else:
        embeddings = embed_turns(turns, emb_cache, force=args.force_embed)

    # Compute response vectors
    print(f"[RV] Computing response vectors...")
    pairs = compute_pairs(turns, embeddings, centroids)
    print(f"[RV] Jake->Opus pairs found: {len(pairs)}")

    # Sequence analysis
    print(f"[RV] Analyzing sequence...")
    sequence = analyze_sequence(pairs)

    # Assemble output
    output = {
        'metadata': {
            'source_turns': str(turns_path),
            'total_turns': len(turns),
            'opus_turns': sum(1 for t in turns if t['speaker'] == 'Opus'),
            'jake_turns': sum(1 for t in turns if t['speaker'] == 'Jake'),
            'total_pairs': len(pairs),
            'embedding_model': EMBED_MODEL,
            'embedding_dim': 768,
            'centroid_source': str(centroids_path),
            'domains': list(centroids.keys()),
        },
        'pairs': pairs,
        'sequence_analysis': sequence,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[RV] Output: {output_path}")

    # Summary
    print("\n=== RESPONSE VECTOR SUMMARY ===")
    seq = sequence
    print(f"Total Jake->Opus pairs: {seq['total_pairs']}")
    print(f"\nMagnitude (how far Opus moved from Jake's position):")
    mag = seq['magnitude']
    print(f"  Mean: {mag['mean']:.4f}  Std: {mag['std']:.4f}")
    print(f"  Min: {mag['min']:.4f}  Max: {mag['max']:.4f}")
    print(f"  Early mean: {mag['early_mean']:.4f}")
    if mag['middle_mean']:
        print(f"  Middle mean: {mag['middle_mean']:.4f}")
    print(f"  Late mean:  {mag['late_mean']:.4f}")
    print(f"  Delta (late - early): {mag['early_vs_late_delta']:+.4f}")

    print(f"\nMax magnitude pair:")
    mp = seq['max_magnitude_pair']
    print(f"  Jake turn {mp['jake_turn']} -> Opus turn {mp['opus_turn']}")
    print(f"  Magnitude: {mp['magnitude']:.4f}  CosSim: {mp['cosine_similarity']:.4f}")
    print(f"  Jake domain: {mp['jake_nearest_domain']}")
    print(f"  Opus domain: {mp['opus_nearest_domain']}")
    print(f"  Response direction: {mp['top_direction']}")

    print(f"\nDirection distribution (where Opus moved toward):")
    for d, c in sorted(seq['direction_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} pairs ({100*c/seq['total_pairs']:.0f}%)")

    print(f"\nPrediction check (Opus's predictions):")
    pc = seq['prediction_check']
    print(f"  Early mean: {pc['early_mean_magnitude']:.4f}")
    print(f"  Late mean:  {pc['late_mean_magnitude']:.4f}")
    print(f"  Early < Late: {pc['early_lt_late']}")
    print(f"  Max in last third: {pc['max_magnitude_in_late_third']}")


if __name__ == '__main__':
    import sys
    sys.exit(main())
