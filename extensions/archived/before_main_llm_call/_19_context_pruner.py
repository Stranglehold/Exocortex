"""
MOVED: Context pruner lives in message_loop_prompts_after/_09_context_pruner.py

before_main_llm_call fires AFTER prepare_prompt() has already assembled the
LLM prompt from loop_data.history_output. Any modifications to history_output
here are silently discarded — overwritten on the next prepare_prompt() call.

message_loop_prompts_after fires inside prepare_prompt(), after history_output
is populated but before the final prompt is built. That is the correct hook
for history_output modifications.

This file is intentionally empty. Do not add logic here.
"""
