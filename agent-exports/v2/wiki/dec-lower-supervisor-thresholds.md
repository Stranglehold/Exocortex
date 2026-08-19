# DEC: Lower Supervisor Thresholds for Earlier Intervention

## Status
PROPOSED — awaiting empirical validation from 10+ supervised sessions

## Current Configuration
| Parameter | Current Value | Location |
|---|---|---|
| supervisor_stall_threshold | 3 | default_config.yaml |
| supervisor_loop_threshold | 3 | default_config.yaml |
| supervisor_cascade_threshold | 5 | default_config.yaml |
| supervisor_context_threshold | 85% | default_config.yaml |
| MIN_UNIQUE_FAILURE_TYPES | 3 | _50_supervisor_loop.py |
| PHASE4_MIN_FAILURES_TRIGGER | 2 | _50_supervisor_loop.py |

## Proposal
- Lower stall_threshold from 3→2 (catch stalls one turn earlier)
- Lower loop_threshold from 3→2 (catch loops one iteration earlier)
- Keep cascade_threshold at 5 (multi-tool failures are rare, lowering risks false positives)

## Empirical Evidence (Workshop Cycles 20-23)
- Supervisor interventions logged: 0 across 4 consecutive cycles
- Stack status shows loop_tier=none at turn 14 in cycle 23
- Journal grep for supervisor/stall/loop_detect/cascade: 0 matches
- Consolidation phases 0-3: clean (0 promotions, 0 archives) across 3 cycles

## Rationale
- Supervisor is idle most of the time — thresholds may be too conservative
- Early intervention costs less than prolonged stalling (fewer wasted LLM turns)
- Phase 4 already discriminates iteration from looping via MIN_UNIQUE_FAILURE_TYPES=3

## Risks
- False positives: legitimate multi-step exploration may trigger unnecessary interventions
- Domain-aware thresholds already exist — lowering may break domain-specific tuning
- Proactive supervisor (_12_proactive_supervisor.py) may duplicate intervention signals

## Implementation Notes
- Modification point: default_config.yaml supervisor_* entries
- Must test against known failure patterns (RESEARCH_AFTER_CONFIRMATION, STRATEGY_REPETITION, MACRO_CYCLE, SELF_DIAGNOSIS_WITHOUT_CHANGE)
- Loop alternatives map in _50_supervisor_loop.py already provides orthogonal suggestions

## Next Steps
- Run 10 supervised sessions with lowered thresholds
- Measure: intervention frequency, false positive rate, turns saved per caught stall
- A/B test against current thresholds
