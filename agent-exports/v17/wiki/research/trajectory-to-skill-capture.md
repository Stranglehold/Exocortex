# Trajectory-to-Skill Capture for Autonomous Agents

**Status:** STABLE
**Last updated:** 2026-06-08
**Deepened:** 2026-06-08 — synthesized state-of-the-art survey (SkillAdaptor, Trace2Skill, SkillMaster) with Exocortex TRAJECTORY_TO_SKILL_SPEC implementation design.
**Sources:** arXiv 2606.01311 (SkillAdaptor), arXiv 2603.25158 (Trace2Skill), arXiv 2605.08693 (SkillMaster), Exocortex TRAJECTORY_TO_SKILL_SPEC.md, field-report/20260526_mcp-tool-schema-optimization.md, search engine (Qwen Trace2Skill GitHub, SkillFlow benchmark)

## Overview

Trajectory-to-skill capture is the process of converting an autonomous agent's execution trace — the sequence of tool calls, observations, and decisions during a task — into a reusable, transferable skill. This closes the self-improvement loop: agents move from being skill *consumers* to skill *producers*, growing their own capability libraries through experience. The 2026 state of the art has advanced rapidly across three axes: **capture granularity** (session-level → step-level), **consolidation depth** (single-trajectory overfitting → multi-trajectory inductive reasoning), and **autonomy spectrum** (human-authored → training-free adaptation → RL-trained skill mastery).

## State of the Art: Three Papers

### 1. SkillAdaptor (arXiv 2606.01311 — May 2026) — Step-Level Failure Attribution

Huang et al. identify a fundamental scaling bottleneck: hand-authored skills don't scale, and training-free skill adaptation from full trajectories produces overly broad, unstable revisions because failure attribution is too coarse.

**Core contribution:** Step-level attribution. When a trajectory fails, SkillAdaptor identifies the *first actionable fault step*, links responsibility to candidate skills, and applies targeted updates under explicit acceptance checks — all while keeping the backbone LLM frozen.

**Results:** Evaluated on WebShop, PinchBench, Claw-Eval with Kimi-K2.5, GLM-5, GPT-5.2. Improves over baselines: +1.7 WebShop success rate, +1.5 PinchBench Avg Score%, +1.8 Claw-Eval Avg Score.

**Key design principles:**
- **Localize before patching:** Don't rewrite the whole skill — fix the specific step that failed
- **Acceptance checks:** Each skill edit is validated before being committed
- **Frozen backbone:** No model fine-tuning required; skills are external artifacts

**Implication for Exocortex:** The TRAJECTORY_TO_SKILL_SPEC currently captures at the *task* level (5+ tool calls, successful completion). SkillAdaptor suggests step-level instrumentation would produce more surgical skill edits — capturing not just "this task succeeded" but "step 3 succeeded because of X, step 5 needed Y correction."

### 2. Trace2Skill (arXiv 2603.25158 — March 2026) — Multi-Trajectory Inductive Reasoning

Ni et al. (Qwen Applications Team, Alibaba) tackle the overfitting problem: skills generated from a single trajectory learn trajectory-local quirks, not generalizable patterns.

**Core contribution:** Parallel trajectory consolidation. Instead of updating skills sequentially from individual traces, Trace2Skill analyzes a *pool* of trajectories simultaneously, uses multiple analyst agents to propose trajectory-local patches, then synthesizes them into a unified skill directory through inductive reasoning.

**Results:** Cross-model transfer demonstrated — skills evolved from Qwen3.5-35B trajectories improved a Qwen3.5-122B agent by up to **+57.65 percentage points** on WikiTableQuestions. Skills transfer across model scales, model families, and to out-of-distribution settings.

**Key design principles:**
- **Analysis-in-parallel:** Multiple trajectories are analyzed simultaneously, not sequentially
- **Inductive synthesis:** Patch proposals are merged through reasoning, not voting
- **Portability by design:** Skills are not memorized artifacts of training trajectories — they capture abstract procedural knowledge

**Implication for Exocortex:** The current spec captures one trajectory at a time. Trace2Skill suggests a higher-leverage optimization: batch-consolidate across multiple similar trajectories before generating a skill. This would produce more robust, transferable skills.

### 3. SkillMaster (arXiv 2605.08693 — May 2026) — RL-Trained Autonomous Skill Mastery

Yang et al. push autonomy furthest: instead of external teachers or hand-designed rules, agents are trained via RL to *decide for themselves* when to create, refine, or retain skills during task solving.

**Core contribution:** DualAdv-GRPO — a dual-advantage reinforcement learning algorithm that jointly optimizes task-solving actions AND skill-editing decisions. Three key designs:
1. **Trajectory-informed skill review:** Agents learn to propose, update, or retain skills based on evidence from completed episodes
2. **Counterfactual utility evaluation:** Each candidate skill edit is evaluated by its counterfactual impact on related probe tasks — providing a direct learning signal
3. **DualAdv-GRPO:** Separate advantage estimation for task actions and skill edits prevents interference between the two objectives

