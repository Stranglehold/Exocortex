# Overnight Latency Investigation — Final Report
## Kestrel → Jake, 2026-05-18

You asked for the rocket-ship latency win, thinking left enabled, changes as
needed, careful while you slept. This is the complete, evidence-grounded result.
Eight hypotheses tested by controlled measurement; six overturned (including two
of my own earlier "headlines"). The methodology held: measurement killed every
wrong theory until only the true one remained.

---

## Bottom line

**The inference stack is not the problem. It is excellent.** Server, litellm,
streaming, request shape, KV-cache — all reuse a stable prefix flawlessly
(measured: 17.8s cold → **0.7s** warm; survives 5-min idle gaps; tolerates
intervening calls).

The cost is this: **every agent turn pays one cold prefill of a ~15,000-token
prompt, and that prefill is not kept warm turn-to-turn.** ~15K tokens at the
measured cold rate (~30 tok/s) ≈ ~8 minutes. Within a turn the agent's later
iterations *do* reuse (81–83% prefix-stable, confirmed on live traffic) — the
pain is the first iteration of each turn starting cold.

So the levers are: **(1) shrink the 15K prompt, (2) keep the stable prefix warm
out-of-band between turns, (3) finish the prefix-stability hardening.** None
touch `enable_thinking` (preserved per your instruction). The cache-warmer
*concept* is vindicated — not as the broken synchronous `_71`, but as an
out-of-band idle keepalive.

---

## The elimination chain (every step measured against the live `:1235`)

