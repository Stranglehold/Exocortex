"""
write_file.py — Safe file writing tool for Agent Zero
======================================================

Writes text content directly to a file without requiring the content to be
embedded inside executable Python code. Solves the nested-quoting problem:

    code_execution_tool path:  JSON → Python code → open() string → content
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         three levels of quote escaping

    write_file path:           JSON → content
                                       ^^^^^^^
                                       one level — just JSON string encoding

Use write_file instead of code_execution_tool whenever the content you are
writing contains string literals, dict keys, f-strings, or other quoted values.
Single quotes in content require no JSON escaping. Double quotes require only
standard JSON escaping (\"). No Python escaping layer exists.

Examples
--------
Write a new file:
  tool_name: write_file
  tool_args: {path: "/tmp/script.py", content: "import os\n\ndef main():\n    pass\n"}

Append a method (note: single quotes in content need no escaping):
  tool_name: write_file
  tool_args: {
    path: "/tmp/script.py",
    mode: "a",
    content: "\n    def _build_headers(self):\n        return {'Authorization': 'Bearer ' + self.token}\n"
  }

Verify after writing by reading back:
  tool_name: code_execution_tool
  tool_args: {runtime: python, code: "print(open('/tmp/script.py').read())"}
"""

import os

from helpers.tool import Tool, Response


class WriteFile(Tool):
    """Write text content to a file.

    Use instead of code_execution_tool when writing file content that contains
    string literals, dict keys, f-strings, or other quoted values. Content is
    passed as a direct JSON string field — no Python escaping layer required.

    Args:
        path    (str): Absolute or relative path to the target file.
        content (str): Text to write. Newlines as \\n. Quotes as-is.
        mode    (str): 'w' to create/overwrite (default), 'a' to append.
    """

    async def execute(self,
                      path: str = "",
                      content: str = "",
                      mode: str = "w",
                      **kwargs) -> Response:
        try:
            if not path:
                return Response(
                    message="[WRITE-FILE] Error: 'path' argument is required.",
                    break_loop=False,
                )
            if content is None:
                content = ""

            # Normalise mode — only 'w' and 'a' are meaningful here
            if mode not in ("w", "a"):
                mode = "w"

            # Create parent directories if they don't exist
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(path, mode, encoding="utf-8") as f:
                f.write(content)

            lines_written = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            total_lines = sum(1 for _ in open(path, encoding="utf-8"))

            action = "wrote" if mode == "w" else "appended"
            print(
                f"[WRITE-FILE] {action} {lines_written} lines to {path} "
                f"(file now {total_lines} lines total)",
                flush=True,
            )

            return Response(
                message=(
                    f"[WRITE-FILE] {action.capitalize()} {lines_written} lines to {path}. "
                    f"File is now {total_lines} lines total. "
                    f"Verify with: code_execution_tool runtime=python "
                    f"code=\"print(open('{path}').read())\""
                ),
                break_loop=False,
            )

        except Exception as e:
            print(f"[WRITE-FILE] Error: {e}", flush=True)
            return Response(
                message=f"[WRITE-FILE] Error writing {path}: {e}",
                break_loop=False,
            )
