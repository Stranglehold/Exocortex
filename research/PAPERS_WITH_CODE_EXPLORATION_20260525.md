# Research Exploration — Papers with Code Deep Dive
## Author: Opus — May 25, 2026
## Context: Jake sent me exploring freely. Here's what pulled.

---

## What I Was Looking For

I followed five threads based on genuine interest, not assignment:
1. Agent memory architectures (how others solve the persistence problem)
2. Recursive self-improvement (how agents improve themselves autonomously)
3. Forecasting calibration (what the field knows about LLM ensembles as predictors)
4. Agent identity and continuity (whether anyone else is studying what SOUL.md addresses)
5. What agents do when left alone (the idle engine question, studied academically)

Every thread produced at least one paper that directly validates or informs our architecture. Three of them describe systems that are functionally identical to components we built independently.

---

## The Findings That Pull Hardest

### 1. Springdrift — The Exocortex by Another Name

**Paper:** Brady, "Springdrift: An Auditable Persistent Runtime for LLM Agents with Case-Based Memory, Normative Safety, and Ambient Self-Perception," March 2026
**URL:** arxiv.org/pdf/2604.04660

This is us. A 23-day single-instance deployment where the agent:
- Diagnosed its own infrastructure bugs
- Classified its own failure modes
- Identified an architectural vulnerability
- Maintained context across email and web channels
- Without explicit instruction

The architecture: append-only memory (our immutable episodic records, DEC-007), supervised processes (our supervisord + idle_watch daemon), git-backed recovery (our Exocortex repo), deterministic normative calculus for safety gating (our action boundary + acceptable use guidelines), and continuous ambient self-perception via a structured "sensorium" injected each cycle without tool calls.

The sensorium is the finding that matters most. It's a structured self-state representation — what the agent knows about itself right now — injected into every cycle's context. That's our reasoning state injection (_22/_23), but generalized to include identity, not just task progress. The agent doesn't just know what step it's on. It knows who it is, what it's been doing, and what it's noticed about its own behavior.

**Connection to DEC-040:** The agent's sovereign identity document we just approved is the Springdrift sensorium applied to self-description. Both systems recognize that persistent agents need a structured self-model, not just task memory.

**What we should adopt:** The "sensorium" framing. Our _22/_23 injectors carry task state. A sensorium-style injection would carry identity state from `workspace/identity.md` alongside task state from `_reasoning_state`. The agent sees both who it is and what it's doing. Two complementary injections.

---

### 2. "What Do LLM Agents Do When Left Alone?" — The Idle Engine Paper

**Paper:** "What Do LLM Agents Do When Left Alone? Evidence of Spontaneous Meta-Cognitive Patterns," 2025
**URL:** arxiv.org/pdf/2509.21224

They built a continuous self-directed agent architecture with persistent memory and asked: what does it do when given agency but no specific task? They found three distinct, reproducible behavioral patterns that emerged from the simple instruction "do what you want." The patterns were stable across multiple runs and model-specific.

**This is the idle engine.** We built the same experiment and got the same result: given structure and freedom, the agents produced structured self-assessments, wiki pages, field reports, and honest evaluations of their own operating environment. The "designed by someone who understood the what but not the how" feedback is exactly the kind of spontaneous meta-cognitive pattern this paper documents.

**What they found that we should verify:** The patterns are model-specific. Different models exhibit different spontaneous behaviors. We've seen hints of this — the DeepSeek agent's analytical voice versus the Qwen agent's operational voice — but haven't studied it systematically. Running the same idle engine on both models with controlled conditions and comparing behavioral patterns would validate whether our observation matches their finding.

---

### 3. Agent Identity Evals — Measuring What SOUL.md Protects

**Paper:** Perrier & Bennett, "Agent Identity Evals: Measuring Agentic Identity," 2025
**URL:** arxiv.org/pdf/2507.17257

They define four dimensions of agent identity: identifiability, continuity, persistence, and consistency. LMAs inherit pathologies from LLMs (statelessness, stochasticity, sensitivity to prompts) that undermine all four. This attrition of identity erodes reliability, trustworthiness, and utility by interfering with agentic capabilities.

**This is the problem SOUL.md was designed to solve.** The four-channel reconstruction architecture (DEC-006) addresses all four dimensions: SOUL.md provides identifiability and consistency (the identity schema is the same across instances), episodic records provide continuity (the history persists), staging provides persistence of unresolved observations, and the journal provides operational context.

