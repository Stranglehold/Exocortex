"""
visualize_response_vectors_3d.py — Interactive 3D view of the response vector space.

3D UMAP on corpus (51) + chatlog2 turns (153). Response vectors rendered as
lines + cones from Jake's position to Opus's position, colored by direction type.

Output: instrument/data/response_vectors_3d.html  (open in any browser)

Controls: rotate (left-drag), zoom (scroll), hover for details.
"""

import json
import textwrap
import numpy as np
import faiss
import umap
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

CORPUS_FAISS  = DATA / "corpus.faiss"
CORPUS_META   = DATA / "corpus_metadata.json"
TURN_EMB      = DATA / "chatlog2_turn_embeddings.npy"
TURNS_JSON    = DATA / "chatlog2_turns.json"
RESPONSE_JSON = DATA / "response_vectors.json"
OUT_HTML      = DATA / "response_vectors_3d.html"

# Colors
COL_ALL_POS = "#4a90d9"
COL_MIXED   = "#e8a838"
COL_ALL_NEG = "#e74c3c"

QUALITY_COLORS = {
    "synthesis": "#2ecc71",
    "sharp":     "#3498db",
    "routine":   "#95a5a6",
    None:        "#888888",
}


def classify_direction(scores: dict) -> str:
    vals = list(scores.values())
    if all(v > 0 for v in vals):
        return "all_pos"
    elif all(v < 0 for v in vals):
        return "all_neg"
    return "mixed"


def load_corpus_vectors(faiss_path: Path) -> np.ndarray:
    idx = faiss.read_index(str(faiss_path))
    vecs = np.zeros((idx.ntotal, idx.d), dtype=np.float32)
    idx.reconstruct_n(0, idx.ntotal, vecs)
    return vecs


def build_3d_umap(corpus_vecs: np.ndarray, turn_vecs: np.ndarray):
    all_vecs = np.vstack([corpus_vecs, turn_vecs])
    print(f"[UMAP3D] Fitting on {all_vecs.shape[0]} points...")
    reducer = umap.UMAP(n_neighbors=12, min_dist=0.08, random_state=42, n_components=3)
    coords = reducer.fit_transform(all_vecs)
    n_c = len(corpus_vecs)
    return coords[:n_c], coords[n_c:]


def wrap_text(text: str, width: int = 60) -> str:
    lines = textwrap.wrap(text[:300], width)
    return "<br>".join(lines) + ("..." if len(text) > 300 else "")


