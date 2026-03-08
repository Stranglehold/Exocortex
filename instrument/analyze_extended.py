#!/usr/bin/env python3
"""
analyze_extended.py — Extended geometric analysis for "The Space Between the Notes"

Opus priorities:
1. Nearest-neighbor evolution in 768-dim space (convergence verification, UMAP-independent)
2. Wallas rolling window cross-correlation (quantify intimation->illumination lag)
3. Super-cooling threshold for Finding 6 (word count at which compression liberates)
4. Chatlog domain distribution = Finding 11 (conversation topology against corpus)
   (uses 923x768 chatlog_embeddings.npy and corpus.faiss)

Output: instrument/data/extended_analysis.json
"""

import json
import math
import sys
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np
from scipy import stats
import faiss

DATA = Path(__file__).resolve().parent.parent / "instrument" / "data"

CORPUS_FAISS   = DATA / "corpus.faiss"
CORPUS_META    = DATA / "corpus_metadata.json"
CHATLOG_EMB    = DATA / "chatlog_embeddings.npy"
CHATLOG_TRAJ   = DATA / "chatlog_trajectory.json"
CHATLOG_TURNS  = DATA / "chatlog_turns.json"
EVOLUTION_EMB  = DATA / "evolution_embeddings.npy"
EVOLUTION_TRAJ = DATA / "evolution_trajectories.json"
GEO_ANALYSIS   = DATA / "geometry_analysis.json"
OUT_FILE       = DATA / "extended_analysis.json"

TOP_K = 5  # neighbors to retrieve


# ══════════════════════════════════════════════════════════════════════════════
# load helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_all():
    index = faiss.read_index(str(CORPUS_FAISS))
    with open(CORPUS_META, encoding="utf-8") as f:
        corpus_meta = json.load(f)
    chatlog_emb = np.load(str(CHATLOG_EMB)).astype(np.float32)  # (923, 768)
    with open(CHATLOG_TRAJ, encoding="utf-8") as f:
        chatlog_traj = json.load(f)
    with open(CHATLOG_TURNS, encoding="utf-8") as f:
        chatlog_turns = json.load(f)
    evo_emb = np.load(str(EVOLUTION_EMB)).astype(np.float32)    # (46, 768)
    with open(EVOLUTION_TRAJ, encoding="utf-8") as f:
        evo_traj = json.load(f)
    with open(GEO_ANALYSIS, encoding="utf-8") as f:
        geo = json.load(f)
    return index, corpus_meta, chatlog_emb, chatlog_traj, chatlog_turns, evo_emb, evo_traj, geo


def l2_normalize(vecs):
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vecs / norms


def build_meta_lookup(corpus_meta):
    """faiss_id -> metadata dict"""
    return {m["faiss_id"]: m for m in corpus_meta}


# ══════════════════════════════════════════════════════════════════════════════
# 1. 768-dim nearest-neighbor evolution for SOUL versions
# ══════════════════════════════════════════════════════════════════════════════

