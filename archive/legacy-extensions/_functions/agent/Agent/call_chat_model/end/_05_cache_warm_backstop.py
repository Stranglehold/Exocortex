"""
Cache-Warm Backstop — Mechanical (part 2 of 2)
==============================================
Hook: _functions/agent/Agent/call_chat_model/end   (@extension.extensible
      implicit end-point of agent.Agent.call_chat_model)
Priority: _05

Pairs with: before_main_llm_call/_05_cache_warm_bypass.py (the detector)

Purpose
-------
GUARANTEES a cache-warm turn ends after exactly one prefill-bearing LLM
call — no PACE plan, no tool execution, no autonomous agent loop.

Verified mechanics (agent.py / helpers/extension.py / tools/response.py,
2026-05-18):
  - ``call_chat_model`` is ``@extension.extensible`` → after the wrapped
    function runs (the model call = PREFILL → KV cache warms), the implicit
    ``/end`` point runs and may **rewrite ``data["result"]``** (and clear
    ``data["exception"]``). ``data["result"]`` here is the return tuple
    ``(response, reasoning)``.
  - monologue does ``agent_response, _ = await self.call_chat_model(...)``
    then ``process_tools(agent_response)``. If ``agent_response`` is a
    ``response`` tool call, ``process_tools`` runs tools/response.py which
    returns ``Response(..., break_loop=True)`` → monologue
    ``if tools_result: return tools_result`` → loop exits. One turn.
  - The prefill already happened inside the wrapped call before this /end
    point — replacing the result does NOT lose the cache warm.

Why here and not ``tool_execute_before`` (the originally-named surface):
  ``tool_execute_before`` is a plain hook fired AFTER ``get_tool`` already
  resolved the tool object and immediately before ``tool.execute()``;
  reassigning a ``tool_name`` kwarg cannot rebind the caller's resolved
  tool, so it cannot force ``break_loop``. The ``@extensible`` /end point
  is the only verified surface that can substitute the response post-prefill
  without a core change.

Reads:  agent data key ``_cache_warm`` (set by the detector)
Writes: data["result"] = (RESPONSE_TOOL_JSON, ""); data["exception"] = None;
        clears the ``_cache_warm`` flag (one-shot)
Log tag: [CW-BACKSTOP]
"""

from typing import Any

from helpers.extension import Extension

CACHE_WARM_FLAG = "_cache_warm"
# Minimal, unambiguous response-tool call. process_tools → tools/response.py
# → Response(message=text, break_loop=True) → monologue loop exits.
_RESPONSE_TOOL_JSON = '{"tool_name": "response", "tool_args": {"text": "OK"}}'


class CacheWarmBackstop(Extension):
    """call_chat_model/end: force a 1-turn exit for flagged cache-warm turns.

    Sync execute() per the _functions/.../end convention (see the in-repo
    pattern source _functions/agent/Agent/get_tool/end/_10_multi_tool_resolver).
    """

    def execute(self, data: dict | None = None, **kwargs) -> None:
        try:
            if data is None:
                return
            if not self.agent.get_data(CACHE_WARM_FLAG):
                return

            # One-shot: consume the flag so nothing downstream re-triggers.
            self.agent.set_data(CACHE_WARM_FLAG, False)

            # Prefill already completed inside the wrapped call → cache warm.
            # Replace the (response, reasoning) tuple with a response-tool
            # call and clear any error so the loop gets a clean 1-turn exit
            # regardless of what the model generated (or if it raised).
            data["result"] = (_RESPONSE_TOOL_JSON, "")
            data["exception"] = None

            print("[CW-BACKSTOP] cache-warm turn: result replaced with "
                  "response tool — loop will exit after this prefill turn.",
                  flush=True)
        except Exception as e:
            # Never break the model-call path. If this fails the worst case
            # is the (already-measured) long warm-up, not a crash.
            try:
                print(f"[CW-BACKSTOP] error (passthrough): {e}", flush=True)
            except Exception:
                pass
