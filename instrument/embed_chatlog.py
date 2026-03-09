"""
embed_chatlog.py — Embed chatlog turns and run full trajectory analysis.

Reads: instrument/data/chatlog_turns.json
Reads: instrument/data/evolution_embeddings.npy (46 evolution docs, 768-dim)
Reads: instrument/data/centroids.json (5 domain centroids at 4 layers)
Reads: instrument/data/geometry_analysis.json (existing trajectory data)

Produces: instrument/data/chatlog_analysis.json
  - Turn-level embeddings (768-dim)
  - Dual trajectory (Opus / Jake) in joint UMAP space
  - Inter-speaker cosine similarity per adjacent turn pair
  - Register classification per turn
  - Off-map detection
  - Transition detection (mean + 1sigma)
  - Comparison to existing action-title trajectory
"""

import json
import time
import numpy as np
import requests
from collections import Counter
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import umap

# --- Paths ---
ROOT = Path(__file__).parent
DATA = ROOT / "data"

TURNS_PATH = DATA / "chatlog_turns.json"
CORPUS_MAP_PATH = DATA / "corpus_map.json"
CENTROIDS_PATH = DATA / "centroids_768.json"  # nomic 768-dim centroids computed from corpus FAISS
EVOLUTION_EMB_PATH = DATA / "evolution_embeddings.npy"
GEOMETRY_PATH = DATA / "geometry_analysis.json"
TURN_EMB_PATH = DATA / "chatlog_turn_embeddings.npy"
OUTPUT_PATH = DATA / "chatlog_analysis.json"

EMBED_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
MAX_CHARS = 32000

# Layer to use for centroid-based classification (established in step 13)
CENTROID_LAYER = "18"  # key in centroids.json['centroids']


# --- Embedding ---

def get_embedding(text: str) -> np.ndarray:
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
    resp = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "input": text}, timeout=60)
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def embed_turns(turns: list[dict], cache_path: Path) -> np.ndarray:
    """Embed all turns. Saves to cache_path. Loads from cache if exists."""
    if cache_path.exists():
        print(f"[EMBED] Loading cached embeddings from {cache_path}")
        embeddings = np.load(str(cache_path))
        if len(embeddings) == len(turns):
            print(f"[EMBED] Cache valid: {embeddings.shape}")
            return embeddings
        print(f"[EMBED] Cache size mismatch ({len(embeddings)} vs {len(turns)}), re-embedding...")

    print(f"[EMBED] Embedding {len(turns)} turns via LM Studio...")
    embeddings = []
    for i, turn in enumerate(turns):
        if i % 10 == 0:
            print(f"  [{i}/{len(turns)}] {turn['speaker']} turn {turn['turn']}")
        emb = get_embedding(turn['content'])
        embeddings.append(emb)
        time.sleep(0.05)  # brief pause to avoid overwhelming LM Studio

    result = np.array(embeddings, dtype=np.float32)
    np.save(str(cache_path), result)
    print(f"[EMBED] Saved: {cache_path} — shape {result.shape}")
    return result


# --- Analysis functions ---

def load_centroids(path: Path, layer: str) -> dict[str, np.ndarray]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    # centroids_768.json has {'layer': ..., 'centroids': {...}}
    # centroids.json (Qwen 1024-dim) has {'centroids': {'18': {...}}}
    if 'centroids' in data and isinstance(data['centroids'], dict):
        raw = data['centroids']
        # If top-level values are dicts (nested by layer), navigate
        first_val = next(iter(raw.values()))
        if isinstance(first_val, dict) and all(isinstance(v, list) for v in first_val.values()):
            # Already domain→vector mapping at top level
            layer_data = raw
        else:
            layer_data = raw.get(layer, raw)
    else:
        layer_data = data
    return {domain: np.array(vec, dtype=np.float32) for domain, vec in layer_data.items()}


def classify_turn(embedding: np.ndarray, centroids: dict[str, np.ndarray]) -> tuple[str, float, dict]:
    distances = {}
    for domain, centroid in centroids.items():
        norm_emb = np.linalg.norm(embedding)
        norm_cen = np.linalg.norm(centroid)
        if norm_emb > 0 and norm_cen > 0:
            sim = float(np.dot(embedding, centroid) / (norm_emb * norm_cen))
        else:
            sim = 0.0
        distances[domain] = round(1.0 - sim, 5)
    nearest = min(distances, key=distances.get)
    return nearest, distances[nearest], distances