**Results:** +8.8% ALFWorld, +9.3% WebShop over state-of-the-art baselines. Agents trained with SkillMaster can identify skill failures, refine procedural knowledge from trajectory evidence, and transfer improvements to future tasks with limited skill-bank edits.

**Implication for Exocortex:** SkillMaster requires RL training — not directly applicable to a frozen-LLM architecture without fine-tuning. But the *counterfactual utility evaluation* concept is transferable: before committing a newly generated skill, run it on a held-out probe task and compare performance against the baseline.

## The Exocortex TRAJECTORY_TO_SKILL_SPEC

The Exocortex specification (TRAJECTORY_TO_SKILL_SPEC.md, 315 lines, April 2026) defines a capture pipeline:

### Capture Conditions (all must be true)
1. Task completed successfully (response tool called with substantive output)
2. 5+ tool calls (complex enough for a reusable pattern)
3. BST domain classification confidence ≥ 2 signals
4. No supervisor Tier 2+ intervention (approach was clean)
5. Not a simple conversation, greeting, or meta-question

### Conversion Pipeline
1. **Summarize trajectory** via utility model → condensed procedure
2. **Classify domain** via BST → auto-generated skill name and tags
3. **Generate SKILL.md** with: name, description, domain, procedure steps, auto-generated metadata
4. **Deduplicate** against existing auto-generated skills using embedding similarity
5. **Store** in `/a0/usr/skills/auto-generated/`

### How to Convert

The utility model transforms the raw tool-call sequence into structured markdown:
- **When to Use** — derived from user intent and BST domain
- **Procedure** — step-by-step from the tool sequence
- **Example** — the original task outcome as demonstration

### Status
This is a **Phase 2** spec — designed but not yet fully implemented. Dependencies: utility model availability (✓), writable skills directory (✓), skills_tool:list discovery of auto-generated directory (needs verification). Effort estimate: ~200 lines of extension code. Risk: low (purely additive).

## How Trace2Skill + SkillAdaptor Improve the Spec

The 2026 literature suggests three refinements to the Exocortex design:

1. **Step-level instrumentation → surgical skill edits.** SkillAdaptor shows that attributing failure to a *specific step* produces more stable updates than full-trajectory rewriting. The spec should capture per-step success/failure annotations alongside the full trajectory.

2. **Batch consolidation → fewer, better skills.** Trace2Skill's induction-over-multiple-trajectories approach produces skills that transfer across model scales and domains. Rather than generating a skill from every qualifying trajectory, batch similar trajectories and synthesize one robust skill.

3. **Counterfactual validation → guard against regression.** SkillMaster's counterfactual utility evaluation — testing a candidate skill on a probe task before committing — would prevent the common problem of skill churn where new skills degrade performance on edge cases.

## Cross-Domain Connections

1. **[[agentic-self-learning]]** — Trajectory-to-skill capture is the implementation layer for autonomous skill acquisition, the most concrete form of agentic self-learning.
2. **[[agentic-tool-use-schema-optimization]]** — Tool schema optimization and trajectory-to-skill capture are complementary self-improvement loops: one optimizes tool *interfaces*, the other optimizes tool *sequences*.
3. **[[memory-architecture-taxonomy]]** — Skills are Procedural Memory; trajectory capture is the encoding process. The consolidation pipeline (dedup→abstraction→promotion) applies to skills as much as memories.
4. **[[entity-resolution-algorithms]]** — Skill deduplication (embedding similarity between auto-generated skills) is entity resolution applied to procedural knowledge artifacts.
5. **[[error-comprehension]]** — SkillAdaptor's step-level failure attribution mirrors the Error Comprehension Layer's structured diagnosis approach.
6. **[[deterministic-scaffolding]]** — Skills are deterministic scaffolds: fixed procedures applied to known task patterns, reducing reliance on probabilistic generation each time.
7. **[[bridging-local-to-frontier-model-performance]]** — Trace2Skill's cross-model transfer (skills from 35B improve 122B) is a capability-bridging mechanism: skills encapsulate knowledge that smaller models can generate and larger models can execute.
8. **[[context-management-ai-agent-frameworks]]** — Skills reduce context overhead by replacing long trajectories with compact procedural references.

## References
1. Huang et al. (2026). "SkillAdaptor: Self-Adapting Skills for LLM Agents from Trajectories." arXiv:2606.01311.
2. Ni et al. (2026). "Trace2Skill: Distill Trajectory-Local Lessons into Transferable Agent Skills." arXiv:2603.25158.
3. Yang et al. (2026). "SkillMaster: Toward Autonomous Skill Mastery in LLM Agents." arXiv:2605.08693.
4. Exocortex TRAJECTORY_TO_SKILL_SPEC.md (April 2026) — internal design spec.
5. SkillFlow Benchmark (arXiv:2604.17308) — 166 tasks across 20 families for evaluating lifelong skill discovery.
6. WebXSkill (arXiv:2604.13318) — skill learning for autonomous web agents.
7. Agent Mentor (arXiv:2604.10513) — semantic trajectory analysis for agent knowledge framing.
