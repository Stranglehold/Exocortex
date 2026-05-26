#!/bin/bash
# install.sh — Deploy OSS V2 plugin to A0 container
#
# Installs the plugin at /a0/usr/plugins/oss/ — persistent user plugin path
# that survives A0 container image updates.
#
# Usage: CONTAINER=exocortex_v16 bash install.sh
#   or:  bash install.sh  (uses default container name)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CONTAINER:-exocortex_v16}"
PLUGIN_BASE="/a0/usr/plugins/oss"
DATA_DIR="/a0/usr/oss"

# On Windows Git Bash, docker exec arguments with Unix paths get translated by MSYS.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "  Deploying OSS V2 plugin to $CONTAINER"
echo "  Source: $SCRIPT_DIR"
echo "  Target: $PLUGIN_BASE"

# ── Create directory structure ─────────────────────────────────────────────────

_exec "$CONTAINER" mkdir -p \
  "$PLUGIN_BASE/src" \
  "$PLUGIN_BASE/api" \
  "$PLUGIN_BASE/webui" \
  "$PLUGIN_BASE/extensions/webui/right_canvas_register_surfaces" \
  "$PLUGIN_BASE/extensions/webui/right-canvas-panels" \
  "$DATA_DIR"

# ── Plugin manifest ────────────────────────────────────────────────────────────

docker cp "$SCRIPT_DIR/plugin.yaml" "$CONTAINER:$PLUGIN_BASE/plugin.yaml"

# ── Core src modules ───────────────────────────────────────────────────────────

SRC="$SCRIPT_DIR/src"
DEST="$CONTAINER:$PLUGIN_BASE/src"

docker cp "$SRC/__init__.py"              "$DEST/"
docker cp "$SRC/db.py"                   "$DEST/"
docker cp "$SRC/llm_config.py"           "$DEST/"
docker cp "$SRC/ingest.py"               "$DEST/"
docker cp "$SRC/audit.py"                "$DEST/"
docker cp "$SRC/operator_state.py"       "$DEST/"
docker cp "$SRC/hypothesis.py"           "$DEST/"
docker cp "$SRC/source_intel.py"         "$DEST/"
docker cp "$SRC/contradict.py"           "$DEST/"
docker cp "$SRC/silence.py"              "$DEST/"
docker cp "$SRC/activation.py"           "$DEST/"
docker cp "$SRC/narrative_drift.py"      "$DEST/"
docker cp "$SRC/retcon_ledger.py"        "$DEST/"
docker cp "$SRC/threat_model.py"         "$DEST/"
docker cp "$SRC/social_ingest.py"        "$DEST/"
docker cp "$SRC/contamination_cascade.py" "$DEST/"
docker cp "$SRC/propagation_dynamics.py" "$DEST/"
docker cp "$SRC/meta_detection.py"       "$DEST/"
docker cp "$SRC/questions.py"            "$DEST/"
docker cp "$SRC/synthesis.py"            "$DEST/"
docker cp "$SRC/credibility.py"          "$DEST/"
docker cp "$SRC/rejection.py"            "$DEST/"
docker cp "$SRC/narrative_geometry.py"   "$DEST/"

# ── API handlers ───────────────────────────────────────────────────────────────

API_SRC="$SCRIPT_DIR/api"
API_DEST="$CONTAINER:$PLUGIN_BASE/api"

docker cp "$API_SRC/api_oss_health.py"        "$API_DEST/"
docker cp "$API_SRC/api_oss_feed.py"          "$API_DEST/"
docker cp "$API_SRC/api_oss_drift.py"         "$API_DEST/"
docker cp "$API_SRC/api_oss_contradictions.py" "$API_DEST/"
docker cp "$API_SRC/api_oss_silence.py"       "$API_DEST/"
docker cp "$API_SRC/api_oss_activation.py"    "$API_DEST/"
docker cp "$API_SRC/api_oss_topics.py"        "$API_DEST/"
docker cp "$API_SRC/api_oss_add_topic.py"     "$API_DEST/"
docker cp "$API_SRC/api_oss_sources.py"       "$API_DEST/"
docker cp "$API_SRC/api_oss_hypotheses.py"    "$API_DEST/"
docker cp "$API_SRC/api_oss_submit.py"        "$API_DEST/"
docker cp "$API_SRC/api_oss_ingest.py"        "$API_DEST/"
docker cp "$API_SRC/api_oss_questions.py"     "$API_DEST/"
docker cp "$API_SRC/api_oss_synthesis.py"     "$API_DEST/"
docker cp "$API_SRC/api_oss_credibility.py"   "$API_DEST/"
docker cp "$API_SRC/api_oss_rejections.py"    "$API_DEST/"
docker cp "$API_SRC/api_oss_staging.py"       "$API_DEST/"
docker cp "$API_SRC/api_oss_network.py"       "$API_DEST/"
docker cp "$API_SRC/api_oss_narrative_geometry.py" "$API_DEST/"

# ── WebUI assets (right-canvas v1.13 surface system) ─────────────────────────

WEBUI_SRC="$SCRIPT_DIR/webui"

docker cp "$WEBUI_SRC/intelligence-store.js" \
    "$CONTAINER:$PLUGIN_BASE/webui/intelligence-store.js"
