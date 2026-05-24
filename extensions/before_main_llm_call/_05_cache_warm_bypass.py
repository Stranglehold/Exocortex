"""
Cache-Warm Bypass — Detector (behavioral layer, part 1 of 2)
============================================================
Hook: before_main_llm_call
Priority: _05 (very early — before BST/PACE/reasoning enrichment)

Pairs with: _functions/agent/Agent/call_chat_model/end/_05_cache_warm_backstop.py

Purpose
-------
The cache warmer (idle_watch.py) sends a trivial message tagged
``[CACHE-WARM]`` through A0's real API so A0 builds its real ~12K system
prefix and llama-server prefills it (KV cache warms). The PROBLEM measured
2026-05-18: a real message through A0 is a full agent invocation —
BST classified ``[CACHE-WARM] Respond with OK`` as a *coding task*, PACE
built a 3-step plan, the agent ran ``code_execution_tool`` for 14+ minutes.
The cache warms during *prefill* (before the agent does anything); the
agent loop afterward is unwanted.

This extension is the DETECTOR. It runs before ``call_chat_model`` and, if
the current user message carries the ``[CACHE-WARM]`` tag, sets a one-shot
flag on the agent. The paired backstop at ``call_chat_model/end`` reads the
flag and replaces the model result with a ``response`` tool call so the
monologue loop exits after exactly one (prefill-bearing) turn — no PACE,
no tool execution, no autonomous coding session.

Why detect here and substitute there (verified against agent.py):
  monologue: prepare_prompt → before_main_llm_call (HERE) → call_chat_model
             (prefill) → call_chat_model/end (BACKSTOP) → process_tools.
  A message rewrite here is too late to reach the model (the prompt is
  already assembled — the seam-#7 timing that moved _22/_23 to
  message_loop_prompts_after). So this layer ONLY sets the flag, correctly
  timed before the model call. Correctness is mechanical, in the backstop.

Reads:  loop_data.user_message / loop_data.history_output (tag detection)
Writes: agent data key ``_cache_warm`` (bool, one-shot; self-heals to False
        when the tag is absent so a reused context can't carry a stale flag)
Log tag: [CW-BYPASS]
"""

from typing import Any

from agent import LoopData
from helpers.extension import Extension

CACHE_WARM_TAG = "[CACHE-WARM]"
CACHE_WARM_FLAG = "_cache_warm"


class CacheWarmBypass(Extension):
    """before_main_llm_call: flag [CACHE-WARM] turns for the backstop."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            tagged = _is_cache_warm(loop_data)

            # One-shot + self-healing: only True for a tagged turn; cleared
            # otherwise so a reused/throwaway context cannot carry a stale flag.
            if tagged:
                self.agent.set_data(CACHE_WARM_FLAG, True)
                print("[CW-BYPASS] [CACHE-WARM] detected — flag set; "
                      "backstop will force 1-turn exit after prefill.",
                      flush=True)
            else:
                if self.agent.get_data(CACHE_WARM_FLAG):
                    self.agent.set_data(CACHE_WARM_FLAG, False)
        except Exception as e:
            # Graceful degradation — never break the main LLM path.
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[CW-BYPASS] error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Inline helpers (no cross-extension imports) ──────────────────────────────

def _text_of(obj: Any) -> str:
    """Best-effort text extraction — A0 messages may be dicts, objects with
    .content/.message, or plain strings. Don't assume one shape."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for k in ("content", "message", "text"):
            v = obj.get(k)
            if isinstance(v, str) and v:
                return v
        return str(obj)
    for attr in ("content", "message", "text"):
        v = getattr(obj, attr, None)
        if isinstance(v, str) and v:
            return v
    return str(obj)


def _is_cache_warm(loop_data: LoopData) -> bool:
    # Primary: the loop's current user message (set at loop start).
    if CACHE_WARM_TAG in _text_of(getattr(loop_data, "user_message", None)):
        return True
    # Fallback: last user item in assembled history (the _22/_23 accessor).
    history = getattr(loop_data, "history_output", None) or []
    for msg in reversed(history):
        if isinstance(msg, dict):
            if not msg.get("ai", True):
                return CACHE_WARM_TAG in _text_of(msg)
        else:
            return False
    return False
