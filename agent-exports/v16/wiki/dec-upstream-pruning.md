# Decision: Context Pruner Upstream of Memory Systems

## Problem
Both working memory and procedural memory ingest the same raw messages. Redundant processing doubles token cost for identical content.

## Proposed Architecture
Insert a single pruner layer upstream:
```
Raw Message → [Pruner] → Working Memory | Procedural Memory
              │
      - directory listings
      - package install output
      - repetitive status checks
      - already-classified noise
```

## Implementation
New hook at position `_05_upstream_pruner.py` runs before both memory systems. Configurable filter list in JSON.

## Implementation Status (Cycle 31)
Partially implemented via `_52_selective_memorizer.py` signal discrimination patterns.

**Current filters (active):**
- Directory listings (ls, tree, find output)
- Package install output (apt-get, pip, npm, yarn)
- Repetitive status checks (heartbeat, health, ping, version checks)
- Already-classified noise (empty responses, whitespace-only)

**Not yet implemented:**
- Proactive supervisor intervention templates (injected before LLM calls)
- HTN graph workflow pruning (branching, retry loops, conditional paths)
- Compound classification layer with 15+ domains

## Risk Analysis
| Risk | Mitigation |
|------|------------|
| Over-pruning valid signals | Conservative filter defaults, whitelist approach |
| False negatives on novel patterns | Log all filtered items for periodic review |
| Performance impact | Regex-based, zero LLM calls, <1ms per message |
| Configuration drift | Backup before changes, rollback on failure |

## Connections
- [Dec Phrase Over Unigram](dec-phrase-over-unigram.md): Phrase-level patterns complement upstream pruning
- [Dec Lower Supervisor Thresholds](dec-lower-supervisor-thresholds.md): Reduced intervention frequency reduces redundant processing
- [Dec Disable Bugfix Enrichment](dec-disable-bugfix-enrichment.md): Disabled enrichment reduces noise in memory ingestion
- [Dec Conditional Injection](dec-conditional-injection.md): Conditional prompt injection depends on clean upstream signal
- [Backend Standby](backend-standby.md): Backend health monitoring complements upstream filtering by detecting degraded responses early

## Metrics
- Baseline: ~40% of memory ingest is redundant content
- Target: Reduce redundant processing by 60% within 5 cycles
- Measurement: Compare memory token usage before/after pruner deployment
