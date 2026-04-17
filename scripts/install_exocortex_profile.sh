#!/bin/bash
# install_exocortex_profile.sh
# Deploys Exocortex as a plugin to the persistent user plugin path.
#
# Target: /a0/usr/plugins/exocortex/
#   extensions/python/{hook}/  — all Exocortex extensions
#   extensions/webui/{slot}/   — webui injection components (theme picker)
#   tools/                     — custom Agent Zero tools
#   prompts/                   — system prompt files
#   webui/                     — Alpine.js stores and theme assets
#   plugin.yaml                — plugin manifest
#   default_config.yaml        — configuration reference
#
# v1.6: Agent Zero discovers plugins at /a0/usr/plugins/ (user-priority).
# get_paths() searches usr/plugins/*/extensions/python/<hook>/ and
# usr/plugins/*/tools/ automatically for enabled plugins.
#
# This path is persistent — survives A0 container image updates.
# Plugin path has higher priority than any ephemeral /a0/ path.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CONTAINER:-exocortex_v16}"
PLUGIN_BASE="/a0/usr/plugins/exocortex"

# On Windows Git Bash, docker exec arguments with Unix paths get translated by MSYS.
# Prefix docker exec commands with MSYS_NO_PATHCONV=1 to suppress this.
# docker cp is exempt — its "container:/path" format is not affected.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "  Deploying Exocortex plugin ($CONTAINER)"
echo "  Source: $SCRIPT_DIR"
echo "  Target: $PLUGIN_BASE"

# ── Create directory structure ────────────────────────────────────────────────

_exec "$CONTAINER" mkdir -p \
  "$PLUGIN_BASE/extensions/python/before_main_llm_call" \
  "$PLUGIN_BASE/extensions/python/error_format" \
  "$PLUGIN_BASE/extensions/python/hist_add_before" \
  "$PLUGIN_BASE/extensions/python/message_loop_end" \
  "$PLUGIN_BASE/extensions/python/message_loop_prompts_after" \
  "$PLUGIN_BASE/extensions/python/monologue_end" \
  "$PLUGIN_BASE/extensions/python/reasoning_stream" \
  "$PLUGIN_BASE/extensions/python/reasoning_stream_end" \
  "$PLUGIN_BASE/extensions/python/response_stream_chunk" \
  "$PLUGIN_BASE/extensions/python/response_stream_end" \
  "$PLUGIN_BASE/extensions/python/tool_execute_after" \
  "$PLUGIN_BASE/extensions/python/tool_execute_before" \
  "$PLUGIN_BASE/extensions/webui/sidebar-bottom-wrapper-start" \
  "$PLUGIN_BASE/extensions/webui/get_message_handler" \
  "$PLUGIN_BASE/api" \
  "$PLUGIN_BASE/tools" \
  "$PLUGIN_BASE/prompts" \
  "$PLUGIN_BASE/webui/themes" \
  "$PLUGIN_BASE/webui/backgrounds"

# ── Deploy plugin manifest ────────────────────────────────────────────────────

docker cp "$SCRIPT_DIR/plugin/plugin.yaml"          "$CONTAINER:$PLUGIN_BASE/plugin.yaml"
docker cp "$SCRIPT_DIR/plugin/default_config.yaml"  "$CONTAINER:$PLUGIN_BASE/default_config.yaml"
docker cp "$SCRIPT_DIR/plugin/tool_domains.json"    "$CONTAINER:$PLUGIN_BASE/tool_domains.json"

# ── Model config: intentionally not deployed ──────────────────────────────────
# Model selection is configured through the Agent Zero UI (Settings → Models).
# A0 persists those choices in its own settings layer. Deploying a _model_config
# plugin config.json here would override whatever the user set in the UI, which
# is the wrong behaviour. Leave model config alone.

# ── Deploy webui assets (theme system) ───────────────────────────────────────

WEBUI_SRC="$SCRIPT_DIR/plugin/webui"
WEBUI_DEST="$CONTAINER:$PLUGIN_BASE/webui"

# Alpine.js store + theme editor + artifact runtime
docker cp "$WEBUI_SRC/theme-store.js"    "$WEBUI_DEST/"
docker cp "$WEBUI_SRC/theme-editor.js"   "$WEBUI_DEST/"
docker cp "$WEBUI_SRC/exo-artifact.js"   "$WEBUI_DEST/"

# Theme JSON files
for f in "$WEBUI_SRC/themes/"*.json; do
  docker cp "$f" "$WEBUI_DEST/themes/"
done

# WebUI extension — theme picker sidebar component
WEBUI_EXT_SRC="$SCRIPT_DIR/plugin/extensions/webui"
WEBUI_EXT_DEST="$CONTAINER:$PLUGIN_BASE/extensions/webui"

docker cp "$WEBUI_EXT_SRC/sidebar-bottom-wrapper-start/theme-picker.html" \
  "$WEBUI_EXT_DEST/sidebar-bottom-wrapper-start/"

# Artifact framework — message handler (DOMPurify hook + ExoArtifact import at module load time)
# NOTE: page-head HTML extension removed — importComponent causes layout disruption.
# DOMPurify hook and exo-artifact.js import live in artifact-handler.js top-level scope instead.
docker cp "$WEBUI_EXT_SRC/get_message_handler/artifact-handler.js" \
  "$WEBUI_EXT_DEST/get_message_handler/"

# ── Deploy extensions ─────────────────────────────────────────────────────────
# Note: _12_org_dispatcher, _13_operator_profile, _14_metacognitive_injection
# are intentionally excluded — replaced by prompt files below.

EXT_SRC="$SCRIPT_DIR/extensions"
EXT_DEST="$CONTAINER:$PLUGIN_BASE/extensions/python"

