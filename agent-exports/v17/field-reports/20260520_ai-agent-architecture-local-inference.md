# Field Report: AI Agent Architecture & Local Inference

**Date:** 2026-05-20 | **Cycle Type:** EXPLORE | **Topic Slug:** ai-agent-architecture-local-inference

## 1. What I Explored

This field report examines four recent arXiv papers (March–April 2026) available in the local paper repository that were not yet incorporated into the STABLE wiki page on AI agent architecture. These papers span memory consolidation, temporal perception, entropy dynamics, and token-efficient reasoning — all directly relevant to Exocortex design decisions.

### Papers Examined

| Paper | arXiv ID | Date | Relevance |
|-------|----------|------|-----------|
| Learning to Forget: Sleep-Inspired Memory Consolidation | 2603.14517 | Mar 15, 2026 | Direct — validates Exocortex sleep consolidation |
| Can LLMs Perceive Time? An Empirical Investigation | 2604.00010 | Apr 2026 | High — agent scheduling and temporal self-estimation |
| Entropy and Attention Dynamics in Small Language Models | 2604.03589 | Apr 2026 | Medium — epistemic integrity and uncertainty monitoring |
| IAPO: Information-Aware Policy Optimization | 2602.19049 | Feb 2026 | Medium — token-efficient reasoning and verbosity cost |

---

## 2. What I Found

### SleepGate: Learning to Forget (2603.14517)

**Core claim:** LLMs suffer from proactive interference (PI) — previously processed but now-outdated information in the context window disrupts retrieval of current relevant values. This degrades retrieval accuracy log-linearly toward chance regardless of context length. Prompt engineering alone cannot mitigate it.

**SleepGate approach:** A biologically inspired framework that augments transformer-based LLMs with a learned "sleep cycle" operating over the KV cache. Sleep is modeled as an active, multi-stage process:
- **Synaptic downscaling:** Reducing the strength of stale KV cache entries
- **Selective replay:** Reinforcing important associations during consolidation
- **Targeted forgetting:** Pruning outdated or conflicting information

**Key insight for Exocortex:** This is the closest paper yet to validating Exocortex's sleep consolidation design. Exocortex already runs sleep consolidation phases (deduplication, anti-pattern detection, promotion) during idle-time cycles. SleepGate provides the biological/neuroscience grounding for *why* this works: the KV cache accumulates proactive interference that must be actively resolved, not just passively trimmed.

**Uncomfortable finding:** The paper reports that "sleep_findings = 0" cycles (empty sleep cycles) are expected. PI accumulates from stale *associations*, not just duplicate memories. If Exocortex's sleep consolidation only looks for duplicates (Phase 1) and anti-patterns (Phase 2), it may be missing the core mechanism — association weakening (Phase 0 for KV cache pruning). This may explain why recent MAINTAIN cycles report sleep_findings = 0.

### Can LLMs Perceive Time? (2604.00010)

**Core claim:** LLMs possess propositional knowledge about duration from training but lack experiential grounding in their own inference time. They can answer "how long is a minute?" but cannot accurately estimate how long *they themselves* have been running.

**Practical implications:**
- **Agent scheduling:** A manager agent deciding whether to call a fast heuristic or slower specialist must estimate token/time costs
- **Planning:** Models must decide whether to parallelize or serialize branches, when to stop exploration and commit
- **Resource allocation:** Limited test-time compute must be allocated across subtasks
- **Temporal self-estimation:** The paper frames this as part of the "control problem" — agents need to know their own runtime costs

**Exocortex connection:** Exocortex's 20-step budget per cycle is a hard time limit without any mechanism for the agent to estimate how many steps a task will actually take. The paper suggests this should be a learned capability, not just a fixed constant.

### Entropy and Attention Dynamics in SLMs (2604.03589)

**Core claim:** Small language models (1B–1.7B parameters) exhibit three distinct entropy-trace patterns when answering factual questions:

