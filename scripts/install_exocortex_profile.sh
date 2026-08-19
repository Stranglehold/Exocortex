#!/bin/bash
# install_exocortex_profile.sh
# Deploys Exocortex to the persistent profile path (Option 3 — profile-canonical).
#
# Extension target:  /a0/usr/agents/agent0/extensions/python/{hook}/
#   This path has the highest runtime priority (first in get_paths() order).
#   All Python extensions deploy here. Profile path wins on filename collision.
#
# Plugin target: /a0/usr/plugins/exocortex/
#   Infrastructure-only: tools, prompts, webui, manifests, default_config.
#   Extensions are NOT deployed to the plugin path (Option 3 design).
#
# Both paths are persistent — survive A0 container image updates.
#
# TOMBSTONE files (_19_context_pruner.py in before_main_llm_call) are skipped
# automatically — they contain only a "MOVED:" comment with no Extension class.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CONTAINER:-exocortex_v17}"
# !! KNOWN WRONG — 2026-08-19, proven by a fresh-container install test !!
# Live containers (VekV2, agent-zero-v2) run the stack at /a0/usr/plugins/_exocortex
# (WITH underscore): 184 files there, 0 here, and /api/plugins/_exocortex/* routes
# return 200 while the no-underscore form 404s. This constant is a leftover from the
# draft DEC-030 plan, which proposed /a0/usr/plugins/exocortex/ before the A0 v2.x
# plugin system existed. Ten files across the pipeline still hardcode this spelling.
#
# NOT changed here because it is not a one-line fix: the same install run also puts
# 82 extension files at /a0/usr/agents/agent0/extensions (the DEC-030 v1.x PROFILE
# path) and 27 at /a0/python (which does not exist in v2.9 stock). Repointing the
# plugin name without migrating those leaves the stack split across three dead paths.
# That is a migration, and it needs a design pass — see the buildplan item.
#
# CONSEQUENCE TO KNOW: plugin.yaml (repointed to the real tree above) correctly
# declares `name: _exocortex`, so a fresh install currently produces directory
# `exocortex/` holding a manifest that names `_exocortex`. The manifest is right for
# the target state and wrong for this constant. Fix them together, not separately.
PLUGIN_BASE="/a0/usr/plugins/exocortex"
PROFILE_EXT="/a0/usr/agents/agent0/extensions/python"

# On Windows Git Bash, docker exec arguments with Unix paths get translated by MSYS.
# Prefix docker exec commands with MSYS_NO_PATHCONV=1 to suppress this.
# docker cp is exempt — its "container:/path" format is not affected.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "  Deploying Exocortex ($CONTAINER)"
echo "  Source:     $SCRIPT_DIR"
echo "  Extensions: $PROFILE_EXT"
echo "  Plugin:     $PLUGIN_BASE"

# ── Create directory structure ────────────────────────────────────────────────

# ── Create directory structure ────────────────────────────────────────────────

# Profile path — Python extensions (highest priority in get_paths() order)
_exec "$CONTAINER" mkdir -p \
  "$PROFILE_EXT/before_main_llm_call" \
  "$PROFILE_EXT/error_format" \
  "$PROFILE_EXT/hist_add_before" \
  "$PROFILE_EXT/message_loop_end" \
  "$PROFILE_EXT/message_loop_prompts_after" \
  "$PROFILE_EXT/monologue_end" \
  "$PROFILE_EXT/reasoning_stream" \
  "$PROFILE_EXT/reasoning_stream_end" \
  "$PROFILE_EXT/response_stream_chunk" \
  "$PROFILE_EXT/response_stream_end" \
  "$PROFILE_EXT/tool_execute_after" \
  "$PROFILE_EXT/tool_execute_before"

# Plugin path — infrastructure only (tools, prompts, webui, manifests)
_exec "$CONTAINER" mkdir -p \
  "$PLUGIN_BASE/extensions/webui/sidebar-bottom-wrapper-start" \
  "$PLUGIN_BASE/extensions/webui/get_message_handler" \
  "$PLUGIN_BASE/api" \
  "$PLUGIN_BASE/tools" \
  "$PLUGIN_BASE/prompts" \
  "$PLUGIN_BASE/webui/themes" \
  "$PLUGIN_BASE/webui/backgrounds"

# ── Deploy plugin manifest ────────────────────────────────────────────────────
#
# 2026-08-19: plugin.yaml was sourced from the stale $SCRIPT_DIR/plugin/ mirror.
# That copy declares `name: exocortex` (the directory — and every registered route
# — is `_exocortex`) and omits `always_enabled: true`. A fresh install would have
# misnamed the plugin and left it disabled. It also carries version 2.0.0 against
# the live 1.0.0, which is probably why it read as newer and went unnoticed.
# Manifest now comes from the real tree; the other two are byte-identical in both
# and are pointed there for consistency.