def soul_nn_evolution(evo_emb, evo_traj, index, meta_lookup, k=TOP_K):
    """
    For each of 18 SOUL versions (evo_emb[0:18]), query corpus FAISS for top-k,
    EXCLUDING SOUL.md and soul_staging.md from the corpus (faiss_ids 22, 25)
    to avoid circular self-match.
    Track how the neighbor type composition changes from v00 to v17.
    UMAP-independent convergence verification.
    """
    # Identify corpus entries to exclude (SOUL itself and soul_staging)
    excluded_fids = set(
        fid for fid, meta in meta_lookup.items()
        if "SOUL" in meta.get("source_file", "") or "soul_staging" in meta.get("source_file", "")
    )

    soul_versions = evo_traj["families"]["soul"]["versions"]
    n_soul = len(soul_versions)

    n_corpus = index.ntotal
    corpus_vecs = np.array([index.reconstruct(i) for i in range(n_corpus)], dtype=np.float32)
    corpus_norm = l2_normalize(corpus_vecs)

    # L2-normalize soul embeddings
    soul_norm = l2_normalize(evo_emb[:n_soul])

    # Build IP index for cosine search — search k+len(excluded) to allow filtering
    ip_index = faiss.IndexFlatIP(corpus_norm.shape[1])
    ip_index.add(corpus_norm)

    search_k = k + len(excluded_fids) + 2

    results = []
    for i, v in enumerate(soul_versions):
        query = soul_norm[i:i+1]
        sims, ids = ip_index.search(query, search_k)
        neighbors = []
        for sim, fid in zip(sims[0], ids[0]):
            if int(fid) in excluded_fids:
                continue
            meta = meta_lookup.get(int(fid), {})
            neighbors.append({
                "rank": len(neighbors) + 1,
                "faiss_id": int(fid),
                "cosine_sim": round(float(sim), 4),
                "document_type": meta.get("document_type", "?"),
                "source_file": meta.get("source_file", "?"),
                "quality_signal": meta.get("quality_signal", "?"),
                "session": meta.get("session"),
            })
            if len(neighbors) >= k:
                break

        type_counts = Counter(n["document_type"] for n in neighbors)
        results.append({
            "version": v["version_label"],
            "date": v["date"],
            "label": v["label"],
            "word_count": v["word_count"],
            "top_neighbors": neighbors,
            "neighbor_type_distribution": dict(type_counts),
            "dominant_type": type_counts.most_common(1)[0][0] if type_counts else None,
        })

    # Type trajectory (dominant type among top-k, excluding SOUL itself)
    type_trajectory = [r["dominant_type"] for r in results]
    type_transitions = []
    for i in range(1, len(type_trajectory)):
        if type_trajectory[i] != type_trajectory[i-1]:
            type_transitions.append({
                "step": i,
                "from": type_trajectory[i-1],
                "to": type_trajectory[i],
                "version": results[i]["version"],
                "date": results[i]["date"],
                "label": results[i]["label"],
            })

    # Track similarity to nearest essay and nearest design_note across all versions
    essay_sims = []
    design_sims = []
    letter_sims = []
    for i_v, r in enumerate(results):
        # find best essay neighbor in full corpus (excluding SOUL)
        best_essay = max(
            (float(np.dot(soul_norm[i_v], corpus_norm[fid])) for fid, meta in meta_lookup.items()
             if meta.get("document_type") == "essay" and fid not in excluded_fids),
            default=0.0
        )
        best_design = max(
            (float(np.dot(soul_norm[i_v], corpus_norm[fid])) for fid, meta in meta_lookup.items()
             if meta.get("document_type") == "design_note" and fid not in excluded_fids),
            default=0.0
        )
        best_letter = max(
            (float(np.dot(soul_norm[i_v], corpus_norm[fid])) for fid, meta in meta_lookup.items()
             if meta.get("document_type") == "letter" and fid not in excluded_fids),
            default=0.0
        )
        essay_sims.append(round(best_essay, 4))
        design_sims.append(round(best_design, 4))
        letter_sims.append(round(best_letter, 4))

    return {
        "description": "SOUL.md nearest-corpus-neighbor evolution in 768-dim nomic space. UMAP-independent. SOUL.md excluded from corpus.",
        "excluded_fids": list(excluded_fids),
        "k": k,
        "versions": results,
        "type_trajectory": type_trajectory,
        "type_transitions": type_transitions,
        "essay_sim_per_version": essay_sims,
        "design_sim_per_version": design_sims,
        "letter_sim_per_version": letter_sims,
        "essay_sim_change_v00_to_v17": round(essay_sims[-1] - essay_sims[0], 4) if essay_sims else None,
        "design_sim_change_v00_to_v17": round(design_sims[-1] - design_sims[0], 4) if design_sims else None,
        "letter_sim_change_v00_to_v17": round(letter_sims[-1] - letter_sims[0], 4) if letter_sims else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Wallas rolling window cross-correlation
# ══════════════════════════════════════════════════════════════════════════════

def wallas_rolling_correlation(geo):
    """
    From geometry_analysis.json, use the classified_turns array.
    Compute rolling contemplative ratio and find whether peaks predict
    synthesis within N turns.

    Quantifies: at what contemplative density does synthesis reliably follow?
    """
    classified = geo["analysis"]["wallas_classified_turns"]
    stages = [t["wallas_stage"] for t in classified]
    n = len(stages)

    # Find all synthesis turn indices
    synthesis_idx = set(i for i, s in enumerate(stages) if s == "synthesis")
    contemp_idx = set(i for i, s in enumerate(stages) if s == "contemplative")

    # Rolling windows of multiple sizes
    window_results = {}
    for window_size in [10, 20, 30]:
        ratios = []
        for i in range(n - window_size + 1):
            window = stages[i:i+window_size]
            contemp_count = sum(1 for s in window if s == "contemplative")
            ratios.append(contemp_count / window_size)

        # For each window, does synthesis appear in next N turns?
        for lookahead in [3, 5, 10]:
            hits = []
            misses = []
            for i, ratio in enumerate(ratios):
                center = i + window_size // 2
                future = stages[center:center + lookahead]
                has_synthesis = any(s == "synthesis" for s in future)
                if has_synthesis:
                    hits.append(ratio)
                else:
                    misses.append(ratio)

            if hits and misses:
                hit_mean = round(float(np.mean(hits)), 4)
                miss_mean = round(float(np.mean(misses)), 4)
                # t-test: are hit ratios higher than miss ratios?
                t_stat, p_val = stats.ttest_ind(hits, misses)
                effect_size = round((hit_mean - miss_mean) / (
                    np.std(hits + misses) + 1e-9), 4)
                window_results[f"w{window_size}_l{lookahead}"] = {
                    "window_size": window_size,
                    "lookahead": lookahead,
                    "hit_mean_contemp_ratio": hit_mean,
                    "miss_mean_contemp_ratio": miss_mean,
                    "difference": round(hit_mean - miss_mean, 4),
                    "t_stat": round(float(t_stat), 4),
                    "p_value": round(float(p_val), 4),
                    "cohens_d": effect_size,
                    "significant": p_val < 0.05,
                }

    # Rolling 20-turn contemplative ratio time series — find peaks
    window_size = 20
    ratios_20 = []
    for i in range(n - window_size + 1):
        window = stages[i:i+window_size]
        contemp_count = sum(1 for s in window if s == "contemplative")
        ratios_20.append(contemp_count / window_size)

    # Find local maxima (peaks) in contemplative ratio
    peaks = []
    for i in range(1, len(ratios_20)-1):
        if ratios_20[i] > ratios_20[i-1] and ratios_20[i] > ratios_20[i+1]:
            if ratios_20[i] > 0.5:  # only significant peaks
                center_turn = i + window_size // 2
                # synthesis within 10 turns after peak?
                future_turns = min(center_turn + 10, n)
                synthesis_after = any(stages[j] == "synthesis" for j in range(center_turn, future_turns))
                peaks.append({
                    "window_start": i,
                    "center_turn": center_turn,
                    "peak_ratio": round(ratios_20[i], 3),
                    "synthesis_within_10": synthesis_after,
                })

    peaks_with_synthesis = sum(1 for p in peaks if p["synthesis_within_10"])

    return {
        "window_comparisons": window_results,
        "peaks_above_0.5": {
            "total_peaks": len(peaks),
            "peaks_with_synthesis_within_10": peaks_with_synthesis,
            "hit_rate": round(peaks_with_synthesis / len(peaks), 4) if peaks else 0,
            "peak_details": peaks,
        },
        "rolling_20_ratios_sample": [round(r, 3) for r in ratios_20[::20]],  # every 20th
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. Super-cooling threshold for Finding 6
# ══════════════════════════════════════════════════════════════════════════════

def super_cooling_threshold(evo_traj):
    """
    For SOUL.md: scatter word count change vs 2D displacement per step.
    Find the word count above which compression (negative delta_words)
    consistently produces larger displacement than addition.

    The super-cooling point: the word count at which the document becomes
    metastable, and reduction triggers crystallization.
    """
    soul_versions = evo_traj["families"]["soul"]["versions"]

    steps = []
    for i in range(len(soul_versions) - 1):
        v0 = soul_versions[i]
        v1 = soul_versions[i+1]
        wc0 = v0["word_count"]
        wc1 = v1["word_count"]
        delta_wc = wc1 - wc0
        disp = math.sqrt((v1["x"]-v0["x"])**2 + (v1["y"]-v0["y"])**2)
        steps.append({
            "step": i,
            "version_from": v0.get("version_label", f"v{i:02d}"),
            "version_to": v1.get("version_label", f"v{i+1:02d}"),
            "wc_start": wc0,
            "wc_end": wc1,
            "delta_wc": delta_wc,
            "displacement": round(disp, 4),
            "direction": "compression" if delta_wc < 0 else "growth",
        })

    # Split into growth vs compression steps
    growth_steps = [s for s in steps if s["delta_wc"] > 0]
    compression_steps = [s for s in steps if s["delta_wc"] < 0]

    growth_disps = [s["displacement"] for s in growth_steps]
    compression_disps = [s["displacement"] for s in compression_steps]

    comparison = {}
    if growth_disps and compression_disps:
        t_stat, p_val = stats.ttest_ind(compression_disps, growth_disps)
        comparison = {
            "growth_mean_displacement": round(float(np.mean(growth_disps)), 4),
            "compression_mean_displacement": round(float(np.mean(compression_disps)), 4),
            "compression_larger": float(np.mean(compression_disps)) > float(np.mean(growth_disps)),
            "t_stat": round(float(t_stat), 4),
            "p_value": round(float(p_val), 4),
        }

    # Threshold analysis: at what word count does compression begin to dominate?
    # Group by word count bins of 1000 words and compare growth vs compression displacement
    wc_bins = {}
    for s in steps:
        wc_bin = (s["wc_start"] // 1000) * 1000
        if wc_bin not in wc_bins:
            wc_bins[wc_bin] = {"growth": [], "compression": []}
        wc_bins[wc_bin][s["direction"]].append(s["displacement"])

    bin_analysis = {}
    for wc_bin in sorted(wc_bins.keys()):
        g = wc_bins[wc_bin]["growth"]
        c = wc_bins[wc_bin]["compression"]
        bin_analysis[str(wc_bin)] = {
            "wc_range": f"{wc_bin}-{wc_bin+999}",
            "growth_displacements": [round(x, 4) for x in g],
            "compression_displacements": [round(x, 4) for x in c],
            "growth_mean": round(float(np.mean(g)), 4) if g else None,
            "compression_mean": round(float(np.mean(c)), 4) if c else None,
            "compression_dominates": (
                float(np.mean(c)) > float(np.mean(g))
                if g and c else None
            ),
        }

    # Estimate the threshold: first wc_bin where compression_mean > growth_mean
    # (if it exists consistently)
    threshold_wc = None
    for wc_bin in sorted(wc_bins.keys()):
        b = bin_analysis[str(wc_bin)]
        if b["compression_dominates"]:
            threshold_wc = wc_bin
            break

    return {
        "steps": steps,
        "growth_vs_compression": comparison,
        "bin_analysis": bin_analysis,
        "super_cooling_threshold_estimate": threshold_wc,
        "interpretation": (
            f"Above ~{threshold_wc} words, compression consistently produces larger displacement than growth"
            if threshold_wc else
            "No clear super-cooling threshold found — more data points needed"
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. Finding 11 — Chatlog domain distribution against corpus
# ══════════════════════════════════════════════════════════════════════════════

def chatlog_domain_distribution(chatlog_emb, chatlog_traj, chatlog_turns, index, meta_lookup, k=3):
    """
    For each of 923 chatlog action title embeddings, find nearest corpus neighbor.
    Classify each turn by nearest neighbor's document_type.
    Tracks: how does conversation domain (as measured by corpus proximity)
    shift across 50 sessions?

    This is Finding 11: the conversation's domain topology.
    """
    n_corpus = index.ntotal
    corpus_vecs = np.array([index.reconstruct(i) for i in range(n_corpus)], dtype=np.float32)
    corpus_norm = l2_normalize(corpus_vecs)

    ip_index = faiss.IndexFlatIP(corpus_norm.shape[1])
    ip_index.add(corpus_norm)

    chatlog_norm = l2_normalize(chatlog_emb)

    # Batch search all 923 turns
    sims_all, ids_all = ip_index.search(chatlog_norm, k)

    trajectory = chatlog_traj["trajectory"]

    classified_turns = []
    for i, turn in enumerate(trajectory):
        neighbors = []
        for rank in range(k):
            fid = int(ids_all[i][rank])
            sim = float(sims_all[i][rank])
            meta = meta_lookup.get(fid, {})
            neighbors.append({
                "rank": rank + 1,
                "faiss_id": fid,
                "cosine_sim": round(sim, 4),
                "document_type": meta.get("document_type", "?"),
                "source_file": meta.get("source_file", "?"),
                "quality_signal": meta.get("quality_signal"),
            })
        # dominant type = nearest neighbor type
        dominant_type = neighbors[0]["document_type"]
        classified_turns.append({
            "turn_index": turn["turn_index"],
            "date": turn["date"],
            "action_title": turn["action_title"],
            "x": round(turn["x"], 4),
            "y": round(turn["y"], 4),
            "nearest_type": dominant_type,
            "nearest_sim": neighbors[0]["cosine_sim"],
            "top_k_neighbors": neighbors,
            "is_transition": turn.get("is_transition", False),
        })

    # Aggregate by document type
    type_counts = Counter(t["nearest_type"] for t in classified_turns)
    total = len(classified_turns)
    type_fractions = {k: round(v/total, 4) for k, v in type_counts.items()}

    # Date-level aggregation (by date label: "Feb 17", "Feb 18", etc.)
    by_date = defaultdict(lambda: defaultdict(int))
    for t in classified_turns:
        by_date[t["date"]][t["nearest_type"]] += 1

    date_summaries = []
    for date in sorted(by_date.keys()):
        counts = dict(by_date[date])
        n_date = sum(counts.values())
        dominant = max(counts.items(), key=lambda x: x[1])[0]
        date_summaries.append({
            "date": date,
            "total_turns": n_date,
            "type_counts": counts,
            "dominant_type": dominant,
            "type_fractions": {k: round(v/n_date, 3) for k, v in counts.items()},
        })

    # Synthesis proximity: for turns near synthesis documents, what's the nearest type?
    # "Near" = nearest corpus neighbor is a synthesis-quality document
    synthesis_proximity = [
        t for t in classified_turns
        if t["top_k_neighbors"][0].get("quality_signal") == "synthesis"
    ]

    # Track how the dominant type evolves over the session
    dominant_trajectory = [t["nearest_type"] for t in classified_turns]
    type_runs = []
    current_type = dominant_trajectory[0]
    run_start = 0
    for i in range(1, len(dominant_trajectory)):
        if dominant_trajectory[i] != current_type:
            type_runs.append({
                "type": current_type,
                "start": run_start,
                "end": i-1,
                "length": i - run_start,
            })
            current_type = dominant_trajectory[i]
            run_start = i
    type_runs.append({"type": current_type, "start": run_start, "end": len(dominant_trajectory)-1, "length": len(dominant_trajectory)-run_start})

    # Longest runs per type
    longest_by_type = {}
    for run in type_runs:
        if run["type"] not in longest_by_type or run["length"] > longest_by_type[run["type"]]["length"]:
            longest_by_type[run["type"]] = run

    return {
        "description": "Chatlog turn classification by nearest corpus neighbor. Finding 11: conversation domain topology.",
        "total_turns": total,
        "type_distribution": type_counts,
        "type_fractions": type_fractions,
        "dominant_type_overall": max(type_counts.items(), key=lambda x: x[1])[0],
        "synthesis_proximity_count": len(synthesis_proximity),
        "synthesis_proximity_fraction": round(len(synthesis_proximity)/total, 4),
        "date_summaries": date_summaries,
        "longest_run_per_type": longest_by_type,
        "classified_turns": classified_turns,  # full per-turn classification
    }


# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("[analyze_extended] Loading data...")
    index, corpus_meta, chatlog_emb, chatlog_traj, chatlog_turns, evo_emb, evo_traj, geo = load_all()
    meta_lookup = build_meta_lookup(corpus_meta)

    print(f"  corpus: {index.ntotal} docs, chatlog: {chatlog_emb.shape}, evolution: {evo_emb.shape}")

    print("\n[1] 768-dim nearest-neighbor evolution for SOUL versions...")
    soul_nn = soul_nn_evolution(evo_emb, evo_traj, index, meta_lookup)
    print(f"  Type trajectory: {soul_nn['type_trajectory']}")
    print(f"  Type transitions: {soul_nn['type_transitions']}")
    print(f"  Essay similarity v00->v17: {soul_nn['essay_sim_per_version'][0]} -> {soul_nn['essay_sim_per_version'][-1]}  (change: {soul_nn['essay_sim_change_v00_to_v17']})")
    print("  Per-version top neighbor:")
    for v in soul_nn["versions"]:
        top = v["top_neighbors"][0]
        print(f"    {v['version']:4s} {v['label']:25s} wc={v['word_count']:5d}  nn={top['document_type']:12s} ({top['cosine_sim']:.4f}) {top['source_file'][:40]}")

    print("\n[2] Wallas rolling window cross-correlation...")
    wallas_corr = wallas_rolling_correlation(geo)
    print("  Window comparisons (contemplative ratio: hit vs miss):")
    for key, r in wallas_corr["window_comparisons"].items():
        sig = "SIGNIFICANT" if r["significant"] else ""
        print(f"    {key}: hit={r['hit_mean_contemp_ratio']}  miss={r['miss_mean_contemp_ratio']}  "
              f"d={r['cohens_d']}  p={r['p_value']}  {sig}")
    peaks = wallas_corr["peaks_above_0.5"]
    print(f"  Peaks above 0.5 contemplative ratio: {peaks['total_peaks']}, "
          f"synthesis within 10 turns: {peaks['peaks_with_synthesis_within_10']} "
          f"({peaks['hit_rate']*100:.1f}%)")

    print("\n[3] Super-cooling threshold (SOUL word count vs displacement)...")
    sc = super_cooling_threshold(evo_traj)
    comp = sc["growth_vs_compression"]
    print(f"  Growth steps: mean displacement={comp.get('growth_mean_displacement')}  "
          f"Compression steps: mean displacement={comp.get('compression_mean_displacement')}")
    print(f"  Compression produces larger displacement: {comp.get('compression_larger')}  "
          f"p={comp.get('p_value')}")
    print(f"  Super-cooling threshold estimate: {sc['super_cooling_threshold_estimate']} words")
    print(f"  Interpretation: {sc['interpretation']}")
    print("  Bin analysis:")
    for wc, b in sc["bin_analysis"].items():
        gm = b.get("growth_mean", "—")
        cm = b.get("compression_mean", "—")
        dom = b.get("compression_dominates")
        print(f"    {b['wc_range']}: growth={gm}  compression={cm}  comp_dominant={dom}")

    print("\n[4] Chatlog domain distribution (Finding 11)...")
    chatlog_dist = chatlog_domain_distribution(chatlog_emb, chatlog_traj, chatlog_turns, index, meta_lookup)
    print(f"  Overall type distribution: {chatlog_dist['type_distribution']}")
    print(f"  Fractions: {chatlog_dist['type_fractions']}")
    print(f"  Synthesis-proximity turns: {chatlog_dist['synthesis_proximity_count']} ({chatlog_dist['synthesis_proximity_fraction']*100:.1f}%)")
    print("  By date (dominant type):")
    for ds in chatlog_dist["date_summaries"]:
        print(f"    {ds['date']:8s} n={ds['total_turns']:3d}  dominant={ds['dominant_type']:12s}  {ds['type_fractions']}")

    # ── assemble output ──────────────────────────────────────────────────────
    output = {
        "generated": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "description": "Extended analysis for 'The Space Between the Notes' — 768-dim verification + Wallas + super-cooling + chatlog topology",
        "analysis": {
            "soul_nn_evolution": {
                k: v for k, v in soul_nn.items() if k != "versions"  # keep summary, versions are large
            },
            "soul_nn_per_version": soul_nn["versions"],
            "wallas_rolling_correlation": {
                k: v for k, v in wallas_corr.items() if k != "rolling_20_ratios_sample"
            },
            "super_cooling": sc,
            "chatlog_domain": {
                k: v for k, v in chatlog_dist.items() if k != "classified_turns"  # omit 923-entry list
            },
            "chatlog_classified_turns": chatlog_dist["classified_turns"],
        }
    }

    def default_serializer(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, Counter):
            return dict(obj)
        raise TypeError(f"Not serializable: {type(obj)}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=default_serializer)
    print(f"\n[analyze_extended] Written to {OUT_FILE}")


if __name__ == "__main__":
    main()
