---
name: code-execution-tool-interactive-prompt
description: "Use before calling code_execution_tool in a context that previously failed with 'interactive_prompt'. Command entered interactive mode requiring keyboard input. This execution environment cannot provide stdin input to running commands."
triggers: ["code_execution_tool", "code_execution_tool interactive_prompt", "interactive prompt"]
success_criterion: "Agent applies the recovery ('Kill the current terminal session') instead of repeating the interactive prompt failure"
confidence: probable
---

# Failure lesson: code_execution_tool — interactive_prompt

Captured automatically from a classified tool failure (Cycle-to-Skill Pipeline, Path A). Check this before repeating the operation.

## What happens
Command entered interactive mode requiring keyboard input. This execution environment cannot provide stdin input to running commands.

Evidence (matched pattern): `Potential dialog detected`

## Avoid
- Do NOT retry the same command — it will hang again for the same reason
- Do NOT try to 'type' into the prompt — stdin is not connected
- Do NOT wait for more output — the command is blocked on input

## Do instead
- Kill the current terminal session
- Use environment variables instead of interactive configuration
- Write configuration directly to the config file
- Use CLI flags to pass values non-interactively
