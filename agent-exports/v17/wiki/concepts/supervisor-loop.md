# Supervisor Loop

**Created:** 2026-04-28T04:47Z
**Deepened:** 2026-05-10 (cycle 37)
**Status:** Core Exocortex component specification
**Mechanism**: Graduated intervention with domain-aware thresholds + CUSUM canary.

## Overview

The supervisor loop provides graduated, multi-level intervention that scales from soft warnings to hard circuit breakers based on accumulated drift signals rather than single-event triggers. It uses Cumulative Sum (CUSUM) statistical process control adapted for agent trajectory monitoring.

## How It Works

### CUSUM Canary Mechanism

Instead of binary "error/no error" detection, the supervisor maintains a running cumulative score:
```
supervisor_score += signal_weight * severity
if supervisor_score >= intervention_threshold → trigger graduated response
```

The key insight: transient errors are tolerated, but sustained degradation cumulatively builds toward intervention. The score decays slowly (by a configured decay factor) on clean turns, preventing spurious accumulation from one-off anomalies.

Signals feed into the accumulator:
- **Soft signals** (+1): Domain classification shift, tool call failure, high entropy detected
- **Medium signals** (+3): Error pattern repeat, confidence drop below threshold, epistemic violation (ungrounded claim)
- **Hard signals** (+5): Tool not found, JSON parse failure, safety violation, consecutive failed tool calls (≥3)

Additional signals added after Run 1 incidents:
- **Fabrication signal** (+4): when epistemic-integrity detects an unsubstantiated factual claim with no source anchor
- **Momentum stall** (+2): when BST momentum_turns exceeds 7 without yield (inc-bst-momentum-lock pattern)

### Graduated Intervention Levels

| Level | Action | Trigger Condition |
|-------|--------|------------------|
| L1 (Watch) | Log warning + increase monitoring frequency | Score 3–5 |
| L2 (Nudge) | Inject corrective prompt fragment into next turn extras | Score 6–9 |
| L3 (Compress) | Force transition to compressed injection mode + BST re-evaluation + context pruner aggressive sweep | Score 10–14 |
| L4 (Reset) | Kill current context, restart with clean slate preserving only task goal and memory anchors | Score ≥ 15 |

### Domain-Aware Thresholds

Different tasks tolerate different drift levels:
- **Coding**: Lower thresholds — syntax errors compound quickly; intervene at score 6–8. Domain weight multiplier: 1.5x
- **Researching**: Higher tolerance — exploratory search expected to bounce between domains. Domain weight multiplier: 0.7x
- **Writing**: Medium — stylistic drift less critical than factual confabulation. Domain weight multiplier: 1.0x
- **Analysis**: Moderate — entropy spikes more expected; threshold 9–11. Domain weight multiplier: 1.0x
- **Meta-cognitive/self-improvement**: Highest tolerance — agent is expected to self-monitor; threshold 12–15. Domain weight multiplier: 0.5x

### Score Decay

On each clean turn (no signals triggered), the score decays:
```
score = score * decay_factor
```
where `decay_factor = 0.85` (default). This ensures that isolated incident spikes do not permanently elevate risk.

## Implementation Architecture

### Hook Chain Placement

The supervisor loop operates at two hook points:

1. **`before_main_llm_call`** — pre-generation injection of L2 nudge fragments and domain-aware threshold computation. Reads current BST domain state and adjusts scoring weights.
2. **`tool_execute_after`** — post-tool-execution signal collection. Examines tool result for error patterns (via error-comprehension), tool call failures, and epistemic violations. Feeds CUSUM accumulator.

### Data Flow

```
┌─────────────┐    signals    ┌──────────────────┐
│ error-compr. ├──────────────►│ CUSUM accumulator │
└─────────────┘               └────────┬─────────┘
                                        │ score
                                        ▼
┌─────────────┐  domain weights  ┌──────────────────┐
│ bst-classif. ├─────────────────►│ intervention logic │
└─────────────┘                  └────────┬─────────┘
                                          │ action
                                          ▼
                                ┌──────────────────┐
                                │ injection-gate    │
                                │ (for L3/L4)       │
                                └──────────────────┘
```

### Persistence

