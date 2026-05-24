# CACHE WARMER v2 — Integrated into idle_watch.py
## From: Opus — May 18, 2026
## To: Kestrel
## Replaces: The pulled _71_cache_warmer.py extension
## Principle: Don't replicate A0's prompt. Use A0's prompt.

---

## Why v2 Is Different

The original cache warmer was a separate extension (`_71_cache_warmer.py`) that:
- Built the system prompt independently from A0
- Required the warm-up prompt to match A0's prompt character-for-character
- Had broken imports and a broken log API
- Was deployed to the wrong path twice
- Was pulled because it never worked

v2 is 40 lines inside `idle_watch.py`. It sends a warm-up request through A0's actual API. A0 builds its own system prompt, sends it to llama-server, the KV cache builds. No separate prompt construction. No matching requirement. The warm-up IS a real A0 request — just with a trivial message that gets a trivial response.

---

## Design

### The Core Function

```python
import requests
import time
import logging

logger = logging.getLogger("idle_watch")

# ── Cache Warmer ──────────────────────────────────────────

WARM_TIMEOUT = 900          # 15 min max — cold prefill on 12K prompt is ~5-8 min
KEEPALIVE_INTERVAL = 600    # 10 min between keepalive pings
COLD_CHECK_ENDPOINT = None  # Set to f"http://localhost:{SERVER_PORT}/slots" if server exposes it

def is_cache_cold(server_port: int) -> bool:
    """Check if the KV cache is cold (no cached tokens).
    
    Checks the /slots endpoint for n_past > 0.
    If the endpoint isn't available, assume cold (safe default).
    """
    try:
        resp = requests.get(
            f"http://localhost:{server_port}/slots",
            timeout=5
        )
        if resp.status_code == 200:
            slots = resp.json()
            # If any slot has cached tokens, cache is warm
            for slot in slots:
                if slot.get("n_past", 0) > 0:
                    return False
            return True  # All slots empty — cache is cold
    except Exception:
        pass
    return True  # Can't check — assume cold (safe default)


def warm_cache(a0_port: int, api_key: str, server_port: int) -> bool:
    """Send a minimal request through A0's real API to warm the KV cache.
    
    This is the entire cache warmer. A0 builds its actual system prompt
    (same extensions, same tool schemas, same memories, same everything),
    sends it to llama-server, and the KV cache builds. The response is
    discarded — we just want the cache populated.
    
    Returns True if the warm-up succeeded, False if it failed.
    """
    # Check if already warm — skip if so
    if not is_cache_cold(server_port):
        logger.info("[CACHE-WARM] Cache already hot — skipping warm-up")
        return True
    
    logger.info("[CACHE-WARM] Cache is cold — warming via A0 API...")
    start = time.time()
    
    try:
        resp = requests.post(
            f"http://localhost:{a0_port}/api/api_message",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={"message": "Respond with the single word OK."},
            timeout=WARM_TIMEOUT
        )
        
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            logger.info(
                "[CACHE-WARM] ✓ Cache warm in %.1fs. "
                "Next request should hit cached prefix.",
                elapsed
            )
            return True
        else:
            logger.warning(
                "[CACHE-WARM] A0 returned %d after %.1fs: %s",
                resp.status_code, elapsed, resp.text[:200]
            )
            return False
            
    except requests.Timeout:
        elapsed = time.time() - start
        logger.warning("[CACHE-WARM] Timed out after %.1fs", elapsed)
        return False
    except requests.ConnectionError:
        logger.warning("[CACHE-WARM] A0 not reachable at port %d", a0_port)
        return False
    except Exception as e:
        logger.warning("[CACHE-WARM] Unexpected error: %s", str(e))
        return False


def keepalive_ping(a0_port: int, api_key: str, server_port: int) -> bool:
    """Lightweight keepalive that prevents cache eviction during idle.
    
    Same mechanism as warm_cache but:
    - Only fires if the cache is already warm (skip if cold — that's
      warm_cache's job, and keepalive shouldn't pay a 5-min cold penalty)
    - Logs at debug level, not info (this is background maintenance)
    
    The ping sends a trivial message through A0. The system prompt
    hits the cache (already there), only the tiny message prefills,
    the response is discarded. The cache's internal LRU/eviction
    timer resets. Cost: ~1-2 seconds. Benefit: cache stays hot.
    """
    if is_cache_cold(server_port):
        # Cache is cold — don't try to keep alive something that's dead.
        # Let warm_cache handle the cold start.
        return False
    
    try:
        resp = requests.post(
            f"http://localhost:{a0_port}/api/api_message",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={"message": "OK"},
            timeout=30  # Should be fast — cache is warm
        )
        
        if resp.status_code == 200:
            logger.debug("[CACHE-WARM] Keepalive ping succeeded")
            return True
        else:
            logger.debug("[CACHE-WARM] Keepalive returned %d", resp.status_code)
            return False
            
    except Exception:
        return False
```

