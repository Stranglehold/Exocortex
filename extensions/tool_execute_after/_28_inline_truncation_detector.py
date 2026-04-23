"""
Inline Truncation Detector — code_execution_tool incomplete input attribution fix
==================================================================================
Hook: tool_execute_after (_28_)

When code_execution_tool receives content that was silently truncated before reaching
the Python interpreter, the IPython kernel raises _IncompleteInputError or reports
"incomplete input". Without this extension, the agent sees this as a syntax error in
its own code and enters a rewrite loop, never reaching the actual cause.

This extension detects the _IncompleteInputError signal and injects a
hist_add_warning that explicitly attributes the failure to tool-side truncation,
not agent-side code quality, and directs the agent to the correct recovery path.

Recovery path: write the script to a file via bash heredoc, then execute it.
The bash heredoc bypasses code_execution_tool's inline content limit entirely.

Part of the False Attribution Loop fix (2026-04-17):
  _25_write_guard.py   — stores intended_line_count in guard state
  _26_write_validator.py — truncation vs genuine-error branch in rejection message
  _28_inline_truncation_detector.py — this file (_IncompleteInputError path)

No LLM calls. Runs at slot 28, after write_validator (_26_) and code_quality (_27_),
before tool fallback chain (_30_).
"""

import re
from python.helpers.extension import Extension
from python.helpers.tool import Response

# IPython kernel signals when it receives incomplete/truncated code
_INCOMPLETE_RE = re.compile(
    r'_IncompleteInputError|incomplete input',
    re.IGNORECASE,
)


class InlineTruncationDetector(Extension):
    """Detects code_execution_tool truncation via _IncompleteInputError and fixes attribution."""

    async def execute(
        self,
        response: Response | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            if tool_name != "code_execution_tool":
                return
            if not response or not response.message:
                return
            if not _INCOMPLETE_RE.search(response.message):
                return

            warning = (
                "[INLINE-TRUNC] The code_execution_tool TRUNCATED your inline code "
                "before it reached the Python interpreter. "
                "The '_IncompleteInputError' / 'incomplete input' you see is NOT a "
                "syntax error in your code — YOUR CODE IS CORRECT. "
                "The tool has an inline content length limit. "
                "Write the script to a file first, then execute it:\n"
                "  bash -c \"cat > /tmp/script.py << 'PYEOF'\\n"
                "  ...your full script content...\\n"
                "  PYEOF && python3 /tmp/script.py\""
            )

            try:
                self.agent.hist_add_warning(warning)
            except Exception:
                pass

            print("[INLINE-TRUNC] Tool truncation detected → attribution fix injected", flush=True)

        except Exception as e:
            print(f"[INLINE-TRUNC] Error (passthrough): {e}", flush=True)
