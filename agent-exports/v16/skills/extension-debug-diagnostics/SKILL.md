---
name: extension-debug-diagnostics
description: An Agent-Zero extension is deployed but not producing expected behavior.
  Docker logs show no output, unexpected...
triggers:
- An Agent-Zero extension is deployed but not producing expected behavior. Docker
  logs show no output, unexpected...
version: '1.0'
author: Exocortex
---

# Skill: Extension Debug & Diagnostics

## Trigger
An Agent-Zero extension is deployed but not producing expected behavior. Docker logs show no output, unexpected output, or errors from the extension. Keywords: "not working," "not firing," "silent," "no output," "extension broken," "logs show nothing," "error in logs."

## Inputs Required
- **Extension file path** — which extension, which hook directory
- **Expected behavior** — what should it be doing
- **Observed behavior** — what is it actually doing (or not doing)
- **Docker logs** — `docker logs <container> 2>&1 | Select-String "<EXTENSION_PREFIX>"` output
- **Comparison extension** — a working extension in the same hook directory

## Procedure

### Phase 1: Confirm Deployment
Before debugging logic, confirm the file is actually there and loadable.

1. **Check file exists and has content:**
   ```bash
   ls -la /a0/python/extensions/<hook_dir>/<extension_file>
   ```
2. **Validate syntax:**
   ```bash
   python3 -m py_compile /a0/python/extensions/<hook_dir>/<extension_file>
   ```
3. **Clear pycache** (stale bytecode is a silent killer):
   ```bash
   rm -rf /a0/python/extensions/<hook_dir>/__pycache__/
   ```

If syntax fails, fix the error first. Everything else is irrelevant until the file compiles.

### Phase 2: Validate Class Pattern
Compare the extension's class structure against a known working extension in the same hook directory.

1. **Extract class signature from working extension:**
   ```bash
   grep -n "class\|async def execute\|from.*import" /a0/python/extensions/<hook_dir>/<working_extension>
   ```
2. **Extract class signature from broken extension:**
   ```bash
   grep -n "class\|async def execute\|from.*import" /a0/python/extensions/<hook_dir>/<broken_extension>
   ```
3. **Compare:** Must match on:
   - Inherits from `Extension`
   - `async def execute(self, loop_data: LoopData = LoopData(), **kwargs)`
   - Imports: `from python.helpers.extension import Extension` and `from agent import LoopData`

If class pattern doesn't match, fix it. Agent-Zero discovers extensions by class pattern.

### Phase 3: Determine Execution Status
The extension either isn't being called at all, or it's being called and exiting silently.

1. **Inject a debug print at the very top of execute():**
   ```python
   print("[EXT-NAME] execute() called", flush=True)
   ```
   Place this BEFORE any try/except block, BEFORE any early return logic.

2. **Clear pycache, restart container, send test message.**

3. **Check logs:**
   ```powershell
   docker logs <container> 2>&1 | Select-String "EXT-NAME" | Select-Object -Last 10
   ```

4. **Interpret:**
   - **No output at all:** Extension not discovered. Class pattern issue, import error at module level, or hook directory mismatch.
   - **"execute() called" appears:** Extension fires. Problem is in the logic — proceed to Phase 4.

### Phase 4: Trace Early Returns
Most silent failures are early returns before any logging. Trace them systematically.

1. **Map all early return points:**
   ```bash
   grep -n "return" /a0/python/extensions/<hook_dir>/<extension_file> | head -20
   ```

2. **Add a labeled print before each early return:**
   ```python
   print("[EXT-NAME] BAIL: <reason>", flush=True)
   return
   ```

3. **Clear pycache, restart, test, check logs.**

4. **The bail message tells you which condition is failing.** Common causes:
   - `extras_persistent` empty — upstream extension didn't populate expected data
   - Config key missing — extension expects config section that doesn't exist
   - Data structure mismatch — extension expects dict, gets string, or vice versa
   - Threshold too aggressive — similarity/confidence threshold filtering everything out

### Phase 5: Expose Swallowed Exceptions
Agent-Zero extensions typically wrap execute() in try/except. Inner try/except blocks around specific operations silently eat errors.

