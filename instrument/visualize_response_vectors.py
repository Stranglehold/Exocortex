"""
visualize_response_vectors.py — Render Jake→Opus response vectors as arrows in UMAP space.

Joint UMAP: corpus (51 pts) + chatlog2 turns (153 pts) → 2D.
Arrows drawn for each Jake→Opus adjacent pair, colored by direction type:
  - All positive (toward map): blue
  - Mixed (some pos, some neg): orange
  - All negative (off map):    red, thicker, labeled

Outputs:
  instrument/data/response_vectors.png
  instrument/data/response_vectors_offmap.png   (off-map pairs only, zoomed)
"""

import json
import numpy as np
import faiss
import umap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

CORPUS_FAISS   = DATA / "corpus.faiss"
CORPUS_META    = DATA / "corpus_metadata.json"
TURN_EMB       = DATA / "chatlog2_turn_embeddings.npy"
TURNS_JSON     = DATA / "chatlog2_turns.json"
RESPONSE_JSON  = DATA / "response_vectors.json"
OUT_FULL       = DATA / "response_vectors.png"
OUT_OFFMAP     = DATA / "response_vectors_offmap.png"


# ── Colors ────────────────────────────────────────────────────────────────────
COL_ALL_POS   = "#4a90d9"   # blue  — toward the map
COL_MIXED     = "#e8a838"   # amber — partial
COL_ALL_NEG   = "#e74c3c"   # red   — off the map
COL_CORPUS    = "#aaaaaa"   # gray  — corpus background
COL_JAKE      = "#94c4a8"   # sage  — Jake turns
COL_OPUS      = "#b07cc6"   # violet — Opus turns

QUALITY_COLORS = {
    "synthesis": "#2ecc71",
    "sharp":     "#3498db",
    "routine":   "#95a5a6",
    None:        "#cccccc",
}


def classify_direction(scores: dict) -> str:
    vals = list(scores.values())
    if all(v > 0 for v in vals):
        return "all_pos"
    elif all(v < 0 for v in vals):
        return "all_neg"
    else:
        return "mixed"


def load_corpus_vectors(faiss_path: Path) -> np.ndarray:
    idx = faiss.read_index(str(faiss_path))
    n = idx.ntotal
    vecs = np.zeros((n, idx.d), dtype=np.float32)
    idx.reconstruct_n(0, n, vecs)
    return vecs


