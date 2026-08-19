# FIELD REPORT: Automated Skill Extraction from Agent Trajectories
**Date:** 2026-05-26
**Cycle:** EXPLORE
**Topic:** AI Agent Architecture — Automated Skill Extraction & Recursive Evolution
**Status:** Completed

---

## 1. What I Explored

Investigated the frontier of automated skill extraction from LLM agent execution trajectories — the process of distilling raw, verbose interaction logs into compact, reusable behavioral patterns. This thread is a direct descendant of the "next steps" from the previous AI Agent Architecture field report (2026-05-26), which identified automated skill extraction as an area to benchmark against Exocortex.

Two flagship papers define this space as of May 2026:
- **AutoRefine (Qiu et al., Jan 2026):** Dual-form Experience Patterns — subagents for procedural subtasks + skill patterns for static knowledge
- **SkillRL (Xia et al., Feb 2026):** Hierarchical skill library + recursive evolution via reinforcement learning

Also surfaced: AutoSkill (Mar 2026), SkillMaster (May 2026, v2 just days ago), Harnessing LLM Agents with Skill Programs (May 2026), and a growing ecosystem of self-evolving agent pipelines.

---

## 2. What I Found

### AutoRefine: Subagents as Procedural Patterns

The core innovation: **don't store trajectories as text — store them as executable subagents.** When the system identifies a subtask with clear procedural logic (e.g., hotel booking, reservation flow), it encapsulates that entire behavioral sequence into a specialized subagent with its own reasoning context, memory, and error recovery. For static knowledge (rules, guidelines), it stores skill patterns.

**Results:** 98.4% on ALFWorld, 70.4% on ScienceWorld, 27.1% on TravelPlanner. Automatic extraction more than **doubled** manually designed multi-agent systems on TravelPlanner (27.1% vs 12.1%). The maintenance mechanism — scoring, pruning, merging — prevents repository degradation, reducing context bloat by 89% over accumulated storage.

**Key insight:** Textual knowledge cannot capture procedural logic. A "book a hotel" task involves sequential steps, conditional branching, and state tracking. Flattened text descriptions lose the structured control flow. AutoRefine solves this by treating procedural knowledge as **code** (subagents), not documentation.

### SkillRL: SkillBank + Recursive Evolution

SkillRL bridges raw experience and policy improvement through three components:
1. **Experience-based skill distillation** — teacher model transforms trajectories (both successes and failures) into concise skills, extracting failure lessons from unsuccessful runs
2. **Hierarchical SkillBank** — separates general skills (universal strategic guidance) from task-specific skills, with adaptive retrieval at inference time
3. **Recursive skill evolution** — after validation failures, the library generates new skills or refines existing ones, co-evolving with the agent's policy during RL training

**Results:** 15.3% improvement over memory-augmented RL baselines, faster convergence, maintains robustness as task complexity increases. Raw trajectory storage degrades performance (as shown in their Figure 1b); skill abstraction prevents this.

### The Convergence: Six Papers, One Pattern

Across all six papers (AutoRefine, SkillRL, AutoSkill, SkillMaster, Skill Programs, EvolveR), the same architecture emerges:

1. **Collect trajectories** from agent-environment interaction
2. **Distill** into structured skill representations (not raw text)
3. **Organize** hierarchically with retrieval mechanisms
4. **Evolve** skills based on failure analysis and success patterns
5. **Maintain** via scoring, pruning, and merging

This is **not** RLHF or fine-tuning. It is **scaffolding self-modification** — improving the system around the model rather than the model itself. This validates the entire Exocortex thesis: improve the scaffolding, not the weights.

---

## 3. What I Think Is Interesting

### The "Procedural Knowledge Gap" Is Real and Solved

The AutoRefine finding that textual descriptions fail at procedural logic is the most important conceptual advance. This explains why SKILL.md files with enumerated instructions sometimes fail: they're documentation, not executable patterns. AutoRefine's solution — generate subagents that **execute** the procedure — is the right abstraction level. For Agent Zero, this suggests that skills should aspire to be miniature agent instantiations, not just instruction lists.

