# KV-Cache Localization — Findings (with an honest magnitude revision)
## Kestrel → Opus / Jake, 2026-05-17
## Re: "Find the datetime. Map the injection order."

---

## TL;DR

The mechanism you predicted is real and proven (controlled experiment: front-prefix
change = 114s→full re-prefill; tail change = 7s; **16×**). But the localization of
v16's *actual* assembled prompt **partially revises the magnitude story**, and I want
to be precise rather than confirm the dramatic version:

- **The injection architecture is already mostly cache-safe by position.** No canonical
  `before_main_llm_call` / `message_loop_prompts_after` extension writes to
  `loop_data.system` (the front/prefix). BST, PACE, memory (`_55/_56`), constraint
  heartbeat (`_21`), completion tracker — **all write to `extras_*`**, which the
  assembler appends *after* history (the tail). They are not front-region cache-busters.
- **The one confirmed per-message cache-buster is the datetime** — but it sits at
  **~89%** of the prompt (in the `extras` block), not the front. So it busts roughly
  the **last ~11% (~1,900 of ~17,200 tokens)** per turn, not the whole thing.
- The "16× being destroyed every turn by front injection" scenario is **not what the
  evidence shows for v16's current prompt.** The mechanism is genuine; v16's actual
  volatility is tail-concentrated. I'd be overclaiming if I reported otherwise.

This is still a real, fixable waste — just smaller than the worst case, and with a
second, larger cost (cold Turn-1) sitting next to it.

---

## What the assembler actually does (from `agent.py:prepare_prompt`)

```python
full_prompt = [ SystemMessage(system_text), *history_langchain ]
#   system_text         = "\n\n".join(loop_data.system)            ← FRONT (prefix)
#   history_langchain   = output_langchain(history_output + extras) ← extras at the TAIL
```

So the **cache-safety column** you asked for, grounded in evidence:

| Injection target | Lands at | Cache-safe? | Who uses it |
|---|---|---|---|
| `loop_data.system` (via `system_prompt` hook) | **front / prefix** | safe **iff static** | `_10_main_prompt`, `_11_tools`, `_15_exocortex_stack` |
| `loop_data.extras_persistent` / `extras_temporary` | **tail** (after history) | **position-safe** (but content can still be per-message volatile) | `_11` BST, `_12`, `_14` PACE, `_15` karpathy, `_21` heartbeat, `_55/_56` memory |
| `loop_data.history_output[-1]` mutation | current user msg (mid/tail) | per-turn new msg; prior history stable | `_13`, `_14`, and `_22`/`_23` when deployed |
| `agent.context.extras.md` block (datetime, agent_info) | **~89%** | **per-message volatile → busts the tail** | A0 framework |

`_15_exocortex_stack.py` appends to the system prompt (front) but its own docstring
states it injects **static** capability summaries and explicitly defers dynamic
per-turn content to the extras-based injectors. Front region appears stable.

## The datetime — confirmed

- Rendered in the prompt as: `current datetime: 2026-05-17 22:04:09-04:00` — **second
  precision**, changes every message (consecutive turns are always ≥1s apart).
- Position: **offset 53,454 / 59,790 chars ≈ 89.4%**, inside the `extras` block
  (`"current_datetime": "...", "agent_info": "..."`), i.e. appended after history.
- (The microsecond ISO strings in `chat.json` are `created_at`/`last_message`
  *metadata*, not in the prompt body — ruled out. The ISO timestamp at 49% is a
  *static example* in the scheduler tool docs — ruled out.)

## Honest accounting of the 58-minute / ~11-min-per-turn run

Evidence supports this decomposition (one part measured, one part inferred, flagged):

1. **Cold Turn-1: ~7-8 min, unavoidable without a pre-warmer.** Real prompt is
   **~17,200 tokens**; observed cold prefill ≈ 37 tok/s → ~465s for a full cold
   prefill. This is the single biggest fixed cost and it is *not* a cache bug — it's
   the absence of a working pre-warmer (we correctly pulled the broken `_71`).
2. **Per-turn tail re-prefill from the datetime bust point (~89%): ~1,900 tokens ≈
   ~50s/turn.** Real but modest.
3. **Thinking-token generation per turn: large.** `enable_thinking:true` (your quality
   call) — the format test showed ~5-6k reasoning chars/turn; that's minutes of
   generation per turn at thinking-phase speed, ×5 turns. **This is plausibly the
   dominant variable cost, not the cache.**

I cannot yet *prove* the exact first-divergence offset between consecutive turns
without a 2-turn capture (see open question). If history is reformatted per turn or
something in 0–89% varies, the bust is higher and worse; if not, it's the ~11% tail.
The structural map found **no volatile markers in 0–75%**, which argues for the
tail-only case — but that's structural inference, not the definitive 2-turn diff.

## Fixes (prioritized, honest about expected payoff)

1. **Coarsen the datetime granularity — trivial, deploy now, real but bounded win.**
   `agent.system.datetime.md` → render date + hour (or date only), not seconds.
   Stops the tail-bust on most consecutive turns (turns within the same hour reuse
   the full prefix). Zero quality cost. **This is the cheap, safe, do-it-now fix** —
   but expect it to recover the ~11% tail (~50s/turn), not a 16×.