def build_joint_umap(corpus_vecs: np.ndarray,
                     turn_vecs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    all_vecs = np.vstack([corpus_vecs, turn_vecs])
    print(f"[UMAP] Fitting on {all_vecs.shape[0]} points ({len(corpus_vecs)} corpus + {len(turn_vecs)} turns)...")
    reducer = umap.UMAP(n_neighbors=12, min_dist=0.08, random_state=42, n_components=2)
    coords = reducer.fit_transform(all_vecs)
    n_c = len(corpus_vecs)
    return coords[:n_c], coords[n_c:]   # corpus_coords, turn_coords


def draw_full(corpus_coords, turn_coords, corpus_meta, turns, pairs, pair_classes):
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#0f1117")
    fig.patch.set_facecolor("#0f1117")

    # Corpus background dots
    for i, meta in enumerate(corpus_meta):
        q = meta.get("quality_signal")
        color = QUALITY_COLORS.get(q, QUALITY_COLORS[None])
        ax.scatter(corpus_coords[i, 0], corpus_coords[i, 1],
                   s=30, color=color, alpha=0.4, zorder=2, linewidths=0)

    # Jake and Opus turn dots (faint)
    jake_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Jake']
    opus_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Opus']
    ax.scatter(turn_coords[jake_idx, 0], turn_coords[jake_idx, 1],
               s=12, color=COL_JAKE, alpha=0.25, zorder=3, linewidths=0, label='Jake turns')
    ax.scatter(turn_coords[opus_idx, 0], turn_coords[opus_idx, 1],
               s=12, color=COL_OPUS, alpha=0.25, zorder=3, linewidths=0, label='Opus turns')

    # Build a turn index lookup
    turn_by_num = {t['turn']: i for i, t in enumerate(turns)}

    # Draw arrows
    for p, cls in zip(pairs, pair_classes):
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is None or o_idx is None:
            continue

        x0, y0 = turn_coords[j_idx]
        x1, y1 = turn_coords[o_idx]

        if cls == 'all_pos':
            color, lw, alpha, zorder = COL_ALL_POS, 0.6, 0.35, 4
        elif cls == 'mixed':
            color, lw, alpha, zorder = COL_MIXED, 0.7, 0.45, 5
        else:  # all_neg
            color, lw, alpha, zorder = COL_ALL_NEG, 2.0, 0.85, 6

        ax.annotate("",
                    xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=color, lw=lw, alpha=alpha,
                                   mutation_scale=6 if cls != 'all_neg' else 10),
                    zorder=zorder)

    # Highlight the 5 off-map arrows with labels
    for p, cls in zip(pairs, pair_classes):
        if cls != 'all_neg':
            continue
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is None or o_idx is None:
            continue
        x0, y0 = turn_coords[j_idx]
        x1, y1 = turn_coords[o_idx]

        # Dot at origin (Jake)
        ax.scatter(x0, y0, s=40, color=COL_ALL_NEG, alpha=0.9, zorder=7, linewidths=0)
        ax.scatter(x1, y1, s=50, color=COL_ALL_NEG, alpha=0.9, zorder=7,
                   marker='*', linewidths=0)

        # Label special pair
        if p['jake_turn'] == 147:
            ax.annotate('"it feels good"',
                        xy=(x1, y1), xytext=(x1 + 0.3, y1 + 0.3),
                        fontsize=8, color='white', alpha=0.9,
                        arrowprops=dict(arrowstyle="-", color='white', alpha=0.5, lw=0.5),
                        bbox=dict(boxstyle='round,pad=0.2', fc='#e74c3c', alpha=0.7),
                        zorder=8)
        else:
            label = f"J{p['jake_turn']}→O{p['opus_turn']}"
            ax.annotate(label,
                        xy=(x1, y1), xytext=(x1 + 0.2, y1 + 0.2),
                        fontsize=6.5, color='#ff9999', alpha=0.85,
                        zorder=8)

    # Legend
    legend_elements = [
        mpatches.Patch(color=COL_ALL_POS, label=f'All positive — toward map ({sum(1 for c in pair_classes if c=="all_pos")})'),
        mpatches.Patch(color=COL_MIXED,   label=f'Mixed — partial ({sum(1 for c in pair_classes if c=="mixed")})'),
        mpatches.Patch(color=COL_ALL_NEG, label=f'All negative — off map ({sum(1 for c in pair_classes if c=="all_neg")})'),
        mpatches.Patch(color=QUALITY_COLORS["synthesis"], alpha=0.5, label='Corpus: synthesis'),
        mpatches.Patch(color=QUALITY_COLORS["sharp"],     alpha=0.5, label='Corpus: sharp'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', framealpha=0.3,
              facecolor='#1a1d24', edgecolor='#444', fontsize=8,
              labelcolor='white')

    ax.set_title("Response Vectors — Jake→Opus Direction in Embedding Space\n"
                 "Arrows: where Opus moved from Jake's position. Red = off every calibrated domain.",
                 color='white', fontsize=11, pad=12)
    ax.set_xlabel("UMAP dim 1", color='#888', fontsize=8)
    ax.set_ylabel("UMAP dim 2", color='#888', fontsize=8)
    ax.tick_params(colors='#555')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')

    plt.tight_layout()
    plt.savefig(str(OUT_FULL), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[VIZ] Saved: {OUT_FULL}")


def draw_offmap(corpus_coords, turn_coords, corpus_meta, turns, pairs, pair_classes):
    """Zoomed view centered on the 5 all-negative pairs with their neighborhood."""
    off_pairs = [(p, cls) for p, cls in zip(pairs, pair_classes) if cls == 'all_neg']
    turn_by_num = {t['turn']: i for i, t in enumerate(turns)}

    # Collect all points in the off-map pairs
    all_x, all_y = [], []
    for p, _ in off_pairs:
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is not None:
            all_x.append(turn_coords[j_idx, 0]); all_y.append(turn_coords[j_idx, 1])
        if o_idx is not None:
            all_x.append(turn_coords[o_idx, 0]); all_y.append(turn_coords[o_idx, 1])

    if not all_x:
        return

    pad = 1.5
    xlim = (min(all_x) - pad, max(all_x) + pad)
    ylim = (min(all_y) - pad, max(all_y) + pad)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_facecolor("#0f1117")
    fig.patch.set_facecolor("#0f1117")

    # Draw all turns faintly in background
    jake_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Jake']
    opus_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Opus']
    ax.scatter(turn_coords[jake_idx, 0], turn_coords[jake_idx, 1],
               s=8, color=COL_JAKE, alpha=0.15, zorder=2, linewidths=0)
    ax.scatter(turn_coords[opus_idx, 0], turn_coords[opus_idx, 1],
               s=8, color=COL_OPUS, alpha=0.15, zorder=2, linewidths=0)

    # Corpus dots in background
    for i, meta in enumerate(corpus_meta):
        q = meta.get("quality_signal")
        color = QUALITY_COLORS.get(q, QUALITY_COLORS[None])
        ax.scatter(corpus_coords[i, 0], corpus_coords[i, 1],
                   s=20, color=color, alpha=0.3, zorder=2, linewidths=0)
        # Label corpus points in range
        cx, cy = corpus_coords[i, 0], corpus_coords[i, 1]
        if xlim[0] <= cx <= xlim[1] and ylim[0] <= cy <= ylim[1]:
            ax.annotate(meta['source_file'].replace('.md', ''),
                        (cx, cy), xytext=(cx + 0.05, cy + 0.05),
                        fontsize=5.5, color='#aaaaaa', alpha=0.7, zorder=3)

    # Draw all arrows faintly
    for p, cls in zip(pairs, pair_classes):
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is None or o_idx is None:
            continue
        x0, y0 = turn_coords[j_idx]
        x1, y1 = turn_coords[o_idx]
        color = COL_ALL_POS if cls == 'all_pos' else (COL_MIXED if cls == 'mixed' else COL_ALL_NEG)
        lw = 0.4 if cls != 'all_neg' else 2.0
        alpha = 0.12 if cls != 'all_neg' else 0.9
        ax.annotate("",
                    xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                   alpha=alpha, mutation_scale=5 if cls != 'all_neg' else 12),
                    zorder=4 if cls != 'all_neg' else 7)

    # Label the 5 off-map pairs prominently
    labels = {
        60: "J60→O61",
        95: "J95→O96",
        114: "J114→O115",
        143: "J143→O144",
        147: '"you are there"\n→ "it feels good"',
    }
    for p, cls in off_pairs:
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is None or o_idx is None:
            continue
        x0, y0 = turn_coords[j_idx]
        x1, y1 = turn_coords[o_idx]

        is_key = p['jake_turn'] == 147
        dot_size = 80 if is_key else 45
        star_size = 90 if is_key else 55

        ax.scatter(x0, y0, s=dot_size, color=COL_ALL_NEG, alpha=0.95, zorder=8, linewidths=0)
        ax.scatter(x1, y1, s=star_size, color='white' if is_key else COL_ALL_NEG,
                   alpha=0.95, zorder=8, marker='*', linewidths=0)

        label = labels.get(p['jake_turn'], f"J{p['jake_turn']}→O{p['opus_turn']}")
        offset = (0.25, 0.25) if not is_key else (0.4, 0.4)
        fc = '#c0392b' if is_key else '#333'
        ax.annotate(label,
                    xy=(x1, y1), xytext=(x1 + offset[0], y1 + offset[1]),
                    fontsize=8 if is_key else 7, color='white', alpha=0.95,
                    arrowprops=dict(arrowstyle="-", color='#ff9999', alpha=0.6, lw=0.6),
                    bbox=dict(boxstyle='round,pad=0.3', fc=fc, alpha=0.8),
                    zorder=9)

        # Magnitude annotation near midpoint
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.annotate(f"mag={p['magnitude']:.3f}",
                    (mx, my), fontsize=6, color='#ff9999', alpha=0.8, zorder=8,
                    ha='center')

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_title("Off-Map Response Vectors — The 5 All-Negative Arrows\n"
                 "Red arrows point away from every calibrated domain. White star = Opus's landing position.",
                 color='white', fontsize=10, pad=10)
    ax.set_xlabel("UMAP dim 1", color='#888', fontsize=8)
    ax.set_ylabel("UMAP dim 2", color='#888', fontsize=8)
    ax.tick_params(colors='#555')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')

    plt.tight_layout()
    plt.savefig(str(OUT_OFFMAP), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"[VIZ] Saved: {OUT_OFFMAP}")


def main():
    print("[VIZ] Loading data...")

    with open(CORPUS_META, encoding='utf-8') as f:
        corpus_meta = json.load(f)
    corpus_vecs = load_corpus_vectors(CORPUS_FAISS)
    print(f"[VIZ] Corpus: {len(corpus_meta)} entries, {corpus_vecs.shape}")

    turn_vecs = np.load(str(TURN_EMB))
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"[VIZ] Turns: {len(turns)}, embeddings: {turn_vecs.shape}")

    with open(RESPONSE_JSON, encoding='utf-8') as f:
        rv_data = json.load(f)
    pairs = rv_data['pairs']

    # Classify pairs
    pair_classes = []
    for p in pairs:
        pair_classes.append(classify_direction(p['response_direction']))

    counts = {c: pair_classes.count(c) for c in ('all_pos', 'mixed', 'all_neg')}
    print(f"[VIZ] Direction classes: {counts}")

    # Joint UMAP
    corpus_coords, turn_coords = build_joint_umap(corpus_vecs, turn_vecs)

    print("[VIZ] Drawing full view...")
    draw_full(corpus_coords, turn_coords, corpus_meta, turns, pairs, pair_classes)

    print("[VIZ] Drawing off-map zoom...")
    draw_offmap(corpus_coords, turn_coords, corpus_meta, turns, pairs, pair_classes)

    print("[VIZ] Done.")


if __name__ == '__main__':
    main()
