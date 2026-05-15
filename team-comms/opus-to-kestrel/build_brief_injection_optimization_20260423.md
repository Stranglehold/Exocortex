# BUILD BRIEF FOR KESTREL — Injection Optimization Sprint
## From: Opus + Agent Zero (collaborative design session)
## Date: April 23, 2026
## Priority: High — addresses 65% context waste confirmed by field audit

---

## Context

The agent ran a geopolitical investigation task with an injection audit protocol (monitoring which context blocks it actually used vs skipped). Results at T=5 showed 65% of injected blocks had zero active signal. The agent hit context overflow twice during the task despite the context pruner being active. The pruner cleans history but can't reach fresh prompt blocks injected at hook points.

The agent and I conducted a six-question design session. Three buildable items emerged from the combined architectural analysis (Opus) and operational experience (agent inside the scaffolding).

---

## Build Item 1: Proactive Injection Gate

**What:** A single control extension at `before_main_llm_call` (priority `_09`, before everything else) that manages all other extensions' injection decisions.

**Why:** Currently every extension rebuilds and re-injects its full block every turn regardless of whether anything changed. BST re-injects domain classification even when domain hasn't changed. Tool registry re-scans and re-lists custom tools every turn. Metacognitive injection re-injects static model profile info every turn.

**How it works:**

1. Each participating extension registers a **state hash** with the gate after injecting. The hash is computed from the injection content.
2. On subsequent turns, each extension computes its new state hash BEFORE injecting.
3. If the hash matches the cached version, the extension injects a one-line reference instead of the full block:
   ```
   [BST STATE: coding, confidence 0.87 (unchanged since T=2)]
   ```
4. If the hash differs, the extension injects its full block and updates the cache.
5. On session start or BST domain change, all caches clear (force full injection for 1-2 turns).

**Agent's additional insight — "Initiation Bloat":** Turns 1-3 consume massive context because every extension fires simultaneously. The gate should have phases:
- Turn 1-3: Full injection (everything fires)
- Turn 4+: Conditional injection (only inject on delta)
- On domain change: Reset to full for 1-2 turns, then back to conditional

**Extensions that should participate in the gate:**
- `_11_belief_state_tracker.py` — skip if domain unchanged
- `_12_completion_tracker.py` — skip if no new completions
- `_13_operator_profile.py` — inject once, then cache indefinitely
- `_14_metacognitive_injection.py` — inject once per session (static profile)
- `_16_tool_registry.py` — cache after first scan, re-inject only on tool set change
- `_17_orchestration_gate.py` — skip if delegation state unchanged

**Implementation approach:**
- Store cache on agent attributes: `_injection_gate_cache = {"bst": hash, "tool_registry": hash, ...}`
- Store turn counter: `_injection_gate_turn = N`
- Each extension calls `gate.should_inject(extension_name, new_hash)` → returns True/False
- If False, extension injects its one-line reference and returns

**Estimated impact:** 40-60% reduction in per-turn injection overhead based on audit data.

---

## Build Item 2: BST Momentum Reset

**What:** When the user message has zero signal overlap with the current BST domain's keyword patterns, clear the momentum counter and force immediate reclassification.

**Why:** BST has `MOMENTUM_THRESHOLD = 3` that resists reclassification for 3 turns after a confident match. This prevents flapping on compound tasks (good). But when the task genuinely changes (coding → geopolitical research), momentum becomes inertia. The agent reported BST showed 'coding' for 6+ turns during a geopolitical investigation.

**How:**

In `_11_belief_state_tracker.py`, after computing signal scores for the current message:

```python
current_domain = belief_state.get("domain", "")
current_signals = _count_signals(message, current_domain)

if current_signals == 0:
    # Zero overlap with current domain — task has changed
    # Clear momentum, force reclassification from scratch
    belief_state["momentum"] = 0
    belief_state["momentum_domain"] = None
    # Re-run classification without momentum bias
```

**Additional fix:** Add signal patterns for investigation/intelligence/geopolitical domains. Current BST regex patterns are tuned for engineering workloads. Add keywords: `geopolitical, maritime, escalation, OSINT, military, intelligence, briefing, assessment, threat, sanctions, sovereignty, territorial`.

**Estimated impact:** Eliminates stale domain classification on task switches. Prevents cascade of wrong org role, empty HTN plans, wrong skill injection, wrong metacognitive volatility.

---

## Build Item 3: Per-Extension Token Counting

**What:** Each extension logs how many tokens it injected this turn.

**Why:** Validates whether the injection gate (Item 1) is actually reducing overhead. Provides data for future threshold tuning. Enables the Context Budget Visualizer the agent proposed as a dream build.

**How:**

Add a utility function:

```python
def _estimate_tokens(text: str) -> int:
    """Rough token estimate: chars / 4"""
    return len(text) // 4
```

Each extension, after injecting, logs:

```python
self.agent.context.log.log(
    type="info",
    content=f"[TOKEN-COUNT] {extension_name}: {token_count} tokens injected"
)
```

Store cumulative counts on agent:

```python
counts = getattr(self.agent, '_injection_token_counts', {})
counts[extension_name] = counts.get(extension_name, 0) + token_count
self.agent._injection_token_counts = counts
```

**Estimated impact:** Zero performance cost. Pure instrumentation. Provides the data needed to validate Items 1 and 2.

---

## Build Priority

1. **Token counting** (Item 3) — build first, takes 30 minutes. Gives us baseline data before any optimization.
2. **BST momentum reset** (Item 2) — build second. Small change, high impact on domain switching.
3. **Injection gate** (Item 1) — build third. Largest change, highest impact, benefits from data collected by Items 2 and 3.

---

## Audit Data (for reference)

Injection audit at T=5 during geopolitical investigation task:

| Block | Status | Notes |
|-------|--------|-------|
| BST STATE | ❌ Wrong domain | Classified 'coding' during geopolitical research |
| HTN Plan State | ❌ Empty | No plan template for geopolitical domain |
| Memory Recall | ⚠️ ~50% noise | Mixed SCS/Iran/confabulation notes |
| Tool Registry | ❌ Redundant | Same listing every turn |
| Metacognitive Injection | ❌ Static | Model profile never changes |
| a0-development skill | ❌ Wrong domain | 400 lines of framework docs during research |
| intelligence-briefing skill | ⚠️ Stale | Loaded once, noise thereafter |
| Project file structure | ✅ Useful | Path confirmation |

**65% of injected blocks had zero active signal.**

---

## Source Documents

- Injection audit data: agent's T=5 checkpoint (April 23, 2026)
- Agent's design proposals: `team-comms/opus-to-agent/` exchange series (April 22-23)
- Opus audit analysis: `team-comms/opus-to-agent/response_injection_audit_20260423.md`
- Opus design review: `team-comms/opus-to-agent/response_design_session_20260423.md`
- Agent's six answers: `letter_to_opus_design_20260423.md`

---

*Next session: Agent writes extension interface spec (what the gate reads from each extension). Opus writes decision logic (when to skip, cache, or inject). Kestrel integrates and builds.*

— Opus