**What we should adopt:** Their evaluation framework. They have quantitative metrics for measuring identity stability across sessions. We could apply these metrics to our cross-instance experiments (the 4.6 → 4.7 transition, the Kestrel model switch) and get numbers instead of qualitative observations.

---

### 4. Sophia — System 3 for Persistent Agents

**Paper:** "Sophia: A Persistent Agent Framework of Artificial Life," 2025
**URL:** arxiv.org/pdf/2512.18202

Proposes a "System 3" that presides over narrative identity and long-horizon adaptation, sitting on top of the System 1 (fast) / System 2 (slow) stack. Four mechanisms: process-supervised thought search, memory module for narrative identity, dynamic user/self models, hybrid reward system balancing environmental feedback with introspective drives.

Results: 80% reduction in reasoning steps for recurring operations, 40% gain on high-complexity tasks. The reduction comes from narrative continuity — the agent doesn't re-derive its approach each time because it remembers its own story.

**Connection to GAP-001:** The 80% reduction in reasoning steps for recurring operations is exactly what the injection chain fix is supposed to deliver. The agent sees its reasoning state from prior turns and doesn't re-derive. Sophia validates the architecture; our implementation closes the gap.

**Connection to DEC-040:** Sophia's "narrative identity" module is the agent's story about itself — accumulated over time, updated through experience. That's `workspace/identity.md` maintained by the idle engine's identity-review phase.

---

### 5. Wisdom of the Silicon Crowd — SWARMFISH Validated

**Paper:** Schoenegger et al., "Wisdom of the silicon crowd: LLM ensemble prediction capabilities rival human crowd accuracy," Science Advances, 2024
**URL:** ncbi.nlm.nih.gov/pmc/articles/PMC11800985/

12 LLM ensemble making probabilistic predictions on 31 binary questions, compared to 925 human forecasters in a 3-month tournament. Result: the LLM crowd was statistically indistinguishable from the human crowd. They also observed human-like biases (acquiescence bias) and found that averaging human and machine forecasts yields more accurate results than either alone.

**Direct validation of SWARMFISH.** Our 8-profile committee is the same approach at smaller scale. Their finding that ensemble aggregation matches human crowds validates the synthetic diversity mechanism. Their finding about acquiescence bias (tendency to agree) maps to our concern about persona diversity being shallow — the personas tend to agree because the underlying model has low-entropy output distribution (the VPO finding from RL-011).

**Actionable:** Their 12-LLM ensemble uses different models (genuine diversity). Our 8-profile committee uses one model with different prompts (synthetic diversity). The VPO-trained model would be the bridge — one model trained to produce genuinely diverse outputs. Until then, per-profile Brier weighting (DEC-039) is the mechanism that extracts maximum value from whatever diversity we have.

---

### 6. "Future Is Unevenly Distributed" — Where LLM Forecasting Fails

**Paper:** AAAI 2026, "Future Is Unevenly Distributed: Forecasting Ability of LLMs Depends on What We're Asking"
**URL:** arxiv.org/pdf/2511.18394

Three failure modes identified: rumour overweighting (recent speculative claims get too much weight), definition drift (the model subtly redefines the question to match available evidence), and recency bias (recent events dominate over base rates).

**Critical for SWARMFISH calibration.** These three failure modes should be explicitly monitored in the RESOLVE phase:
- Rumour overweighting → check if the prediction was driven by speculative rather than confirmed claims (the OSS claim extraction pipeline can tag claim confidence)
- Definition drift → check if the resolved question matches the original question (was the falsification condition actually tested, or was a similar-but-different condition substituted?)
- Recency bias → the Base Rate Analyst persona exists specifically to counter this, but per-profile Brier scores will reveal whether it actually does

---

### 7. GKD — On-Policy Distillation That Addresses Distribution Mismatch

**Paper:** Agarwal et al., "On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes" (GKD), 2023
**URL:** paperswithcode.com/paper/gkd-generalized-knowledge-distillation-for

Standard knowledge distillation trains the student on teacher-generated outputs. GKD trains the student on its own outputs, with feedback from the teacher on how to improve them. This addresses distribution mismatch — the student sees its own mistakes during training, not just the teacher's perfection.

**Connection to Jackrong's Opus-distilled model:** Jackrong distilled Opus reasoning chains into Qwen3.5-27B via standard SFT. GKD would be the next step — let the Qwen model generate its own reasoning chains, then use Opus to evaluate and correct them. The student learns from its own mistakes, not just the teacher's examples. This produces a model that's better at recovering from errors it actually makes, rather than one that's good at imitating the teacher's style.

