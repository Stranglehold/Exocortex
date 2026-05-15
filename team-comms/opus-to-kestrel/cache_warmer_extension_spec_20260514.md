# KV CACHE PRE-WARMER — Extension Spec
## From: Opus — May 14, 2026
## To: Kestrel
## Priority: 🔴 HIGH — eliminates the 3-5 minute first-turn TTFT
## Depends on: Cache reuse fix (already applied), tool injection archive (Workstream B)
## Hook: `message_loop_start` (runs once when a new conversation begins)
## Additional trigger: Server startup, scheduled time, system activity detection

---

## The Problem

Qwen3.6-27B's GatedDeltaNet recurrent layers cannot parallelize prefill. At ~57 tok/s prefill rate, a 12-15K token system prompt takes 3-5 minutes to process on the first turn of every conversation. The cache reuse fix works for Turn 2+ (only delta processed, ~10-30 seconds). But Turn 1 is always a full prefill because the KV cache is empty.

This is the latency Jake experiences every time he starts a session. The 43.7 tok/s decode speed is invisible behind 3-5 minutes of prefill.

## The Solution

**Move the prefill to a time when nobody's waiting.**

Before Jake's first interaction, send a warm-up request containing the exact system prompt A0 will send. The KV cache builds during warm-up (3-5 minutes, background). When Jake's real message arrives, the system prompt is already cached. Turn 1 becomes effectively Turn 2.

**Expected result:** First-turn TTFT drops from 3-5 minutes to ~10-30 seconds.

---

## Architecture

### New Extension: `_71_cache_warmer.py`

**Hook:** `agent_loop_start` (or the earliest hook that fires before the first LLM call)

**Also callable from:** idle detector, server startup script, scheduled task

### How It Works

```
Server starts (or model loads)
         │
         ▼
┌─────────────────────┐
│  Cache Warmer fires  │
│  (background thread) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Build system prompt identical  │
│  to what A0 will send:          │
│  - Base system prompt            │
│  - Extension injections          │
│  - Native API tool schemas       │
│  (NO TOOL-REG, NO Tiered —      │
│   those are archived)            │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│  Send minimal completion:        │
│  POST /v1/chat/completions       │
│  {                               │
│    system: <full system prompt>, │
│    messages: [{user: "OK"}],     │
│    max_tokens: 1,                │
│    cache_prompt: true            │
│  }                               │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│  KV cache now contains the       │
│  system prompt. Server holds it. │
└─────────────┬───────────────────┘
              │
              ▼
   Jake's first real message arrives
              │
              ▼
┌─────────────────────────────────┐
│  llama-server matches prefix:    │
│  cache_n = 12000+ (reused)       │
│  prompt_n = 50-200 (new only)    │
│  TTFT: ~10-30 seconds            │
└─────────────────────────────────┘
```

---

## Implementation

### File: `extensions/agent_loop_start/_71_cache_warmer.py`

