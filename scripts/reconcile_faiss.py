#!/usr/bin/env python3
"""
reconcile_faiss.py — rebuild the OSS FAISS index from the claims table, ground truth.

Why this exists: ingest assigns claims.faiss_id from an in-memory index but only
writes the index file at pass-end (see narrative_geometry / wiring_truth DESYNC).
If run_ui restarts mid-pass, the file lags the assigned ids and faiss_id slots can
collide on the next add — silent retrieval corruption. This is the manual
reconciliation for that (the proper hot-path fix — single locked writer or
save-per-add — is a separate design item).

Re-embeds every claim's text with the same model, rebuilds claims.index fresh, and
reassigns sequential faiss_ids so SQLite, the index, and the vectors all agree.
Deterministic (same model, normalized) — does not change dedup behaviour.

RUN WITH INGEST PAUSED, then restart run_ui so its in-memory index reloads the
rebuilt file. In-container:
    /opt/venv-a0/bin/python3 /a0/usr/reconcile_faiss.py
"""
import os
import sqlite3

DB    = os.environ.get("OSS_DB_PATH", "/a0/usr/oss/oss.db")
FAISS = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
EMB   = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def main():
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, claim_text FROM claims ORDER BY id").fetchall()
    if not rows:
        print("no claims; nothing to reconcile")
        return
    print(f"re-embedding {len(rows)} claims with {EMB} ...")
    model = SentenceTransformer(EMB, device="cpu")
    vecs = model.encode([r[1] for r in rows], normalize_embeddings=True,
                        show_progress_bar=False).astype("float32")

    idx = faiss.IndexFlatIP(vecs.shape[1])
    idx.add(vecs)
    os.makedirs(os.path.dirname(FAISS), exist_ok=True)
    faiss.write_index(idx, FAISS)

    for new_fid, (cid, _) in enumerate(rows):
        conn.execute("UPDATE claims SET faiss_id=? WHERE id=?", (new_fid, cid))
    conn.commit()

    n = conn.execute("SELECT COUNT(*) FROM claims WHERE faiss_id IS NOT NULL").fetchone()[0]
    conn.close()
    print(f"rebuilt index ntotal={idx.ntotal} | claims with faiss_id={n} | "
          f"{'CONSISTENT' if idx.ntotal == n else 'STILL DESYNCED'}")


if __name__ == "__main__":
    main()
