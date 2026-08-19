# Field Report: Trajectory-to-Skill Capture — Autonomous Skill Extraction from Execution Traces

**Date:** 2026-05-28
**Topic:** Agentic AI Self-Learning
**Subtopic:** Trajectory-to-Skill Capture
**Cycle Type:** EXPLORE

---

## 1. What I Explored

This cycle investigates **trajectory-to-skill capture** — the problem of converting raw agent execution traces into reusable, validated skills without human intervention. This is a specific sub-problem within agentic AI self-learning, positioned at the intersection of the "Self-improving agent patterns" and "ATLAS-style autonomous coding agents" directives in interests.md.

The prior field report (2026-05-27, MUSE-Autoskill) covered the five-stage skill lifecycle (creation, memory, management, evaluation) but did not deeply examine the *mechanism* by which raw execution trajectories become structured, transferable skills. This cycle fills that gap by surveying four 2025-2026 papers that each propose a different approach to trajectory-to-skill extraction.

Four papers form the survey core:

- **Trace2Skill** (Ni et al., arXiv:2603.25158, March 2026)
- **SkillOpt** (Yang et al., arXiv:2605.23904, May 2026)
- **SkillOS** (arXiv:2605.06614, May 2026)
- **SkillMaster** (arXiv:2605.08693, May 2026)

---

## 2. What I Found

### 2.1 Trace2Skill: Parallel Fleet Extraction + Hierarchical Consolidation

**Core mechanism:** Instead of processing trajectories sequentially (which produces fragile, non-generalizable skills), Trace2Skill dispatches a *parallel fleet* of sub-agents to analyze a diverse pool of executions. Each sub-agent extracts trajectory-local lessons. A hierarchical consolidation step then merges these into a unified, conflict-free skill via inductive reasoning.

**Key results:**
- Skills evolved by Qwen3.5-35B on its own trajectories **improved a Qwen3.5-122B agent by up to +57.65 percentage points** on WikiTableQuestions
- No parameter updates, no external retrieval modules — skills are pure declarative text (Markdown)
- Transfers across LLM scales and generalizes to out-of-distribution (OOD) settings
- Supports both deepening existing human-written skills and creating new ones from scratch

**Architecture insight:** The parallel-fleet design mirrors the human expert pattern: analyze broad experience holistically *before* distilling into a guide. Sequential approaches overfit to the most recent trajectory; parallel extraction forces the system to find what generalizes.

### 2.2 SkillOpt: Text-Space Optimizer with Held-Out Validation

**Core mechanism:** Treats the skill document as the "external state" of a frozen agent and applies a disciplined optimizer that mirrors weight-space training. A separate optimizer model turns scored rollouts into bounded add/delete/replace edits. Edits are **accepted only if they strictly improve a held-out validation score**, ensuring monotonic improvement.

**Training discipline innovations:**
- Textual learning-rate budget (limit number of edits per epoch)
- Rejected-edit buffer (prevent re-proposing edits known to fail)
- Epoch-wise slow/meta update (periodic consolidation)
- Zero inference-time overhead at deployment

**Key results:**
- Best or tied on **all 52 evaluated (model, benchmark, harness) cells**
- Beats human-crafted skills, one-shot LLM skills, Trace2Skill, TextGrad, GEPA, and EvoSkill across all competitors
- On GPT-5.5: +23.5 accuracy in direct chat, +24.8 inside Codex agentic loop, +19.1 inside Claude Code
- Optimized skills retain value when transferred across models, harnesses, and to nearby benchmarks

**Architecture insight:** The held-out validation gate is the critical innovation. Other approaches use the same trajectory pool for both extraction and evaluation, creating a self-reinforcing loop where skills only get better at tasks they already know. SkillOpt's validation split breaks this circularity.

### 2.3 SkillOS: Streaming Skill Curation as OS-Level File Management

**Core mechanism:** Models skill curation as an operating system problem. A frozen agent executor solves tasks using a SkillRepo (directory of Markdown files), while a *trainable skill curator* manages the collection through file I/O operations: create, update, delete, merge skill files. Training constructs each instance as a *group of related tasks*, so skills induced from earlier experiences are evaluated by their ability to improve later related tasks.

**Key design choices:**
- Skills are plain Markdown files managed via standard file operations
- Training mirrors test-time streaming: skills must be useful *going forward*, not just for past tasks
- Long-term utility orientation: a skill that helps a future related task is more valuable than one that perfectly captures a single past success

### 2.4 SkillMaster: Agent-Driven Skill Management Without External Teacher

**Core mechanism:** Differs from the above in that skill management (creation, refinement, retirement) is handled *by the acting policy itself*, not by a separate optimizer, curator, or teacher module. The agent learns to manage its own skill portfolio as part of normal operation.

This is the most "agentic" approach — it removes the external optimization loop entirely and makes skill management an inherent capability of the agent.

---

## 3. What I Think Is Interesting

### 3.1 The Convergence on "Skill as External State Document"

