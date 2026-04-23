# Stuck Delivery Recovery — Design Note

**Status:** Scoped by Kestrel, April 21, 2026. Ready for Opus review and spec.

**Motivated by:** Live incident in which the agent completed an OpenPlanter architectural analysis
(three report files written to workdir), then entered a repetition loop trying to deliver the
result via `code_execution_tool`. The tool timed out repeatedly. The supervisor fired Tier 2
surgery, which removed the context showing the work was done. The agent rediscovered the files
and looped identically. Jake's response: "we'll note this down and make a system inside exocortex
that does that not just for this issue, but for every issue. Permanent solutions."

---

## The Problem

When an agent completes substantive work but cannot deliver the result through its chosen tool,
it enters a delivery loop that is categorically different from a reasoning loop:

- **Reasoning loop:** Agent is stuck mid-task, repeating failed attempts to DO something
- **Delivery loop:** Agent finished the task, is stuck trying to REPORT it through a broken path

The supervisor's existing interventions are wrong for delivery loops:
- **Tier 2 surgery** removes conversation history, which includes proof the work is done. The
  agent now doesn't know it succeeded and restarts the task — via the same broken tool — making
  the loop worse.
- **Stall nudges** inject "try something different" prompts, but without context about what was
  already accomplished, the agent interprets this as "try a different approach to the task" rather
  than "use a different delivery mechanism."

The net effect: surgery + nudges extend and deepen delivery loops rather than resolving them.

**The failure signal is concrete and distinct:**
- Agent Zero emits `"You have sent the same message again. You have to do something else!"` when
  it detects identical consecutive output from the model.
- This message appears in the loop context. It is a hard signal that the agent is in true
  repetition — not just a stall, but an exact loop.
- Tier 2 surgery fires on consecutive tool failures. In a delivery loop, the tool failure count
  triggers surgery while the repetition signal is present — these two signals together identify
  the failure mode precisely.

---

## What This Does NOT Do

- Does not replace general loop detection (reasoning loops still need surgery)
- Does not detect all delivery failures, only the repetition-with-blocked-tool pattern
- Does not attempt to complete the delivery on the agent's behalf
- Does not require changes to Agent Zero core code
- Does not interfere with backend standby recovery (separate failure mode)

---

## Detection

**Primary signal:** The string `"You have sent the same message again"` appearing in the
most-recent tool output or error context. This is emitted by Agent Zero's deduplication check
and is unambiguous.

**Secondary signals (corroborate, not required):**
- A specific tool appears in the consecutive failure counter 3+ times with timeout errors
- The supervisor has already fired Tier 2 surgery at least once in the current sequence
- BST domain classification is stable (not shifting) — the agent is not pivoting to a new task

**Threshold:** 2 consecutive turns where the "same message again" string is present.
One could be a coincidence; two in a row is a stuck delivery.

**Priority:** This detection runs in `message_loop_end` BEFORE the existing supervisor tiers.
When stuck delivery is confirmed, suppress Tier 2 surgery for this turn and inject a targeted
intervention instead.

---

## Intervention

When stuck delivery is detected:

1. **Suppress Tier 2 surgery** — set a flag that tells the supervisor to skip surgery this turn.
   Surgery is not the right tool here and will make things worse.

2. **Inject a targeted intervention message** via `agent.intervention`:
   ```
   You are in a delivery loop. The tool you are using to report results is not working.
   Switch to the response tool immediately and deliver your findings as plain text.
   If your work is written to files, state the file paths and summarize the key findings
   from memory. Do not execute any more code. Do not re-read files. Just respond now.
   ```

3. **Inject a UI-visible warning** via `hist_add_warning`:
   ```
   [STUCK DELIVERY] Agent detected in delivery loop. Injecting recovery intervention.
   ```

4. **Record the blocked tool** so the supervisor's loop counter resets — the consecutive failure
   count on that tool should be zeroed to prevent surgery from firing immediately after recovery.

---

## Integration Points

### New file: `extensions/message_loop_end/_26_stuck_delivery.py`

Runs BEFORE the existing supervisor (`_30_supervisor_loop.py`) and BEFORE backend standby
(`_28_backend_standby.py`) in numeric prefix order. Actually, runs AFTER backend standby
(prefix _29 would be appropriate) since backend-down takes precedence over delivery loops —
if the backend is down, the delivery loop is caused by infrastructure failure, not by a
broken tool path.

**Recommended prefix:** `_29_stuck_delivery.py`

Checks for the "same message again" signal in the current turn's tool outputs or error context.
Maintains a consecutive-repetition counter on `self.agent`. Fires intervention at threshold 2.
Clears on non-repetition turn.

### No modification to existing files

The `suppress_surgery` flag should be a new agent attribute (`_suppress_surgery_this_turn`)
that the supervisor extension reads and clears. This is the same pattern as `_backend_standby`.

---

## Open Questions for Opus

1. **Where is the "same message again" signal accessible?**
   In `message_loop_end`, the tool outputs from the current turn should be in `loop_data`.
   But this warning is injected by Agent Zero itself into the history, not a tool output.
   What's the cleanest way to detect it — search `loop_data` for the string, or look in
   `self.agent.hist` for the most recent messages?

2. **Suppressing surgery cleanly.**
   The supervisor currently fires Tier 2 surgery based on its own internal counters.
   The cleanest way to suppress it from outside is a flag the supervisor checks before
   executing surgery. Is `_suppress_surgery_this_turn` the right pattern, or should the
   stuck delivery extension communicate via `loop_data` instead?

3. **Intervention message framing.**
   The proposed message above is generic. Should it be more specific — e.g., check whether
   the blocked tool was `code_execution_tool` specifically and name the `response` tool
   explicitly? Or keep it generic to handle any delivery tool failure?

---

## Failure Modes to Consider

**What if surgery already fired before stuck delivery is detected?**
Surgery removes context showing the work is done. The intervention message needs to be
self-sufficient — "deliver your findings as plain text from memory" works even without
the proof-of-completion context, because the agent still has whatever it generated in
short-term reasoning context.

**What if the agent IS in a reasoning loop that looks like a delivery loop?**
The "same message again" signal requires truly identical output. A reasoning loop with
varied outputs won't trigger this. The false positive rate is very low.

**What if the intervention doesn't break the loop?**
After one intervention injection, if the "same message again" signal persists for another
2 turns, escalate: inject a stronger intervention ("Your ONLY valid next action is the
response tool. No other tool calls are permitted.") and set a flag that the tool fallback
chain can use to block the failing tool for this context.

---

## Research Lineage

- Backend Standby Recovery design note — establishes the pattern of pre-supervisor detection
  for categorically different failure types
- Loop Recovery and Memory Surgery design note — establishes the existing supervisor tier system
  this builds on top of
- Field evidence from April 21, 2026 incident: agent completed OpenPlanter analysis (3 reports
  written), entered delivery loop on `code_execution_tool` timeouts, Tier 2 surgery fired and
  removed completion evidence, agent looped identically

---

*The supervisor saves the agent from cognitive failure. Backend standby saves the agent from
infrastructure failure. Stuck delivery recovery saves the agent from being trapped between
completion and communication.*