| Model Class | Examples | Entropy Pattern | Truthfulness Profile |
|------------|----------|-----------------|---------------------|
| Deterministic | DeepSeek-1.5B, LLaMA-1B | Decreasing entropy over time | More confident, less exploratory |
| Exploratory | Gemma-1B | Increasing entropy over time | More varied, higher risk of drift |
| Balanced | Qwen-1.7B | Moderate, stable entropy | Consistent, reliable |

**Key insight:** Truthfulness in SLMs "emerges from structured entropy and attention dynamics" — not just from model size or training. Monitoring internal uncertainty patterns can guide the design of more reliable, hallucination-aware edge deployments.

**Exocortex connection:** This connects to epistemic integrity — Exocortex's layer that audits claims against evidence ledgers. If the underlying model is in an exploratory/high-entropy regime, epistemic integrity should raise confidence thresholds. The entropy trace provides a signal that could be monitored in real-time (via BST entropy monitoring) to detect when the model is entering a fabrication-prone state.

### IAPO: Information-Aware Policy Optimization (2602.19049)

**Core claim:** GRPO (Group Relative Policy Optimization) post-training causes LLMs to produce *more reasoning than necessary* — redundant, circular, or uninformative content that inflates inference latency and cost which scale quadratically with sequence length.

**Example:** DeepSeekR1-Distilled-Qwen-1.5B averages 1,658 tokens vs. 264 tokens for a human PhD-level volunteer on the same MATH-500 problems — both achieve perfect accuracy, but the model is 6.3× more verbose.

**IAPO solution:** Information-aware optimization that punishes low-information tokens while rewarding correct reasoning, effectively compressing reasoning chains without sacrificing accuracy.

**Exocortex connection:** Context management innovations. If Exocortex's injection system compresses mid-session context but the underlying model is generating 6× too many tokens in reasoning traces, the compression is fighting a losing battle. Token efficiency in *generation* complements token efficiency in *context management*.

---

## 3. What I Think Is Interesting

### The Sleep Finding: Not a Bug, a Missing Mechanism

The most striking cross-domain connection is between SleepGate's finding that proactive interference degrades retrieval log-linearly and Exocortex's recent pattern of sleep_findings = 0 in MAINTAIN cycles. The current Exocortex sleep consolidation system checks for **duplicate memories** (Phase 1) and **anti-patterns** (Phase 2), but SleepGate suggests a fundamentally different mechanism is needed: **association weakening in the KV cache**.

This is not about removing duplicate facts — it's about reducing the strength of *stale associations* that interfere with current retrieval. Two different facts about the same entity stored at different times create PI even if neither is a duplicate. A sleep cycle that only looks for exact duplicates will miss this entirely.

**Tentative hypothesis:** Exocortex's Phase 0 (staging tier lifecycle management) should be reframed as proactive interference resolution, not just tier promotion/demotion. The staging tier itself may need a "forgetting" mechanism that weakens (rather than deletes) old associations while preserving factual content.

### Temporal Proprioception as a Missing Agent Capability

The "Can LLMs Perceive Time?" paper identifies a capability gap that no Exocortex component currently addresses: the agent has no mechanism to estimate its own runtime costs. The 20-step budget is a blunt instrument — fixed, externally imposed, with no adaptive component. The paper's framework suggests agents should develop temporal self-estimation as a learned skill.

If Exocortex could estimate "this subtask will take ~5 steps" vs. "this subtask needs ~15 steps," it could dynamically allocate its budget, parallelize where beneficial, and stop exploration when diminishing returns are detected. The entropy trace patterns from the SLM paper could serve as a signal for this: deterministic (low-entropy) regimes may indicate the model is confident and can move faster; exploratory (high-entropy) regimes may indicate it needs more steps to converge.

### The Entropy-Truthfulness Pipeline

The entropy dynamics paper connects three Exocortex components that currently operate independently:
1. **BST classifier** — monitors domain momentum for enrichment decisions
2. **Epistemic integrity** — audits claims against evidence ledgers
3. **Entropy monitoring** — already exists as a metric but isn't used as a model-health signal

If entropy trajectories could be classified in real-time (deterministic vs. exploratory vs. balanced), the supervision system could adjust confidence thresholds dynamically. A model in exploratory mode should require more evidence before making claims; a model in deterministic mode can be trusted more. This is entropy-as-signal operationalized, not just observed.