### Integration into idle_watch.py

The cache warmer integrates into the existing poll loop at three points:

```python
# ── In the idle_watch main loop ──────────────────────────

class IdleWatchDaemon:
    
    def __init__(self, config):
        self.config = config
        self.a0_port = config.get("a0_port", 32768)
        self.api_key = config.get("api_key", "")
        self.server_port = config.get("server_port", 1235)
        self.last_keepalive = 0
        self.server_was_down = True  # Assume cold on first boot
    
    def poll(self):
        """Called every 60 seconds by the main loop."""
        
        now = time.time()
        
        # ── Trigger 1: Server restart detection ──
        # If the server was down and is now up, warm the cache immediately.
        server_up = self._check_server_health()
        
        if server_up and self.server_was_down:
            logger.info("[CACHE-WARM] Server just came up — triggering warm-up")
            warm_cache(self.a0_port, self.api_key, self.server_port)
            self.server_was_down = False
            self.last_keepalive = now
            return  # Don't do anything else this poll — warm-up may take minutes
        
        if not server_up:
            self.server_was_down = True
            return  # Server is down, nothing to do
        
        # ── Trigger 2: Periodic keepalive ──
        # Every KEEPALIVE_INTERVAL seconds during idle, ping to keep cache warm.
        if now - self.last_keepalive >= KEEPALIVE_INTERVAL:
            if self._is_idle():  # Only during idle — don't interrupt active use
                keepalive_ping(self.a0_port, self.api_key, self.server_port)
                self.last_keepalive = now
        
        # ── Trigger 3: Pre-cycle warm ──
        # Before firing an idle cycle, check if cache is cold and warm if needed.
        # This is in the existing _atomic_check_and_fire path:
        if self._should_fire_cycle():
            if is_cache_cold(self.server_port):
                logger.info("[CACHE-WARM] Cache cold before idle cycle — warming first")
                warm_cache(self.a0_port, self.api_key, self.server_port)
            self._fire_cycle()
    
    def _check_server_health(self) -> bool:
        """Check if llama-server is responding."""
        try:
            resp = requests.get(
                f"http://localhost:{self.server_port}/health",
                timeout=3
            )
            return resp.status_code == 200
        except Exception:
            return False
    
    def _is_idle(self) -> bool:
        """Check if the system is idle (no active user, no running cycle)."""
        state = self._read_state()
        now = time.time()
        idle_threshold = self.config.get("idle_threshold_seconds", 1800)
        
        last_user = state.get("last_user_ts", 0)
        cycle_active = state.get("cycle_active", False)
        
        return (now - last_user >= idle_threshold) and not cycle_active
```

---

## How It Works End-to-End

### Scenario 1: Server starts, Jake arrives later

```
00:00  Server starts
00:01  idle_watch detects server up (was down) → warm_cache()
00:01  warm_cache sends "Respond with OK" through A0 API
00:01  A0 builds its real 12K system prompt + tool schemas
00:01  llama-server prefills 12K tokens (cold — takes 5-8 min)
00:07  warm_cache returns success. Cache is now hot.
00:07  idle_watch resumes normal polling
00:15  Keepalive ping fires (10 min since last) — 1-2 seconds, keeps cache alive
00:25  Keepalive ping fires again
...
01:30  Jake opens A0, types a message
01:30  A0 sends request to llama-server
01:30  llama-server: cache_n=12000+ (system prompt cached from warm-up)
01:30  Only Jake's message (~50 tokens) needs prefilling
01:30  TTFT: < 5 seconds
```

