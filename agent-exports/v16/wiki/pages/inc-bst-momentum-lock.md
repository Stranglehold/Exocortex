# Incident: BST Momentum Lock — False Signal Classification Cascade
## Status: ACTIVE MONITORING → PATTERN IDENTIFIED
## Domain: Belief State Tracking, Compound Classification
## Date Created: 2026-05-08 (Workshop Cycle #3)
## Severity: MEDIUM — enrichment overhead amplification during normal turns
---
## Description
The BST compound classification layer sometimes locks onto a domain signal that doesn't persist across turns. Once classified, the momentum counter increments even when subsequent turns don't reinforce the signal. This causes enrichment passes to run on irrelevant domains for 2-3 extra turns.

Current behavior:
1. Turn N: User sends message containing "investigate" → BST classifies as investigation domain (confidence=2)
2. Turn N+1: Conversation shifts to coding/debugging but momentum_turns still > 0 from previous classification
3. Enrichment passes run for investigation domain even though current turn is unrelated
4. Working memory extracts investigation-relevant entities that don't apply → noise in WM state
5. Supervisor checks for investigation anomalies on non-investigation turns → wasted cycles
---
## Root Cause Analysis
| Factor | Weight | Detail |
|--------|--------|--------|
| Momentum counter doesn't decay fast enough | PRIMARY | momentum_turns decrements by 1 per turn but classification confidence isn't re-evaluated for persistence |
| Domain priority system lacks cross-turn validation | CONTRIBUTING | High-priority domains (investigation, coding) get momentum bonus even on tangential mentions |
| No pre-enrichment domain relevance check | SYSTEMIC | Enrichment runs based on BST state alone, not current turn content |
---
## Impact Metrics
- **Wasted enrichment passes**: ~15% of turns run enrichment for wrong domain (estimated from journal patterns)
- **Per-turn overhead during lock**: +800-1200ms from irrelevant extension hooks
- **Working memory pollution**: 3-4 false entities added per locked turn, decayed after wm_decay_turns=8 cycles
---
## Mitigation Strategies Proposed
1. **Pre-enrichment relevance check**: Before running domain-specific enrichment, verify current turn content matches classified domain (regex scan of user message)
2. **Faster momentum decay**: Reduce momentum half-life from 3 turns to 2 turns for high-confidence classifications
3. **Cross-turn confidence re-evaluation**: If secondary classification differs from primary by >1 confidence level on consecutive turns, force declassification
---
## Related Pages
- [[dec-disable-bugfix-enrichment]] — bugfix turn enrichment skip (complementary optimization)
- [[dec-conditional-injection]] — broader signal-based skip strategy
- [[bst-compound-classification]] — the classification system that drives this behavior
