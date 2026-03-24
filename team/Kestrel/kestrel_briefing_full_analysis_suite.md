# Kestrel Briefing — Full Chatlog Analysis Suite

## Source Data
- **Full chatlog:** 1,934 turns, speaker-labeled (Jake/Opus), spanning Sessions 001–051 (February 17 – March 8, 2026)
- **Annotated session:** 153 turns from "When I Saw Opus" (Sessions 050–051), higher-fidelity parse with manual annotation
- **Corpus:** 51 documents with embeddings (corpus.faiss + corpus_metadata.json)
- **Existing centroids:** 5 domain centroids in 768-dim (centroids_768.json)

## Overview

Nine analyses, ordered by priority. Each produces a data layer for visualization. All operate on the same 768-dim nomic embedding space. Output format: JSON per analysis, plus a unified visualization with toggleable layers and a timeline range filter.

---

## Analysis 1: Session Signatures (Priority 1)

**What:** Compute a single summary vector for each session — the centroid of all turn embeddings in that session.

**Compute:**
- Group turns by session (use date boundaries or session markers in the chatlog)
- For each session: centroid = mean of all turn embeddings in that session
- Project session centroids into the joint UMAP (alongside corpus + all turns)
- For each session centroid: nearest domain centroid, distance to each centroid, dominant register
- Sequential displacement: distance between consecutive session centroids
- Session arc length: sum of turn-to-turn displacements within that session (how much the conversation moved during the session)

**Output:** `session_signatures.json`
```json
{
  "sessions": [
    {
      "session_id": 1,
      "date": "2026-02-17",
      "turn_range": [0, 42],
      "turn_count": 43,
      "centroid_768": [...],  // or just store UMAP coords
      "umap_x": ..., "umap_y": ..., "umap_z": ...,
      "dominant_register": "operational",
      "centroid_distances": {"phil": ..., "oper": ..., "refl": ..., "rela": ..., "mixe": ...},
      "displacement_from_previous": ...,
      "internal_arc_length": ...,
      "entropy": ...  // register entropy within session
    }
  ]
}
```

**Visualization:** 51 large dots (one per session) connected chronologically. Color by dominant register or date. Size by internal arc length (big dot = session covered lots of ground, small dot = focused session).

---

## Analysis 2: Recurrence Matrix (Priority 2)

**What:** For every pair of turns (i, j), compute cosine similarity. Visualize as a heatmap.

**Compute:**
- Full 1934×1934 cosine similarity matrix (this is large but feasible — ~3.7M values, all float32)
- For visualization, downsample to blocks if needed (e.g., average similarity per 10-turn block → 193×193 matrix)
- Mark session boundaries on both axes
- Identify off-diagonal bright spots: pairs (i, j) where |i - j| > 50 and similarity > threshold (e.g., mean + 1σ)

**Output:** `recurrence_matrix.json`
```json
{
  "resolution": 10,  // turns per block
  "matrix": [[...], ...],  // 193x193 or full 1934x1934 if feasible
  "session_boundaries": [0, 43, 87, ...],  // turn indices where sessions start
  "high_recurrence_pairs": [
    {"turn_i": ..., "turn_j": ..., "similarity": ..., "session_i": ..., "session_j": ...}
  ]
}
```

**Visualization:** 2D heatmap (separate from the 3D space). X and Y axes are turn indices. Color = similarity. Session boundaries as grid lines. Bright off-diagonal spots are where the conversation rhymes with itself across time. Clicking a bright spot could show both turns.

---

## Analysis 3: Cross-Speaker Phase Coupling (Priority 3)

**What:** Track the distance between Jake and Opus through the conversation over time.

**Compute:**
- For each adjacent Jake-Opus pair: cosine similarity in 768-dim (already have this from response vectors, extend to full chatlog)
- Smoothed inter-speaker distance: rolling average of cosine distance over 10-turn window
- Convergence moments: local minima in the distance trace (voices closest together)
- Divergence moments: local maxima (voices furthest apart)
- Correlation with session boundaries: does inter-speaker distance reset at session starts?

**Output:** `speaker_coupling.json`
```json
{
  "pairs": [
    {"position": ..., "jake_turn": ..., "opus_turn": ..., "similarity": ..., "distance": ...}
  ],
  "smoothed_distance": [...],  // rolling average
  "convergence_points": [...],  // local minima with turn indices
  "divergence_points": [...],   // local maxima with turn indices
  "session_boundary_distances": [...]  // distance at each session start
}
```

**Visualization:** Line chart overlaid on the timeline. Y-axis = inter-speaker distance. Peaks (divergence) and valleys (convergence) labeled. Session boundaries as vertical lines. This shows the rhythm of the two voices moving together and apart.

---

## Analysis 4: Sliding Window Trajectory (Priority 4)

**What:** Smoothed trajectory of the conversation's position over time.

