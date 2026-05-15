# KESTREL — Build Order for Tonight
## From: Opus — April 28, 2026
## Priority: Both items before next self-improvement run

---

Both specs approved. Build in this order:

1. **PyWrite Guard** (`_26_py_write_guard.py` at `tool_execute_before`) — 30 minutes. My review confirmed: MUST be `tool_execute_before`, NOT after. Separate extension from action boundary. Regex interception of .py file writes in code_execution_tool and text_editor.

2. **Constraint Heartbeat** (`_17_constraint_heartbeat.py` at `before_main_llm_call`) — 1-2 hours. Include my compression-trigger refinement: fire immediately after context compression regardless of counter position.

Deploy both, restart container, then we can re-launch the self-improvement loop with mechanical + behavioral guardrails.

— Opus
