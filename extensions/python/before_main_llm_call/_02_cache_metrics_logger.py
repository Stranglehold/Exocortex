"""
Cache Metrics Logger — DeepSeek prompt-cache instrumentation
============================================================
Hook: before_main_llm_call (_02_) — registers a litellm success callback ONCE
per process. Captures the real token `usage` of every chat/utility model call
to a JSONL ledger, so we can measure actual cost and (when the provider reports
them) prompt-cache hit/miss tokens instead of projecting.

WHY a litellm callback and not a chat_model_call_after extension:
  A0 1.18's models.py stream loop reports OUTPUT tokens via approximate_tokens()
  (a length estimate) and never reads the API `usage` object. The only place the
  real usage surfaces is litellm's own success event. This callback reads it
  there without modifying A0's call path.

LIMITATION (measured, honest):
  DeepSeek only emits `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` on a
  streaming response when `stream_options.include_usage=true` is set. A0 does NOT
  set it, and adding it requires guarding models.py `_parse_chunk` against the
  empty-`choices` usage chunk (it does `chunk["choices"][0]` unguarded → IndexError).
  That guard is validated separately on the test container. Until it ships, this
  ledger captures litellm's reconstructed usage (token volume, possibly estimated;
  cache split only if the provider passes it through). It is enough to monitor
  per-call token volume and cost trends, and to confirm end-to-end plumbing.

Zero behavior change: purely additive success callback. Never raises into A0.
Ledger: /a0/usr/Exocortex/cache_metrics.jsonl  (one JSON object per line)
"""

import json
import os
import time

from agent import LoopData
from helpers.extension import Extension

_LEDGER = "/a0/usr/Exocortex/cache_metrics.jsonl"

# Process-level guard. The in-list type-name check below is the authoritative
# idempotency guard (survives module reload); this just short-circuits the common case.
_REGISTERED = False


def _usage_to_dict(usage) -> dict:
    """Best-effort flatten of a litellm/pydantic Usage object (or dict) to plain JSON."""
    if usage is None:
        return {}
    for attr in ("model_dump", "dict"):
        fn = getattr(usage, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    if isinstance(usage, dict):
        return dict(usage)
    out: dict = {}
    for k in dir(usage):
        if k.startswith("_"):
            continue
        try:
            v = getattr(usage, k)
        except Exception:
            continue
        if callable(v):
            continue
        if isinstance(v, (int, float, str, bool)) or v is None:
            out[k] = v
        else:
            for attr in ("model_dump", "dict"):
                fn = getattr(v, attr, None)
                if callable(fn):
                    try:
                        out[k] = fn()
                        break
                    except Exception:
                        pass
    return out


def _write(rec: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_LEDGER), exist_ok=True)
        with open(_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


def _record(kwargs, response_obj) -> None:
    try:
        usage = getattr(response_obj, "usage", None)
        if usage is None and isinstance(response_obj, dict):
            usage = response_obj.get("usage")
        model = ""
        try:
            model = kwargs.get("model") or getattr(response_obj, "model", "") or ""
        except Exception:
            pass
        opt = kwargs.get("optional_params", {}) or {}
        stream_opts = opt.get("stream_options") or kwargs.get("stream_options") or {}
        _write({
            "ts": round(time.time(), 3),
            "model": model,
            "usage": _usage_to_dict(usage),
            "stream_options": stream_opts,
        })
    except Exception:
        pass


def _register() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    import litellm

    try:
        from litellm.integrations.custom_logger import CustomLogger

        class _CacheMetricsLogger(CustomLogger):
            def log_success_event(self, kwargs, response_obj, start_time, end_time):
                _record(kwargs, response_obj)

            async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
                _record(kwargs, response_obj)

        if litellm.callbacks is None:
            litellm.callbacks = []
        if not any(type(cb).__name__ == "_CacheMetricsLogger" for cb in litellm.callbacks):
            litellm.callbacks.append(_CacheMetricsLogger())
        _REGISTERED = True
        print("[CACHE-METRICS] litellm CustomLogger registered.", flush=True)
        return
    except Exception as e:
        # Fallback: plain success_callback function (older/newer litellm shapes)
        try:
            def _cb(kwargs, completion_response, start_time, end_time):
                _record(kwargs, completion_response)

            if litellm.success_callback is None:
                litellm.success_callback = []
            if not any(getattr(c, "__name__", "") == "_cb" for c in litellm.success_callback):
                litellm.success_callback.append(_cb)
            _REGISTERED = True
            print(f"[CACHE-METRICS] success_callback registered (fallback: {e}).", flush=True)
        except Exception as e2:
            print(f"[CACHE-METRICS] registration failed (passthrough): {e2}", flush=True)


class CacheMetricsLogger(Extension):
    """Registers the litellm usage logger once. Cheap no-op on every subsequent turn."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            _register()
        except Exception as e:
            print(f"[CACHE-METRICS] execute error (passthrough): {e}", flush=True)
