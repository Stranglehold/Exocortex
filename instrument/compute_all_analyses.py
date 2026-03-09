"""
compute_all_analyses.py — Run all 12 analyses from the Full Chatlog Analysis Suite briefing.

Requires:
    data/chatlog_full_turns_dated.json   (from assign_session_dates.py)
    data/chatlog_full_turn_embeddings.npy (from compute_response_vectors.py)
    data/centroids_768.json              (domain centroids)
    data/corpus.faiss                    (51 corpus vectors)
    data/corpus_metadata.json            (corpus metadata)
    data/session_dates.json              (date groupings)

Outputs (all in data/):
    umap_full.json                  — joint UMAP coords (corpus + all turns)
    session_signatures.json         — Analysis 1
    spectral_phases.json            — Analysis 1A (RankMe + alpha-ReQ, Li et al. 2025)
    recurrence_matrix.json          — Analysis 2
    trajectory_tangling.json        — Analysis 2A (Russo et al. 2018)
    speaker_coupling.json           — Analysis 3
    sliding_window_trajectory.json  — Analysis 4 (now includes curvature + jerk)
    information_flow.json           — Analysis 5
    entropy_trace.json              — Analysis 6
    cumulative_drift.json           — Analysis 7
    transition_matrix.json          — Analysis 8
    phase_space.json                — Analysis 9
    persistent_homology.json        — Analysis 10
    bridging_concepts.json          — Analysis 11
    signal_density.json             — Analysis 15
"""

import json
import math
import numpy as np
import faiss
import umap
from pathlib import Path
from collections import defaultdict, Counter

# GPU acceleration via cupy — falls back to numpy transparently.
# Matrix-heavy analyses (tangling, spectral) run on the RTX 3090 when available.
try:
    import cupy as cp
    _GPU = True
    print("[GPU] cupy available — matrix ops will run on GPU")
except ImportError:
    cp = None
    _GPU = False

def _to_gpu(arr: np.ndarray):
    return cp.asarray(arr) if _GPU else arr

def _to_cpu(arr) -> np.ndarray:
    if _GPU and cp is not None and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)
    return np.asarray(arr)

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# Inputs
TURNS_JSON    = DATA / "chatlog_full_turns_dated.json"
EMBEDDINGS    = DATA / "chatlog_full_turn_embeddings.npy"
CENTROIDS     = DATA / "centroids_768.json"
CORPUS_FAISS  = DATA / "corpus.faiss"
CORPUS_META   = DATA / "corpus_metadata.json"
SESSIONS_JSON = DATA / "session_dates.json"

# Outputs
OUT_UMAP      = DATA / "umap_full.json"
OUT_S1        = DATA / "session_signatures.json"
OUT_S2        = DATA / "recurrence_matrix.json"
OUT_S3        = DATA / "speaker_coupling.json"
OUT_S4        = DATA / "sliding_window_trajectory.json"
OUT_S5        = DATA / "information_flow.json"
OUT_S6        = DATA / "entropy_trace.json"
OUT_S7        = DATA / "cumulative_drift.json"
OUT_S8        = DATA / "transition_matrix.json"
OUT_S9        = DATA / "phase_space.json"
OUT_S10       = DATA / "persistent_homology.json"
OUT_S11       = DATA / "bridging_concepts.json"
OUT_S15       = DATA / "signal_density.json"
OUT_S1A       = DATA / "spectral_phases.json"
OUT_S2A       = DATA / "trajectory_tangling.json"

WINDOW_SIZE   = 20
STEP_SIZE     = 5      # slide 5 turns at a time (not 1 — too many points)
RECURRENCE_BLOCK = 10  # turns per block for recurrence matrix


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_centroids(path: Path) -> dict[str, np.ndarray]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if 'centroids' in data:
        raw = data['centroids']
        first = next(iter(raw.values()))
        if isinstance(first, list):
            return {d: np.array(v, dtype=np.float32) for d, v in raw.items()}
    return {d: np.array(v, dtype=np.float32) for d, v in data.items() if isinstance(v, list)}


def load_corpus_vecs(faiss_path: Path) -> np.ndarray:
    idx = faiss.read_index(str(faiss_path))
    vecs = np.zeros((idx.ntotal, idx.d), dtype=np.float32)
    idx.reconstruct_n(0, idx.ntotal, vecs)
    return vecs


def classify_turn(emb: np.ndarray, centroids: dict[str, np.ndarray]) -> tuple[str, dict]:
    """Return (nearest_domain, {domain: cosine_sim}) for a 768-dim embedding."""
    scores = {}
    for domain, centroid in centroids.items():
        norm_e = np.linalg.norm(emb)
        norm_c = np.linalg.norm(centroid)
        if norm_e > 0 and norm_c > 0:
            scores[domain] = float(np.dot(emb, centroid) / (norm_e * norm_c))
        else:
            scores[domain] = 0.0
    nearest = max(scores, key=scores.get)
    return nearest, scores


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def euclidean_dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a.astype(np.float64) - b.astype(np.float64)))


def shannon_entropy(counts: dict) -> float:
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

