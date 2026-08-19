# BST Classifier

**Created:** 2026-04-28T04:39Z
**Status:** Core Exocortex component documentation
**Implementation**: `_11_belief_state_tracker.py` (1702 LOC)

## Overview

The Belief State Tracker (BST) is the primary domain classification engine in Exocortex. It runs before every LLM call via the `before_main_llm_call` hook, analyzing conversation history to determine task domain and complexity without requiring the LLM to self-classify.

## Classification Mechanism

### Phrase Signal Matching

Instead of asking "what kind of task is this?" (probabilistic), BST uses compiled regex phrase signals mapped to 16 domains:
- **Complexity-eligible** (8): `coding`, `system_admin`, `planning`, `investigation`, `analysis`, `bugfix`, `git_ops`, `file_ops`
- **Specialized** (5): `testing`, `config_edit`, `prompt_engineering`, `financial` 
- **Register-shift override** (3): `orientation`, `meta_cognitive`, `philosophical` — these take absolute priority when detected, suppressing all other domains
- **Fallback** (2): `conversation` (priority 99), and implicit unknown

Each domain has explicit signal patterns. Matches update domain confidence scores incrementally.

### Domain Priority System (Tiebreaker)

When multiple domains fire equally, `DOMAIN_PRIORITY` dict resolves conflicts. Lower number wins:
| Domain | Priority |
|--------|----------|
| orientation/meta_cognitive/philosophical | 0 (register-shift override) |
| bugfix | 1 |
| coding/testing | 2-3 |
| analysis | 4 |
| system_admin | 5 |
| investigation | 11 (fallback — wins only when nothing specific fires) |
| conversation | 99 (ultimate fallback) |

### Momentum Tracking

Classification stability tracked across consecutive turns via `momentum_turns`. When a single domain holds for N≥3 turns (`MOMENTUM_THRESHOLD=3`), the system considers the conversation "locked" to that domain. This triggers:
- Transition from full injection → conditional enrichment mode (line 687)
- Reduced context overhead in subsequent turns
- Domain-matched tool filtering (only relevant tools described)

### Register-Shift Override (v3.3+)

Lines 531, 663: When register-shift signals fire (`orientation`, `meta_cognitive`, `philosophical`), they immediately supersede all other domain classifications regardless of momentum strength. This prevents the system from treating reflective/meta-cognitive turns as technical tasks requiring tool injection.

### Anti-Signals

Certain phrases explicitly prevent classification into specific domains regardless of other signals. Example: `\b(?:don't|never|no\s+need)\b.{0,20}\bcoding\b` prevents coding classification even when code-related terms appear.

### Compound Detection

When multiple complexity-eligible domains show high confidence simultaneously, BST creates a compound signature (e.g., `coding+planning`). This enables:
- Dual-domain enrichment without oscillation between classifications
- Wider tool filtering covering both domains
- Appropriate complexity escalation for multi-faceted tasks

## Operational Metrics

| Metric | Value |
|--------|-------|
| LOC | 1702 (largest single extension) |
| Hook position | `before_main_llm_call` — runs every turn |
| Domain coverage | 16 explicit domains with priority resolution |
| Momentum threshold | 3 turns before lock |

## Connection to Other Concepts

- **[[deterministic-scaffolding]]** — BST replaces probabilistic self-classification with regex-matched signals
- **[[temporal-proprioception]]** — momentum tracking provides turn-aware stability detection LLMs cannot self-compute
- **[[injection-gate]]** — classification output drives three-phase context management transitions
- **[[supervisor-loop]]** — BST domain confidence feeds supervisor threshold decisions

## References

- Implementation: `/a0/usr/Exocortex/extensions/before_main_llm_call/_11_belief_state_tracker.py`
- Exocortex integration analysis: `/a0/usr/workdir/exocortex_integration_analysis.md`

## Verification Status
Last verified: 2026-05-02. Domain list and priority system traced to _11_belief_state_tracker.py lines 39-106, 81, 531, 663. Register-shift override mechanism added per v3.3 source. Latency claim removed (unverifiable).
