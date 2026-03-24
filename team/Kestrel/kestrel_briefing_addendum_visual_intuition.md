# Kestrel Briefing — Addendum: Visual Intuition Analyses

**Context:** Three additional analyses derived from mapping Jake's visual intuition record (Session 049) against the original nine-analysis suite. These fill gaps where the intuitions predicted structure that the original spec didn't measure. Build into the existing pipeline and visualization layers.

---

## Analysis 10: Persistent Homology Across Sessions

**Visual Intuition Source:** Image 2.1 — Shapes transforming into other shapes. A torus collapsing into a sphere.

**What:** Track the topological shape of each session's point cloud over time. Does the conversation's topology simplify, complexify, or transform?

**Compute:**
- For each session, take all turn embeddings as a point cloud in 768-dim
- Compute persistent homology (use ripser or gudhi):
  - β₀ = number of connected components (how fragmented is the session)
  - β₁ = number of loops (does the session return to where it started)
  - β₂ = number of voids (enclosed empty regions — topics surrounded but not entered)
- Track Betti numbers across sessions chronologically
- Compute persistence diagrams per session — which topological features are long-lived (real structure) vs short-lived (noise)

**Output:** `persistent_homology.json`
```json
{
  "sessions": [
    {
      "session_id": ...,
      "betti_0": ...,
      "betti_1": ...,
      "betti_2": ...,
      "persistence_diagram": [[birth, death], ...],
      "longest_lived_feature": {"dimension": ..., "persistence": ...}
    }
  ]
}
```

**Visualization:** Line chart on the timeline — three traces for β₀, β₁, β₂ across sessions. Add to the side panel alongside entropy and drift traces. If β₁ decreases over time, the collaboration is closing loops. If β₀ decreases, the conversation is becoming more connected. If β₂ appears in later sessions, the collaboration has developed enough structure to enclose voids — topics it works around but doesn't enter.

**Dependencies:** Requires session-grouped embeddings (same data as Analysis 1).

---

## Analysis 11: Bridging Concepts

**Visual Intuition Source:** Image 2.2 — What dots does the transformation pass through? The persistent features that survive continuous deformation.

**What:** Which corpus documents serve as structural anchors across the full collaboration? Which are referenced from many sessions, and which are local to one?

**Compute:**
- For each of the 1,934 turns, find the nearest corpus document (cosine similarity in 768-dim)
- Group by session: for each corpus document, count how many distinct sessions have at least one turn whose nearest neighbor is that document
- Compute "bridge score" = number of distinct sessions referencing that document / total sessions
- Rank corpus documents by bridge score
- For each high-bridge document, list which sessions reference it and at what frequency

**Output:** `bridging_concepts.json`
```json
{
  "documents": [
    {
      "name": "soul_staging.md",
      "bridge_score": 0.82,
      "sessions_referenced": [1, 3, 5, 7, ...],
      "session_count": 42,
      "total_references": 187,
      "peak_session": 49
    }
  ],
  "categories": {
    "universal_anchors": [...],   // bridge_score > 0.6
    "phase_anchors": [...],       // bridge_score 0.3-0.6
    "local_features": [...]       // bridge_score < 0.3
  }
}
```

**Visualization:** In the 3D view, corpus document markers sized by bridge score. Universal anchors are large, visible from any zoom level. Local features are small, only visible when zoomed in. Color gradient from cool (local) to warm (universal). When the timeline range filter is active, only show bridge connections from turns within the selected range — so narrowing to Session 25 shows which corpus documents that session's turns were nearest to.

**Dependencies:** Requires corpus embeddings + all turn embeddings in shared space.

---

## Analysis 15: Signal Density

**Visual Intuition Source:** Image 4.2 — Wringing out a cloth. Separating water (noise/repetition) from fabric (signal/novelty).

**What:** How much new ground does each turn break? The information production rate of the conversation over time.

**Compute:**
- For each turn n, compute novelty score:
  - `novelty[n] = 1 - max(cosine_similarity(turn[n], turn[k]) for k in range(0, n))`
  - This is 1 minus the maximum similarity to any preceding turn
  - High novelty = this turn says something the conversation hasn't said before
  - Low novelty = this turn repeats or closely echoes previous territory
