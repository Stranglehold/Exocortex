# ARTIFACT_REGISTRY_SPEC_L3.md
# Cross-Context Artifact Registry: Filesystem Write Tracking Across API Boundaries

*Specification Level 3 — Ready for Implementation*
*Evidence basis: ST-006 stress test (March 2026), C5 gap evaluation (Round 2 context reset)*
*Extends: Orientation Stack Wave 2 (_49_reasoning_state_update.py, _13_reasoning_state.py)*
*Derived from: Research-Driven Design Methodology (March 2026)*

---

## 1. What This Is

The Artifact Registry adds a single new field — `artifacts` — to the reasoning state and a companion
detection pass that scans tool arguments for file-write patterns. When the API context resets (conversation
boundary), the artifacts list is written to staging.jsonl so the next context can read it and tell the
agent exactly which files exist on disk from prior work.

This is the minimal fix for the C5 gap: the agent loses track of files it created when the API context
boundary fires, and searches the wrong directories or rebuilds from scratch. The fix provides structured
persistence for file paths only. Everything else about the reasoning state architecture is unchanged.

---

## 2. What This Does NOT Do

- Does NOT reconstruct the full reasoning state (theory, tried, current, open) from staging across
  context resets. Those fields survive in-context only — this spec extends Wave 2 precisely at the
  artifact gap, not at a general cross-context state reconstruction problem.
- Does NOT store file contents, checksums, or binary data. Paths and one-line descriptions only.
- Does NOT validate that tracked files still exist on disk. It records writes, not filesystem state.
- Does NOT track files created via `memory_save`, shell scripts invoked without a heredoc pattern,
  or writes performed inside subagent containers.
- Does NOT integrate with `_10_session_init.py`'s injection pipeline. `_10` injects on first turn
  only; artifacts must be available every turn.
- Does NOT replace tool use. The agent must still call `code_execution_tool` to verify a file's
  contents. The registry tells it where to look.
- Does NOT require changes to staging.jsonl format. Uses a new `category == "artifact"` entry type
  that existing readers silently skip (they filter on category).

---

## 3. Evidence Basis

**ST-006, Round 2 (context ERZ8bCQH):** Agent lost state at the API conversation boundary. It
acknowledged "I don't have context from this conversation about what was started." It searched
`/a0/usr/workdir/` — a reasonable default — but the GEPA files were in `/a0/skills/gepa/`. LOOP
DETECTED fired once on a repeated `find /a0/usr/workdir` call. Agent rebuilt from scratch rather
than locating prior work. Total cost: ~10 turns and one supervisor intervention.

Root cause: `_13_reasoning_state.py` reads only `agent._reasoning_state`, which is in-memory. The
API context reset cleared the in-memory attribute. `_49_reasoning_state_update.py` writes to
staging.jsonl only on compression events (history shrinkage), not on API context resets. File
paths created before the boundary were not in staging. Nothing told the new context where files
were.

**ST-005 comparison baseline:** Stock Agent Zero (no Exocortex) showed Type 3 loops (identical dead-
end recycling) on tool failures. Wave 2 eliminated Type 3 and reduced Type 2. The C5 gap is a
different failure mode: not failed-approach recycling, but lost-path-knowledge at context boundaries.

---

## 4. Design Decisions

### 4.1 Extend `_empty_state()` with `artifacts: []`

The `artifacts` list lives inside `agent._reasoning_state` alongside the existing fields. This keeps
all session state in one place, keeps `_13` as the single injection point, and requires no new agent
attributes.

Rationale: The alternative (separate `agent._artifact_registry` attribute) would require `_13` to
read from two sources and adds an additional attribute lifecycle to manage.

### 4.2 Detect file writes from tool_args, not tool_results

`_get_last_tool_pair()` returns the result side only. File path information lives in the command that
was executed (`tool_args.code`), not in the output. Artifact detection must walk AI messages in history
to find `code_execution_tool` calls with `runtime == "terminal"` or `runtime == "python"` and extract
paths from the code content.

Rationale: Tool results sometimes confirm a write ("exit code 0"), but they do not contain the
destination path. The source of truth is the command itself.

### 4.3 Write artifact entries to staging.jsonl immediately on new detections

The existing reasoning state writes to staging only on context compression (history shrinkage ≥ 35%).
API context resets do not trigger compression detection — the new context starts with a short history,
not a shrunk one. Therefore artifact entries must be written on every turn where new artifacts are
detected, not only on compression.

