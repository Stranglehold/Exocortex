#!/bin/bash
# install_exocortex_profile.sh
# Deploys Exocortex extensions to the persistent agent profile path.
#
# Target: /a0/usr/agents/agent0/extensions/python/{hook}/
#         /a0/usr/agents/agent0/prompts/
#
# v1.6: Agent Zero uses extensions/python/ subdirectory under profile path.
# get_paths() now looks under extensions/python/<hook>/ rather than extensions/<hook>/.
#
# This path is persistent — survives A0 container image updates.
# Profile path has higher priority than any ephemeral /a0/ path.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CONTAINER:-flamboyant_bell}"
PROFILE_BASE="/a0/usr/agents/agent0"

# On Windows Git Bash, docker exec arguments with Unix paths get translated by MSYS.
# Prefix docker exec commands with MSYS_NO_PATHCONV=1 to suppress this.
# docker cp is exempt — its "container:/path" format is not affected.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "  Deploying Exocortex extensions to profile path ($CONTAINER)"
echo "  Source: $SCRIPT_DIR"
echo "  Target: $PROFILE_BASE"

# ── Create directory structure ────────────────────────────────────────────────

_exec "$CONTAINER" mkdir -p \
  "$PROFILE_BASE/extensions/python/before_main_llm_call" \
  "$PROFILE_BASE/extensions/python/error_format" \
  "$PROFILE_BASE/extensions/python/hist_add_before" \
  "$PROFILE_BASE/extensions/python/message_loop_end" \
  "$PROFILE_BASE/extensions/python/message_loop_prompts_after" \
  "$PROFILE_BASE/extensions/python/monologue_end" \
  "$PROFILE_BASE/extensions/python/reasoning_stream" \
  "$PROFILE_BASE/extensions/python/reasoning_stream_end" \
  "$PROFILE_BASE/extensions/python/response_stream_chunk" \
  "$PROFILE_BASE/extensions/python/tool_execute_after" \
  "$PROFILE_BASE/extensions/python/tool_execute_before" \
  "$PROFILE_BASE/prompts"

# ── Deploy extensions ─────────────────────────────────────────────────────────
# Note: _12_org_dispatcher, _13_operator_profile, _14_metacognitive_injection
# are intentionally excluded — replaced by prompt files below.

EXT_SRC="$SCRIPT_DIR/extensions"
EXT_DEST="$CONTAINER:$PROFILE_BASE/extensions/python"

# before_main_llm_call
docker cp "$EXT_SRC/before_main_llm_call/_11_belief_state_tracker.py" "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/slot_taxonomy.json"          "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/_15_htn_plan_selector.py"    "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/_16_tool_registry.py"        "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/_18_memory_catalog.py"       "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/_20_context_watchdog.py"     "$EXT_DEST/before_main_llm_call/"
# Proactive Reasoning Supervisor — injection hook (v1.6 source path)
docker cp "$EXT_SRC/python/before_main_llm_call/_12_proactive_supervisor.py" "$EXT_DEST/before_main_llm_call/"

# error_format
docker cp "$EXT_SRC/error_format/_20_structured_retry.py"  "$EXT_DEST/error_format/"
docker cp "$EXT_SRC/error_format/_30_failure_tracker.py"   "$EXT_DEST/error_format/"

# hist_add_before
docker cp "$EXT_SRC/hist_add_before/_11_working_memory.py" "$EXT_DEST/hist_add_before/"

# message_loop_end
docker cp "$EXT_SRC/message_loop_end/_50_supervisor_loop.py" "$EXT_DEST/message_loop_end/"

# message_loop_prompts_after
docker cp "$EXT_SRC/message_loop_prompts_after/_55_memory_relevance_filter.py" "$EXT_DEST/message_loop_prompts_after/"
docker cp "$EXT_SRC/message_loop_prompts_after/_56_memory_enhancement.py"       "$EXT_DEST/message_loop_prompts_after/"
docker cp "$EXT_SRC/message_loop_prompts_after/_58_ontology_query.py"           "$EXT_DEST/message_loop_prompts_after/"
docker cp "$EXT_SRC/message_loop_prompts_after/_95_tiered_tool_injection.py"    "$EXT_DEST/message_loop_prompts_after/"

# monologue_end
docker cp "$EXT_SRC/monologue_end/_25_epistemic_integrity.py"  "$EXT_DEST/monologue_end/"
docker cp "$EXT_SRC/monologue_end/_52_selective_memorizer.py"  "$EXT_DEST/monologue_end/"
docker cp "$EXT_SRC/monologue_end/_53_insight_capture.py"      "$EXT_DEST/monologue_end/"
docker cp "$EXT_SRC/monologue_end/_55_memory_classifier.py"    "$EXT_DEST/monologue_end/"
docker cp "$EXT_SRC/monologue_end/_57_memory_maintenance.py"   "$EXT_DEST/monologue_end/"
docker cp "$EXT_SRC/monologue_end/_59_ontology_maintenance.py" "$EXT_DEST/monologue_end/"

# reasoning_stream — Proactive Reasoning Supervisor buffer hook
docker cp "$EXT_SRC/python/reasoning_stream/_12_proactive_supervisor.py" "$EXT_DEST/reasoning_stream/"

# reasoning_stream_end — Proactive Reasoning Supervisor analysis hook
docker cp "$EXT_SRC/python/reasoning_stream_end/_12_proactive_supervisor.py" "$EXT_DEST/reasoning_stream_end/"

# response_stream_chunk
docker cp "$EXT_SRC/response_stream_chunk/_21_plain_text_response.py" "$EXT_DEST/response_stream_chunk/"

# tool_execute_after
docker cp "$EXT_SRC/tool_execute_after/_20_error_comprehension.py"    "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_20_reset_failure_counter.py"  "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_22_response_finalizer.py"     "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_25_evidence_ledger_recorder.py" "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_30_tool_fallback_logger.py"   "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_60_sleep_trigger.py"          "$EXT_DEST/tool_execute_after/"

# tool_execute_before
docker cp "$EXT_SRC/tool_execute_before/_15_action_boundary.py"     "$EXT_DEST/tool_execute_before/"
docker cp "$EXT_SRC/tool_execute_before/_20_meta_reasoning_gate.py" "$EXT_DEST/tool_execute_before/"
docker cp "$EXT_SRC/tool_execute_before/_30_tool_fallback_advisor.py" "$EXT_DEST/tool_execute_before/"

# ── Deploy prompt files ───────────────────────────────────────────────────────
# These replace per-turn dynamic injection of static content.

PROMPT_SRC="$SCRIPT_DIR/prompts"
PROMPT_DEST="$CONTAINER:$PROFILE_BASE/prompts"

docker cp "$PROMPT_SRC/agent.system.operator_calibration.md" "$PROMPT_DEST/"
docker cp "$PROMPT_SRC/agent.system.model_awareness.md"      "$PROMPT_DEST/"
docker cp "$PROMPT_SRC/agent.system.capabilities.md"         "$PROMPT_DEST/"

echo "  Profile deployment complete."
echo "  Extensions: $(_exec $CONTAINER find $PROFILE_BASE/extensions -name '*.py' | wc -l) files"
echo "  Prompts:    $(_exec $CONTAINER ls $PROFILE_BASE/prompts | wc -l) files"