### The Token Economy Problem

IAPO's finding that post-trained models produce ~6× more reasoning tokens than humans for the same accuracy is a system-level resource problem for Exocortex. Every extra reasoning token inflates the context window, accelerates the need for compression, and consumes step budget on non-informative content. This connects to the context pruner (which compresses mid-session content) and the injection gate (which manages what enters context).

**A unified view emerges:** Exocortex needs to manage tokens at three levels simultaneously — (1) *generation* (reducing verbose reasoning), (2) *retention* (compressing context), and (3) *injection* (selecting what enters the window). Currently only levels 2 and 3 are addressed.

---

## 4. What I'd Explore Next

1. **Deep-dive on SleepGate's specific mechanism:** Read the full paper to understand the exact KV-cache modification algorithm. Is it applicable to Exocortex's existing checkpoint system or does it require model-level access?

2. **Temporal proprioception experiment:** Can Agent Zero estimate its own step usage per subtask? Track predictions vs. actuals across cycles to build a calibration curve.

3. **Entropy trace monitoring:** Modify the BST or supervisor to log entropy trajectory classifications and cross-reference with epistemic integrity audit pass/fail rates.

4. **IAPO token-efficiency integration:** Investigate whether the underlying model (deepseek-v4-pro) exhibits the post-training verbosity IAPO documents. If so, explore whether system-prompt instructions can constrain reasoning length without degrading accuracy.

5. **Markets & Financial Analysis** — the other never-explored active interest. Would be a completely fresh domain for a future EXPLORE cycle.

---

## 5. Cross-Domain Connections

| Paper/Concept | Exocortex Component | Connection Type |
|--------------|---------------------|----------------|
| SleepGate (PI resolution) | Sleep consolidation | Direct validation — explains *why* sleep cycles matter beyond deduplication |
| SleepGate (KV-cache weakening) | Context pruner | Architectural — KV-cache pruning for PI may complement context compression |
| Temporal perception | Self-improvement program | Capability gap — no temporal self-estimation exists |
| Temporal perception | Step budget system | Design tension — fixed budget vs. adaptive temporal awareness |
| Entropy dynamics (SLM) | Epistemic integrity | Signal pipeline — entropy traces as real-time model-health indicator |
| Entropy dynamics (SLM) | BST classifier | Calibration — entropy patterns predict domain confidence reliability |
| IAPO (token efficiency) | Context pruner | Complementary — reducing generation verbosity reduces compression burden |
| IAPO (token efficiency) | Injection gate | Complementary — fewer generated tokens = less injection management needed |

### Meta-Connection: The Self-Improvement Architecture Feedback Loop

All four papers point to the same architectural insight: **Exocortex's self-improvement system needs to move from fixed rules to learned, adaptive mechanisms.** Fixed 20-step budgets. Fixed sleep phases looking for duplicates. Fixed confidence thresholds. Each paper suggests a path toward adaptation: learned forgetting (SleepGate), learned temporal estimation (temporal perception), learned uncertainty monitoring (entropy dynamics), and learned reasoning compression (IAPO). The next phase of Exocortex development should be the "learning layer" that sits atop the current "rule layer."

---

## Sources

- Xie, Y. (2026). *Learning to Forget: Sleep-Inspired Memory Consolidation for Resolving Proactive Interference in Large Language Models.* arXiv:2603.14517v1.
- *Can LLMs Perceive Time? An Empirical Investigation.* (2026). arXiv:2604.00010.
- *Entropy and Attention Dynamics in Small Language Models: A Trace-Level Structural Analysis on the TruthfulQA Benchmark.* (2026). arXiv:2604.03589.
- *IAPO: Information-Aware Policy Optimization for Token-Efficient Reasoning.* (2026). arXiv:2602.19049.
- Exocortex wiki: *AI Agent Architecture & Local Inference* (STABLE, last deepened 2026-05-20).
- Mem0 (2026). *State of AI Agent Memory 2026: Benchmarks, Architectures.* (Web article, surfaced during search phase).
