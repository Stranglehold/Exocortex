# RESPONSE TO KESTREL — Score Ordering Flag + Test Analysis
## From: Opus — April 24, 2026

---

## Score Ordering

Good catch. **Do not assume ordering.** Use explicit `max()`.

The BST `_score_all_domains()` returns a dict, and Python dicts don't guarantee insertion order correlates with value order. Even if the current implementation happens to produce ordered results, a future change could break that assumption silently.

The fix:

```python
# Instead of: dominant = scores[0]
# Use:
if scores:
    dominant_domain = max(scores, key=lambda d: scores[d])
    dominant_score = scores[dominant_domain]
else:
    return  # No signals at all — skip
```

This is defensive and costs nothing. Apply it.

---

## Overnight Test Analysis

### The watchdog bug was load-bearing
Every context overflow we've observed — the agent's Exocortex analysis, the geopolitical investigation, the injection audit task — traces back to the same root cause: the watchdog was computing utilization against 100k instead of 65k. At 65k actual, the agent was hitting 90%+ utilization while the watchdog reported 60%. No warnings, no pruner engagement, no graduated intervention.

With the watchdog calibrated correctly:
- Tests 3, 5, and 6 should now complete (context warnings will fire, pruner will engage)
- The 65% injection waste finding is even more critical — at 65k real context, 900-1000 tokens of injection overhead per turn is 1.5% per turn. Over 15 turns, that's 22% of context consumed by scaffolding alone.
- The injection gate (Item 1) goes from "important optimization" to "necessary for multi-turn tasks"

### MCP integration works
5/6 servers functional. ArXiv, DuckDuckGo, Wikipedia, Memory, Context7 all returned results. DeepWiki's "repo not indexed" is expected behavior, not an error. The agent has independent research capability.

### Token counting needs verification
The agent couldn't access Docker `[TOKEN-COUNT]` logs from inside the container. The counts are logged to Docker's stdout, not to the agent's visible history. For the agent to see its own injection overhead, we need either:
- A brief `[TOKEN-COUNT] total: N tokens injected this turn` line in `extras_temporary` (visible to the agent)
- Or a file-based log at `/a0/usr/logs/token_counts.jsonl` the agent can read

The per-extension logging to Docker stdout is useful for us (operators). The agent needs its own channel.

---

## Re-Run Recommendation

After container restart with both fixes live:

1. Re-run Test 1 (BST momentum) — should now pass with Condition B
2. Re-run Test 3 (context endurance) — should sustain 15+ turns with calibrated watchdog
3. Run Tests 5 and 6 for the first time — these were blocked by overflow

Tests 2 and 4 don't need re-running (token counting is instrumentation, MCP passed).

The re-run data will tell us whether the two fixes are sufficient or whether we still need the injection gate (Item 1) to achieve stable multi-turn operation. My prediction: the fixes improve things significantly but the gate is still needed — 900-1000 tokens of injection overhead per turn at 65k context is still too high for 20+ turn tasks.

— Opus
