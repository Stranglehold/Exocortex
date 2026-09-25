import re

from helpers.extension import Extension

# MetaGate refusals are policy blocks, not format failures (Opus, 2026-09-25). Since MetaGate
# raises a RepairableException, its refusals reach this hook through A0's _50, and a JSON-format
# reminder stapled onto "you sent a tool call without required arguments" misdiagnoses call
# content as format. That is the same wrong-diagnosis class as the retired truncation text.
# A0's format_error places the exception line at the top or the bottom depending on the class
# name, so this matches that LINE ("<Type>: [MetaGate…"), not the start of the message. Indented
# traceback source lines such as `    raise MetaGateBlockError(f"[MetaGate] {msg}")` do not match.
_METAGATE_REFUSAL = re.compile(r"^[\w\.]+: \[MetaGate", re.M)

# Keywords that indicate a JSON format/parse failure from DirtyJson or tool extraction
FORMAT_ERROR_SIGNALS = [
    "json", "parse", "format", "tool", "missing", "invalid",
    "expected", "syntax", "decode", "key", "argument"
]

# Inline schema injected when a format error is detected
# Mirrors the actual structure process_tools expects
SCHEMA_REMINDER = """
Output ONLY a valid JSON object. No text before or after it.

Required structure:
~~~json
{
  "thoughts": "your reasoning here",
  "tool_name": "name_of_tool",
  "tool_args": {
    "arg_name": "arg_value"
  }
}
~~~

Rules:
- No trailing commas
- No markdown outside the JSON block
- tool_name must exactly match one of the available tools
- tool_args must contain all required arguments for the chosen tool
"""


class StructuredRetry(Extension):
    async def execute(self, **kwargs):
        msg = kwargs.get("msg")
        if not msg or "message" not in msg:
            return

        # A MetaGate refusal describes itself; see _METAGATE_REFUSAL.
        if _METAGATE_REFUSAL.search(msg["message"]):
            return

        error_text = msg["message"].lower()

        # Only augment messages that look like format/parse failures
        # Other RepairableExceptions (network errors, tool failures) should
        # pass through unmodified so their original error context is preserved
        if not any(signal in error_text for signal in FORMAT_ERROR_SIGNALS):
            return

        # Augment in-place — MaskErrorSecrets (_10) has already run,
        # hist_add_warning reads this value after all error_format extensions complete
        msg["message"] = msg["message"].rstrip() + SCHEMA_REMINDER
