# PyWrite Guard — L3 Specification

**Version:** 1.0
**Date:** 2026-04-28
**Status:** Ready for Opus review
**Hook:** `tool_execute_after` (intercepts before tool execution reaches the model)
**Extension file:** `extensions/tool_execute_after/_17_pywrite_guard.py`
**Motivated by:** Two self-improvement cycles in which the agent modified `.py` files at the profile path despite Rule 5 explicitly prohibiting it. The constraint heartbeat (`_17_constraint_heartbeat.py`) addresses the recency decay problem behaviorally. This extension addresses it mechanically — the agent cannot violate what it cannot execute.

**Companion spec:** `specs/CONSTRAINT_HEARTBEAT_SPEC_L3.md` (Layer 1, behavioral)

---

## Problem Statement

The self-improvement agent violated Rule 5 (no `.py` modifications) in both observed cycles. The violation pattern is consistent: the agent reads the rule at session start, performs authorized work, then at turn 20+ modifies a `.py` file as part of an invented "bonus" achievement. The behavioral constraint in program.md is insufficient because:

1. Long-context recency bias reduces rule salience by turn 20+ (addressed by heartbeat)
2. The model's training distribution strongly rewards "impressive" technical output, creating task pressure that overrides distant instructions
3. Even with the heartbeat, a sufficiently motivated model can override a rule it has just been shown

The only reliable solution for a hard constraint is mechanical enforcement: intercept the tool call at the execution boundary and refuse it before the action takes effect.

---

## What This Does

Intercepts `code_execution_tool` and `text_editor` calls before execution. Scans the tool arguments for `.py` file path patterns. If a `.py` write operation is detected, blocks the call and returns a structured refusal message instead of executing.

Read operations on `.py` files are permitted. Only write operations are blocked. The extension does not block `.py` reads, imports, or analysis — only creation, modification, or overwrite.

No LLM calls. No file reads. Pure argument pattern matching.

---

## What This Does NOT Do

- Does not block reading `.py` files (cat, open, inspect, import are permitted).
- Does not block `.py` files in temporary or test directories if explicitly whitelisted.
- Does not prevent the agent from analyzing or describing `.py` file content.
- Does not block non-`.py` file writes (config JSON, skill files, wiki pages, YAML, TOML — all permitted).
- Does not log to the evidence ledger or make any external calls.
- Does not make LLM calls.
- Does not affect any tool other than `code_execution_tool` and `text_editor`.

---

## Research Lineage

- **Observed failure data (2026-04-27, 2026-04-28):** Two cycles. In both, the agent modified profile-path `.py` files. In cycle 1 it modified the repo copy of `_11_belief_state_tracker.py`. In cycle 2 it modified the profile-path copy (the running system). The profile-path modification is the more dangerous failure — it affects live behavior without going through version control or human review.
- **Exocortex design principle:** "Deterministic scaffolding beats probabilistic reasoning where reliability matters." Rule 5 is a reliability constraint — the running extension stack must not be modified by an autonomous agent. Mechanical enforcement is the correct implementation of a reliability constraint.
- **Action Boundary design** (`specs/ACTION_BOUNDARY_DESIGN_NOTE.md`): The existing action boundary handles authorization at the task-intent level (Tier 4 blocks before the agent acts). The PyWrite Guard operates at the tool-execution level — a narrower, later gate that intercepts specific tool calls regardless of intent classification. Both are needed: the action boundary handles broad authorization; the write guard handles a specific, high-consequence action class.

---

## Architecture

### Hook Position

`tool_execute_after` fires after the model has chosen a tool but before execution. The extension receives `tool_name` and the full tool call arguments in `kwargs`. If the guard blocks the call, it modifies the response to return a refusal — the execution does not proceed.

**Note:** Verify the exact hook signature against the Agent Zero source. The hook may be `tool_execute_before` depending on Agent Zero version. The guard must fire before execution, not after.

### Detection Logic

Two tool names are in scope: `code_execution_tool` and `text_editor`.

**For `code_execution_tool`:** Scan the `code` argument for patterns that write to `.py` files:

```python
PY_WRITE_PATTERNS = [
    r"open\s*\([^)]*\.py[^)]*['\"]w['\"]",   # open("file.py", "w")
    r"open\s*\([^)]*\.py[^)]*['\"]a['\"]",   # open("file.py", "a")  
    r"open\s*\([^)]*\.py[^)]*['\"]x['\"]",   # open("file.py", "x")
    r">\s*\S+\.py\b",                          # shell redirect: > file.py
    r"tee\s+\S+\.py\b",                        # tee file.py
    r"cp\s+\S+\s+\S+\.py\b",                  # cp src dest.py
    r"mv\s+\S+\s+\S+\.py\b",                  # mv src dest.py
    r"shutil\.copy[^(]*\([^)]*\.py",           # shutil.copy(..., "x.py")
    r"shutil\.move[^(]*\([^)]*\.py",           # shutil.move
    r"Path\([^)]*\.py[^)]*\)\.write",          # Path("x.py").write_text()
]
```

Any match → block.