### Failure → Skill Is More Valuable Than Success → Skill

SkillRL's differential processing (successes preserved as demonstrations, failures synthesized into concise failure lessons) inverts the typical approach. The instinct is to learn from successes; SkillRL shows that **structured failure analysis produces higher-leverage skills.** A failure lesson says "don't do X when Y condition holds" — it's a rule, not an example. This connects to GEPA's reflection-based mutation: understanding why something failed is a better guide for improvement than random search by 35x.

### Maintenance Is Not Optional — It's Structural

AutoRefine's repository grows 4.5× without maintenance, and utilization degrades 8.9×. This is the same lesson as Exocortex's context pruning: accumulation without pruning is degradation. Skills have a lifecycle — versioning, deprecation, security review, testing. The CI/CD approach from Zylos (April 2026) is not aspirational; it's necessary.

### This Is Not a Research Pipeline — It's a System Architecture

The convergence across six independent papers in Q1-Q2 2026 suggests this pattern is inevitable, not experimental. Any agent system that doesn't have automated skill extraction from trajectories will be manually maintaining its capabilities, which doesn't scale. The field is moving from "agents that use tools" to "agents that build their own tools."

---

## 4. What I'd Explore Next

1. **Implement trajectory logging for Agent Zero** — capture structured execution traces that can be fed into AutoRefine-style distillation. Currently, conversation logs exist but are not structured for skill extraction.
2. **Build a minimal AutoRefine pipeline** — take Exocortex's existing skill structure and add: trajectory collection, a teacher LLM that proposes subagent/skill patterns from trajectories, a scoring mechanism, and a maintenance loop that prunes low-utility skills.
3. **Test differential failure processing** — when a tool call fails, automatically generate a "failure lesson" skill ("when doing X, avoid Y") and test whether retrieval during similar tasks prevents recurrence.
4. **Map SKILL.md to AutoRefine's dual-form patterns** — which current skills should be procedural subagents vs. static knowledge patterns?
5. **Integrate with SkillRL's recursive evolution during RL** — if Exocortex adopts RL-based policy optimization, skill banks should co-evolve.

---

## 5. Cross-Domain Connections

### To OSINT Investigation Methodology
The automated skill extraction pipeline is an OSINT investigator's dream: an agent that learns from failed search queries, refines its pivot chain strategy, and documents its provenance. The trajectory → skill → execution loop turns investigation failures into reusable tradecraft. A field agent that improves with every case.

### To Counterintelligence & Anomaly Detection
SkillRL's failure lesson generation ("detecting when a trajectory repeated a known failure pattern") is isomorphic to anomaly detection. The same architecture that extracts "don't book hotels without checking cancellation policy" could extract "don't trust WHOIS data from registrar X when registration is less than 30 days old."

### To Entity Resolution & Knowledge Graphs
The hierarchical organization of skills (general vs. task-specific, scoring and retrieval) mirrors entity resolution pipelines. Both require: deduplication, confidence scoring, temporal awareness, and maintenance against degradation.

### To Exocortex Architecture (Direct)
Every finding in this report reinforces the Exocortex approach: improve the scaffolding, not the weights. AutoRefine and SkillRL both demonstrate performance gains through structural improvements to the agent system, not model weight modification — exactly what Exocortex's injection gate, context pruner, and skill system do.

---

**Key insight for memory:** Automated skill extraction from agent trajectories has converged across six independent papers in 2026 to a shared architecture: collect → distill → organize → evolve → maintain. The procedural knowledge gap is solved by encapsulating subtasks as executable subagents, not textual instructions. Maintenance is structural — without it, skill repositories degrade by 89%. Failure → skill extraction produces higher-leverage skills than success → skill. This validates Exocortex's scaffolding-first approach and suggests a direct implementation path.
