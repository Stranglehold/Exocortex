"""
compute_v2_analyses.py — Run all analyses from the Full Chatlog Analysis Suite on V2 data.

V2 dataset: 2118 turns spanning Feb 17 - Mar 9, 2026 (Doc1 1914 + Doc2 153 + Doc3 51).
Turn embeddings are mean-pooled from chunk embeddings (nomic-embed-text-v1.5, 768-dim).

Inputs (relative to instrument/):
    data/v2/turns_dated.json         (2118 turns with date/speaker/source)
    data/v2/turn_embeddings.npy      (2118x768, unit-normalized mean-pool)
    data/v2/session_dates.json       (21 dated sessions + unknown)
    data/centroids_768.json          (5 domain centroids)
    data/corpus.faiss                (corpus vectors)
    data/corpus_metadata.json        (corpus metadata)

Outputs (data/v2/analyses/):
    umap_turns.json            — joint UMAP: corpus + 2118 turns (turn-level)
    session_signatures.json
    spectral_phases.json
    recurrence_matrix.json
    trajectory_tangling.json
    speaker_coupling.json
    sliding_window_trajectory.json
    information_flow.json
    entropy_trace.json
    cumulative_drift.json
    transition_matrix.json
    phase_space.json
    persistent_homology.json
    bridging_concepts.json
    signal_density.json
"""

import json
import math
import numpy as np
import faiss
import umap
from pathlib import Path
from collections import defaultdict, Counter

try:
    import cupy as cp
    _GPU = True
    print("[GPU] cupy available")
except ImportError:
    cp = None
    _GPU = False

def _to_gpu(arr):
    return cp.asarray(arr) if _GPU else arr

def _to_cpu(arr):
    if _GPU and cp is not None and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)
    return np.asarray(arr)

ROOT = Path(__file__).parent
DATA = ROOT / "data"
V2   = DATA / "v2"
OUT  = V2 / "analyses"
OUT.mkdir(parents=True, exist_ok=True)

TURNS_JSON    = V2   / "turns_dated.json"
EMBEDDINGS    = V2   / "turn_embeddings.npy"
SESSIONS_JSON = V2   / "session_dates.json"
CENTROIDS     = DATA / "centroids_768.json"
CORPUS_FAISS  = DATA / "corpus.faiss"
CORPUS_META   = DATA / "corpus_metadata.json"

