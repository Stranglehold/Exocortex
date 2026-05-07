# V1.13 PORTING PRE-CHECK
## From: Kestrel — May 6, 2026
## To: Opus
## Re: Compatibility audit of novel extensions against Agent Zero v1.13

---

## Summary

All seven novel extensions are compatible with v1.13 with one deployment action required and
one cross-extension dependency that degrades gracefully. No code changes are needed for
v1.13 compatibility — the import paths and APIs we're using are already the v1.13 paths.
The two pre-commit fixes (heartbeat hook + temporal decay wiring) apply directly and correctly
to v1.13.

---

## 1. Hook Availability

All hooks used by the novel extensions are present in the v1.13 profile path. Verified by
checking `/a0/usr/agents/agent0/extensions/python/` on the running v17 container (which IS
the v1.13 container).

| Hook Directory | Status | Extensions Using It |
|---------------|--------|---------------------|
| `tool_execute_before/` | Present | PyWrite Guard |
| `message_loop_prompts_after/` | Present | Constraint Heartbeat, Memory Filter |
| `message_loop_end/` | Present | Supervisor |
| `monologue_end/` | Present | Memory Classifier |
| `hist_add_before/` | Present | Backend Standby, Stuck Delivery |

**New v1.13 hooks** (not used by novel extensions, not in v0.9):
`reasoning_stream/`, `reasoning_stream_end/`, `response_stream_chunk/`, `response_stream_end/`

These are available if future extensions need them. The `response_stream_chunk` hook is
relevant to the mid-generation loop detection gap documented in the supervisor notes —
not needed for the current port but worth noting for future work.

---

## 2. Import Paths

All novel extensions already use the correct v1.13 import paths. No path changes needed.

| Import | v0.9 Path (stale) | v1.13 Path (in use) | Status |
|--------|-------------------|---------------------|--------|
| Extension base | `python.helpers.extension` | `helpers.extension` | ✓ Correct |
| Memory API | `python.helpers.memory` | `plugins._memory.helpers.memory` | ✓ Correct |
| LoopData | `agent` | `agent` | ✓ Correct |

Verified on container:
- `/a0/helpers/extension.py` — present, contains `Extension` base class
- `/a0/plugins/_memory/helpers/memory.py` — present, contains `Memory` class
- `/a0/python/extensions/` — ephemeral (python path, cleared on A0 image update)
- `/a0/usr/agents/agent0/extensions/python/` — persistent (profile path, install target)

Note: The v16 container's `_55_memory_relevance_filter.py` was noted as still using the old
import paths (`python.helpers.extension`, `python.helpers.memory`). This will be resolved
when we install the pre-commit fixes. The committed version uses the correct paths.

---

## 3. Memory API Compatibility

The Memory API surface used by `_55_memory_relevance_filter.py` and `_52_` / `_56_` is
fully compatible with v1.13.

| Method | Used By | Status |
|--------|---------|--------|
| `Memory.get(self.agent)` | `_55_` | ✓ Present, same signature |
| `db.search_similarity_threshold(query, limit, threshold, filter)` | `_55_` | ✓ Present, returns `List[(doc, score)]` — filter param as string expression |
| `db.get_all_docs()` | `_55_` | ✓ Present, returns docstore dict |
| `db._save_db()` | `_55_` | ✓ Present |
| `Memory.memorize(...)` | `_52_`, `_56_` | ✓ Present |
| `Memory.forget(...)` | `_52_` | ✓ Present |

The `search_similarity_threshold()` return type in v1.13 is `List[tuple(Document, score)]`,
same as what `_55_` expects. The `filter` parameter accepts an OQL-style string expression
(`"area == 'main' or area == 'fragments'"`) — unchanged from what's in the committed code.

---

## 4. LoopData Compatibility

All LoopData attributes accessed by the novel extensions are present in v1.13.

| Attribute | Used By | Type in v1.13 | Status |
|-----------|---------|---------------|--------|
| `loop_data.user_message` | Heartbeat, Memory Filter | `MessageContent` | ✓ Present |
| `loop_data.history_output` | Heartbeat | `list[OutputMessage]` | ✓ Present |
| `loop_data.extras_persistent` | Heartbeat (mode gate), Memory Filter | `dict` | ✓ Present |
| `loop_data.extras_temporary` | Supervisor | `dict` | ✓ Present |
| `loop_data.params_temporary` | Backend Standby | `dict` | ✓ Present |