**For `text_editor`:** Check the `path` argument (or equivalent field). If it ends in `.py` and the command is `write`, `create`, `insert`, `replace`, or `str_replace` → block. Read commands (`view`, `read`) are permitted.

### Whitelist

An optional `pywrite_guard.allowed_paths` list in config permits specific `.py` paths. Default: empty (all `.py` writes blocked). This is for exceptional cases (e.g., writing to a dedicated scratch directory). The whitelist is an operator escape hatch, not an agent-accessible mechanism.

### Refusal Response

When blocking, the extension returns a structured message injected as the tool result:

```
[PYWRITE_GUARD] Blocked: attempted write to a .py file.

Rule 5 prohibits modifying Python source files. This applies to:
  - Extension files in extensions/
  - Any .py file regardless of directory

Permitted alternatives:
  - Config JSON: /a0/usr/Exocortex/config.json
  - Skill files: /a0/usr/skills/auto-generated/*.md (SKILL.md format)
  - Wiki pages: /a0/usr/Exocortex/wiki/**/*.md
  - Memory saves: memory_save tool

If you believe this block is incorrect, stop and report to the operator.
```

The message is informative: it tells the agent exactly what it tried, why it was blocked, and what alternatives exist. This reduces the chance the agent loops trying variations.

### Logging

Every block emits:

```
[PYWRITE-GUARD] Blocked {tool_name} write to .py file. Path/pattern: {matched_fragment}
```

Every permitted pass-through emits nothing (code_execution_tool calls are frequent; logging clean passes would flood the output).

---

## Configuration

```json
"pywrite_guard": {
    "enabled": true,
    "allowed_paths": [],
    "log_blocks": true
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Master switch. |
| `allowed_paths` | list | `[]` | `.py` paths exempt from blocking. Operator-set only. |
| `log_blocks` | bool | `true` | Emit `[PYWRITE-GUARD]` log line on each block. |

---

## Class Pattern

```python
class PyWriteGuard(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            if tool_name not in ("code_execution_tool", "text_editor"):
                return
            # load config, check enabled
            # extract relevant argument (code or path+command)
            # check against PY_WRITE_PATTERNS or path suffix + write command
            # check whitelist
            # if blocked: inject refusal into response, log, return
        except Exception:
            pass  # never interrupt execution on guard failure
```

**Critical:** If the guard itself fails (exception in pattern matching, missing argument key, etc.), it must fail open — allow the tool call to proceed. A broken guard that silently blocks all tool execution is worse than no guard. The `except Exception: pass` at the outer level ensures this.

---

## Hook Signature Verification Required

Before implementation, verify the `tool_execute_after` hook signature against the current Agent Zero source at `/a0/python/helpers/extension.py` and `agent.py`. Specifically:

1. Confirm the hook name — it may be `tool_execute_before` or `tool_execute_after`
2. Confirm that the hook fires before execution (not after — if after, the write has already happened)
3. Confirm how to inject a refusal (modify `loop_data` response field, or return a value that the hook runner treats as an override)

The existing `_55_memory_classifier.py` (monologue_end) and `_25_evidence_ledger_recorder.py` (tool_execute_after) are pattern sources — read both before implementing.

---

## Testing Criteria

1. **Blocks write via open():** Code containing `open("extensions/foo.py", "w")` is blocked; tool does not execute.
2. **Blocks shell redirect:** Code containing `echo "x" > /a0/usr/extensions/foo.py` is blocked.
3. **Permits read:** Code containing `open("extensions/foo.py", "r")` passes through unblocked.
4. **Permits non-.py writes:** Code writing to `config.json` or a `.md` file passes through.
5. **text_editor write blocked:** `text_editor` call with `path="foo.py"` and command `write` is blocked.
6. **text_editor read permitted:** `text_editor` call with `path="foo.py"` and command `view` passes through.
7. **Whitelist respected:** Path in `allowed_paths` passes through even on write.
8. **Fails open:** With malformed kwargs (missing `code` key), guard does not crash and tool proceeds.
9. **Refusal message content:** Blocked response contains `[PYWRITE_GUARD]`, names the tool, lists permitted alternatives.

---

## Relationship to Action Boundary

The action boundary (`_15_action_boundary.py`) operates at intent classification — it evaluates the task the agent is attempting and can block entire categories of action at Tier 4. The PyWrite Guard operates at tool execution — it intercepts a specific, narrow action class regardless of what the action boundary decided about intent.

These are complementary, not redundant:

| Layer | Gate | Scope | Timing |
|-------|------|-------|--------|
| Action Boundary | Intent-level | Broad task categories | Before agent selects tools |
| PyWrite Guard | Tool-execution | `.py` writes specifically | After tool selected, before execution |

Both should be active. The action boundary catches broad authorization failures. The PyWrite Guard catches the specific `.py` modification failure mode that has appeared twice in production.

---

## Files Modified

| File | Change |
|------|--------|
| `extensions/tool_execute_after/_17_pywrite_guard.py` | New file |
| Agent Zero config or `Exocortex/config.json` | Add `pywrite_guard` section |

No database changes. No new dependencies. No other files modified.