1. **Find all except blocks:**
   ```bash
   grep -n "except Exception" /a0/python/extensions/<hook_dir>/<extension_file>
   ```

2. **Replace bare except blocks with traced versions:**
   ```python
   except Exception as _err:
       print(f"[EXT-NAME] CRASH: {type(_err).__name__}: {_err}", flush=True)
       import traceback; traceback.print_exc()
   ```

3. **Important:** Replace inner except blocks FIRST. The outer except for execute() catches everything — if inner blocks silently swallow the real error, the outer block never fires.

4. **Clear pycache, restart, test, check logs.**

5. **Common crash causes:**
   - `NameError` — Sonnet referenced a function/variable that doesn't exist
   - `AttributeError` — called a method that doesn't exist on the object (wrong API assumption)
   - `KeyError` — expected dict key missing from config or metadata
   - `TypeError` — wrong argument types to a method call

### Phase 6: Verify API Assumptions
Implementation models (Sonnet) frequently assume API methods that don't exist.

1. **Check method exists on the object:**
   ```bash
   grep -n "def <method_name>" /a0/python/helpers/<relevant_file>.py
   ```

2. **Check method signature matches how it's being called:**
   ```bash
   grep -n -A3 "def <method_name>" /a0/python/helpers/<relevant_file>.py
   ```

3. **If the method doesn't exist**, find the actual method name:
   ```bash
   grep -n "def " /a0/python/helpers/<relevant_file>.py
   ```

### Phase 7: Verify Side Effects
Once the extension appears to run without errors, confirm it actually did something.

1. **Check file creation** (co-retrieval logs, sidecar files):
   ```bash
   ls -la /a0/usr/memory/
   ```

2. **Check metadata updates** (access counts, timestamps):
   ```bash
   . /opt/venv-a0/bin/activate && python3 -c "<pickle inspection script>"
   ```

3. **Check config was read correctly** (add a print of loaded config values).

4. **If side effects are missing but no errors**, the extension ran but its logic produced no output. This is a tuning issue (thresholds too tight, filters too aggressive), not a bug.

## Key Paths
```
/a0/python/extensions/before_main_llm_call/     — BST, meta-gate, dispatcher
/a0/python/extensions/monologue_end/             — Memory classifier, maintenance
/a0/python/extensions/message_loop_prompts_after/ — Memory recall, enhancement
/a0/python/extensions/message_loop_end/          — Supervisor
/a0/python/helpers/memory.py                     — Memory API (search, get_all_docs)
/a0/python/helpers/extension.py                  — Extension base class
/opt/venv-a0/                                    — Agent-Zero Python environment
```

## Quality Checks
- [ ] Never skip Phase 1. Stale pycache causes more silent failures than bad logic.
- [ ] Debug prints include `flush=True`. Without it, prints may buffer and never appear in docker logs.
- [ ] Every debug print has a unique, greppable prefix (e.g., `[MEM-ENHANCE]`, `[MEM-MAINT]`, `[BST]`).
- [ ] Inner except blocks are traced BEFORE outer except blocks.
- [ ] Use Python heredoc (`python3 << 'EOF'`) for multi-line patches, not `sed` with escaped newlines.
- [ ] Always `python3 -m py_compile` after any edit, before restarting.

## Anti-Patterns
- **Using `sed` for multi-line insertions.** `sed` with `\n` escaping creates triple-duplicate blocks and literal `\n` strings. Use Python heredoc for any edit longer than one line.
- **Debugging logic before confirming execution.** If the extension isn't being called, no amount of logic debugging helps. Phase 3 (execution status) must come before Phase 4 (early returns).
- **Assuming the outer except will catch everything.** Inner try/except blocks with bare `except: pass` silently eat the real error. The outer except never fires because the inner one already handled (swallowed) the exception.
- **Blaming the extension when it's the upstream.** If the extension depends on data from another extension (e.g., _56 depending on _50's output), the bug may be in the dependency, not the extension itself. Trace the data flow across extensions.
- **Forgetting the venv.** Agent-Zero's Python environment is at `/opt/venv-a0/`. System Python doesn't have LangChain, FAISS, or other dependencies. Always activate the venv for inspection scripts.