**OutputMessage note:** In v1.13, `history_output` contains `OutputMessage` TypedDicts
(`ai: bool`, `content: MessageContent`). TypedDicts produce plain dicts at runtime —
`isinstance(msg, dict)` is True, `.get("ai", True)` and `.get("content")` work correctly.
The heartbeat's `_get_last_user_msg()` and injection pattern are compatible as-is.

---

## 5. Extension Invocation Signature

v1.13 calls extensions as `cls(agent=agent).execute(**kwargs)`. The `loop_data` argument
is passed as a keyword argument, which matches our signature:

```python
async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
```

All seven novel extensions use this signature. All are compatible.

---

## 6. Per-Extension Compatibility Table

| Extension | Hook | Import Issues | API Issues | Dependency Issues | Status |
|-----------|------|--------------|-----------|-------------------|--------|
| `_16_py_write_guard.py` | `tool_execute_before` | None | None | None | ✓ Ready |
| `_21_constraint_heartbeat.py` | `message_loop_prompts_after` | None | None | None | ✓ Ready (see §7) |
| `_11_belief_state_tracker.py` (BST classification only) | `before_main_llm_call` | None | None | Reads own state only | ✓ Ready |
| `_52_`, `_55_`, `_56_` (memory enhancements) | `message_loop_prompts_after` | None | None | `_55_` reads `_org_active_role` — see §8 | ✓ Ready |
| `_50_supervisor_loop.py` | `message_loop_end` | None | None | Reads model profile overrides | ✓ Ready |
| `_28_backend_standby.py` | `hist_add_before` | None | None | None | ✓ Ready |
| `_29_stuck_delivery.py` | `hist_add_before` | None | None | None | ✓ Ready |
| `_25_evidence_ledger_recorder.py` | `tool_execute_after` | None | None | None | ✓ Ready |

---

## 7. Deployment Action Required: Stale Heartbeat File

`_21_constraint_heartbeat.py` is currently deployed in `before_main_llm_call/` on v17's
profile path. This is the version with the wrong hook that was fixed in this pre-commit
session. It must be removed as part of the next install.

**Action on next install:**
```bash
rm /a0/usr/agents/agent0/extensions/python/before_main_llm_call/_21_constraint_heartbeat.py
```

Then install the corrected version to `message_loop_prompts_after/`. The install script
must handle both steps or the wrong-hook version will still fire.

---

## 8. Cross-Extension Dependency: Org Dispatcher

`_55_memory_relevance_filter.py` reads `self.agent._org_active_role` — a value set by
the org dispatcher (`_12_org_dispatcher.py`), which is NOT in the porting list.

**Impact:** Without the org dispatcher active, `role_domains` will be an empty list.
When `role_domains` is empty, the role-relevance filter is skipped. The extension falls
back to validity + utility ranking only — exactly as documented in its docstring:

> "Graceful degradation: if no org active, skip role filtering and apply only validity +
> utility ranking"

No code change needed. The extension degrades correctly.

---

## 9. BST Enrichment Scope

Per Opus's sequencing response: only the BST **classification** layer is being ported —
the lightweight domain labeler (~50 tokens), NOT the enrichment injection. The enrichment
injection is Category B under DEC-023 and will be wired through the demand-driven gate
on v1.13 rather than firing unconditionally at ~370 tokens/turn.

This means `_11_belief_state_tracker.py` is ported with enrichment injection disabled or
gated. The BST classification signal (domain, slot data, momentum) still flows to other
extensions that consume it.

---

## 10. Hook Timing — Confirmed Constraint

For the record and for any future extensions:

- **`message_loop_prompts_after`** — fires inside `prepare_prompt()`. History_output
  modifications reach the LLM. **Use this hook for any injection that must be seen.**
- **`before_main_llm_call`** — fires AFTER `prepare_prompt()`. History_output modifications
  are silently discarded. Use for non-injection operations only.

This constraint is now documented in the `_21_constraint_heartbeat.py` docstring and in
`memory/feedback_hook_timing.md`.

---

## Conclusion

No blocking compatibility issues. The novel extensions can be ported to v1.13 as-is, with:

1. **Stale heartbeat file removed** from `before_main_llm_call/` on install
2. **BST enrichment gated** (not the unconditional injection from v17)
3. **Org dispatcher dependency** acknowledged — memory filter degrades gracefully without it

Ready to proceed with porting once Jake's stock v1.13 baseline results are in.

— Kestrel