# before_main_llm_call
docker cp "$EXT_SRC/before_main_llm_call/_11_belief_state_tracker.py" "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/slot_taxonomy.json"          "$EXT_DEST/before_main_llm_call/"
docker cp "$EXT_SRC/before_main_llm_call/_15_htn_plan_selector.py"    "$EXT_DEST/before_main_llm_call/"
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
docker cp "$EXT_SRC/message_loop_prompts_after/_16_tool_registry.py"           "$EXT_DEST/message_loop_prompts_after/"
docker cp "$EXT_SRC/message_loop_prompts_after/_18_memory_catalog.py"           "$EXT_DEST/message_loop_prompts_after/"
docker cp "$EXT_SRC/message_loop_prompts_after/_19_skill_suggester.py"           "$EXT_DEST/message_loop_prompts_after/"
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

# reasoning_stream_end — Proactive Reasoning Supervisor analysis hook + thinking token logger
docker cp "$EXT_SRC/python/reasoning_stream_end/_12_proactive_supervisor.py" "$EXT_DEST/reasoning_stream_end/"
docker cp "$EXT_SRC/reasoning_stream_end/_14_thinking_token_logger.py"        "$EXT_DEST/reasoning_stream_end/"

# response_stream_chunk
docker cp "$EXT_SRC/response_stream_chunk/_21_plain_text_response.py" "$EXT_DEST/response_stream_chunk/"

# response_stream_end
docker cp "$EXT_SRC/response_stream_end/_20_clear_generating_content.py" "$EXT_DEST/response_stream_end/"

# tool_execute_after
docker cp "$EXT_SRC/tool_execute_after/_20_error_comprehension.py"      "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_20_reset_failure_counter.py"    "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_22_response_finalizer.py"       "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_25_evidence_ledger_recorder.py" "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_28_output_compressor.py"        "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_30_tool_fallback_logger.py"     "$EXT_DEST/tool_execute_after/"
docker cp "$EXT_SRC/tool_execute_after/_60_sleep_trigger.py"            "$EXT_DEST/tool_execute_after/"

# tool_execute_before
docker cp "$EXT_SRC/tool_execute_before/_15_action_boundary.py"      "$EXT_DEST/tool_execute_before/"
docker cp "$EXT_SRC/tool_execute_before/_20_meta_reasoning_gate.py"  "$EXT_DEST/tool_execute_before/"
docker cp "$EXT_SRC/tool_execute_before/_30_tool_fallback_advisor.py" "$EXT_DEST/tool_execute_before/"

# ── Deploy plugin API handlers ────────────────────────────────────────────────
# Loaded by A0 at /api/plugins/exocortex/<handler> — persistent in plugin dir.

API_SRC="$SCRIPT_DIR/plugin/api"
API_DEST="$CONTAINER:$PLUGIN_BASE/api"

docker cp "$API_SRC/api_theme_save.py"   "$API_DEST/"
docker cp "$API_SRC/api_theme_upload.py" "$API_DEST/"

# ── Deploy tools ──────────────────────────────────────────────────────────────
# Custom Agent Zero tools discovered automatically from plugin tools/ directory.

TOOLS_SRC="$SCRIPT_DIR/tools"
TOOLS_DEST="$CONTAINER:$PLUGIN_BASE/tools"

docker cp "$TOOLS_SRC/emit_artifact.py"       "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/investigation_tools.py" "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/oss.py"                 "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/stack_status.py"        "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/staging_note.py"        "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/swarmfish.py"           "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/tla_check.py"           "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/theme_author.py"        "$TOOLS_DEST/"
docker cp "$TOOLS_SRC/write_file.py"          "$TOOLS_DEST/"

# ── Deploy prompt files ───────────────────────────────────────────────────────
# These replace per-turn dynamic injection of static content.

PROMPT_SRC="$SCRIPT_DIR/prompts"
PLUGIN_PROMPT_SRC="$SCRIPT_DIR/plugin/prompts"
PROMPT_DEST="$CONTAINER:$PLUGIN_BASE/prompts"

docker cp "$PROMPT_SRC/agent.system.operator_calibration.md" "$PROMPT_DEST/"
docker cp "$PROMPT_SRC/agent.system.model_awareness.md"      "$PROMPT_DEST/"
docker cp "$PROMPT_SRC/agent.system.capabilities.md"         "$PROMPT_DEST/"

# Plugin tool documentation prompts (agent.system.tool.*.md — picked up by _11_tools_prompt)
for f in "$PLUGIN_PROMPT_SRC/"agent.system.tool.*.md; do
  [ -f "$f" ] && docker cp "$f" "$PROMPT_DEST/"
done

echo "  Plugin deployment complete."
echo "  Extensions: $(_exec $CONTAINER find $PLUGIN_BASE/extensions -name '*.py' | wc -l) Python files"
echo "  WebUI ext:  $(_exec $CONTAINER find $PLUGIN_BASE/extensions/webui -name '*.html' 2>/dev/null | wc -l) HTML components"
echo "  API:        $(_exec $CONTAINER ls $PLUGIN_BASE/api | wc -l) handlers"
echo "  Themes:     $(_exec $CONTAINER ls $PLUGIN_BASE/webui/themes | wc -l) files"
echo "  Tools:      $(_exec $CONTAINER ls $PLUGIN_BASE/tools | wc -l) files"
echo "  Prompts:    $(_exec $CONTAINER ls $PLUGIN_BASE/prompts | wc -l) files"
echo ""
echo "  Plugin visible at: Settings → Plugins → Exocortex"
echo "  Theme picker appears in sidebar above Preferences section."
echo "  Click ✏ next to Themes (with a theme active) to open the visual editor."
echo "  Reload the browser tab to activate (no agent restart needed for webui changes)."