def detect_transitions(sequence: np.ndarray) -> tuple[list, list, float, float, float]:
    """
    Detect high-movement transitions.
    Transition at i if cosine_distance(i, i+1) > mean + 1σ.
    Returns (transition_indices, all_distances, mean, std, threshold).
    """
    distances = []
    for i in range(len(sequence) - 1):
        a, b = sequence[i], sequence[i + 1]
        sim = float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0][0])
        distances.append(round(1.0 - sim, 5))
    if not distances:
        return [], [], 0.0, 0.0, 0.0
    mean_d = float(np.mean(distances))
    std_d = float(np.std(distances))
    threshold = mean_d + std_d
    transitions = [i for i, d in enumerate(distances) if d > threshold]
    return transitions, distances, round(mean_d, 5), round(std_d, 5), round(threshold, 5)


def inter_speaker_similarity(turns: list[dict], embeddings: np.ndarray) -> list[dict]:
    """Sequential inter-speaker similarity: adjacent Opus↔Jake pairs."""
    pairs = []
    for i in range(len(turns) - 1):
        a, b = turns[i], turns[i + 1]
        if a['speaker'] != b['speaker']:
            sim = float(cosine_similarity(
                embeddings[i:i+1], embeddings[i+1:i+2]
            )[0][0])
            pairs.append({
                'position': i,
                'opus_turn': a['turn'] if a['speaker'] == 'Opus' else b['turn'],
                'jake_turn': a['turn'] if a['speaker'] == 'Jake' else b['turn'],
                'similarity': round(sim, 5),
            })
    return pairs


def off_map_detection(turns: list[dict], embeddings: np.ndarray,
                      centroids: dict[str, np.ndarray],
                      evolution_embeddings: np.ndarray) -> dict:
    centroid_matrix = np.array(list(centroids.values()), dtype=np.float32)
    centroid_names = list(centroids.keys())

    min_distances = []
    for emb in embeddings:
        sims = cosine_similarity(emb.reshape(1, -1), centroid_matrix)[0]
        dists = 1.0 - sims
        min_distances.append(float(np.min(dists)))

    mean_dist = float(np.mean(min_distances))
    std_dist = float(np.std(min_distances))
    threshold = mean_dist + std_dist

    off_map = []
    for i, (turn, dist) in enumerate(zip(turns, min_distances)):
        if dist > threshold:
            sims_to_evo = cosine_similarity(embeddings[i:i+1], evolution_embeddings)[0]
            nn_idx = int(np.argmax(sims_to_evo))
            off_map.append({
                'turn': turn['turn'],
                'speaker': turn['speaker'],
                'timestamp': turn.get('timestamp'),
                'min_centroid_distance': round(dist, 5),
                'nearest_evo_idx': nn_idx,
                'nearest_evo_sim': round(float(sims_to_evo[nn_idx]), 5),
            })

    return {
        'threshold': round(threshold, 5),
        'mean_min_distance': round(mean_dist, 5),
        'std_min_distance': round(std_dist, 5),
        'off_map_count': len(off_map),
        'off_map_turns': off_map,
        'all_min_distances': [round(d, 5) for d in min_distances],
    }


def build_joint_umap(turn_embeddings: np.ndarray,
                     evolution_embeddings: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    all_embs = np.vstack([evolution_embeddings, turn_embeddings])
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42, n_components=2)
    print(f"[UMAP] Fitting on {all_embs.shape[0]} points ({len(evolution_embeddings)} evo + {len(turn_embeddings)} turns)...")
    all_coords = reducer.fit_transform(all_embs)
    n_evo = len(evolution_embeddings)
    return all_coords[n_evo:], all_coords


# --- Main ---

