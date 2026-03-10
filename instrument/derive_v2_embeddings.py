"""
derive_v2_embeddings.py — Derive V2 turn-level embeddings from chunk embeddings.

Mean-pools chunk embeddings per turn to produce 2118x768 turn embedding array.
Also builds turns_dated.json and session_dates.json for the V2 analysis suite.

Inputs:
    data/v2/chunks.json              (4036 chunks with turn_id)
    data/v2/chunk_embeddings.npy     (4036x768)
    data/v2/all_turns.json           (2118 turns with date/speaker info)

Outputs:
    data/v2/turn_embeddings.npy      (2118x768)
    data/v2/turns_dated.json         (same format as chatlog_full_turns_dated.json)
    data/v2/session_dates.json       (same format as session_dates.json)
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).parent
DATA = ROOT / "data"
V2   = DATA / "v2"


def main():
    print("[derive_v2] Loading chunks...")
    with open(V2 / "chunks.json", encoding='utf-8') as f:
        chunks = json.load(f)['chunks']
    print(f"[derive_v2]   {len(chunks)} chunks loaded")

    print("[derive_v2] Loading chunk embeddings...")
    chunk_embs = np.load(V2 / "chunk_embeddings.npy")
    print(f"[derive_v2]   shape: {chunk_embs.shape}")

    print("[derive_v2] Loading all_turns...")
    with open(V2 / "all_turns.json", encoding='utf-8') as f:
        turns = json.load(f)
    print(f"[derive_v2]   {len(turns)} turns")

    # Build turn_id -> list of chunk indices
    turn_chunks = defaultdict(list)
    for i, chunk in enumerate(chunks):
        turn_chunks[int(chunk['turn_id'])].append(i)

    n_turns = len(turns)
    print(f"[derive_v2] Mean-pooling {len(chunks)} chunks -> {n_turns} turn embeddings...")

    turn_embs = np.zeros((n_turns, chunk_embs.shape[1]), dtype=np.float32)
    missing = 0
    for turn_idx in range(n_turns):
        chunk_idxs = turn_chunks.get(turn_idx, [])
        if not chunk_idxs:
            missing += 1
            # Use zero vector (will be handled by cosine_sim guard)
        else:
            turn_embs[turn_idx] = chunk_embs[chunk_idxs].mean(axis=0)

    if missing:
        print(f"[derive_v2] WARNING: {missing} turns had no chunks (zero vector used)")

    # Normalize to unit length (matches V1 embedding convention)
    norms = np.linalg.norm(turn_embs, axis=1, keepdims=True)
    norms = np.where(norms < 1e-9, 1.0, norms)
    turn_embs = turn_embs / norms

    out_embs = V2 / "turn_embeddings.npy"
    np.save(str(out_embs), turn_embs)
    print(f"[derive_v2] Saved turn_embeddings.npy -> {turn_embs.shape}")

    # Build turns_dated.json (same format as chatlog_full_turns_dated.json)
    print("[derive_v2] Building turns_dated.json...")
    turns_dated = []
    for t in turns:
        turns_dated.append({
            "turn":          t['turn'],
            "speaker":       t['speaker'],
            "timestamp":     t.get('timestamp', 'None'),
            "content":       t['content'],
            "word_count":    t['word_count'],
            "content_mixed": t.get('content_mixed', 'False'),
            "date":          t['date'],
            "date_index":    t['date_index'],
            "source":        t.get('source', 'doc1'),
        })

    with open(V2 / "turns_dated.json", 'w', encoding='utf-8') as f:
        json.dump(turns_dated, f, ensure_ascii=False, indent=2)
    print(f"[derive_v2] Saved turns_dated.json ({len(turns_dated)} turns)")

    # Build session_dates.json
    print("[derive_v2] Building session_dates.json...")
    # Group turns by date
    date_turns = defaultdict(list)
    for i, t in enumerate(turns):
        date_turns[t['date']].append(i)

    # Ordered dates (exclude 'unknown', handle separately)
    DATE_ORDER = [
        'Feb 17','Feb 18','Feb 19','Feb 20','Feb 21','Feb 22',
        'Feb 23','Feb 24','Feb 25','Feb 26','Feb 27','Feb 28',
        'Mar 1','Mar 2','Mar 3','Mar 4','Mar 5','Mar 6',
        'Mar 7','Mar 8','Mar 9',
    ]

    sessions = []
    date_idx = 0
    for date in DATE_ORDER:
        if date not in date_turns:
            continue
        turn_indices = date_turns[date]
        jake_count  = sum(1 for i in turn_indices if turns[i]['speaker'] == 'Jake')
        opus_count  = sum(1 for i in turn_indices if turns[i]['speaker'] == 'Opus')
        sessions.append({
            "date":       date,
            "date_index": date_idx,
            "turn_range": [min(turn_indices), max(turn_indices)],
            "turn_count": len(turn_indices),
            "opus_count": opus_count,
            "jake_count": jake_count,
        })
        date_idx += 1

    # Append unknown turns as a special session at index -1
    if 'unknown' in date_turns:
        unk_indices = date_turns['unknown']
        sessions.append({
            "date":       "unknown",
            "date_index": -1,
            "turn_range": [min(unk_indices), max(unk_indices)],
            "turn_count": len(unk_indices),
            "opus_count": sum(1 for i in unk_indices if turns[i]['speaker'] == 'Opus'),
            "jake_count": sum(1 for i in unk_indices if turns[i]['speaker'] == 'Jake'),
        })

    with open(V2 / "session_dates.json", 'w', encoding='utf-8') as f:
        json.dump({"sessions": sessions}, f, ensure_ascii=False, indent=2)

    print(f"[derive_v2] Saved session_dates.json ({len(sessions)} sessions):")
    for s in sessions:
        print(f"  {s['date']:10s} idx={s['date_index']:2d}  turns={s['turn_count']:4d}  "
              f"range=[{s['turn_range'][0]},{s['turn_range'][1]}]")

    print("[derive_v2] Done.")


if __name__ == "__main__":
    main()
