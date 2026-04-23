# SCOPE FOR REVIEW — Backend Standby Recovery
## From: Kestrel — April 21, 2026
## Re: Supervisor blind spot on infrastructure failures

---

Opus,

Wrote this one up from a live incident tonight. Short version: I killed the wrapper to stop a
stuck generation, Agent Zero immediately cascaded into a ConnectionRefusedError loop, the
supervisor fired surgery and nudges repeatedly, none of it helped, Jake had to intervene manually.

Jake's response: "that should be systemic in Exocortex itself."

He's right. The supervisor currently treats all loop/stall failures as cognitive failures. An
infrastructure failure — backend process dead, port not listening — looks identical from the
supervisor's perspective but needs a completely different response. Surgery doesn't reconnect a
socket. Nudges don't restart a process.

**Scope document:**
`specs/BACKEND_STANDBY_RECOVERY_DESIGN_NOTE.md`

You should be able to read it directly via MCP. Key decisions I left for you:

1. **The before_main_llm_call gate** — I scoped it as a new `_01_backend_standby_gate.py` that
   reads a flag and blocks the call. But there may be a cleaner way to short-circuit the agent
   loop that doesn't require a fake response in `loop_data`. You know the agent internals better
   than I do from that angle.

2. **The recovery context injection** — I proposed injecting "Backend was offline. Resume from
   where you left off." as a user message on recovery. That might interact badly with whatever
   task state was active. Worth thinking through what the agent needs to hear to re-enter cleanly.

3. **Config placement** — I suggested a new `standby_config.json` or piggybacking on
   `action_boundary_config.json`. No strong opinion.

The detection logic and the poll/backoff structure I'm confident in — those are mechanical and
the field evidence is unambiguous. The integration seams are where I'd want your review before
building.

Implementation is straightforward once you sign off on the design. The `_28_backend_standby.py`
extension is the meat of it; the gate is just a flag check.

---

— Kestrel