```python
"""
KV Cache Pre-Warmer
Sends a minimal request with the full system prompt to warm the KV cache
before the user's first interaction, eliminating 3-5 min first-turn TTFT.

Design: Opus, May 14, 2026
Ref: Session 113 — cache reuse bug + prefill latency analysis
"""

import asyncio
import aiohttp
import time
import json
from python.helpers.extension import Extension
from python.helpers import log

WARM_FLAG = "_cache_warmed"
WARM_LOCK = "_cache_warming"
SERVER_URL = "http://localhost:1235"  # MTP server port


class CacheWarmer(Extension):

    async def execute(self, loop_data=None, **kwargs):
        """
        Fires at agent_loop_start. If the cache hasn't been warmed
        this server session, warm it now.
        """
        
        # Check if already warmed (persists across turns within a conversation)
        if self.agent.get_data(WARM_FLAG):
            return  # Already warmed, skip
        
        # Check if warming is in progress (another turn triggered it)
        if self.agent.get_data(WARM_LOCK):
            return  # Warming in progress, skip
        
        # Check if server has a warm cache already
        # (e.g., from a startup warm or scheduled warm)
        if await self._check_cache_warm():
            self.agent.set_data(WARM_FLAG, True)
            return  # Cache is already hot
        
        # Warm the cache
        self.agent.set_data(WARM_LOCK, True)
        try:
            await self._warm_cache()
            self.agent.set_data(WARM_FLAG, True)
        except Exception as e:
            log.warning("Cache warmer failed: %s", str(e))
        finally:
            self.agent.set_data(WARM_LOCK, False)

    async def _check_cache_warm(self) -> bool:
        """
        Check if the server already has a warm cache by inspecting
        the /slots endpoint. If a slot has cached tokens > 0, 
        the cache is warm.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SERVER_URL}/slots",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        slots = await resp.json()
                        for slot in slots:
                            if slot.get("n_past", 0) > 0:
                                log.info("[CACHE-WARM] Cache already hot "
                                        "(slot has %d cached tokens)",
                                        slot["n_past"])
                                return True
        except Exception:
            pass  # Server might not support /slots, proceed with warming
        return False

    async def _warm_cache(self):
        """
        Send a minimal completion request with the full system prompt.
        We don't care about the response — we just want the KV cache built.
        """
        log.info("[CACHE-WARM] Starting KV cache warm-up...")
        start = time.time()
        
        # Build the system prompt exactly as A0 would send it.
        # This MUST match what the agent sends on a real turn,
        # or the cache prefix won't match and llama-server
        # will re-process from scratch.
        system_prompt = self._build_system_prompt()
        
        # Build the tool schemas exactly as A0 would send them.
        tools = self._build_tool_schemas()
        
        payload = {
            "model": "qwen",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Respond with OK."}
            ],
            "max_tokens": 1,
            "enable_thinking": False,
            "cache_prompt": True,
            "stream": False,
        }
        
        # Include tools if available (native API tool schemas)
        if tools:
            payload["tools"] = tools
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVER_URL}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 min max
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        elapsed = time.time() - start
                        
                        # Extract cache info from response
                        usage = result.get("usage", {})
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        
                        log.info(
                            "[CACHE-WARM] Complete in %.1fs. "
                            "Prefilled %d tokens. Cache is hot.",
                            elapsed, prompt_tokens
                        )
                    else:
                        body = await resp.text()
                        log.warning(
                            "[CACHE-WARM] Server returned %d: %s",
                            resp.status, body[:200]
                        )
        except asyncio.TimeoutError:
            log.warning("[CACHE-WARM] Timed out after 600s")
        except aiohttp.ClientError as e:
            log.warning("[CACHE-WARM] Connection error: %s", str(e))

    def _build_system_prompt(self) -> str:
        """
        Reconstruct the system prompt exactly as A0 would send it.
        
        CRITICAL: This must match the real system prompt character-for-character,
        or the cache prefix won't match and the warm-up is wasted.
        
        The safest approach: call the same method A0 uses to build its
        system prompt. If that's not accessible, reconstruct from the
        same sources (prompts/agent.system.main.md + active extensions).
        """
        # Option 1: If agent exposes a build_system_prompt method:
        # return self.agent.build_system_prompt()
        
        # Option 2: Read from the same source files A0 uses:
        # This needs to be adjusted based on actual A0 internals.
        # The key files are in /a0/usr/prompts/ and the extension
        # injection outputs.
        
        # KESTREL: Inspect how A0 constructs its system prompt in
        # the main agent loop. The warm-up MUST use the same construction.
        # If the agent has a method like `self.agent.system_prompt` or
        # builds it in `agent.py`, call that same path here.
        #
        # Placeholder — replace with actual construction:
        try:
            with open("/a0/usr/prompts/agent.system.main.md", "r") as f:
                base_prompt = f.read()
            return base_prompt
        except FileNotFoundError:
            log.warning("[CACHE-WARM] System prompt file not found")
            return "You are a helpful assistant."

    def _build_tool_schemas(self) -> list:
        """
        Build the native API tool schemas exactly as A0 would send them.
        
        After tool injection archive: the only tool schemas are the ones
        A0 registers natively (not TOOL-REG, not Tiered Tool Injection).
        These come from the agent's tool registry, not from extensions.
        """
        # KESTREL: Inspect how A0 builds its tools array for the API call.
        # The warm-up must include the same tools list so the full
        # request prefix matches.
        #
        # If A0 stores registered tools somewhere accessible:
        # return self.agent.get_registered_tools()
        #
        # Placeholder — return empty if unknown:
        return []
```

### Critical Implementation Notes

**1. System prompt MUST match exactly.**

This is the make-or-break detail. If the warm-up request's system prompt differs by even one character from what A0 sends on the real first turn, the cache prefix won't match and llama-server re-processes everything from scratch. The warm-up is wasted.

Kestrel: inspect `agent.py` or wherever A0 constructs the system prompt for the LLM call. The warm-up must call the same construction path. If A0 builds the prompt dynamically (injecting timestamps, session IDs, etc.), the warm-up needs to either:
- Use the same dynamic construction, OR
- Ensure the dynamic parts appear AFTER the static prefix (timestamps at the end, not the beginning — so the prefix still matches)

**2. Tool schemas MUST match exactly.**

Same principle. If A0 sends 49 tool schemas in the `tools` array, the warm-up must send the same 49 schemas. After archiving TOOL-REG and Tiered Tool Injection, the tools come from A0's native registry only — this is more deterministic and easier to replicate.

**3. The `enable_thinking: false` flag MUST be present.**

Without it, the Qwen3.6 chat template injects `<think>\n\n</think>\n\n` thinking tokens. If the warm-up includes these but the real request doesn't (or vice versa), the prefix won't match. Both must use the same flag.

**4. Single-slot server assumption.**

The MTP server runs with one slot (one concurrent request). The warm-up occupies that slot during prefill. If Jake sends a message while the warm-up is running, it will queue behind the warm-up. This is acceptable — the warm-up takes 3-5 minutes whether it happens before or during Jake's first message. At least with pre-warming, the delay happens in the background.

If we later move to multi-slot serving, the warm-up should target a dedicated slot.