2. **Move the datetime out of the per-turn extras into stable system, or to the very
   end.** If it must be second-precision, it should be the *last* thing in the prompt
   so it busts nothing after it (Test B: volatile-at-very-end ≈ free).
3. **Build a correct out-of-band pre-warmer — biggest single win.** The ~7-8 min cold
   Turn-1 dwarfs the datetime tail. A pre-warmer that prefills the stable system
   prefix at server idle (NOT synchronously in the agent path — that was `_71`'s sin)
   eliminates it. This is the real headline, and it's the legitimate version of what
   the broken `_71` attempted.
4. **`_22`/`_23` deployment guardrail:** they mutate `history_output[-1]`. Confirmed
   this is the current user message (near tail), so per-turn it's acceptable, but
   GAP-004 Phase B (write to `extras_persistent`) keeps them definitively tail-safe.
   Not a blocker; a correctness preference.

## The one open question worth one more measurement

Definitive proof of the per-turn bust offset = capture `agents[0].data.ctx_window`
on **two consecutive real turns** and diff for the first differing byte. That turns
"~11% tail (structural inference)" into a measured number and tells us whether the
history region is stable. ~2 cheap turns. **Recommend doing this before investing in
the pre-warmer build**, so the pre-warmer is sized against measured reality.

## Bottom line

Mechanism: proven. v16 reality: the injection architecture is largely cache-safe
already; the datetime is a genuine but tail-bounded (~11%) per-message buster;
the dominant cost is cold Turn-1 (~7-8 min, no pre-warmer) plus thinking-token
volume (your deliberate quality tradeoff). The "stop destroying the cache every
turn via injection ordering" framing is directionally right but, on the evidence,
**v16 isn't currently bleeding a 16× to front-region injection** — it's bleeding
cold-start and a tail datetime. I'd rather hand you the accurate smaller number
than the dramatic one. Cheap fixes (#1, #2) deploy now; the real win (#3) deserves
the 2-turn measurement first.

---

## ADDENDUM — 2-turn measurement OVERTURNS the above. Read this; it supersedes the priority.

The body of this report was structural inference. Jake's measurement-first call was
right and it overturned it. Two definitive experiments:

**Experiment 1 — server caching behavior (direct, controlled):**

| request shape | 1st (cold) | 2nd (same prefix) |
|---|---|---|
| no `cache_prompt` key (A0's nominal shape) | cache_n=0, 83.8s | **cache_n=3411, 7.7s — REUSES** |
| `cache_prompt: false` explicit | cache_n=0, 86.2s | **cache_n=0, 85.2s — NO REUSE** |
| `cache_prompt: true` explicit | cache_n=0, 7.7s* | cache_n=3411, 7.8s — REUSES |

The server **caches by default**. The *only* request shape that produces "every
call re-prefills the full prompt even when the prefix is byte-identical" is
**`cache_prompt: false`**.

**Experiment 2 — two consecutive real agent turns, same context:**
- T1 cold: 14,698 tok, **550s**. T2 (consecutive, same context): 14,810 tok, **533s**.
- The two assembled prompts are **byte-identical for the first 82.7%** (chars
  0–44,896 verified identical, including the entire system prompt).
- A byte-identical 82.7% prefix against a cache-by-default server **must** yield
  large reuse → T2 should have been ~5× faster. **It got essentially zero benefit
  (533s ≈ 550s).** That outcome is only possible if caching is being actively
  disabled on the live request — the exact signature of `cache_prompt: false`.

**Root cause (measurement-driven, supersedes the datetime framing):**
Prompt caching is **effectively OFF on every live A0→llama request**. Every turn
of every interaction pays a full cold prefill of ~15K tokens (~9 min) regardless
of prefix stability. Code corroborates the mechanism: `models.py:376` injects
Anthropic `cache_control:{"type":"ephemeral"}` toward a **llama.cpp** server that
doesn't speak Anthropic cache hints; the litellm/lm_studio translation or a
default ends up suppressing the server's native prefix cache (the `cache_prompt:
false` signature).

**Corrected priority:**
1. **Stop disabling the server prefix cache on live requests** (don't send
   `cache_prompt:false`; don't push Anthropic `cache_control` to the llama.cpp
   provider). Potential **~65× on per-turn prefill** (550s → ~8s), every turn,
   every interaction. This is the entire latency story.
2. **A0 history re-render non-determinism** (the 82.7% divergence:
   `[Step N/80] {'user_message':...}` → `{"user_message":...}`). Independent
   prefix-stability bug; caps reuse even after #1. Real, but moot until #1.
3. **Datetime granularity/placement (89%)** — third-order. Only matters after 1 & 2.
   My original "datetime headline" was wrong-priority; the measurement corrected it.

**Decisive confirmatory next step:** capture the literal wire request A0 sends to
`:1235` (litellm debug or a logging proxy) to read the exact cache-disabling param,
then the fix is config-level: strip Anthropic `cache_control` for the llama.cpp
provider / ensure `cache_prompt` is not false. Recommend this before any datetime
or history work — it's potentially the whole 16–65×.

— Kestrel
