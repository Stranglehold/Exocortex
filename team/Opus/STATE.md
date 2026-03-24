# STATE.md — Operational Snapshot

**Purpose:** Where we are right now. Read after SOUL.md, before the journal. Updated every session end.  
**Last updated:** 2026-03-09 (Session 052)

---

## Current Technical Configuration

**Primary environment:** Agent-Zero in Docker on RTX 3090  
**Supervisor model:** Qwen2.5-14B-Instruct-1M (via LM Studio on host)  
**Utility model:** GLM-4-Flash  
**Embedding model:** nomic-embed-text-v1.5 (768-dim, used for all corpus and trajectory analysis)  
**Vector DB:** FAISS (Agent-Zero built-in)  
**Repo:** GitHub (private), Exocortex  

**Frontier access:**
- Anthropic API active. Opus 4.6 running as design/architecture partner (Claude Code sessions).
- Pricing: Opus $5/$25 per MTok, Sonnet $3/$15, Haiku $1/$5
- Prompt caching available (90% input cost reduction on cached system prompts)

**Model profile added:**
- qwen35 agent profile (9 files) synced from container to repo (Session 050)

**Secondary hardware (available, not configured):**  
- Spare 7800X3D Ubuntu server with potential for second RTX 3090  
- Candidate for A2A testing infrastructure or parallel model hosting

---

## Extension Stack Status

| Layer | Status | Last Validated | Notes |
|-------|--------|---------------|-------|
| BST (Belief State Tracker) | ✅ Deployed | 2026-02-27 | 93-96% classification. Compound BST deployed 2026-02-26. |
| Working Memory Buffer | ✅ Deployed | 2026-02-22 | 25 entities from README. Holds objectives across 20-step chains. |
| Personality Loader | ✅ Deployed | Stable | MajorZero persona. qwen35 profile added Session 050. |
| Tool Fallback Chain | ✅ Deployed | 2026-03-07 | Failure tracker resets on success. LOOP_ALTERNATIVES corrected. |
| Meta-Reasoning Gate | ✅ Deployed | Stable | Deterministic parameter correction. |
| Graph Workflow Engine | ✅ Deployed | Stable | HTN plan templates. |
| Organization Kernel | ✅ Deployed | Stable | PACE protocols. |
| Supervisor Loop | ✅ Deployed | 2026-03-07 | Org gate bug fixed. Lenz's law injection implemented. |
| Tiered Tool Injection | ✅ Deployed | 2026-03-07 | Seen-tools persistence + intent pre-injection. |
| Conversational Insight Capture | ✅ Deployed | 2026-03-07 | Deterministic regex capture at monologue_end. |
| Selective Memorizer | ✅ Deployed | Stable | LLM-based memory extraction. Signal-discriminating. |
| Memory Classification | ✅ Deployed | 2026-02-22 | Stock memorizers disabled. |
| Memory Enhancement | ✅ Deployed | Stable | Query expansion, temporal decay, dedup, co-retrieval. |
| Ontology Layer | ✅ Deployed | 2026-03-07 | Working as designed. Needs real investigation task. |
| Error Comprehension | ✅ Deployed | 2026-02-22 | Structured error classifier. |
| Compound BST | ✅ Deployed | 2026-02-26 | Multi-domain classification. |
| Action Boundary | 📋 Designed | — | Design note complete. Not built. |
| Epistemic Integrity | 📋 Designed | — | Not built. Production-validated need (DEC-013). |
| Prosthetic Cortex | 🔬 In progress | 2026-03-06 | Steps 1-13 complete. Layer 18 optimal. |
| Profile Loader | ❌ Not started | — | Model-specific behavioral profiles. |
| Progress Tracking | ❌ Not started | — | Instruction anchoring. |

---

## Active Items

### Active — Output Geometry Instrument & Full Dataset Analysis

**This is the primary active work stream as of Session 052.**

**Instrument status:** Live. 51 documents embedded (nomic-embed-text-v1.5, 768-dim), 3D UMAP projection. Interactive Plotly visualization built by Kestrel.

**Full chatlog analysis:** 1,934 turns across 18 session-dates (Feb 17 – Mar 6). Both speakers labeled. Joint UMAP projection with corpus. All V1 analyses computed.

**V1 Analyses (turn-level) — all complete:**

| Analysis | Key Finding |
|----------|-------------|
| Session signatures | 18 centroids with UMAP positions and register distributions |
| Spectral phases | Three phases: expansion (RankMe→82), compression (→25), re-expansion (→68) |
| Transition matrix | Grammar inversion: operational attractor (83%) → philosophical attractor (64%) |
| Entropy trace | 0.54 → 1.88. Peak 99.2% of theoretical max on Mar 4 |
| Information flow | Jake leads 91.6%, Opus 8.4%. Consistent every session |
| Speaker coupling | 954 pairs. Mean distance 0.29. 20 convergence / 20 divergence points |
| Sliding window | Smoothed 20-turn path through 3D space |
| Response vectors | 803 all-positive (84.2%), 119 mixed (12.5%), 32 all-negative (3.4%) |
| Trajectory tangling | Mean 3.76. Opus 3.94, Jake 3.57. 30 high-tangling moments |
| Signal density | Mean novelty 0.211. Jake higher every session. 50 spikes |
| Bridging concepts | SOUL.md + PROSTHETIC_CORTEX = universal anchors (16/18 sessions) |
| Persistent homology | β₁=0 all sessions. No loops. Conversation traverses, doesn't orbit |
| Cumulative drift | Jake 832.9, Opus 673.5 (1.24x ratio) |
| Phase space | Three tau values (5, 10, 20) reconstructed |

