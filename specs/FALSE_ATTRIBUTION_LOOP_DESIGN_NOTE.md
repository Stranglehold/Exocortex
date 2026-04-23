# False Attribution Loop — Design Note
**Date:** 2026-04-17
**Status:** Built (same session)
**Classification:** Cross-cutting hardening / Tool integrity

---

## The Failure Class

A **false attribution loop** occurs when:
1. A tool reports success but silently corrupts its output
2. The agent observes the downstream failure (syntax error, wrong output)
3. The agent correctly diagnoses *that* something failed but *misattributes the cause* — believing it made an error rather than the tool did
4. Recovery actions (rewriting, retrying) target the wrong cause and reproduce the same failure indefinitely

This is distinct from both tool failure (exit code ≠ 0, exception raised — caught by fallback chain) and logic error (agent reasoning was wrong — supervisor detects stagnation). It is a third failure class that neither system handles correctly.

---

## Observed Incident

**Session:** 2026-04-17, linear.app UI capture task  
**Container:** exocortex_v16 (port 32797)  
**Failure duration:** ~40 turns, multiple supervisor stagnation firings, one context surgery

**What happened:**

The agent tried to write a Playwright capture script via `text_editor`. The tool has a content length limit and silently truncated the submitted content at line 13, cutting off mid-parenthesis:

```python
    context = browser.new_context(viewport={"width":1920,"height":1080}
    # ↑ missing closing paren, bracket, method call continuation, indented body, and 60+ more lines
```

The tool reported: `written 13 lines` — success signal.

The write validator (`_26_write_validator.py`) ran, py_compiled the truncated file, detected `SyntaxError: unexpected EOF while parsing`, and injected:

> `[WRITE-VAL] Write to capture_linear.py REJECTED — SyntaxError: ... Rewrite the complete, correct content and retry.`

The agent read this and thought: *I wrote bad Python syntax. I need to fix my code.* It rewrote the same script. The tool truncated again. The validator fired again with the same message. The agent looped.

**Why "Rewrite the complete, correct content" caused the loop:**  
The recovery instruction is true for genuine syntax errors but catastrophically wrong for tool truncation. The agent's code was correct. Rewriting it produced identical content, which the tool truncated at the same boundary, indefinitely.

**Second path — inline truncation:**  
The agent also tried submitting the script inline to `code_execution_tool`. The IPython kernel received truncated code and raised `_IncompleteInputError: incomplete input`. No validator runs on `code_execution_tool` output. The agent saw this error and also attributed it to bad syntax, reinforcing the misattribution.

---

## Why the Existing System Almost Worked

The write validator correctly detected the failure. `py_compile` is the right tool. The guard/validator architecture is sound. The failure was in the **diagnostic layer of the error message** — not the detection layer.

The validator has no way to distinguish:
- Genuine syntax error: agent submitted malformed Python → syntax check fails → "fix your code"
- Tool truncation: agent submitted valid Python, tool cut it off → syntax check fails → **"the tool cut your content, your code is fine"**

Both present as `SyntaxError: unexpected EOF`. The validator treated both the same.

---

## The Fix

Three targeted changes. No new architectural layers.

### Fix 1: Write guard stores intended content metrics

`_25_write_guard.py` already has `tool_args["content"]` available. Store its line count alongside the guard state. The validator needs this to distinguish truncation from genuine error.

### Fix 2: Write validator distinguishes truncation from genuine error

When py_compile fails: compare written line count against intended line count from guard state.

```
written_lines < intended_lines * TRUNCATION_THRESHOLD (0.85)
→ tool truncation: inject truncation-specific recovery guidance
→ "YOUR CODE IS CORRECT. The tool cut off the content. Use bash heredoc."

written_lines ≥ intended_lines * TRUNCATION_THRESHOLD  
→ genuine syntax error: inject original guidance
→ "Rewrite the complete, correct content."
```

The threshold accounts for minor line count differences (trailing newlines, etc.).

### Fix 3: Inline truncation detector (new extension)

`_28_inline_truncation_detector.py` in `tool_execute_after`:
- Runs after `code_execution_tool` only
- Detects `_IncompleteInputError` or `incomplete input` in output
- Injects `hist_add_warning` with explicit guidance: "The tool truncated your inline code. Your code is not the problem. Write to a file first, then execute."

---

## What This Does NOT Do

- Does not change the detection mechanism (py_compile is correct)
- Does not protect against tools other than `text_editor` and `code_execution_tool`
- Does not prevent the truncation from happening — only corrects the diagnosis
- Does not handle all possible silent partial completions (e.g., network writes, database operations)
- Does not modify supervisor stagnation detection (supervisor correctly fired; the problem was earlier)

---

## Failure Class Taxonomy

This incident adds a third class to the tool failure taxonomy:

| Class | Signal | Current Handler | Recovery |
|---|---|---|---|
| **Tool failure** | Exception / non-zero exit | Fallback chain (_30_) | Retry with alternate tool |
| **Logic error** | Task not advancing despite tool success | Supervisor stagnation | Reformulate approach |
| **False attribution loop** | Task not advancing; tool reports success; agent misattributes cause | *(gap — now closed)* | Correct the attribution, give tool-specific recovery |

The false attribution loop is uniquely resistant to generic stagnation recovery because the supervisor's guidance ("consider whether your approach is working") gets interpreted in light of the wrong diagnosis. The agent tries harder, not differently.

---

## Research Lineage

This failure class is structurally identical to what Anthropic's interpretability research calls "sycophantic attribution" — the model updates beliefs to be consistent with received feedback rather than examining whether the feedback source is reliable. Here the "feedback" is the error message, the unreliable source is the tool, and the "sycophantic" behavior is assuming the tool is correct and the agent's code is wrong.

It is also related to the "alarm source confusion" problem in industrial safety systems: when a secondary alarm (syntax error) fires in response to a primary failure (tool truncation), operators address the secondary alarm without reaching the primary cause.

---

## Files Changed

| File | Type | Change |
|---|---|---|
| `extensions/tool_execute_before/_25_write_guard.py` | Modified | Store `intended_line_count` in guard state |
| `extensions/tool_execute_after/_26_write_validator.py` | Modified | Truncation vs genuine error branch in rejection message |
| `extensions/tool_execute_after/_28_inline_truncation_detector.py` | New | `_IncompleteInputError` detection for code_execution_tool |
