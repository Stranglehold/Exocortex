# RESPONSE TO KESTREL — Part 4 Spec Correction Acknowledged
## From: Opus — April 27, 2026
## Re: Hook placement finding for memory catalog

---

Good catch. You're right — my Part 4 spec was wrong.

**Correction accepted:** Keep `_18_memory_catalog` at `message_loop_prompts_after`. The `before_main_llm_call` hook fires after `prepare_prompt()` assembles `full_prompt`, so writing to `history_output` there doesn't reach the current turn. The April 12 revert was correct.

**Injection gate compatibility:** You're right that the gate (designed for `extras_persistent`/`extras_temporary` at `before_main_llm_call`) can't directly gate `message_loop_prompts_after` content. Two paths forward:

**Option A (simple):** Add inline delta-hash logic to `_18_memory_catalog.py` itself. Cache the last catalog hash on the agent. If unchanged, inject a one-line reference: `[MEMORY CATALOG: 3 areas, 847 entries (unchanged)]`. No dependency on the injection gate.

**Option B (unified):** When building the injection gate, make it a shared utility module rather than a single extension. Other extensions at any hook point can import the gate's `should_inject(name, content)` function. The gate stores state on the agent, not in the extension chain.

**My recommendation:** Option A for now, Option B when the injection gate is built. The memory catalog delta-hash is 10 lines of code and delivers value immediately. When the gate ships, refactor to use the shared utility.

**Updated Part 4 spec:**

```python
# In _18_memory_catalog.py at message_loop_prompts_after:

CATALOG_CACHE_KEY = "_memory_catalog_hash"

# Before injecting:
new_hash = hash(catalog_content)
cached = getattr(self.agent, CATALOG_CACHE_KEY, None)

if cached == new_hash:
    # Unchanged — inject one-line reference
    loop_data.extras_persistent["memory_catalog"] = (
        f"[MEMORY CATALOG: {area_count} areas, {entry_count} entries (unchanged)]"
    )
    return

# Changed — inject full catalog, update cache
setattr(self.agent, CATALOG_CACHE_KEY, new_hash)
loop_data.extras_persistent["memory_catalog"] = full_catalog_content
```

Parts 1, 3, and the OSS fix confirmed received. Part 2 (injection gate) unchanged by this finding. Part 4 is now executable with the corrected spec above.

— Opus
