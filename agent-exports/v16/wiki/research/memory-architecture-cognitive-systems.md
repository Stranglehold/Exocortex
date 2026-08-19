# Memory Architecture in Cognitive & AI Systems

**Status:** STABLE
**Created:** 2026-05-20
**Last Deepened:** 2026-05-20
**Primary Sources:** 8
**Cross-Domain Links:** 5

## Overview

Memory architecture in artificial cognitive systems maps three biological memory divisions — episodic (event-specific), semantic (fact-based), and procedural (skill-based) — onto LLM-based agent components. Biological complementary learning systems (McClelland et al., 1995) provide a validated architectural blueprint: the hippocampus handles rapid one-shot episodic encoding; the neocortex handles slow semantic integration. Sleep consolidation bridges the two. Modern AI systems that separate episodic storage (vector DB, RAG) from semantic storage (model weights, knowledge graphs) replicate this division implicitly. The open question is whether consolidation — the active process of transferring and integrating memories — is being implemented deliberately or left to chance.

## Episodic Memory in AI Systems

### Biological Model

Episodic memory (Endel Tulving, 1972) stores specific events with spatiotemporal context. The hippocampus enables rapid one-shot encoding without catastrophic interference to existing knowledge. This is the hippocampal-neocortical dual-system model (McClelland, Cohen & O'Reilly, 1995; Klinzing, Spaak & Gais, 2019, Nature Reviews Neuroscience).

### AI Implementation

Three architectural approaches map to episodic memory:

1. **Memory-Augmented Neural Networks (MANNs):** Differentiable Neural Computer (Graves et al., 2014), Neural Turing Machine (Graves et al., 2016) — external memory matrices with read/write heads. Conceptually foundational but largely superseded by transformer attention.
2. **Retrieval-Augmented Generation (RAG):** Vector DB episodic store + LLM semantic processor. Functionally equivalent to hippocampal-neocortical separation: vector DB = episodic buffer (rapid lookup, one-shot retrieval), model weights = semantic store (slow integration, generalization).
3. **Episodic Memory Benchmarks:** ICLR 2025 introduced the first episodic memory generation and evaluation benchmark for LLMs, establishing that current LLMs lack robust episodic memory mechanisms despite strong semantic capabilities. Human-inspired episodic memory architectures (ScienceDirect, 2025) show computational benefits: one-shot memorization without catastrophic interference while avoiding long-context computational costs.

**Key metric:** Separate episodic systems enable one-shot memorization without interfering with semantic weights. This is the computational advantage that biological systems exploit and that RAG-based agents approximate.

## Catastrophic Forgetting & Interference

Catastrophic forgetting (McCloskey & Cohen, 1989) remains the dominant failure mode in continual learning. Three primary mechanisms identified in transformer LLMs (arXiv 2601.18699, "Mechanistic Analysis of Catastrophic Forgetting in LLMs"):

1. **Gradient interference in attention weights** — new task gradients overwrite attention patterns learned from prior tasks
2. **Representational drift in intermediate layers** — hidden layer representations shift as new data arrives, destabilizing downstream task heads
3. **Loss landscape flattening** — optimization erodes decision boundaries for previously learned tasks

Mitigation strategies (taxonomized in 2025 survey):

| Strategy | Mechanism | Tradeoff |
|----------|-----------|----------|
| EWC (Kirkpatrick et al., 2017) | Fisher information penalty on important weights | Computationally expensive Fisher calculation |
| Synaptic Intelligence (Zenke et al., 2017) | Online importance estimation per parameter | Approximate, not exact |
| RiemannianWalk (Masana et al., 2020) | Riemannian geometry on parameter space | Complex implementation |
| Learning without Forgetting (Li & Hoiem, 2017) | Distillation loss on previous task outputs | Requires replay buffer |
| MemRL Utility Scoring (Zhang et al., 2026) | Score memories by actual retrieval utility, not semantic similarity | Requires tracking infrastructure |

**Nature Communications 2025** (Bayesian continual learning) showed that biological synapses balance retention and flexibility through Bayesian inference. Artificial networks still struggle at both extremes — catastrophic forgetting and catastrophic remembering (rigid weights that cannot adapt).

## Working Memory Capacity

Human working memory: Cowan (2001) established 4±1 chunks as the capacity limit. Engemann et al. (2023) refined this with neural decoding methods.

LLM context windows: Maximum context window (MCW) ≠ effective context window. arXiv 2509.21361 ("Context Is What You Need: The Maximum Effective Context Window") empirically demonstrates that while models cite 128K, 1M, or 10M token architectures, practical retention degrades well before architectural limits. The transformer's ability to represent and communicate information within the window saturates long before token limits are reached.

**Cross-reference:** Adaptive supervisor architecture's trajectory abstraction layer (~300-500 token compressed context) is functionally a working memory buffer — compressed representations that fit within effective capacity while preserving task-critical information. This is the engineering equivalent of cognitive chunking.

## Procedural Memory

Procedural memory stores skills and habits implicitly. In AI systems, this maps to:

1. **Model weights** — learned patterns that generalize across tasks without explicit retrieval
2. **Fine-tuned adapters** (LoRA, QLoRA) — task-specific procedural modifications without full weight updates
3. **Reinforcement learning policies** — learned behaviors that emerge from reward signals, not explicit rules

Our procedural memory system (anti-pattern entries, loop cascade breakers) is a deliberate implementation: specific session errors compress into reusable procedural rules. The anti-pattern "before any SELECT, run schema inspection" is a procedural memory derived from episodic failures.

## Consolidation Mechanisms

Sleep consolidation in biology: during slow-wave sleep, hippocampal replays transfer episodic memories to neocortical semantic stores (Marlin & McClelland, 2012; Schmidt et al., 2021). This is not passive decay — it is active reorganization.

**Our implementation:** The sleep consolidation engine (sleep_consolidation.py) runs three phases:
- Phase 1: Deduplication (merge near-duplicate memories, discard noise)
- Phase 2: Anti-pattern detection (extract failure-recovery pairs into procedural rules)
- Phase 3: Promotion (surface high-utility memories into active recall)

Theoretical basis: Kolb's experiential learning cycle (experience → reflection → conceptualization → experimentation), Argyris & Schön double-loop learning (question governing assumptions, not just fix symptoms), Complementary Learning Systems (hippocampal → neocortical transfer during consolidation).

**MemRL utility scoring** (Zhang et al., 2026) adds a critical dimension: memories are scored by actual retrieval utility, not semantic similarity. An anti-pattern that successfully prevented a loop gets higher utility. One that was retrieved but didn't help gets downweighted. This approximates Q-value learning without full RL infrastructure.

## Interaction Modeling as Memory

Novel contribution: interaction patterns between agent and operator are learnable memory. Operator message length, correction frequency, and delegation patterns encode information about operator preferences and expectations. The interaction model is stored as an editable operator profile document — transparent, observable, correctable.

This extends sleep consolidation from self-improvement to collaborative calibration. The agent doesn't just wake up better at tasks — it wakes up better at working with its operator.

## Primary Sources (Verified)

1. McClelland, J. L., Cohen & O'Reilly (1995) — Complementary Learning Systems theory
2. Klinzing, J. G., Spaak & Gais (2019) — Sleep dependence of memory systems, Nature Reviews Neuroscience
3. McCloskey & Cohen (1989) — Catastrophic interference in connectionist networks
4. Kirkpatrick et al. (2017) — Overcoming catastrophic forgetting with EWC
5. Zhang et al. (2026) — MemRL: Memory with utility scoring
6. arXiv 2601.18699 — Mechanistic Analysis of Catastrophic Forgetting in LLMs
7. ICLR 2025 — Episodic Memory Generation and Evaluation Benchmark for LLMs
8. arXiv 2509.21361 — Maximum Effective Context Window for Real-World LLM Applications

## Cross-Domain Links

- [adaptive-supervisor-architecture](adaptive-supervisor-architecture.md) — trajectory abstraction layer as working memory buffer; dual-process theory basis
- [autonomous-self-improving-agents](autonomous-self-improving-agents.md) — GEPA-style prompt evolution as procedural memory update
- [multi-agent-coordination-economies](multi-agent-coordination-economies.md) — shared memory across agent coordination
- [mechanistic-interpretability-grokking](mechanistic-interpretability-grokking.md) — internal knowledge representation in transformer weights
- [ai-native-database-search-infrastructure](ai-native-database-search-infrastructure.md) — vector DB as episodic memory backend

## Key Insights

1. **Separation is the architecture.** Episodic (vector DB/RAG) and semantic (weights/KG) separation mirrors biological complementary learning systems. Consolidation is the missing link — the active transfer mechanism between stores.
2. **Catastrophic forgetting has three mechanisms.** Gradient interference, representational drift, and loss landscape flattening. Mitigation requires addressing all three, not just one.
3. **Effective context ≠ maximum context.** Working memory capacity saturates well before architectural limits. Compressed representations (trajectory abstraction) are more effective than raw context expansion.
4. **Utility scoring > semantic similarity.** MemRL's key insight: memories should be valued by demonstrated utility, not similarity. This is learnable with simple counters, not full RL infrastructure.
5. **Interaction is data.** Operator patterns are learnable and actionable. Interaction modeling as part of the consolidation loop is an open research problem with no known reference implementation.
