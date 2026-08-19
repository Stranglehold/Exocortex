# Injection Gate

**Created:** 2026-04-28T04:43Z
**Status:** Core Exocortex component specification
**Spec**: `/a0/usr/workdir/injection_gate_agent_interface_spec.md`

## Overview

The Injection Gate implements three-phase context management that transitions automatically based on conversation state rather than static turn counts. This is the operational mechanism that reduces context waste from initiation bloat while preserving structural integrity when domains shift.

## Three Phases

### Phase 1: Full Injection (Turns 1–3)

```
Inject:
  - Complete system prompt fragments
  - All recalled memories (up to 8 max per decay filter)
  - Full tool registry descriptions for invoked tools
  - BST full domain summary + complexity assessment
```

Rationale: Early conversation has no established baseline — maximum information needed for proper task classification and scaffolding setup.

### Phase 2: Conditional Enrichment (Turns 4–N)

Triggered when BST momentum threshold reached (domain stable for consecutive turns).

```
Inject:
  - System prompt core only (drop unused profile fragments)
  - Domain-matched memories only (filter by BST primary domain)
  - Tool descriptions only if tools invoked in last 3 turns
  - BST compact state: primary_domain + confidence score
```

Rationale: Conversation has locked into a domain; irrelevant scaffolding becomes noise.

### Phase 3: Compressed Mode (Steady State)

Triggered when no new domains detected AND no tool calls in last M turns.

```
Inject:
  - Minimal system prompt header (~50 tokens)
  - BST diff only if domain shift detected (usually empty)
  - No memory recall unless explicit query triggered
  - Tool registry skipped entirely
```

Rationale: Agent operating in steady-state on known task; context window freed for actual content.

## Transition Logic

| From Phase | To Phase | Trigger Condition |
|-----------|----------|------------------|
| Full → Conditional | BST momentum_turns >= threshold AND classification stable |
| Conditional → Compressed | No new domains + no tool calls in last M turns |
| Any → Full | New domain signal detected OR error recovery triggered |
| Compressed → Conditional | Tool invocation or memory recall request |

## Connection to Other Concepts

- **[[stateful-injection]]** — Phase 3 relies on cached state; only diffs injected when transitions occur
- **[[temporal-proprioception]]** — turn counting enables phase detection LLM cannot self-assess
- **[[initiation-bloat]]** — Injection Gate is the structural response to observed bloat pattern
- **[[bst-classifier]]** — domain stability signals drive all phase transitions

## References

- Full spec: `/a0/usr/workdir/injection_gate_agent_interface_spec.md`
- BST implementation feeds transition logic via `_11_belief_state_tracker.py`

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
