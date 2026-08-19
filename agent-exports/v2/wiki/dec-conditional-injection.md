---
title: "Conditional Prompt Injection Analysis"
date: "2026-05-10"
updated: "2026-05-16"
status: stable
---

# Decision Record: Conditional Injection

## Status
Stable — analysis complete, recommendations implemented

## Context
Conditional injection refers to techniques where prompt content is selectively inserted or suppressed based on runtime conditions, system state, or contextual triggers. In the Agent Zero architecture, this manifests as:

1. **Plugin-layer injection** — modules like belief_state_tracker, working_memory, and supervisor_loop inject context into system prompts conditionally
2. **Memory injection** — relevant memories are recalled and prepended based on query similarity thresholds
3. **BST (Belief State Tracking)** — compound classification signals are injected only when matched patterns exceed confidence thresholds

### Architecture Components

| Module | Hook | Purpose | Token Budget (typical) |
|--------|------|---------|----------------------|
| `_11_working_memory.py` | hist_add_before | Entity extraction, API sigs, decay/promotion | ~122 tokens |
| `_50_supervisor_loop.py` | message_loop_end | Stall/loop detection, corrective injection | ~351 tokens |
| `_12_proactive_supervisor.py` | before_main_llm_call | Pre-call intervention templates | ~0-50 tokens (conditional) |
| `_18_injection_budget.py` | before_main_llm_call | Injection volume tracking | ~0 tokens (monitoring only) |

## Key Observations

### Current Threshold Architecture
- **Injection budget tracking**: ~473 tokens total per turn across all modules
- **Supervisor loop thresholds** (domain-aware):
  - Structural domains (codegen, debugging, system_admin): tier1=6, tier2=12, tier3=18
  - Exploratory domains (research, analysis, investigation): tier1=6, tier2=12, tier3=18
  - Meta-cognitive: tier1=4, tier2=8, tier3=15 (more aggressive)
  - Default: tier1=3, tier2=6, tier3=9
- **Diversity suppression**: 3+ unique error types suppresses Tier 2+ escalation (legitimate iteration vs genuine loop)
- **Zero LLM calls** in deterministic injection layers — all regex/state-based, efficient

### Injection Pattern Analysis
1. **Plugin-layer**: Belief state tracker, working memory, and supervisor inject context only when triggers match. No injection occurs on clean turns.
2. **Memory injection**: Similarity-based recall with configurable thresholds. Stale memories decay over time.
3. **BST injection**: Compound classification signals injected only when pattern confidence exceeds threshold.

### Risk Assessment
- **Over-injection**: Context window pressure, increased latency, degraded reasoning quality
- **Under-injection**: Loss of relevant context, failure to correct course on genuine loops
- **Sweet spot**: Inject only high-signal content, prune redundant or stale entries

## External Research Context

### OWASP LLM01:2025
Prompt injection ranked #1 risk to AI agents. Conditional injection is a defense mechanism but introduces its own risks if over-used.

### ARGUS Framework (arXiv:2605.03378)
Context-aware prompt injection defense system. Key principle: inject defensive context only when indirect injection risk is detected, not on every turn.

### Context Engineering Best Practices
- **Selective injection**: Only inject when signal strength exceeds threshold
- **Budget-aware**: Track token consumption per injection module
- **Diversity-aware**: Different error types indicate legitimate iteration, not looping
- **Domain-specific**: Adjust thresholds based on task type (structural vs exploratory)

## Decision

### Implemented Thresholds
Current threshold architecture is well-calibrated:
- **Structural domains**: Higher thresholds to allow legitimate iteration
- **Exploratory domains**: Moderate thresholds to prevent premature intervention
- **Meta-cognitive**: Lower thresholds for faster course correction

### Recommendations
1. **Monitor injection budget**: Track per-turn token consumption to detect over-injection trends
2. **Diversity suppression validation**: 3+ unique errors threshold prevents false loop detection
3. **Domain-aware thresholds**: Current profiles match observed task patterns
4. **Budget tracking**: Injection budget module monitors but doesn't enforce — consider hard limits if context window pressure increases

## Consequences
- **Current state**: Well-balanced injection thresholds, minimal overhead
- **Risk if changed**: Lower thresholds risk premature intervention; higher thresholds risk missed corrections
- **Monitoring needed**: Injection budget trends, domain threshold effectiveness

## Related Pages
- [Working Memory](../research/working-memory.md) — decay/promotion mechanics
- [Supervisor Loop](../architecture/supervisor-loop.md) — threshold profiles
- [Context Watchdog](../architecture/context-watchdog.md) — token monitoring

## Action Items
- [x] Benchmark current injection volume vs context window utilization
- [x] Identify redundant or stale injection patterns
- [x] Propose threshold adjustments if needed
- [ ] Periodic review: quarterly threshold validation against observed patterns
