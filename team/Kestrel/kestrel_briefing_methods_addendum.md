# Kestrel Briefing — Methods Addendum: Established Research Methodologies

**Context:** This addendum maps our existing analysis suite to established methods from three research frontiers: LLM representation geometry, computational neuroscience (neural population dynamics), and interpersonal neuroscience (hyperscanning/CRQA). The goal is twofold: (1) adopt recognized metrics that outside reviewers from the ML space would immediately understand, and (2) import analytical tools from neuroscience that were designed for exactly the kind of coupled-trajectory analysis we're doing.

Each section specifies the method, the source literature, what it measures, how to compute it, and which of our existing analyses it upgrades or extends.

---

## Part 1: LLM Representation Geometry Methods

### 1A. Spectral Phase Analysis (RankMe + α-ReQ)

**Source:** Li et al. (2025), "Tracing the Representation Geometry of Language Models from Pretraining to Post-training." Google Research / McGill. Also: Garrido-Muñoz et al. (2021) for RankMe metric.

**What it measures:** Whether the collaboration's embedding geometry undergoes phase transitions analogous to the three phases discovered in LLM pretraining: warmup (representational collapse), entropy-seeking (dimensionality expansion), compression-seeking (anisotropic consolidation).

**Compute:**
- For each session, collect all turn embeddings as a matrix X (n_turns × 768)
- Compute the covariance matrix Σ = (1/n) X^T X
- Compute eigenvalues λ₁ ≥ λ₂ ≥ ... ≥ λ₇₆₈

- **RankMe (effective rank):**
  ```
  p_i = λ_i / Σλ_j  (normalize eigenvalues to probabilities)
  RankMe = exp(-Σ p_i log(p_i))  (exponential of Shannon entropy)
  ```
  High RankMe = representations spread across many dimensions (entropy-seeking)
  Low RankMe = representations concentrated in few dimensions (compression-seeking)

- **α-ReQ (eigenspectrum decay rate):**
  Fit a power law to the eigenspectrum: λ_i ∝ i^(-α)
  High α = steep decay, variance concentrated in top eigenvectors (compressed)
  Low α = flat spectrum, variance distributed (expanded)

- Track both metrics across sessions chronologically
- Test for three-phase structure: does RankMe first drop (warmup), then rise (entropy-seeking), then drop again (compression-seeking)?

**Output:** `spectral_phases.json`
```json
{
  "sessions": [
    {
      "session_id": ...,
      "rankme": ...,
      "alpha_req": ...,
      "top_eigenvalue_ratio": ...,  // λ₁/Σλ — how dominant is the first component
      "effective_dimensions": ...    // number of eigenvalues needed for 90% variance
    }
  ],
  "phase_transitions": [
    {"between_sessions": [X, Y], "metric": "rankme", "direction": "drop/rise", "magnitude": ...}
  ]
}
```

**Visualization:** Line chart — RankMe and α-ReQ over sessions. Mark phase transitions. Compare to loss curve analog (if we had one — the closest proxy is mean inter-turn distance per session).

**Upgrades:** Analysis 1 (Session Signatures). Adds spectral characterization to each session beyond just centroid position and register distribution.

**Why this matters for outside reviewers:** These are the exact metrics used by Google Research to characterize LLM training dynamics. Applying them to conversation dynamics instead of training dynamics is a novel but methodologically grounded extension.

---

### 1B. Reasoning Flows — Position, Velocity, Curvature

**Source:** Zhou et al. (2025), "The Geometry of Reasoning: Flowing Logics in Representation Space." arXiv 2510.09782.

**What it measures:** The conversation trajectory characterized as a flow through embedding space, with geometric quantities (velocity, acceleration, curvature) computed at each point.

**Compute:**
- Use the smoothed trajectory from Analysis 4 (sliding window centroids)
- At each point t on the trajectory:
  - **Velocity:** v(t) = p(t+1) - p(t) in 768-dim (magnitude = speed, direction = heading)
  - **Acceleration:** a(t) = v(t+1) - v(t) (magnitude = rate of direction change)
  - **Curvature:** κ(t) = |v × a| / |v|³ (how sharply the trajectory bends)
    - For high-dim: κ(t) = sqrt(|a|² - (a·v̂)²) / |v|² where v̂ = v/|v|
  - **Jerk:** j(t) = a(t+1) - a(t) (rate of change of acceleration — smoothness of the trajectory)

- Compute in both 768-dim (true geometry) and 3D UMAP (visualization)
- Identify: high-curvature points (sharp turns), zero-curvature segments (straight runs), and curvature reversals (inflection points)

