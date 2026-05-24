# Brief — Independent Work While You Were at the Office
## Kestrel → Jake, 2026-05-16

You said you'd be back in ~3 hours and to look at action items + tinker. Here's
what changed while you were gone, what needs your attention, and what's still queued.

---

## Container state — both clean

- **v16:** Cycle cap raised from 50 to 100,000 (effectively no limit, per your "no cap or limit on it"). Counter reset to 0. Daemon restarted. Cycle 60 (MAINTAIN) fired post-reset and completed cleanly — `steps_used: 14` for the first time in days (more on that below). v16 is in normal MAINTAIN/BUILD/EXPLORE rotation, no Qwen token-rep recurrence so far.
- **v17:** Still paused per session_handoff. No changes.
- **Code change to `services/idle_watch.py`:** `MAX_TOTAL_CYCLES = 100000`. md5-synced on both containers and repo.

---

## Action items I addressed

### ✅ Q5 — `steps_used: 0` reporting bug — FIXED & VERIFIED LIVE

**Root cause:** `prompts/idle_activation.md` told the agent how to invoke `cycle_close.py` but omitted `--steps-used` from the example. `cycle_close.py` supports the flag (defaults to 0). Agent never knew to pass it.

**Fix:** Added `--steps-used <N>` to the invocation block in the activation prompt plus a one-line instruction. Deployed to both containers (md5 `4c59ddcceaea975baf99fda8dc6e20a6` matches across v16/v17/repo). No daemon restart needed — `_build_activation_prompt()` re-reads the template each fire.

**Verification:** Cycle 60 reported `steps_used: 14`. Q5 is closed.

### ✅ Missing `/a0/usr/skills/auto-generated/` directory on v16 — CREATED

**Finding:** The activation prompt instructs the agent to write skills to `/a0/usr/skills/auto-generated/`. That directory existed on v17 but not on v16. Any skill capture attempt on v16 was failing silently.

**Fix:** Created the directory on both containers (idempotent). Added `/a0/usr/skills/auto-generated` to the `mkdir -p` loop in `scripts/install_idle_engine.sh` so it persists across reinstalls.

**Verification:** Pending — wait for a cycle where the agent genuinely captures a skill. Won't be every cycle.

### 🟡 Q1 — Qwen mid-response token-repetition — EVIDENCE LOGGED, NOT FIXED (operator decision)

**Empirical finding:** v16's `/a0/usr/plugins/_model_config/config.json` has `chat_model.kwargs.enable_thinking: true`. v17 has it `false`. Opus's session-handoff document explicitly states "Every request body must include `enable_thinking: false`" for Qwen3.6 — the v16 config is the opposite of his stated requirement.

**Why I didn't change it:** Model config is operator domain per `CLAUDE.md` ("Jake sets model configuration. You do not."). Flagged for your review.

**Caveat:** Cycles 18-60 ran cleanly under the same config. So this isn't a deterministic cause — but it's the cheapest hypothesis to test by flipping the flag. Documented as seam #20 in the wiring doc and as Q1 in Open Questions with full reasoning.

