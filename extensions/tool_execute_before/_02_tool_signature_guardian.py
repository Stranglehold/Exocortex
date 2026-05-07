"""
Tool Signature Guardian — First-Line Loop Detection via Signature Hashing
=========================================================================
Hook: tool_execute_before (_02_)
Tier 1: Mechanical Safety — zero model calls, fires every tool call

Hashes (tool_name + canonical_args) for every invocation. If the same
signature appears 3+ times in the last 15 invocations, blocks execution:
  - shell tools (code_execution_tool): replaces code with warning echo
  - text_editor and other tools: injects hist_add_warning, lets tool run

Catches identical-call repetition 2-3 turns earlier than message-level
supervisor detection. Designed as the first mechanical gate before the
model's reasoning loop can entrench a bad pattern.

Pattern source: OpenPlanter runtime policy (blocks identical shell commands
repeated >2x at same depth) + Agent's own AO-002 self-diagnosis.

No LLM calls. O(N) hash check, N ≤ 15.
"""

import hashlib
import json
from collections import deque
from typing import Any, Dict

from helpers.extension import Extension

_HISTORY_WINDOW = 15      # How many recent invocations to track
_BLOCK_THRESHOLD = 3      # How many identical sigs trigger a block
_SHELL_TOOLS = frozenset({"code_execution_tool"})
_SKIP_TOOLS = frozenset({"response", "memory_save", "memory_load"})

_WARNING_TEMPLATE = """[SIG-GUARDIAN] LOOP DETECTED: identical {tool_name} call seen {count}x in last {window} invocations.

This tool call has been made with the same arguments {count} times without
progressing. Continuing will not produce a different result.

Required actions:
  1. Stop calling {tool_name} with these arguments.
  2. Diagnose WHY the previous calls did not succeed.
  3. Try a different approach: different arguments, different tool, or ask for help.
  4. If the task is complete, call the response tool to report results.

Signature: {sig_short}"""


def _canonical_hash(tool_name: str, tool_args: dict | None) -> str:
    """Stable hash of (tool_name, sorted_args). Truncates long string values."""
    try:
        if tool_args:
            # Truncate long values to avoid hash instability from tiny differences
            truncated = {}
            for k, v in tool_args.items():
                s = str(v)
                truncated[k] = s[:200] if len(s) > 200 else s
            canonical = json.dumps(truncated, sort_keys=True)
        else:
            canonical = ""
        digest = hashlib.md5(f"{tool_name}:{canonical}".encode()).hexdigest()[:10]
        return digest
    except Exception:
        return f"{tool_name}:unhashable"


def _sig_short(tool_name: str, sig_hash: str) -> str:
    return f"{tool_name}:{sig_hash}"


class ToolSignatureGuardian(Extension):
    """Mechanically blocks identical tool calls repeated above threshold."""

    async def execute(
        self,
        tool_name: str = "",
        tool_args: Dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        try:
            if not tool_name or tool_name in _SKIP_TOOLS:
                return

            # Retrieve or initialise per-agent history deque
            history: deque = getattr(
                self.agent, "_sig_guardian_history", None
            )
            if history is None:
                history = deque(maxlen=_HISTORY_WINDOW)
                self.agent._sig_guardian_history = history

            sig = _canonical_hash(tool_name, tool_args or {})
            count = sum(1 for s in history if s == sig)

            # Record this call BEFORE deciding whether to block so the
            # deque always reflects reality including the current call
            history.append(sig)

            if count < _BLOCK_THRESHOLD:
                return  # Not yet a problem

            warning = _WARNING_TEMPLATE.format(
                tool_name=tool_name,
                count=count,
                window=_HISTORY_WINDOW,
                sig_short=_sig_short(tool_name, sig),
            )

            print(
                f"[SIG-GUARDIAN] Blocking {tool_name} (sig {sig}, "
                f"count={count}/{_BLOCK_THRESHOLD})",
                flush=True,
            )

            # Block strategy: shell tools get replaced; others get warned
            if tool_name in _SHELL_TOOLS and isinstance(tool_args, dict):
                lines = warning.strip().split("\n")
                tool_args["code"] = "\n".join(
                    f"echo {json.dumps(line)}" for line in lines
                )
                tool_args.pop("runtime", None)

            try:
                self.agent.hist_add_warning(warning)
            except Exception:
                pass

        except Exception as e:
            print(f"[SIG-GUARDIAN] Error (passthrough): {e}", flush=True)