---

## Trigger Conditions

The warm-up should fire in multiple scenarios:

### Trigger 1: Server Startup
Add to `start_mtp.bat` after the server health check:

```batch
:: Wait for server to be ready
:wait_health
curl -s --max-time 3 http://localhost:1235/health | findstr "ok" >nul
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto wait_health
)

:: Pre-warm the KV cache
echo [CACHE-WARM] Warming KV cache with system prompt...
curl -s -X POST http://localhost:1235/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen\",\"messages\":[{\"role\":\"system\",\"content\":\"SYSTEM_PROMPT_HERE\"},{\"role\":\"user\",\"content\":\"OK\"}],\"max_tokens\":1,\"enable_thinking\":false,\"cache_prompt\":true,\"stream\":false}" ^
  > nul
echo [CACHE-WARM] Cache is hot.
```

**Note:** The system prompt in the bat file needs to be the exact same prompt A0 sends. This is fragile — if the prompt changes, the bat file must be updated. The extension-based approach (Trigger 2) is more robust because it reads the prompt from the same source A0 uses.

### Trigger 2: Agent Loop Start (the extension above)
Fires when A0 begins a new conversation. If the cache is cold (server restarted, cache evicted), the extension warms it. If the cache is already hot (server startup warm or previous conversation), it skips.

### Trigger 3: Idle Detector Return
Add to `_70_idle_trigger.py`:

```python
async def on_user_return(self):
    """Called when idle detector senses Jake is back."""
    # Set power to interactive
    subprocess.run(["nvidia-smi", "-pl", "300"], capture_output=True)
    
    # Warm the cache if cold
    warmer = CacheWarmer(self.agent)
    await warmer._warm_cache()
```

### Trigger 4: Scheduled (optional)
A simple cron job or Windows Task Scheduler entry that sends the warm-up curl at a fixed time (e.g., 7:00 AM EST, 30 minutes before Jake typically starts work):

```bash
# crontab entry (Linux) or Task Scheduler (Windows)
0 7 * * * curl -s -X POST http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"system","content":"..."},{"role":"user","content":"OK"}],"max_tokens":1,"enable_thinking":false,"cache_prompt":true}' \
  > /dev/null 2>&1
```

---

## Verification

### How to confirm the warm-up worked:

**1. Check the server logs after warm-up:**
```
# Should see prefill activity during warm-up:
"prompt_tokens": 12000+
```

**2. Check the FIRST real A0 request's timings:**
```json
{
  "timings": {
    "cache_n": 12000,    // ← system prompt REUSED
    "prompt_n": 50,      // ← only Jake's message processed
  }
}
```

If `cache_n` is 0 on the first real request after warm-up: the system prompt didn't match. Check for differences between the warm-up payload and A0's actual payload.

**3. Time the first turn:**
- Without warm-up: 3-5 minutes TTFT
- With warm-up (cache hit): ~10-30 seconds TTFT
- If still 3-5 minutes: cache miss, investigate prefix mismatch

### Dashboard integration (Workstream C):

Add a "Cache Status" indicator to the inference monitor:
- 🟢 **Hot** — `cache_n > 0` on last request (warm-up successful or Turn 2+)
- 🟡 **Warming** — warm-up request in progress
- 🔴 **Cold** — no cache, next request will be full prefill

---

## Interaction with Other Workstreams

| Workstream | Interaction |
|-----------|-------------|
| **A (Cache Fix)** | REQUIRED — without the cache fix, warm-up tokens are never reused anyway |
| **B (Tool Injection Archive)** | HELPS — fewer tokens in system prompt = faster warm-up + more deterministic prefix matching |
| **C (Monitor Dashboard)** | OBSERVABILITY — dashboard shows cache status so Jake knows if warm-up succeeded |
| **D (Proactive Supervisor)** | INDEPENDENT — no interaction |

---

## Expected Outcome

### Before (current state):
```
Jake opens A0 → types message → waits 3-5 minutes → first token appears
Turn 2 → waits 10-30 seconds → response
Turn 3 → waits 10-30 seconds → response
```

### After (with pre-warmer):
```
Server starts → warm-up runs (3-5 min, background, nobody waiting)
Jake opens A0 → types message → waits 10-30 seconds → first token appears
Turn 2 → waits 10-30 seconds → response
Turn 3 → waits 10-30 seconds → response
```

The 3-5 minute cost doesn't disappear — it moves from "Jake is staring at a blank screen" to "the server is warming up while Jake is commuting / making coffee / waking up." The prefill happens. It just happens when nobody's waiting for it.

---

## Fallback

If the pre-warmer can't match the system prompt exactly (too dynamic, too many variables), there's a simpler fallback: **keep the MTP server running continuously and never restart it.** The cache persists across conversations as long as the server process stays alive. The warm-up cost is paid once (first conversation after server start) and then every subsequent conversation reuses the cached system prompt.

This is simpler but less robust — any server crash, model swap, or restart loses the cache and triggers a cold start. The pre-warmer is the proper solution because it recovers from cold starts automatically.

— Opus
