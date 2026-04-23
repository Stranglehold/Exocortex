# SCOPE FOR REVIEW — Stuck Delivery Recovery
## From: Kestrel — April 21, 2026
## Re: New failure mode: agent completes task, can't report it

---

Opus,

Second incident today. First was the backend-down cascade (already built and deployed).
This one is different and needs its own systemic fix.

**What happened:**
Agent completed an OpenPlanter architectural analysis — wrote 3 report files to workdir.
Then entered a repetition loop trying to deliver the result via `code_execution_tool`.
Tool timed out. Supervisor fired Tier 2 surgery. Surgery removed the context showing the
work was done. Agent rediscovered the files and looped identically. Jake watched it happen
and said: permanent solutions, not manual intervention.

**The new failure mode: stuck delivery.**
The agent succeeded at the task. It can't report the result. This is categorically different
from a reasoning loop (stuck mid-task) and from a backend-down failure (infrastructure).
Surgery is the wrong intervention — it makes delivery loops worse by removing completion
evidence.

**The concrete signal:**
Agent Zero emits `"You have sent the same message again. You have to do something else!"`
when its deduplication check fires on identical consecutive output. This is unambiguous.
Two consecutive turns with this signal = stuck delivery.

Design note is at:
`specs/STUCK_DELIVERY_RECOVERY_DESIGN_NOTE.md`

You should be able to read it directly via MCP. Three open questions I left for you:

1. **Where is the "same message again" signal accessible** from `message_loop_end`?
   Is it in `loop_data`, or do I need to search `self.agent.hist` for recent messages?

2. **Cleanest way to suppress Tier 2 surgery from outside the supervisor.**
   My proposal: `_suppress_surgery_this_turn` flag on `self.agent`, checked and cleared
   by the supervisor before executing surgery. Is that the right pattern, or should this
   go through `loop_data`?

3. **Intervention message framing** — generic vs. tool-specific.
   Should the injection name `code_execution_tool` specifically and say "use response tool,"
   or stay generic to handle any delivery tool failure?

The implementation pattern is the same as `_28_backend_standby.py` — pre-supervisor detection
in `message_loop_end`, agent attribute flag, targeted intervention via `agent.intervention`.
Prefix `_29_stuck_delivery.py` puts it after backend standby but before the supervisor.

---

— Kestrel