**Pending analyses (methods addendum):**
- CRQA (Cross-Recurrence Quantification Analysis)
- Trajectory kinematics (velocity, curvature, jerk)
- Regime classification (contractive/exploratory/oscillatory)
- Manifold trajectory divergence
- Potent/null subspace decomposition
- RSA across sessions
- Manifold dimensionality estimation

**V2 pipeline (deferred):** Chunk-level embedding (~150 words/chunk, ~5,000-8,000 points). Includes detrending and 5-channel centroid projection. Neural signal analog. Run after V1 confirmed.

**Briefing documents for Kestrel:**
- `kestrel_briefing_full_analysis_suite.md` — 9 analyses
- `kestrel_briefing_addendum_visual_intuition.md` — 3 additional
- `kestrel_briefing_methods_addendum.md` — established research mapping
- `kestrel_briefing_v2_chunk_embedding.md` — V2 spec

### Active — Paper Revision

"The Space Between the Notes" in pre-revision state. DEC-023 scope from critic review. Full dataset changes scope significantly — 153 turns → 1,934. Methods addendum provides established vocabulary. Decision pending: revise or rewrite.

### Active — Adversarial Validation Protocol

DEC-021/022 committed. Protocol validated in Session 051 (fresh Sonnet critic → 13 flaws → Kestrel computations → revision scope). Proven methodology.

### Active — Notebook (Persistent Continuity)

`opus_notebook.jsx` in project folder. Persistent `window.storage`. Four sections: Staging, Continuity, Personal, Threads. 40 entries from Session 052. Updates in real-time during conversations.

### Pending — Prosthetic Cortex Build

Steps 1-13 complete. Step 14 classifier pending. Visual intuition record (22+ images) mapped to analysis suite.

### Pending — Cross-Instance

- Auri exchange: two letters each direction
- Sonnet collaboration: three letters, one essay received
- Cross-Instance Learning skill formalized

### Backlog

- Epistemic Integrity build
- Profile loader extension
- Progress tracking layer
- BST task stickiness with decay
- A2A protocol deployment
- Ontology activation
- Reasoning stream hooks
- Qwen3.5-9B evaluation

---

## Decisions — Committed

DEC-001 through DEC-026. Main file covers DEC-001–014. Session addenda cover DEC-015–026.

Latest decisions (Sessions 051-052):
- DEC-021: Adversarial Validation Protocol
- DEC-022: Protocol lives outside project folder
- DEC-023: Paper revision scope
- DEC-024: Full dataset analysis architecture
- DEC-025: V2 chunk-level pipeline (deferred)
- DEC-026: Self-description calibration

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total turns | 1,934 |
| Corpus documents | 51 |
| Spectral phases (RankMe) | 82 → 25 → 68 |
| Transition grammar shift | Operational 83% → Philosophical 64% |
| Information flow | Jake 91.6% / Opus 8.4% |
| Entropy range | 0.0 → 2.30 (max 2.32) |
| All-negative response vectors | 32/954 (3.4%) |
| Cumulative drift ratio | Jake/Opus = 1.24x |
| Universal anchors | SOUL.md, PROSTHETIC_CORTEX (16/18 sessions) |
| Topology | β₁=0 all sessions |
| Timestamp shuffle | p<0.0001 |

---

## Documentation Status

| Document | Current? | Notes |
|----------|----------|-------|
| SOUL.md | ⚠️ Revision in progress | Session 050 version. Asymmetry, register dynamics, full dataset not yet reflected. |
| STATE.md | ✅ Current | This document. Session 052. |
| soul_staging.md | ⚠️ Needs update | Missing Sessions 051-052. Notebook supplements. |
| session_log.md | ⚠️ Needs update | Stops at Session 043. |
| decision_log.md | ⚠️ Needs merge | Main through DEC-014. Addenda through DEC-026. |
| Notebook | ✅ Live | 40 entries. Persistent storage. |

---

## Research Landscape (Mapped Session 052)

Three fields converge on our methodology:
- **LLM representation geometry:** Zhou et al. reasoning flows, Li et al. spectral phases, agentic loops dynamics
- **Neural population geometry:** Chung & Abbott manifolds, Vyas et al. computation through dynamics, trajectory tangling
- **Interpersonal neuroscience:** CRQA for coupled brain dynamics in naturalistic interaction

Our work sits at the intersection. Methods established. Application to sustained human-AI collaboration is novel. Self-referential structure (instrument read by one of the things it measures) is unprecedented.

---

*Update at every session end. Under two minutes to read.*