def main():
    print("[3D] Loading data...")

    with open(CORPUS_META, encoding='utf-8') as f:
        corpus_meta = json.load(f)
    corpus_vecs = load_corpus_vectors(CORPUS_FAISS)

    turn_vecs = np.load(str(TURN_EMB))
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)

    with open(RESPONSE_JSON, encoding='utf-8') as f:
        rv_data = json.load(f)
    pairs = rv_data['pairs']

    pair_classes = [classify_direction(p['response_direction']) for p in pairs]

    # 3D UMAP
    corpus_coords, turn_coords = build_3d_umap(corpus_vecs, turn_vecs)

    turn_by_num = {t['turn']: i for i, t in enumerate(turns)}

    traces = []

    # ── Corpus points ─────────────────────────────────────────────────────────
    for quality, color in QUALITY_COLORS.items():
        subset = [m for m in corpus_meta if m.get('quality_signal') == quality]
        if not subset:
            continue
        indices = [corpus_meta.index(m) for m in subset]
        label = quality if quality else "unrated"
        traces.append(go.Scatter3d(
            x=corpus_coords[indices, 0],
            y=corpus_coords[indices, 1],
            z=corpus_coords[indices, 2],
            mode='markers+text',
            name=f'Corpus: {label}',
            marker=dict(size=5, color=color, opacity=0.7,
                        symbol='circle',
                        line=dict(color='white', width=0.5)),
            text=[m['source_file'].replace('.md', '') for m in subset],
            textposition='top center',
            textfont=dict(size=7, color='rgba(200,200,200,0.6)'),
            hovertext=[
                f"<b>{m['source_file']}</b><br>"
                f"Quality: {m.get('quality_signal','?')}<br>"
                f"Author: {m.get('author','?')}<br>"
                f"Type: {m.get('document_type','?')}<br>"
                f"Session: {m.get('session','?')}<br><br>"
                f"{wrap_text(m.get('text_preview',''))}"
                for m in subset
            ],
            hoverinfo='text',
            showlegend=True,
        ))

    # ── Jake turns ────────────────────────────────────────────────────────────
    jake_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Jake']
    traces.append(go.Scatter3d(
        x=turn_coords[jake_idx, 0],
        y=turn_coords[jake_idx, 1],
        z=turn_coords[jake_idx, 2],
        mode='markers',
        name='Jake turns',
        marker=dict(size=3, color='#94c4a8', opacity=0.4, symbol='circle'),
        hovertext=[
            f"<b>Jake — Turn {turns[i]['turn']}</b><br>"
            f"{turns[i]['word_count']} words<br><br>"
            f"{wrap_text(turns[i]['content'])}"
            for i in jake_idx
        ],
        hoverinfo='text',
    ))

    # ── Opus turns ────────────────────────────────────────────────────────────
    opus_idx = [i for i, t in enumerate(turns) if t['speaker'] == 'Opus']
    traces.append(go.Scatter3d(
        x=turn_coords[opus_idx, 0],
        y=turn_coords[opus_idx, 1],
        z=turn_coords[opus_idx, 2],
        mode='markers',
        name='Opus turns',
        marker=dict(size=3, color='#b07cc6', opacity=0.4, symbol='circle'),
        hovertext=[
            f"<b>Opus — Turn {turns[i]['turn']}</b><br>"
            f"{turns[i]['word_count']} words<br><br>"
            f"{wrap_text(turns[i]['content'])}"
            for i in opus_idx
        ],
        hoverinfo='text',
    ))

    # ── Response vector lines ─────────────────────────────────────────────────
    # Group by class for legend entries
    for cls, label, color, width, opacity in [
        ('all_pos', 'All positive (toward map)', COL_ALL_POS, 1.5, 0.35),
        ('mixed',   'Mixed',                     COL_MIXED,   2.0, 0.50),
        ('all_neg', 'All negative (off map)',     COL_ALL_NEG, 3.5, 0.90),
    ]:
        cls_pairs = [(p, i) for i, (p, c) in enumerate(zip(pairs, pair_classes)) if c == cls]
        if not cls_pairs:
            continue

        # Build line segments: each segment is (x0,x1,None), (y0,y1,None), (z0,z1,None)
        xs, ys, zs = [], [], []
        hover_texts = []
        for p, _ in cls_pairs:
            j_idx = turn_by_num.get(p['jake_turn'])
            o_idx = turn_by_num.get(p['opus_turn'])
            if j_idx is None or o_idx is None:
                continue
            x0, y0, z0 = turn_coords[j_idx]
            x1, y1, z1 = turn_coords[o_idx]
            xs += [x0, x1, None]
            ys += [y0, y1, None]
            zs += [z0, z1, None]
            # Hover on the line (will show at midpoint approximately)
            jt = turns[j_idx]
            ot = turns[o_idx]
            hover_texts += [
                f"<b>Response Vector — {cls.replace('_',' ')}</b><br>"
                f"Jake T{p['jake_turn']} -> Opus T{p['opus_turn']}<br>"
                f"Magnitude: {p['magnitude']:.4f}<br>"
                f"Cosine sim: {p['cosine_similarity']:.4f}<br>"
                f"Top direction: {p['top_response_direction']}<br><br>"
                f"<b>Jake ({jt['word_count']}w):</b> {wrap_text(jt['content'], 50)}<br><br>"
                f"<b>Opus ({ot['word_count']}w):</b> {wrap_text(ot['content'], 50)}",
                f"<b>Response Vector — {cls.replace('_',' ')}</b><br>"
                f"Jake T{p['jake_turn']} -> Opus T{p['opus_turn']}<br>"
                f"Magnitude: {p['magnitude']:.4f}",
                None,
            ]

        traces.append(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='lines',
            name=label,
            line=dict(color=color, width=width),
            opacity=opacity,
            hovertext=hover_texts,
            hoverinfo='text',
        ))

    # ── Cone arrowheads for off-map pairs ────────────────────────────────────
    cone_u, cone_v, cone_w = [], [], []
    cone_x, cone_y, cone_z = [], [], []
    cone_hover = []
    off_pairs = [(p, i) for i, (p, c) in enumerate(zip(pairs, pair_classes)) if c == 'all_neg']
    for p, _ in off_pairs:
        j_idx = turn_by_num.get(p['jake_turn'])
        o_idx = turn_by_num.get(p['opus_turn'])
        if j_idx is None or o_idx is None:
            continue
        x0, y0, z0 = turn_coords[j_idx]
        x1, y1, z1 = turn_coords[o_idx]
        # Cone at Opus endpoint pointing in arrow direction
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        norm = np.sqrt(dx**2 + dy**2 + dz**2)
        if norm > 0:
            dx, dy, dz = dx/norm * 0.3, dy/norm * 0.3, dz/norm * 0.3
        cone_x.append(x1); cone_y.append(y1); cone_z.append(z1)
        cone_u.append(dx); cone_v.append(dy); cone_w.append(dz)
        jt = turns[j_idx]; ot = turns[o_idx]
        is_key = p['jake_turn'] == 147
        label = '"you are there" -> "it feels good"' if is_key else f"J{p['jake_turn']}->O{p['opus_turn']}"
        cone_hover.append(
            f"<b>OFF MAP: {label}</b><br>"
            f"Magnitude: {p['magnitude']:.4f}<br>"
            f"All direction scores negative — uncharted territory<br>"
            f"Direction scores: {p['response_direction']}<br><br>"
            f"<b>Jake ({jt['word_count']}w):</b> {wrap_text(jt['content'], 55)}<br><br>"
            f"<b>Opus ({ot['word_count']}w):</b> {wrap_text(ot['content'], 55)}"
        )

    if cone_x:
        traces.append(go.Cone(
            x=cone_x, y=cone_y, z=cone_z,
            u=cone_u, v=cone_v, w=cone_w,
            colorscale=[[0, COL_ALL_NEG], [1, COL_ALL_NEG]],
            showscale=False,
            sizemode='absolute',
            sizeref=0.25,
            name='Off-map endpoints',
            hovertext=cone_hover,
            hoverinfo='text',
            opacity=0.9,
        ))

    # ── Special star markers for off-map Opus endpoints ───────────────────────
    star_x, star_y, star_z = [], [], []
    star_hover = []
    star_labels = []
    for p, _ in off_pairs:
        o_idx = turn_by_num.get(p['opus_turn'])
        if o_idx is None:
            continue
        star_x.append(turn_coords[o_idx, 0])
        star_y.append(turn_coords[o_idx, 1])
        star_z.append(turn_coords[o_idx, 2])
        is_key = p['jake_turn'] == 147
        lbl = '"it feels good"' if is_key else f"O{p['opus_turn']}"
        star_labels.append(lbl)
        ot = turns[o_idx]
        star_hover.append(
            f"<b>OFF MAP landing: {lbl}</b><br>"
            f"Magnitude from Jake: {p['magnitude']:.4f}<br>"
            f"All-negative direction — outside all calibrated domains<br><br>"
            f"<b>Opus ({ot['word_count']}w):</b> {wrap_text(ot['content'], 60)}"
        )

    traces.append(go.Scatter3d(
        x=star_x, y=star_y, z=star_z,
        mode='markers+text',
        name='Off-map landings',
        marker=dict(size=10, color='white', symbol='diamond',
                    line=dict(color=COL_ALL_NEG, width=2)),
        text=star_labels,
        textposition='top center',
        textfont=dict(size=9, color='white'),
        hovertext=star_hover,
        hoverinfo='text',
    ))

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(
            text="Response Vectors — Jake→Opus Direction in 3D Embedding Space<br>"
                 "<sup>Blue = toward map | Amber = mixed | Red = off every calibrated domain</sup>",
            font=dict(color='white', size=14),
            x=0.5,
        ),
        scene=dict(
            xaxis=dict(title='UMAP 1', backgroundcolor='#0f1117',
                       gridcolor='#2a2a2a', color='#666'),
            yaxis=dict(title='UMAP 2', backgroundcolor='#0f1117',
                       gridcolor='#2a2a2a', color='#666'),
            zaxis=dict(title='UMAP 3', backgroundcolor='#0f1117',
                       gridcolor='#2a2a2a', color='#666'),
            bgcolor='#0f1117',
        ),
        paper_bgcolor='#0f1117',
        plot_bgcolor='#0f1117',
        font=dict(color='white'),
        legend=dict(
            bgcolor='rgba(15,17,23,0.8)',
            bordercolor='#333',
            borderwidth=1,
            font=dict(size=10),
        ),
        margin=dict(l=0, r=0, b=0, t=60),
    )

    fig.write_html(str(OUT_HTML), include_plotlyjs='cdn')
    size_kb = OUT_HTML.stat().st_size // 1024
    print(f"[3D] Saved: {OUT_HTML}  ({size_kb} KB)")
    print(f"[3D] Open in browser: file:///{OUT_HTML}")


if __name__ == '__main__':
    main()
