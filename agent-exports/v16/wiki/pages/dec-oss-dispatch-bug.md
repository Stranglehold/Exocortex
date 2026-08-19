# DEC-015: OSS Sprint Dispatch Blocking Bug

## Status
CONFIRMED — Source-verified in _50_supervisor_loop.py lines 1136-1192

## Symptom
`oss_ingest_sprint` returns `[OSS] dispatch error`. All 253 claims in ledger remain unattributed to topics. Topic routing non-functional.

## Source Analysis

### Function: `_drain_staging_buffer` (lines 1136-1192)

**Active source path:** `/a0/usr/plugins/exocortex/extensions/python/message_loop_end/_50_supervisor_loop.py`

### Root Cause: Fire-and-Forget Async Dispatch

Line 1179-1183:
```python
loop = asyncio.get_event_loop()
if loop.is_running():
    asyncio.ensure_future(_mark())  # schedules but returns immediately
else:
    loop.run_until_complete(_mark())  # only blocking path when loop not running
```

**The bug:** During active message loops (the common case), `ensure_future(_mark())` schedules the coroutine but the outer function returns immediately without awaiting. The `_mark()` coroutine never completes before the staging buffer is consumed, so entries are never tagged as `loop_period`.

### Secondary Issue: Silent Failure in Inner Coroutine

The `_mark()` async function (lines 1159-1177) has its own try/except that prints to stdout but never re-raises. Even if dispatch worked, inner errors are swallowed.

### Call Sites
- Line 1270: called during Tier 2 surgery
- Line 1330: called during Tier 3 surgery

Both paths hit the same dispatch bug when the event loop is running.

## Impact
- 253 claims staged but 0 attributed to iran or iran-hormuz topics
- Topics inactive since 2026-04-05
- Ingestion resumed 2026-05-08 but claims accumulate without routing
- volume_anomaly metric degraded

## Required Fix (Cannot Modify .py Files — Requires Human Action)
Patch `_50_supervisor_loop.py` `_drain_staging_buffer` to either:
1. Use `asyncio.create_task()` with proper await in async context
2. Fall back to synchronous DB write when async dispatch fails
3. Add retry with exponential backoff
4. Convert outer function to async and await _mark()

## Related
- Cycle 23: same error observed during sprint dispatch
- Cycle 25: confirmed 253 claims / 0 attributed, source verified
- Program.md Rule 8: deterministic layers should not fail silently

## Last Updated
2026-05-09 Cycle 25 — Source verification complete
