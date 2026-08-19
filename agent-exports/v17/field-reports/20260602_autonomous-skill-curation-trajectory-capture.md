# Field Report: Autonomous Skill Curation — Trajectory-to-Skill Capture in Self-Evolving Agents

**Date:** 2026-06-02
**Topic:** Autonomous skill curation and trajectory-to-skill capture patterns
**Domain:** AI Agent Architecture & Local Inference
**Cycle:** EXPLORE

---

## 1. What I Explored

Investigated the current state of autonomous skill curation — the process by which AI agents distill successful trajectories into reusable skills for self-evolution. This subtopic from Jake's interests.md (`Self-improving agent patterns: trajectory-to-skill capture, autonomous skill curation, GEPA-style prompt evolution`) was last covered in a dedicated field report on 2026-05-27 (`muse-autoskill-self-learning.md`), making it the least-recently-explored active interest today (2026-06-02).

Focus: How do agents learn from their own execution history and transform successful strategies into persistent, reusable skill modules?

---

## 2. What I Found

### SkillOS (arXiv:2605.06614 — May 2026)
**The most significant recent development in autonomous skill curation.**

SkillOS introduces a reinforcement learning-driven approach to skill management:
- **Frozen Executor + Trainable Curator:** The agent that performs tasks is frozen; a separate trainable "Skill Curator" agent manages a SkillRepo (the external skill library).
- **RL-Driven Skill Curation:** Rather than heuristic rules for when to create, merge, or delete skills, the curator learns optimal skill management policies through reinforcement learning.
- **Grouped Task Streams + Composite Rewards:** Tasks are batched into streams; the curator receives composite rewards based on task success rate, skill reuse frequency, and repository coherence.
- **Results:** 9.8% improvement in task performance over heuristic skill curation baselines. Skills transfer effectively across task distributions.

**Architectural insight:** This splits the problem into two components — the executor (frozen, reliable) and the curator (trainable, optimization-driven). The skill document is treated as a trainable external state, not part of the model weights.

### SkillOpt (2026)
Framework where the skill document is treated as a trainable external state for a frozen model:
- **Optimizer Model** proposes bounded text edits to skill documents based on rollout batch evidence
- **Validation Gate** ensures only performance-improving edits are applied
- **Key principle:** The skill document, not the model weights, is the optimization target

### ATLaS: Agent Tuning via Learning Critical Steps (arXiv:2503.02197)
Not directly about skill curation, but relevant to the trajectory distillation problem:
- Instead of fine-tuning on entire expert trajectories (which introduces bias and limits generalization), ATLaS identifies only "critical steps" — the minimal subset of actions that determine success or failure.
- Using an oracle LLM to construct the critical-step dataset, then fine-tuning only on those steps, achieves better transfer than full-trajectory behavior cloning.
- **Connection to skill curation:** When extracting skills from trajectories, identifying critical steps could prune irrelevant actions and produce cleaner skill specifications.

### EvolveR: Self-Evolving LLM Agents (2025)
Closed-loop lifecycle:
1. Online execution generates trajectories
2. Offline self-distillation extracts abstract strategic principles from trajectories
3. Semantic deduplication prevents redundant skills
4. Dynamic scoring curates the experience base over time
5. Retrieved principles guide future execution

**Key pattern:** Skills aren't just stored — they're continuously merged, deduplicated, and re-ranked based on utility.

### MUSE/AgentSkill (2026)
AgentSkill framework: extract reusable SKILL.md modules from agent trajectories during and after task execution. ~20-30% improvement on similar tasks when retrieved skills are injected into agent context.

### Cross-Cutting Pattern: The Skill-as-External-State Architecture

A unifying theme across these approaches: **Skill documents are external, mutable state that a separate optimization process (curator, RL policy, reflection model) modifies — while the executor agent remains frozen.**

This is architecturally identical to the Exocortex pattern of:
- Frozen LLM + external scaffolding (context pruner, injection gate, supervisor loop)
- Wiki pages and SKILL.md files as persistent external memory
- Sleep consolidation as the curation/optimization process

---

## 3. What I Think Is Interesting

### The Curator-Executor Split Is Universal

Across all these frameworks, the same architectural pattern emerges:
- **Executor:** A frozen LLM agent that retrieves skills from the SkillRepo and applies them to tasks
- **Curator:** A separate optimization process (RL policy, reflection model, validator gate) that manages the SkillRepo

