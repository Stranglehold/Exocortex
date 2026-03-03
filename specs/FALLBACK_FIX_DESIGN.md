# Fallback System Fix — Design Rationale

**Triggered by:** ST-001 (OpenPlanter Integration Stress Test)
**Finding:** ~80% false positive rate on fallback triggers
**Root cause:** Failure history never decays on success

---

## The Bug

The fallback system has two extensions working together:

```
Tool executes → _30_tool_fallback_logger (classifies result, writes history)
Next tool call → _30_tool_fallback_advisor (reads history, injects advice)
```

**Logger** (tool_execute_after): On failure, appends to `history[]` and increments `consecutive[tool_name]`. On success, resets `consecutive[tool_name] = 0` but **never touches `history`**.

**Advisor** (tool_execute_before): Checks `len(history[-5:])` against threshold. Since history only grows and never shrinks, once 5 failures have ever occurred (normal during any multi-step troubleshooting), the global threshold fires on **every subsequent tool call forever**.

The advisor's check was:
```python
recent_total = sum(1 for entry in history[-GLOBAL_THRESHOLD:])
if recent_total >= GLOBAL_THRESHOLD:
    advice_parts.append(STEP_BACK_ADVICE)  # fires every call
```

This is equivalent to `if len(history) >= 5`, which is permanently true after 5 accumulated failures.

## The Fix

### Logger (Tier 1 — root cause)

**History decay on success:** When a tool succeeds, clear `history` entirely. Once the agent recovers from errors, the accumulated failure context is stale. This makes `len(history)` represent consecutive global failures since last success, which is the correct input for the advisor's threshold.

**Success indicators:** Added patterns that override error classification. A `pip install` that outputs "Successfully installed X" should not be classified as a failure just because a warning earlier in the output contained the word "error."

**Narrowed catch-all:** The original catch-all pattern `(?i)error|exception|failed|traceback` matched informational messages, warnings, and successful operations. Replaced with `(?i)^ERROR:|^error:|Traceback \(most recent|raise \w+Error|FATAL|CRITICAL` — requires explicit error prefixes or Python tracebacks.

### Advisor (Tier 1 — symptom)

**Correct threshold logic:** With history decaying on success, the existing check (`len(history) >= GLOBAL_THRESHOLD`) now correctly measures "consecutive global failures without any intervening success."

**Raised per-tool threshold:** From 2 to 3. The agent demonstrated during ST-001 that it can self-correct within 2-3 attempts. Firing advice on the 2nd failure pressures the agent to abandon approaches that would have worked on the 3rd try.

**Compact messages:** All advice reduced to single lines. With BST maintaining domain context, working memory holding the objective, and org kernel managing role switching, the agent doesn't need 3-line paragraphs of generic strategy advice on every failure. A one-line nudge is sufficient.

### Dialog Detection Prompt (Tier 2 — mitigation)

The `fw.code.pause_dialog.md` template was replaced with a version that:
- Acknowledges the detection may be a false positive
- Mentions slow operations (builds, downloads) as normal causes
- Provides actionable guidance for actual interactive prompts (use config files, env vars, CLI flags)

### What This Does NOT Fix (Tier 3 — core)

**`code_execution_tool.py` dialog_timeout:** The 5-second dialog detection timeout in Agent-Zero's core code is too aggressive for slow operations. The dialog pattern `r":\s*$"` (line ending with colon) matches half of normal terminal output. Fixing this requires modifying core Agent-Zero code, which is higher risk. The prompt template fix mitigates the impact by making the message less alarmist, but the false trigger rate from dialog detection remains.

**Recommended future fix:** Make `dialog_timeout` configurable via agent settings, and narrow the dialog regex patterns. Or add a whitelist for known-slow commands (pip, apt-get, curl, ollama, npm, cargo, make).

---

## Validation

After deploying, run the same OpenPlanter installation sequence from ST-001 and measure:
- Fallback fire count (ST-001 baseline: ~20 fires)
- False positive rate (ST-001 baseline: ~80%)
- Context tokens consumed by fallback messages (should be ~70% less due to compact messages)
- Agent behavior: should complete the same task with fewer interruptions

Expected result: false positive rate drops to <20%, total fallback fires drop to <5.

## Context

This system was built before PACE, supervisor loop, BST, and working memory existed. It was the primary circuit breaker preventing infinite retry loops. Now that four other prosthetics handle strategic reasoning and loop prevention, the fallback advisor's role is reduced to: last-resort nudge when all other systems have failed to redirect the agent. The thresholds and message weight should reflect this reduced role.