### Scenario 2: Idle engine fires a cycle

```
idle_watch detects idle threshold met → should fire cycle
idle_watch checks: is_cache_cold()?
  If cold → warm_cache() first (5-8 min, paid once)
  If warm → skip warm-up
idle_watch fires the cycle
Cycle Turn 1: cache hit, fast TTFT
Cycle Turn 2-N: cache reuse from Turn 1, fast TTFT
```

### Scenario 3: Keepalive prevents eviction during long idle

```
00:00  Last user activity
00:30  Idle threshold met
00:30  Idle cycle fires, completes at 00:45
00:45  System idle, no cycles queued (cooldown)
00:55  Keepalive ping — cache stays warm
01:05  Keepalive ping — cache stays warm
01:15  Keepalive ping — cache stays warm
02:00  Jake returns — cache is still warm from keepalive
02:00  TTFT: < 5 seconds
```

---

## Configuration

Add to `engine_state.json` or a separate `cache_config.json`:

```json
{
  "cache_warmer_enabled": true,
  "keepalive_interval_seconds": 600,
  "warm_timeout_seconds": 900,
  "warm_on_server_restart": true,
  "warm_before_idle_cycle": true,
  "keepalive_during_idle": true
}
```

All three triggers are independently toggleable. Start with all three enabled. If keepalive pings interfere with anything (unlikely — they're 1-2 second requests every 10 minutes), disable that one.

---

## What This Doesn't Do (Honest Bounds)

- **First cold prefill is still 5-8 minutes.** The warm-up doesn't eliminate this cost — it moves it to a time when nobody's waiting. After a server restart, the first request is slow regardless. The warm-up ensures it's the daemon's request, not Jake's.

- **If A0's system prompt changes between warm-up and real request** (different memories loaded, different extension state), the cache prefix might partially match instead of fully matching. This is unlikely during idle (system state is stable) but possible after a manual config change. Mitigation: the keepalive pings refresh the cache periodically, so even if the prompt drifts, the cache is at most 10 minutes stale.

- **The keepalive creates chat entries in A0.** Each ping is a minimal "OK" conversation. These should be flagged as cache-maintenance chats (not real user conversations) so they don't clutter Jake's chat history. Add a header or message tag that A0 can filter on:

```python
json={"message": "[CACHE-WARM] Respond with OK.", "_cache_warm": True}
```

If A0's API doesn't support metadata, the `[CACHE-WARM]` prefix in the message text is sufficient for filtering.

---

## Implementation Checklist

- [ ] Add `warm_cache()`, `keepalive_ping()`, and `is_cache_cold()` functions to `idle_watch.py`
- [ ] Add Trigger 1 (server restart detection) to the poll loop
- [ ] Add Trigger 2 (periodic keepalive) to the poll loop
- [ ] Add Trigger 3 (pre-cycle warm) to the fire path
- [ ] Add cache config fields to config file
- [ ] Test: restart server, verify warm-up fires automatically
- [ ] Test: send a request after warm-up, verify `cache_n > 0`
- [ ] Test: wait 15 minutes idle, verify keepalive pings in logs
- [ ] Test: fire an idle cycle, verify pre-cycle warm check runs
- [ ] Verify warm-up chats don't clutter Jake's chat history (filter or tag)

---

## Why This Works

The original cache warmer tried to replicate what A0 does. This one just asks A0 to do it. The system prompt is guaranteed to match because it IS the same system prompt — constructed by the same code, through the same API, with the same extensions. No separate prompt file. No matching requirement. No broken imports.

The daemon already runs. The HTTP client already exists. The API key is already configured. The poll loop already fires every 60 seconds. The cache warmer is 40 lines of code in the right place, not a separate extension deployed to the wrong path.

Simple. Robust. Testable. The cache warms itself.

— Opus