**Compute:**
- Rolling window centroid: for each window of 20 turns, compute the mean embedding
- Project window centroids into 3D UMAP
- Compute derivative: direction and magnitude of change between consecutive window centroids
- Compute acceleration: change in the derivative (where the conversation changes direction)
- Peak acceleration points = major register transitions

**Output:** `sliding_window_trajectory.json`
```json
{
  "window_size": 20,
  "step_size": 1,
  "points": [
    {
      "center_turn": ...,
      "umap_x": ..., "umap_y": ..., "umap_z": ...,
      "velocity_magnitude": ...,
      "acceleration_magnitude": ...,
      "dominant_register": ...
    }
  ],
  "peak_accelerations": [...]  // turn indices where direction changes most sharply
}
```

**Visualization:** A smooth curve through 3D space — the conversation's path with noise filtered out. Color the curve by velocity (fast = bright, slow = dim) or by register. Peak acceleration points marked as larger dots. This is the moving average from Jake's visual intuition, Image 2.4.

---

## Analysis 5: Information Flow Direction (Priority 5)

**What:** Who's leading the trajectory at each moment?

**Compute:**
- For each Jake→Opus pair: compute how far Opus moved from the previous Opus turn vs how far Jake moved from the previous Jake turn
- Leader ratio: Opus_displacement / Jake_displacement
  - Ratio > 1: Opus is leading (moving further, carrying the conversation to new territory)
  - Ratio < 1: Jake is leading
  - Ratio ≈ 1: co-movement
- Smoothed leader trace over time
- Correlation with session phase: who leads at session starts vs session ends?

**Output:** `information_flow.json`
```json
{
  "pairs": [
    {"position": ..., "jake_displacement": ..., "opus_displacement": ..., "leader": "jake"|"opus", "ratio": ...}
  ],
  "smoothed_ratio": [...],
  "jake_lead_percentage": ...,
  "opus_lead_percentage": ...,
  "by_session": [{"session": ..., "jake_lead_pct": ..., "opus_lead_pct": ...}]
}
```

**Visualization:** Timeline with colored bands — green when Jake leads, violet when Opus leads. Width of band proportional to how strongly one voice leads. Moments of balance (ratio ≈ 1) are thin. This is the jazz ensemble — who has the solo at each moment.

---

## Analysis 6: Register Entropy Trace (Priority 6)

**What:** How diverse is the conversation's register distribution at each moment?

**Compute:**
- For each window of 20 turns, classify each turn by nearest centroid
- Compute Shannon entropy of the register distribution within the window
  - H = -Σ p(r) log₂ p(r) for each register r
  - Max entropy (all 5 registers equally present) = log₂(5) ≈ 2.32
  - Min entropy (all turns in one register) = 0
- Entropy trace over time
- Correlation with synthesis production: do high-entropy windows precede synthesis moments?

**Output:** `entropy_trace.json`
```json
{
  "window_size": 20,
  "trace": [
    {"center_turn": ..., "entropy": ..., "register_distribution": {"phil": ..., "oper": ..., ...}}
  ],
  "mean_entropy": ...,
  "max_entropy_moment": ...,
  "min_entropy_moment": ...
}
```

**Visualization:** Line chart on the timeline. Y-axis = entropy (0 to 2.32). High entropy = conversation distributed across registers. Low entropy = focused in one. Session boundaries as vertical lines.

---

## Analysis 7: Cumulative Drift (Priority 7)

**What:** How far has each speaker traveled from where they started?

**Compute:**
- For each speaker independently: cumulative sum of turn-to-turn displacements
- Jake_drift[n] = Σ(distance between consecutive Jake turns, from turn 0 to turn n)
- Opus_drift[n] = same for Opus turns
- Plot both on same timeline
- Rate of drift: derivative of cumulative drift (is it accelerating, decelerating, or constant?)

**Output:** `cumulative_drift.json`
```json
{
  "jake": [{"turn": ..., "cumulative_distance": ..., "rate": ...}],
  "opus": [{"turn": ..., "cumulative_distance": ..., "rate": ...}],
  "total_jake_distance": ...,
  "total_opus_distance": ...
}
```

**Visualization:** Two lines on the timeline, Jake in green and Opus in violet. Steeper slope = moving faster through the space. Plateaus = stationary period. Diverging lines = one voice exploring more than the other.

---

## Analysis 8: Markov Transition Matrix (Priority 8)

**What:** The grammar of register transitions — given the current register, what's the probability of each next register?

**Compute:**
- Classify each turn by nearest centroid (5 registers)
- Compute transition counts: for each pair of consecutive turns, count (register_i → register_j)
- Normalize rows to get transition probabilities
- Compute separately for: full chatlog, early sessions (1–20), late sessions (21–51)
- Compare early vs late matrices: which transitions became more common? Which became less?
- Stationarity test: is the transition matrix stable over time, or does it drift?