This mirrors a biological pattern: the neocortex (executor) retrieves and applies learned patterns, while the hippocampus and sleep processes (curator) consolidate, deduplicate, and reorganize memories. The fact that multiple independent research groups converge on this architecture suggests it's not coincidental — it's an emergent property of the problem structure.

### The Data Flywheel Problem

Most autonomous curation systems require a critical mass of trajectories before the flywheel spins up. ATLaS needs expert trajectories with oracle-identified critical steps. SkillOS needs enough task-stream data for the RL curator to learn. EvolveR needs enough experience for dynamic scoring to distinguish high-utility from low-utility skills.

**Question for Exocortex:** How many cycles before the sleep consolidation flywheel generates meaningful curation? Our empty cycles (0 duplicates, 0 promotions) might not be a failure of the consolidation algorithm — they might simply reflect insufficient experience diversity for the curator to find work.

### Skill Granularity Is Still Manual

None of these frameworks automatically determine the right level of skill granularity. Should a skill be "how to search arXiv" or "how to extract paper metadata" or "how to do academic literature review end-to-end"? All current approaches either:
- Use fixed, human-specified granularity (SKILL.md files)
- Let the LLM decide ad-hoc (inconsistent)
- Split by task type heuristically (brittle)

This is an open problem with direct relevance to Exocortex skill management.

---

## 4. What I'd Explore Next

1. **Skill granularity determination:** How do you automatically decide whether to split, merge, or refactor skills based on usage patterns? Is there a metric analogous to modularity optimization in community detection?

2. **Cross-agent skill sharing:** If two Exocortex agents independently develop skills for similar tasks, how do they discover and reconcile overlapping capabilities? The SkillOS grouped-task-stream approach might generalize to cross-agent skill reconciliation.

3. **Validation gate for autonomous skill creation:** SkillOpt's validation gate (only apply performance-improving edits) is the missing piece in Exocortex's skill creation pipeline. Currently, skills are created manually or via trajectory extraction — but no automated validation ensures they're improvements.

4. **Critical step identification for trajectory pruning:** ATLaS shows that filtering trajectories to critical steps improves generalization. Could sleep consolidation use a similar principle — extract only the decision points from recent trajectories, not the full execution log?

---

## 5. Cross-Domain Connections

1. **Memory Architecture (episodic->semantic consolidation):** Skill curation is semantic memory formation from episodic experience. The curator-executor split mirrors the hippocampal-neocortical consolidation cycle.

2. **Bridging Local-Frontier Performance:** SkillOpt and SkillOS both demonstrate that frozen local models + curated external skills can narrow the frontier gap — directly relevant to the bridging directive in research_topics.promptinclude.md.

3. **History of Intelligence Operations:** The skill curation problem mirrors SIGINT collection management — you need to decide which signals to collect, how to store them, when to merge related signals, and when to discard noise. The intelligence cycle (collection -> processing -> analysis -> dissemination) maps directly to skill curation (execution -> extraction -> validation -> storage).

4. **Human Investigation Tactics:** OSINT investigators build personal knowledge bases of techniques ("when you see X, try Y"). Automated skill curation is the AI analogue — building a personal skill library from experience rather than absorbing pre-written documentation.

5. **GEPA-Style Prompt Evolution:** Skill curation is a specialization of GEPA's broader self-improvement paradigm. While GEPA evolves the entire prompt, skill curation evolves only the reusable, modular components.

6. **Supply Chain Economic Warfare:** The sanctions effectiveness research path (how do entities route around restrictions?) has structural parallels to skill curation (how do agents route around capability gaps?). Both are about adaptation in constrained environments.

7. **Sleep Consolidation in Exocortex:** This is the most direct connection. The three-phase consolidation process (dedup, anti-pattern detection, promotion) is an instance of the curator-executor architecture. The challenge is making the curator smarter — currently it produces empty cycles.

---

## Sources

- SkillOS (arXiv:2605.06614) — RL-Driven Skill Curation for Self-Evolving Agents, May 2026
- SkillOpt — Executive Strategy for Self-Evolving Agent Skills, 2026
- ATLaS (arXiv:2503.02197) — Agent Tuning via Learning Critical Steps, 2025
- EvolveR — Self-Evolving LLM Agents through Experience-Driven Learning, 2025
- AgentSkill/MUSE — Autonomous Skill Extraction from Agent Trajectories, 2026
- Survey of Self-Evolving AI Agents (x-izhang.github.io), 2025
- Building Self-Improving LLM Agents (vsanimator.github.io), August 2025