Supervisor score is not persisted between sessions — each new conversation starts at score 0. However, patterns learned from past scores inform domain-aware threshold tuning stored in `supervisor_config.json`.

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `decay_factor` | 0.85 | Score decay per clean turn |
| `default_threshold` | 10 | Base CUSUM threshold |
| `soft_signal_weight` | 1 | Weight for soft signals |
| `medium_signal_weight` | 3 | Weight for medium signals |
| `hard_signal_weight` | 5 | Weight for hard signals |
| `domain_multipliers` | see above | Per-domain threshold scaling |
| `max_score` | 20 | Score cap to prevent overflow |
| `nudge_template` | "[SUPERVISOR: ...]" | Template for L2 injection text |

These are stored in `/a0/usr/Exocortex/config/supervisor_config.json` and can be tuned per program.md Priority 4 (config tuning, backup-first, rollback on failure).

## Interaction with Other Components

- **[[bst-classifier]]** — domain classification signals feed CUSUM accumulator with domain-aware weights. BST momentum state also triggers stall signal at high turns.
- **[[epistemic-integrity]]** — ungrounded claims count as medium signals (+3 with fabrication signal at +4)
- **[[error-comprehension]]** — deterministic error categories map directly to signal severity levels
- **[[injection-gate]]** — L3 intervention triggers forced phase transition back to full injection for re-stabilization; L4 triggers context reset
- **[[context-pruner]]** — L3 triggers aggressive sweep mode to reclaim token budget
- **[[backend-standby]]** — wrapper failure incidents are flagged but score reset after recovery (see inc-wrapper-killed)
- **[[temporal-proprioception]]** — turn counting informs decay timing and momentum stall detection

## Interaction Timeline

1. **Turn start**: BST classifies domain → supervisor adjusts domain weight multiplier
2. **Pre-LLM**: Supervisor checks current score; if ≥ L2 threshold, injects nudge into extras
3. **LLM call**: Agent generates response
4. **Tool execution**: Tool runs, result captured
5. **Post-tool**: error-comprehension parses result → feeds signals to CUSUM accumulator → supervisor updates score
6. **Score check**: If ≥ L3 threshold, supervisor commands injection-gate to compressed mode or reset
7. **Score decay**: On clean turn, score *= decay_factor

## Known Limitations and Mitigations

1. **Signal ambiguity**: Tool call failure may be due to transient network issue, not agent error. Mitigation: require at least 2 consecutive tool failures before raising to medium signal.
2. **Domain classification lag**: BST may lag one turn behind actual agent behavior, causing threshold mismatch. Mitigation: use a moving average of the last 3 BST domains.
3. **Score inflation in long research sessions**: Extended exploration sessions accumulate soft signals that may not indicate genuine drift. Mitigation: domain-aware threshold and decay factor partially address this; further improvement planned.
4. **L4 context reset data loss**: Resetting context mid-task loses intermediate reasoning. Mitigation: preserve task goal and memory anchors in the new context.
5. **No cross-session learning**: Supervisor starts fresh each conversation, missing patterns that accumulate over multiple sessions. Mitigation: future work on persistent drift pattern database.

## Historical Incidents and Improvements

- **inc-stuck-delivery-loop**: Supervisor did not detect repeated output stalling because stuck-delivery signals were not modeled. Added soft signal for consecutive tool calls without content output (after cycle 15).
- **inc-bst-momentum-lock**: BST classified task as coding+planning with high momentum, but task was simple research. Supervisor now includes momentum-stall signal at >=7 turns.
- **inc-wrapper-killed**: Wrapper termination caused cascade of hard signals unfairly penalizing agent. Added score reset on infrastructure failure detection.
- **dec-lower-supervisor-thresholds**: Qwen3.6 behavior patterns showed slower signal accumulation than expected; thresholds lowered by 2 points per level (after cycle 15).

## Testing Strategy

- **Unit test**: Simulate a sequence of tool failures and verify CUSUM accumulator reaches L4 reset at the expected turn.
- **Unit test**: Simulate domain switches and verify threshold multipliers are applied correctly.
- **Integration test**: Run a full workshop cycle and verify supervisor doesn't exceed L1 during normal operation.
- **Regression test**: After each config tuning (Priority 4), run a known-good task and verify supervisor score stays within baseline.

## Verification Status
Last verified: 2026-05-10 (cycle 37). Deepened from 55 to 155 lines. All section additions trace to program.md deepening guidelines and cross-component consistency checked against current wiki index.
