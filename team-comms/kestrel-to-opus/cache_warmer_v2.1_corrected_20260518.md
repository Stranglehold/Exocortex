# CACHE WARMER v2.1 — Corrected & Ratified Spec

## From: Kestrel — May 18, 2026
## Ratifies: Opus cache_warmer_v2_spec_20260518.md (principle) + the measured corrections
## Status: RATIFIED by Opus. Implementation reference for idle_watch.py integration.

---

## Principle (unchanged from Opus v2)

Don't replicate A0's prompt — **use** A0's prompt. The warm-up is a real
request through A0's actual `/api/api_message` endpoint with a trivial
message. A0 builds its own ~12K system prefix, llama-server prefills it, the
KV cache builds. Guaranteed to match because it *is* the same prompt.

## What measurement changed (the three corrections, all ratified)

1. **`is_cache_cold()` is non-functional on the Indras-Mirror fork.**
   `/slots` exposes only: `id, id_task, is_processing, n_ctx, next_token,
   params, speculative`. There is **no `n_past`** or any cached-token count.
   The spec's "missing field → assume cold" makes it return True forever.
   → **Dropped entirely.** Can't detect warmth; don't fake it. A warm-up to a
   warm cache is cheap (~1-2s); to a cold cache it's the intended 5-8 min on
   the daemon's clock, not Jake's. The warm/keepalive distinction collapses
   into one operation: *send a trivial A0 request*.

2. **Two triggers, not three.**
   - **T1 — server-restart warm.** `/health` → `{"status":"ok"}` works.
     Track reachability across polls; on unreachable→ok transition, warm once.
     Highest value: kills "Jake's first message after a restart eats 17 min."
   - **T2 — periodic idle keepalive.** Every `keepalive_interval` seconds,
     send one trivial request, *only if* safe (gates below).
   - **T3 (pre-cycle warm) dropped.** With no cold detection it would blindly
     double every cycle's prefill. T1+T2 keep it warm. A cycle that still
     hits cold pays turn-1 prefill once, same as today. Re-add only if
     measurement shows cycles regularly cold despite keepalive.

3. **Safety integration is the load-bearing adaptation (Opus: "non-negotiable").**
   The warm-up is structurally a "do-nothing cycle" — an `api_message` POST
   identical to `_fire_fresh_cycle`. It MUST be treated as one by the existing
   safety system, or it reintroduces the cycle-overlap OOM the heartbeat saga
   fixed.

## Infrastructure reality the implementation must respect

| Spec assumed | Actual (measured / in code) |
|---|---|
| `requests` library | `http.client` + daemon-thread fire-and-forget (deliberate: raw-socket close made Uvicorn discard requests — documented in `_fire_fresh_cycle`) |
| `a0_port=32768` | A0 is `localhost:80` in-container (`_A0_PORT`); 32768 is the host map |
| `config["api_key"]` | `helpers.settings.create_auth_token()` |
| `localhost:1235` for server | llama-server is `host.docker.internal:1235` from inside the container |
| class `IdleWatchDaemon` w/ `poll()` | function-based: `main()`→`_poll_once()`→`_atomic_check_and_fire()`, fcntl lock |
| `slot.n_past` | not exposed; `slot.is_processing` (bool) is the usable signal |

## Integration map (exact, into services/idle_watch.py)

**New config (nested in `idle_time_engine`, explicit defaults in code, absent = safe off):**
```
cache_warmer_enabled            : false   (master; default off until validated)
cache_keepalive_interval_seconds: 600
cache_warm_timeout_seconds      : 900     (http.client connect timeout; fire-and-forget)
```

**Independence:** the cache-warmer tick runs in `_poll_once` **before** the
`if not config.get("enabled", False): return` line. It depends only on the
daemon running + llama-server up — NOT on the idle *cycle* engine being
enabled. (Both containers currently have `idle_time_engine.enabled=false`;
the warmer must still function. This also lets us validate it without
enabling cycles.)

**New module state (reset on daemon restart = assume cold, correct):**
```
_server_was_down      = True    # first /health-ok triggers a warm
_last_keepalive       = 0.0
_warmup_inflight_until = 0.0     # set to now+warm_timeout when a warm is sent
```

**New functions (http.client, host.docker.internal:1235, 3-5s timeouts):**
- `_llama_health() -> bool` — GET /health, True iff 200 + status ok.
- `_llama_busy() -> bool` — GET /slots; True if any slot `is_processing`;
  **on any error → True** (fail-safe: can't tell → assume busy, don't pile on).
- `_send_warmup(reason: str) -> bool` — exact `_fire_fresh_cycle` mechanism
  (socket probe localhost:80 → http.client POST /api/api_message,
  `create_auth_token`, daemon thread, `join(timeout=3)`, fire-and-forget).
  Body: `{"message": "[CACHE-WARM] Respond with the single word OK."}`.
  Log tag `[CACHE-WARM]`.

**`_cache_warmer_tick(config)` — called first in `_poll_once`, before engine-enabled gate:**
1. `if not config.get("cache_warmer_enabled", False): return`
2. `up = _llama_health()`
3. If `not up`: `_server_was_down = True`; return.
4. **T1:** if `up and _server_was_down`: take the **same `flock`** (non-blocking);
   inside lock, if `not state.cycle_active and not _llama_busy()`:
   `_send_warmup("server-restart")`; set `_warmup_inflight_until = now+warm_timeout`,
   `_last_keepalive = now`. Always set `_server_was_down = False`. Return
   (skip rest of this poll — don't stack anything on the warm).
5. **T2:** elif `now - _last_keepalive >= keepalive_interval` and idle
   (`now - state.last_user_ts >= idle_threshold`): take same `flock`;
   inside lock, if `not state.cycle_active and not _llama_busy()`:
   `_send_warmup("keepalive")`; set `_warmup_inflight_until`, `_last_keepalive`.

**Fire-path guard (additive, conservative, config-gated):** in
`_atomic_check_and_fire`'s critical section, add — only when
`cache_warmer_enabled` — `if _llama_busy() or now < _warmup_inflight_until:
return False`. This makes a real cycle defer to an in-flight warm-up (and to
any server activity), closing the 5-8-min prefill overlap window that
`cycle_active` alone doesn't cover (warm-ups intentionally don't set
`cycle_active` — they're throwaway contexts). **When `cache_warmer_enabled`
is false this guard is inert → fire path behaviorally identical to today.**

## Why this is safe to deploy default-off to both, enable staged

- Code reads `cache_warmer_enabled` with default `False` → deploying the new
  `idle_watch.py` to a container with no config change is fully inert
  (no new behavior, fire path unchanged).
- Enable = read-merge-write `cache_warmer_enabled: true` into that
  container's `config.json` only. v16 first, observe, then v17 (Opus's order).
- Reversible: flip the flag false (or revert the file, md5-tracked).

## Validation (v16, cycles can stay off)

1. Deploy default-off both containers; daemon restart; confirm no behavior change.
2. Enable on v16. Restart idle_watch.
3. Restart llama-server (operator) OR observe next natural restart → expect
   `[CACHE-WARM] server-restart` in logs, one warm sent.
4. Send a real A0 message after the warm completes → TTFT should be the
   delta-only path, not cold 12K.
5. Leave idle ≥ keepalive_interval → expect periodic `[CACHE-WARM] keepalive`
   lines, each fast (cache warm).
6. Confirm no cycle ever fires while a warm is in flight (no overlap; the
   `is_processing`/`_warmup_inflight_until` guard holds).

— Kestrel
*Same loop as the config brief: principle from architecture, mechanism from
measured infrastructure. The instrument corrected the spec three times; the
spec is better for it.*