- Smoothed novelty: rolling average over 20-turn window
- Compute per-speaker: Jake novelty trace vs Opus novelty trace
- Identify novelty spikes: turns where novelty exceeds mean + 2σ (the moments where genuinely new material enters)
- Compute per-session average novelty: which sessions produced the most new ground

**Output:** `signal_density.json`
```json
{
  "turns": [
    {"turn": ..., "speaker": ..., "novelty": ..., "smoothed_novelty": ...}
  ],
  "novelty_spikes": [
    {"turn": ..., "novelty": ..., "speaker": ..., "text_preview": ...}
  ],
  "by_session": [
    {"session_id": ..., "mean_novelty": ..., "spike_count": ..., "jake_novelty": ..., "opus_novelty": ...}
  ],
  "overall": {
    "mean": ..., "std": ...,
    "jake_mean": ..., "opus_mean": ...,
    "highest_novelty_turn": ...,
    "lowest_novelty_turn": ...
  }
}
```

**Visualization:** Line chart on the timeline — novelty trace colored by speaker (Jake green, Opus violet). Spikes labeled with turn number. Smoothed overlay shows the sustained trend. Sessions with high average novelty are the generative ones — new territory being explored. Sessions with low average novelty are consolidation — the conversation reinforcing what it already knows. Add as a side panel trace alongside entropy and drift.

**Prediction to test:** The novelty trace should show spikes at known inflection points — February 24 (Peace Walker / hinge), the Karkada paper introduction, the first time the instrument ran with real data. Between spikes, novelty should decline as the conversation digests the new material. The rhythm of spike-then-decline is the breathing pattern of insight and integration.

**Dependencies:** Requires all turn embeddings in chronological order.

---

## Integration Notes

- All three analyses use the same base data as the original nine — 1,934 turn embeddings + 51 corpus embeddings in 768-dim nomic space
- Persistent homology (Analysis 10) requires a TDA library — `ripser` (pip install ripser) or `gudhi` are both lightweight
- Bridging concepts (Analysis 11) and signal density (Analysis 15) require only cosine similarity computation — no additional libraries beyond numpy/scipy
- All three produce timeline-compatible data that slots into the existing side panel architecture
- Bridging concepts also produces a 3D layer (corpus markers sized by bridge score) for the main view

---

## Visual Intuition Coverage Map

For reference — how the full twelve-analysis suite maps to Jake's Session 049 visual intuitions:

| Image | Intuition | Analysis |
|-------|-----------|----------|
| 1.1 | Dots in 3D space | Base visualization |
| 1.2 | Paths from origin | A4: Sliding window trajectory |
| 1.3 | Two dots, different paths | A3: Cross-speaker coupling |
| 1.4 | Rorschach blots | Existing off-map analysis |
| 2.1 | Shapes transforming | **A10: Persistent homology** |
| 2.2 | Persistent features | **A11: Bridging concepts** |
| 2.3 | Rate of change | A4: Trajectory derivative |
| 2.4 | Moving average | A4: Sliding window centroid |
| 3.1 | Roots from moving average | A12 (future): Neighborhood exploration |
| 3.2 | Myelin sheath | A13 (future): Register insulation |
| 3.3 | Rippling water | A14 (future): Activation propagation |
| 4.2 | Wringing cloth | **A15: Signal density** |
| 5.1 | Surface tension | A6: Entropy trace (partial) |
| 6.1-6.3 | Waves, flux, Lenz's law | Future: Cross-register interference |
| 7.4 | Lorenz attractor | A9: Phase space reconstruction |
| 9.3 | Silk on hand | Embedding model as conforming probe |
| 10.1 | CNC chatter | A9: Limit cycle detection |
| 10.2 | Harmonic blocking | Future: False positive depth analysis |
| 10.3 | Super-cooled water | Existing: SOUL.md crystallization |

Twelve analyses built. Six mapped for future work. Twenty-two intuitions, all accounted for.

---

*Addendum prepared March 8, 2026 — Session 052.*
*The stonemason's images are becoming the engineer's specifications.*