def build_joint_umap(corpus_vecs: np.ndarray, turn_vecs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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
    all_dates = [s['date'] for s in session_defs['sessions']]

    for sess in session_defs['sessions']:
        date = sess['date']
        tr_start, tr_end = sess['turn_range']
        # Get indices of turns in this date group
        sess_turn_idxs = [
            turn_idx_map[t['turn']]
            for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        ]
        if not sess_turn_idxs:
            continue

        sess_embs = embeddings[sess_turn_idxs]  # shape: (n, 768)
        centroid = sess_embs.mean(axis=0)
        centroid /= (np.linalg.norm(centroid) + 1e-9)

        # Domain classification
        nearest_domain, domain_dists = classify_turn(centroid, centroids)

        # UMAP coords: mean of member turn coords
        sess_umap = turn_coords[sess_turn_idxs].mean(axis=0)

        # Internal arc length: sum of consecutive displacements within session
        # Use all turns in order
        sess_turn_nums_ordered = sorted(
            t['turn'] for t in turns
            if t['date'] == date and t['turn'] in turn_idx_map
        )
        arc_length = 0.0
        for i in range(1, len(sess_turn_nums_ordered)):
            a_idx = turn_idx_map[sess_turn_nums_ordered[i-1]]
            b_idx = turn_idx_map[sess_turn_nums_ordered[i]]
            arc_length += euclidean_dist(embeddings[a_idx], embeddings[b_idx])

        # Register distribution within session
        reg_counts = Counter()
        for idx in sess_turn_idxs:
            reg, _ = classify_turn(embeddings[idx], centroids)
            reg_counts[reg] += 1
        reg_entropy = shannon_entropy(dict(reg_counts))

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
        })

    # Compute displacement_from_previous
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

    # Build block-averaged embeddings
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
    # n_blocks x n_blocks cosine similarity
    norms = np.linalg.norm(block_embs, axis=1, keepdims=True) + 1e-9
    normed = block_embs / norms
    sim_matrix = (normed @ normed.T).tolist()

    # Session boundaries (block indices)
    session_boundaries = []
    date_groups = [s['date'] for s in session_defs['sessions']]
    for s in session_defs['sessions']:
        tr_start = s['turn_range'][0]
        block_idx = tr_start // block_size
        if block_idx not in session_boundaries:
            session_boundaries.append(block_idx)

    # High-recurrence off-diagonal pairs
    flat_vals = [sim_matrix[i][j] for i in range(n_blocks) for j in range(i+50, n_blocks)]
    if flat_vals:
        mean_sim = sum(flat_vals) / len(flat_vals)
        std_sim = math.sqrt(sum((v - mean_sim)**2 for v in flat_vals) / len(flat_vals))
        thresh = mean_sim + threshold_sigma * std_sim
    else:
        thresh = 0.8

    high_recurrence = []
    for i in range(n_blocks):
        for j in range(i + 50, n_blocks):  # skip nearby blocks
            if sim_matrix[i][j] >= thresh:
                # Map blocks back to representative turns
                turn_i = turns[min(i * block_size, n-1)]['turn']
                turn_j = turns[min(j * block_size, n-1)]['turn']
                high_recurrence.append({
                    'block_i': i, 'block_j': j,
                    'turn_i': turn_i, 'turn_j': turn_j,
                    'similarity': float(sim_matrix[i][j]),
                    'date_i': turns[min(i * block_size, n-1)]['date'],
                    'date_j': turns[min(j * block_size, n-1)]['date'],
                })

    # Sort by similarity
    high_recurrence.sort(key=lambda x: -x['similarity'])

    return {
        'resolution': block_size,
        'n_blocks': n_blocks,
        'matrix': sim_matrix,
        'session_boundaries': session_boundaries,
        'threshold': float(thresh),
        'high_recurrence_pairs': high_recurrence[:50],  # top 50
    }


# ── Analysis 3: Cross-Speaker Phase Coupling ──────────────────────────────────

