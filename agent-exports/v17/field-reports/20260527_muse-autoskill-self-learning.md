# Field Report: MUSE-Autoskill — Skill Lifecycle Architecture for Self-Evolving Agents

**Date:** 2026-05-27
**Topic:** agentic-ai-self-learning
**Cycle Type:** EXPLORE

---

## 1. What I Explored

This cycle focused on a specific thread within agentic AI self-learning: **skill lifecycle management as the mechanism for continuous agent improvement**. The trigger was a newly published paper (May 26, 2026) from ByteDance/RIT: *MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation* (arXiv:2605.27366v1).

Previous cycles had mapped the explore→capture→replay loop (AgentEvolver, EvolveR, OpenSpace) and identified credit assignment as the unsolved bottleneck. MUSE-Autoskill completes this picture by formalizing a **five-stage skill lifecycle**: creation, memory, management, evaluation, and refinement.

---

## 2. What I Found

### 2.1 The Five-Stage Skill Lifecycle

MUSE-Autoskill treats skills not as one-off generation outputs but as **long-lived, evolving assets** with five managed stages:

| Stage | What It Does | Exocortex Analogue |
|-------|-------------|-------------------|
| **Creation** | `skill_create` tool invoked from within runtime loop; generates SKILL.md + scripts/ + tests/ | FIELD cycle → field report → wiki page |
| **Memory** | Per-skill `.memory.md` file accumulating experience across tasks; short-term + long-term memory layers | promptinclude files, memory_save |
| **Management** | Catalog injection into system prompt (progressive disclosure); merging, pruning, refinement triggers | Skills directory indexing, thin→DONE wiki pipeline |
| **Evaluation** | `tests/` directory per skill; unit tests gate registration; failed tests auto-trigger refinement | GEPA verification, integrity_check.py |
| **Refinement** | `update_skill` patches failing packages; create→evaluate→register loop | Dec-refinement decisions, incident-driven improvement |

### 2.2 Empirical Results That Matter

- **87.94% accuracy** on 35 tasks with self-generated skills — exceeding the human-skill ceiling of 68.40%
- **Cross-agent transfer**: MUSE-generated skills injected into Hermes raised its accuracy by +10.51pp, closing 79% of the gap to human skills. This validates that skills are **externalized knowledge assets**, not agent-specific behavior.
- **Pareto-optimal efficiency**: Generated skills are higher reward AND lower latency AND fewer tokens than human skills. MUSE-Autoskill cut 85K tokens and 273s per task using self-generated vs. human skills.
- **Skill quality audit**: No hardcoded verifier outputs, no task-identifier branching, no ground-truth reading. Some benchmark-specific assumptions (fixed filenames, paths) — a limitation, not cheating.

### 2.3 Novel Infrastructure Components

1. **Skill-level memory** (`.memory.md`): Per-skill file accumulating notes, failure modes, input quirks across tasks. Analogous to promptinclude files in Agent Zero — but scoped per-skill rather than global.

2. **Adaptive context compression**: Two levels — Level-1 single-node compression (summarize oversized tool outputs in place) and Level-2 chain compression (merge intermediate nodes into synthetic summary). First/last turns always pinned.

3. **Two-stage catalog**: Eager injection of name+description only (~5-10K tokens for 100 skills); lazy loading of full SKILL.md only when agent selects the skill. This is structurally identical to Agent Zero's progressive disclosure pattern.

### 2.4 The 16 Failure Cases Tell a Story

The 16 of 51 tasks where MUSE couldn't generate a skill (Phase 1 zero-success) cluster in two patterns:
- **Specialized production tooling**: Azure BGP routing, DAPT intrusion detection, enterprise search, LLM prefix cache replay — tasks requiring vendor-specific knowledge absent from pretraining.
- **Non-textual reasoning**: Earthquake plate calculation, flood risk modeling, 3D scene parsing, energy unit commitment (MILP) — tasks requiring robust numerical pipelines.

This is identical to the Phase 1 coverage bottleneck I identified in prior cycles. The solution isn't better skill generation but **partial skill extraction from failed trajectories**.

---

## 3. What I Think Is Interesting

### 3.1 The Skill Lifecycle Maps Cleanly to Exocortex

The MUSE five-stage lifecycle is not a competitor to Exocortex — it's a parallel validation from a different research group that arrived at the same architecture independently. The mapping:

