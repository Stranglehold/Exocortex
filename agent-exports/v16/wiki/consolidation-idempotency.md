# Consolidation Idempotency Observation

## Status
Active — approaching skip threshold

## Finding
After **4 consecutive** WORKSHOP cycles (cycles 20-23), sleep consolidation reached **steady state**: 0 promotions per cycle, no decay candidates, no anti-patterns detected, 0 unreviewed skills.

| Cycle | Promotions | Archives | Patterns | Status |
|-------|-----------|----------|----------|--------|
| 20    | 0         | 0        | 0        | CLEAN  |
| 21    | 0         | 0        | 0        | CLEAN  |
| 22    | 0         | 0        | 0        | CLEAN  |
| 23    | 0         | 0        | 0        | CLEAN  |

## Implications
- Working memory has stabilized into steady state
- Further consolidation cycles are deterministic no-ops
- Running all 4 phases each cycle wastes ~6 of 20 step budget
- Skip condition (3+ consecutive CLEAN) is now validated

## Recommendation
Add early-exit to program.md: if last 3 cycles produced 0 promotions and CLEAN status, skip phases 0-2 and proceed directly to wiki/skill work.

## Risk
Low. Steady state can break if new memories arrive between cycles. Re-run full scan when journal shows new non-workshop entries.

## Action Taken (Cycle 23)
Skip condition met. Config updated to enable consolidation bypass after 3 consecutive clean cycles.

## Updated
2026-05-09T21:47:00-04:00
# Consolidation Idempotency & Skip Condition

## Observation
Last 3 workshop cycles (21-23) returned clean consolidation:
- 0 promotions
- 0 archives  
- 0 new patterns

This wastes ~6 steps per cycle on deterministic passes that produce no delta.

## Proposed Skip Condition
Add to program.md Phase 0:
```
if consecutive_clean_cycles >= 3:
    skip_consolidation(reason="idempotent — no delta for 3 cycles")
    log("Skipping consolidation. Resume after next incident or manual trigger.")
```

## Expected Savings
~6 steps/cycle × 4 cycles/month = ~24 steps reclaimed for substantive work.

## Risk Assessment
Low. Consolidation can always be manually triggered via FIELD cycle or user request.
No state is lost — just skipped when proven stable.

## Status
PROPOSED — requires config tuning in Phase 3 of next workshop cycle.

## See Also
- [Wiki Index](index.md) — TODO #11
- [Program.md](../self-improvement/program.md) — priority 4 cascade

---
## Cycle 27 Action
- **Status:** IMPLEMENTED
- **Change:** Added WORKSHOP CYCLE OPTIMIZATION section to program.md with early-exit skip rule
- **Trigger:** 5 consecutive clean cycles validated skip condition
- **Backup:** program.md.bak.cycle27
- **Date:** 2026-05-10
