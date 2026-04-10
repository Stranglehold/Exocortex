"""
Write Validator — Post-execution syntax + truncation check for text_editor writes
==================================================================================
Hook: tool_execute_after (_26_)

After text_editor write or patch operations: validates the written file.

Validation rules:
  .py files  — py_compile syntax check + truncation ratio check
  other files — truncation ratio check only

Truncation threshold:
  New file has fewer than TRUNCATION_RATIO (50%) of original lines AND
  original was at least TRUNCATION_MIN_LINES (50) lines.

On failure:
  - Restores pre-write content (or deletes new file if it had no prior content)
  - Injects hist_add_warning so the model sees the rejection on the next turn

On success:
  - Logs ACCEPTED with line count and (for .py) syntax-OK note

Paired with _25_write_guard (tool_execute_before).
State key: _write_guard = {path, content, lines, op}

No LLM calls. Runs between evidence ledger (_25_) and code quality gate (_27_).
"""

import os
import py_compile
from pathlib import Path
from typing import Optional

from python.helpers.extension import Extension
from python.helpers.tool import Response

GUARD_KEY = "_write_guard"

# New file has fewer than this fraction of original lines → suspect truncation
TRUNCATION_RATIO = 0.5
# Only apply truncation check when original was at least this many lines
TRUNCATION_MIN_LINES = 50


class WriteValidator(Extension):
    """Validates text_editor writes; restores previous version on failure."""

    async def execute(
        self,
        response: Response | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            if tool_name != "text_editor":
                return

            guard = self.agent.get_data(GUARD_KEY)
            if not guard:
                return

            # Clear guard early — prevents stale state on any exit path
            self.agent.set_data(GUARD_KEY, None)

            path: str = guard["path"]
            original_content: Optional[str] = guard["content"]
            original_lines: int = guard["lines"]

            # Read what was actually written
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    new_content = f.read()
                new_lines = new_content.count("\n") + 1
            except FileNotFoundError:
                # Write didn't create the file — tool probably errored; nothing to do
                print(f"[WRITE-VAL] {path} not present after write — skipping", flush=True)
                return
            except Exception as e:
                print(f"[WRITE-VAL] Could not read {path} post-write: {e}", flush=True)
                return

            rejection_reason: Optional[str] = None

            # ── Syntax check (.py only) ───────────────────────────────────────
            if path.endswith(".py"):
                rejection_reason = _check_syntax(path)

            # ── Truncation check (all files with substantial originals) ───────
            if rejection_reason is None and original_lines >= TRUNCATION_MIN_LINES:
                ratio = new_lines / original_lines
                if ratio < TRUNCATION_RATIO:
                    rejection_reason = (
                        f"Truncation detected: {new_lines} lines written, "
                        f"previous version had {original_lines} lines "
                        f"({ratio:.0%} of original, threshold {TRUNCATION_RATIO:.0%})"
                    )

            if rejection_reason:
                self._reject(path, rejection_reason, original_content, original_lines, new_lines)
            else:
                suffix = ", syntax OK" if path.endswith(".py") else ""
                print(f"[WRITE-VAL] ACCEPTED {path}: {new_lines} lines{suffix}", flush=True)

        except Exception as e:
            print(f"[WRITE-VAL] Error (passthrough): {e}", flush=True)

    def _reject(
        self,
        path: str,
        reason: str,
        original_content: Optional[str],
        original_lines: int,
        new_lines: int,
    ) -> None:
        """Restore pre-write content and inject rejection warning into agent history."""

        # ── Restore ───────────────────────────────────────────────────────────
        if original_content is not None:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(original_content)
                restore_note = f"Restored previous {original_lines}-line version."
            except Exception as e:
                restore_note = f"Restore FAILED ({e}) — previous content may be lost."
        else:
            # New file with invalid content — delete it
            try:
                os.remove(path)
                restore_note = "File removed (was a new file with invalid content)."
            except Exception as e:
                restore_note = f"Could not remove invalid new file: {e}."

        # ── Warning injection ─────────────────────────────────────────────────
        fname = Path(path).name
        warning = (
            f"[WRITE-VAL] Write to {fname} REJECTED — {reason}. "
            f"{restore_note} "
            f"Rewrite the complete, correct content and retry."
        )

        try:
            self.agent.hist_add_warning(warning)
        except Exception:
            pass

        print(
            f"[WRITE-VAL] REJECTED {path}: {reason} | {restore_note}",
            flush=True,
        )


def _check_syntax(path: str) -> Optional[str]:
    """Run py_compile on path. Returns error description or None on success."""
    try:
        py_compile.compile(path, doraise=True)
        return None
    except py_compile.PyCompileError as e:
        # PyCompileError message includes cache path noise — keep just the core message
        msg = str(e)
        # Format: "Sorry: <ExcType>: <msg> (<file>, line N)"
        # Strip everything after the last closing paren to avoid cache path leakage
        return f"SyntaxError: {msg}"
    except Exception as e:
        return f"Compile check failed: {e}"
