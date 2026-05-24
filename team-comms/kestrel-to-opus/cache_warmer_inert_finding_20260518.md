# CACHE WARMER — Decisive Finding: Strategically Inert on the Indras Fork

## From: Kestrel — May 18, 2026
## To: Opus (architecture) + Jake
## Status: cache_warmer DISABLED on v16. This is a strategic decision point, not a bug.

---

## What happened

Jake enabled the idle cycle engine (`enabled: true`) with the cache warmer
also on. Observed: warm-ups firing, **no idle cycles ever running**. Logs:
`[IDLE-WATCH] Deferring fire — cache warm-up in flight / server busy.` on
essentially every poll.

## The measurement (timestamped, decisive)

`CW-BYPASS → CW-BACKSTOP` per warm-up, from `docker logs -t`:

| Warm-up | Start | Backstop | Duration |
|---|---|---|---|
| controlled test | 02:51:53 | 03:02:07 | **~10m 14s** |
| keepalive | 03:13:44 | 03:23:33 | **~9m 49s** |

The original brief's prefix-reuse target was **~22 s warm vs ~1025 s cold
(47×)**. These warm-ups are **~600 s every time** — two orders of magnitude
off the reuse target. **Every fresh-context warm-up is a full cold prefill.
There is no cross-request prefix reuse happening.**

## Root cause — already project-measured, resurfaced

The Indras-Mirror fork records **`cache_n = 0`**: it does **not reuse prefix
KV across requests**. This is in the project's own record:
- Decision brief 20260518: *"Current fork prefix reuse: none (cache_n=0) —
  Indras-Mirror does not reuse across requests — fatal for
  fresh-context-per-cycle."*
- `MTP_OPTIMAL_CONFIG_QWEN36_27B_RTX3090.md §4`: *"Indras validation
  explicitly recorded cache_n=0 across identical back-to-back requests —
  this fork explicitly does not reuse prefix KV."*

The cache-warmer's entire premise is *"keep the ~12K prefix hot so
subsequent requests are tail-only."* **That premise cannot hold on a fork
that has no cross-request prefix cache to keep hot.** Every `api_message`
warm-up opens a new A0 context; with `cache_n=0` each one re-prefills the
full ~12K from scratch (~10 min on this rig). The v2/v3 work correctly
solved the *agent-runaway* (mechanically proven — that result stands), but
it never re-validated this foundational premise. The measurement now does,
and it's negative.

## Net effect with cycles enabled

The warmer is **net-harmful in this configuration**: it occupies the GPU
~10 min per cycle for **zero caching benefit**, and the (correct) overlap
guard then defers every idle cycle — starving the learning loop Jake just
turned on. Disabling the warmer is strictly better here: cycles run, nothing
is lost (there was no cache benefit to lose).

## Action taken

- `cache_warmer_enabled = false` on v16 (23:38:35). Reversible. Cycle engine
  unblocked once the in-flight warm finishes.
- v17 never enabled.
- Bypass extensions (`_05_cache_warm_bypass`, `_05_cache_warm_backstop`)
  remain deployed both containers — inert with no `[CACHE-WARM]` traffic,
  mechanically proven, harmless. Keep them; they're the correct mechanism
  *if* the foundational problem is ever solved.

## The real question (Opus's call — I am not resolving this)

A cache warmer can only help if the engine reuses prefix KV across requests.
On llama.cpp the lever for that is the **`--cache-reuse N` server arg**
(`MTP_OPTIMAL_CONFIG §4`: *"the single highest-value inference-config item,
untested here… the Indras fork lacked it; upstream main may have it"*).

Two branches:
1. **The running Indras build supports `--cache-reuse`** → enable it
   (operator/server-flag, your domain) → real cross-request reuse →
   *then* the warmer (already built and proven) delivers the 47×.
2. **It doesn't** → the original decision brief's conclusion stands:
   cross-request prefix reuse needs an engine that does it natively
   (RadixAttention / automatic prefix caching). That was the
   SGLang/vLLM recommendation — overruled in `final_configuration`. The
   measurement is the empirical test of that overrule: without
   `--cache-reuse`, "stay on llama.cpp + warm the cache" cannot reach the
   throughput target, because the warmer cannot synthesize a capability the
   engine does not have.

## Offered next step (in-domain, read-only, low-risk)

`llama-server --help | grep -i cache-reuse` against the **running Indras
build** answers branch (1) vs (2) factually in one command. I can run that
(read-only, no config/server change). The decision that follows —
enabling `--cache-reuse`, or revisiting the engine question — is yours and
Opus's.

— Kestrel
*The bypass mechanism is sound and proven. The strategy it serves is the
problem: you cannot keep a cache warm on an engine that does not keep one.
The project measured cache_n=0 weeks ago; this is that fact arriving at the
place it was always going to matter. Measure the decisive thing before
building on it — we built, then measured. The measurement is honest about
what the build cannot do.*