| # | Hypothesis | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Missing `cache_prompt` flag | ❌ ruled out | server caches by default; no-flag reuses (16×) |
| 2 | Streaming breaks reuse | ❌ ruled out | `stream:true` reuses identically |
| 3 | Anthropic `cache_control` sent to llama.cpp | ❌ ruled out | `explicit_caching` defaults False; live path never adds it |
| 4 | Single-slot eviction by utility/embed calls | ❌ ruled out | re-request after an intervening different prompt **still reused** |
| 5 | Prompt-content prefix instability (datetime / `_08` step tag) | ⚠️ real but **not the cause** | `_08` was a genuine instance — fixed — but fixing it didn't move latency |
| 6 | Structured/templated growing message array | ❌ ruled out | A0's exact array shape reuses (even better than a string) |
| 7 | Idle-time slot reclamation | ❌ ruled out | cache survives 60/150/**300s** idle (near-total reuse after) |
| 8 | litellm wire param disabling cache | ❌ ruled out | **faithful in-process litellm capture: 17.8s→0.7s, clean minimal body, no `cache_prompt`/`cache_control`/slot param** |

Two of my own earlier reports were overturned here and I want that on the
record: the "datetime is the headline" framing (it's tertiary) and the
"single-slot eviction is primary" framing (disproven by test #4). Measurement
beat inference, repeatedly. That is the process working, not failing.

## Ground truth from live traffic (read-only capture, since removed)

Captured 4 consecutive real `:1235` request bodies during one multi-iteration
turn via a temporary in-process httpx logger (removed; clean state verified):

- **req[0] = 1,684 chars: a separate "chat naming assistant" utility call.**
  A small, *different* prompt that hits the same single-slot server around the
  main loop. (Tolerated per test #4, but it confirms non-chat traffic shares
  `:1235`.)
- **req[1..3] ≈ 60K chars: the main agent loop iterations.** Consecutive
  diffs: first divergence at **81.0%** then **83.4%** — i.e. each iteration is
  byte-identical to the previous for ~81–83%, diverging only at the natural
  append point (new tool result / assistant turn). **The prefix is stable
  within a turn; the server should and does reuse it after iteration 1.**

Conclusion: intra-turn, only iteration 1 is cold. The ~8 min/turn ≈ that single
~15K-token cold prefill. The faithful litellm test proves a stable-prefix
growing conversation reuses in 0.7s — so the fix space is "make the per-turn
first-iteration prefill cheap," three independent ways below.

**One honest open item:** I did not fully nail *why* turn N+1's first iteration
doesn't reuse turn N's cached prefix in normal operation (A0 rebuilds the full
system prompt via `get_system_prompt()` every turn; idle cycles use fresh
contexts; the prompt is simply huge and cold each turn). It doesn't change the
fix direction — a 15K cold prefill per turn is the cost regardless — but it's
the one mechanism I'd still want to confirm, and it needs the live wire-diff
*across* turns (the in-process hook can do it; I removed it for clean state).

## `_08_step_budget_tracker` fix — deployed, correct, reversible, not the cause

`_08` prepended `[Step N/M]` into `history_output[-1]` (the cacheable history
region); the tag rode whatever message was current each turn, so the same
historical message rendered differently every turn — a real prefix-instability
(GAP-004 pattern). **Fixed:** the step tag/warning now writes to
`extras_temporary` (the tail, after history, cleared each turn) — cache-safe,
same information reaches the model. Deployed both containers, md5
`88615489374430e026241ecfbe9cf44e` (v16 = v17 = repo), py_compile clean. It is
a correct cache-hygiene improvement and the right pattern, but measurement
showed it is **not** the dominant latency cause. Keep it; it's reversible
(git/file revert) and aligned with the cache principle.

## Ranked fixes (evidence-grounded)

1. **Shrink the ~15K-token prompt (highest leverage, in-domain).** Cold prefill
   time is linear in prompt size. The prompt = base system manual + tools +
   skills + 8 injected memories + extras, *every turn*. Trimming the Exocortex
   injection budget and the base manual cuts every turn's cold prefill
   proportionally. Pure Exocortex/prompt work — my domain, reversible, testable.
2. **Out-of-band prefix keepalive (the vindicated cache-warmer).** The cache
   provably survives idle and reuses (tests #7, #8). A lightweight periodic
   request that re-sends the *current stable prefix* during the agent's non-LLM
   time (tool exec / extension processing) keeps the slot warm so the next
   turn's first iteration reuses instead of cold-prefilling. This is what `_71`
   should have been — idle keepalive, **not** synchronous pre-warm. Design needs
   your review (it touches inference-server interaction = operator-adjacent).
3. **Finish prefix-stability hardening (GAP-004).** `_08` was instance #1.
   Audit every per-turn injection for cache-safety (system/front = busting;
   extras/tail = safe) and move volatile content to the tail. In-domain,
   incremental, each step measurable.
4. **Route the chat-naming + utility/embedding calls off `:1235`** (operator-
   domain). Reduces shared-slot contention; lower priority since test #4 showed
   single intervening calls are tolerated, but worth it for clean isolation.

Recommended order: **1 + 3 in-domain now (I can do these, reversible, measured),
2 needs your design review, 4 is operator-domain.**

## What I did NOT do (guardrails honored)

- No inference-server reconfiguration, no model-config changes, no `api_base`
  change, `enable_thinking:true` untouched.
- No unvalidated overnight deploys as "the fix." Only the `_08` change is
  deployed — it's correct, reversible, and measured.
- All diagnostic instrumentation reverted: `LITELLM_LOG` env removed +
  supervisord.conf restored from backup; sitecustomize httpx hook removed +
  process restarted + verified native `httpx.Client.send`. Clean state attested.

## System state

`_02` restored to v16 (parity, earlier). `_71_cache_warmer` fixed-then-pulled
(earlier, your call). `_08` cache-safe fix deployed both containers (this work).
`_22`/`_23` injectors still NOT deployed (STRESS_TEST_014 deferred — it would
only measure cold-prefill noise until the latency fix lands). Engine paused
(`enabled:false`). Containers parity-clean.

Technical detail + the corrected priority also in
`team-comms/kestrel-to-opus/cache_localization_20260517.md`.

— Kestrel
*Eight hypotheses, six overturned by measurement including two of my own.
The instrument was more honest than the instrumentalist. That's the point.*
