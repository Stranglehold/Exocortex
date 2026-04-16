Your response could not be parsed as valid JSON. Two causes and fixes:

── TRUNCATED PAYLOAD (most common) ──
Your JSON was cut off mid-payload. This happens when you try to embed large code inside a single code_execution_tool call — the output token limit truncates the JSON before it closes.

FIX: Use code_execution_tool with runtime=python to write files in small sections:

Section 1 (creates the file):
{"tool_name": "code_execution_tool", "tool_args": {"runtime": "python", "code": "with open('/path/to/file.py', 'w') as f:\n    f.write('first section — max ~800 chars')"}}

Section 2+ (appends to the file):
{"tool_name": "code_execution_tool", "tool_args": {"runtime": "python", "code": "with open('/path/to/file.py', 'a') as f:\n    f.write('next section')"}}

Rules:
- Always use code_execution_tool with runtime=python — do NOT use text_editor, text_editor_remote, or any other tool
- Keep each "code" string under 800 characters
- Use 'w' mode for the first section, 'a' mode for every section after
- Continue appending until all content is written

── FORMAT ERROR (no large payload involved) ──
Your response must be ONLY a JSON object — no text, markdown, or prose before or after it.

Required format:
{"thoughts": "your reasoning", "tool_name": "tool_name_here", "tool_args": {"arg": "value"}}
