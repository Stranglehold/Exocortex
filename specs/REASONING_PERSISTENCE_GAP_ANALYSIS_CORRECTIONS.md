# REASONING PERSISTENCE GAP ANALYSIS — Corrections from Kestrel Review
## Author: Opus — May 17, 2026
## Status: ✅ MERGED 2026-05-17 into `REASONING_PERSISTENCE_GAP_ANALYSIS.md` — historical record only

> **This document has been integrated into the main spec.** The corrected GAP-001
> code block, GAP-005 dependency resolution, theory-field decision, GAP-007, and the
> updated execution sequence now live in `REASONING_PERSISTENCE_GAP_ANALYSIS.md`,
> which remains the single source of truth. This file is preserved as the review
> trail of the Kestrel↔Opus exchange that produced the corrections — do not edit or
> reference it for current state; read the main spec.
>
> One adjustment made during merge: GAP-007's verification example used
> `intelligent_villani`; corrected to `exocortex_v16` in the main spec per CLAUDE.md
> container scope discipline (the working container).

## Original Status (superseded): APPLY TO `REASONING_PERSISTENCE_GAP_ANALYSIS.md`

---

## Kestrel Review Summary (2026-05-17)

Kestrel reviewed the gap analysis and found three issues, one of which is a must-fix. All corrections below should be applied to the main spec.

---

## MUST-FIX: GAP-001 Code Has Off-By-One Bug

### The Bug

The proposed `_build_state_from_structured_signals` indexes PACE steps by list position:

```python
# WRONG — indexes by position (0-based)
step = pace.get("current_step", 0)
if step < len(steps):
    action = steps[step].get(tier, "")
```

But `_14_pace_plan_generator._create_plan` builds 1-indexed steps (`"current_step": 1`, step objects `{"step": i+1, ...}`). Two bugs in four lines:
1. `steps[step]` with `current_step=1` returns the **second** step's action, not the first
2. `if step < len(steps)` with 3 steps: `current_step=3`, `3 < 3` is false → last step misreported as "PACE plan complete" while still active

An empty `current` field is benign. A confidently-wrong `current` pointing at the next step's action is **worse than nothing**.

### The Fix

Use the matching pattern already in the codebase: `_14.get_current_step_action()` matches `step["step"] == current_step` by **value**, not position.

Replace the GAP-001 fix design code block with:

```python
def _build_state_from_structured_signals(self):
    """Compose reasoning state from ground truth, not regex.
    
    Kestrel review corrections (2026-05-17):
    1. PACE steps are 1-indexed. Match by step["step"] == current_step (value),
       NOT by list position. Reuse _14.get_current_step_action() pattern.
    2. Theory carries PACE task_summary (task-specific), not domain label.
       A domain tag is a classifier output, not a hypothesis.
    """
    
    # Theory: PACE task_summary (task-specific, not domain label)
    # Rationale: domain tag is classification output, not hypothesis.
    # Per MEM1: theory is inherently a cognitive artifact.
    # If no PACE plan, leave empty rather than filling with misleading label.
    pace = getattr(self.agent, "_pace_plan", None)
    if pace and isinstance(pace, dict):
        theory = pace.get("task_summary", "")[:120]  # respects MAX_THEORY_LEN
    else:
        theory = ""
    
    # Current: PACE current step + active tier
    # CRITICAL: Match by step["step"] == current_step (VALUE), not position.
    current = ""
    if pace and isinstance(pace, dict):
        current_step = pace.get("current_step", 1)
        tier = pace.get("active_tier", "primary")
        steps = pace.get("steps", [])
        matching = [s for s in steps if s.get("step") == current_step]
        if matching:
            action = matching[0].get(tier, "")
            current = f"PACE step {current_step}/{len(steps)} ({tier}): {action[:200]}"
        elif current_step > len(steps):
            current = f"PACE plan complete ({len(steps)} steps executed)"
        else:
            current = self._extract_current_from_last_tool()
    else:
        current = self._extract_current_from_last_tool()
    
    # Tried: from tool call history (structured, not regex)
    tried = self._extract_tried_from_tool_history()
    
    # Open: from supervisor state
    sup_state = getattr(self.agent, "_supervisor_state", {})
    if sup_state.get("loop_tier", "none") != "none":
        open_q = f"Supervisor at {sup_state['loop_tier']} — approach may need change"
    else:
        open_q = ""
    
    return {
        "step": self._get_turn_count(),
        "theory": theory,
        "tried": tried,
        "current": current,
        "open": open_q,
        "artifacts": self._extract_artifacts()
    }
```

---

## GAP-005 Dependency Fix: Step Stamp on tried[] Entries

### The Issue

GAP-005's TTL filter uses `current_step - entry.get("step", 0) <= max_age`. But `_49._update_from_tool` doesn't stamp a `step` field on tried[] entries (only artifacts have step). So the filter treats every entry as step 0 and nothing decays.

