"""
Proactive Reasoning Supervisor — Buffer Hook
============================================
Hook: reasoning_stream
Priority: _12 (v1.6 path: extensions/python/reasoning_stream/)

Accumulates the model's reasoning text into agent data so the
reasoning_stream_end hook can analyze the complete thinking block
after generation completes.

One responsibility: keep the buffer current. The reasoning_stream hook
fires per-chunk with the FULL accumulated text so far, so each call
simply overwrites the previous value. By the time reasoning_stream_end
fires, this buffer contains the complete reasoning for the turn.

Companion files:
  reasoning_stream_end/_12_proactive_supervisor.py  — analyze + flag
  before_main_llm_call/_12_proactive_supervisor.py  — inject corrections

Agent data keys (shared across all three hooks):
  _ps_rs_buf   — full reasoning text for current turn
  _ps_signal   — dict: signal_class, severity, evidence, redirect
  _ps_fired    — bool: intervention will be injected next turn

Log tag: [PS-BUF]
"""

from agent import LoopData
from helpers.extension import Extension

# Agent data key for reasoning buffer (read by reasoning_stream_end)
RS_BUF_KEY = "_ps_rs_buf"


class ProactiveSupervisorBuffer(Extension):
    """reasoning_stream: accumulate full reasoning text into agent data buffer."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # reasoning_stream fires per-chunk with full accumulated text in 'text' kwarg
            text = kwargs.get("text", "")
            if text:
                self.agent.set_data(RS_BUF_KEY, text)
        except Exception as e:
            print(f"[PS-BUF] Error: {e}", flush=True)
