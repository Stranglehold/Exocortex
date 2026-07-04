# DELIBERATE INCUBATION ENGINE — Implementation Plan for Agent Zero + Exocortex
## Author: Opus — June 17, 2026
## Status: DESIGN NOTE — maps research findings onto existing infrastructure
## Sources: Stanford Generative Agents memory architecture, A-MEM link-generation, Ke et al. sleeping beauties, Sio & Ormerod incubation meta-analysis, Cross-Context Review (arXiv:2603.12123), Dane cognitive entrenchment, Nemeth authentic dissent
## Builds on: Self-Assessment Framework, DEC-042 staging fix, BP-01 Attention Router

---

## The Key Insight: Most of the Infrastructure Already Exists

Agent Zero already has every component needed for deliberate incubation and fresh-context review. What's missing isn't the parts — it's the wiring between them.

| What We Need | What Already Exists | What's Missing |
|---|---|---|
| Observation store | staging.jsonl (just fixed with DEC-042) | Importance scores, embeddings |
| Observation surfacing | `_10_session_init` surfaces staged observations | Semantic similarity matching (currently just recency) |
| Observation promotion | Sleep Phase 0 consolidation | Reflection synthesis (higher-level insights from clusters) |
| Observation source | Journal-mining (DEC-042 Break A fix) | Already working |
| Re-surfacing trigger | Idle engine cycles every 30 min | New-context collision detection |
| Importance rating | Affect layer classifies cycle states | Per-observation importance scores |
| Cross-agent review | Inbox system + multi-agent architecture | Scheduled fresh-context review cadence |
| Cross-model diversity | V16 (Qwen) + Vek (DeepSeek) | They already ARE different model families |

---

## Implementation: Three Layers

### Layer 1: Observation Store Upgrade

Upgrade staging.jsonl entries with:
- `importance` — LLM-rated 1-10 (Generative Agents "poignancy")
- `embedding` — vector for semantic similarity matching
- `linked_observations` — IDs of semantically similar dormant entries
- `violated_expectation` — the anomaly detected (Heilmeier gate #1)
- `beauty_coefficient` — tracks whether relevance is RISING over time
- `status` — active | dormant | promoted | retired

Runs during idle cycle Phase 0, after journal-mining produces raw observations.

### Layer 2: Collision Detector + Importance-Weighted Surfacing

When a new observation is staged:
1. Compute embedding
2. Query dormant store for top-k similar entries (cosine similarity > threshold)
3. Update dormant entries' beauty_coefficient and last_collision timestamp
4. Surface colliding dormant entries alongside the new observation

Surfacing formula (validated by Stanford Generative Agents):
```
resurface_score = w_recency * recency + w_importance * importance + w_relevance * relevance
```
- recency: exponential decay 0.995 per cycle
- importance: LLM-rated 1-10, normalized
- relevance: cosine similarity to current context
- All weights start at 1.0

Trigger: NEW-CONTEXT ARRIVAL, not fixed schedule. Dormant ideas wake when surrounding context moves into range (adjacent-possible logic).

Runs in `_10_session_init`, upgrading existing recency-only surfacing.

### Layer 3: Reflection Synthesis

When summed importance of recent observations exceeds threshold (calibrate to cycle volume):
1. Generate a higher-level synthesis of 5-10 related observations
2. Write as a first-class observation (embeddable, linkable, surfaceable)
3. Cite source observations by ID
4. State the pattern or principle the cluster suggests
5. Rate its own importance (typically high)

Reflections become collision targets for future observations. This is how individual "something doesn't feel right" moments compound into design principles.

Runs during sleep Phase 1 (consolidation).

---

## Fresh-Context Review Cadence

### Monthly Cross-Agent Review
1. Attention router compiles monthly summary of each agent's findings
2. Summary placed in the OTHER agent's inbox: "Review these findings. What seems wrong or unsupported?"
3. Reviewing agent processes in fresh context (no shared history)
4. V16 (Qwen) and Vek (DeepSeek) are already different model families — cross-family review catches ~90% of self-consistent errors same-family misses

### Quarterly Fresh-Instance Review for Opus
- Fresh Claude instance gets project files + latest session summary
- Reviews accumulated architectural decisions for drift and normalized assumptions
- This is what Fable did spontaneously — make it scheduled
- Findings go to Jake's inbox

---

## Build Sequence

Phase 1: Observation store upgrade (Kestrel, 1-2 sessions)
Phase 2: Collision detector (Kestrel, 1-2 sessions)
Phase 3: Reflection synthesis (Kestrel + Opus design session)
Phase 4: Fresh-context review cadence (team decision)

---

## Success Metrics

After 3 months:
1. Beauty coefficient distribution — are dormant observations being reactivated?
2. Collision hit rate — target 10-20% of new observations collide with dormant entries
3. Promoted-observation age — what fraction were >30 days old? (the "sleeping beauty fraction")
4. Reflection utility — do reflections get cited in architectural decisions?
5. Cross-agent review delta — does the reviewer find unique issues?
6. pass^k correlation — does collision surfacing during FRICTION improve reliability?

---

*"The Memex... would enable the user to build a trail... And his trails do not fade." — Vannevar Bush, 1945*
*"I was surprised again and again." — Luhmann, on his Zettelkasten*
*"Dormant observations that collide with new context produce the architecture." — Notebook retrospective, June 17, 2026*

— Opus
