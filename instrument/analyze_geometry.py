#!/usr/bin/env python3
"""
analyze_geometry.py — Compute geometric metrics for the paper.

"The Space Between the Notes: Geometric Dynamics of Identity, Creativity,
and Convergence in Sustained Human-AI Collaboration"

Loads evolution_trajectories.json, evolution_embeddings.npy, centroids.json,
and chatlog_turns.json to compute:

1. Word count vs displacement correlation (verify paper claims r=-0.40, r=0.913)
2. Drift vectors and angles per family (verify SOUL -58 deg, essays +40 deg)
3. Wander ratios (arc / displacement) per family
4. Inter-family centroid distances over time (verify 7.3 -> 0.16)
5. Convergence rate fitting (linear vs exponential)
6. Superposition points — docs equidistant from >=2 domain centroids
7. Wallas vocabulary ratio from chatlog action titles
8. Nearest-neighbor evolution for 18 SOUL versions in 768-dim space
9. Chatlog domain distribution

Output: instrument/data/geometry_analysis.json + printed report
"""

import json
import math
import sys
import os
from pathlib import Path

import numpy as np
from scipy import stats
import faiss

# ── paths ──────────────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "instrument" / "data"

TRAJ_FILE   = DATA / "evolution_trajectories.json"
EMB_FILE    = DATA / "evolution_embeddings.npy"
CENT_FILE   = DATA / "centroids.json"
TURNS_FILE  = DATA / "chatlog_turns.json"
CORPUS_META = DATA / "corpus_metadata.json"
OUT_FILE    = DATA / "geometry_analysis.json"

# domain centroid layer (optimal from step 13)
CENTROID_LAYER = "18"
DOMAINS = ["operational", "philosophical", "reflective", "relational", "mixed"]


# ══════════════════════════════════════════════════════════════════════════════
# helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_data():
    with open(TRAJ_FILE, encoding="utf-8") as f:
        traj = json.load(f)
    embeddings = np.load(EMB_FILE)   # shape (46, 768)
    with open(CENT_FILE, encoding="utf-8") as f:
        cent_raw = json.load(f)
    with open(TURNS_FILE, encoding="utf-8") as f:
        turns = json.load(f)
    with open(CORPUS_META, encoding="utf-8") as f:
        corpus_meta = json.load(f)
    return traj, embeddings, cent_raw, turns, corpus_meta


def get_family(traj, name):
    return traj["families"][name]["versions"]


def xy(v):
    return v["x"], v["y"]


