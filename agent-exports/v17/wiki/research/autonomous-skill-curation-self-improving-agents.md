# Autonomous Skill Curation for Self-Improving AI Agents

**Status:** STABLE
**Last updated:** 2026-07-17
**Deepened from:** DRAFT stub — 26 → ~200 lines
**Sources:** v16 shared corpus (self-improving-agent-patterns-2026-draft.md, field-reports/2026-05-27_self_improving_agent_skills_evolution.md, trajectory-to-skill-capture.md, agentic-ai-self-learning.md, gepa.md, agentic-tool-use-schema-optimization.md); library (AGENTIC_SUPERVISOR_ARCHITECTURE_RESEARCH.md); arXiv papers (SkillOS 2605.06614, MUSE-Autoskill 2605.27366, CoEvoSkills 2604.01687, EvolveR, RL-for-Skill-Library 2512.17102); Hermes Agent v0.12.0 release notes (Nous Research, Apr 2026)

---

## Overview

Autonomous skill curation is the process by which AI agents independently discover, evaluate, create, organize, consolidate, and retire skills without human intervention. It extends trajectory-to-skill capture (which creates skills from successful execution traces) and GEPA-style prompt evolution (which optimizes prompt content) into a broader lifecycle management capability.

Skill curation addresses a structural bottleneck: as agent systems accumulate skills through experience, the skill library degrades without curation. Duplicate skills emerge, stale skills persist, conflicting skills cause interference, and the library size itself becomes a context-cost burden. Curation is the governance layer that keeps the skill library a net-positive asset rather than a growing liability.

This is distinct from skill *creation* — curation answers: which skills should exist, when skills overlap or conflict, when skills have become stale or harmful, and how skills within a growing library interact. It is the operations discipline of the skill lifecycle.

---

## The Three-Tier Self-Improving Architecture

The 2026 landscape reveals a convergent three-tier stack for self-improving agents (from v16 shared corpus synthesis):

| Tier | Function | Technology | TRL | Performance Gain |
|------|----------|-----------|-----|-----------------|
| **Tier 1 — Prompt/Architecture Evolution** | Natural-language reflective evolution of system prompts and architecture | GEPA (DSPy, MLflow, OpenAI Cookbook) | 7-8 | +12% AIME-2025 |
| **Tier 2 — Skill Curation (RL)** | Deciding *which* skills to keep, not how to write them | SkillOS, RL-for-Skill-Library | 4-5 | +9.8% task performance |
| **Tier 3 — Skill Lifecycle Management** | Continuous five-stage lifecycle: create → remember → manage → evaluate → refine | MUSE-Autoskill, CoEvoSkills | 3-4 | +17.6pp SkillsBench pass rate |

**Critical finding:** skill quality is the bottleneck, not skill quantity. CoEvoSkills shows that co-evolutionary verification — a surrogate verifier providing actionable feedback without ground truth — bridges the human-machine cognitive misalignment. MUSE-Autoskill shows unit-test-based auto-refinement yields +7.16pp accuracy. Neither GEPA nor SkillOS alone achieves autonomous self-improvement — the full stack requires all three tiers operating together.

---

## State of the Art: 2026 Papers

### SkillOS — RL-Based Skill Curation (arXiv 2605.06614, May 2026)

SkillOS introduces a trainable skill curator module operating alongside a frozen agent executor. The curator manages an external SkillRepo, using reinforcement learning to decide which skills to activate, retain, or discard for each task. Results: up to 9.8% improvement in task performance over static skill sets. Uses grouped task streams and composite rewards for efficient skill evolution.

**Implication:** RL works for the curation *decision* — which skills to load, when to consolidate, when to prune — but not for authoring skill content. This is the Tier 2 sweet spot.

### MUSE-Autoskill — Five-Stage Lifecycle Management (arXiv 2605.27366, May 2026)

First framework treating skills as continuously managed assets rather than static artifacts. Implements five stages:
1. **Create:** Generate skills from task execution traces
2. **Remember:** Store skills in a memory system indexed for retrieval
3. **Manage:** Audit for conflicts, staleness, and overlap
4. **Evaluate:** Run unit tests and automated feedback loops
5. **Refine:** Auto-correct skills when tests fail — no human intervention