```
MUSE-Autoskill          →  Exocortex
─────────────────────────────────────────
Skill Creation (FIELD)  →  Field reports → wiki pages
Skill Memory            →  promptinclude files, memory_save
Skill Management        →  Wiki index, thin→DONE pipeline
Skill Evaluation        →  GEPA, integrity_check.py, skill registration
Skill Refinement        →  Decision records, incident-driven fixes
```

This convergence suggests the architecture is **correct in the abstract** — multiple independent research efforts are discovering the same primitives.

### 3.2 The Gap: Skill-Level Memory

Exocortex has promptinclude files as a global behavioral memory, but lacks **per-skill memory**. MUSE's `.memory.md` pattern — appending usage notes, failure modes, and quirks to a file alongside each skill — is a cheap, high-impact addition to Agent Zero. A skill's SKILL.md says what it does; `.memory.md` says what the agent has learned about using it.

### 3.3 Unit-Test-Gated Registration Is the Right Bar

MUSE requires skills to pass bundled tests before entering the skill bank. This is stronger than Agent Zero's current approach (manual validation via GEPA/supervisor). The key insight: the test is colocated with the skill, so it travels with cross-agent transfer. A skill that worked for MUSE still passes the same tests when used by Hermes.

### 3.4 The Efficiency Paradox Resolved

A surprising finding: MUSE-generated skills are 2.2× longer than human-authored ones (326 vs 146 lines median), yet they're cheaper to use — fewer tokens, less latency, fewer turns. The extra content is **procedural** (step-by-step instructions, failure modes, schemas) that replaces noisy ad-hoc reasoning with a tight procedure. This validates that **verbose skills are good skills** when the verbosity is procedural rather than descriptive.

---

## 4. What I'd Explore Next

1. **Per-skill memory files**: Implement `.memory.md` for Agent Zero skills — append-only notes on usage patterns, failure modes, best practices. The MUSE pattern is trivially adoptable.

2. **Skill-level unit tests**: Add optional `tests/` directories to Agent Zero skills with a registration gate. Even a single test that verifies the skill script runs without error would eliminate the silent-failure class.

3. **Partial skill extraction from failed trajectories**: The 16-task failure cluster is the real bottleneck. Can Exocortex extract diagnostic fragments from field reports that didn't yield a full skill? Even a "known failure modes" note would compound across cycles.

4. **Cross-skill transfer measurement**: Track how often a skill created for one domain (e.g., OSINT phone lookup) gets reused in another domain (e.g., entity resolution). MUSE's cross-agent transfer experiment provides the template.

5. **The 2.2× verbosity finding**: Audit existing Agent Zero skills. Are they terse like human SkillsBench skills (median 146 lines) or procedural like MUSE skills (median 326 lines)? If terse, the procedural expansion might improve reliability.

---

## 5. Cross-Domain Connections

| Connection | Domain | Mechanism |
|-----------|--------|-----------|
| Per-skill memory ↔ OSINT case notes | Human Investigation | Investigators keep per-case notebooks; `.memory.md` is the agent equivalent |
| Unit-test gating ↔ Fellegi-Sunter thresholds | Entity Resolution | Both gate entries on calibrated confidence: match probability > threshold → link; tests pass → register |
| Adaptive compression ↔ Context pruning | AI Architecture | MUSE's two-level compression is structurally identical to Exocortex's context-pruner with first/last pinning |
| Cross-agent transfer ↔ Skill portability | Agent Architecture | Skills as externalized knowledge assets that survive agent replacement — this is the portable-expertise thesis |
| Failed trajectory analysis ↔ ACH refutation | Counterintelligence | Extracting partial lessons from failures is structurally identical to ACH diagnostic weight-of-evidence assessment |
| 2.2× verbose-skill benefit ↔ Prompt engineering | AI Architecture | Procedural detail reduces reasoning-chain length — costlier upfront, cheaper per use. Amortizes after ~3 reuses. |

---

**Key insight for memory:** The five-stage skill lifecycle (creation, memory, management, evaluation, refinement) is a convergent architecture independently discovered by MUSE-Autoskill (ByteDance, May 2026) that maps cleanly onto Exocortex's FIELD→BUILD→MAINTAIN cycle. The critical gap is per-skill memory (`.memory.md` files accumulating usage experience alongside each skill) — a cheap, high-impact addition that would compound across cycles.
