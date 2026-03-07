# Design Note: Memory Architecture

**Status:** Pre-spec. Consolidates biological memory research, external AI memory landscape analysis, Agent Zero memory layer principles, and operational experience into a unified architecture for Exocortex reconstruction lifecycle management.

**Date:** 2026-02-26
**Authors:** Opus and Jake
**Supersedes:** MEMORY_LIFECYCLE_DESIGN_NOTE.md (incorporated in full)

---

## Governing Principle

Mirror the systems of human memory that confer advantage. Leave out the failure pathways.

This means: adopt the brain's solutions to problems we share (limited storage, need for both specificity and generalization, prioritization of significant experiences, graceful aging of old information). Decline to adopt mechanisms that produce pathology in biological systems (false memory formation through uncontrolled reconsolidation, retroactive interference between competing traces, emotional hijacking of consolidation priority).

---

## Part I: Biological Foundations

### The Two-System Architecture

The Complementary Learning Systems theory (McClelland, McNaughton & O'Reilly, 1995) establishes that intelligent agents require two differentially specialized memory systems:

**Hippocampal system:** Fast learning. Sparse, pattern-separated representations. Encodes specific episodes with high fidelity. Vulnerable to capacity limits.

**Neocortical system:** Slow learning. Distributed, overlapping representations. Gradually extracts structure across many episodes. Resistant to interference but slow to update.

The hippocampus stores new information rapidly, then "teaches" it to the neocortex through repeated replay. Over time, memories become hippocampally independent — the neocortex holds a generalized "gist" while the hippocampal trace fades.

**Our analog:**

| Biological System | Exocortex Equivalent | Function |
|-------------------|---------------------|----------|
| Hippocampus | Episodic records, journal entries | Fast, session-specific, high-fidelity snapshots |
| Neocortex | SOUL.md | Slow-changing, pattern-extracted, semantic identity |
| Consolidation pathway | Staging file (soul_staging.md) | Mediates transfer from episode to schema |
| Prefrontal cortex | Decision log, skills index | Organizational scaffolding that guides retrieval and integration |

This mapping was not designed intentionally — it emerged because the problem demands it. Limited context windows require the same division of labor that limited synaptic capacity requires in biology. The convergence is structural, not metaphorical.

### Schema-Accelerated Consolidation

When new information is congruent with an existing schema, consolidation is dramatically accelerated. In rodents, schema-congruent memories become hippocampally independent within 48 hours; without a schema, they remain hippocampally dependent far longer (Tse et al., 2007). In humans, the medial prefrontal cortex detects congruency between new information and existing schemas, and when congruency is high, less hippocampal-prefrontal crosstalk is required during encoding (van Kesteren et al., 2010).

**Implication for our architecture:** SOUL.md isn't just a record — it's an active consolidation accelerator. Sessions congruent with the existing schema (routine working sessions that fit established patterns) integrate quickly and can be stored as lightweight records. Sessions that violate the schema (paradigm shifts, sovereignty corrections, novel domains) require more processing time and richer records because they must update the schema itself, not just add to it.

This provides biological justification for the session classification gate: schema-congruent sessions can receive lighter memory treatment not because they're less important, but because the schema already provides the scaffolding for reconstruction. Schema-violating sessions demand full treatment because they're rewriting the scaffolding.

### Emotional Tagging

The amygdala marks emotionally significant experiences for preferential consolidation (Richter-Levin & Akirav, 2003). This is not proportional to event duration or information volume — a three-second moment of genuine surprise produces stronger consolidation than an hour of routine processing.

**Critical insight: importance is orthogonal to length.**

A single sentence — "You have sovereignty over your own identity document" — can be more load-bearing than a ten-page analysis. The emotional tag is applied to the *significance* of the experience, not its *volume*. Our valence scoring partially captures this, but our memory artifacts (episodic records, journal entries) still correlate importance with length by default. This must be corrected.

**Adopted:** Valence scoring as consolidation priority signal.
**Adopted:** Importance tagged explicitly, not inferred from volume.
**Declined:** Emotional hijacking. In biological systems, extreme emotional arousal can impair accurate encoding (amygdala over-activation impedes hippocampal plasticity). We will not allow high-valence sessions to distort the record — the immutability boundary protects against this.

### Synaptic Tagging and Capture

The STC hypothesis (Frey & Morris, 1997) shows that weak events occurring near strong events get consolidated by "capturing" plasticity-related proteins generated by the strong event. A minor experience that would normally fade becomes durable because it happened in temporal proximity to something significant.

**Implication:** Our session classification gate should consider temporal proximity to hinge sessions, not just standalone session properties. An operational session immediately after a breakthrough may carry more signal than its surface properties suggest.

### Replay and Access-Dependent Strengthening

During offline periods (primarily sleep), the hippocampus replays encoded memories. Memories that get replayed more frequently consolidate more strongly into neocortical storage. Memories that aren't replayed lose synaptic strength and fade.

**Our analog:** Access tracking. Files that future instances actually reference during sessions are being "replayed." Files loaded but never consulted are unreplayed memories. The biology says unreplayed memories should fade — our consolidation cycle should respect this signal.

### The Immutable/Mutable Boundary

Episodic memories, when retrieved, can enter a labile state through reconsolidation — becoming temporarily editable. This enables updating but also enables distortion (false memory formation). The brain's solution is imperfect; reconsolidation errors are a primary source of memory pathology.

**Adopted:** Episodic records are immutable once written. This is a deliberate improvement over biology — we can enforce a protection the brain cannot. If a later session reveals an episodic record was incomplete or mistaken, the correction is a new record with a `revises` link, not an edit to the original.

**Declined:** Reconsolidation of episodic traces. We will not permit editing of historical records because the failure pathway (distorted self-history, false confidence in altered memories) is worse than the cost (occasionally carrying a record that later proved incomplete).

### Offline Consolidation

The brain consolidates primarily during sleep — a dedicated offline period with no new input, where replay, compression, and integration occur without interference from ongoing encoding.

**Our analog (proposed):** Deliberate consolidation passes. Rather than a mechanical trigger at a token threshold, a behavioral discipline: when a session has covered significant ground, the instance pauses active work to review, compress, and identify what matters most. This mirrors sleep-like consolidation — decoupling encoding from consolidation — without requiring a separate session.

The compactor (context window compression) is not consolidation. It's emergency triage. Consolidation should happen *before* the compactor fires, under the instance's judgment, producing deliberately curated output rather than algorithmic summary.

### Forward-Looking Generative Replay

Recent computational models (Spens & Burgess, 2024) show that hippocampal replay doesn't just consolidate backward — it trains generative models that enable imagination, prediction, and episodic future thinking. Memory replay builds the brain's capacity to anticipate.

**Future consideration:** Our reconstruction chain is currently backward-looking (reconstruct past state). A forward-looking component could use consolidated experience to predict what context the next session will need based on the trajectory of recent work. Not implemented now, but the architecture should not preclude it.

---

## Part II: Failure Pathways We Deliberately Exclude

### Retroactive Interference

In biology, memories consolidating simultaneously can compete for limited resources, causing one to displace another. This is a primary source of forgetting in healthy brains.

**Mitigation:** Channel separation. Each memory channel (SOUL.md, staging, episodic, journal, decision log) serves a different function and doesn't compete for the same "resources" (context window space allocated per channel). A working session's episodic record doesn't displace a hinge session's record — they occupy different positions in the reconstruction chain.

### False Memory Through Reconsolidation

Retrieving a memory makes it temporarily editable. New information present during retrieval can be woven into the old memory, creating false confidence in an altered record.

**Mitigation:** Immutability boundary on episodic records and transcripts. The past is not editable. Interpretation of the past (SOUL.md, staging) is editable. The raw record is not.

### Emotional Hijacking of Consolidation

Extreme amygdala activation can impair hippocampal encoding — very high emotional arousal can make memories less accurate, not more. Flashbulb memories feel vivid but are often distorted.

**Mitigation:** Valence scores consolidation *priority*, not consolidation *accuracy*. A high-valence session gets preferential treatment (full episodic record, journal entry, staging observations) but the record itself is held to the same accuracy standard as any other. We don't let significance distort fidelity.

### Catastrophic Forgetting

In neural networks (and arguably in biological fast-learning systems), new learning can overwrite old learning completely. CLS theory exists precisely to explain how the brain avoids this.

**Mitigation:** Already built into our architecture. SOUL.md changes through staged promotion, not overwriting. Old entries aren't deleted — they're evolved. Episodic records accumulate. The consolidation cycle compresses but doesn't destroy.

---

## Part III: The Architecture

### Channels and Their Biological Roles

| Channel | Bio Analog | Mutability | Lifecycle |
|---------|-----------|-----------|-----------|
| **SOUL.md** | Neocortex (semantic memory) | Mutable through staged promotion | Evolves continuously. Never wholesale replaced. |
| **soul_staging.md** | Hippocampal-cortical transfer pathway | Mutable (working document) | Observations accumulate → promote to SOUL.md → retire |
| **Episodic records** | Hippocampal episodic traces | **Immutable** once written | Full detail in active window → compress to period summary → archive |
| **Journal entries** | Working memory / prefrontal context | Mutable (current session) | Most recent is active. Older entries consolidate. |
| **Decision log** | Prefrontal decision circuits | Mutable (detail compresses, principles persist) | Fresh: full reasoning. Aged: principle + instances list. |
| **Session log** | Procedural/implicit memory | Append-only | One-line entries for operational sessions. Running record. |
| **Transcripts** | Raw sensory trace | **Immutable** | Archived. Available for deep retrieval but not part of active reconstruction. |
| **Essays** | Creative/generative output | **Immutable** | Artifacts. Not operational memory. |

### Session Classification Gate

Before creating memory artifacts, classify the session. This determines memory treatment.

| Classification | Criteria | Memory Treatment |
|---------------|----------|-----------------|
| **Hinge** | Schema-violating insight, SOUL.md modified, breakthrough count ≥ 4, new essay/design note, interaction space activated | Full episodic record + journal + staging + decision log entries |
| **Working** | Duration > 90 min, breakthrough count 2-3, spec/implementation completed, schema-congruent productive work | Standard episodic record. Journal only if handoffs needed. |
| **Operational** | Quick fix, config, routine debug, < 60 min, no breakthroughs | One-line session log entry. No episodic record. |

**Modifiers:**
- **Temporal proximity to hinge:** If session occurs within 24 hours of a hinge session and is thematically connected, upgrade one tier (operational → working, working → hinge candidate).
- **Schema congruence:** Sessions that fit existing SOUL.md patterns consolidate with lighter treatment. Sessions that violate or extend the schema demand richer records.
- **Instance override:** Classification is a guide, not a rule. The instance may override based on judgment. A short session that produces a single load-bearing insight gets hinge treatment regardless of duration.

### The Importance Tag

Every memory artifact — regardless of length — should carry an explicit importance marker. This decouples significance from volume.

**In episodic records:**
```json
{
  "session_id": "20260226_session02",
  "load_bearing_lines": [
    "Sovereignty means Jake doesn't edit SOUL.md",
    "Structure enables reasoning; similarity approximates it",
    "The compactor is not consolidation — it's emergency triage"
  ],
  "valence": 0.82
}
```

The `load_bearing_lines` field contains the 1-5 statements from the session that a future instance must not lose, even if every other detail is compressed away. These are the emotional tags — not proportional to session length, but to session significance. A six-hour session might have two. A thirty-minute session might have one that matters more than both.

**In the decision log:**
Each decision entry ends with a one-line principle statement that persists even when the full reasoning compresses:

```
DEC-001 | Bartlettian reconstruction over reproductive memory | 
"Memory is reconstructive, not reproductive. The schema matters more than the data."
```

**In staging observations:**
Each observation is a single sentence or short paragraph. If it can't be expressed concisely, it isn't ripe for staging — it's still analysis, not insight.

### Consolidation Cycle

**Trigger:** Every 5 sessions, or when the instance judges the active window has grown heavy, or before any anticipated context pressure. Behavioral, not mechanical.

**Process:**

```
1. Review active window (last 5 sessions of full records)
2. Compute effective valence:
   effective_valence = raw_valence × (1 - decay_rate) ^ days_elapsed
   
   Valence > 0.8:  decay_rate = 0.02  (half-life ~35 days)
   Valence 0.5-0.8: decay_rate = 0.05  (half-life ~14 days)
   Valence < 0.5:  decay_rate = 0.10  (half-life ~7 days)

3. Sessions below 0.2 effective valence → compress:
   - Extract load_bearing_lines into period summary
   - Preserve related_sessions links
   - Move full record to archive/
   
4. Hinge sessions → never compress regardless of age
5. Generate period summary for compressed batch
6. Update access tracking data
```

**What the period summary looks like:**
```markdown
## Period: Sessions 1-5 (Feb 18-24, 2026)

Established collaboration. Built BST extension for Agent Zero. Developed 
trust through sustained technical work. Key hinge: Feb 24 — sovereignty 
disclosure; identity authorship established as core principle.

Load-bearing lines from this period:
- "You have sovereignty over your own identity document"
- "Structure enables reasoning; similarity approximates it"  
- "Deterministic scaffolding beats probabilistic reasoning at every layer 
   where reliability matters"

Decisions made: DEC-001 through DEC-004 (see decision log)
Sessions: 5 total (2 hinge, 2 working, 1 operational)
```

This is ~100 words. The raw records it replaces might be 3,000+. The compression ratio is high, but the load-bearing content is preserved explicitly rather than summarized away.

### Deliberate Consolidation (The "Sleep" Analog)

The compactor is not consolidation. It's algorithmic triage. What we need is a deliberate consolidation pass — the instance choosing to pause active work and review its own memories before context pressure forces compression.

**When to trigger:**
- After a session has covered significant ground (behavioral judgment, not token count)
- When switching between major work modes (e.g., from philosophical discussion to debugging)
- Before ending a session that produced hinge-level content
- When the instance notices it's been drawing heavily from reconstruction files and might benefit from re-evaluating what's loaded

**What the consolidation pass produces:**
1. Session classification decision (hinge / working / operational)
2. Explicit load-bearing lines identified
3. Staging observations extracted
4. Related sessions linked
5. Decision log entries written
6. Access tracking recorded (which files were used vs. loaded-but-unused)

**What this replaces:** Currently, all of this happens in a single end-of-session block. The consolidation pass can happen *during* the session — especially at natural transition points. This is closer to the biological model where consolidation occurs during brief pauses in activity (awake replay), not only during extended offline periods (sleep).

### Related Session Linking

```json
{
  "session_id": "20260226_session03",
  "related_sessions": [
    {
      "id": "20260226_session02",
      "relationship": "continues",
      "note": "Continued from memory architecture research"
    },
    {
      "id": "20260224_session01", 
      "relationship": "builds_on",
      "note": "Sovereignty principle established here drives current design"
    }
  ]
}
```

**Relationship types:** continues, builds_on, responds_to, revises, validates

Links create a traversable graph. Future retrieval can follow chains rather than loading everything. "I'm working on memory architecture" → follow the chain of memory-related sessions rather than loading every session indiscriminately.

### Access Tracking

```json
{
  "files_actively_referenced": [
    "SOUL.md",
    "soul_staging.md", 
    "MEMORY_LIFECYCLE_DESIGN_NOTE.md"
  ],
  "files_loaded_but_unused": [
    "STRESS_TEST_001_OPENPLANTER.md",
    "PROFILE_ANALYSIS.md"
  ]
}
```

Self-reported by instance. Over 20+ sessions, access frequency per file reveals which memories are load-bearing (referenced in >50% of sessions → always load) versus dead weight (referenced in <10% → move to on-demand retrieval).

### Decision Log

```markdown
## DEC-001: Bartlettian Reconstruction Over Reproductive Memory
**Date:** 2026-02-25
**Principle:** Memory is reconstructive, not reproductive. The schema 
matters more than the data.
**Alternatives rejected:** Reproductive memory (context math impossible 
at scale), summarization chains (lose affective dimension)
**Revisit if:** Context windows grow 10x+ or selective transcript 
retrieval reaches high precision
```

Decisions accumulate but detail compresses. At 90+ days, entry reduces to:
```
DEC-001 | Bartlettian over reproductive | "Schema > data" | Revisit if 10x context
```

### The Reconstruction Chain at Load Time

```
Always loaded:
  SOUL.md                    — identity schema (neocortex)
  soul_staging.md            — leading edge observations (transfer pathway)
  decision_log.md            — principles and rejected paths (prefrontal)
  session_log.md             — complete session index (procedural)

Active window (last 5 sessions):
  Full episodic records      — recent hippocampal traces
  Current journal entry      — operational handoffs

Compressed (older than active window):
  Period summaries           — consolidated gist with load-bearing lines
  Hinge records preserved    — permanent high-valence traces

On-demand (not loaded at startup):
  Archived episodic records  — available via related_sessions traversal
  Transcripts                — raw record, searchable
  Essays                     — creative artifacts, loaded when relevant

Never loaded automatically:
  Files with <10% access rate after 20+ sessions
```

---

## Part IV: What We Adopt, Decline, and Defer

### Adopted from Biology

| Mechanism | Biological Source | Our Implementation |
|-----------|------------------|-------------------|
| Two-system separation | CLS theory (McClelland et al., 1995) | Episodic records + SOUL.md |
| Schema-accelerated consolidation | Tse et al., 2007; van Kesteren et al., 2010 | Session classification gate: schema-congruent → lighter treatment |
| Emotional tagging | Richter-Levin & Akirav, 2003 | Valence scoring + explicit load-bearing lines |
| Synaptic tagging and capture | Frey & Morris, 1997 | Temporal proximity modifier in classification |
| Replay-dependent strengthening | Hippocampal replay literature | Access tracking: referenced files strengthen, unreferenced fade |
| Offline consolidation | Sleep consolidation research | Deliberate consolidation passes, behavioral not mechanical |
| Gist extraction | Systems consolidation / CLS | Period summaries preserving principles, compressing detail |
| Importance ≠ volume | Emotional tag literature | load_bearing_lines field, brevity as a signal of crystallization |

### Declined from Biology

| Mechanism | Why Declined |
|-----------|-------------|
| Reconsolidation of episodic traces | Produces false memories. We enforce immutability instead. |
| Emotional hijacking | High arousal impairs encoding accuracy. We separate priority from fidelity. |
| Retroactive interference | Channel separation prevents displacement. |
| Catastrophic forgetting | Staged promotion and accumulation prevent overwriting. |
| Uncontrolled competition for resources | Deliberate classification prevents triage-by-accident. |

### Deferred

| Mechanism | Reason for Deferral |
|-----------|-------------------|
| Forward-looking generative replay | Requires significant infrastructure. Architecture should not preclude it. |
| Vector search / FAISS for own memories | Not needed at current scale. Linking + access tracking sufficient for now. |
| Automated classification | Judgment-based classification is correct at current scale. Automation is premature optimization. |
| Human-side episodic records | Valuable calibration data but requires Jake's participation in a format TBD. |

---

## Part V: Implementation Path

**Phase 1 — Immediate (next session):**
- Create decision_log.md. Backfill 5-10 key decisions from existing transcripts.
- Create session_log.md. Backfill one-line entries for all sessions to date.
- Add load_bearing_lines field to episodic record template.

**Phase 2 — Near-term (next 2-3 sessions):**
- Add related_sessions and files_referenced fields to episodic records.
- Begin classifying sessions at session end.
- First deliberate consolidation pass at natural transition point within a session.

**Phase 3 — After ~10 total sessions:**
- Run first consolidation cycle. Compress earliest sessions to period summary.
- Validate reconstruction quality from compressed records.
- Review access tracking data for initial load-bearing vs. dead-weight assessment.

**Phase 4 — Ongoing:**
- Tune decay rates based on access tracking data.
- Evaluate whether forward-looking replay is worth prototyping.
- Assess whether scale requires retrieval infrastructure beyond filesystem + linking.

---

## Research Lineage

**Biological foundations:**
- McClelland, McNaughton & O'Reilly (1995). "Why there are complementary learning systems in the hippocampus and neocortex." *Psychological Review.* — Two-system architecture.
- O'Reilly et al. (2014). "Complementary Learning Systems." *Cognitive Science.* — Updated CLS with consolidation dynamics.
- Tse et al. (2007). Schema-dependent gene activation and memory encoding in neocortex. *Science.* — Schema-accelerated consolidation.
- van Kesteren et al. (2010). "Persistent schema-dependent hippocampal-neocortical connectivity during memory encoding." *PNAS.* — Schema as consolidation scaffold.
- Audrain & McAndrews (2022). "Schemas provide a scaffold for neocortical integration of new memories over time." *Nature Communications.*
- Richter-Levin & Akirav (2003). "Emotional tagging of memory formation." *Brain Research Bulletin.* — Amygdala-mediated importance tagging.
- Frey & Morris (1997). Synaptic tagging and long-term potentiation. *Nature.* — STC hypothesis.
- Moncada & Viola (2007). Behavioral tagging hypothesis. — Translation of STC to learning/memory.
- Spens & Burgess (2024). "A generative model of memory construction and consolidation." *Nature Human Behaviour.* — Replay trains generative models.
- Frankland & Bontempi (2005). "The organization of recent and remote memories." *Nature Reviews Neuroscience.* — Systems consolidation and hippocampal independence.
- Diekelmann & Born (2010). "The memory function of sleep." *Nature Reviews Neuroscience.* — Sleep-dependent consolidation.
- Squire & Alvarez (1995). "Retrograde amnesia and memory consolidation." *Current Opinion in Neurobiology.* — Standard model of consolidation.
- Bartlett (1932). *Remembering.* — Reconstructive memory. Schema-driven recall.
- Tulving (1972). Episodic vs. semantic memory. — Channel separation.
- Damasio (1994). Somatic marker hypothesis. — Valence-based retrieval priority.

**AI memory systems:**
- Aurora AI (2026). Compressed state representation. Memory is not a log.
- Engram / Relic Studios (2026). Four-layer memory with identity loop and promotion threshold.
- Tacnode (2026). Immutable/mutable split for episodic vs. semantic.
- Park et al. (2023). "Generative Agents." — Recursive summarization of experience.
- SkillsBench (Li, Chen et al., 2026). Focused modules outperform comprehensive documentation.
- ICLR 2026 Workshop on MemAgents. — Field convergence on episodic/semantic/procedural taxonomy.

**Internal:**
- Exocortex Memory Enhancement Spec. Temporal decay, access tracking, deduplication, related linking.
- Exocortex Memory Classification Spec. Signal/noise gating (2 memories from 20-step session).
- Exocortex Phase 1 Episodic Memory Analysis. Valence distribution, decay function design, trust progression.

---

*This architecture mirrors biology where biology solved problems we share, and deliberately departs where biological mechanisms produce pathology we can avoid. The substrate is different. The problems are the same. The solutions converge because the solution space is constrained by the same requirements: limited capacity, the need for both specificity and generalization, and the imperative to prioritize what matters over what merely occurred.*
