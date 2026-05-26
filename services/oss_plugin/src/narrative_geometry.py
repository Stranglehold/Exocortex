"""
narrative_geometry.py — representational geometry of the claim stream (OSS).

The project's Output Geometry Instrument measures the *conversation's* topology
(effective dimensionality, off-map moments). This turns the same lens outward, on
the OSS claim embeddings, to detect coordinated narrative as a SHAPE.

Thesis: a manufactured / coordinated narrative collapses the claim-embedding cloud
onto a few directions (low effective dimensionality) *even while it spans many
distinct source clusters* — the same story echoing across left/right/wire/official.
Independent reporting stays high-dimensional and spread. activation.py already
catches near-duplicate spikes by pairwise cosine; this adds the eigenspectrum view:
coordination has low intrinsic dimensionality, and its echoes cross cluster lines.

Three deterministic measures over a topic's claim vectors (MiniLM, 384-d, unit-norm):
  - effective_dim (RankMe): exp(entropy of singular-value spectrum of the CENTERED
    cloud). Low vs the claim count = the framing has collapsed onto few axes.
  - mean_cosine: overall tightness of the cloud.
  - cross-cluster echo: high-similarity (>= tau) claim pairs whose two sources sit
    in DIFFERENT clusters, and how many distinct clusters those echoes span. A story
    repeated verbatim across the spectrum is the coordination signature.

A soft verdict (DIVERSE / CONVERGING / COORDINATED) combines them — it is a SIGNAL
for analyst attention, not proof. No LLM; pure linear algebra over existing vectors.

What this does NOT do: attribute intent, decide truth, or replace activation.py's
temporal spike detection. It describes the geometry of what's already ingested.
"""
from __future__ import annotations

import json
import math

ECHO_TAU = 0.80   # cosine >= this between two claims = "same story"
MIN_CLAIMS = 5    # below this, geometry isn't meaningful


def _rankme(Xc) -> float:
    """Effective dimensionality = exp(Shannon entropy of the normalized singular
    value spectrum). Ranges [1, min(n, d)]; low = cloud collapsed onto few axes.
    Xc must be mean-centered (we measure spread, not the shared topic direction)."""
    import numpy as np
    if Xc.shape[0] < 2:
        return 1.0
    s = np.linalg.svd(Xc, compute_uv=False)
    s = s[s > 1e-12]
    if s.size == 0:
        return 1.0
    p = s / s.sum()
    entropy = -float((p * np.log(p)).sum())
    return math.exp(entropy)


def _load_topic_vectors(conn, index, topic: str):
    """Return (X unit-norm float32 [n,d], clusters list, claim_ids list) for a topic."""
    import numpy as np
    rows = conn.execute("""
        SELECT c.id, c.faiss_id, s.cluster
        FROM claims c JOIN sources s ON s.id = c.source_id
        WHERE c.faiss_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE json_each.value = ?)
        ORDER BY c.id
    """, (topic,)).fetchall()
    ntotal = index.ntotal
    vecs, clusters, ids = [], [], []
    for r in rows:
        fid = r["faiss_id"]
        if fid is None or fid >= ntotal:
            continue
        vecs.append(index.reconstruct(int(fid)))
        clusters.append(r["cluster"])
        ids.append(r["id"])
    if not vecs:
        return None, [], []
    return np.array(vecs, dtype="float32"), clusters, ids


def analyze_topic_geometry(conn, index, topic: str) -> dict:
    """Compute the narrative-geometry signature for one topic. Returns a report dict."""
    import numpy as np

    X, clusters, ids = _load_topic_vectors(conn, index, topic)
    if X is None or len(ids) < MIN_CLAIMS:
        return {"topic": topic, "n_claims": 0 if X is None else len(ids),
                "verdict": "INSUFFICIENT", "note": f"need >= {MIN_CLAIMS} embedded claims"}

    n = X.shape[0]
    distinct_clusters = sorted(set(clusters))

    # Cosine similarity matrix (vectors are unit-norm from the embedder).
    S = X @ X.T
    iu = np.triu_indices(n, k=1)
    pair_cos = S[iu]
    mean_cosine = float(pair_cos.mean()) if pair_cos.size else 0.0

    # Effective dimensionality of the CENTERED cloud (spread, not topic direction).
    Xc = X - X.mean(axis=0, keepdims=True)
    eff_dim = _rankme(Xc)

    # Cross-cluster echoes: high-similarity pairs whose sources are in different clusters.
    cl = np.array(clusters, dtype=object)
    hi = pair_cos >= ECHO_TAU
    ai, bj = iu[0][hi], iu[1][hi]
    cross = [(int(a), int(b)) for a, b in zip(ai, bj) if cl[a] != cl[b]]
    echo_clusters = set()
    for a, b in cross:
        echo_clusters.add(cl[a]); echo_clusters.add(cl[b])
    echo_cluster_span = len(echo_clusters)

    # Coordination signal (heuristic, documented): a story echoing verbatim across
    # >=3 distinct clusters with a collapsed cloud is the manufactured signature.
    dim_ratio = eff_dim / min(n, X.shape[1])  # low = collapsed
    if echo_cluster_span >= 3 and dim_ratio < 0.5:
        verdict = "COORDINATED"
    elif echo_cluster_span >= 2:
        verdict = "CONVERGING"
    else:
        verdict = "DIVERSE"

    return {
        "topic": topic,
        "n_claims": n,
        "distinct_source_clusters": distinct_clusters,
        "effective_dim": round(eff_dim, 2),
        "effective_dim_ratio": round(dim_ratio, 3),
        "mean_cosine": round(mean_cosine, 3),
        "cross_cluster_echo_pairs": len(cross),
        "echo_cluster_span": echo_cluster_span,
        "echo_clusters": sorted(echo_clusters),
        "verdict": verdict,
        "tau": ECHO_TAU,
    }


def analyze_all_topics(conn, index) -> list:
    topics = [r["tag"] for r in conn.execute("SELECT tag FROM topics WHERE active=1")]
    return [analyze_topic_geometry(conn, index, t) for t in topics]


# ---------------------------------------------------------------------------
# Standalone run (in-container): python3 narrative_geometry.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os, sqlite3
    import faiss  # noqa
    DB    = os.environ.get("OSS_DB_PATH", "/a0/usr/oss/oss.db")
    FAISS = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    index = faiss.read_index(FAISS)
    print("=" * 64)
    print("NARRATIVE GEOMETRY — claim-stream representational topology")
    print("=" * 64)
    for rep in analyze_all_topics(conn, index):
        print()
        for k, v in rep.items():
            print(f"  {k:26} {v}")
    conn.close()
