# SleepGate: KV Cache Proactive Interference Management

**Created:** 2026-04-28T05:39Z
**Status**: Research paper summary — arXiv:2603.14517
**Category**: Memory interference in LLMs.

## Abstract Summary (arXiv:2603.14517)

SleepGate investigates how pre-processed stale information (proactive interference) degrades retrieval accuracy in transformer KV caches more severely than conflicting new information (retroactive interference). All tested LLMs show inverted PI>RI pattern — opposite to human memory.

## Key Findings

### Proactive Interference Dominance

- Cohen's d = 1.73 favoring proactive interference across all models tested
- Retrieval accuracy degrades log-linearly with number of prior conflicting entries even when current information is correct
- Reasoning models optimize consolidation at expense of recency access — the opposite of what agent systems need for real-time adaptation

### Empirical Comparison to Human Memory

| Species | PI vs RI Pattern |
|---------|------------------|
| Humans | Retroactive > Proactive (newer information overwrites) |
| LLMs | Proactive > Retroactive by 1.73 SD — prior entries block current retrieval |

## System Design Implications for Exocortex

### KV Cache Pruning Priority

SleepGate confirms that proactive interference is the core problem both KV cache and DeltaNet share. Stale pre-processed information actively competes with current values degrading accuracy.

1. **Aggressive stale entry eviction** — prioritize removing old conflicting entries from KV cache over preserving comprehensive history
2. **DeltaNet alignment** — delta-update approach manages PI by controlling what new information enters the cache; SleepGate provides theoretical justification for this design choice
3. **Domain-transition flushes** — when BST detects domain shift, full KV cache flush may be more effective than gradual decay because old domain entries cause proactive interference in new context

## Connection to Other Concepts

- **[[proactive-interference]]** — SleepGate provides the empirical evidence for this core concept
- **[[context-pruner]]** — pruning strategy justified by PI dominance: removing stale entries matters more than controlling new entry volume
- **[[bst-classifier]]** — domain shift detection triggers proactive cache flush rather than gradual decay

## References

- Adeseye et al. (2026). *SleepGate: Proactive Interference in Transformer KV Caches*. arXiv:2603.14517 [cs.AI]