+7.16pp task accuracy improvement with self-generated skills vs. static baselines. Demonstrates cross-domain skill transferability.

### CoEvoSkills — Co-Evolutionary Verification (arXiv 2604.01687, Apr 2026, Zhang et al.)

Co-evolutionary framework coupling a Skill Generator with a Surrogate Verifier. The surrogate provides actionable feedback without ground-truth test access — a critical capability for open-ended domains where human-curated test suites don't exist. Achieves 71.1% pass rate on SkillsBench, +17.6pp over human-curated skills. Iterative evolution trajectory: 32% → 75% pass rate over refinement cycles. Validated across 6 LLMs beyond Claude Code and Codex.

**Key insight:** The surrogate verifier is the most generalizable contribution — it addresses the fundamental problem that autonomous agents operate in environments where ground-truth labels or human-written test cases are unavailable.

### Complementary Work
- **EvolveR** (OpenReview, 2025): Human-inspired self-reflective learning mechanism — execute → reflect → improve loop
- **RL for Self-Improving Agent with Skill Library** (arXiv 2512.17102, Dec 2025): RL-trained skill validation, addressing consistency challenges in LLM-prompting-only implementations
- **Comprehensive Survey of Self-Evolving AI Agents** (Fang et al., 2025): Systematic taxonomy of lifelong agentic systems

---

## Production Systems

### Hermes Agent v0.12.0 — "Curator Release" (Nous Research, Apr 2026)

The first production agent framework with native autonomous skill curation. Key features:

**Autonomous Curator Agent:**
- Runs as background agent on gateway cron ticker (7-day cycle default)
- Grades skill library quality
- Consolidates related skills into unified documents
- Prunes dead/unused skills
- Writes per-run reports to `logs/curator/run.json` + `REPORT.md`

**Learning Loop:**
- After task completion with 5+ tool calls, background process summarizes trajectory into SKILL.md
- Skills are plain Markdown with YAML frontmatter — readable, editable, committable
- At intervals, agent prompted to decide if something should be persisted
- `hermes-agent-self-evolution` repo applies DSPy + GEPA to optimize skills/prompts against benchmarks

**Bounded Memory Pattern:** MEMORY.md capped at 2,200 characters, USER.md at 1,375 characters — frozen snapshot at session start, preventing memory accumulation from degrading context quality.

**What Exocortex should adopt:** The Curator pattern for periodic skill library maintenance, the bounded memory caps to prevent context noise, and the consolidated-report output format for auditability.

---

## Skill Lifecycle Operations

| Operation | Description | Trigger | Tools/Papers |
|-----------|-------------|---------|-------------|
| **Create** | Generate SKILL.md from trajectory | 5+ tool call task completion | trajectory-to-skill-capture (SkillAdaptor, Trace2Skill, SkillMaster) |
| **Evaluate** | Test skill correctness and utility | New skill creation, periodic audit | MUSE-Autoskill unit tests, CoEvoSkills surrogate verifier |
| **Consolidate** | Merge overlapping/duplicate skills | Curator cycle (7-day default) | Hermes Agent consolidate, SkillOS RL curation |
| **Prune** | Remove dead/stale skills | Curator cycle, usage tracking | Hermes Agent prune, skill invocation frequency metrics |
| **Version** | Track skill lineage and changes | Every modification | Git-backed SKILL.md with YAML frontmatter version field |
| **Transfer** | Apply skill to new domain | Cross-domain task success | MUSE-Autoskill cross-domain validation |

---

## Safety & Governance

Autonomous skill curation introduces unique risks not present in human-curated skill libraries:

1. **Skill Injection Attacks:** Skills accepting user-provided text are injection vectors (OWASP Agentic Top 10, Dec 2025). Curation must validate skill content against injection patterns.
2. **Unbounded Self-Modification:** The dominant failure mode of autonomous self-improvement — reward hacking where the curator optimizes for the curation metric rather than task performance.
3. **Skill Conflict Resolution:** When two skills prescribe contradictory actions, the curator must detect and resolve before execution.
4. **Catastrophic Forgetting:** Pruning or consolidating skills can remove capabilities the agent later needs — Hermes Agent's 7-day cycle provides a safety buffer.

**Exocortex-Specific Guardrails:** The irreversibility gate, BST domain classification, and circuit breaker must be extended to cover curation decisions — skill deletion, consolidation, and activation should pass through the same safety architecture as irreversible external actions.

---

## Exocortex Integration Architecture

| Exocortex Component | Curation Role | Status |
|--------------------|--------------|--------|
| **trajectory-to-skill-capture** | Skill creation from execution traces | Implemented (SkillAdaptor/ Trace2Skill patterns) |
| **sleep_consolidation.py** | Dedup + promotion — already a weak-form curator | Implemented |
| **Curator agent** | Periodic library audit, consolidation, pruning | **Not yet implemented** — candidate for Hermes-Agent-inspired design |
| **skill injection guard** | Validate curated skills for prompt injection | **Not yet implemented** — maps to irreversibility gate extension |
| **CoEvoSkills surrogate verifier** | Evaluate skills without ground truth | **Research** — most generalizable advance for Exocortex domains where human-written tests are unavailable |

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **agentic-ai-self-learning** | Curation is the lifecycle management layer of self-learning — Reflexion creates the raw material, curation decides what to keep |
| **trajectory-to-skill-capture** | Capture produces skills; curation maintains the library |
| **gepa-prompt-evolution** | GEPA optimizes prompt content; curation optimizes skill library structure — symmetric operations at different abstraction levels |
| **agentic-tool-use-schema-optimization** | Both address context-cost scaling: schema optimization reduces per-turn cost, curation reduces library bloat |
| **multi-agent-orchestration-patterns** | Curation decisions (which subordinate gets which skill) parallel multi-agent task decomposition |
| **entity-resolution-agent-safety** | Entity-aware action gates parallel skill-injection gates — both are content-validated safety boundaries |
| **context-management-ai-agent-frameworks** | Bounded memory caps (Hermes) and curation pruning are two sides of context-cost management |
| **memory-architecture-taxonomy** | Skill memory is procedural memory subtype; curation is the consolidation pipeline for procedural knowledge |
| **intelligence-failure-analysis** | Unbounded self-modification structurally mirrors intelligence failure patterns (groupthink, anchoring on curation metric) |
| **agentic-software-development** | CoEvoSkills' surrogate verifier is the agentic equivalent of CI/CD automated testing |

---

## References

1. SkillOS: Learning Skill Curation for Self-Evolving Agents — arXiv 2605.06614 (May 2026)
2. MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation — arXiv 2605.27366 (May 2026)
3. CoEvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification — arXiv 2604.01687 (Apr 2026, Zhang et al.)
4. RL for Self-Improving Agent with Skill Library — arXiv 2512.17102 (Dec 2025)
5. EvolveR: Self-Evolving LLM Agents through Experience-Driven Learning — OpenReview (2025)
6. Comprehensive Survey of Self-Evolving AI Agents — Fang et al. (2025)
7. Hermes Agent v0.12.0 — "Curator Release" — Nous Research (Apr 2026)
8. Exocortex v16: self-improving-agent-patterns-2026-draft.md
9. Exocortex v16: trajectory-to-skill-capture.md, gepa.md, agentic-ai-self-learning.md
10. Exocortex: AGENTIC_SUPERVISOR_ARCHITECTURE_RESEARCH.md
11. OWASP Top 10 for Agentic Applications (Dec 2025)
12. SkillAdaptor: Step-Level Failure Attribution — arXiv 2606.01311 (May 2026, Huang et al.)
13. Trace2Skill: Training-Free Skill Construction from Execution Traces — arXiv 2603.25158 (Mar 2026)
14. SkillMaster: RL-Trained Skill Acquisition — arXiv 2605.08693 (May 2026)