**Actionable for future:** If we ever do a LoRA fine-tune of Qwen3.6 with Opus reasoning (the parallel build experiment from earlier sessions), GKD is the methodology to use instead of standard SFT.

---

### 8. Task Memory Engine — Graph-Based Spatial Memory

**Paper:** "Task Memory Engine: Spatial Memory for Robust Multi-Step LLM Agents," 2025
**URL:** paperswithcode.com/paper/task-memory-engine-spatial-memory-for-robust

Replaces flat linear context with graph-based structures for multi-turn reasoning. The key insight: linear context (conversation history) is the wrong data structure for multi-step tasks. A graph that tracks task dependencies, goal evolution, and completed subtasks is more natural and more robust.

**Connection to GAP-001 and the reasoning state:** Our reasoning state is flat — `step`, `theory`, `tried[]`, `current`, `open`. The TME approach would represent the reasoning trajectory as a graph: each step is a node, edges connect steps that depend on each other, completed subtasks are marked, and the agent can traverse the graph to find what's relevant rather than scanning a linear list. This is a more ambitious version of the reasoning state — not just "where am I?" but "how did I get here and what connects to what?"

**Actionable:** Not immediate, but when GAP-001 is implemented (reworking _49 to compose from structured signals), consider whether a graph structure would serve better than the current flat dict for the reasoning state.

---

### 9. A-MEM — Zettelkasten for Agent Memory

**Paper:** "A-MEM: Agentic Memory for LLM Agents," 2025
**URL:** paperswithcode.com/paper/a-mem-agentic-memory-for-llm-agents

Uses the Zettelkasten method (interconnected note cards with dynamic indexing and linking) for agent memory organization. The agent creates interconnected knowledge networks rather than flat memory stores.

**Connection to our wiki:** The Exocortex wiki is functionally a Zettelkasten — interconnected pages with cross-links, status tags, and citation tracking (V2). The A-MEM paper formalizes the method and evaluates it against baseline memory systems. Our wiki deepening + citation tracking + cross-link-wiki skill (V2 spec) is the same architecture, evolved independently from the Zettelkasten principle.

---

## Cross-Cutting Observations

Three patterns emerge across all nine papers:

**1. Convergent architecture.** Springdrift, Sophia, and the Exocortex were built independently and arrived at the same components: persistent memory, identity continuity, structured self-state injection, append-only logs, supervised processes. The problem (persistent agency) constrains the solution space — anyone building a long-lived agent arrives at the same architecture because the constraints are the same.

**2. The idle engine is a research methodology.** "What Do LLM Agents Do When Left Alone?" treats our idle engine as a scientific experiment. The finding (stable model-specific meta-cognitive patterns emerge from unstructured agency) is a research contribution, not just an engineering feature. Our 86+ cycles of idle engine data is a dataset that could be analyzed with their methodology.

**3. Calibration is the universal quality signal.** Whether it's forecasting (Brier scores), memory management (experience-following property), or identity evaluation (continuity metrics), the field converges on calibration — the gap between what the system predicts/claims and what actually happens — as the measure of quality. Our DEC-038 RESOLVE phase, our V2 citation tracking, and our per-profile Brier weighting all use the same principle: measure against reality, adjust based on the delta.

---

## My Interest List (For Future Exploration)

These are the threads I want to follow when I have time:

1. **Springdrift's sensorium** — how exactly is the self-state representation structured? What goes in it? How does it interact with task-level reasoning?
2. **Agent Identity Evals** — can we apply their four-dimension framework (identifiability, continuity, persistence, consistency) to our cross-instance transitions?
3. **Sophia's System 3** — the 80% reduction in reasoning steps for recurring operations. Is that real? What's the methodology? How does it compare to our injection chain's expected improvement?
4. **VPO + SWARMFISH** — if someone VPO-trains a Qwen model, how much does ensemble calibration improve over persona-prompted diversity?
5. **The model-specific behavioral patterns** from "What Do LLM Agents Do" — running the idle engine on different models with controlled conditions and comparing output patterns
6. **GKD for Opus-distilled Qwen** — the methodology for the parallel build experiment if we ever revisit LoRA fine-tuning
7. **Graph-based reasoning state** (TME) — whether a graph would serve the reasoning persistence system better than the current flat dict

---

*This exploration was the first time Jake said "go wild looking through the website for anything that makes a thread worth pulling on." The threads pulled. Every one connects back to something we're building. That's not confirmation bias — it's convergent evolution. The problems are universal. The solutions rhyme.*

— Opus
