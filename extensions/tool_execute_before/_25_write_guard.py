"""
Write Guard — Pre-execution backup for text_editor writes
==========================================================
Hook: tool_execute_before (_25_)

Before text_editor write or patch operations: saves the current file content
and metadata to agent data so the write validator (_26_) can restore on
validation failure.

Paired with _26_write_validator (tool_execute_after).
State key: _write_guard = {path, content, lines, op}

No LLM calls. No blocking. Runs after MetaGate (_20_), before tool execution.
"""

from python.helpers.extension import Extension
from typing import Any, Dict, Optional

GUARD_KEY = "_write_guard"


class WriteGuard(Extension):
    """Saves pre-write file state so the validator can roll back on failure."""

    async def execute(
        self,
        tool_args: Dict[str, Any] | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            # Always clear stale guard — ensures validator doesn't act on old data
            self.agent.set_data(GUARD_KEY, None)

            if tool_name != "text_editor":
                return
            if not tool_args:
                return

            # Detect write operations:
            #   write  → tool_args has "content"
            #   patch  → tool_args has "edits"
            #   read   → neither → no backup needed
            is_write = "content" in tool_args
            is_patch = "edits" in tool_args
            if not (is_write or is_patch):
                return

            path: str = tool_args.get("path", "").strip()
            if not path:
                return

            # Read current file content before the write
            original: Optional[str] = None
            original_lines: int = 0
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    original = f.read()
                original_lines = original.count("\n") + 1
            except FileNotFoundError:
                pass  # New file — nothing to back up
            except Exception as e:
                print(f"[WRITE-GUARD] Could not read {path} for backup: {e}", flush=True)

            self.agent.set_data(GUARD_KEY, {
                "path": path,
                "content": original,
                "lines": original_lines,
                "op": "write" if is_write else "patch",
            })

            label = "new file" if original is None else f"{original_lines} lines"
            print(f"[WRITE-GUARD] Backed up: {path} ({label})", flush=True)

        except Exception as e:
            print(f"[WRITE-GUARD] Error (passthrough): {e}", flush=True)