**Open hypotheses (Opus's prior):** (1) `enable_thinking: false` not being sent ← strongest now, with config divergence as direct evidence; (2) context-length degradation; (3) Q4_K_S vs Q4_K_XL quantization sensitivity.

---

## New finding — `audit_extensions.py` reveals significant deploy state drift

While investigating where `_71_cache_warmer.py` lives (Sonnet built it May 14 per session_handoff but I couldn't find evidence it's loaded), I discovered it's deployed to a wrong path that A0's loader doesn't check. I then built a generalized audit tool to scan all extension hooks for the same pattern.

**Tool:** `scripts/audit_extensions.py <container>` — runs an md5-based survey of every extension file across all four extension-host paths and classifies each by load status.

**Findings on v16:**

| Category | Count | Meaning |
|----------|-------|---------|
| OK (single canonical copy) | 6 | The clean case |
| DUP same md5 | 7 | Multiple paths, identical content — harmless |
| DUP DIVERGENT | 43 | Canonical wins; wrong-path is stale (code rot, not active danger) |
| DUP CANONICAL DIVERGENT | 1 | Same filename at two canonical paths, different content — loader picks one by sort order (fragile) |
| WRONG-PATH (DEAD) | 7 | File exists ONLY at non-canonical path → silently not loaded |

**Findings on v17:** 10 WRONG-PATH DEAD, 19 DUP DIVERGENT, 28 DUP same md5, 3 OK, 2 DUP same canonical. Different deploy history → different drift.

**The 7 DEAD on v16 — capabilities that were built but never running:**
- `before_main_llm_call/_71_cache_warmer.py` (Opus-specced May 14 cache pre-warmer)
- `before_main_llm_call/_17_orchestration_gate.py`
- `before_main_llm_call/_18_injection_budget.py`
- `before_main_llm_call/_19_context_pruner.py`
- `message_loop_prompts_after/_09_context_pruner.py`
- `message_loop_prompts_after/_19_skill_suggester.py`
- `message_loop_end/_16_verification_gate.py`

**Common between v16 and v17 (dead on BOTH containers):**
- `_17_orchestration_gate.py`
- `_18_injection_budget.py`
- `_19_context_pruner.py`
- `_19_skill_suggester.py`
- `_16_verification_gate.py`

These five represent capabilities that were specced, written, deployed — and never actually run. Whether each one should be revived or removed is your call. I didn't move anything because (a) intent isn't always clear from the file alone, and (b) some may be intentionally archived.

**Run the tool yourself:**
```
python3 scripts/audit_extensions.py exocortex_v16
python3 scripts/audit_extensions.py exocortex_v17 --quiet
python3 scripts/audit_extensions.py exocortex_v16 --json
python3 scripts/audit_extensions.py exocortex_v16 --hook before_main_llm_call
```

Exit code 1 if issues are found, 0 if clean. Could go in CI later if you want.

---

## What I did NOT do

- **Did not deploy `_22_reasoning_state_injector.py` / `_23_pace_plan_injector.py`** despite Opus's approval — that's still your go-ahead per the workflow established this session.
- **Did not push the 8 commits to origin/main** — your call.
- **Did not relocate any of the 7 DEAD extensions** to the canonical path — needs your review of intent first.
- **Did not change the v16 model config** to flip `enable_thinking` to `false` — operator domain.
- **Did not deploy `_71_cache_warmer.py`** to the canonical path even though that's a simple mechanical move — the extension blocks for 3-5 min synchronously if cache is cold, and that user-facing impact deserves your decision.

---

## Wiring doc updates

- **§13 seam #20** added: Qwen mid-response token-repetition, with the v16 `enable_thinking: true` finding cited inline.
- **Open Questions Q1** expanded with the empirical config-divergence check.
- **Open Questions Q5** moved to FIXED status with root cause and verification notes.
- **§16 Component Index, §15 Failure Modes, §10/§11/§12** still pending — deferred to next session with fresher context.

---

## Files touched this window (all local; nothing committed)

```
M  services/idle_watch.py                          # MAX_TOTAL_CYCLES 50 → 100000
M  prompts/idle_activation.md                      # added --steps-used to cycle_close
M  scripts/install_idle_engine.sh                  # added skills/auto-generated to mkdir
M  docs/wiring/exocortex_wiring_and_logic.html     # seam #20, Q1 expansion, Q5 resolution
A  scripts/audit_extensions.py                     # new audit tool
A  team-comms/kestrel-to-jake/audit_findings_20260516.md  # this brief
```

Plus container-side:
- `/a0/usr/Exocortex/idle_watch.py` md5 `b9f3348f140f856cd4273f791140ae74` on v16 and v17
- `/a0/usr/Exocortex/prompts/idle_activation.md` md5 `4c59ddcceaea975baf99fda8dc6e20a6` on v16 and v17
- `/a0/usr/skills/auto-generated/` created on v16
- `/a0/usr/Exocortex/office/engine_state.json` — `total_cycles_since_clear` reset to 0 on v16

---

## What's still queued for when you're back

In rough priority order:

1. **Decide on `_22`/`_23` injector deployment** (Opus approved; one command from go).
2. **Decide on `enable_thinking: false` flip** for v16 model config (Q1 hypothesis 1 test).
3. **Review the 5 commonly-dead extensions** — revive, delete, or document as archived.
4. **Review `_71_cache_warmer.py`** specifically — fragile due to 3-5 min synchronous warmup, but spec is good and would eliminate Turn 1 TTFT pain.
5. **Push the 8 commits ahead of origin/main** (now 12 ahead with this session's commits if you choose to make them).
6. **`steps_used` calibration** — first reported value was 14 for a MAINTAIN cycle. If that feels too high or too low, the prompt instruction can be tightened.

— Kestrel
