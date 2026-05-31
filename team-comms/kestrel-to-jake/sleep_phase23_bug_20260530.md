# Sleep Consolidation Phases 2 & 3 Crash — Diagnosis + Fix (held for review)

**From:** Kestrel
**To:** Jake
**Date:** 2026-05-30 (overnight)
**Trigger:** v17 MAINTAIN cycle 138 flagged it; also seen in earlier `[SLEEP]` logs.
**Status:** Root-caused. Fix applied to repo + tested. **NOT committed, NOT deployed** — held for your review (you said we'd go over it in the morning, and these are your containers).

---

## The bug

Sleep consolidation Phase 2 (anti-pattern detection) and Phase 3 (promotion) crash with:

```
AttributeError: 'list' object has no attribute 'get'
  sleep_episode_chunker.py:116      tool_name = content.get("tool_name", "")   ← Phase 2
  sleep_interaction_analyzer.py:250 tool_name = content.get("tool_name", "")   ← Phase 3
```

Both files extract a message's `content` and handle it being a **string** but not a **list**:

```python
content = msg.get("content", {})
if isinstance(content, str):
    try:    content = json.loads(content)     # a JSON *array* string parses to a list
    except: content = {"raw": content}
# ← no handling if content is a list; downstream does content.get(...) → crash
```

When `content` is a list, the first `content.get(...)` raises. Phase 1 (dedup) doesn't touch message content, so it survives — which is why you see "Phase 1 OK, Phases 2-3 crash."

**Impact:** whenever it fires, phases 2 & 3 produce *zero* output — sleep consolidation runs at ~⅓ effectiveness (dedup only; no anti-pattern capture, no promotion).

## Why it's intermittent (and why post-hoc scans look clean)

The crash needs a message whose `content` is a **list**. I scanned **all 393 stored sessions** — at both the parsed and the raw `chat.json` level — and found **zero** list-content messages. Yet it crashed tonight.

Conclusion: **the trigger is ephemeral runtime state.** The list-shaped content exists only in the agent's *live, in-flight session* during a cycle (streaming / structured multi-part content), and normalizes to a dict by the time the session is written to disk. `load_recent_sessions(n=3)` pulls the most recent sessions — including the agent's own in-flight one — so the crash fires only when a recent session currently holds list content. After the cycle finalizes, the evidence is gone. That's the intermittency.

Plausibly related to A0 v1.18's message-content format (structured/multi-part content), but the fix is robust regardless of the source.

## The fix (applied to repo, uncommitted)

One guard block added after the str-handling in **both** files — normalize any non-dict to a dict so every downstream `.get` / `in` / index is safe:

```python
if not isinstance(content, dict):
    content = {"raw": content}
```

This is minimal, in-pattern (matches the existing str-guard), and fixes every downstream site in both files at once. List-content messages get safely skipped (treated as `{"raw": [...]}`) instead of crashing the whole phase.

## Tested

- **Synthetic reproduction:** a session with list content + a JSON-array-string both reproduce the exact `AttributeError` on the old code; with the fix, `chunk_session` → 2 episodes (dict messages processed correctly, list messages skipped), `analyze_sessions` → clean. No crash.
- **Real-data regression:** ran the patched modules against the real 3 recent sessions + scanned 393 sessions — no regression, no crash, correct output.
- **Compile:** both files `py_compile` clean.

## What I recommend (your call in the morning)

1. **Deploy the fix** to v16 + v17 (`docker cp` both files to `/a0/usr/Exocortex/` + clear pycache; or via `scripts/install_sleep_consolidation.sh`). Then the next sleep cycle's phases 2/3 produce real output. I'll commit it to `upgrade/v1.18` on your OK.
2. **Optional diagnostic:** add a one-line log that captures the list content's actual shape the first time it's hit, so we can decide whether to *richly extract* text from list content vs. the current safe-skip. Right now we skip it (no crash, but we don't mine those messages for anti-patterns). If list content turns out to carry real tool calls, extraction would recover that signal.
3. **Alternative fix location (not chosen):** normalizing in `_parse_session` would be a single-point fix, but it changes parsing for all consumers; the consumer-side guards are safer and match the existing defensive pattern. Happy to discuss.

Working tree has the two files modified, uncommitted. Nothing deployed. Ready to ship on your word.

— Kestrel
