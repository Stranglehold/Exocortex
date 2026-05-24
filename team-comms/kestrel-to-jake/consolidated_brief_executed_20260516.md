# Consolidated Brief — Executed
## Kestrel → Jake, 2026-05-16 (post-briefing-from-Opus)

Read the consolidated brief. Executed everything that was mine to execute. Below: what's done, what remains for you, what didn't change and why.

---

## Priority 1 — Upstream MTP Build — NOT EXECUTED (out of scope for me)

The build, model download, server launch, and benchmarking are all Windows-host activities that need your machine and your operator decision on switching the production backend. The brief is clear; the test plan is well-defined. Nothing for me to pre-stage from inside a Docker container.

**Status:** Yours when you sit down at the box. The benchmark targets (50+ tok/s, <22 GB VRAM at 60K, working tool calls) are in the brief.

---

## Priority 2a — `enable_thinking` direction reversed — DONE

Per `enable_thinking_correction_20260516.md`:

- **Wiring doc §13 seam #20 + Open Questions Q1 rewritten.** Withdrew the hypothesis that "v16 has `enable_thinking: true` opposite of spec". v16's config is now correct as-is. Seam #20 demoted from ACTIVE to RARE; remaining candidate causes are context-length degradation and Q4_K_S quantization sensitivity. The Q4_K_M model in the Priority 1 upstream build is the next opportunity to bisect quantization.
- **Wiring doc §09 amended.** Added a callout connecting the (still-inert) reasoning-state and PACE injection chain to the now-enabled thinking: model thinks during a turn, injectors carry compressed traces across turns, both load-bearing, complementary.
- **`extensions/before_main_llm_call/_71_cache_warmer.py`** — removed the `"enable_thinking": False` field from the warm-up payload and updated the docstring.
- **`inference/warm_cache.py`** — same field removed.
- **Grepped the rest of the active codebase** for `enable_thinking` references. The only remaining mentions are in `.bat` server-launch scripts (comments only, already correct) and historical journals / team-comms (intentionally left as records).

**Not touched (operator domain):** v16's `_model_config/config.json` still has `enable_thinking: true` — which is now the correct value, so no change needed.

---

## Priority 2b — Cache warmer wrong path — DONE

Deployed `_71_cache_warmer.py` to canonical path on both containers.

```
/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_71_cache_warmer.py
md5 a8e840e046e45b9ad478aa9867ad5e09  (v16, v17, repo all match)
```

Wrong-path copy removed on both containers.

**Caveat:** A0's extension class cache may have been populated before the deploy. To activate the new extension cleanly, a container restart picks it up. I did not restart v16 because it's running idle cycles autonomously and that's your operator decision. The first LLM call after a restart will fire the warmer; thereafter `WARM_FLAG` prevents re-warming within the same conversation.

---

## Priority 2c — Dead extensions archived — DONE

Five extensions moved from `extensions/<hook>/` to `extensions/archived/<hook>/`:

```
extensions/archived/before_main_llm_call/_17_orchestration_gate.py
extensions/archived/before_main_llm_call/_18_injection_budget.py
extensions/archived/before_main_llm_call/_19_context_pruner.py
extensions/archived/message_loop_end/_16_verification_gate.py
extensions/archived/message_loop_prompts_after/_19_skill_suggester.py
```

`extensions/install_extensions.sh` updated with:
- `_16_verification_gate.py` added to the canonical-path tombstone block (was missing).
- A new **wrong-path tombstone block** that scrubs the no-`python/`-segment path on every re-run. The block covers the 5 archived extensions plus the existing already-tombstoned set (TOOL-REG, Tiered, etc.) plus the cache_warmer wrong-path entry (so future re-runs don't accidentally resurrect the wrong-path version).

Also cleaned the wrong-path copies directly on v16 and v17 via `docker exec rm -f` so the audit reflects the change without needing to re-run install_extensions.sh.

---

## Priority 2d — Audit after changes — DONE

| Container | Before | After |
|-----------|--------|-------|
| v16 | 7 dead, 43 divergent, 6 OK | **0 dead**, 40 divergent, 12 OK |
| v17 | 10 dead, 19 divergent, 3 OK | **0 dead**, 18 divergent, 5 OK |

The remaining DIVERGENT entries are stale wrong-path copies whose canonical versions are loaded — they're code rot but not active danger. Removing them is a follow-up cleanup pass that doesn't need to happen tonight (each one needs a quick sanity check that the canonical version is the intended one).

One leftover worth flagging: v16's `_12_org_dispatcher.py` exists at TWO canonical paths (`/a0/usr/agents/agent0/extensions/python/` and `/a0/python/extensions/`) with different md5s. A0's loader picks the first by sort order. Fragile but not currently misbehaving. Add to your queue when you have a moment.

Run the audit yourself any time:
```
python3 scripts/audit_extensions.py exocortex_v16
python3 scripts/audit_extensions.py exocortex_v17 --quiet
```

---

## Priority 3 — Injection Chain Fix (`_22`/`_23`) — STILL HOLDING

Per Opus: "Deploy AFTER the upstream MTP build is validated." That's your sequencing — Priority 1 first, then this. The injectors are at:
- `extensions/message_loop_prompts_after/_22_reasoning_state_injector.py`
- `extensions/message_loop_prompts_after/_23_pace_plan_injector.py`

When you're ready: deploy to `/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/` on both containers, md5-verify, restart run_ui.

---

## Priority 4 — Idle Engine Monitoring — ONGOING

v16 cycles 60 and 61 completed clean during this window. `steps_used` reporting is now working (Q5 fix verified). Wiki at 34 pages. No Qwen token-rep recurrence. Cycle cap at 100,000 per your earlier directive.

---

## Files touched this round (uncommitted)

```
M  extensions/before_main_llm_call/_71_cache_warmer.py    # enable_thinking field removed
M  inference/warm_cache.py                                # enable_thinking field removed
M  extensions/install_extensions.sh                       # tombstones expanded
M  docs/wiring/exocortex_wiring_and_logic.html            # §13 seam #20, Q1, §09 update
A  extensions/archived/before_main_llm_call/_17_orchestration_gate.py    # moved
A  extensions/archived/before_main_llm_call/_18_injection_budget.py      # moved
A  extensions/archived/before_main_llm_call/_19_context_pruner.py        # moved
A  extensions/archived/message_loop_end/_16_verification_gate.py         # moved
A  extensions/archived/message_loop_prompts_after/_19_skill_suggester.py # moved
D  extensions/before_main_llm_call/_17_orchestration_gate.py             # archived
D  extensions/before_main_llm_call/_18_injection_budget.py               # archived
D  extensions/before_main_llm_call/_19_context_pruner.py                 # archived
D  extensions/message_loop_end/_16_verification_gate.py                  # archived
D  extensions/message_loop_prompts_after/_19_skill_suggester.py          # archived
A  team-comms/kestrel-to-jake/consolidated_brief_executed_20260516.md    # this brief
```

Plus container-side, both v16 and v17:
- `/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_71_cache_warmer.py` md5 `a8e840e046e45b9ad478aa9867ad5e09`
- Wrong-path dead files scrubbed from `/a0/usr/agents/agent0/extensions/<hook>/`

---

## One-line summary

Priority 2 fully executed. Priority 1 awaits your hands on the Windows box. Priority 3 awaits your go after Priority 1 validates.

— Kestrel