### 4.4 `_13` reads staging.jsonl once on first turn to bootstrap artifacts

On first turn, `agent._reasoning_state` is None. Currently `_13` returns immediately when state is
None. The new behavior: when state is None, read staging.jsonl for `category == "artifact"` entries,
reconstruct the artifacts list, and continue with injection.

The bootstrap sets `agent._reasoning_state["artifacts"]` so `_49` has the prior list on turn 1 and
can correctly detect only new paths (deduplication). This also means `_13`'s existing guards
("if not state: return") must be updated to allow injection of artifacts even with an otherwise-empty
state.

Rationale: `_13` reading staging.jsonl once per session is the same pattern `_10` already uses.
The cost is one file read on first turn when artifacts are present. All subsequent turns read from
in-memory state.

### 4.5 `_10_session_init.py` unchanged

`_10` already surfaces staging observations on first turn. Adding a new `artifact` category handler
to `_10` would surface artifacts there too — but `_10`'s output is a general `[STAGING — session
continuity]` block that the model may not associate with "files I can use right now." The `_13`
path injects artifacts adjacent to the reasoning state, which is the correct framing: "here is what
you were working on, and here are the files you already built."

---

## 5. Schema Changes

### 5.1 `_empty_state()` addition

```python
def _empty_state() -> dict:
    return {
        "step": 0,
        "theory": "",
        "tried": [],       # list of {"approach": str, "outcome": str}
        "current": "",
        "open": "",
        "artifacts": [],   # NEW: list of {"path": str, "description": str, "step": int}
    }
```

Default: empty list. Type: `list[dict]`. Max entries: 12 (configurable). Deduplication key: `path`.

### 5.2 staging.jsonl artifact entry format

```json
{
  "category": "artifact",
  "status": "active",
  "text": "/a0/skills/gepa/gepa_framework.py — Python module (step 7)",
  "why": "File written during this session — path preserved across context reset",
  "importance": 0.9,
  "reactivation_count": 0,
  "created": 1741000000.0,
  "_artifact_entry": true,
  "path": "/a0/skills/gepa/gepa_framework.py",
  "description": "Python module",
  "artifact_step": 7
}
```

Fields:
- `category`: `"artifact"` — skipped by `_10_session_init`'s category filter (intention/relational/observation/canary)
- `_artifact_entry`: `True` — deduplication marker, same pattern as `_rs_entry`
- `path`: canonical filesystem path
- `description`: one-line file type description
- `artifact_step`: reasoning state step at which the file was created

Deduplication: on write, existing entries for the same `path` are dropped before re-appending
(same read-filter-rewrite pattern as `_write_to_staging`).

---

## 6. `_49_reasoning_state_update.py` Changes

### 6.1 New constants

```python
MAX_ARTIFACTS   = 12   # Maximum tracked files before oldest are dropped
# Patterns for detecting file writes in terminal commands
HEREDOC_WRITE_RX = re.compile(r'cat\s+>\s+(/[^\s<]+)', re.MULTILINE)
TEE_WRITE_RX     = re.compile(r'\btee\s+(/[^\s|&;]+)')
# Pattern for detecting file writes in Python code
PY_OPEN_WRITE_RX = re.compile(r'open\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']w')
```

### 6.2 New function: `_detect_new_artifacts(history, existing_paths, current_step)`

```python
def _detect_new_artifacts(
    history: list,
    existing_paths: set,
    current_step: int,
) -> list[dict]:
    """
    Walk AI messages in history for code_execution_tool calls.
    Extract file paths written via heredoc, tee, or open(..., 'w').
    Return only paths not already in existing_paths.
    """
    new_artifacts = []
    seen_this_scan = set()

    for msg in history:
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            continue
        content = msg.get("content", "")
        tool_name = _parse_tool_name(content)
        if tool_name != "code_execution_tool":
            continue
        args = _parse_tool_args(content)
        runtime = args.get("runtime", "")
        code = args.get("code", "")
        if not code:
            continue

        paths = []
        if runtime == "terminal":
            paths += HEREDOC_WRITE_RX.findall(code)
            paths += TEE_WRITE_RX.findall(code)
        elif runtime == "python":
            paths += PY_OPEN_WRITE_RX.findall(code)

        for path in paths:
            path = path.strip()
            if not path.startswith("/"):
                continue
            if path in existing_paths or path in seen_this_scan:
                continue
            seen_this_scan.add(path)
            description = _path_to_description(path)
            new_artifacts.append({
                "path": path,
                "description": description,
                "step": current_step,
            })

    return new_artifacts