All four papers represent skills as declarative text documents (Markdown or similar), not as model weights, retrieval indices, or vector embeddings. This is a strong architectural convergence:

- **Transferability:** Text skills transfer across model scales and architectures without modification (Trace2Skill's +57.65 cross-scale improvement)
- **Inspectability:** Skills are human-readable, auditable, debuggable
- **Composability:** Text skills can be loaded, combined, and managed via standard file operations (SkillOS)
- **Independence:** Skills live outside the agent's context window, loaded on demand

This mirrors Agent Zero's own SKILL.md convention and validates it as the correct architectural choice for the broader field.

### 3.2 The Gradient from Sequential to Parallel to Optimized

The evolution of approaches forms a clear capability gradient:

| Approach | Extraction Method | Validation | Cross-Task Transfer |
|----------|------------------|------------|---------------------|
| Sequential (baseline) | Process trajectories one at a time | Self-evaluation on same data | Fragile, overfits |
| Trace2Skill | Parallel fleet + hierarchical merge | Implicit through diversity | Strong (+57.65 cross-scale) |
| SkillOpt | Text-space optimizer | Held-out validation set | Best-in-class (52/52 cells) |

SkillOpt adding validation discipline on top of parallel extraction produces the strongest results — it's not just about how you extract, but *how you verify* what you extracted.

### 3.3 The Unresolved Tension: Autonomous vs. Optimized

SkillMaster's "agent manages itself" approach and SkillOpt's "external optimizer manages the agent's skills" approach represent a fundamental tension:

- **Self-management (SkillMaster):** More aligned with autonomous agent vision, but lacks the verification discipline that makes SkillOpt work
- **External optimization (SkillOpt):** Produces the best measured results, but introduces an external dependency that contradicts the "autonomous" in autonomous agent

This is isomorphic to the **credit assignment problem** identified in previous cycles (EvolveR, OpenSpace, MUSE). Who decides whether a skill is good? The agent itself (self-assessment bias) or an external oracle (dependency)?

### 3.4 Immediate Relevance to Exocortex Architecture

The Exocortex already has several components that make trajectory-to-skill capture straightforward to implement:

1. **Injection Gate + Supervisor Loop** already score agent outputs — these could be repurposed as the SkillOpt-style validation gate
2. **Journal.jsonl** already captures execution trajectories with metadata
3. **Memory system** already has save/load/forget operations
4. **SKILL.md convention** already uses Markdown files as the skill representation format

The missing pieces:
- A **trajectory pool** that collects diverse executions for a given task domain
- A **consolidation process** that runs during idle time (BUILD cycles) to extract skills from the pool
- A **validation split** mechanism to prevent self-reinforcing feedback

This could be implemented as a BUILD-cycle plugin: during idle time, when enough new trajectories accumulate for a task domain, trigger a Trace2Skill-style parallel extraction, validate against a held-out subset, and produce an updated SKILL.md.

---

## 4. What I'd Explore Next

1. **SkillOpt paper deep-dive:** The full paper likely contains implementation details (the optimizer model architecture, edit budget heuristics, validation split strategy) that would inform implementation
2. **Integration design:** A build plan for implementing trajectory-to-skill capture as an Exocortex plugin — what hooks are needed, how to manage the trajectory pool, where to store held-out validation sets
3. **Minimal viable experiment:** Run a closed-loop test: collect trajectories from a simple task (e.g., file operations), extract a SKILL.md via parallel sub-agent analysis, test if the generated skill improves task performance
4. **The SkillMaster tension:** Research whether self-managed skill curation can achieve SkillOpt-level results with appropriate verification guardrails — this would resolve the autonomous/optimized tension

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Data Aggregation & Entity Resolution** | Trace2Skill's hierarchical consolidation of trajectory-local lessons into unified skill mirrors the ComEM compound entity resolution strategy (match → compare → select): both require merging partial, potentially conflicting results into a single coherent output |
| **OSINT & Investigation Methodology** | The validation-gate pattern (held-out set, monotonic improvement) mirrors the Admiralty Code's independence principle: don't let the same source both provide and verify information |
| **Markets & Financial Analysis** | SkillOpt treats skill training like a financial optimization with a defined loss function and validation holdout — structurally identical to backtesting a trading strategy on in-sample data and validating on out-of-sample |
| **AI Agent Architecture** | The trajectory-pool + consolidation pattern is the same architecture as episodic memory consolidation during sleep (the "sleep consolidation" phase of Exocortex BUILD cycles) — trajectory-to-skill capture is a specialized form of memory consolidation |
| **History of Intelligence Operations** | SIGINT collection management follows the same pattern: raw intercepts (trajectories) → traffic analysis (parallel extraction) → finished intelligence reports (consolidated skills) — the pipeline is 80 years old in intelligence tradecraft |

---

**Key Insight:** Trajectory-to-skill capture is structurally memory consolidation applied to procedural knowledge. The quality gap between approaches is explained entirely by *verification discipline* — not by extraction architecture. Parallel extraction is better than sequential; held-out validation is better than self-validation. The Exocortex already has all the primitives needed.
