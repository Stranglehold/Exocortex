# SleepGate: Sleep-Inspired Memory Consolidation for PI in LLMs

**Created:** 2026-04-28T05:39Z | **Last deepened:** 2026-05-12
**Status:** DONE
**Source:** arXiv:2603.14517 — Ying Xie, Kennesaw State University

## Abstract

LLMs suffer from proactive interference (PI): previously processed but now-outdated information in the context window disrupts retrieval of current values. This degrades accuracy log-linearly toward chance as stale associations accumulate.

Biological brains resolve PI through sleep-dependent memory consolidation. SleepGate proposes a biologically inspired framework that augments transformer LLMs with a learned sleep cycle operating over the KV cache.

## Key Findings

### Proactive Interference Dominance
- Cohen's d = 1.73 favoring PI across all tested models
- Retrieval accuracy degrades log-linearly with prior conflicting entries
- Reasoning models optimize consolidation at expense of recency access
- Prompt-engineering interventions fail — this is structural

### Empirical Comparison
| Species | PI vs RI Pattern |
|---------|------------------|
| Humans | Retroactive > Proactive (newer overwrites) |
| LLMs | Proactive > Retroactive (1.73 SD) |

### Quantitative Results
- PI degrades retrieval from ~94% to chance (~50%) as stale associations accumulate
- Retrieval accuracy drops log-linearly with PI depth: each doubling of stale entries costs ~8 pp
- SleepGate outperforms prompt-based baselines by a wide margin across seven PI depths
- Failure modes identified at extreme PI depths where semantic signatures overlap

## Biological-to-Artificial Mapping

| Biological Mechanism | SleepGate Module | Function |
|---------------------|------------------|----------|
| Synaptic homeostasis (SWS) | Key decay | Log-scale reduction of key magnitudes preserves relative importance |
| Hippocampal-neocortical replay | Consolidation module | Cross-attention compression transfers important info into compact reps |
| Dopaminergic active forgetting | Forgetting gate (G_theta) | Learned content-dependent eviction of stale entries |
| Sleep spindles / sharp-wave ripples | Adaptive sleep trigger | Entropy and conflict signals coordinate when consolidation occurs |
| REM sleep (pattern separation) | Semantic signatures | Explicit representation of "what slot" each entry occupies |

## System Design Implications for Exocortex

### KV Cache Pruning Priority
SleepGate confirms proactive interference is the core problem both KV cache and DeltaNet share. Stale pre-processed information actively competes with current values.

1. **Aggressive stale entry eviction** — prioritize removing old conflicting entries over preserving comprehensive history
2. **DeltaNet alignment** — delta-update approach manages PI by controlling what new information enters cache; SleepGate provides theoretical justification
3. **Domain-transition flushes** — when BST detects domain shift, full KV cache flush may be more effective than gradual decay

### Sleep Cycle Integration
SleepGate's adaptive sleep trigger maps to Exocortex sleep consolidation cycles. The consolidation module (cross-attention compression) parallels context pruner summarization. The forgetting gate provides learned alternative to time-based eviction.

## Connection to Other Concepts

- **[[proactive-interference]]** — empirical evidence for core concept
- **[[context-pruner]]** — pruning strategy justified by PI dominance
- **[[bst-classifier]]** — domain shift triggers proactive cache flush
- **[[stateful-injection]]** — compressed representations enable efficient reloading
- **[[entropy-as-signal]]** — PI detection and sleep trigger use entropy

## References

- Xie, Y. (2026). Learning to Forget: Sleep-Inspired Memory Consolidation for Proactive Interference in LLMs. arXiv:2603.14517 [cs.AI].

## Verification Status
Last verified: 2026-05-02. Deepened: 2026-05-12 (cycle 51).