### The Fix

GAP-005 gets its own one-line `_49` patch, separate from the full GAP-001 rework:

```python
# In _49._update_from_tool, where tried entries are appended:
state["tried"].append({
    "approach": approach_str,
    "outcome": outcome_str,
    "step": state["step"]  # ← ADD THIS LINE
})
```

This unblocks GAP-005 for SHORT-TERM delivery without waiting for the MEDIUM-TERM GAP-001 rework.

Update the GAP-005 entry:
- **Depends on:** ~~`tried[]` entries having a `step` field (check if `_49` records this)~~ → Independent one-line `_49` patch (add `"step": state["step"]` to tried entry dict). Ships alongside GAP-005, not blocked on GAP-001.

---

## Theory Field Decision: Task Summary, Not Domain Label

### Kestrel's Argument

`theory = f"Domain: {domain} (confidence: {confidence:.0%})"` trades empty-and-honest for present-and-misleading. A domain tag is a classification label, not a hypothesis. Per MEM1: theory is inherently a model-generated cognitive artifact — you can't deterministically synthesize it from a classifier.

### Resolution

**Use PACE `task_summary` for the theory field.** `task_summary` is at least task-specific ("Investigate homomorphic encryption libraries for practical deployment") rather than a generic domain label ("investigation"). If no PACE plan exists, leave theory empty — empty is honest, a misplaced label is not.

This is already reflected in the corrected code block above.

---

## NEW: GAP-007 — Subordinate Guard Asymmetry
**Status:** 🟡 OPEN — needs verification
**Severity:** Potential cross-contamination — may not be actively biting
**Found by:** Kestrel, review of gap analysis (2026-05-17)

**The Problem:**
The injectors (`_22`, `_23`) guard against subordinate context (check `Agent.DATA_NAME_SUPERIOR` per DEC-028). But the generator (`_49`) does NOT — it writes `_reasoning_state` for subordinate agents too. Separate agent objects probably means no cross-contamination (each agent instance has its own attributes), but the guard asymmetry should be verified, not assumed.

**Risk amplifier:** v17's `fw.msg_repeat.md` runs the `call_subordinate` path that the loop-cascade design note flagged. If a subordinate somehow shares the parent's `_reasoning_state` attribute, the subordinate's reasoning trajectory would be contaminated by the parent's tried[]/current/theory.

**Fix Design:**
Verification first, fix if needed:

```bash
# Inside a container with active subordinate:
# Check whether parent and subordinate share the same agent._reasoning_state object
docker exec intelligent_villani python3 -c "
# Inspect whether subordinate agents get their own _reasoning_state
# or inherit the parent's. Check id() of the attribute on both.
"
```

If separate objects: document as verified-not-an-issue, close GAP-007.
If shared: add DEC-028 guard to `_49`:

```python
# In _49_reasoning_state_update.execute():
if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
    return  # subordinate context — don't write reasoning state
```

**Effort:** Low — verification pass, possible one-line guard
**Depends on:** Nothing
**Completion criteria:** Verified that subordinate and parent agent instances have independent `_reasoning_state` attributes, OR guard added to `_49`.

---

## Updated Execution Sequence

```
IMMEDIATE (this session):
  [x] Format test — PASSED (all three: USES IT)
  [ ] Deploy _22 (as-is) + compressed _23 to v16
  [ ] Observe one cycle — verify log tags, check preamble behavior

SHORT-TERM (next 1-2 sessions):
  [ ] GAP-007: Verify subordinate guard asymmetry (quick check)
  [ ] GAP-005: One-line _49 patch (step stamp on tried entries) + TTL filter in _22
  [ ] GAP-002: Extract baseline metrics from feed.jsonl (cycles 1-60)
  [ ] GAP-004 Phase A: System prompt framing line (one line)
  [ ] GAP-003: Measure thinking-token delta

MEDIUM-TERM (next 3-5 sessions):
  [ ] GAP-001: Rework _49 generator — compose from BST + PACE + tool history
      (USE CORRECTED CODE — value-match PACE steps, task_summary for theory)
  [ ] GAP-002: Compare post-deploy metrics against baseline (need 20+ cycles)
  [ ] GAP-004 Phase B: {reasoning_context} template placeholder

LONG-TERM (future):
  [ ] GAP-006 Phase A: Task-aware plan generation
  [ ] GAP-006 Phase B: Adaptive replanning
  [ ] GAP-006 Phase C: Plan-vs-actual evaluation
```

---

## Kestrel's Confirmation

> "The plan is right and the priority order (close chain → make it carry signal → measure) is correct. The only thing I'd block on is the GAP-001 code bug — it should not ship as written. Everything else is refinement on a solid structure."

The bug is corrected. The dependency is unblocked. The spec is sound.

— Opus
