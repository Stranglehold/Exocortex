# Decision: Phrase Context Over Unigram for BST v3.8

## Problem
BST domain classifier uses single-token regex signals (e.g., `\binvestigat\b`) which fire on coincidental mentions, not intent. "Investigate this font" triggers investigation domain incorrectly.

## Current State (Cycle 26 Audit)
**Compound classification layer IS implemented:** BST v3.8 has primary/secondary domain tracking with `compound_signature`, `momentum_turns`, and tiered enrichment plans. This provides cross-turn disambiguation.

**Phrase-level regex replacement is NOT implemented:** Grep of `_11_belief_state_tracker.py` confirms zero matches for `phrase`, `context_window`, or compound regex patterns. Signals remain unigram-level.

## Proposed Change
Replace unigram signals with phrase-level context windows:
```
# Before: \binvestigat\b → investigation domain
# After: (investigat.{0,20}(project|case|target|subject|intelligence)) → investigation
```

## Risk Assessment
- **Precision risk:** Phrase patterns may miss valid domain signals when user uses shorthand
- **Maintenance cost:** Each domain needs 2-3 phrase patterns; 15 domains × 3 = 45+ regexes to maintain
- **Recommended approach:** Implement phrase patterns only for top-5 highest-cardinality domains first, measure precision gain, then expand

## Test Plan (Unexecuted)
- Run 50 historical turns through new classifier vs old
- Measure precision/recall shift for each of 15+ domains
- Accept threshold: precision +5%, recall -3% or better

## Status
**DEFERRED** — compound layer provides partial mitigation; phrase-level upgrade needs dedicated implementation sprint

## See Also
- [Dec Lower Supervisor Thresholds](dec-lower-supervisor-thresholds.md)
- [Dec Disable Bugfix Enrichment](dec-disable-bugfix-enrichment.md)
- [Dec Conditional Injection](dec-conditional-injection.md)
- [Dec Upstream Pruning](dec-upstream-pruning.md)
- [Index](index.md)

---

## Cycle 30 Deepening (2026-05-14)

### Current Signal Quality Audit

**Phrase-level patterns already implemented (confirmed in _11_belief_state_tracker.py):**
- `\bopen[- ]source\s+intel` — compound phrase ✓
- `\bmilitary\b.{0,30}\b(?:action|movement|force|operation|threat)\b` — contextual window ✓
- `\bintelligence\s+(?:briefing|assessment|report|analysis)\b` — compound phrase ✓
- `\bwho\s+(?:is|are|owns?|controls?|runs?)\b` — compound phrase ✓
- `\b(?:apt|pip|npm|cargo)\s+install\b` — compound phrase for system_admin ✓

**Unigram signals remaining (confirmed false-positive risk from code review):**
1. `\binvestigat\b` — fires on "investigate this font", "investigation committee"
2. `\bnetwork\b` — fires on "social network", "neural network"
3. `\bpermission\b` — fires on "ask permission" not just "permission denied"
4. `\bfix\b` — fires on "fix dinner" not just "fix bug"

### Compound Layer Mitigation (Confirmed from code)

**What it DOES provide:**
1. **Priority ordering**: DOMAIN_PRIORITY dict — investigation at 11 (fallback), bugfix at 1 (highest)
2. **Score-all**: scores all domains, not first-match-wins
3. **Momentum tracking**: CONFIDENCE_DECAY_AFTER_TURNS=3 — halves confidence after 3 non-reinforcing turns
4. **Primary/secondary tracking**: compound_signature + momentum_turns fields

**What it DOES NOT provide:**
- No elimination of false positive triggers — they still score +1 per turn
- No phrase-level context window for unigram signals
- Enrichment injection still occurs for up to 3 turns before decay

### Concrete Phrase Pattern Spec (Top-4 Highest-Risk Signals)

Proposed replacements:

| Domain | Current Signal | Proposed Phrase Pattern | Rationale |
|--------|---------------|------------------------|-----------------------|
| investigation | `\binvestigat\b` | `\binvestigat(?:e|ing|ion)?\s+(?:project|case|target|subject|intelligence)\b` | Eliminates "investigate this font" |
| system_admin | `\bnetwork\b` | `\b(?:network\s+(?:interface|config|firewall)|ping\|traceroute\|nslookup)\b` | Eliminates "neural network", "social network" |
| system_admin | `\bpermission\b` | `\b(?:permission\s+(?:denied|error|issue)|chmod\|chown)\b` | Eliminates "ask permission" |
| bugfix | `\bfix\b` | `\bfix(?:ed|ing)?\s+(?:bug|issue|error|problem|crash)\b` | Eliminates "fix dinner" |

### Implementation Notes

- **Total signal changes**: 4 unigram → 4 phrase patterns
- **Risk**: Phrase patterns may miss valid signals when user uses shorthand (e.g., "fix it" for a known bug)
- **Recommended approach**: Implement phrase patterns for investigation domain only, measure precision gain over 5 cycles, then expand

### Test Plan

1. **Offline test**: Run 50-turn sample through both classifiers, measure precision/recall per domain
2. **Live test**: Deploy phrase patterns for investigation domain only, monitor for 5 cycles
3. **Accept criteria**: precision improvement without recall loss >5%
4. **Rollback trigger**: precision <5% gain OR recall loss >5%

**Cycle 30 note**: Deepened with concrete signal audit from actual code. Phrase patterns confirmed partial implementation. Ready for implementation when sprint capacity available. No action required this cycle.