docker cp "$SCRIPT_DIR/plugins/_exocortex/plugin.yaml"          "$CONTAINER:$PLUGIN_BASE/plugin.yaml"
docker cp "$SCRIPT_DIR/plugins/_exocortex/default_config.yaml"  "$CONTAINER:$PLUGIN_BASE/default_config.yaml"
docker cp "$SCRIPT_DIR/plugins/_exocortex/tool_domains.json"    "$CONTAINER:$PLUGIN_BASE/tool_domains.json"

# ── Model config: deploy for max_tokens + utility fallback ────────────────────
# We deploy _model_config/config.json for two reasons:
#   1. max_tokens: 16384 on the chat model — not settable through the A0 web UI.
#   2. utility_model only contains ctx_input (no name/provider), so it inherits
#      the chat model via the patched get_utility_model_config() fallback.
#      Changing the model in the web UI only requires updating chat_model.name
#      here — utility follows automatically. No second model loads.
# NOTE: chat_model.name in this config MUST match what LM Studio has loaded.
#       Update it here when switching models, not in the A0 web UI.
MODEL_CONFIG_SRC="$SCRIPT_DIR/patches/plugins/_model_config"
MODEL_CONFIG_PLUGIN_DEST="$CONTAINER:/a0/usr/agents/agent0/plugins/_model_config"
MODEL_CONFIG_CODE_DEST="$CONTAINER:/a0/plugins/_model_config/helpers"

docker cp "$MODEL_CONFIG_SRC/config.json"                     "$MODEL_CONFIG_PLUGIN_DEST/config.json"

# ── DISABLED 2026-08-19 (Tier 1.1 step 1) — this line BRICKED fresh v2.9 containers ──
# It overwrote A0 core's model_config.py with our v1.18-era copy (ours 614 lines,
# v2.9 stock 908 — a wholesale stale replacement, not a patch). Ours DROPS
# DEFAULT_PRESET_NAME and _ensure_default_preset, which v2.9's own
# _10_migrate_model_config startup extension calls UNCONDITIONALLY. Result: A0
# crash-loops and the container never serves.
#
# Proven causal, not inferred: our file -> crash-loop; `git checkout` of stock ->
# boots immediately. A hand-written presets.yaml also crashes on our module and is
# accepted fine on stock.
#
# Opus's call: drop our version entirely, run stock. If v2.9's migration needs these
# symbols then v2.9 manages presets correctly and our override is actively harmful.
# If custom behaviour is needed later, add it ON TOP of v2.9's file (the PTY-patch
# pattern: surgical addition), never as a replacement.
#
# Guarded by scripts/check_core_patch_staleness.py — any STALE result blocks the gate.
# docker cp "$MODEL_CONFIG_SRC/helpers/model_config.py"       "$MODEL_CONFIG_CODE_DEST/model_config.py"

# ── Deploy webui assets (theme system) ───────────────────────────────────────

# 2026-08-19: repointed from the stale $SCRIPT_DIR/plugin/ mirror. Every named file
# this block copies was older than what is live — all three .js assets plus the
# big-shell, kaer-morhen, and shadow-moses themes. Same curated file list, current
# source. (The remaining count difference between the trees IS deliberate curation:
# this block ships named assets, not the whole directory.)
WEBUI_SRC="$SCRIPT_DIR/plugins/_exocortex/webui"
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
# 2026-08-19: repointed — both named files here were stale in the mirror too.
WEBUI_EXT_SRC="$SCRIPT_DIR/plugins/_exocortex/extensions/webui"
WEBUI_EXT_DEST="$CONTAINER:$PLUGIN_BASE/extensions/webui"

docker cp "$WEBUI_EXT_SRC/sidebar-bottom-wrapper-start/theme-picker.html" \
  "$WEBUI_EXT_DEST/sidebar-bottom-wrapper-start/"

# Artifact framework — message handler (DOMPurify hook + ExoArtifact import at module load time)
# NOTE: page-head HTML extension removed — importComponent causes layout disruption.
# DOMPurify hook and exo-artifact.js import live in artifact-handler.js top-level scope instead.
docker cp "$WEBUI_EXT_SRC/get_message_handler/artifact-handler.js" \
  "$WEBUI_EXT_DEST/get_message_handler/"

# ── Deploy extensions → profile path (Option 3) ───────────────────────────────
# Deploys ALL .py files from each hook directory in the repo.
# Tombstone files (containing only "MOVED:" comments) are detected and skipped.
# Data files (slot_taxonomy.json, htn_plan_library.json) are deployed alongside.
#
# The `extensions/python/<hook>/` subdirectory holds newer proactive_supervisor
# hooks that were structured differently from the main extension source tree.
# Those deploy to the same hook dirs in the profile path.