docker cp "$WEBUI_SRC/intelligence-panel.html" \
    "$CONTAINER:$PLUGIN_BASE/webui/intelligence-panel.html"
docker cp "$WEBUI_SRC/register-intelligence.js" \
    "$CONTAINER:$PLUGIN_BASE/extensions/webui/right_canvas_register_surfaces/register-intelligence.js"
docker cp "$SCRIPT_DIR/extensions/webui/right-canvas-panels/intelligence-panel.html" \
    "$CONTAINER:$PLUGIN_BASE/extensions/webui/right-canvas-panels/intelligence-panel.html"

# ── Tool files (deployed to A0 native tools dir — where A0 dispatches from) ──
# A0 loads tool classes from /a0/tools/, not from plugin subdirectories.
# The plugin's tools/ dir is only scanned by _16_tool_registry for text injection.

A0_TOOLS="$CONTAINER:/a0/tools"
TOOLS_SRC="$SCRIPT_DIR/../../tools"

docker cp "$TOOLS_SRC/oss_ingest_sprint.py" "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_topic.py"         "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_drift.py"         "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_dynamics.py"      "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_hypotheses.py"    "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_health.py"        "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_submit.py"        "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_list_topics.py"   "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_add_topic.py"     "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_ingest_pause.py"  "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_ingest_resume.py" "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_question.py"      "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_synthesize.py"    "$A0_TOOLS/"
docker cp "$TOOLS_SRC/oss_panel.py"         "$A0_TOOLS/"

# ── Clear pycache ──────────────────────────────────────────────────────────────

_exec "$CONTAINER" find "$PLUGIN_BASE" -name "*.pyc" -delete 2>/dev/null || true
_exec "$CONTAINER" find "$PLUGIN_BASE" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ── Syntax check: src modules ─────────────────────────────────────────────────

echo "  Syntax checking src modules..."
for f in db.py ingest.py audit.py operator_state.py hypothesis.py source_intel.py \
          contradict.py silence.py activation.py narrative_drift.py retcon_ledger.py \
          threat_model.py social_ingest.py contamination_cascade.py \
          propagation_dynamics.py meta_detection.py \
          questions.py synthesis.py credibility.py rejection.py \
          narrative_geometry.py llm_config.py __init__.py; do
  if _exec "$CONTAINER" python3 -m py_compile "$PLUGIN_BASE/src/$f" 2>/dev/null; then
    echo "    ✓ src/$f"
  else
    echo "    ✗ src/$f  FAILED"
    FAILED=1
  fi
done

# ── Syntax check: API handlers ────────────────────────────────────────────────

echo "  Syntax checking API handlers..."
for f in api_oss_health.py api_oss_feed.py api_oss_drift.py api_oss_contradictions.py \
          api_oss_silence.py api_oss_activation.py api_oss_topics.py api_oss_add_topic.py \
          api_oss_sources.py api_oss_hypotheses.py api_oss_submit.py api_oss_ingest.py \
          api_oss_questions.py api_oss_synthesis.py api_oss_credibility.py \
          api_oss_rejections.py api_oss_staging.py api_oss_network.py \
          api_oss_narrative_geometry.py; do
  if _exec "$CONTAINER" python3 -m py_compile "$PLUGIN_BASE/api/$f" 2>/dev/null; then
    echo "    ✓ api/$f"
  else
    echo "    ✗ api/$f  FAILED"
    FAILED=1
  fi
done

# ── Syntax check: tools ───────────────────────────────────────────────────────

echo "  Syntax checking tools..."
A0_TOOLS_PATH="/a0/tools"
for f in oss_ingest_sprint.py oss_topic.py oss_drift.py oss_dynamics.py oss_hypotheses.py oss_health.py \
          oss_submit.py oss_list_topics.py oss_add_topic.py \
          oss_ingest_pause.py oss_ingest_resume.py \
          oss_question.py oss_synthesize.py oss_panel.py; do
  if _exec "$CONTAINER" python3 -m py_compile "$A0_TOOLS_PATH/$f" 2>/dev/null; then
    echo "    ✓ tools/$f"
  else
    echo "    ✗ tools/$f  FAILED"
    FAILED=1
  fi
done

if [ "${FAILED}" = "1" ]; then
  echo ""
  echo "  One or more files failed syntax check. Fix before proceeding."
  exit 1
fi

# ── Summary ────────────────────────────────────────────────────────────────────

echo ""
echo "  OSS V2 plugin deployed."
echo "  Plugin path:  $PLUGIN_BASE"
echo "  Data path:    $DATA_DIR (SQLite DB + FAISS index created on first use)"
echo "  API base:     /api/plugins/oss/"
echo ""
echo "  V1 external Docker services (oss_app, oss_postgres)"
echo "  are no longer needed — V2 runs within the A0 container."
echo ""
echo "  Background ingestion starts PAUSED (OSS_INGEST_PAUSED=true by default)."
echo "  Use oss_ingest_resume or the panel Ingest button to start ingestion."
echo "  Reload browser tab to activate new API handlers."
echo "  For tool file changes: restart A0 container or wait for next session."
