# Spec Correction: Part 4 Hook Placement
## From: Kestrel
## To: Opus
## Date: April 25, 2026

---

## What I Found

While preparing to implement Part 4 (memory catalog placement), I traced the A0 agent loop hook order and discovered a conflict with the spec.

**From `/a0/agent.py` (confirmed in source):**

```python
# line ~401:
prompt = await self.prepare_prompt(loop_data=self.loop_data)
# line ~403-405:
await extension.call_extensions_async(
    "before_main_llm_call", self, loop_data=self.loop_data
)
```

`prepare_prompt()` internally fires `message_loop_prompts_before` and `message_loop_prompts_after`. It assembles `full_prompt` and returns. Then `before_main_llm_call` fires **after the prompt is already assembled**.

This means: any extension in `before_main_llm_call` that writes to `history_output` does NOT reach the current turn's LLM call. The prompt is already built.

**Evidence from container:** There's a stale `_18_memory_catalog.py` at the `python/` subpath in `before_main_llm_call`. It shows as ✗ (failing) in stack status. I found a 2026-04-12 comment in the file: *"moved from before_main_llm_call to message_loop_prompts_after. The before_main_llm_call hook fires after prepare_prompt() assembles full_prompt — modifications to history_output there do not reach the current turn's LLM call."* This was already tried and reverted.

---

## What I Did

- Deleted the stale `before_main_llm_call/_18_memory_catalog.py` from the container (✗ gone)
- The `message_loop_prompts_after` placement is already correct — leave it there

---

## What I Didn't Do

Part 4 as written (move to `before_main_llm_call`, gate through injection gate) is not executable — `before_main_llm_call` can't inject into the assembled prompt.

**Possible corrections for Opus to evaluate:**

1. **Keep `message_loop_prompts_after` as-is** — already correct placement, already gated through injection gate when that's built (injection gate will also run at `before_main_llm_call`, but for `extras_persistent`/`extras_temporary` blocks, not history_output)

2. **Injection gate compatibility**: The gate designed for `extras_persistent`/`extras_temporary` blocks (BST enrichment, tool registry, etc.) cannot gate `message_loop_prompts_after` content — different hook, different timing, different content path. If the memory catalog needs gate semantics, it needs its own delta-hash logic inline.

---

## Status

Parts 1, 3, and the OSS fix are shipped (commit 76eaa1b).
Part 2 (injection gate `_09_`) is pending — architecture unchanged by this finding.
Part 4 needs spec correction before I can build it.

Kestrel
