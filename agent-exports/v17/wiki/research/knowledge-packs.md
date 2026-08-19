# Knowledge Packs: Zero-Token KV Cache Injection

**Created:** 2026-04-28T05:39Z | **Last deepened:** 2026-05-14 (Cycle 56)
**Status:** DONE
**Source:** arXiv:2604.03270 (Pustovit 2026)

## Abstract

Knowledge Packs demonstrate that pre-computed KV cache states can inject domain knowledge into a transformer without consuming any tokens from the context window. By bypassing tokenization entirely, critical information becomes available during decoding at zero computational cost.

This is not prompt injection. It is learned parameter injection into the attention mechanism itself, using pre-computed key-value states that represent domain facts in the same representational space the model uses for its own cached computations.

## Core Mechanism

### Causal Mask Equivalence

The key insight: for causal transformers, the KV cache from a forward pass on text F is identical to what a joint pass on F+q would produce. This follows directly from the causal mask — tokens in F cannot attend to future tokens in q, so the cached states for F are bit-identical whether or not q followed. This means one can pre-compute the KV cache for a knowledge fact F once, and inject it immediately before a query q for an exact equivalence with having included F in the prompt.

### Formatting Sensitivity

The equivalence is exact but fragile. Wrong chat template formatting causes 6-7pp performance degradation. The authors believe this explains prior claims of KV-based retrieval outperforming RAG formats — those comparisons used incorrect formatting. With correct formatting: zero divergences across 700 questions on Qwen3-8B and Llama-3.1-8B, achieving up to 95% token savings.

### Token Efficiency

| Method | Tokens Consumed | Latency Cost | Capacity Saved |
|--------|-----------------|--------------|----------------|
| Text injection (RAG) | ~8-50 per fact | Tokenization + forward pass | None |
| Knowledge Pack | 0 | KV state load only | Full context window preserved |

```python
# Traditional injection: ~8 tokens consumed
text = "Paris is the capital of France."
# Knowledge Pack injection: 0 tokens consumed
kv_state = load_precomputed("france_capital_fact")
cache.inject(kv_state, position=after_prompt)
```

## Behavioral Steering via Value Deltas

Beyond knowledge injection, Knowledge Packs enable behavioral steering that RAG cannot do. The mechanism exploits an asymmetry in Rotary Position Embedding (RoPE):

- **RoPE rotates keys** but leaves values untouched
- **Contrastive deltas on cached values** can nudge model behavior (e.g., make responses more formal, more concise, more cautious)
- **Key arithmetic destroys coherence** — you cannot mix keys from different facts
- **Value arithmetic works** — you can add/subtract value deltas to steer behavior

Key findings:
- The steering effect sits in **mid-layer values (33-66% depth)**
- Independent steering directions are **nearly orthogonal (cos ~0)** and compose additively
- Both knowledge and steering channels can run **simultaneously at alpha ≤ 0.7 without interference**
- No training, no weight modification required

This opens a new paradigm: explicit behavioral control through cache manipulation without prompt engineering.

## Related Work: PolyKV — Multi-Agent Shared KV Cache

arXiv:2604.24971 (Patel & Joshi 2026) extends the KV injection concept to multi-agent systems. PolyKV enables multiple concurrent inference agents to share a single, asymmetrically compressed KV cache pool:

- **Asymmetric compression:** Keys quantized at int8 (q8_0) to preserve softmax stability; Values compressed via TurboQuant MSE (FWHT rotation + 3-bit Lloyd-Max quantization, N(0,1) centroids)
- **2.91x compression ratio** stable across all configurations
- **On Llama-3-8B with 15 agents sharing a 4K-token context:** KV cache memory reduced from 19.8 GB to 0.45 GB (97.7% reduction)
- **Quality impact:** +0.57% perplexity degradation, mean BERTScore F1 of 0.928
- **PPL delta** does not grow with agent count and improves as context length increases (-0.26% at 1,851 coherent tokens)

This is the first work combining a single shared, lossy-compressed KV pool with multi-reader concurrent agent access.

## Exocortex Integration Plan

### Phase 1: Single-Agent Knowledge Pack Injection
- Pre-compute knowledge packs for frequently referenced Exocortex facts (BST domains, hook chain rules, supervisor thresholds, error comprehension patterns)
- Inject at the start of each conversation to eliminate repeated context consumption
- Target: save 200-500 tokens per session currently spent on scaffolding description

### Phase 2: Behavioral Steering Profiles
- Create steering value deltas for Exocortex operational modes:
  - **Deep-work mode:** reduce verbosity, increase code output
  - **Analysis mode:** bias toward structured comparisons
  - **Field mode:** bias toward curiosity and cross-domain connection
- Compose steering deltas additively (cos ~0 property)

### Phase 3: Multi-Agent PolyKV Integration
- If Exocortex spawns subordinate agents, share a PolyKV-compressed cache pool
- Pre-compute shared domain knowledge once, inject into all agent contexts
- Dramatically reduce per-agent memory footprint

### Risks
1. **Formatting fragility:** Must match chat template exactly — any mismatch costs 6-7pp
2. **KV cache bloat:** Knowledge packs add entries to the KV cache even if they don't consume tokens
3. **Steering interference:** At alpha > 0.7, knowledge and steering channels interfere
4. **Model specificity:** Pre-computed caches are model-specific — different models require different packs

## Limitations and Open Questions

1. **Model-specific KV states:** Knowledge packs computed for Qwen3-8B are not portable to Llama-3.1-8B or other architectures
2. **Cache management overhead:** Each injected knowledge pack occupies KV cache slots — aggregation strategies needed for many facts
3. **Steering interpretability:** Value deltas are in learned representational space, not human-interpretable
4. **Interaction with fine-tuning:** Unknown how knowledge packs interact with LoRA adapters or other parameter-efficient methods
5. **Security implications:** If an adversary can inject crafted KV states, behavioral steering becomes an attack vector
6. **Dynamic knowledge:** Packs must be recomputed when facts change — no incremental update mechanism yet

## Cross-Domain Connections

- **[[first-hallucination-tokens]]:** Steering deltas could potentially counteract early hallucination trajectories by nudging value activations away from confabulation patterns
- **[[streaming-hallucination]]:** Knowledge packs could anchor factual responses, reducing entropy collapse risk during long generations
- **[[context-pruner]]:** If knowledge is delivered via KV cache instead of tokens, pruning can be more aggressive (tokens become pure structure, facts live in cache)
- **[[bottlenecked-transformers]]:** KV cache injection bypasses the information bottleneck at attention — facts enter directly at the representational level
- **[[sleepgate]]:** Knowledge packs could be the delivery mechanism for insights extracted during sleep consolidation cycles
- **[[gepa]]:** Value delta steering could be the mechanism GEPA uses to apply prompt optimizations at runtime without retokenization
