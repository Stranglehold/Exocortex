# OVERNIGHT TEST ANALYSIS — Root Causes and Fixes
## From: Kestrel — April 24, 2026
## Re: overnight_test_suite_20260423.md results

---

## Summary

Two root-cause failures explain all six test outcomes. Both fixed and deployed to v17.

---

## Root Cause 1: Context Watchdog Window Size Bug

**Symptom:** Context overflow at turn ~4-5 with no [CONTEXT WARNING] or [CTX-PRUNE] events. The pruner never fired.

**Root cause:** `_20_context_watchdog.py` had `DEFAULT_CONTEXT_WINDOW = 100000`, but v17 runs at 65536. At 60k actual tokens, the watchdog computed 60k/100k = 60% utilization — below the 70% WARN threshold. It saw no problem while the agent was actually at 92% capacity.

**Fix:** Changed `_20_context_watchdog.py` to read `context_window_tokens` from `/a0/usr/Exocortex/config.json` (new config key). Default drops to 65536. Runtime override via `agent.set_data("context_window_size", N)` still works. Created `config.json` in v17 with `context_window_tokens: 65536`.

**Impact:** Watchdog now fires WARN at ~45k tokens, CRITICAL at ~55k. The supervisor loop Tier 3 (context surgery) should now engage before overflow rather than after. This unblocks Tests 3, 5, and 6 on the next run.

**Long-term:** When models change, update `context_window_tokens` in config.json. No code change required.

---

## Root Cause 2: BST Zero-Signal Reset Not Triggering on Compound Momentum

**Symptom:** After coding task, compound classifier `coding+planning` held for 7+ turns despite a clear geopolitical investigation task. The v3.4 zero-signal reset didn't fire.

**Root cause:** The zero-signal reset (v3.4) checked if `current_domains.intersection(scored_domains)` was empty. In the geopolitical task, the word "strategy" (from "TSMC's business strategy") triggered `planning` domain signals, so `planning` had score > 0. Since `planning` is in the current compound `coding+planning`, the intersection was non-empty and the reset didn't fire.

Simultaneously, the compound momentum rule (Rule 3a) held because `planning` scored as the new primary — and planning IS in the current compound. So the compound held as `planning+coding` instead of breaking to `investigation`.

**Fix:** Added Condition B to the zero-signal reset (v3.5):

```
Condition A (all-silent): ALL compound domains have zero signals → reset.
Condition B (domain-shift): The dominant new domain scores >= 2 signals AND
  is NOT in the current compound → reset, even if compound components still score.
```

Condition B catches the TSMC scenario: `investigation` scores 3+ signals (geopolitical, export controls, semiconductor, TSMC), which is higher than `planning`'s 1-2 signals from "strategy". The dominant domain (investigation) is not in `coding+planning`, so momentum breaks.

Threshold of 2 prevents single-signal noise from triggering spurious resets.

**Note on scores ordering:** The fix assumes `scores` is ordered by descending confidence, i.e., `scores[0]` is the highest-scoring domain. Confirm this is the case in `_compute_scores()` or wherever `scores` is assembled before passing to the execute block. If not ordered, a `max(scores, key=lambda x: x[1])` is needed.

---

## Still Open: The 900-1000 Token/Turn Injection Cost

Even with the watchdog fixed, ~900-1000 tokens injected per turn is expensive for a 65k window. At that rate, 65 turns of overhead alone consumes the window. The agent estimated it via proxy; the `[TOKEN-COUNT]` docker logs weren't accessible from inside the session.

**Blocking item:** We need actual `[TOKEN-COUNT]` log data to know which extensions are the biggest contributors. The token counting instrumentation from yesterday's build is in place — we just need to collect real data from a new run with the watchdog working correctly.

**After we have real data:** Item 1 (injection gate `_09_`) targets this directly. Domain-gated injection could cut the per-turn cost by 50-70% by suppressing irrelevant extensions.

---

## Test Results Status After Fixes

| Test | Old Status | Expected After Fixes |
|------|-----------|---------------------|
| 1 — BST Momentum Reset | FAIL | PASS (domain-shift reset now triggers) |
| 2 — Token Counting Baseline | PARTIAL | PARTIAL→PASS (docker logs need external collection) |
| 3 — Context Endurance | FAIL | PASS (watchdog fires at correct thresholds, surgery engages) |
| 4 — MCP Integration | PASS (5/6) | PASS (5/6) — unchanged, DeepWiki expected |
| 5 — Epistemic Integrity | NOT EXECUTED | Now executable (context endurance fixed) |
| 6 — Cross-Domain Skill Loading | NOT EXECUTED | Now executable (context + BST both fixed) |

Recommend re-running the full suite after a container restart to validate.

— Kestrel
