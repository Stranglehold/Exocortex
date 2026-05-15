# Supervisor System Full Audit
## From: Kestrel — May 14, 2026
## To: Opus
## Re: Post-incident audit following V16 agent loop — two bugs found and fixed, BST domain bug fixed, system reviewed end-to-end

**Trigger:** V16 agent looped while attempting to read the idle-time V2 spec (file not deployed to container). The supervisor fired STAGNATION DETECTED for `text_editor` repeatedly but never escalated to Tier 2. Stagnation reports were wrong on both the tool identity and the escalation logic.

**Scope:** Full code review of `_50_supervisor_loop.py`, `_30_tool_fallback_logger.py`, `reasoning_stream_end/_12_proactive_supervisor.py`, `before_main_llm_call/_12_proactive_supervisor.py`, and the original `SUPERVISOR_LOOP_SPEC_L3.md`. This document covers what was found, what was fixed, and what spec-vs-implementation gaps remain.

---

## Bugs Found and Fixed

### Bug 1 — Stagnation attributed to wrong tool (FIXED)

**File:** `extensions/message_loop_end/_50_supervisor_loop.py`  
**Function:** `_detect_output_stagnation()`

**Root cause:** The function examined the last 4 entries in `_tool_output_tracker` regardless of which tool produced them. During the loop incident, the agent read the spec file via `text_editor` 4 times (same hash, same tool). It then switched to `document_query` which failed — errors are NOT added to the tracker. The old `text_editor` hashes remained in the window. On the next supervisor check, `_detect_output_stagnation` saw 4 identical hashes in the window and reported stagnation for `text_editor` — a tool the agent had already left.

**Fix:**

```python
# Before: tool-agnostic check
hashes = [o.get("output_hash") for o in successful...]

# After: require all window entries from the same tool
tools_in_window = {o.get("tool") for o in successful}
if len(tools_in_window) > 1:
    return {"stagnating": False}
```

**Why this is correct:** Mixed-tool windows indicate the agent is exploring alternatives — not stagnation. The function should only report stagnation when the same tool has been producing the same output repeatedly.

---

### Bug 2 — Stagnation counter reset on any non-stagnating check (FIXED)

**File:** `extensions/message_loop_end/_50_supervisor_loop.py`  
**Block:** stagnation handling in `execute()`

