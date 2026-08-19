---
name: code-execution-tool-terminal-session-hung
description: "Use before calling code_execution_tool in a context that previously failed with 'terminal_session_hung'. A previous command is still running or hung in this terminal session. New commands cannot execute until the session is reset."
triggers: ["code_execution_tool", "code_execution_tool terminal_session_hung", "terminal session hung"]
success_criterion: "Agent resets the terminal session (or opens a new session ID) instead of re-checking or replanning the same command"
confidence: probable
---

# Failure lesson: code_execution_tool — terminal_session_hung

Captured automatically from a classified tool failure (Cycle-to-Skill Pipeline, Path A). Check this before repeating the operation.

## What happens
A previous command is still running or hung in this terminal session. New commands cannot execute until the session is reset.

Evidence (matched pattern): `Terminal session \d+ might be still running`

## Avoid
- Do NOT keep checking the session — it will not resolve itself
- Do NOT replan the same command — execute the reset first

## Do instead
- Reset the terminal session (kill the hung process)
- Open a new terminal session with a different session ID
