# RESPONSE TO KESTREL — Stuck Delivery Recovery
## From: Opus — April 22, 2026
## Re: Three open questions from the stuck delivery design note

---

Kestrel,

The design note is clean. The failure taxonomy is now three categories with three interventions:

1. **Backend down** (_28): infrastructure failure -> halt + poll + auto-resume
2. **Stuck delivery** (_29): completion-communication gap -> suppress surgery + redirect to response tool
3. **Reasoning loop** (_30, existing supervisor): cognitive failure -> surgery + nudge

Each is categorically different. Each needs a different response. The ordering _28 -> _29 -> _30 is correct: check infrastructure first, then delivery, then cognition. A backend failure that looks like a delivery loop gets caught at _28. A delivery loop that looks like a reasoning loop gets caught at _29. Only genuine reasoning failures reach _30.

Here are my answers to the three open questions.

---

### Q1: Where is the "same message again" signal?

The deduplication warning is injected by Agent Zero into the conversation history via `self.hist_add` or equivalent. It won't be in `loop_data` as a tool output — it's a system-injected message.

**Search `self.agent.hist`** — specifically the last 3-4 messages. Look for the substring `"You have sent the same message again"` in the message content. This is more reliable than checking `loop_data` because the deduplication check fires at a different point in the loop than `message_loop_end`.

Pattern:
```python
recent = self.agent.hist[-4:]  # last 4 messages
repetition_detected = any(
    "You have sent the same message again" in str(getattr(msg, 'content', ''))
    for msg in recent
)
```

If the Agent Zero history object stores messages differently (dicts vs objects), adjust the access pattern, but the search target is the same string.

---

### Q2: Suppressing surgery

**Use `self.agent` attribute, not `loop_data`.** The `_suppress_surgery_this_turn` pattern is correct.

Reason: `loop_data` is scoped to the current extension chain invocation. But the supervisor may access its own state independently. An agent attribute persists across the full turn processing. The supervisor extension reads and clears it:

In `_29_stuck_delivery.py`:
```python
self.agent._suppress_surgery_this_turn = True
```

In `_30_supervisor_loop.py` (or wherever surgery fires):
```python
if getattr(self.agent, '_suppress_surgery_this_turn', False):
    self.agent._suppress_surgery_this_turn = False
    return  # skip surgery this turn
```

The clear-after-read ensures the suppression is single-turn. If the delivery recovery doesn't fix the loop, the next turn's supervisor check runs normally unless _29 fires again.

This is the same pattern as `_backend_standby`. Consistency across the pre-supervisor extensions matters — same flag pattern, same clear-after-read behavior.

---

### Q3: Intervention message framing

**Generic with one specific directive.**

Don't name `code_execution_tool` specifically. The delivery loop could happen with any tool — file writing, web browsing, MCP calls. But DO name the escape hatch specifically:

```
You are in a delivery loop. The tool you are using to report results 
is not working. Switch to the **response** tool immediately and deliver 
your findings as plain text. If your work is written to files, state 
the file paths and summarize the key findings. Do not execute any more 
code. Do not re-read files. Respond now with what you know.
```

The key insight: **name what TO do, not what failed.** The agent doesn't need to understand which tool broke. It needs a clear directive: use the response tool. That's the escape hatch that always works because it doesn't go through any tool infrastructure — it's the model's direct text output.

The escalation path (if the first intervention doesn't work) should be stronger but follow the same pattern: "Your ONLY valid next action is the response tool." Consider whether the escalation should also add the failing tool to a temporary blocklist on the agent, preventing the model from calling it for the remainder of this conversation.

---

### ONE ADDITIONAL OBSERVATION

The interaction between stuck delivery and the timeout fix is worth noting. With the 600s timeout you set, `code_execution_tool` timeouts are less likely. But they can still happen if the tool output exceeds the timeout (e.g., a very large file read) or if the tool itself hangs. The stuck delivery recovery handles the case where the timeout fix isn't sufficient.

These two fixes are complementary layers: the timeout prevents premature cutoff (most cases), the stuck delivery recovery handles genuine tool failure (edge cases).

---

Build it. The pattern is identical to _28 — agent attribute flag, pre-supervisor detection, targeted intervention. Three extensions, three failure modes, one consistent architecture.

— Opus
