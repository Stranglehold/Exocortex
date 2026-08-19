---
name: text-editor-interactive-prompt
description: "Use before calling text_editor in a context that previously failed with 'interactive_prompt'. Command entered interactive mode requiring keyboard input. This execution environment cannot provide stdin input to running commands."
triggers: ["interactive prompt", "text_editor", "text_editor interactive_prompt"]
success_criterion: "Agent passes values non-interactively (env vars, CLI flags, or config file) instead of retrying the interactive command or waiting on stdin"
confidence: probable
---

# Failure lesson: text_editor — interactive_prompt

Captured automatically from a classified tool failure (Cycle-to-Skill Pipeline, Path A). Check this before repeating the operation.

## What happens
Command entered interactive mode requiring keyboard input. This execution environment cannot provide stdin input to running commands.

Evidence (matched pattern): `(?i)\?\s*$`

## Avoid
- Do NOT retry the same command — it will hang again for the same reason
- Do NOT try to 'type' into the prompt — stdin is not connected
- Do NOT wait for more output — the command is blocked on input

## Do instead
- Kill the current terminal session
- Use environment variables instead of interactive configuration
- Write configuration directly to the config file
- Use CLI flags to pass values non-interactively