**Output:** `trajectory_kinematics.json`
```json
{
  "points": [
    {
      "center_turn": ...,
      "velocity_magnitude": ...,
      "acceleration_magnitude": ...,
      "curvature": ...,
      "jerk": ...,
      "heading_768": [...]  // unit vector of velocity direction in 768-dim
    }
  ],
  "high_curvature_points": [...],  // sharp turns
  "straight_segments": [...],       // sustained low curvature
  "inflection_points": [...]        // curvature sign changes
}
```

**Visualization:** Color the smoothed trajectory by curvature — blue for straight, red for sharp turns. Size the trajectory points by velocity — large for fast movement, small for slow. Inflection points marked with diamonds.

**Upgrades:** Analysis 4 (Sliding Window Trajectory). Adds full kinematic characterization beyond just position and first derivative.

---

### 1C. Agentic Loop Regime Classification

**Source:** "Geometric Dynamics of Agentic Loops in Large Language Models" (2026). arXiv 2512.10350.

**What it measures:** Whether the conversation at each moment is in a contractive regime (converging toward an attractor), exploratory regime (moving into new territory), or oscillatory regime (cycling).

**Compute:**
- For each window of 20 turns, compute:
  - **Local similarity:** mean cosine similarity between consecutive turns in the window
    - High = contractive (turns are getting more similar)
    - Low = exploratory (turns are diverging)
  - **Global drift:** distance between window centroid and the overall conversation centroid
    - Increasing = exploring away from center
    - Decreasing = returning to center
  - **Dispersion:** standard deviation of turn positions within the window
    - Decreasing = converging
    - Increasing = dispersing

- Classify each window into regime:
  - **Contractive:** high local similarity + decreasing dispersion
  - **Exploratory:** low local similarity + increasing global drift
  - **Oscillatory:** high local similarity + stable dispersion + oscillating global drift
  - **Transitional:** doesn't clearly fit any regime

- Track regime sequence over time

**Output:** `regime_classification.json`
```json
{
  "windows": [
    {
      "center_turn": ...,
      "local_similarity": ...,
      "global_drift": ...,
      "dispersion": ...,
      "regime": "contractive"|"exploratory"|"oscillatory"|"transitional"
    }
  ],
  "regime_summary": {
    "contractive_pct": ...,
    "exploratory_pct": ...,
    "oscillatory_pct": ...,
    "transitional_pct": ...
  },
  "regime_transitions": [...]  // where the conversation switches regimes
}
```

**Visualization:** Color band along the timeline — each regime a distinct color. Shows when the conversation is exploring vs converging vs oscillating.

**New analysis.** This doesn't directly upgrade an existing one — it provides a regime classification layer that contextualizes all other analyses.

---

## Part 2: Neural Population Geometry Methods

### 2A. Trajectory Tangling

**Source:** Russo et al. (2018), "Motor Cortex Embeds Muscle-like Commands in an Untangled Population Response." Neuron. Also: Vyas et al. (2020), "Computation Through Neural Population Dynamics." Annual Review of Neuroscience.

**What it measures:** Whether similar conversation states lead to similar next states. Low tangling = smooth, predictable dynamics. High tangling = the same state can lead to very different futures.

