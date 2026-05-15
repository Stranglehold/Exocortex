# BST Classifier

**Created:** 2026-04-28T04:39Z
**Status:** Core Exocortex component documentation
**Implementation**: `_11_belief_state_tracker.py` (1702 LOC)

## Overview

The Belief State Tracker (BST) is the primary domain classification engine in Exocortex. It runs before every LLM call via the `before_main_llm_call` hook, analyzing conversation history to determine task domain and complexity without requiring the LLM to self-classify.

## Classification Mechanism

### Phrase Signal Matching

Instead of asking "what kind of task is this?" (probabilistic), BST uses compiled regex phrase signals mapped to 10 domains:
- `coding`, `planning`, `investigating`, `writing`, `researching`, `debugging`, `administering`, `learning`, `socializing`, `unknown`

Each domain has explicit signal patterns (e.g., coding: `\bwrite\b.{0,30}\b(?:function|class|script)\b`). Matches update domain confidence scores incrementally.

### Momentum Tracking

Classification stability tracked across consecutive turns via `momentum_turns`. When a single domain holds for N consecutive turns (threshold configurable), the system considers the conversation "locked" to that domain. This triggers:
- Transition from full injection → conditional enrichment mode
- Reduced context overhead in subsequent turns
- Domain-matched tool filtering (only relevant tools described)

### Anti-Signals

Certain phrases explicitly prevent classification into specific domains regardless of other signals. Example: `\b(?:don't|never|no\s+need)\b.{0,20}\bcoding\b` prevents coding classification even when code-related terms appear.

### Compound Detection

When multiple domains show high confidence simultaneously, BST creates a compound signature (e.g., `coding+planning`). This enables:
- Dual-domain enrichment without oscillation between classifications
- Wider tool filtering covering both domains
- Appropriate complexity escalation for multi-faceted tasks

## Operational Metrics

| Metric | Value |
|--------|-------|
| LOC | 1702 (largest single extension) |
| Hook position | `before_main_llm_call` — runs every turn |
| Latency overhead | ~8ms per classification cycle |
| Domain coverage | 10 explicit domains + unknown fallback |

## Connection to Other Concepts

- **[[deterministic-scaffolding]]** — BST replaces probabilistic self-classification with regex-matched signals
- **[[temporal-proprioception]]** — momentum tracking provides turn-aware stability detection LLMs cannot self-compute
- **[[injection-gate]]** — classification output drives three-phase context management transitions
- **[[supervisor-loop]]** — BST domain confidence feeds supervisor threshold decisions

## References

- Implementation: `/a0/usr/Exocortex/extensions/before_main_llm_call/_11_belief_state_tracker.py`
- Exocortex integration analysis: `/a0/usr/workdir/exocortex_integration_analysis.md`
