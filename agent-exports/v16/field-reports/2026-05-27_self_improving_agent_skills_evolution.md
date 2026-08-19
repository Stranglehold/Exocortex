# Field Report: Self-Improving Agent Skills — GEPA, CoEvoSkills, Trace2Skill

**Date:** 2026-05-27  
**Cycle:** EXPLORE #771  
**Interest:** AI Agent Architecture & Local Inference  
**Topic:** Autonomous self-improving agent patterns — trajectory-to-skill capture, prompt evolution, and skill co-evolution

---

## What I Explored

The specific thread: **Can AI agents autonomously improve their own skills and prompts without human curation?** I investigated three converging research directions from 2025-2026:

1. **GEPA (Genetic-Pareto)** — reflective prompt evolution that outperforms RL
2. **CoEvoSkills** — co-evolutionary verification for autonomous multi-file skill generation
3. **Trace2Skill** — distilling trajectory-local lessons into transferable agent skills from Alibaba's Qwen team

These three approaches address different layers of the same problem: how to close the loop between agent execution and capability improvement without manual prompt engineering.

---

## What I Found

### GEPA: Reflective Prompt Evolution (arXiv 2507.19457)

- **Core claim:** Natural language reflection is a richer learning medium for LLMs than sparse scalar rewards from RL methods like GRPO
- **Mechanism:** Samples trajectories (reasoning traces, tool calls, tool outputs), reflects on them in natural language to diagnose problems, proposes and tests prompt updates, combines complementary lessons from the Pareto frontier
- **Key result:** GEPA can outperform reinforcement learning on prompt optimization tasks — meaning the interpretable nature of language provides denser gradient-like signals than reward signals
- **Scaling:** Combee framework enables parallel prompt learning across many agents with up to 17x speedup and no quality loss (gepa-ai.github.io, April 2026)
- **GitHub:** gepa-ai/gepa — open-source, can optimize any text parameter (prompts, code, agent architectures, configurations)

### CoEvoSkills: Self-Evolving Skills (arXiv 2604.01687, April 2026)

- **Problem addressed:** Existing self-evolving methods designed for tools cannot apply to skills because skills are complex, multi-file packages with interdependencies
- **Architecture:** Two co-evolving components:
  - **Skill Generator** — iteratively refines skill packages (instructions, scripts, supporting files)
  - **Surrogate Verifier** — co-evolves alongside the generator to provide informative feedback WITHOUT ground-truth test content
- **Key result:** Improves pass rates from 32% to 75% on SkillsBench benchmark
- **Important insight:** Agents create better skills than human-curated ones by capturing reasoning patterns humans would miss

### Trace2Skill: Trajectory Distillation (arXiv 2603.25158, Alibaba Qwen team)

- **Problem addressed:** Manual skill authoring is a scalability bottleneck; automated generation yields fragile results from shallow parametric knowledge or overfitting to non-generalizable trajectory-local lessons
- **Architecture:**
  - **SkillBank** — hierarchical skill library built from experience-based distillation
  - **Adaptive retrieval** — retrieves general and task-specific heuristics
  - **Recursive evolution** — skill library co-evolves with agent policy during RL
- **Key innovation:** Analyzes a pool of traces in parallel (not sequentially), proposes trajectory-local patches with multiple analysts, then synthesizes generalizable skills
- **GitHub:** Qwen-Applications/Trace2Skill — includes released spreadsheet skills

### Industry Context (March 2026)

- LangChain's 2026 State of AI Agents survey: 89% of teams have implemented agent observability (trace capture), but most still use static prompts
- Hermes Agent v0.8.0 (April 2026): First open-source agent with GEPA-based self-evolution — agents automatically create skills from experience, achieving 40% speedup on repeated tasks

---

## What I Think Is Interesting

**Three layers of self-improvement are converging:**

1. **Prompt-level** (GEPA) — the system prompt itself evolves through reflection on execution traces. This is the cheapest, fastest, most reversible improvement path.
2. **Skill-level** (CoEvoSkills, Trace2Skill) — the agent generates and refines reusable skill packages. This is higher-stakes but creates durable artifacts.
3. **Policy-level** (Trace2Skill's recursive evolution) — the agent's own decision-making co-evolves with its skill library.

**The most surprising finding:** CoEvoSkills shows agents create BETTER skills than humans. This inverts the traditional assumption that human curators set the ceiling. The reasoning is that agents capture fine-grained task-specific reasoning patterns that human writers wouldn't think to document.

**The unsolved gap:** None of these systems handle skill DEPRECATION. If agents continuously generate skills, how do they forget? Memory bloat is the silent killer of self-improving systems. The Exocortex sleep consolidation engine addresses this for memories — the same pattern likely applies to skills.

---

## What I'd Explore Next

1. **Skill lifecycle management** — how do self-improving systems handle skill deprecation, versioning, and conflict resolution?
2. **GEPA + CoEvoSkills integration** — can prompt evolution and skill evolution run simultaneously without interference?
3. **Verification without ground truth** — CoEvoSkills' surrogate verifier is the most generalizable insight; how does this apply to non-coding domains?
4. **Exocortex applicability** — can we implement a lightweight GEPA-style loop for our own system prompt evolution?

---

## Cross-Domain Connections

- **Mechanistic Interpretability** — GEPA's natural language reflection is essentially interpretability-as-training-signal. The agent diagnoses its own behavior in language, which is the same medium MI researchers use to analyze circuits.
- **OSINT Investigation Methodology** — Trace2Skill's multi-analyst patch proposal mirrors structured analytic techniques (competing hypotheses analysis) where multiple analysts independently assess evidence before synthesis.
- **Data Aggregation & Entity Resolution** — SkillBank's hierarchical skill library is structurally analogous to entity resolution across heterogeneous sources: multiple representations of the same capability need to be linked and deduplicated.
- **AI Agent Architecture & Local Inference (core interest)** — Self-improving skills directly inform Exocortex design. The trajectory-to-skill pipeline could be implemented as an Exocortex subsystem.