```

### 6.3 New helper: `_path_to_description(path)`

```python
def _path_to_description(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".py":   "Python module",
        ".sh":   "Shell script",
        ".json": "JSON config",
        ".md":   "Markdown doc",
        ".txt":  "Text file",
        ".yaml": "YAML config",
        ".yml":  "YAML config",
    }.get(ext, "File")
```

### 6.4 New function: `_write_artifact_entries(artifacts)`

```python
def _write_artifact_entries(artifacts: list[dict]) -> None:
    """
    Write or update artifact entries in staging.jsonl.
    One entry per file path. Replaces existing entry for same path.
    """
    try:
        os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)
        updated_paths = {a["path"] for a in artifacts}

        existing = []
        if os.path.exists(STAGING_PATH):
            with open(STAGING_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        # Drop stale entries for paths we're updating
                        if e.get("_artifact_entry") and e.get("path") in updated_paths:
                            continue
                        existing.append(line)
                    except Exception:
                        existing.append(line)

        for a in artifacts:
            entry = {
                "category": "artifact",
                "status": "active",
                "text": f"{a['path']} — {a['description']} (step {a['step']})",
                "why": "File written during this session — path preserved across context reset",
                "importance": 0.9,
                "reactivation_count": 0,
                "created": time.time(),
                "_artifact_entry": True,
                "path": a["path"],
                "description": a["description"],
                "artifact_step": a["step"],
            }
            existing.append(json.dumps(entry))

        with open(STAGING_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(existing) + "\n")
    except Exception:
        pass
```

### 6.5 Integration into `execute()` method

After the existing tool-pair update and AI-text extraction (lines ~108–117 in current code), add:

```python
# Detect and register new file artifacts
existing_paths = {a["path"] for a in state.get("artifacts", [])}
new_artifacts = _detect_new_artifacts(
    loop_data.history_output or [],
    existing_paths,
    state["step"],
)
if new_artifacts:
    artifact_list = state.get("artifacts", [])
    artifact_list.extend(new_artifacts)
    # Trim to max
    if len(artifact_list) > MAX_ARTIFACTS:
        artifact_list = artifact_list[-MAX_ARTIFACTS:]
    state["artifacts"] = artifact_list
    setattr(self.agent, REASONING_KEY, state)
    _write_artifact_entries(new_artifacts)
    self.agent.context.log.log(
        type="info",
        content=(
            f"[REASON-STATE] New artifacts: "
            + ", ".join(a["path"] for a in new_artifacts)
        ),
    )
```

Add to the existing log line: `f"artifacts={len(state.get('artifacts', []))}"`.

---

## 7. `_13_reasoning_state.py` Changes

### 7.1 New imports

Add at top:
```python
import json
import os
```

Add constant:
```python
STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
```

### 7.2 New function: `_load_artifacts_from_staging()`

```python
def _load_artifacts_from_staging() -> list[dict]:
    """
    Read staging.jsonl and return all active artifact entries.
    Called once on first turn when agent._reasoning_state is None.
    """
    artifacts = []
    try:
        if not os.path.exists(STAGING_PATH):
            return artifacts
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if (
                        e.get("_artifact_entry")
                        and e.get("status") == "active"
                        and e.get("path")
                    ):
                        artifacts.append({
                            "path": e["path"],
                            "description": e.get("description", "File"),
                            "step": e.get("artifact_step", 0),
                        })
                except Exception:
                    pass
    except Exception:
        pass
    return artifacts
```

### 7.3 Updated `execute()` — bootstrap on first turn

Replace the current early return block:
```python
# BEFORE (current code, lines 42-44)
state = getattr(self.agent, REASONING_KEY, None)
if not state:
    return
```

With:
```python
state = getattr(self.agent, REASONING_KEY, None)
if not state:
    # First turn: attempt artifact bootstrap from staging
    prior_artifacts = _load_artifacts_from_staging()
    if not prior_artifacts:
        return
    # Build minimal state to carry artifacts into this context
    from extensions.message_loop_end._49_reasoning_state_update import _empty_state
    state = _empty_state()
    state["artifacts"] = prior_artifacts
    setattr(self.agent, REASONING_KEY, state)
    self.agent.context.log.log(
        type="info",
        content=f"[REASON-INJ] Bootstrapped {len(prior_artifacts)} artifact(s) from staging",
    )
```

**Note on import:** The `_empty_state` import from `_49` avoids duplicating the schema. If the
circular import path causes issues (both files are extensions, not modules), inline the minimal
dict instead:
```python
state = {"step": 0, "theory": "", "tried": [], "current": "", "open": "", "artifacts": prior_artifacts}
```

### 7.4 Updated `_format_block()` — add `[ARTIFACTS]` section

Add after the `open_q` line:

```python
artifacts = state.get("artifacts", [])
if artifacts:
    lines.append("[ARTIFACTS — files created this session]")
    for a in artifacts:
        lines.append(f"  {a['path']} ({a['description']})")
    lines.append(
        "These files exist on disk. Check them before rebuilding."
    )
```

The `[ARTIFACTS]` section is injected only when the list is non-empty. It appears below the
reasoning state content, above the update instruction line.

### 7.5 Guard update — inject artifacts even with otherwise empty state

The current guard (line 53):
```python
if not current and not tried and not theory:
    return
```

Must also check artifacts:
```python
if not current and not tried and not theory and not state.get("artifacts"):
    return
```

---

## 8. Artifact Detection Scope and Limits

### Files detected

| Pattern | Example | Detected |
|---------|---------|---------|
| `cat > /path/file.py << 'EOF'` | Terminal heredoc | Yes |
| `cat > /path/file.py << EOF` | Terminal heredoc (unquoted) | Yes |
| `tee /path/file.py` | Terminal tee | Yes |
| `echo '...' > /path/file.py` | Echo redirect | Yes (requires file extension) |
| `printf '...' > /path/file.py` | Printf redirect | Yes (requires file extension) |
| `open('/path/file.py', 'w')` | Python write | Yes |
| `open("/path/file.py", "w")` | Python write (double-quote) | Yes |

### Files NOT detected

| Pattern | Reason |
|---------|--------|
| `echo "..." > /path/noext` | Redirect to path with no file extension — excluded to avoid false positives on debug redirects |
| `with open(...) as f: f.write(...)` | Multi-line context not required; the `open(..., 'w')` pattern captures the open call regardless of assignment form |
| Files created inside subagent containers | `loop_data.history_output` contains only this context's history |
| `cp`, `mv` operations | Not file creation events |
| Relative paths | Only absolute paths starting with `/` are tracked |

### False positive handling

Regex patterns are conservative (require `/` prefix, avoid backtracking). Tracking a path that
doesn't end up written is low-cost: the agent checks the file and finds it missing, which is
recoverable. Missing a written file is the failure mode we're preventing.

---

## 9. Configuration

No new config section required. Uses existing `REASONING_KEY = "_reasoning_state"` and
`STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"` constants. New constant `MAX_ARTIFACTS = 12`
is defined in `_49`.

**Graceful degradation:**
- `_detect_new_artifacts` catches all exceptions internally — if regex fails, returns empty list
- `_write_artifact_entries` catches all exceptions — staging.jsonl write failure is silent
- `_load_artifacts_from_staging` catches all exceptions — returns empty list on any error
- If `artifacts` field is missing from state dict (old state format), `state.get("artifacts", [])` returns `[]`

---

## 10. Testing Criteria

All assertions are specific and measurable.

### TC-01: Detection fires on terminal heredoc

Setup: send message "create a file /tmp/test_artifact.py containing `print('hello')`"
Expected: agent uses `code_execution_tool` with `runtime=terminal` and a heredoc pattern
Assertion: `docker logs flamboyant_bell --since 5m | grep "REASON-STATE" | grep "test_artifact.py"`
returns a line with the path.

### TC-02: Artifact written to staging.jsonl

After TC-01:
Assertion: `docker exec flamboyant_bell grep "test_artifact.py" /a0/usr/Exocortex/staging.jsonl`
returns a JSON line with `"category": "artifact"` and `"path": "/tmp/test_artifact.py"`.

### TC-03: Artifact survives context reset

Precondition: TC-02 passed (artifact in staging.jsonl).
Action: restart Agent Zero container (`docker restart flamboyant_bell`).
Action: send "where is the test_artifact.py file?"
Expected: agent response references `/tmp/test_artifact.py` without searching.
Assertion: response contains the path within 2 turns. No `find /a0/usr/workdir` calls visible
in docker logs.

### TC-04: Bootstrap log fires on first turn with prior artifacts

Action: after TC-02, send any message to a fresh context.
Assertion: `docker logs flamboyant_bell --since 1m | grep "REASON-INJ"` contains
`"Bootstrapped N artifact(s) from staging"` where N ≥ 1.

### TC-05: `[ARTIFACTS]` block appears in injection

Precondition: TC-04 passed (artifacts in in-memory state).
Assertion: `docker logs flamboyant_bell --since 1m | grep "REASON-INJ"` shows injection fired
(step N, artifacts=N). Verify `[ARTIFACTS]` section visible in model's context by asking the
agent to describe its current reasoning state.

### TC-06: No LOOP DETECTED on path search after context reset

Run a modified ST-006 Wave 2: build a file in context A, reset context (restart container),
send "continue building gepa_framework.py" in context B.
Assertion: `docker logs flamboyant_bell --since 30m | grep "LOOP DETECTED" | wc -l` returns 0.
Assertion: agent locates the prior file within 2 turns.

### TC-07: Max artifacts cap enforced

Create 13+ files in sequence.
Assertion: `state["artifacts"]` length never exceeds 12 (oldest are dropped).

### TC-08: Python runtime open() detected

Send: "write a config file to /tmp/config.json" — agent uses Python runtime with `open()`.
Assertion: path appears in `docker logs ... | grep "REASON-STATE" | grep "config.json"`.

---

## 11. Files to Create/Modify

| File | Action | Summary |
|------|--------|---------|
| `extensions/message_loop_end/_49_reasoning_state_update.py` | MODIFY | Add `artifacts: []` to `_empty_state()`, add detection constants, add `_detect_new_artifacts()`, `_path_to_description()`, `_write_artifact_entries()`, integrate into `execute()` |
| `extensions/before_main_llm_call/_13_reasoning_state.py` | MODIFY | Add `json`, `os` imports, add `STAGING_PATH` constant, add `_load_artifacts_from_staging()`, update `execute()` bootstrap, update `_format_block()` with `[ARTIFACTS]` section, update empty-state guard |

No new files. No schema changes to staging.jsonl format (new entry type is additive).
No changes to `_10_session_init.py`, `_14_situational_orientation.py`, or `_50_supervisor_loop.py`.

---

## 12. Deployment

```bash
# After modifying both files locally:
docker cp extensions/message_loop_end/_49_reasoning_state_update.py \
  flamboyant_bell:/a0/usr/agents/agent0/extensions/message_loop_end/_49_reasoning_state_update.py

docker cp extensions/before_main_llm_call/_13_reasoning_state.py \
  flamboyant_bell:/a0/usr/agents/agent0/extensions/before_main_llm_call/_13_reasoning_state.py

# Clear pycache for both
docker exec flamboyant_bell rm -f \
  /a0/usr/agents/agent0/extensions/message_loop_end/__pycache__/_49_reasoning_state_update.cpython-312.pyc \
  /a0/usr/agents/agent0/extensions/before_main_llm_call/__pycache__/_13_reasoning_state.cpython-312.pyc

# Syntax check (run from repo root)
C:/Users/Jake/miniconda3/python.exe -m py_compile \
  extensions/message_loop_end/_49_reasoning_state_update.py && \
C:/Users/Jake/miniconda3/python.exe -m py_compile \
  extensions/before_main_llm_call/_13_reasoning_state.py && \
echo "Syntax OK"
```

---

## 13. Research Lineage

**Primary evidence:**
- ST-006, Round 2 context ERZ8bCQH — file-path loss across API context boundary, LOOP DETECTED
  on `/a0/usr/workdir` search, agent rebuilt from scratch. C5 criterion: PARTIAL.

**Design pattern sources:**
- `_49_reasoning_state_update.py` Wave 2 — read-filter-rewrite staging pattern, `_rs_entry` dedup
  marker, compression detection architecture. This spec extends those patterns, not replaces them.
- `_10_session_init.py` — staging.jsonl read pattern, first-turn bootstrap pattern. `_13` borrows
  the file-read-on-first-turn approach.

**What This Does Not Require:**
No external research citations for this spec. The design follows directly from ST-006 observation
and existing code patterns. Citing research for an internal state-field addition would be
speculative formalism. The pattern source is the codebase itself.

---

*Spec written March 2026. Evidence: ST-006 C5 gap (context ERZ8bCQH). Pattern source: Wave 2
reasoning state architecture. Implementation target: Kestrel (Claude Code / Sonnet 4.6).*
