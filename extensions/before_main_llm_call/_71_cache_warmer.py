"""
KV Cache Pre-Warmer — eliminates 3-5 min first-turn TTFT on Qwen3.6-27B-MTP.

Design: Opus, May 14 2026 (session 113)
Ref: team-comms/opus-to-kestrel/cache_warmer_extension_spec_20260514.md

Hook: before_main_llm_call (fires after prepare_prompt(), so loop_data.system is
populated with the exact system prompt that A0 will send — guaranteed prefix match).

Primary use: detect that the bat-file trigger already warmed the cache and return
immediately (fast path, <1s). Fallback: warm synchronously if cache is cold.
HTTP done via urllib.request + asyncio.to_thread (no aiohttp dependency).
"""

import asyncio
import json
import time
import urllib.request
import urllib.error
from typing import Any

from python.helpers.extension import Extension
from python.helpers import log
from agent import LoopData

WARM_FLAG = "_cache_warmed"
SERVER_URL = "http://host.docker.internal:1235"
HOT_THRESHOLD = 1000  # n_past tokens considered a warm cache


def _http_get_json(url: str, timeout: int = 5) -> dict | None:
    """Synchronous GET, returns parsed JSON or None on failure."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _http_post_json(url: str, payload: dict, timeout: int = 600) -> dict | None:
    """Synchronous POST with JSON payload, returns parsed JSON or None."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        log.warning("[CACHE-WARM] HTTP error: %s", e)
        return None


class CacheWarmer(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs: Any):
        # Skip if already warmed this conversation
        if self.agent.get_data(WARM_FLAG):
            return

        # Fast path: check /slots — if n_past > threshold, bat-file trigger already ran
        hot = await asyncio.to_thread(self._check_cache_warm)
        if hot:
            self.agent.set_data(WARM_FLAG, True)
            return

        # Cache is cold. Warm using loop_data.system which prepare_prompt() just
        # assembled — this is the exact same prompt A0 will send (perfect prefix match).
        system_parts = getattr(loop_data, "system", None)
        if not system_parts:
            log.warning("[CACHE-WARM] loop_data.system empty — skipping warm-up")
            self.agent.set_data(WARM_FLAG, True)
            return

        system_prompt = "\n\n".join(system_parts)
        await asyncio.to_thread(self._warm_cache, system_prompt)
        self.agent.set_data(WARM_FLAG, True)

    def _check_cache_warm(self) -> bool:
        """Return True if any slot already has > HOT_THRESHOLD cached tokens."""
        result = _http_get_json(f"{SERVER_URL}/slots", timeout=5)
        if result is None:
            return False  # server busy or unreachable — proceed with warm-up
        slots = result if isinstance(result, list) else result.get("slots", [])
        for slot in slots:
            # n_past can be None in the JSON when the slot is freshly initialized
            n_past = slot.get("n_past") or 0
            if n_past > HOT_THRESHOLD:
                log.info(
                    "[CACHE-WARM] Cache already hot (slot n_past=%d) — Turn 1 will be fast",
                    n_past,
                )
                return True
        return False

    def _warm_cache(self, system_prompt: str):
        """
        Send a minimal completion with the full system prompt to populate KV cache.
        max_tokens=1 stops immediately after prefill. enable_thinking=False avoids
        generating reasoning tokens in this throw-away request.
        """
        log.info(
            "[CACHE-WARM] Cache cold — warming KV cache (~3-5 min). "
            "Turn 1 LLM call will be fast once this completes."
        )
        start = time.time()

        payload = {
            "model": "qwen",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Respond with OK."},
            ],
            "max_tokens": 1,
            "enable_thinking": False,
            "cache_prompt": True,
            "stream": False,
        }

        result = _http_post_json(f"{SERVER_URL}/v1/chat/completions", payload, timeout=600)
        elapsed = time.time() - start

        if result:
            prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
            log.info(
                "[CACHE-WARM] Complete in %.1fs. Prefilled %d tokens. Cache is hot.",
                elapsed,
                prompt_tokens,
            )
        else:
            log.warning("[CACHE-WARM] Warm-up may have failed (%.1fs elapsed).", elapsed)