EXT_SRC="$SCRIPT_DIR/extensions"
EXT_DEST="$CONTAINER:$PROFILE_EXT"
deployed_ext=0
skipped_ext=0

for hook in \
  before_main_llm_call \
  error_format \
  hist_add_before \
  message_loop_end \
  message_loop_prompts_after \
  monologue_end \
  reasoning_stream \
  reasoning_stream_end \
  response_stream_chunk \
  response_stream_end \
  tool_execute_after \
  tool_execute_before
do
  src_dir="$EXT_SRC/$hook"

  if [ -d "$src_dir" ]; then
    for f in "$src_dir"/*.py "$src_dir"/*.json; do
      [ -f "$f" ] || continue
      name=$(basename "$f")

      # Skip tombstone .py files — they start with "MOVED:" and have no Extension class
      if [[ "$name" == *.py ]]; then
        first_line=$(head -2 "$f" | tail -1)
        if [[ "$first_line" == MOVED:* ]]; then
          echo "    ~ SKIP tombstone  $hook/$name"
          skipped_ext=$((skipped_ext + 1))
          continue
        fi
      fi

      docker cp "$f" "$EXT_DEST/$hook/"
      deployed_ext=$((deployed_ext + 1))
    done
  fi

  # Also deploy from extensions/python/<hook>/ if it exists (proactive_supervisor etc.)
  py_src_dir="$EXT_SRC/python/$hook"
  if [ -d "$py_src_dir" ]; then
    for f in "$py_src_dir"/*.py; do
      [ -f "$f" ] || continue
      docker cp "$f" "$EXT_DEST/$hook/"
      deployed_ext=$((deployed_ext + 1))
    done
  fi
done

echo "  Extensions: $deployed_ext deployed, $skipped_ext tombstones skipped"

# ── Deploy plugin API handlers ────────────────────────────────────────────────
# Loaded by A0 at /api/plugins/_exocortex/<handler> — persistent in plugin dir.
#
# 2026-08-19: this block used to name two files from $SCRIPT_DIR/plugin/api — a
# SECOND, stale copy of the tree. It shipped 2 of 6 handlers, and its copies of
# the two it did ship were older than what was live. Running the installer would
# have downgraded api_theme_save/upload AND left chat_retention, idle_control,
# idle_cycle, office_feed, and diagnostics uninstalled — the idle engine and the
# Office panel both depend on handlers that were never in the pipeline.
# Now: copy every handler from the real tree, so a fresh install matches a
# hand-deployed container.

API_SRC="$SCRIPT_DIR/plugins/_exocortex/api"
API_DEST="$CONTAINER:$PLUGIN_BASE/api"

api_count=0
for api_file in "$API_SRC"/*.py; do
  [ -f "$api_file" ] || continue
  docker cp "$api_file" "$API_DEST/" && api_count=$((api_count + 1))
done
echo "  API handlers: $api_count deployed from plugins/_exocortex/api"

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

# Create per-tool stub files so A0's single-file dispatcher can find multi-class tools
# (oss.py has 13 classes, swarmfish.py has 5, investigation_tools.py has 5)
STUBS_SCRIPT="$SCRIPT_DIR/scripts/create_tool_stubs.py"
if [ -f "$STUBS_SCRIPT" ]; then
  docker cp "$STUBS_SCRIPT" "$CONTAINER:/tmp/create_tool_stubs.py"
  docker exec "$CONTAINER" /opt/venv-a0/bin/python3 /tmp/create_tool_stubs.py
else
  echo "  WARNING: scripts/create_tool_stubs.py not found — tool stubs not created"
fi

echo "  Deployment complete."
echo "  Extensions (profile):  $(_exec $CONTAINER find $PROFILE_EXT -name '*.py' | wc -l) Python files → $PROFILE_EXT"
echo "  WebUI ext (plugin):    $(_exec $CONTAINER find $PLUGIN_BASE/extensions/webui -name '*.html' 2>/dev/null | wc -l) HTML components"
echo "  API (plugin):          $(_exec $CONTAINER ls $PLUGIN_BASE/api | wc -l) handlers"
echo "  Themes (plugin):       $(_exec $CONTAINER ls $PLUGIN_BASE/webui/themes | wc -l) files"
echo "  Tools (plugin):        $(_exec $CONTAINER ls $PLUGIN_BASE/tools | wc -l) files"
echo "  Prompts (plugin):      $(_exec $CONTAINER ls $PLUGIN_BASE/prompts | wc -l) files"
echo ""
echo "  Restart agent-zero or start a fresh chat to load extension changes."
echo "  Plugin visible at: Settings → Plugins → Exocortex"
echo "  Run scripts/verify_deployment.sh to confirm all extensions are at correct paths."