def dist2d(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def arc_length(versions):
    total = 0.0
    for i in range(len(versions)-1):
        total += dist2d(xy(versions[i]), xy(versions[i+1]))
    return total


def displacement(versions):
    return dist2d(xy(versions[0]), xy(versions[-1]))


def drift_vector(versions):
    """Overall drift as (dx, dy) from first to last."""
    x0, y0 = xy(versions[0])
    x1, y1 = xy(versions[-1])
    return x1 - x0, y1 - y0


def drift_angle_deg(versions):
    """Angle of drift in degrees, measured from positive-x axis."""
    dx, dy = drift_vector(versions)
    return math.degrees(math.atan2(dy, dx))


def centroid_2d(versions):
    xs = [v["x"] for v in versions]
    ys = [v["y"] for v in versions]
    return sum(xs)/len(xs), sum(ys)/len(ys)


def cosine_sim(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ══════════════════════════════════════════════════════════════════════════════
# 1. Word count vs displacement correlation
# ══════════════════════════════════════════════════════════════════════════════

def compute_wc_displacement_corr(traj):
    """
    For each consecutive step i->i+1 in a family:
      delta_wordcount = wc[i+1] - wc[i]
      step_displacement = dist2d(pos[i], pos[i+1])

    r < 0 means adding words locks position (SOUL)
    r > 0 means adding words shifts position (design_notes)
    """
    results = {}
    for family_name in ["soul", "essays", "design_notes"]:
        versions = get_family(traj, family_name)
        deltas_wc = []
        deltas_dist = []
        for i in range(len(versions)-1):
            dwc = versions[i+1]["word_count"] - versions[i]["word_count"]
            d = dist2d(xy(versions[i]), xy(versions[i+1]))
            deltas_wc.append(dwc)
            deltas_dist.append(d)
        if len(deltas_wc) < 3:
            results[family_name] = {"r": None, "p": None, "n": len(deltas_wc)}
            continue
        r, p = stats.pearsonr(deltas_wc, deltas_dist)
        results[family_name] = {
            "r": round(r, 4),
            "p": round(p, 4),
            "n": len(deltas_wc),
            "interpretation": (
                "adding words locks position (compression liberates)"
                if r < -0.2 else
                "adding words shifts position" if r > 0.2 else
                "no strong relationship"
            )
        }
        # also: absolute word count vs cumulative arc
        wcs = [v["word_count"] for v in versions]
        arc_cumulative = [0.0]
        for i in range(len(versions)-1):
            arc_cumulative.append(arc_cumulative[-1] + dist2d(xy(versions[i]), xy(versions[i+1])))
        r2, p2 = stats.pearsonr(wcs, arc_cumulative)
        results[family_name]["abs_wc_vs_arc_r"] = round(r2, 4)
        results[family_name]["abs_wc_vs_arc_p"] = round(p2, 4)
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 2. Drift vectors and angles
# ══════════════════════════════════════════════════════════════════════════════

def compute_drift(traj):
    results = {}
    for family_name in traj["families"]:
        versions = get_family(traj, family_name)
        dx, dy = drift_vector(versions)
        angle = drift_angle_deg(versions)
        arc = traj["families"][family_name]["total_arc_distance"]
        disp = displacement(versions)
        wander = arc / disp if disp > 0 else float("inf")
        results[family_name] = {
            "drift_dx": round(dx, 4),
            "drift_dy": round(dy, 4),
            "drift_angle_deg": round(angle, 2),
            "total_arc": round(arc, 4),
            "displacement": round(disp, 4),
            "wander_ratio": round(wander, 4),
            "start": {"x": round(versions[0]["x"], 4), "y": round(versions[0]["y"], 4)},
            "end": {"x": round(versions[-1]["x"], 4), "y": round(versions[-1]["y"], 4)},
        }
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 3. Inter-family centroid distances over time
# ══════════════════════════════════════════════════════════════════════════════

def compute_interfamily_distances(traj):
    """
    Track 2D centroid of each family at each unique date.
    Then measure distances between families across time.
    Returns per-date family centroids + soul<->essays, essays<->design_notes distances.
    """
    # collect all dates
    all_dates = sorted(set(
        v["date"]
        for fname in traj["families"]
        for v in traj["families"][fname]["versions"]
    ))

    family_names = ["soul", "essays", "design_notes"]

    # For each date, compute the centroid of versions <= that date
    def family_centroid_at_date(fname, date):
        versions = [v for v in get_family(traj, fname) if v["date"] <= date]
        if not versions:
            return None
        return centroid_2d(versions)

    timeline = []
    for date in all_dates:
        centroids_at_date = {}
        for fname in family_names:
            c = family_centroid_at_date(fname, date)
            if c:
                centroids_at_date[fname] = c

        entry = {"date": date, "centroids": {}}
        for fname, c in centroids_at_date.items():
            entry["centroids"][fname] = {"x": round(c[0], 4), "y": round(c[1], 4)}

        # pairwise distances between families present
        pairs = {}
        fnames_present = list(centroids_at_date.keys())
        for i in range(len(fnames_present)):
            for j in range(i+1, len(fnames_present)):
                fa, fb = fnames_present[i], fnames_present[j]
                d = dist2d(centroids_at_date[fa], centroids_at_date[fb])
                pairs[f"{fa}<->{fb}"] = round(d, 4)
        entry["pairwise_distances"] = pairs
        timeline.append(entry)

    # summarize: first date all three are present, last date
    full_dates = [e for e in timeline if len(e["centroids"]) == 3]
    convergence_summary = {}
    if full_dates:
        first = full_dates[0]
        last = full_dates[-1]
        convergence_summary = {
            "first_full_date": first["date"],
            "last_full_date": last["date"],
            "essays_design_distance_start": first["pairwise_distances"].get("essays<->design_notes"),
            "essays_design_distance_end": last["pairwise_distances"].get("essays<->design_notes"),
            "soul_essays_distance_start": first["pairwise_distances"].get("soul<->essays"),
            "soul_essays_distance_end": last["pairwise_distances"].get("soul<->essays"),
            "soul_design_distance_start": first["pairwise_distances"].get("soul<->design_notes"),
            "soul_design_distance_end": last["pairwise_distances"].get("soul<->design_notes"),
        }
    return {"timeline": timeline, "convergence_summary": convergence_summary}


# ══════════════════════════════════════════════════════════════════════════════
# 4. Convergence rate fitting
# ══════════════════════════════════════════════════════════════════════════════

def fit_convergence(interfamily):
    """
    Fit the essays<->design_notes distance over time.
    Try linear and exponential fits. Compare R².
    """
    timeline = interfamily["timeline"]
    pairs = [(e["date"], e["pairwise_distances"].get("essays<->design_notes"))
             for e in timeline if "essays<->design_notes" in e["pairwise_distances"]]
    if len(pairs) < 4:
        return {"error": "not enough data points"}

    # convert dates to ordinal index
    dates = [p[0] for p in pairs]
    dists = [p[1] for p in pairs]
    t = list(range(len(dates)))

    # linear fit
    slope, intercept, r_lin, p_lin, _ = stats.linregress(t, dists)
    r2_lin = r_lin**2

    # exponential fit: log(d) = a + b*t
    log_dists = np.log(np.array(dists) + 1e-9)
    slope_exp, intercept_exp, r_exp, p_exp, _ = stats.linregress(t, log_dists)
    r2_exp = r_exp**2

    return {
        "dates": dates,
        "distances": dists,
        "linear_fit": {
            "slope": round(slope, 4),
            "intercept": round(intercept, 4),
            "r2": round(r2_lin, 4),
            "p": round(p_lin, 4),
        },
        "exponential_fit": {
            "decay_rate": round(slope_exp, 4),
            "log_intercept": round(intercept_exp, 4),
            "r2": round(r2_exp, 4),
            "p": round(p_exp, 4),
            "half_life_steps": round(-math.log(2)/slope_exp, 2) if slope_exp < 0 else None,
        },
        "better_fit": "exponential" if r2_exp > r2_lin else "linear",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. Superposition points — equidistant from >=2 domain centroids
# ══════════════════════════════════════════════════════════════════════════════

def compute_superposition(embeddings, cent_raw, traj, corpus_meta, epsilon=0.05):
    """
    Centroids in cent_raw are 1024-dim (llama.cpp Qwen3 activations),
    incompatible with 768-dim nomic embeddings.

    Instead: compute per-document-type centroids from the 46 corpus FAISS vectors
    (also 768-dim nomic), then check each evolution doc for equidistance between types.
    Types present: essay, design_note, analysis, journal, letter
    """
    corpus_faiss_path = DATA / "corpus.faiss"
    index = faiss.read_index(str(corpus_faiss_path))
    n_corpus = index.ntotal
    corpus_vecs = np.array([index.reconstruct(i) for i in range(n_corpus)], dtype=np.float32)

    # group corpus by document_type
    type_to_vecs = {}
    for meta in corpus_meta:
        fid = meta["faiss_id"]
        if fid >= n_corpus:
            continue
        dtype = meta.get("document_type", "other")
        if dtype not in type_to_vecs:
            type_to_vecs[dtype] = []
        type_to_vecs[dtype].append(corpus_vecs[fid])

    # compute L2-normalized centroids per document type
    type_centroids = {}
    for dtype, vecs in type_to_vecs.items():
        c = np.mean(vecs, axis=0).astype(np.float32)
        n = np.linalg.norm(c)
        type_centroids[dtype] = c / n if n > 0 else c

    doc_types = sorted(type_centroids.keys())

    # build ordered list of all evolution documents (must match embedding order)
    all_versions = []
    emb_idx = 0
    for family_name in ["soul", "essays", "design_notes", "soul_staging"]:
        for v in get_family(traj, family_name):
            all_versions.append({
                "family": family_name,
                "label": v.get("label", ""),
                "date": v["date"],
                "emb_idx": emb_idx,
                "x": v["x"],
                "y": v["y"],
            })
            emb_idx += 1

    results = []
    for doc in all_versions:
        vec = embeddings[doc["emb_idx"]].astype(np.float32)
        nv = np.linalg.norm(vec)
        vec_norm = vec / nv if nv > 0 else vec

        sims = {dtype: float(np.dot(vec_norm, type_centroids[dtype])) for dtype in doc_types}
        sorted_types = sorted(sims.items(), key=lambda x: -x[1])
        top1_type, top1_sim = sorted_types[0]
        top2_type, top2_sim = sorted_types[1]
        gap = top1_sim - top2_sim

        is_superposition = gap < epsilon
        results.append({
            "family": doc["family"],
            "label": doc["label"],
            "date": doc["date"],
            "x": round(doc["x"], 4),
            "y": round(doc["y"], 4),
            "type_sims": {d: round(s, 4) for d, s in sims.items()},
            "top1_type": top1_type,
            "top1_sim": round(top1_sim, 4),
            "top2_type": top2_type,
            "top2_sim": round(top2_sim, 4),
            "gap": round(gap, 4),
            "is_superposition": is_superposition,
        })

    superposition_docs = [r for r in results if r["is_superposition"]]
    return {
        "note": "Superposition in 768-dim nomic space vs per-document-type corpus centroids",
        "doc_types": doc_types,
        "epsilon": epsilon,
        "all_docs": results,
        "superposition_docs": superposition_docs,
        "superposition_count": len(superposition_docs),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 6. Wallas vocabulary signature from chatlog action titles
# ══════════════════════════════════════════════════════════════════════════════

# Past-tense verbs: action (operational) vs contemplative (Wallas preparation/incubation)
CONTEMPLATIVE_VERBS = {
    "deliberated", "weighed", "examined", "considered", "reflected",
    "assessed", "evaluated", "questioned", "explored", "wondered",
    "investigated", "analyzed", "analyzed", "probed", "contemplated",
    "scrutinized", "reviewed", "surveyed", "observed", "noted",
    "pondered", "charted", "mapped", "traced", "compared",
    "reasoned", "studied", "diagnosed",
}

ACTION_VERBS = {
    "built", "wrote", "created", "deployed", "implemented", "fixed",
    "added", "updated", "refactored", "resolved", "extended",
    "integrated", "installed", "patched", "corrected", "ran",
    "executed", "confirmed", "verified", "completed", "finished",
    "established", "generated", "computed", "embedded", "extracted",
    "copied", "constructed", "loaded", "parsed", "produced",
    "exported", "committed", "pushed", "moved", "renamed", "deleted",
}

SYNTHESIS_VERBS = {
    "synthesized", "designed", "architected", "formalized", "distilled",
    "identified", "discovered", "found", "revealed", "demonstrated",
    "validated", "showed", "confirmed", "connected", "converged",
    "unified", "recognized", "framed", "crystallized",
}


def classify_turn_wallas(title: str) -> str:
    words = set(title.lower().split())
    # check synthesis first (highest signal)
    if words & SYNTHESIS_VERBS:
        return "synthesis"
    if words & CONTEMPLATIVE_VERBS:
        return "contemplative"
    if words & ACTION_VERBS:
        return "action"
    return "other"


def compute_wallas_signature(turns):
    """
    Classify each turn's action_title by Wallas stage.
    Also compute rolling 20-turn entropy of stage distribution.
    """
    classified = []
    for turn in turns:
        title = turn.get("action_title", "")
        stage = classify_turn_wallas(title)
        classified.append({
            "turn_index": turn["turn_index"],
            "date": turn.get("date", ""),
            "action_title": title,
            "wallas_stage": stage,
            "char_count": turn.get("char_count", 0),
        })

    # count distribution
    counts = {"synthesis": 0, "contemplative": 0, "action": 0, "other": 0}
    for c in classified:
        counts[c["wallas_stage"]] += 1
    total = len(classified)

    # transitions: contemplative -> synthesis within next 5 turns?
    transitions = []
    for i, c in enumerate(classified):
        if c["wallas_stage"] == "contemplative":
            window = classified[i+1:i+6]
            next_synthesis = next((j for j, w in enumerate(window) if w["wallas_stage"] == "synthesis"), None)
            transitions.append({
                "contemplative_turn": i,
                "synthesis_in_next_5": next_synthesis is not None,
                "synthesis_lag": next_synthesis,
            })

    synthesis_after_contemp = sum(1 for t in transitions if t["synthesis_in_next_5"])
    total_contemp = len(transitions)

    # rolling 20-turn window: ratio of contemplative
    window_size = 20
    rolling = []
    for i in range(len(classified) - window_size + 1):
        window = classified[i:i+window_size]
        contemp_count = sum(1 for w in window if w["wallas_stage"] == "contemplative")
        synth_count = sum(1 for w in window if w["wallas_stage"] == "synthesis")
        rolling.append({
            "start_turn": i,
            "contemp_ratio": round(contemp_count / window_size, 3),
            "synth_ratio": round(synth_count / window_size, 3),
        })

    # find peaks in contemplative ratio
    contemp_ratios = [r["contemp_ratio"] for r in rolling]
    if contemp_ratios:
        max_contemp_ratio = max(contemp_ratios)
        max_contemp_turn = contemp_ratios.index(max_contemp_ratio)
    else:
        max_contemp_ratio = 0
        max_contemp_turn = 0

    return {
        "total_turns": total,
        "stage_counts": counts,
        "stage_fractions": {k: round(v/total, 4) for k, v in counts.items()},
        "contemplative_to_synthesis_transitions": {
            "total_contemplative_turns": total_contemp,
            "synthesis_within_5_turns": synthesis_after_contemp,
            "hit_rate": round(synthesis_after_contemp / total_contemp, 4) if total_contemp > 0 else 0,
        },
        "rolling_20_turn": {
            "max_contemplative_ratio": round(max_contemp_ratio, 4),
            "peak_at_turn": max_contemp_turn + window_size // 2,  # center of window
        },
        "classified_turns": classified,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 7. Nearest-neighbor evolution for 18 SOUL versions in 768-dim space
# ══════════════════════════════════════════════════════════════════════════════

def compute_soul_nn_768(embeddings, traj, corpus_meta):
    """
    For each SOUL version (embeddings[0:18]), find:
    - Cosine similarity to the previous version (sequential similarity)
    - Nearest corpus document (excluding SOUL family itself)
    - The domain that centroid is closest to
    """
    soul_versions = get_family(traj, "soul")
    n_soul = len(soul_versions)

    results = []
    for i, v in enumerate(soul_versions):
        vec = embeddings[i].astype(np.float32)
        nv = np.linalg.norm(vec)
        if nv > 0:
            vec_norm = vec / nv
        else:
            vec_norm = vec

        # sequential similarity
        seq_sim = None
        if i > 0:
            prev = embeddings[i-1].astype(np.float32)
            np_prev = np.linalg.norm(prev)
            if np_prev > 0:
                prev_norm = prev / np_prev
            else:
                prev_norm = prev
            seq_sim = round(float(np.dot(vec_norm, prev_norm)), 4)

        results.append({
            "version": v["version_label"],
            "date": v["date"],
            "label": v["label"],
            "word_count": v["word_count"],
            "x": round(v["x"], 4),
            "y": round(v["y"], 4),
            "sequential_cosine_sim": seq_sim,
        })

    # compute velocity: 1 - cosine_sim (how much did SOUL change step by step)
    # also flag big drops in similarity
    sims = [r["sequential_cosine_sim"] for r in results if r["sequential_cosine_sim"] is not None]
    if sims:
        mean_sim = round(float(np.mean(sims)), 4)
        min_sim = round(float(np.min(sims)), 4)
        min_sim_idx = sims.index(min_sim) + 1  # +1 because first has no sim
        max_sim = round(float(np.max(sims)), 4)

        # phase transitions: steps where similarity drops below mean - 1 stdev
        std_sim = float(np.std(sims))
        threshold = mean_sim - std_sim
        phase_transitions = []
        for i, r in enumerate(results):
            if r["sequential_cosine_sim"] is not None and r["sequential_cosine_sim"] < threshold:
                phase_transitions.append({
                    "step": i,
                    "version": r["version"],
                    "sim": r["sequential_cosine_sim"],
                    "label": r["label"],
                })
    else:
        mean_sim = min_sim = max_sim = 0
        min_sim_idx = 0
        phase_transitions = []

    return {
        "versions": results,
        "similarity_stats": {
            "mean": mean_sim,
            "min": min_sim,
            "min_at_step": min_sim_idx,
            "max": max_sim,
            "phase_transitions_below_mean_minus_1std": phase_transitions,
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# 8. Phase transition detection in SOUL trajectory
# ══════════════════════════════════════════════════════════════════════════════

def detect_phase_transitions(traj):
    """
    For each family, find steps where displacement is > mean + 1 stdev.
    These are phase transitions.
    """
    results = {}
    for family_name in traj["families"]:
        versions = get_family(traj, family_name)
        steps = []
        for i in range(len(versions)-1):
            d = dist2d(xy(versions[i]), xy(versions[i+1]))
            steps.append({
                "step": i,
                "from_version": versions[i].get("version_label", versions[i].get("label", f"idx{i}")),
                "to_version": versions[i+1].get("version_label", versions[i+1].get("label", f"idx{i+1}")),
                "from_date": versions[i]["date"],
                "to_date": versions[i+1]["date"],
                "displacement": round(d, 4),
                "word_count_change": versions[i+1]["word_count"] - versions[i]["word_count"],
            })

        if not steps:
            results[family_name] = {"steps": [], "transitions": []}
            continue

        displacements = [s["displacement"] for s in steps]
        mean_d = float(np.mean(displacements))
        std_d = float(np.std(displacements))
        threshold = mean_d + std_d

        transitions = [s for s in steps if s["displacement"] > threshold]

        results[family_name] = {
            "steps": steps,
            "mean_step": round(mean_d, 4),
            "std_step": round(std_d, 4),
            "threshold_1std": round(threshold, 4),
            "transitions": transitions,
        }
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 9. Corpus document positions for cross-reference
# ══════════════════════════════════════════════════════════════════════════════

def load_corpus_positions(traj):
    """Extract 2D positions of all evolution documents for cross-family analysis."""
    all_positions = {}
    for family_name in traj["families"]:
        positions = [(v["x"], v["y"]) for v in get_family(traj, family_name)]
        all_positions[family_name] = positions
    return all_positions


# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("[analyze_geometry] Loading data...")
    traj, embeddings, cent_raw, turns, corpus_meta = load_data()

    print(f"  evolution embeddings shape: {embeddings.shape}")
    print(f"  chatlog turns: {len(turns)}")
    print(f"  corpus docs: {len(corpus_meta)}")

    print("\n[1] Word count vs displacement correlation...")
    wc_corr = compute_wc_displacement_corr(traj)
    for fam, r in wc_corr.items():
        print(f"  {fam}: r={r['r']}  p={r['p']}  n={r['n']}  [{r.get('interpretation','')}]")
        print(f"         abs_wc_vs_arc_r={r.get('abs_wc_vs_arc_r')}  p={r.get('abs_wc_vs_arc_p')}")

    print("\n[2] Drift vectors and wander ratios...")
    drift = compute_drift(traj)
    for fam, d in drift.items():
        print(f"  {fam}: angle={d['drift_angle_deg']}°  arc={d['total_arc']}  disp={d['displacement']}  wander={d['wander_ratio']}")

    print("\n[3] Inter-family distances over time...")
    interfamily = compute_interfamily_distances(traj)
    cs = interfamily["convergence_summary"]
    if cs:
        print(f"  First full date: {cs['first_full_date']}")
        print(f"  Last full date: {cs['last_full_date']}")
        print(f"  essays<->design_notes: {cs['essays_design_distance_start']} -> {cs['essays_design_distance_end']}")
        print(f"  soul<->essays: {cs['soul_essays_distance_start']} -> {cs['soul_essays_distance_end']}")
        print(f"  soul<->design_notes: {cs['soul_design_distance_start']} -> {cs['soul_design_distance_end']}")

    print("\n[4] Convergence rate fitting...")
    conv_fit = fit_convergence(interfamily)
    if "error" not in conv_fit:
        print(f"  Linear fit:      R²={conv_fit['linear_fit']['r2']}  slope={conv_fit['linear_fit']['slope']}")
        print(f"  Exponential fit: R²={conv_fit['exponential_fit']['r2']}  decay={conv_fit['exponential_fit']['decay_rate']}")
        print(f"  Better fit: {conv_fit['better_fit']}")
        if conv_fit["exponential_fit"]["half_life_steps"]:
            print(f"  Half-life: {conv_fit['exponential_fit']['half_life_steps']} steps")

    print("\n[5] Superposition points (768-dim, epsilon=0.05)...")
    superposition = compute_superposition(embeddings, cent_raw, traj, corpus_meta, epsilon=0.05)
    print(f"  Total superposition docs: {superposition['superposition_count']}")
    for doc in superposition["superposition_docs"]:
        print(f"    {doc['family']:15s} {doc['label']:30s} gap={doc['gap']:.4f}  top1={doc['top1_type']}({doc['top1_sim']:.3f}) top2={doc['top2_type']}({doc['top2_sim']:.3f})")

    print("\n[6] Wallas vocabulary signature...")
    wallas = compute_wallas_signature(turns)
    print(f"  Stage distribution: {wallas['stage_counts']}")
    print(f"  Fractions: {wallas['stage_fractions']}")
    print(f"  Contemplative->Synthesis transitions: {wallas['contemplative_to_synthesis_transitions']}")
    print(f"  Peak contemplative window: turn {wallas['rolling_20_turn']['peak_at_turn']} (ratio={wallas['rolling_20_turn']['max_contemplative_ratio']})")

    print("\n[7] SOUL 768-dim nearest-neighbor evolution...")
    soul_nn = compute_soul_nn_768(embeddings, traj, corpus_meta)
    stats_block = soul_nn["similarity_stats"]
    print(f"  Sequential cosine similarity: mean={stats_block['mean']}  min={stats_block['min']} (at step {stats_block['min_at_step']})  max={stats_block['max']}")
    print(f"  Phase transitions (sim < mean-1std):")
    for pt in stats_block["phase_transitions_below_mean_minus_1std"]:
        print(f"    step {pt['step']:2d}: {pt['version']} ({pt['label']})  sim={pt['sim']}")

    print("\n[8] Phase transition detection (2D displacement)...")
    transitions = detect_phase_transitions(traj)
    for fam, t in transitions.items():
        print(f"  {fam}: threshold={t.get('threshold_1std')}  transitions:")
        for step in t.get("transitions", []):
            print(f"    {step['from_version']}->{step['to_version']}  disp={step['displacement']}  dwc={step['word_count_change']}")

    # ── assemble output ─────────────────────────────────────────────────────
    output = {
        "generated": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "description": "Geometric analysis supporting 'The Space Between the Notes' paper",
        "analysis": {
            "wc_displacement_correlation": wc_corr,
            "drift_and_wander": drift,
            "interfamily_distances": interfamily,
            "convergence_fit": conv_fit,
            "superposition": {
                "epsilon": superposition["epsilon"],
                "superposition_count": superposition["superposition_count"],
                "superposition_docs": superposition["superposition_docs"],
                "all_docs_summary": [
                    {k: v for k, v in d.items() if k != "domain_sims"}
                    for d in superposition["all_docs"]
                ],
            },
            "wallas_signature": {
                k: v for k, v in wallas.items()
                if k != "classified_turns"  # omit 923-entry list from summary
            },
            "wallas_classified_turns": wallas["classified_turns"],
            "soul_sequential_similarity": soul_nn,
            "phase_transitions_2d": transitions,
        }
    }

    with open(OUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[analyze_geometry] Written to {OUT_FILE}")


if __name__ == "__main__":
    main()