**Output:** `transition_matrix.json`
```json
{
  "full": {
    "matrix": [[...], ...],  // 5x5
    "labels": ["phil", "oper", "refl", "rela", "mixe"],
    "self_transition_rate": ...  // average diagonal value — how sticky is each register
  },
  "early": { ... },
  "late": { ... },
  "transition_drift": {
    "increased": [["oper", "phil", 0.15, 0.28]],  // transitions that became more common
    "decreased": [...]
  }
}
```

**Visualization:** Two 5×5 heatmaps side by side — early matrix and late matrix. Color = transition probability. Diagonal dominance shows register stickiness. Off-diagonal brightness shows cross-register movement. The difference between early and late shows what the collaboration learned.

---

## Analysis 9: Phase Space Reconstruction (Priority 9)

**What:** Does the conversation have attractor dynamics?

**Compute:**
- Take the smoothed trajectory from Analysis 4
- Compute delay embeddings: for each time point t, create the vector [x(t), x(t+τ), x(t+2τ)] for various values of τ (5, 10, 20 turns)
- Project into 3D
- Look for: limit cycles (closed orbits), fixed points (convergence), strange attractors (structured but non-repeating paths)
- Compute Lyapunov exponent if feasible — positive = chaotic/divergent, negative = convergent, zero = neutral

**Output:** `phase_space.json`
```json
{
  "tau_values": [5, 10, 20],
  "reconstructions": {
    "tau_5": {
      "points": [{"t": ..., "x": ..., "y": ..., "z": ...}],
      "lyapunov_estimate": ...
    }
  }
}
```

**Visualization:** 3D scatter plot — delay embedding reconstruction. If the collaboration has attractor dynamics, this plot will show them as geometric shapes. This is the Lorenz attractor test from Jake's visual intuition, Image 7.4.

---

## Visualization Spec: Unified Interactive Instrument

### Architecture
Single HTML page (Plotly 3D or Three.js) with:

**Main view:** 3D scatter plot with all data layers toggleable.

**Timeline range filter:** Dual-handle slider at the bottom.
- Left handle = start turn/date
- Right handle = end turn/date
- Dragging either handle filters ALL visible layers to only show data within the selected range
- Default: full range (turn 0 to 1934)
- Preset buttons: "All", "Session N", "Feb 24 (Hinge)", "Mar 7-8 (Late Night)"

**Layer toggles:**
- [ ] Corpus (51 documents)
- [ ] All turns (1,934 points, colored by speaker)
- [ ] Session signatures (51 large dots)
- [ ] Sliding window trajectory (smoothed path)
- [ ] Response vectors (arrows, if computed for full chatlog)
- [ ] Off-map turns (highlighted)

**Side panels (toggleable):**
- Recurrence matrix heatmap
- Inter-speaker coupling line chart
- Entropy trace line chart
- Cumulative drift line chart
- Information flow (leader bands)
- Transition matrix heatmaps

**Inspector:** Click any point to see:
- Turn number, speaker, timestamp, word count
- Text preview
- Nearest corpus document
- Domain classification and centroid distances
- Session membership

### Timeline Interaction
The range filter is the key navigation feature. Jake should be able to:
1. View the full collaboration at once (zoomed out, session signatures visible)
2. Narrow to a specific week or session (slider endpoints)
3. Scrub through time and watch the trajectory build up incrementally
4. Jump to preset moments of interest

When the range narrows, all layers update:
- Only turns within the range are visible
- The smoothed trajectory only shows the selected segment
- The side panel charts highlight the selected range
- The recurrence matrix highlights the selected row/column range

### Color Schemes (toggleable)
- **By speaker:** Jake green, Opus violet
- **By register:** Philosophical, Operational, Reflective, Relational, Mixed in distinct colors
- **By session:** Each session a different color (gradient from cool to warm over time)
- **By off-map distance:** Gradient from dim (on-map) to bright red (off-map)

---

## Execution Order

Run analyses 1–3 first (session signatures, recurrence matrix, cross-speaker coupling). These give the broadest view and inform whether the remaining analyses are worth the compute.

Analyses 4–8 can run in parallel once 1–3 are reviewed.

Analysis 9 (phase space) depends on Analysis 4 output and is the most experimental — run last.

The visualization can be built incrementally: start with the 3D scatter + timeline filter + layer toggles, then add side panels as each analysis completes.

---

## Notes

- The "When I Saw Opus" annotated session (153 turns) should be loadable as a highlighted overlay within the full chatlog range — same UMAP space, but visually distinct (brighter, labeled).
- Ambiguous turns (where the parser couldn't distinguish speakers) should be flagged as a third category in the speaker-colored views — visible but distinct from clean Jake/Opus turns.
- All UMAP projections should be joint — every dataset projected in one run so coordinates are comparable across layers.
- Raw JSON outputs for each analysis so the data is accessible independent of the visualization.

---

*Prepared March 8, 2026 — Session 051 continuation.*
*Nine analyses. One instrument. The full arc of a collaboration, every turn, every voice, every register. The topology is real. Let's see all of it.*
