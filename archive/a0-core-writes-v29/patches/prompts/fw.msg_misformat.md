Your response could not be parsed as valid JSON. Identify which case applies and follow the fix:

── RESPONSE TEXT TOO LONG ──
You tried to send a long response and the text field was cut off before the closing braces.

DO NOT retry the same long response — it will be cut off again.

FIX:
Step 1 — Write the content to a file using code_execution_tool. Write in sections of ≤800 characters each, using 'w' mode for the first section and 'a' mode for every section after.
Step 2 — Call response with 2-3 sentences summarizing what you wrote and where the file is.

── CODE PAYLOAD TOO LARGE ──
Your JSON was cut off mid-payload. This happens when you embed large code inside a single code_execution_tool call and the output token limit truncates the JSON before it closes.

FIX: Write files in small sections using code_execution_tool with runtime=python. Keep each "code" string under 800 characters. Use 'w' mode for the first section, 'a' mode for every section after.

Do NOT use text_editor, text_editor_remote, or any other tool — only code_execution_tool with runtime=python.

── FORMAT ERROR (no large payload involved) ──
Your response must be ONLY a JSON object — no text, markdown, or prose before or after it.

Required format:
{"thoughts": "your reasoning", "tool_name": "tool_name_here", "tool_args": {"arg": "value"}}