def analysis_3_speaker_coupling(turns, embeddings, turn_idx_map, window=10):
    print("[A3] Cross-Speaker Phase Coupling...")
    pairs = []
    for i in range(len(turns) - 1):
        t1, t2 = turns[i], turns[i+1]
        if t1['speaker'] == 'Jake' and t2['speaker'] == 'Opus':
            idx1 = turn_idx_map.get(t1['turn'])
            idx2 = turn_idx_map.get(t2['turn'])
            if idx1 is None or idx2 is None:
                continue
            sim = cosine_sim(embeddings[idx1], embeddings[idx2])
            dist = float(1.0 - sim)
            pairs.append({
                'position': len(pairs),
                'jake_turn': t1['turn'],
                'opus_turn': t2['turn'],
                'date': t1['date'],
                'similarity': float(sim),
                'distance': dist,
            })

    if not pairs:
        return {'pairs': [], 'smoothed_distance': [], 'convergence_points': [], 'divergence_points': []}

    distances = [p['distance'] for p in pairs]

    # Smoothed distance (rolling average)
    half_w = window // 2
    smoothed = []
    for i in range(len(distances)):
        start = max(0, i - half_w)
        end = min(len(distances), i + half_w + 1)
        smoothed.append(float(sum(distances[start:end]) / (end - start)))

    # Find convergence (local minima) and divergence (local maxima) in smoothed
    convergence = []
    divergence = []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] < smoothed[i-1] and smoothed[i] < smoothed[i+1]:
            convergence.append({'position': i, 'turn': pairs[i]['jake_turn'],
                                'distance': smoothed[i], 'date': pairs[i]['date']})
        elif smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
            divergence.append({'position': i, 'turn': pairs[i]['jake_turn'],
                               'distance': smoothed[i], 'date': pairs[i]['date']})

    # Top 10 convergence / divergence points
    convergence.sort(key=lambda x: x['distance'])
    divergence.sort(key=lambda x: -x['distance'])

    # Add smoothed_distance to pairs
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

        # Classify centroid
        nearest, domain_scores = classify_turn(centroid_normed, centroids)

        # UMAP: mean of member UMAP coords
        umap_centroid = turn_coords[window_idxs].mean(axis=0)
        curr_coords = umap_centroid

        # Velocity (distance from previous window centroid)
        velocity = float(np.linalg.norm(curr_coords - prev_coords)) if prev_coords is not None else 0.0

        # Acceleration (change in velocity direction)
        if prev_prev_coords is not None and prev_coords is not None:
            prev_vel = prev_coords - prev_prev_coords
            curr_vel = curr_coords - prev_coords
            pn = np.linalg.norm(prev_vel)
            cn = np.linalg.norm(curr_vel)
            if pn > 1e-9 and cn > 1e-9:
                accel = float(1.0 - np.dot(prev_vel/pn, curr_vel/cn))  # angle change
            else:
                accel = 0.0
        else:
            accel = 0.0

        # 768-dim kinematics (true geometry, Zhou et al. 2025)
        zero768 = np.zeros(768, dtype=np.float32)
        vel_768 = (centroid_normed - prev_centroid_768) if prev_centroid_768 is not None else zero768
        accel_768 = (vel_768 - prev_vel_768) if prev_vel_768 is not None else zero768
        jerk_768 = (accel_768 - prev_accel_768) if prev_accel_768 is not None else zero768
        vel_mag_768 = float(np.linalg.norm(vel_768))
        jerk_mag = float(np.linalg.norm(jerk_768))
        # Curvature: sqrt(|a_normal|^2) / |v|^2, where a_normal = a - (a.v_hat)v_hat
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

    # Peak accelerations (top 20)
    peak_accels = sorted(points, key=lambda p: -p['acceleration_magnitude'])[:20]

    # High curvature points (top 20, Zhou et al. terminology)
    high_curv = sorted(points, key=lambda p: -p['curvature'])[:20]

    # Inflection points: local curvature maxima
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
    jake_turns = [t for t in turns if t['speaker'] == 'Jake' and t['turn'] in turn_idx_map]
    opus_turns = [t for t in turns if t['speaker'] == 'Opus' and t['turn'] in turn_idx_map]

    # For each adjacent Jake->Opus pair, compute displacement
    pairs = []
    for i in range(len(turns) - 1):
        t1, t2 = turns[i], turns[i+1]
        if t1['speaker'] != 'Jake' or t2['speaker'] != 'Opus':
            continue
        idx1 = turn_idx_map.get(t1['turn'])
        idx2 = turn_idx_map.get(t2['turn'])
        if idx1 is None or idx2 is None:
            continue

        # Find previous Jake and Opus turns for displacement computation
        # Jake displacement: distance from previous Jake turn
        # Opus displacement: distance from previous Opus turn
        prev_jake_idx = None
        prev_opus_idx = None

        # Search backwards
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

    # Smoothed ratio
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

    # By date
    by_date = defaultdict(list)
    for p in pairs:
        by_date[p['date']].append(p)
    by_date_summary = []
    for date, date_pairs in sorted(by_date.items(), key=lambda x: x[0]):
        jl = sum(1 for p in date_pairs if p['leader'] == 'jake')
        ol = sum(1 for p in date_pairs if p['leader'] == 'opus')
        by_date_summary.append({
            'date': date,
            'n_pairs': len(date_pairs),
            'jake_lead_pct': float(100 * jl / len(date_pairs)) if date_pairs else 0,
            'opus_lead_pct': float(100 * ol / len(date_pairs)) if date_pairs else 0,
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
    # Classify all turns first
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
    jake_drift = []
    opus_drift = []
    jake_cum = 0.0
    opus_cum = 0.0
    prev_jake_emb = None
    prev_opus_emb = None

    for t in turns:
        idx = turn_idx_map.get(t['turn'])
        if idx is None:
            continue
        emb = embeddings[idx]
        if t['speaker'] == 'Jake':
            if prev_jake_emb is not None:
                step_dist = euclidean_dist(emb, prev_jake_emb)
                jake_cum += step_dist
                jake_drift.append({
                    'turn': t['turn'],
                    'date': t['date'],
                    'cumulative_distance': float(jake_cum),
                    'step_distance': float(step_dist),
                })
            else:
                jake_drift.append({
                    'turn': t['turn'], 'date': t['date'],
                    'cumulative_distance': 0.0, 'step_distance': 0.0,
                })
            prev_jake_emb = emb
        else:
            if prev_opus_emb is not None:
                step_dist = euclidean_dist(emb, prev_opus_emb)
                opus_cum += step_dist
                opus_drift.append({
                    'turn': t['turn'],
                    'date': t['date'],
                    'cumulative_distance': float(opus_cum),
                    'step_distance': float(step_dist),
                })
            else:
                opus_drift.append({
                    'turn': t['turn'], 'date': t['date'],
                    'cumulative_distance': 0.0, 'step_distance': 0.0,
                })
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

    # Classify all turns
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
            t1 = subset_turns[i]
            t2 = subset_turns[i+1]
            d1 = turn_domains.get(t1['turn'])
            d2 = turn_domains.get(t2['turn'])
            if d1 and d2:
                counts[d_to_i[d1], d_to_i[d2]] += 1
        # Normalize rows
        probs = np.zeros_like(counts, dtype=float)
        for i in range(n_d):
            row_sum = counts[i].sum()
            if row_sum > 0:
                probs[i] = counts[i] / row_sum
        self_transition = float(np.diag(probs).mean())
        return {
            'matrix': probs.tolist(),
            'counts': counts.tolist(),
            'labels': domains,
            'self_transition_rate': self_transition,
        }

    n = len(turns)
    early = compute_matrix(turns[:n//2])
    late  = compute_matrix(turns[n//2:])
    full  = compute_matrix(turns)

    # Drift analysis: which transitions changed most?
    early_mat = np.array(early['matrix'])
    late_mat  = np.array(late['matrix'])
    diff = late_mat - early_mat

    increased, decreased = [], []
    for i in range(n_d):
        for j in range(n_d):
            if i != j and abs(diff[i, j]) > 0.05:
                entry = [domains[i], domains[j], float(early_mat[i,j]), float(late_mat[i,j])]
                if diff[i, j] > 0:
                    increased.append(entry)
                else:
                    decreased.append(entry)

    increased.sort(key=lambda x: -(x[3]-x[2]))
    decreased.sort(key=lambda x: x[3]-x[2])

    return {
        'full': full,
        'early': early,
        'late': late,
        'transition_drift': {
            'increased': increased[:5],
            'decreased': decreased[:5],
        },
    }


# ── Analysis 9: Phase Space Reconstruction ────────────────────────────────────

def analysis_9_phase_space(sliding_window_points, tau_values=(5, 10, 20)):
    print("[A9] Phase Space Reconstruction...")
    # Use UMAP coords from sliding window as the 3-component signal
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

        # Simple Lyapunov estimate: average divergence rate
        # Approximation: average separation growth between nearest neighbors
        # (expensive to do properly; use a crude estimate)
        lyapunov_est = None
        if len(recon) > 10:
            coords = np.array([[r['x'], r['y'], r['z']] for r in recon])
            # For each point, find nearest neighbor (exclude immediate neighbors)
            separations = []
            for i in range(len(coords)):
                dists = []
                for j in range(len(coords)):
                    if abs(i - j) > tau:
                        d = np.linalg.norm(coords[i] - coords[j])
                        dists.append(d)
                if dists:
                    separations.append(min(dists))
            if separations:
                # Lyapunov ~ log of mean nearest-neighbor distance
                lyapunov_est = float(math.log(sum(separations) / len(separations) + 1e-9))

        results[f'tau_{tau}'] = {
            'tau': tau,
            'n_points': len(recon),
            'points': recon,
            'lyapunov_estimate': lyapunov_est,
        }

    return {
        'tau_values': list(tau_values),
        'reconstructions': results,
    }


# ── Analysis 10: Persistent Homology ─────────────────────────────────────────

def analysis_10_persistent_homology(turns, embeddings, turn_idx_map, session_defs):
    print("[A10] Persistent Homology...")
    try:
        from ripser import ripser as rips
    except ImportError:
        print("  [A10] ripser not installed — skipping")
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

        # Cosine distance matrix (ripser works on distances, not similarities)
        norms = np.linalg.norm(sess_embs, axis=1, keepdims=True) + 1e-9
        normed = sess_embs / norms
        cos_sim = normed @ normed.T
        dist_mat = np.clip(1.0 - cos_sim, 0.0, 2.0)

        # Run ripser up to H1 (H2 is slow; add max_dim=2 if needed)
        result = rips(dist_mat, maxdim=1, distance_matrix=True)
        dgms = result['dgms']

        # Count Betti numbers: features that are still alive at the end
        # (death == inf means still alive)
        inf = float('inf')
        betti_0 = sum(1 for b, d in dgms[0] if d == inf)
        betti_1 = sum(1 for b, d in dgms[1] if d == inf) if len(dgms) > 1 else 0

        # Persistence diagram: all finite-lifetime features
        all_features = []
        for dim, dgm in enumerate(dgms):
            for b, d in dgm:
                persistence = (d - b) if d != inf else float(max(d if d != inf else 0 for b, d in dgm if d != inf) + 1)
                all_features.append({
                    'dim': dim,
                    'birth': float(b),
                    'death': float(d) if d != inf else None,
                    'persistence': float(d - b) if d != inf else None,
                })

        # Find longest-lived finite feature
        finite = [f for f in all_features if f['persistence'] is not None]
        longest = max(finite, key=lambda f: f['persistence']) if finite else None

        sessions_out.append({
            'date': date,
            'date_index': sess['date_index'],
            'turn_count': sess['turn_count'],
            'betti_0': int(betti_0),
            'betti_1': int(betti_1),
            'betti_2': 0,  # not computed (slow)
            'persistence_diagram': all_features[:50],  # cap for JSON size
            'longest_lived_feature': longest,
        })
        print(f"  {date}: b0={betti_0}, b1={betti_1}, features={len(all_features)}")

    return {'sessions': sessions_out}


# ── Analysis 11: Bridging Concepts ────────────────────────────────────────────

def analysis_11_bridging_concepts(turns, embeddings, turn_idx_map,
                                   corpus_vecs, corpus_meta, session_defs):
    print("[A11] Bridging Concepts...")
    n_corpus = len(corpus_vecs)
    n_sessions = len(session_defs['sessions'])
    date_to_idx = {s['date']: s['date_index'] for s in session_defs['sessions']}

    # Normalize corpus vecs
    corp_norms = np.linalg.norm(corpus_vecs, axis=1, keepdims=True) + 1e-9
    corp_normed = corpus_vecs / corp_norms

    # For each turn, find nearest corpus doc
    nearest_corpus = {}   # turn_num -> corpus_idx
    total_refs = np.zeros(n_corpus, dtype=int)
    session_refs = [set() for _ in range(n_corpus)]  # corpus_idx -> set of date_indices

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

    # Build document bridge scores
    documents = []
    for i, meta in enumerate(corpus_meta):
        if i >= n_corpus:
            break
        n_sessions_ref = len(session_refs[i])
        bridge_score = n_sessions_ref / n_sessions if n_sessions > 0 else 0.0
        peak_session = -1
        if session_refs[i]:
            # Find session where this doc is most referenced
            counts_by_session = Counter(
                t['date']
                for t in turns
                if nearest_corpus.get(t['turn']) == i
            )
            peak_date = max(counts_by_session, key=counts_by_session.get)
            peak_session = date_to_idx.get(peak_date, -1)

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

    # Categorize
    universal = [d for d in documents if d['bridge_score'] > 0.6]
    phase     = [d for d in documents if 0.3 <= d['bridge_score'] <= 0.6]
    local     = [d for d in documents if d['bridge_score'] < 0.3]

    print(f"  Universal anchors: {len(universal)}, Phase anchors: {len(phase)}, Local: {len(local)}")
    for d in documents[:5]:
        print(f"  {d['name']}: bridge={d['bridge_score']:.2f}, {d['session_count']} sessions")

    return {
        'documents': documents,
        'categories': {
            'universal_anchors': [d['name'] for d in universal],
            'phase_anchors': [d['name'] for d in phase],
            'local_features': [d['name'] for d in local],
        },
        'nearest_corpus_by_turn': {
            str(k): v for k, v in list(nearest_corpus.items())[:100]  # sample for JSON
        },
    }


# ── Analysis 15: Signal Density ───────────────────────────────────────────────

def analysis_15_signal_density(turns, embeddings, turn_idx_map, session_defs,
                                window=20, spike_sigma=2.0):
    print("[A15] Signal Density (novelty)...")
    # embeddings are already normalized unit vectors
    # novelty[n] = 1 - max(embeddings[:n] @ embeddings[n])

    ordered = [t for t in turns if t['turn'] in turn_idx_map]
    n = len(ordered)
    ordered_embs = np.array([embeddings[turn_idx_map[t['turn']]] for t in ordered],
                             dtype=np.float32)

    novelty = np.zeros(n, dtype=np.float32)
    novelty[0] = 1.0

    print(f"  Computing novelty for {n} turns (vectorized)...")
    for i in range(1, n):
        # cosine similarity with all previous turns (both normalized -> dot product)
        sims = ordered_embs[:i] @ ordered_embs[i]
        novelty[i] = float(1.0 - sims.max())

    # Smoothed novelty
    half_w = window // 2
    smoothed = np.zeros(n, dtype=np.float32)
    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        smoothed[i] = novelty[start:end].mean()

    mean_nov = float(novelty.mean())
    std_nov  = float(novelty.std())
    thresh   = mean_nov + spike_sigma * std_nov

    # Identify spikes
    spikes = []
    for i, t in enumerate(ordered):
        if novelty[i] >= thresh:
            spikes.append({
                'turn': t['turn'],
                'speaker': t['speaker'],
                'date': t['date'],
                'novelty': float(novelty[i]),
                'smoothed_novelty': float(smoothed[i]),
                'text_preview': t['content'][:120],
            })

    spikes.sort(key=lambda s: -s['novelty'])

    # Per-speaker stats
    jake_nov = [novelty[i] for i, t in enumerate(ordered) if t['speaker'] == 'Jake']
    opus_nov = [novelty[i] for i, t in enumerate(ordered) if t['speaker'] == 'Opus']

    # Per-session average novelty
    date_to_idx_map = {s['date']: s['date_index'] for s in session_defs['sessions']}
    by_date = defaultdict(list)
    for i, t in enumerate(ordered):
        by_date[t['date']].append((i, novelty[i]))

    by_session = []
    for sess in session_defs['sessions']:
        date = sess['date']
        sess_entries = by_date[date]
        if not sess_entries:
            continue
        sess_novs = [n for _, n in sess_entries]
        jake_novs = [novelty[i] for i, t in enumerate(ordered)
                     if t['date'] == date and t['speaker'] == 'Jake']
        opus_novs = [novelty[i] for i, t in enumerate(ordered)
                     if t['date'] == date and t['speaker'] == 'Opus']
        sess_spikes = sum(1 for n in sess_novs if n >= thresh)
        by_session.append({
            'date': date,
            'date_index': sess['date_index'],
            'mean_novelty': float(np.mean(sess_novs)),
            'max_novelty': float(np.max(sess_novs)),
            'spike_count': sess_spikes,
            'jake_novelty': float(np.mean(jake_novs)) if jake_novs else 0.0,
            'opus_novelty': float(np.mean(opus_novs)) if opus_novs else 0.0,
        })

    # Build turn-level output (summary fields only, not full content)
    turns_out = [
        {
            'turn': ordered[i]['turn'],
            'speaker': ordered[i]['speaker'],
            'date': ordered[i]['date'],
            'novelty': float(novelty[i]),
            'smoothed_novelty': float(smoothed[i]),
        }
        for i in range(n)
    ]

    highest = max(turns_out, key=lambda t: t['novelty'])
    lowest  = min(turns_out, key=lambda t: t['novelty'])

    print(f"  Mean novelty: {mean_nov:.4f}, Spikes (>{thresh:.4f}): {len(spikes)}")
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
    """RankMe + alpha-ReQ per session. Li et al. (2025), Google Research / McGill.

    RankMe = exp(Shannon entropy of normalized eigenspectrum) — high = spread across
    many dimensions (entropy-seeking), low = concentrated (compression-seeking).
    alpha-ReQ = power-law decay exponent of eigenspectrum — high alpha = steep decay
    (anisotropic), low alpha = flat (isotropic).
    """
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
                'date': date,
                'date_index': sess['date_index'],
                'n_turns': len(sess_turn_idxs),
                'rankme': None,
                'alpha_req': None,
                'top_eigenvalue_ratio': None,
                'effective_dimensions': None,
            })
            continue

        # Covariance on GPU if available, eigendecomposition back on CPU
        X = _to_gpu(embeddings[sess_turn_idxs].astype(np.float64))
        xp = cp if _GPU else np
        X = X - X.mean(axis=0)
        cov = _to_cpu((X.T @ X) / len(X))  # eigenvalsh needs scipy/numpy
        X = None  # free GPU memory
        eigvals = np.linalg.eigvalsh(cov)[::-1]  # descending
        eigvals = np.maximum(eigvals, 0.0)
        total = eigvals.sum() + 1e-12

        # RankMe: exp(-sum(p_i * log(p_i)))
        probs = eigvals / total
        probs_nz = probs[probs > 1e-12]
        rankme = float(np.exp(-np.sum(probs_nz * np.log(probs_nz))))

        # alpha-ReQ: slope of log-log eigenspectrum (power-law decay exponent)
        K = min(50, len(eigvals))
        ranks = np.arange(1, K + 1, dtype=np.float64)
        lam = eigvals[:K] + 1e-12
        alpha_req = float(-np.polyfit(np.log(ranks), np.log(lam), 1)[0])

        # Top eigenvalue dominance ratio
        top_ratio = float(eigvals[0] / total)

        # Effective dimensionality: how many eigenvalues cover 90% of variance
        cumsum = np.cumsum(eigvals)
        n_eff = int(np.searchsorted(cumsum, 0.9 * total) + 1)

        entry = {
            'date': date,
            'date_index': sess['date_index'],
            'n_turns': len(sess_turn_idxs),
            'rankme': rankme,
            'alpha_req': alpha_req,
            'top_eigenvalue_ratio': top_ratio,
            'effective_dimensions': n_eff,
        }
        sessions_out.append(entry)

        # Detect phase transitions: RankMe change > 20% between consecutive sessions
        if prev_rankme is not None:
            delta = rankme - prev_rankme
            rel = delta / (prev_rankme + 1e-9)
            if abs(rel) > 0.2:
                phase_transitions.append({
                    'date': date,
                    'date_index': sess['date_index'],
                    'metric': 'rankme',
                    'direction': 'rise' if delta > 0 else 'drop',
                    'magnitude': float(abs(rel)),
                    'from_rankme': float(prev_rankme),
                    'to_rankme': float(rankme),
                })
        prev_rankme = rankme

    n_valid = sum(1 for s in sessions_out if s['rankme'] is not None)
    print(f"  {n_valid} sessions analyzed, {len(phase_transitions)} phase transitions")
    return {
        'sessions': sessions_out,
        'phase_transitions': phase_transitions,
    }


# ── Analysis 2A: Trajectory Tangling ──────────────────────────────────────────

def analysis_2a_trajectory_tangling(turns, embeddings, turn_idx_map, session_defs,
                                     spike_sigma=2.0):
    """Trajectory tangling per Russo et al. (2018), Neuron 97:953-966.

    Q(t) = max_{t'!=t} ||d(t) - d(t')||^2 / (||e(t) - e(t')||^2 + eps)
    where d(t) = e(t+1) - e(t) is the derivative (velocity vector).

    High Q(t): this state can lead to very different next states (tangled).
    Low Q(t): similar states lead to similar next states (smooth dynamics).
    Maps to our vocabulary: high-tangling moments = off-map moments.
    """
    print("[A2A] Trajectory Tangling (Russo et al. 2018)...")

    ordered = sorted(turns, key=lambda t: t['turn'])
    ordered_turns = [t for t in ordered if t['turn'] in turn_idx_map]
    ordered_idxs = [turn_idx_map[t['turn']] for t in ordered_turns]

    if len(ordered_idxs) < 3:
        return {'turns': [], 'high_tangling_moments': [], 'mean_tangling': 0.0,
                'std_tangling': 0.0, 'threshold': 0.0,
                'tangling_by_session': [], 'tangling_by_speaker': {}}

    xp = cp if _GPU else np  # use cupy if available, numpy otherwise
    E = _to_gpu(embeddings[ordered_idxs].astype(np.float64))  # (n, 768) on GPU/CPU
    n = int(E.shape[0])

    # Derivatives: d[i] = e[i+1] - e[i]
    D = E[1:] - E[:-1]      # (n-1, 768)
    E_base = E[:-1]          # (n-1, 768) — start states matching each derivative
    m = n - 1

    mem_mb = m ** 2 * 8 // 1_000_000
    device = "GPU" if _GPU else "CPU"
    print(f"  Building {m}x{m} tangling matrices ({mem_mb} MB) on {device}...")

    # ||d(t) - d(t')||^2 via dot product expansion
    d_sq = xp.sum(D ** 2, axis=1)         # (m,)
    d_dot = D @ D.T                        # (m, m)
    d_diff_sq = d_sq[:, None] + d_sq[None, :] - 2 * d_dot
    d_diff_sq = xp.maximum(d_diff_sq, 0.0)

    # ||e(t) - e(t')||^2
    e_sq = xp.sum(E_base ** 2, axis=1)    # (m,)
    e_dot = E_base @ E_base.T             # (m, m)
    e_diff_sq = e_sq[:, None] + e_sq[None, :] - 2 * e_dot
    e_diff_sq = xp.maximum(e_diff_sq, 0.0)

    # Regularization: 1% of mean state distance squared
    eps = 0.01 * float(e_diff_sq.mean()) + 1e-9

    ratio = d_diff_sq / (e_diff_sq + eps)
    xp.fill_diagonal(ratio, 0.0)
    Q = _to_cpu(ratio.max(axis=1)).astype(np.float32)  # back to CPU numpy (m,)
    del ratio, d_diff_sq, e_diff_sq, d_dot, e_dot  # free GPU/CPU memory

    mean_Q = float(Q.mean())
    std_Q = float(Q.std())
    thresh = mean_Q + spike_sigma * std_Q

    turns_out = []
    by_session = defaultdict(list)
    jake_Q, opus_Q = [], []

    for i, t in enumerate(ordered_turns[:-1]):  # length matches D / Q
        q_val = float(Q[i])
        entry = {
            'turn': t['turn'],
            'speaker': t['speaker'],
            'date': t.get('date', 'unknown'),
            'tangling': q_val,
        }
        turns_out.append(entry)
        by_session[t.get('date', 'unknown')].append(q_val)
        if t['speaker'] == 'Jake':
            jake_Q.append(q_val)
        else:
            opus_Q.append(q_val)

    high_tangling = sorted(
        [e for e in turns_out if e['tangling'] >= thresh],
        key=lambda x: -x['tangling']
    )[:30]

    session_tangling = []
    for sess in session_defs['sessions']:
        vals = by_session.get(sess['date'], [])
        if vals:
            session_tangling.append({
                'date': sess['date'],
                'date_index': sess['date_index'],
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
    print("=== FULL CHATLOG ANALYSIS SUITE ===\n")

    # Load data
    print("[LOAD] Loading turns...")
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"  {len(turns)} turns loaded")

    print("[LOAD] Loading embeddings...")
    embeddings = np.load(str(EMBEDDINGS))
    print(f"  Shape: {embeddings.shape}")

    if len(embeddings) != len(turns):
        print(f"  WARNING: embedding count {len(embeddings)} != turn count {len(turns)}")
        # Truncate to min
        n = min(len(embeddings), len(turns))
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

    # Build turn index map: turn_number -> embedding row
    # (turns are in order, so index i in turns array corresponds to embeddings[i])
    turn_idx_map = {t['turn']: i for i, t in enumerate(turns)}

    # Build joint UMAP
    print("\n[UMAP] Building joint 3D projection (corpus + all turns)...")
    corpus_coords, turn_coords = build_joint_umap(corpus_vecs, embeddings)
    print(f"  Corpus coords: {corpus_coords.shape}")
    print(f"  Turn coords: {turn_coords.shape}")

    # Save UMAP coords
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
            for i in range(len(corpus_coords))
            if i < len(corpus_meta)
        ],
        'turns': [
            {
                'turn': t['turn'],
                'speaker': t['speaker'],
                'date': t['date'],
                'date_index': t.get('date_index', -1),
                'word_count': t['word_count'],
                'umap_x': float(turn_coords[i, 0]),
                'umap_y': float(turn_coords[i, 1]),
                'umap_z': float(turn_coords[i, 2]),
                'content_preview': t['content'][:200],
            }
            for i, t in enumerate(turns)
        ],
    }
    with open(OUT_UMAP, 'w', encoding='utf-8') as f:
        json.dump(umap_data, f, ensure_ascii=False)
    print(f"  Saved: {OUT_UMAP}")

    # Run analyses in order
    print()

    # Analysis 1
    s1 = analysis_1_session_signatures(turns, embeddings, session_defs, centroids,
                                        corpus_coords, turn_coords, turn_idx_map)
    with open(OUT_S1, 'w', encoding='utf-8') as f:
        json.dump(s1, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S1} ({len(s1['sessions'])} sessions)")

    # Analysis 2
    s2 = analysis_2_recurrence(turns, embeddings, turn_idx_map, session_defs)
    with open(OUT_S2, 'w', encoding='utf-8') as f:
        json.dump(s2, f, ensure_ascii=False)
    print(f"  Saved: {OUT_S2} ({s2['n_blocks']}x{s2['n_blocks']} blocks, "
          f"{len(s2['high_recurrence_pairs'])} high-recurrence pairs)")

    # Analysis 3
    s3 = analysis_3_speaker_coupling(turns, embeddings, turn_idx_map)
    with open(OUT_S3, 'w', encoding='utf-8') as f:
        json.dump(s3, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S3} ({len(s3['pairs'])} pairs, "
          f"mean dist={s3.get('mean_distance', 0):.3f})")

    # Analysis 4
    s4 = analysis_4_sliding_window(turns, embeddings, turn_idx_map, centroids, turn_coords)
    with open(OUT_S4, 'w', encoding='utf-8') as f:
        json.dump(s4, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S4} ({s4['n_points']} window points)")

    # Analysis 5
    s5 = analysis_5_information_flow(turns, embeddings, turn_idx_map)
    with open(OUT_S5, 'w', encoding='utf-8') as f:
        json.dump(s5, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S5} (Jake leads {s5['jake_lead_percentage']:.0f}%, "
          f"Opus leads {s5['opus_lead_percentage']:.0f}%)")

    # Analysis 6
    s6 = analysis_6_entropy_trace(turns, embeddings, turn_idx_map, centroids)
    with open(OUT_S6, 'w', encoding='utf-8') as f:
        json.dump(s6, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S6} (mean entropy={s6['mean_entropy']:.3f}, "
          f"max={s6['max_theoretical_entropy']:.3f})")

    # Analysis 7
    s7 = analysis_7_cumulative_drift(turns, embeddings, turn_idx_map)
    with open(OUT_S7, 'w', encoding='utf-8') as f:
        json.dump(s7, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S7} (Jake total={s7['total_jake_distance']:.2f}, "
          f"Opus total={s7['total_opus_distance']:.2f})")

    # Analysis 8
    s8 = analysis_8_markov(turns, embeddings, turn_idx_map, centroids)
    with open(OUT_S8, 'w', encoding='utf-8') as f:
        json.dump(s8, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S8} (self-transition rate: {s8['full']['self_transition_rate']:.2f})")

    # Analysis 9 (uses Analysis 4 output)
    s9 = analysis_9_phase_space(s4['points'])
    with open(OUT_S9, 'w', encoding='utf-8') as f:
        json.dump(s9, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S9}")

    # Analysis 10: Persistent Homology
    s10 = analysis_10_persistent_homology(turns, embeddings, turn_idx_map, session_defs)
    with open(OUT_S10, 'w', encoding='utf-8') as f:
        json.dump(s10, f, ensure_ascii=False, indent=2)
    b0_mean = sum(s.get('betti_0',0) for s in s10['sessions']) / max(len(s10['sessions']),1)
    b1_mean = sum(s.get('betti_1',0) for s in s10['sessions']) / max(len(s10['sessions']),1)
    print(f"  Saved: {OUT_S10} (mean b0={b0_mean:.1f}, mean b1={b1_mean:.1f})")

    # Analysis 11: Bridging Concepts
    s11 = analysis_11_bridging_concepts(turns, embeddings, turn_idx_map,
                                         corpus_vecs, corpus_meta, session_defs)
    with open(OUT_S11, 'w', encoding='utf-8') as f:
        json.dump(s11, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S11} ({len(s11['categories']['universal_anchors'])} universal anchors)")

    # Analysis 15: Signal Density
    s15 = analysis_15_signal_density(turns, embeddings, turn_idx_map, session_defs)
    with open(OUT_S15, 'w', encoding='utf-8') as f:
        json.dump(s15, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S15} ({len(s15['novelty_spikes'])} spikes)")

    # Analysis 1A: Spectral Phases (RankMe + alpha-ReQ)
    s1a = analysis_1a_spectral_phases(turns, embeddings, turn_idx_map, session_defs)
    with open(OUT_S1A, 'w', encoding='utf-8') as f:
        json.dump(s1a, f, ensure_ascii=False, indent=2)
    n_transitions = len(s1a['phase_transitions'])
    print(f"  Saved: {OUT_S1A} ({n_transitions} phase transitions)")

    # Analysis 2A: Trajectory Tangling
    s2a = analysis_2a_trajectory_tangling(turns, embeddings, turn_idx_map, session_defs)
    with open(OUT_S2A, 'w', encoding='utf-8') as f:
        json.dump(s2a, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {OUT_S2A} (mean Q={s2a['mean_tangling']:.3f}, "
          f"{len(s2a['high_tangling_moments'])} high-tangling turns)")

    print("\n=== ALL ANALYSES COMPLETE ===")
    print(f"Files in {DATA}/:")
    for out in [OUT_UMAP, OUT_S1, OUT_S1A, OUT_S2, OUT_S2A, OUT_S3, OUT_S4, OUT_S5,
                OUT_S6, OUT_S7, OUT_S8, OUT_S9, OUT_S10, OUT_S11, OUT_S15]:
        if out.exists():
            size = out.stat().st_size // 1024
            print(f"  {out.name:<40} {size:>5} KB")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