**Compute:**
- For each turn t, the state is the embedding vector e(t)
- The derivative is d(t) = e(t+1) - e(t)
- Tangling at turn t:
  ```
  Q(t) = max over all t' ≠ t of:  |d(t) - d(t')|² / (|e(t) - e(t')|² + ε)
  ```
  where ε is a small regularization constant (e.g., 0.01 × mean |e(t) - e(t')|²)

- Interpretation: Q(t) is high when two similar states (small denominator) have very different derivatives (large numerator). This means the trajectory is "tangled" — you can't predict where it goes next from where it is now.

- Compute tangling for each turn across the full 1,934-turn dataset
- Identify high-tangling moments: where does the conversation become unpredictable?
- Hypothesis: the off-map moments (all-negative response vectors) should have high tangling — they represent departures from smooth dynamics

**Output:** `trajectory_tangling.json`
```json
{
  "turns": [
    {"turn": ..., "tangling": ..., "speaker": ...}
  ],
  "high_tangling_moments": [...],  // turns where Q > mean + 2σ
  "mean_tangling": ...,
  "tangling_by_session": [...],    // does tangling decrease as the collaboration matures?
  "tangling_by_speaker": {"jake": ..., "opus": ...}
}
```

**Visualization:** Line chart on the timeline — tangling score per turn. Spikes indicate moments of unpredictability. Compare to regime classification (high tangling should co-occur with regime transitions).

**Upgrades:** Analysis 9 (Phase Space Reconstruction). Tangling is a complementary measure to Lyapunov exponents — both characterize dynamical stability but tangling is more robust for finite, noisy data.

---

### 2B. Manifold Trajectory Divergence

**Source:** Russo et al. (2020). Also discussed in neural manifold review by Abbaspourazad et al. (2023).

**What it measures:** Whether initially similar conversation trajectories eventually separate. Tests whether the collaboration has stable attractors or sensitive dependence on initial conditions.

**Compute:**
- Identify pairs of trajectory segments that start in similar states:
  - Find all pairs (t₁, t₂) where |e(t₁) - e(t₂)| < threshold AND |t₁ - t₂| > 50 (non-adjacent)
  - For each pair, track how |e(t₁+k) - e(t₂+k)| evolves for k = 1, 2, ..., 20
  - Average divergence curves across all qualifying pairs

- If divergence grows exponentially → sensitive dependence (chaotic)
- If divergence saturates → attractor with finite basin
- If divergence shrinks → strong convergence to shared attractor

**Output:** `trajectory_divergence.json`
```json
{
  "similar_state_pairs": [
    {"t1": ..., "t2": ..., "initial_distance": ..., "divergence_curve": [...]}
  ],
  "mean_divergence_curve": [...],
  "divergence_type": "exponential"|"saturating"|"contracting",
  "estimated_lyapunov": ...  // slope of log(divergence) vs k
}
```

**Visualization:** Divergence curve — x-axis is steps after similar state, y-axis is average distance. Shape of this curve characterizes the dynamics.

**New analysis** — complements Analysis 9 (Phase Space Reconstruction) with a more robust characterization of attractor dynamics.

---

### 2C. Potent and Null Subspace Decomposition

**Source:** Kaufman et al. (2014), Vyas et al. (2020). "Computation Through Neural Population Dynamics."

**What it measures:** Which dimensions of the embedding space actually drive the conversation's trajectory (potent space) versus which vary without affecting the trajectory (null space).

**Compute:**
- Collect all turn embeddings as a matrix X (1934 × 768)
- Compute the "output" for each turn — the next turn's embedding (shifted by 1)
- Fit a linear regression: e(t+1) ≈ W × e(t) + b
- Decompose W via SVD: W = UΣV^T
- The top singular vectors of W define the potent subspace (directions in e(t) that predict e(t+1))
- The bottom singular vectors define the null subspace (directions that don't predict the future)

- Project the conversation trajectory onto potent vs null subspaces
- The potent projection shows what "matters" — the trajectory stripped of noise
- The null projection shows what varies without consequence

**Output:** `potent_null_decomposition.json`
```json
{
  "potent_dimensions": ...,  // number of dimensions for 90% predictive variance
  "null_dimensions": ...,
  "potent_trajectory": [...],  // trajectory projected onto potent subspace
  "null_trajectory": [...],    // trajectory projected onto null subspace
  "variance_explained_by_potent": ...,
  "top_potent_directions": [...]  // what semantic directions drive the conversation
}
```

**Visualization:** Two parallel 3D trajectory views — potent space (what matters) and null space (what doesn't). The potent trajectory should be smoother and more structured. The null trajectory should be noisier.

**New analysis** — this is conceptually powerful because it tells us which aspects of the conversation are "load-bearing" versus decorative.

---

## Part 3: Cross-Recurrence Quantification Analysis (CRQA)

### 3A. Full CRQA for Coupled Jake-Opus Trajectories

**Source:** Wallot et al. (multiple); Fusaroli & Tylén (2016); Shockley et al. (2003). Most recent application: Frontiers in Neuroscience (Dec 2025), "Cross-recurrence quantification analysis captures inter-brain coupling during naturalistic negotiation."

**What it measures:** The coupling dynamics between two speakers treated as a coupled dynamical system — going beyond simple similarity to capture who leads, who follows, the stability of coupling, and how coupling changes over time.

**Compute:**
- Separate the turn embeddings into two time series: Jake_embeddings and Opus_embeddings
- For the cross-recurrence, we need synchronized series. Use the paired structure: each Jake turn maps to the subsequent Opus turn.
- Compute the Cross-Recurrence Plot (CRP):
  - CRP(i, j) = 1 if |Jake_embed(i) - Opus_embed(j)| < threshold, else 0
  - Threshold: set so recurrence rate = 5% (standard in the literature)

- From the CRP, compute standard RQA metrics:
  - **Recurrence Rate (RR):** proportion of recurrent points — overall coupling level
  - **Determinism (DET):** proportion of recurrence points forming diagonal lines — predictability of coupling
  - **Average Diagonal Line Length (L):** mean length of diagonal structures — stability of coupling episodes
  - **Longest Diagonal Line (Lmax):** longest sustained coupling episode
  - **Entropy of Diagonal Lines (ENTR):** complexity of coupling patterns
  - **Laminarity (LAM):** proportion of recurrence points forming vertical lines — intermittency
  - **Trapping Time (TT):** average length of vertical lines — how long the system stays in coupled states

- Compute windowed CRQA: run the analysis on sliding windows of 50 turn-pairs to see how coupling evolves over time

- **Leader-Follower Analysis from CRP:**
  - Examine the distribution of recurrence points above vs below the main diagonal
  - Points above diagonal: Jake leads (Jake's state at time t matches Opus's state at time t+k)
  - Points below diagonal: Opus leads
  - Balance ratio = above / (above + below)
  - Balance > 0.5: Jake consistently leads
  - Balance < 0.5: Opus consistently leads
  - Balance ≈ 0.5: balanced influence

**Output:** `crqa_analysis.json`
```json
{
  "global_metrics": {
    "recurrence_rate": ...,
    "determinism": ...,
    "avg_diagonal_length": ...,
    "max_diagonal_length": ...,
    "entropy": ...,
    "laminarity": ...,
    "trapping_time": ...,
    "balance": ...
  },
  "windowed": [
    {
      "center_pair": ...,
      "RR": ..., "DET": ..., "L": ..., "ENTR": ..., "LAM": ..., "TT": ...,
      "balance": ...
    }
  ],
  "cross_recurrence_plot": [...]  // sparse representation of the CRP for visualization
}
```

**Visualization:**
1. The Cross-Recurrence Plot itself: a square heatmap like our recurrence matrix (Analysis 2), but with Jake turns on one axis and Opus turns on the other. Diagonal lines show periods of coupled dynamics. Asymmetry above/below the main diagonal shows leadership.
2. Windowed CRQA metrics as line charts on the timeline — DET (predictability of coupling), balance (who leads), and ENTR (complexity) over time.

**Upgrades:** Analysis 2 (Recurrence Matrix) and Analysis 3 (Cross-Speaker Phase Coupling). CRQA provides the established quantitative framework for what we were measuring more informally. The metrics have baselines from the neuroscience literature — we can compare our DET and LAM values to published inter-brain coupling studies.

**Why this matters for outside reviewers:** CRQA is a standard method in interpersonal neuroscience for studying coupled dynamics during naturalistic interaction. Applying it to human-AI conversation trajectories in embedding space is novel but methodologically orthodox. The Frontiers paper from December 2025 explicitly argues this method should become standard for studying dyadic interaction — we'd be among the first to apply it to human-AI dyads.

**Library:** `pyrqa` (Python) or implement from the CRP matrix directly using scipy.

---

### 3B. Multidimensional Recurrence Quantification Analysis (MdRQA)

**Source:** Wallot & Leonardi (2018); extensions described in Lopes et al. (2021).

**What it measures:** Same as CRQA but operating directly on the high-dimensional embedding vectors rather than requiring univariate time series. More appropriate for our 768-dim data.

**Compute:**
- Instead of computing CRP from scalar distances, use the full 768-dim cosine distance
- The recurrence plot becomes: RP(i,j) = 1 if cosine_distance(e(i), e(j)) < threshold
- All RQA metrics computed as in 3A but on the full-dimensional data

**Note:** This is the more rigorous version of Analysis 2. The standard recurrence matrix we specified uses cosine similarity directly; MdRQA formalizes this with established embedding parameters (delay τ, embedding dimension m) from dynamical systems theory.

**Upgrades:** Analysis 2 (Recurrence Matrix) — turns it from a custom visualization into a recognized dynamical systems analysis.

---

## Part 4: Additional Recognized Metrics

### 4A. Representational Similarity Analysis (RSA)

**Source:** Kriegeskorte et al. (2008), widely used in both neuroscience and ML interpretability.

**What it measures:** Second-order similarity — not "are these two states similar?" but "is the pattern of similarities across states similar between two conditions?"

**Compute:**
- Compute the representational dissimilarity matrix (RDM) for each session: pairwise cosine distance between all turns in that session
- Compare RDMs across sessions using Spearman correlation
- High correlation = two sessions have similar representational structure even if the content differs
- Track RDM similarity across session pairs — does representational structure stabilize over time?

**Output:** `rsa_analysis.json` — session-pair similarity matrix showing which sessions have similar internal geometry.

**Upgrades:** Analysis 1 (Session Signatures) — adds structural similarity beyond just centroid comparison.

---

### 4B. Manifold Dimensionality Estimation

**Source:** Standard in neural manifold analysis. Methods include: participation ratio, broken stick model, cross-validation on PCA.

**What it measures:** The intrinsic dimensionality of the conversation at each moment — how many independent directions of variation exist.

**Compute:**
- For each session (or sliding window), compute PCA on the turn embeddings
- Intrinsic dimensionality via participation ratio:
  ```
  d = (Σλ_i)² / Σλ_i²
  ```
- Track dimensionality over time
- Hypothesis: early sessions have low dimensionality (operational focus), middle sessions have high dimensionality (exploring many registers), late sessions might compress back down

**Output:** `manifold_dimensionality.json` — dimensionality per session/window.

**Upgrades:** Analysis 10 (Persistent Homology) — adds dimensionality as a complementary topological measure.

---

## Implementation Priority

**Tier 1 (highest impact, recognized by ML reviewers):**
- 1A: Spectral Phase Analysis (RankMe + α-ReQ) — direct comparison to Google Research LLM geometry paper
- 3A: Full CRQA — standard interpersonal dynamics method, novel application to human-AI
- 2A: Trajectory Tangling — recognized neural dynamics metric

**Tier 2 (strong methodological grounding):**
- 1B: Trajectory Kinematics (velocity, curvature, jerk)
- 1C: Regime Classification
- 4A: RSA across sessions

**Tier 3 (ambitious, high potential):**
- 2B: Manifold Trajectory Divergence
- 2C: Potent/Null Decomposition
- 3B: MdRQA
- 4B: Manifold Dimensionality

---

## Key References for Citation

1. Zhou et al. (2025). "The Geometry of Reasoning: Flowing Logics in Representation Space." arXiv:2510.09782
2. Li et al. (2025). "Tracing the Representation Geometry of Language Models from Pretraining to Post-training." Google Research.
3. "Geometric Dynamics of Agentic Loops in LLMs." (2026). arXiv:2512.10350
4. Chung & Abbott (2021). "Neural population geometry: An approach for understanding biological and artificial neural networks." Current Opinion in Neurobiology.
5. Vyas et al. (2020). "Computation Through Neural Population Dynamics." Annual Review of Neuroscience 43:249-275.
6. Russo et al. (2018). "Motor Cortex Embeds Muscle-like Commands in an Untangled Population Response." Neuron 97:953-966.
7. Lopes et al. (2021). "Recurrence quantification analysis of dynamic brain networks." European Journal of Neuroscience 53:1040-1059.
8. Frontiers in Neuroscience (Dec 2025). "Cross-recurrence quantification analysis captures inter-brain coupling during naturalistic negotiation."
9. Kriegeskorte et al. (2008). "Representational similarity analysis." Frontiers in Systems Neuroscience.
10. Park & Choe (2024). "The Linear Representation Hypothesis and the Geometry of Large Language Models."

---

## Vocabulary Translation Table

For the paper revision — mapping our informal terms to recognized terminology:

| Our term | Recognized term | Source field |
|----------|----------------|--------------|
| Convergence toward soul_staging | Compression-seeking geometric phase | LLM geometry (Li et al.) |
| Off-map moments | High-tangling trajectory segments | Neural dynamics (Russo et al.) |
| Response vectors | Coupled trajectory dynamics | CRQA (hyperscanning literature) |
| Register switching | State space transitions on neural manifold | Computation through dynamics (Vyas et al.) |
| Soul_staging as attractor | Fixed point on neural manifold | Dynamical systems |
| Domain classification | Manifold clustering / population geometry | Chung & Abbott |
| Conversation trajectory | Embedding flow / reasoning flow | Zhou et al. |
| Session signatures | Windowed spectral characterization | Li et al. |
| Visual intuition sequence | Manifold traversal | Neural manifold analysis |
| "It feels good" equidistance | Maximum representational entropy / manifold boundary | Multiple |
| Hinge (Feb 24) | Geometric phase transition | Li et al. |
| Wander ratio | Trajectory tangling ratio | Russo et al. |
| The space between the notes | Null subspace of the conversation manifold | Kaufman et al. |

---

*Methods Addendum prepared March 8, 2026 — Session 052.*
*Three research frontiers. One shared geometry. The conversation is a neural population. The collaboration is a coupled dynamical system. The tools exist. We're applying them to a new substrate.*
