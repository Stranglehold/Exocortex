"""
MOVED: Orchestration gate logic lives in message_loop_prompts_after/_57_orchestration_mode.py

before_main_llm_call fires AFTER prepare_prompt() has assembled the LLM prompt.
User-message prepend modifications here are silently overwritten on the next
prepare_prompt() call — this hook cannot reliably modify message content.

message_loop_prompts_after fires inside prepare_prompt() at the correct point.
_57_orchestration_mode.py handles delegation scaffolding there.

This file is intentionally empty. Do not add logic here.
"""