def main():
    print("[CHATLOG] Loading data...")
    with open(TURNS_PATH, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"[CHATLOG] {len(turns)} turns")

    evolution_embeddings = np.load(str(EVOLUTION_EMB_PATH))
    print(f"[CHATLOG] Evolution embeddings: {evolution_embeddings.shape}")

    with open(GEOMETRY_PATH, encoding='utf-8') as f:
        geometry = json.load(f)

    # Embed turns (cached)
    turn_embeddings = embed_turns(turns, TURN_EMB_PATH)

    # Centroids
    centroids = load_centroids(CENTROIDS_PATH, CENTROID_LAYER)
    print(f"[CHATLOG] Centroids: {list(centroids.keys())}")

    opus_indices = [i for i, t in enumerate(turns) if t['speaker'] == 'Opus']
    jake_indices = [i for i, t in enumerate(turns) if t['speaker'] == 'Jake']

    # --- Register classification ---
    print("[CHATLOG] Classifying turns...")
    classifications = []
    for i, turn in enumerate(turns):
        domain, min_dist, all_dists = classify_turn(turn_embeddings[i], centroids)
        classifications.append({
            'turn': turn['turn'],
            'speaker': turn['speaker'],
            'domain': domain,
            'min_distance': round(min_dist, 5),
            'all_distances': {k: round(v, 5) for k, v in all_dists.items()},
        })

    opus_domains = Counter(classifications[i]['domain'] for i in opus_indices)
    jake_domains = Counter(classifications[i]['domain'] for i in jake_indices)

    # --- Inter-speaker similarity ---
    print("[CHATLOG] Computing inter-speaker similarity...")
    sequential_pairs = inter_speaker_similarity(turns, turn_embeddings)
    if sequential_pairs:
        max_pair = max(sequential_pairs, key=lambda x: x['similarity'])
        min_pair = min(sequential_pairs, key=lambda x: x['similarity'])
        mean_sim = round(float(np.mean([p['similarity'] for p in sequential_pairs])), 5)
    else:
        max_pair = min_pair = None
        mean_sim = None

    # --- Transitions ---
    print("[CHATLOG] Detecting transitions...")
    transitions, all_dists, mean_d, std_d, thresh_d = detect_transitions(turn_embeddings)
    opus_trans, _, opus_mean, opus_std, opus_thresh = detect_transitions(turn_embeddings[opus_indices])
    jake_trans, _, jake_mean, jake_std, jake_thresh = detect_transitions(turn_embeddings[jake_indices])

    # Map transition indices to actual turn numbers for context
    transition_turns = []
    for idx in transitions:
        transition_turns.append({
            'between_turns': [turns[idx]['turn'], turns[idx+1]['turn']],
            'speakers': [turns[idx]['speaker'], turns[idx+1]['speaker']],
            'domain_before': classifications[idx]['domain'],
            'domain_after': classifications[idx+1]['domain'],
            'distance': all_dists[idx],
        })

    # --- Off-map ---
    print("[CHATLOG] Off-map detection...")
    off_map = off_map_detection(turns, turn_embeddings, centroids, evolution_embeddings)

    # --- UMAP ---
    print("[CHATLOG] UMAP projection...")
    turn_coords, joint_coords = build_joint_umap(turn_embeddings, evolution_embeddings)

    # --- Comparison with existing action-title trajectory ---
    existing_traj_turns = geometry.get('wallas_classified_turns', [])
    comparison = None
    if existing_traj_turns:
        existing_domains_counter = Counter(t.get('wallas_stage', 'unknown') for t in existing_traj_turns)
        chatlog_domains_counter = Counter(c['domain'] for c in classifications)
        comparison = {
            'note': (
                'Existing trajectory uses Wallas-stage classification on 923 action titles. '
                'Chatlog uses 5-domain centroid classification on 153 full turns. '
                'Not directly comparable, but domain overlap is informative.'
            ),
            'existing_wallas_distribution': dict(existing_domains_counter),
            'chatlog_domain_distribution': dict(chatlog_domains_counter),
            'chatlog_opus_domains': dict(opus_domains),
            'chatlog_jake_domains': dict(jake_domains),
        }

    # --- Assemble output ---
    print("[CHATLOG] Writing output...")
    output = {
        'metadata': {
            'source': 'When_I_Saw_Opus.docx',
            'total_turns': len(turns),
            'opus_turns': len(opus_indices),
            'jake_turns': len(jake_indices),
            'content_mixed_note': (
                'Turns 3, ~93, ~112 may contain content mixing: first Jake turn in each '
                'consecutive Jake:Jake annotation pair contains both Jake and Opus content. '
                'These affect 3 out of 76 Jake turns.'
            ),
            'centroid_layer': CENTROID_LAYER,
        },
        'turn_sequence': [
            {
                'turn': turns[i]['turn'],
                'speaker': turns[i]['speaker'],
                'timestamp': turns[i].get('timestamp'),
                'word_count': turns[i]['word_count'],
                'umap_x': round(float(turn_coords[i][0]), 4),
                'umap_y': round(float(turn_coords[i][1]), 4),
                'domain': classifications[i]['domain'],
                'min_centroid_distance': classifications[i]['min_distance'],
            }
            for i in range(len(turns))
        ],
        'register_classification': {
            'per_turn': classifications,
            'opus_distribution': dict(opus_domains),
            'jake_distribution': dict(jake_domains),
            'combined_distribution': dict(Counter(c['domain'] for c in classifications)),
        },
        'inter_speaker_similarity': {
            'sequential_pairs': sequential_pairs,
            'max_similarity': {
                'value': max_pair['similarity'],
                'position': max_pair['position'],
                'opus_turn': max_pair['opus_turn'],
                'jake_turn': max_pair['jake_turn'],
            } if max_pair else None,
            'min_similarity': {
                'value': min_pair['similarity'],
                'position': min_pair['position'],
                'opus_turn': min_pair['opus_turn'],
                'jake_turn': min_pair['jake_turn'],
            } if min_pair else None,
            'mean_similarity': mean_sim,
        },
        'transitions': {
            'all_turns': {
                'transition_details': transition_turns,
                'transition_count': len(transitions),
                'mean_distance': mean_d,
                'std_distance': std_d,
                'threshold': thresh_d,
                'all_distances': all_dists,
            },
            'opus_only': {
                'transition_count': len(opus_trans),
                'transition_at_opus_indices': opus_trans,
                'mean_distance': opus_mean,
                'std_distance': opus_std,
                'threshold': opus_thresh,
            },
            'jake_only': {
                'transition_count': len(jake_trans),
                'transition_at_jake_indices': jake_trans,
                'mean_distance': jake_mean,
                'std_distance': jake_std,
                'threshold': jake_thresh,
            },
        },
        'off_map': off_map,
        'umap': {
            'note': (
                'Fit on evolution (46) + turns (153). Not directly comparable to corpus_map.json '
                'coordinates. Use 768-dim cosine similarity for quantitative analysis.'
            ),
            'opus_trajectory': [
                {'turn': turns[idx]['turn'], 'x': round(float(turn_coords[idx][0]), 4),
                 'y': round(float(turn_coords[idx][1]), 4),
                 'timestamp': turns[idx].get('timestamp')}
                for idx in opus_indices
            ],
            'jake_trajectory': [
                {'turn': turns[idx]['turn'], 'x': round(float(turn_coords[idx][0]), 4),
                 'y': round(float(turn_coords[idx][1]), 4)}
                for idx in jake_indices
            ],
        },
        'trajectory_comparison': comparison,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[CHATLOG] Output: {OUTPUT_PATH}")

    # Summary
    print("\n=== KEY FINDINGS ===")
    print(f"Turns: {len(turns)} ({len(opus_indices)} Opus, {len(jake_indices)} Jake)")
    print(f"\nOpus domain distribution:")
    for d, c in sorted(opus_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} ({100*c/len(opus_indices):.0f}%)")
    print(f"\nJake domain distribution:")
    for d, c in sorted(jake_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} ({100*c/len(jake_indices):.0f}%)")
    if max_pair:
        print(f"\nInter-speaker similarity: mean={mean_sim:.4f}")
        print(f"  Max: {max_pair['similarity']:.4f} at position {max_pair['position']} (Opus {max_pair['opus_turn']}, Jake {max_pair['jake_turn']})")
        print(f"  Min: {min_pair['similarity']:.4f} at position {min_pair['position']}")
    print(f"\nTransitions (full sequence): {len(transitions)}")
    for td in transition_turns[:8]:
        print(f"  Between turns {td['between_turns']}: {td['domain_before']} -> {td['domain_after']} (d={td['distance']:.4f})")
    print(f"\nOff-map turns: {off_map['off_map_count']} (threshold: {off_map['threshold']:.4f})")
    if off_map['off_map_turns']:
        for t in off_map['off_map_turns']:
            ts = f" [{t['timestamp']}]" if t['timestamp'] else ''
            print(f"  Turn {t['turn']} ({t['speaker']}){ts}: dist={t['min_centroid_distance']:.4f}")


if __name__ == '__main__':
    main()