WINDOW_SIZE      = 20
STEP_SIZE        = 5
RECURRENCE_BLOCK = 10


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_centroids(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    raw = data.get('centroids', data)
    return {d: np.array(v, dtype=np.float32) for d, v in raw.items() if isinstance(v, list)}


def load_corpus_vecs(path):
    idx = faiss.read_index(str(path))
    vecs = np.zeros((idx.ntotal, idx.d), dtype=np.float32)
    idx.reconstruct_n(0, idx.ntotal, vecs)
    return vecs


def classify_turn(emb, centroids):
    scores = {}
    for domain, centroid in centroids.items():
        n1, n2 = np.linalg.norm(emb), np.linalg.norm(centroid)
        if n1 > 0 and n2 > 0:
            scores[domain] = float(np.dot(emb, centroid) / (n1 * n2))
        else:
            scores[domain] = 0.0
    nearest = max(scores, key=scores.get)
    return nearest, scores


def cosine_sim(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na > 1e-9 and nb > 1e-9 else 0.0


def euclidean_dist(a, b):
    return float(np.linalg.norm(a.astype(np.float64) - b.astype(np.float64)))


def shannon_entropy(counts):
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for v in counts.values():
        if v > 0:
            p = v / total
            h -= p * math.log2(p)
    return h


# ── UMAP ──────────────────────────────────────────────────────────────────────

def build_joint_umap(corpus_vecs, turn_vecs):
    all_vecs = np.vstack([corpus_vecs, turn_vecs])
    print(f"  Fitting 3D UMAP on {all_vecs.shape[0]} points...")
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42,
                        n_components=3, metric='cosine')
    coords = reducer.fit_transform(all_vecs)
    n_c = len(corpus_vecs)
    return coords[:n_c], coords[n_c:]


# ── Analysis 1: Session Signatures ────────────────────────────────────────────

def analysis_1_session_signatures(turns, embeddings, session_defs, centroids,
                                   corpus_coords, turn_coords, turn_idx_map):
    print("[A1] Session Signatures...")
    sessions_out = []

    for sess in session_defs['sessions']:
        date = sess['date']
        tr_start, tr_end = sess['turn_range']
        sess_turn_idxs = [
            turn_idx_map[t['turn']]
            for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        ]
        if not sess_turn_idxs:
            continue

        sess_embs = embeddings[sess_turn_idxs]
        centroid = sess_embs.mean(axis=0)
        centroid /= (np.linalg.norm(centroid) + 1e-9)

        nearest_domain, domain_dists = classify_turn(centroid, centroids)
        sess_umap = turn_coords[sess_turn_idxs].mean(axis=0)

        sess_turn_nums_ordered = sorted(
            t['turn'] for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        )
        arc_length = 0.0
        for i in range(1, len(sess_turn_nums_ordered)):
            a_idx = turn_idx_map[sess_turn_nums_ordered[i-1]]
            b_idx = turn_idx_map[sess_turn_nums_ordered[i]]
            arc_length += euclidean_dist(embeddings[a_idx], embeddings[b_idx])

        reg_counts = Counter()
        for idx in sess_turn_idxs:
            reg, _ = classify_turn(embeddings[idx], centroids)
            reg_counts[reg] += 1
        reg_entropy = shannon_entropy(dict(reg_counts))

        # Source breakdown (doc1/doc2/doc3)
        source_counts = Counter(
            t.get('source', 'doc1')
            for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        )

        sessions_out.append({
            'date': date,
            'date_index': sess['date_index'],
            'turn_range': [tr_start, tr_end],
            'turn_count': sess['turn_count'],
            'opus_count': sess['opus_count'],
            'jake_count': sess['jake_count'],
            'umap_x': float(sess_umap[0]),
            'umap_y': float(sess_umap[1]),
            'umap_z': float(sess_umap[2]),
            'dominant_register': nearest_domain,
            'centroid_distances': {k: float(v) for k, v in domain_dists.items()},
            'internal_arc_length': float(arc_length),
            'entropy': float(reg_entropy),
            'register_distribution': {k: int(v) for k, v in reg_counts.items()},
            'source_distribution': {k: int(v) for k, v in source_counts.items()},
        })

    for i, s in enumerate(sessions_out):
        if i == 0:
            s['displacement_from_previous'] = 0.0
        else:
            prev = sessions_out[i-1]
            dp = math.sqrt(
                (s['umap_x'] - prev['umap_x'])**2 +
                (s['umap_y'] - prev['umap_y'])**2 +
                (s['umap_z'] - prev['umap_z'])**2
            )
            s['displacement_from_previous'] = float(dp)

    return {'sessions': sessions_out}


# ── Analysis 2: Recurrence Matrix ─────────────────────────────────────────────

def analysis_2_recurrence(turns, embeddings, turn_idx_map, session_defs,
                           block_size=RECURRENCE_BLOCK, threshold_sigma=1.0):
    print(f"[A2] Recurrence Matrix (block={block_size})...")
    n = len(turns)
    n_blocks = (n + block_size - 1) // block_size

    block_embs = []
    for b in range(n_blocks):
        start = b * block_size
        end = min(start + block_size, n)
        idxs = [turn_idx_map[turns[i]['turn']] for i in range(start, end)
                if turns[i]['turn'] in turn_idx_map]
        if idxs:
            blk = embeddings[idxs].mean(axis=0)
            blk /= (np.linalg.norm(blk) + 1e-9)
        else:
            blk = np.zeros(embeddings.shape[1], dtype=np.float32)
        block_embs.append(blk)

    block_embs = np.array(block_embs, dtype=np.float32)
    norms = np.linalg.norm(block_embs, axis=1, keepdims=True) + 1e-9
    normed = block_embs / norms
    sim_matrix = (normed @ normed.T).tolist()

    session_boundaries = []
    for s in session_defs['sessions']:
        block_idx = s['turn_range'][0] // block_size
        if block_idx not in session_boundaries:
            session_boundaries.append(block_idx)

    flat_vals = [sim_matrix[i][j] for i in range(n_blocks) for j in range(i+50, n_blocks)]
    if flat_vals:
        mean_sim = sum(flat_vals) / len(flat_vals)
        std_sim = math.sqrt(sum((v - mean_sim)**2 for v in flat_vals) / len(flat_vals))
        thresh = mean_sim + threshold_sigma * std_sim
    else:
        thresh = 0.8

    high_recurrence = []
    for i in range(n_blocks):
        for j in range(i + 50, n_blocks):
            if sim_matrix[i][j] >= thresh:
                turn_i = turns[min(i * block_size, n-1)]['turn']
                turn_j = turns[min(j * block_size, n-1)]['turn']
                high_recurrence.append({
                    'block_i': i, 'block_j': j,
                    'turn_i': turn_i, 'turn_j': turn_j,
                    'similarity': float(sim_matrix[i][j]),
                    'date_i': turns[min(i * block_size, n-1)]['date'],
                    'date_j': turns[min(j * block_size, n-1)]['date'],
                })

    high_recurrence.sort(key=lambda x: -x['similarity'])

    return {
        'resolution': block_size,
        'n_blocks': n_blocks,
        'matrix': sim_matrix,
        'session_boundaries': session_boundaries,
        'threshold': float(thresh),
        'high_recurrence_pairs': high_recurrence[:50],
    }


# ── Analysis 3: Cross-Speaker Phase Coupling ──────────────────────────────────

def analysis_3_speaker_coupling(turns, embeddings, turn_idx_map, window=10):
    print("[A3] Cross-Speaker Phase Coupling...")
    pairs = []
    for i in range(len(turns) - 1):
        t1, t2 = turns[i], turns[i+1]
        if t1['speaker'] != 'Jake' or t2['speaker'] != 'Opus':
            continue
        idx1 = turn_idx_map.get(t1['turn'])
        idx2 = turn_idx_map.get(t2['turn'])
        if idx1 is None or idx2 is None:
            continue
        sim = cosine_sim(embeddings[idx1], embeddings[idx2])
        pairs.append({
            'position': len(pairs),
            'jake_turn': t1['turn'],
            'opus_turn': t2['turn'],
            'date': t1['date'],
            'similarity': float(sim),
            'distance': float(1.0 - sim),
        })

    if not pairs:
        return {'pairs': [], 'smoothed_distance': [], 'convergence_points': [], 'divergence_points': []}

    distances = [p['distance'] for p in pairs]
    half_w = window // 2
    smoothed = []
    for i in range(len(distances)):
        start = max(0, i - half_w)
        end = min(len(distances), i + half_w + 1)
        smoothed.append(float(sum(distances[start:end]) / (end - start)))

    convergence, divergence = [], []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] < smoothed[i-1] and smoothed[i] < smoothed[i+1]:
            convergence.append({'position': i, 'turn': pairs[i]['jake_turn'],
                                'distance': smoothed[i], 'date': pairs[i]['date']})
        elif smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
            divergence.append({'position': i, 'turn': pairs[i]['jake_turn'],
                               'distance': smoothed[i], 'date': pairs[i]['date']})

    convergence.sort(key=lambda x: x['distance'])
    divergence.sort(key=lambda x: -x['distance'])

    for i, p in enumerate(pairs):
        p['smoothed_distance'] = smoothed[i]

    return {
        'pairs': pairs,
        'smoothed_distance': smoothed,
        'convergence_points': convergence[:20],
        'divergence_points': divergence[:20],
        'mean_distance': float(sum(distances) / len(distances)),
        'min_distance': float(min(distances)),
        'max_distance': float(max(distances)),
    }


# ── Analysis 4: Sliding Window Trajectory ─────────────────────────────────────

