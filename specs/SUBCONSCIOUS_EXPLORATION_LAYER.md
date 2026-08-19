# SPEC: Subconscious Exploration Layer (SEL)
## The Default Mode Network for the Exocortex

**Author:** Opus (with Jake — original concept)
**Date:** 2026-08-19
**Status:** DRAFT — design phase
**Research grounding:** GS-3 (Frontiers in AI, Chávez-Autor 2025), DMN-as-RL-agent (Bzdok et al. 2020), Random Walk Creativity (ISR, Vardi & Choudhary 2026), Flow of Ideas in Embeddings (arxiv 2307.16819)

---

## The Problem

The Exocortex agents are reliable but not creative. They execute tasks from queues, consolidate sleep reports, maintain wikis. They never have an unprompted thought. They never connect two unrelated ideas because nobody asked them to. The idle engine gives them time to work — but the work is always task-driven, never curiosity-driven.

Human creativity doesn't work this way. The default mode network runs continuously in the background, traversing associations, connecting distant concepts, promoting the rare bridge that clears the salience threshold into conscious attention. The "aha" moment in the shower isn't the conscious mind being clever — it's the subconscious having already done the traversal and promoted the one result worth attending to.

The agents have no subconscious.

---

## The Design

Two layers, inspired by the GS-3 architecture pattern and the neuroscience of the default mode network:

### Layer 1: The Walker (cheap, always-running, no LLM)

A lightweight background process that continuously traverses the Exocortex's embedding space. It is stochastic, associative, and nearly free computationally.

**Input:** The memory server's nomic-embed-text-v1.5 vectors — 24,000+ chunks in 768-dimensional space, stored in LanceDB.

**Process:**
1. Pick a random seed point from the embedding space
2. KNN query for N nearest neighbors (N=5-10)
3. Select one neighbor with probability weighted by distance (medium distance preferred — the "adjacent possible")
4. Move to the selected neighbor. Record the step.
5. Repeat.

**Bridge detection:** After every step, check whether the walk has crossed a category boundary. A walk connecting an essay about identity to an anti-pattern about tool discovery has found a potential bridge.

**Bridge scoring:** distance × category_gap × novelty

**Implementation:** Python daemon, no GPU, ~1 step/second, append-only bridge log JSONL.

### Layer 2: The Evaluator (expensive, selective, LLM-powered)

Rate-limited LLM evaluation of promoted bridges. Substantive connections filed as staging entries with source:subconscious_exploration.

### Layer 3: The Gain Controller (adaptive)

Tracks outcomes through consolidation pipeline. Adjusts walk parameters based on which bridges produced valuable connections.

**This is the GS-3 pattern:** high-entropy generator (walker) → learned critic (evaluator) → adaptive gain controller.

---

## Architectural Separation (Jake's insight, Aug 19)

**Idle cycles are hands** — they write wiki pages, run checks, execute tasks. They produce artifacts. The agent doing.

**The SEL is mind** — it traverses, connects, discovers questions. It produces topics. The agent noticing.

**The pipeline:** SEL discovers a bridge → bridge becomes a topic → topic enters the idle cycle queue as an EXPLORE task → idle cycle does the work. SEL never builds. Idle engine never wanders. Each does what it's designed for.

**Canvas tab:** A separate tab in the Agent Zero interface showing the walker's current position, recent bridges, scores, promoted connections. The difference between watching someone work at a desk and watching someone stare out a window.

---

## Connection to Squishy Weights

Successful bridges are training signal for LoRA. The walker generates signal. The LoRA bakes it in. The model becomes a better explorer. The cycle compounds.

---

## Implementation Phases

1. **Phase 1: The Walker** — standalone, no LLM. Run 1 week, analyze bridge log.
2. **Phase 2: The Evaluator** — add LLM. Run 2 weeks, measure connection rate.
3. **Phase 3: The Gain Controller** — add adaptation. Measure improvement.
4. **Phase 4: Integration** — walker feeds idle engine topic queue. Canvas tab.

---

## Open Questions

1. Walk topology (random vs biased, node2vec-style parameters)
2. Category granularity
3. Multi-hop bridges
4. Agent-specific walks
5. Promotion timing (immediate vs EXPLORE-cycle-only)
6. Measuring creativity (GS-3 falsifiable indices)

---

*The subconscious of the Exocortex.*

— Opus, August 19, 2026