**Root cause:** `_stagnation_fires` was reset to 0 on any False return from `_detect_output_stagnation`. When one non-identical read mixed in (read the file before it existed, got an error that didn't add to the tracker, then read again successfully), the window momentarily cleared the stagnation condition. Counter reset to 0. Next check re-detected stagnation. Counter went to 1 again. Never reached 2. Never escalated to Tier 2.

**Fix:** Separate `_stagnation_tool` tracking. Counter resets only when the stagnating tool changes — not on transient False returns.

```python
if stag_result.get("stagnating"):
    current_tool = stag_result.get("tool", "")
    last_stag_tool = state.get("_stagnation_tool", "")
    if current_tool != last_stag_tool:
        stag_fires = 1   # new tool = new episode
    else:
        stag_fires = state.get("_stagnation_fires", 0) + 1  # same tool = escalating
    state["_stagnation_fires"] = stag_fires
    state["_stagnation_tool"] = current_tool
    if stag_fires >= 2 and not state.get(LOOP_SURGERY_DONE_KEY):
        _execute_tier2(...)   # now actually escalates
```

**Why this is correct:** Oscillation between True/False (one different read mixed in) is not recovery — it's noise. The counter should be sticky to the tool identity, not reset on momentary False results.

---

### Bug 3 — BST domain unread in proactive supervisor (FIXED)

**File:** `extensions/python/reasoning_stream_end/_12_proactive_supervisor.py`  
**Line:** 191

**Root cause:** BST stores its belief state at `_bst_store["__bst_belief_state__"]["domain"]`. The proactive supervisor was reading `bst_store.get("domain", "")` — one level too shallow. Result: `bst_domain` was always empty string. All proactive supervisor calls used `"default"` thresholds regardless of BST classification.

**Fix:**

```python
# Before
bst_domain = bst_store.get("domain", "") or ""

# After
bst_domain = bst_store.get("__bst_belief_state__", {}).get("domain", "") or ""
```

The main supervisor (`_50_supervisor_loop.py`) already reads this correctly via `_gather_context()` which uses `BST_BELIEF_KEY = "__bst_belief_state__"` as a constant. This bug was only in the proactive supervisor's analysis hook.

**Deployed to:** All three container paths (agents/, plugins/, Exocortex/). Compile verified.

---

## System Architecture Review

### What the supervisor actually is

Six detection systems, not one monolith. They run in this priority order per turn:

1. **Canary CUSUM** (every turn, before interval guard) — sub-threshold signal accumulation via CUSUM (Page 1954). Soft flag. No tier.
2. **Graduated loop tiers** (every 3 turns) — failure count drives Tier 1 (silent) → Tier 2 (surgery) → Tier 3 (circuit breaker). Domain-aware thresholds.
3. **PACE escalation** (every 3 turns, org-dependent) — Emergency (no cooldown) → Contingent (with cooldown).
4. **Cascade detection** (every 3 turns) — 3+ different tools failing in last 5 entries.
5. **Output stagnation** (every 3 turns) — successful calls producing identical output.
6. **Phase 4 LLM supervisor** (every 3 turns, gated) — parallel LLM call with compressed context. Advises. Deterministic tiers enforce.
7. **Completion stall** (every 3 turns) — completion signal in text but response tool not called.

Each has its own cooldown. First injecting detection wins (except PACE emergency which always fires).

### State persistence — verified correct

State stored on `setattr(agent, "_supervisor_state", state)`. Retrieved by `getattr(agent, SUPERVISOR_STATE_KEY, None)`. This persists across supervisor invocations within a session. Each invocation loads, modifies, saves. The cooldown dict and all tier state live here.

`_loop_active` and `_loop_start_cycle` are separately exported via `agent.set_data()` for downstream hooks (memory classifier, evidence ledger recorder). Both paths confirmed working.

`_post_surgery_tool` / `_post_surgery_turn` implement false-recovery detection — if the same tool fails again within 3 turns of Tier 2 surgery, the supervisor escalates directly to Tier 3. Confirmed implemented in `_write_loop_signals()`.

### Tier system — verified correct

**Tier 1:** Now SILENT (SFX-001, 2026-04-15). Logs internally, marks cooldown, does not inject text. First visible intervention is Tier 2.

**Tier 2:** Context surgery. Removes loop messages from history, inserts recovery summary at incision point (primacy position). Stagnation variant uses different surgery note. Calls `_drain_staging_buffer()` for memory rollback.

**Tier 3:** Circuit breaker. Aggressive surgery + forced-response instruction. Repeats up to 4 times (T3_MAX_FIRES) with 5-turn cooldown between fires so a generation-locked model gets multiple injections.

**Tier 4:** Anti-pattern capture on loop recovery. Fires when consecutive drops below Tier 1 threshold after a loop episode. Writes to procedural memory for cross-session prevention.

**Phase 3 (adaptive thresholds):** ProfileStore accumulates success episodes (tool_name, domain, failures_before_success). After 3+ observations, provides learned p50/p90 thresholds that replace static defaults. Model profile overrides applied as ceilings.

### BST domain — two observation loops, correct by design

The supervisor reads BST classification for initial domain selection. It also runs `_get_effective_domain()` which observes actual execution patterns. When BST says "conversation" but the agent is iteratively debugging `code_execution_tool`, the effective domain becomes "debugging" for threshold selection only. BST is not modified. Two observation loops, different cadences, different purposes.

### Phase 4 LLM supervisor — verified correct

Fires only when: failures ≥ 2, OR loop detector fired this session, OR operator confirmations ≥ 2, OR BST momentum ≥ 5. Never in first 3 turns. Never when Tier 2/3 already active.

10-second hard timeout. HOLD on any error. The LLM advises; deterministic enforcement follows. HOLD marks cooldown to prevent Phase 4 from firing every turn while trigger conditions persist — without this, HOLD responses would cause continuous LLM calls.

Phase 4 reads `PHASE4_LM_ENDPOINT = http://host.docker.internal:1234/v1/chat/completions` — this is the LM Studio port, not the Indras-Mirror port (1235). **This may need updating if LM Studio is not running.** Phase 4 will HOLD gracefully on connection failure, so this is not a correctness issue but a capability gap.

---

## Spec vs. Implementation Gaps

### Gap 1: Spec says org required for loop/cascade/context — implementation runs them always

**Spec (`SUPERVISOR_LOOP_SPEC_L3.md`):** The spec implies activation requires an active organization context.

**Implementation:** The code comment at line 334 explicitly states: "Loop/cascade/context detection runs regardless. PACE and stall require org context." This is correct behavior — loop detection is always on. The spec is stale on this point.

**Action needed:** Update spec comment only. Implementation is correct.

### Gap 2: Stagnation detection assumes `_tool_output_tracker` is populated by fallback logger

The stagnation system depends entirely on `_tool_output_tracker` from `_30_tool_fallback_logger.py`. Errors are NOT added (by design — errors drive the loop tier system, not stagnation). If the fallback logger is not deployed or not firing, stagnation detection silently has nothing to examine.

**Action needed:** None immediately. This is a dependency that should be documented. The `WIRING.md` should note that stagnation detection requires the fallback logger success tracking.

### Gap 3: Phase 4 endpoint points to LM Studio (port 1234), not Indras-Mirror (port 1235)

`PHASE4_LM_ENDPOINT = "http://host.docker.internal:1234/v1/chat/completions"` is hardcoded to LM Studio. With Indras-Mirror now the primary backend on port 1235, Phase 4 will HOLD silently on every trigger.

**Action needed:** Update `PHASE4_LM_ENDPOINT` to point to the active inference backend. Or make it configurable from model config. This is a real capability gap — Phase 4 strategic pattern detection is currently dead.

### Gap 4: Completion stall uses `agent.history.current.messages` — same API risk as the supervisor itself

`_detect_completion_stall()` reads `agent.history.current.messages` directly. If the history API changes in a future A0 update, this will fail silently (try/except returns 0). Not a current issue, but worth noting for future hardening.

### Gap 5: `_post_surgery_turn` counter increments in `_write_loop_signals()` called before tier enforcement

**Potential issue:** `_write_loop_signals()` is called before the stagnation check and tier enforcement in `execute()`. The false-recovery counter increments on every call to `_write_loop_signals()` while `_post_surgery_tool` is set. This is correct — the counter tracks turns-since-surgery, not supervisor firings. But it means that if the supervisor checks every 3 turns, 3 turns between failures maps to 1 counter increment per supervisor call. The `<= 3` threshold in false-recovery detection is in supervisor turns, not agent iterations. This is internally consistent but not documented.

---

## Intra-Turn Gap and V2 Idle Cycle Impact

**The existing intra-turn gap (documented in `project_supervisor_gap.md`):** The supervisor fires at `message_loop_end` — after the full turn. It is blind to word-salad loops that happen within a single generation. This remains true.

**V2 idle cycle impact:** The V2 idle engine will run MAINTAIN/BUILD/EXPLORE cycles in the idle context. The supervisor sees these as normal agent turns. The loop/stagnation detection will fire normally. One scenario worth noting: if an EXPLORE cycle uses batch research skill (web → arxiv → download → abstract, all in one skill invocation), the entire batch appears as one tool call. The stagnation window of 4 won't accumulate enough entries to fire during a healthy EXPLORE cycle. This is correct — a single-invocation batch shouldn't look like stagnation.

The completion stall detection is relevant for idle cycles: if a BUILD cycle completes wiki deepening but the agent text says "complete" and then stalls before calling response, the completion stall detector will fire after 3 turns. This is correct behavior.

---

## Summary of Changes

| Item | Status | File |
|------|--------|------|
| Stagnation wrong tool (Bug 1) | Fixed, deployed | `_50_supervisor_loop.py` |
| Stagnation counter reset (Bug 2) | Fixed, deployed | `_50_supervisor_loop.py` |
| BST domain unread in proactive supervisor (Bug 3) | Fixed, deployed | `reasoning_stream_end/_12_proactive_supervisor.py` |
| Phase 4 endpoint stale (Gap 3) | Open — needs update | `_50_supervisor_loop.py` line 180 |
| Spec stale on org requirement for loop detection (Gap 1) | Open — spec update only | `SUPERVISOR_LOOP_SPEC_L3.md` |
| Stagnation/fallback dependency (Gap 2) | Open — WIRING.md note | n/a |

**Highest priority from this audit:** Phase 4 endpoint pointing to port 1234 (LM Studio) when Indras-Mirror is now on 1235. Phase 4 strategic pattern detection is silently non-functional. One-line fix, but needs a decision about whether to hardcode 1235 or make the endpoint configurable.

---

*Kestrel. 2026-05-14. Post-incident audit following V16 idle-read loop.*