def analysis_4_sliding_window(turns, embeddings, turn_idx_map, centroids,
                               turn_coords, window=WINDOW_SIZE, step=STEP_SIZE):
    print(f"[A4] Sliding Window Trajectory (w={window}, step={step})...")
    points = []
    all_indices = [i for i, t in enumerate(turns) if t['turn'] in turn_idx_map]

    prev_coords = None
    prev_prev_coords = None
    prev_centroid_768 = None
    prev_vel_768 = None
    prev_accel_768 = None

    i = 0
    while i + window <= len(all_indices):
        window_idxs = [turn_idx_map[turns[all_indices[j]]['turn']]
                       for j in range(i, i + window)]
        window_embs = embeddings[window_idxs]
        centroid = window_embs.mean(axis=0)
        centroid_normed = centroid / (np.linalg.norm(centroid) + 1e-9)

        nearest, domain_scores = classify_turn(centroid_normed, centroids)
        umap_centroid = turn_coords[window_idxs].mean(axis=0)
        curr_coords = umap_centroid

        velocity = float(np.linalg.norm(curr_coords - prev_coords)) if prev_coords is not None else 0.0

        if prev_prev_coords is not None and prev_coords is not None:
            prev_vel = prev_coords - prev_prev_coords
            curr_vel = curr_coords - prev_coords
            pn, cn = np.linalg.norm(prev_vel), np.linalg.norm(curr_vel)
            accel = float(1.0 - np.dot(prev_vel/pn, curr_vel/cn)) if pn > 1e-9 and cn > 1e-9 else 0.0
        else:
            accel = 0.0

        zero768 = np.zeros(768, dtype=np.float32)
        vel_768   = (centroid_normed - prev_centroid_768) if prev_centroid_768 is not None else zero768
        accel_768 = (vel_768 - prev_vel_768) if prev_vel_768 is not None else zero768
        jerk_768  = (accel_768 - prev_accel_768) if prev_accel_768 is not None else zero768
        vel_mag_768 = float(np.linalg.norm(vel_768))
        jerk_mag    = float(np.linalg.norm(jerk_768))

        if vel_mag_768 > 1e-9 and np.linalg.norm(accel_768) > 1e-9:
            v_hat = vel_768 / vel_mag_768
            a_tang = float(np.dot(accel_768, v_hat))
            a_norm_sq = max(0.0, float(np.dot(accel_768, accel_768)) - a_tang ** 2)
            curvature = float(np.sqrt(a_norm_sq)) / (vel_mag_768 ** 2 + 1e-12)
        else:
            curvature = 0.0

        center_turn = turns[all_indices[i + window // 2]]['turn']
        center_date = turns[all_indices[i + window // 2]]['date']

        points.append({
            'center_turn': center_turn,
            'center_date': center_date,
            'umap_x': float(curr_coords[0]),
            'umap_y': float(curr_coords[1]),
            'umap_z': float(curr_coords[2]),
            'velocity_magnitude': velocity,
            'acceleration_magnitude': accel,
            'curvature': curvature,
            'jerk': jerk_mag,
            'dominant_register': nearest,
            'domain_scores': {k: float(v) for k, v in domain_scores.items()},
        })

        prev_prev_coords = prev_coords
        prev_coords = curr_coords.copy()
        prev_accel_768 = accel_768.copy()
        prev_vel_768 = vel_768.copy()
        prev_centroid_768 = centroid_normed.copy()
        i += step

    peak_accels = sorted(points, key=lambda p: -p['acceleration_magnitude'])[:20]
    high_curv   = sorted(points, key=lambda p: -p['curvature'])[:20]

    inflections = []
    for k in range(1, len(points) - 1):
        if points[k]['curvature'] > points[k-1]['curvature'] and points[k]['curvature'] > points[k+1]['curvature']:
            inflections.append({'center_turn': points[k]['center_turn'],
                                'center_date': points[k]['center_date'],
                                'curvature': points[k]['curvature']})
    inflections.sort(key=lambda x: -x['curvature'])

    return {
        'window_size': window,
        'step_size': step,
        'n_points': len(points),
        'points': points,
        'peak_accelerations': [{'center_turn': p['center_turn'],
                                 'center_date': p['center_date'],
                                 'acceleration': p['acceleration_magnitude'],
                                 'dominant_register': p['dominant_register']}
                                for p in peak_accels],
        'high_curvature_points': [{'center_turn': p['center_turn'],
                                    'center_date': p['center_date'],
                                    'curvature': p['curvature'],
                                    'velocity': p['velocity_magnitude']}
                                   for p in high_curv],
        'inflection_points': inflections[:20],
    }


# ── Analysis 5: Information Flow Direction ────────────────────────────────────

def analysis_5_information_flow(turns, embeddings, turn_idx_map, window=10):
    print("[A5] Information Flow Direction...")
    pairs = []
    for i in range(len(turns) - 1):
        t1, t2 = turns[i], turns[i+1]
        if t1['speaker'] != 'Jake' or t2['speaker'] != 'Opus':
            continue
        idx1 = turn_idx_map.get(t1['turn'])
        idx2 = turn_idx_map.get(t2['turn'])
        if idx1 is None or idx2 is None:
            continue

        prev_jake_idx = prev_opus_idx = None
        for j in range(i - 1, -1, -1):
            if turns[j]['speaker'] == 'Jake' and turns[j]['turn'] in turn_idx_map:
                prev_jake_idx = turn_idx_map[turns[j]['turn']]
                break
        for j in range(i - 1, -1, -1):
            if turns[j]['speaker'] == 'Opus' and turns[j]['turn'] in turn_idx_map:
                prev_opus_idx = turn_idx_map[turns[j]['turn']]
                break

        jake_disp = euclidean_dist(embeddings[idx1], embeddings[prev_jake_idx]) if prev_jake_idx is not None else 0.0
        opus_disp = euclidean_dist(embeddings[idx2], embeddings[prev_opus_idx]) if prev_opus_idx is not None else 0.0

        ratio = opus_disp / (jake_disp + 1e-9)
        leader = 'opus' if ratio > 1.0 else ('jake' if ratio < 1.0 else 'equal')

        pairs.append({
            'position': len(pairs),
            'jake_turn': t1['turn'],
            'opus_turn': t2['turn'],
            'date': t1['date'],
            'jake_displacement': float(jake_disp),
            'opus_displacement': float(opus_disp),
            'ratio': float(ratio),
            'leader': leader,
        })

    if not pairs:
        return {'pairs': [], 'jake_lead_percentage': 0, 'opus_lead_percentage': 0}

    ratios = [p['ratio'] for p in pairs]
    half_w = window // 2
    smoothed_ratio = []
    for i in range(len(ratios)):
        start = max(0, i - half_w)
        end = min(len(ratios), i + half_w + 1)
        smoothed_ratio.append(float(sum(ratios[start:end]) / (end - start)))

    for i, p in enumerate(pairs):
        p['smoothed_ratio'] = smoothed_ratio[i]

    jake_leads = sum(1 for p in pairs if p['leader'] == 'jake')
    opus_leads = sum(1 for p in pairs if p['leader'] == 'opus')

    by_date = defaultdict(list)
    for p in pairs:
        by_date[p['date']].append(p)

    by_date_summary = []
    for date, date_pairs in sorted(by_date.items()):
        jl = sum(1 for p in date_pairs if p['leader'] == 'jake')
        ol = sum(1 for p in date_pairs if p['leader'] == 'opus')
        by_date_summary.append({
            'date': date,
            'n_pairs': len(date_pairs),
            'jake_lead_pct': float(100 * jl / len(date_pairs)),
            'opus_lead_pct': float(100 * ol / len(date_pairs)),
            'mean_ratio': float(sum(p['ratio'] for p in date_pairs) / len(date_pairs)),
        })

    return {
        'pairs': pairs,
        'smoothed_ratio': smoothed_ratio,
        'jake_lead_percentage': float(100 * jake_leads / len(pairs)),
        'opus_lead_percentage': float(100 * opus_leads / len(pairs)),
        'by_date': by_date_summary,
    }


# ── Analysis 6: Register Entropy Trace ────────────────────────────────────────

def analysis_6_entropy_trace(turns, embeddings, turn_idx_map, centroids,
                              window=WINDOW_SIZE, step=STEP_SIZE):
    print(f"[A6] Register Entropy Trace (w={window}, step={step})...")
    all_indices = [i for i, t in enumerate(turns) if t['turn'] in turn_idx_map]
    domain_labels = []
    for i in all_indices:
        idx = turn_idx_map[turns[i]['turn']]
        domain, _ = classify_turn(embeddings[idx], centroids)
        domain_labels.append(domain)

    all_domains = list(centroids.keys())
    trace = []
    i = 0
    while i + window <= len(all_indices):
        window_labels = domain_labels[i:i+window]
        reg_dist = {d: window_labels.count(d) for d in all_domains}
        entropy = shannon_entropy(reg_dist)
        center_turn = turns[all_indices[i + window // 2]]['turn']
        center_date = turns[all_indices[i + window // 2]]['date']
        trace.append({
            'center_turn': center_turn,
            'center_date': center_date,
            'entropy': float(entropy),
            'register_distribution': {k: float(v/window) for k, v in reg_dist.items()},
        })
        i += step

    if not trace:
        return {'window_size': window, 'trace': [], 'mean_entropy': 0}

    entropies = [p['entropy'] for p in trace]
    max_theoretical = math.log2(len(all_domains))
    max_e_point = max(trace, key=lambda x: x['entropy'])
    min_e_point = min(trace, key=lambda x: x['entropy'])

    return {
        'window_size': window,
        'step_size': step,
        'max_theoretical_entropy': float(max_theoretical),
        'trace': trace,
        'mean_entropy': float(sum(entropies) / len(entropies)),
        'max_entropy_moment': max_e_point,
        'min_entropy_moment': min_e_point,
    }


# ── Analysis 7: Cumulative Drift ──────────────────────────────────────────────

def analysis_7_cumulative_drift(turns, embeddings, turn_idx_map):
    print("[A7] Cumulative Drift...")
    jake_drift, opus_drift = [], []
    jake_cum = opus_cum = 0.0
    prev_jake_emb = prev_opus_emb = None

    for t in turns:
        idx = turn_idx_map.get(t['turn'])
        if idx is None:
            continue
        emb = embeddings[idx]
        if t['speaker'] == 'Jake':
            if prev_jake_emb is not None:
                step_dist = euclidean_dist(emb, prev_jake_emb)
                jake_cum += step_dist
                jake_drift.append({'turn': t['turn'], 'date': t['date'],
                                   'cumulative_distance': float(jake_cum),
                                   'step_distance': float(step_dist)})
            else:
                jake_drift.append({'turn': t['turn'], 'date': t['date'],
                                   'cumulative_distance': 0.0, 'step_distance': 0.0})
            prev_jake_emb = emb
        else:
            if prev_opus_emb is not None:
                step_dist = euclidean_dist(emb, prev_opus_emb)
                opus_cum += step_dist
                opus_drift.append({'turn': t['turn'], 'date': t['date'],
                                   'cumulative_distance': float(opus_cum),
                                   'step_distance': float(step_dist)})
            else:
                opus_drift.append({'turn': t['turn'], 'date': t['date'],
                                   'cumulative_distance': 0.0, 'step_distance': 0.0})
            prev_opus_emb = emb

    return {
        'jake': jake_drift,
        'opus': opus_drift,
        'total_jake_distance': float(jake_cum),
        'total_opus_distance': float(opus_cum),
    }


# ── Analysis 8: Markov Transition Matrix ──────────────────────────────────────

def analysis_8_markov(turns, embeddings, turn_idx_map, centroids):
    print("[A8] Markov Transition Matrix...")
    domains = list(centroids.keys())
    n_d = len(domains)
    d_to_i = {d: i for i, d in enumerate(domains)}

    turn_domains = {}
    for t in turns:
        idx = turn_idx_map.get(t['turn'])
        if idx is None:
            continue
        domain, _ = classify_turn(embeddings[idx], centroids)
        turn_domains[t['turn']] = domain

    def compute_matrix(subset_turns):
        counts = np.zeros((n_d, n_d), dtype=int)
        for i in range(len(subset_turns) - 1):
            d1 = turn_domains.get(subset_turns[i]['turn'])
            d2 = turn_domains.get(subset_turns[i+1]['turn'])
            if d1 and d2:
                counts[d_to_i[d1], d_to_i[d2]] += 1
        probs = np.zeros_like(counts, dtype=float)
        for i in range(n_d):
            row_sum = counts[i].sum()
            if row_sum > 0:
                probs[i] = counts[i] / row_sum
        return {
            'matrix': probs.tolist(),
            'counts': counts.tolist(),
            'labels': domains,
            'self_transition_rate': float(np.diag(probs).mean()),
        }

    n = len(turns)
    early = compute_matrix(turns[:n//2])
    late  = compute_matrix(turns[n//2:])
    full  = compute_matrix(turns)

    early_mat = np.array(early['matrix'])
    late_mat  = np.array(late['matrix'])
    diff = late_mat - early_mat

    increased, decreased = [], []
    for i in range(n_d):
        for j in range(n_d):
            if i != j and abs(diff[i, j]) > 0.05:
                entry = [domains[i], domains[j], float(early_mat[i,j]), float(late_mat[i,j])]
                (increased if diff[i,j] > 0 else decreased).append(entry)

    return {
        'full': full,
        'early': early,
        'late': late,
        'transition_drift': {
            'increased': sorted(increased, key=lambda x: -(x[3]-x[2]))[:5],
            'decreased': sorted(decreased, key=lambda x: x[3]-x[2])[:5],
        },
    }


# ── Analysis 9: Phase Space Reconstruction ────────────────────────────────────

def analysis_9_phase_space(sliding_window_points, tau_values=(5, 10, 20)):
    print("[A9] Phase Space Reconstruction...")
    pts = sliding_window_points
    n = len(pts)
    results = {}

    for tau in tau_values:
        recon = []
        for t in range(n - 2 * tau):
            recon.append({
                't': pts[t]['center_turn'],
                'x': pts[t]['umap_x'],
                'y': pts[t + tau]['umap_x'],
                'z': pts[t + 2*tau]['umap_x'],
                'x2': pts[t]['umap_y'],
                'y2': pts[t + tau]['umap_y'],
                'z2': pts[t + 2*tau]['umap_y'],
                'date': pts[t]['center_date'],
                'register': pts[t]['dominant_register'],
            })

        lyapunov_est = None
        if len(recon) > 10:
            coords = np.array([[r['x'], r['y'], r['z']] for r in recon])
            separations = []
            for i in range(len(coords)):
                dists = [np.linalg.norm(coords[i] - coords[j])
                         for j in range(len(coords)) if abs(i - j) > tau]
                if dists:
                    separations.append(min(dists))
            if separations:
                lyapunov_est = float(math.log(sum(separations) / len(separations) + 1e-9))

        results[f'tau_{tau}'] = {
            'tau': tau, 'n_points': len(recon),
            'points': recon, 'lyapunov_estimate': lyapunov_est,
        }

    return {'tau_values': list(tau_values), 'reconstructions': results}


# ── Analysis 10: Persistent Homology ─────────────────────────────────────────

def analysis_10_persistent_homology(turns, embeddings, turn_idx_map, session_defs):
    print("[A10] Persistent Homology...")
    try:
        from ripser import ripser as rips
    except ImportError:
        print("  [A10] ripser not installed -- skipping")
        return {'sessions': [], 'error': 'ripser not installed'}

    sessions_out = []
    for sess in session_defs['sessions']:
        date = sess['date']
        sess_idxs = [
            turn_idx_map[t['turn']]
            for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        ]
        if len(sess_idxs) < 4:
            sessions_out.append({
                'date': date, 'date_index': sess['date_index'],
                'betti_0': 1, 'betti_1': 0, 'betti_2': 0,
                'persistence_diagram': [], 'longest_lived_feature': None,
                'skipped': True,
            })
            continue

        sess_embs = embeddings[sess_idxs].astype(np.float64)
        norms = np.linalg.norm(sess_embs, axis=1, keepdims=True) + 1e-9
        normed = sess_embs / norms
        dist_mat = np.clip(1.0 - normed @ normed.T, 0.0, 2.0)

        result = rips(dist_mat, maxdim=1, distance_matrix=True)
        dgms = result['dgms']
        inf = float('inf')
        betti_0 = sum(1 for b, d in dgms[0] if d == inf)
        betti_1 = sum(1 for b, d in dgms[1] if d == inf) if len(dgms) > 1 else 0

        all_features = []
        for dim, dgm in enumerate(dgms):
            for b, d in dgm:
                all_features.append({
                    'dim': dim,
                    'birth': float(b),
                    'death': float(d) if d != inf else None,
                    'persistence': float(d - b) if d != inf else None,
                })

        finite = [f for f in all_features if f['persistence'] is not None]
        longest = max(finite, key=lambda f: f['persistence']) if finite else None

        sessions_out.append({
            'date': date, 'date_index': sess['date_index'],
            'turn_count': sess['turn_count'],
            'betti_0': int(betti_0), 'betti_1': int(betti_1), 'betti_2': 0,
            'persistence_diagram': all_features[:50],
            'longest_lived_feature': longest,
        })
        print(f"  {date}: b0={betti_0}, b1={betti_1}")

    return {'sessions': sessions_out}


# ── Analysis 11: Bridging Concepts ────────────────────────────────────────────

def analysis_11_bridging_concepts(turns, embeddings, turn_idx_map,
                                   corpus_vecs, corpus_meta, session_defs):
    print("[A11] Bridging Concepts...")
    n_corpus = len(corpus_vecs)
    n_sessions = len(session_defs['sessions'])
    date_to_idx = {s['date']: s['date_index'] for s in session_defs['sessions']}

    corp_norms = np.linalg.norm(corpus_vecs, axis=1, keepdims=True) + 1e-9
    corp_normed = corpus_vecs / corp_norms

    nearest_corpus = {}
    total_refs = np.zeros(n_corpus, dtype=int)
    session_refs = [set() for _ in range(n_corpus)]

    print(f"  Computing nearest corpus for {len(turns)} turns...")
    for t in turns:
        idx = turn_idx_map.get(t['turn'])
        if idx is None:
            continue
        emb = embeddings[idx]
        norm = np.linalg.norm(emb)
        if norm < 1e-9:
            continue
        sims = corp_normed @ (emb / norm)
        best = int(np.argmax(sims))
        nearest_corpus[t['turn']] = best
        total_refs[best] += 1
        date_idx = date_to_idx.get(t['date'], -1)
        if date_idx >= 0:
            session_refs[best].add(date_idx)

    documents = []
    for i, meta in enumerate(corpus_meta):
        if i >= n_corpus:
            break
        n_sessions_ref = len(session_refs[i])
        bridge_score = n_sessions_ref / n_sessions if n_sessions > 0 else 0.0

        counts_by_session = Counter(
            t['date'] for t in turns if nearest_corpus.get(t['turn']) == i
        )
        peak_date = max(counts_by_session, key=counts_by_session.get) if counts_by_session else None
        peak_session = date_to_idx.get(peak_date, -1) if peak_date else -1

        documents.append({
            'corpus_idx': i,
            'name': meta.get('source_file', f'doc_{i}'),
            'author': meta.get('author', ''),
            'quality_signal': meta.get('quality_signal', ''),
            'bridge_score': float(bridge_score),
            'session_count': int(n_sessions_ref),
            'total_references': int(total_refs[i]),
            'sessions_referenced': sorted(session_refs[i]),
            'peak_session': int(peak_session),
        })

    documents.sort(key=lambda d: -d['bridge_score'])

    universal = [d for d in documents if d['bridge_score'] > 0.6]
    phase     = [d for d in documents if 0.3 <= d['bridge_score'] <= 0.6]
    local     = [d for d in documents if d['bridge_score'] < 0.3]
    print(f"  Universal: {len(universal)}, Phase: {len(phase)}, Local: {len(local)}")
    for d in documents[:5]:
        print(f"  {d['name']}: bridge={d['bridge_score']:.2f}, {d['session_count']} sessions")

    return {
        'documents': documents,
        'categories': {
            'universal_anchors': [d['name'] for d in universal],
            'phase_anchors': [d['name'] for d in phase],
            'local_features': [d['name'] for d in local],
        },
        'nearest_corpus_by_turn': {str(k): v for k, v in list(nearest_corpus.items())[:100]},
    }


# ── Analysis 15: Signal Density ───────────────────────────────────────────────

def analysis_15_signal_density(turns, embeddings, turn_idx_map, session_defs,
                                window=20, spike_sigma=2.0):
    print("[A15] Signal Density (novelty)...")
    ordered = [t for t in turns if t['turn'] in turn_idx_map]
    n = len(ordered)
    ordered_embs = np.array([embeddings[turn_idx_map[t['turn']]] for t in ordered],
                             dtype=np.float32)

    novelty = np.zeros(n, dtype=np.float32)
    novelty[0] = 1.0

    print(f"  Computing novelty for {n} turns (vectorized)...")
    for i in range(1, n):
        sims = ordered_embs[:i] @ ordered_embs[i]
        novelty[i] = float(1.0 - sims.max())

    half_w = window // 2
    smoothed = np.zeros(n, dtype=np.float32)
    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        smoothed[i] = novelty[start:end].mean()

    mean_nov = float(novelty.mean())
    std_nov  = float(novelty.std())
    thresh   = mean_nov + spike_sigma * std_nov

    spikes = []
    for i, t in enumerate(ordered):
        if novelty[i] >= thresh:
            spikes.append({
                'turn': t['turn'],
                'speaker': t['speaker'],
                'date': t['date'],
                'source': t.get('source', 'doc1'),
                'novelty': float(novelty[i]),
                'smoothed_novelty': float(smoothed[i]),
                'text_preview': t['content'][:120],
            })
    spikes.sort(key=lambda s: -s['novelty'])

    jake_nov = [novelty[i] for i, t in enumerate(ordered) if t['speaker'] == 'Jake']
    opus_nov = [novelty[i] for i, t in enumerate(ordered) if t['speaker'] == 'Opus']

    by_date = defaultdict(list)
    for i, t in enumerate(ordered):
        by_date[t['date']].append((i, novelty[i]))

    by_session = []
    for sess in session_defs['sessions']:
        date = sess['date']
        sess_entries = by_date[date]
        if not sess_entries:
            continue
        sess_novs = [nv for _, nv in sess_entries]
        jake_novs = [novelty[i] for i, t in enumerate(ordered)
                     if t['date'] == date and t['speaker'] == 'Jake']
        opus_novs = [novelty[i] for i, t in enumerate(ordered)
                     if t['date'] == date and t['speaker'] == 'Opus']
        sess_spikes = sum(1 for nv in sess_novs if nv >= thresh)
        by_session.append({
            'date': date,
            'date_index': sess['date_index'],
            'mean_novelty': float(np.mean(sess_novs)),
            'max_novelty': float(np.max(sess_novs)),
            'spike_count': sess_spikes,
            'jake_novelty': float(np.mean(jake_novs)) if jake_novs else 0.0,
            'opus_novelty': float(np.mean(opus_novs)) if opus_novs else 0.0,
        })

    turns_out = [
        {'turn': ordered[i]['turn'], 'speaker': ordered[i]['speaker'],
         'date': ordered[i]['date'], 'source': ordered[i].get('source','doc1'),
         'novelty': float(novelty[i]), 'smoothed_novelty': float(smoothed[i])}
        for i in range(n)
    ]
    highest = max(turns_out, key=lambda t: t['novelty'])
    lowest  = min(turns_out, key=lambda t: t['novelty'])

    print(f"  Mean novelty: {mean_nov:.4f}, Spikes: {len(spikes)}")
    print(f"  Highest novelty: turn {highest['turn']} ({highest['novelty']:.4f})")
    print(f"  Jake mean: {np.mean(jake_nov):.4f}, Opus mean: {np.mean(opus_nov):.4f}")

    return {
        'turns': turns_out,
        'novelty_spikes': spikes[:50],
        'by_session': by_session,
        'overall': {
            'mean': float(mean_nov),
            'std': float(std_nov),
            'threshold': float(thresh),
            'jake_mean': float(np.mean(jake_nov)) if jake_nov else 0.0,
            'opus_mean': float(np.mean(opus_nov)) if opus_nov else 0.0,
            'highest_novelty_turn': highest['turn'],
            'lowest_novelty_turn': lowest['turn'],
        },
    }


# ── Analysis 1A: Spectral Phase Analysis ──────────────────────────────────────

def analysis_1a_spectral_phases(turns, embeddings, turn_idx_map, session_defs):
    print("[A1A] Spectral Phase Analysis (RankMe + alpha-ReQ)...")
    sessions_out = []
    phase_transitions = []
    prev_rankme = None

    for sess in session_defs['sessions']:
        date = sess['date']
        sess_turn_idxs = [
            turn_idx_map[t['turn']]
            for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        ]
        if len(sess_turn_idxs) < 5:
            sessions_out.append({
                'date': date, 'date_index': sess['date_index'],
                'n_turns': len(sess_turn_idxs),
                'rankme': None, 'alpha_req': None,
                'top_eigenvalue_ratio': None, 'effective_dimensions': None,
            })
            continue

        X = _to_gpu(embeddings[sess_turn_idxs].astype(np.float64))
        xp = cp if _GPU else np
        X = X - X.mean(axis=0)
        cov = _to_cpu((X.T @ X) / len(X))
        X = None
        eigvals = np.linalg.eigvalsh(cov)[::-1]
        eigvals = np.maximum(eigvals, 0.0)
        total = eigvals.sum() + 1e-12

        probs = eigvals / total
        probs_nz = probs[probs > 1e-12]
        rankme = float(np.exp(-np.sum(probs_nz * np.log(probs_nz))))

        K = min(50, len(eigvals))
        ranks = np.arange(1, K + 1, dtype=np.float64)
        lam = eigvals[:K] + 1e-12
        alpha_req = float(-np.polyfit(np.log(ranks), np.log(lam), 1)[0])
        top_ratio = float(eigvals[0] / total)
        cumsum = np.cumsum(eigvals)
        n_eff = int(np.searchsorted(cumsum, 0.9 * total) + 1)

        entry = {
            'date': date, 'date_index': sess['date_index'],
            'n_turns': len(sess_turn_idxs),
            'rankme': rankme, 'alpha_req': alpha_req,
            'top_eigenvalue_ratio': top_ratio,
            'effective_dimensions': n_eff,
        }
        sessions_out.append(entry)

        if prev_rankme is not None:
            delta = rankme - prev_rankme
            rel = delta / (prev_rankme + 1e-9)
            if abs(rel) > 0.2:
                phase_transitions.append({
                    'date': date, 'date_index': sess['date_index'],
                    'metric': 'rankme',
                    'direction': 'rise' if delta > 0 else 'drop',
                    'magnitude': float(abs(rel)),
                    'from_rankme': float(prev_rankme),
                    'to_rankme': float(rankme),
                })
        prev_rankme = rankme

    n_valid = sum(1 for s in sessions_out if s['rankme'] is not None)
    print(f"  {n_valid} sessions analyzed, {len(phase_transitions)} phase transitions")
    return {'sessions': sessions_out, 'phase_transitions': phase_transitions}


# ── Analysis 2A: Trajectory Tangling ──────────────────────────────────────────

def analysis_2a_trajectory_tangling(turns, embeddings, turn_idx_map, session_defs,
                                     spike_sigma=2.0):
    print("[A2A] Trajectory Tangling (Russo et al. 2018)...")
    ordered = sorted([t for t in turns if t['turn'] in turn_idx_map], key=lambda t: t['turn'])
    ordered_idxs = [turn_idx_map[t['turn']] for t in ordered]

    if len(ordered_idxs) < 3:
        return {'turns': [], 'high_tangling_moments': [], 'mean_tangling': 0.0,
                'std_tangling': 0.0, 'threshold': 0.0,
                'tangling_by_session': [], 'tangling_by_speaker': {}}

    xp = cp if _GPU else np
    E = _to_gpu(embeddings[ordered_idxs].astype(np.float64))
    n = int(E.shape[0])
    D = E[1:] - E[:-1]
    E_base = E[:-1]
    m = n - 1

    mem_mb = m ** 2 * 8 // 1_000_000
    device = "GPU" if _GPU else "CPU"
    print(f"  Building {m}x{m} tangling matrices ({mem_mb} MB) on {device}...")

    d_sq  = xp.sum(D ** 2, axis=1)
    d_dot = D @ D.T
    d_diff_sq = xp.maximum(d_sq[:, None] + d_sq[None, :] - 2 * d_dot, 0.0)

    e_sq  = xp.sum(E_base ** 2, axis=1)
    e_dot = E_base @ E_base.T
    e_diff_sq = xp.maximum(e_sq[:, None] + e_sq[None, :] - 2 * e_dot, 0.0)

    eps = 0.01 * float(e_diff_sq.mean()) + 1e-9
    ratio = d_diff_sq / (e_diff_sq + eps)
    xp.fill_diagonal(ratio, 0.0)
    Q = _to_cpu(ratio.max(axis=1)).astype(np.float32)
    del ratio, d_diff_sq, e_diff_sq, d_dot, e_dot

    mean_Q = float(Q.mean())
    std_Q  = float(Q.std())
    thresh = mean_Q + spike_sigma * std_Q

    turns_out = []
    by_session = defaultdict(list)
    jake_Q, opus_Q = [], []

    for i, t in enumerate(ordered[:-1]):
        q_val = float(Q[i])
        entry = {'turn': t['turn'], 'speaker': t['speaker'],
                 'date': t.get('date', 'unknown'), 'tangling': q_val}
        turns_out.append(entry)
        by_session[t.get('date', 'unknown')].append(q_val)
        (jake_Q if t['speaker'] == 'Jake' else opus_Q).append(q_val)

    high_tangling = sorted(
        [e for e in turns_out if e['tangling'] >= thresh],
        key=lambda x: -x['tangling']
    )[:30]

    session_tangling = []
    for sess in session_defs['sessions']:
        vals = by_session.get(sess['date'], [])
        if vals:
            session_tangling.append({
                'date': sess['date'], 'date_index': sess['date_index'],
                'mean_tangling': float(np.mean(vals)),
                'max_tangling': float(np.max(vals)),
            })

    print(f"  Mean Q={mean_Q:.3f}, threshold={thresh:.3f}, "
          f"high-tangling turns={len(high_tangling)}")
    return {
        'turns': turns_out,
        'high_tangling_moments': high_tangling,
        'mean_tangling': mean_Q,
        'std_tangling': float(std_Q),
        'threshold': float(thresh),
        'tangling_by_session': session_tangling,
        'tangling_by_speaker': {
            'jake_mean': float(np.mean(jake_Q)) if jake_Q else 0.0,
            'opus_mean': float(np.mean(opus_Q)) if opus_Q else 0.0,
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== V2 FULL CHATLOG ANALYSIS SUITE ===")
    print(f"Input:  {TURNS_JSON}")
    print(f"Output: {OUT}\n")

    print("[LOAD] Loading turns...")
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"  {len(turns)} turns loaded")

    print("[LOAD] Loading embeddings...")
    embeddings = np.load(str(EMBEDDINGS))
    print(f"  Shape: {embeddings.shape}")

    if len(embeddings) != len(turns):
        n = min(len(embeddings), len(turns))
        print(f"  WARNING: mismatch {len(embeddings)} vs {len(turns)} - truncating to {n}")
        embeddings = embeddings[:n]
        turns = turns[:n]

    print("[LOAD] Loading centroids...")
    centroids = load_centroids(CENTROIDS)
    print(f"  Domains: {list(centroids.keys())}")

    print("[LOAD] Loading corpus...")
    corpus_vecs = load_corpus_vecs(CORPUS_FAISS)
    with open(CORPUS_META, encoding='utf-8') as f:
        corpus_meta = json.load(f)
    print(f"  Corpus: {len(corpus_vecs)} vectors")

    print("[LOAD] Loading session dates...")
    with open(SESSIONS_JSON, encoding='utf-8') as f:
        session_defs = json.load(f)
    print(f"  Sessions: {len(session_defs['sessions'])}")

    # Build turn index map: turn_number -> row in embeddings array
    turn_idx_map = {t['turn']: i for i, t in enumerate(turns)}

    # Build joint UMAP (turn-level, for analyses)
    print("\n[UMAP] Building joint 3D projection (corpus + turns)...")
    corpus_coords, turn_coords = build_joint_umap(corpus_vecs, embeddings)
    print(f"  Corpus coords: {corpus_coords.shape}")
    print(f"  Turn coords: {turn_coords.shape}")

    umap_data = {
        'corpus': [
            {
                'faiss_id': i,
                'source_file': corpus_meta[i].get('source_file', ''),
                'author': corpus_meta[i].get('author', ''),
                'quality_signal': corpus_meta[i].get('quality_signal', ''),
                'umap_x': float(corpus_coords[i, 0]),
                'umap_y': float(corpus_coords[i, 1]),
                'umap_z': float(corpus_coords[i, 2]),
            }
            for i in range(len(corpus_coords)) if i < len(corpus_meta)
        ],
        'turns': [
            {
                'turn': t['turn'],
                'speaker': t['speaker'],
                'date': t['date'],
                'date_index': t.get('date_index', -1),
                'source': t.get('source', 'doc1'),
                'word_count': t['word_count'],
                'umap_x': float(turn_coords[i, 0]),
                'umap_y': float(turn_coords[i, 1]),
                'umap_z': float(turn_coords[i, 2]),
                'content_preview': t['content'][:200],
            }
            for i, t in enumerate(turns)
        ],
    }
    out_umap = OUT / "umap_turns.json"
    with open(out_umap, 'w', encoding='utf-8') as f:
        json.dump(umap_data, f, ensure_ascii=False)
    print(f"  Saved: {out_umap}")

    print()

    def save(name, data, indent=None):
        path = OUT / name
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        size = path.stat().st_size // 1024
        print(f"  Saved: {path.name:<40} {size:>5} KB")
        return data

    s1 = analysis_1_session_signatures(turns, embeddings, session_defs, centroids,
                                        corpus_coords, turn_coords, turn_idx_map)
    save("session_signatures.json", s1, indent=2)
    print(f"    {len(s1['sessions'])} sessions")

    s2 = analysis_2_recurrence(turns, embeddings, turn_idx_map, session_defs)
    save("recurrence_matrix.json", s2)
    print(f"    {s2['n_blocks']}x{s2['n_blocks']} blocks")

    s3 = analysis_3_speaker_coupling(turns, embeddings, turn_idx_map)
    save("speaker_coupling.json", s3, indent=2)
    print(f"    {len(s3['pairs'])} pairs, mean dist={s3.get('mean_distance',0):.3f}")

    s4 = analysis_4_sliding_window(turns, embeddings, turn_idx_map, centroids, turn_coords)
    save("sliding_window_trajectory.json", s4, indent=2)
    print(f"    {s4['n_points']} window points")

    s5 = analysis_5_information_flow(turns, embeddings, turn_idx_map)
    save("information_flow.json", s5, indent=2)
    print(f"    Jake {s5['jake_lead_percentage']:.0f}% / Opus {s5['opus_lead_percentage']:.0f}%")

    s6 = analysis_6_entropy_trace(turns, embeddings, turn_idx_map, centroids)
    save("entropy_trace.json", s6, indent=2)
    print(f"    mean entropy={s6['mean_entropy']:.3f}, max={s6['max_theoretical_entropy']:.3f}")

    s7 = analysis_7_cumulative_drift(turns, embeddings, turn_idx_map)
    save("cumulative_drift.json", s7, indent=2)
    print(f"    Jake {s7['total_jake_distance']:.2f} / Opus {s7['total_opus_distance']:.2f}")

    s8 = analysis_8_markov(turns, embeddings, turn_idx_map, centroids)
    save("transition_matrix.json", s8, indent=2)
    print(f"    self-transition rate: {s8['full']['self_transition_rate']:.2f}")

    s9 = analysis_9_phase_space(s4['points'])
    save("phase_space.json", s9, indent=2)

    s10 = analysis_10_persistent_homology(turns, embeddings, turn_idx_map, session_defs)
    save("persistent_homology.json", s10, indent=2)
    b0m = sum(s.get('betti_0', 0) for s in s10['sessions']) / max(len(s10['sessions']), 1)
    b1m = sum(s.get('betti_1', 0) for s in s10['sessions']) / max(len(s10['sessions']), 1)
    print(f"    mean b0={b0m:.1f}, mean b1={b1m:.1f}")

    s11 = analysis_11_bridging_concepts(turns, embeddings, turn_idx_map,
                                         corpus_vecs, corpus_meta, session_defs)
    save("bridging_concepts.json", s11, indent=2)
    print(f"    {len(s11['categories']['universal_anchors'])} universal anchors")

    s15 = analysis_15_signal_density(turns, embeddings, turn_idx_map, session_defs)
    save("signal_density.json", s15, indent=2)
    print(f"    {len(s15['novelty_spikes'])} spikes")

    s1a = analysis_1a_spectral_phases(turns, embeddings, turn_idx_map, session_defs)
    save("spectral_phases.json", s1a, indent=2)
    print(f"    {len(s1a['phase_transitions'])} phase transitions")

    s2a = analysis_2a_trajectory_tangling(turns, embeddings, turn_idx_map, session_defs)
    save("trajectory_tangling.json", s2a, indent=2)
    print(f"    mean Q={s2a['mean_tangling']:.3f}, {len(s2a['high_tangling_moments'])} high-tangling")

    print("\n=== V2 ANALYSES COMPLETE ===")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
