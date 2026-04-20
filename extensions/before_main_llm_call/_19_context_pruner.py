"""
Staleness-Aware Context Pruner — Proactive Interference Mitigation
==================================================================
Hook: before_main_llm_call (_19_)
Position: After BST/metacognitive injection, before LLM call

Compresses or removes stale tool outputs in loop_data.history_output
before each LLM call. Based on the SleepGate finding (arXiv 2603.14517):
stale KV cache entries don't just waste space — they actively compete
with current information, degrading retrieval accuracy.

This extension operates at the context layer (pre-token), complementing
the attention-level PI mitigation that requires llama.cpp access. Both
layers are needed; this is Layer 1.

Measurement target: BST domain classification accuracy across conversation
length. The 20-turn collapse is the PI baseline. Improvement validates
PI as the mechanism and justifies the llama-cpp-python migration.

Tool result structure (from agent.py hist_add_tool_result):
  {"tool_name": str, "tool_result": str}  stored as ai=False

No LLM calls. Deterministic. Graceful passthrough on any error.
"""

from __future__ import annotations

import json
from typing import Any

from agent import LoopData
from helpers.extension import Extension

CONFIG_KEY = "context_pruner"

DEFAULT_CONFIG = {
    "enabled": True,
    "preserve_last_n": 3,           # always keep N most recent tool outputs intact
    "compress_after_n": 5,          # compress tool outputs beyond this rank from end
    "remove_errors_after_n": 2,     # remove error outputs beyond this rank from end
    "max_compressed_chars": 600,    # chars to keep when compressing
    "min_history_length": 8,        # skip pruning in short conversations
}

# Signals that identify an error tool output
_ERROR_SIGNALS = (
    "Error", "error", "ERROR",
    "Failed", "failed", "FAILED",
    "Exception", "exception",
    "Traceback", "traceback",
    "not found", "Not found",
    "Permission denied",
    "Connection refused",
    "Timed out", "timed out", "timeout",
    "No such file",
    "command not found",
)


class ContextPruner(Extension):
    """Compress stale tool outputs before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            history = loop_data.history_output
            if not history:
                return

            min_len = cfg.get("min_history_length", DEFAULT_CONFIG["min_history_length"])
            if len(history) < min_len:
                return

            removed, compressed = _prune(history, cfg)

            if removed > 0 or compressed > 0:
                print(
                    f"[CTX-PRUNE] history_len={len(history)} "
                    f"removed={removed} compressed={compressed}",
                    flush=True,
                )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[CTX-PRUNE] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Pruning Logic ──────────────────────────────────────────────────────────────

def _prune(history: list, cfg: dict) -> tuple[int, int]:
    """
    Walk history_output, find tool result messages, compress/remove stale ones.

    Tool results are ai=False messages with content dict containing
    'tool_name' and 'tool_result' keys (from agent.py hist_add_tool_result).

    Ranking is by position from the END of history — rank 0 = most recent
    tool result, rank N = oldest. High rank = more stale.
    """
    preserve_n = cfg.get("preserve_last_n", DEFAULT_CONFIG["preserve_last_n"])
    compress_after = cfg.get("compress_after_n", DEFAULT_CONFIG["compress_after_n"])
    remove_errors_after = cfg.get("remove_errors_after_n", DEFAULT_CONFIG["remove_errors_after_n"])
    max_chars = cfg.get("max_compressed_chars", DEFAULT_CONFIG["max_compressed_chars"])

    # Collect indices of tool result messages (oldest first)
    tool_result_indices = [
        i for i, msg in enumerate(history)
        if isinstance(msg, dict)
        and not msg.get("ai", True)
        and _is_tool_result(msg.get("content"))
    ]

    removed = 0
    compressed = 0

    # Iterate from oldest → newest, assigning rank from end
    total = len(tool_result_indices)
    for rank_from_end, idx in enumerate(reversed(tool_result_indices)):
        # rank_from_end: 0 = most recent, total-1 = oldest
        if rank_from_end < preserve_n:
            continue  # always keep the N most recent intact

        msg = history[idx]
        content = msg.get("content", {})
        tool_result = content.get("tool_result", "") if isinstance(content, dict) else str(content)
        tool_name = content.get("tool_name", "unknown") if isinstance(content, dict) else "unknown"
        is_err = _is_error_output(tool_result)

        if is_err and rank_from_end >= remove_errors_after:
            # Error outputs beyond max age: replace with tombstone
            msg["content"] = {
                "tool_name": tool_name,
                "tool_result": f"[error output pruned — stale error from {tool_name} removed]",
            }
            removed += 1

        elif not is_err and rank_from_end >= compress_after:
            # Successful outputs beyond compress age: truncate
            original_len = len(tool_result)
            if original_len > max_chars:
                truncated = tool_result[:max_chars]
                msg["content"] = {
                    "tool_name": tool_name,
                    "tool_result": (
                        f"[output compressed: {original_len} → {max_chars} chars]\n"
                        + truncated
                    ),
                }
                compressed += 1

    return removed, compressed


def _is_tool_result(content: Any) -> bool:
    """True if content is a tool result dict (from hist_add_tool_result)."""
    if not isinstance(content, dict):
        return False
    return "tool_result" in content and "tool_name" in content


def _is_error_output(tool_result: str) -> bool:
    """True if the tool result string signals a failure."""
    if not tool_result:
        return False
    return any(signal in tool_result for signal in _ERROR_SIGNALS)


# ── Config Loading ─────────────────────────────────────────────────────────────

def _load_config(agent) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    try:
        raw_cfg = getattr(agent, "config", None)
        if raw_cfg is None:
            return cfg
        raw = raw_cfg if isinstance(raw_cfg, dict) else vars(raw_cfg)
        overrides = raw.get(CONFIG_KEY, {})
        cfg.update(overrides)
    except Exception:
        pass
    return cfg
