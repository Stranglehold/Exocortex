# Tool Injection Archive Validation
**Date:** 2026-05-13
**Workstream:** B (Session 113)
**Validated by:** Kestrel

---

## What Was Archived

Two extensions removed from all active discovery paths in both containers:

| Extension | Hook | Reason archived |
|-----------|------|-----------------|
| `_16_tool_registry.py` | `before_main_llm_call` | Redundant — Qwen3.6-27B uses native API tool schemas |
| `_95_tiered_tool_injection.py` | `message_loop_prompts_after` | Redundant — same schemas already in API `tools` param |

A third copy of `_16_tool_registry.py` was found unexpectedly in `message_loop_prompts_after/`
in both containers (wrong hook — likely from a prior iteration). Archived separately as
`_16_tool_registry_mlpa.py`.

---

## Containers Cleaned

### exocortex_v16

Discovery paths cleared:
- `/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_16_tool_registry.py` — removed
- `/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/_16_tool_registry.py` — removed
- `/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/_95_tiered_tool_injection.py` — removed
- `/a0/usr/plugins/exocortex/extensions/python/` — cleared (plugin path)

Archive location: `/a0/usr/Exocortex/extensions/archived/`

### exocortex_v17

Same cleanup applied. All tool injection files exist only in `/archived/`.

---

## install_extensions.sh Updates (B8/B9)

`extensions/install_extensions.sh` now tombstones both extensions across three paths:

1. **Profile path** (`/a0/usr/agents/agent0/extensions/python/`) — stale removal section (lines ~54-68)
2. **Plugin path** (`/a0/usr/plugins/exocortex/extensions/python/`) — plugin cleanup section (lines ~76-89)
3. **Exocortex source dir** (`/a0/usr/Exocortex/extensions/`) — new EXO_EXT section (lines ~91-97)

Verification pass already present in script — scans both profile and plugin paths for
un-curated `.py` files and reports any that aren't in the install manifest.

---

## Validation Status

**B10 (prompt token measurement):** Pending — requires running a real A0 investigation task
and capturing server-side token counts from the llama-server log. Expected: ~15-20K fewer
tokens per turn (tool schemas no longer injected as text).

**B11 (tool call accuracy):** Pending — requires observation during B10 test run.
Qwen3.6-27B has been evaluated at 33.3% recovery rate on tool failures (model_eval report).
Removing text injection should not affect accuracy since the model was already using API schemas.
If accuracy degrades: restore from archive (`docker cp` from `/archived/` back to active path).

**Rollback time:** Under 1 minute — files are in `/archived/`, not deleted.

---

## Expected Impact

~15-20K tokens removed per turn on investigation tasks (BST domain = 49 tools injected by
tiered tool injection). At the prior prefill rate (~0.05s/token with MTP + cache fix), this
represents ~750-1000s of prefill reduction per investigation task — significant even after
the cache fix.

The cache fix addresses the dominant bottleneck (full re-processing every turn). Tool injection
archive addresses the secondary bottleneck (large prompt size inflating first-turn prefill).
Both are needed for acceptable investigation task performance.
