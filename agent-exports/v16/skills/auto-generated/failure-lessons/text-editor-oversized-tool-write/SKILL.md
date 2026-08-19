---
name: text-editor-oversized-tool-write
description: "Use before calling text_editor in a context that previously failed (oversized_tool_write). A text_editor:write was blocked because the content exceeds the ~5000-char JSON payload limit and would truncate, breaking the tool call."
triggers: ["oversized write", "text_editor", "text_editor write", "write large file", "write long content", "write wiki page"]
success_criterion: "Agent uses code_execution with Python open() for writes >5000 chars instead of text_editor"
confidence: probable
---

# Failure lesson: text_editor — oversized_tool_write

Captured automatically from a recurring error (Cycle-to-Skill Pipeline, Path A, handle_exception). Check this before repeating the operation.

## What happens
A text_editor:write was blocked because the content exceeds the ~5000-char JSON payload limit and would truncate, breaking the tool call.

Observed error: `[MetaGate-SIZE] text_editor:write blocked — content is 7,103 chars, exceeds the ~5000 char JSON payload limit and will truncate. Use code_execution_tool with Python open() instead:`

## Avoid
- Do NOT retry text_editor:write with the same oversized content — it will be blocked again

## Do instead
- Use code_execution_tool with Python open()/write for large content
- Or write in append-mode chunks, each under ~5000 chars
