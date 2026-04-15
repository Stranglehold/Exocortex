#!/bin/bash
# install.sh — Deploy SWARMFISH V2 plugin to A0 container
#
# Installs the plugin at /a0/usr/plugins/swarmfish/ — the persistent user plugin
# path that survives A0 container image updates.
#
# Usage: CONTAINER=exocortex_v16 bash install.sh
#   or:  bash install.sh  (uses default container name)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CONTAINER:-exocortex_v16}"
PLUGIN_BASE="/a0/usr/plugins/swarmfish"
DATA_DIR="/a0/usr/swarmfish"

# On Windows Git Bash, docker exec arguments with Unix paths get translated by MSYS.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "  Deploying SWARMFISH V2 plugin to $CONTAINER"
echo "  Source: $SCRIPT_DIR"
echo "  Target: $PLUGIN_BASE"

# ── Create directory structure ─────────────────────────────────────────────────

_exec "$CONTAINER" mkdir -p \
  "$PLUGIN_BASE/src" \
  "$PLUGIN_BASE/api" \
  "$PLUGIN_BASE/prompts" \
  "$DATA_DIR"

# ── Plugin manifest ────────────────────────────────────────────────────────────

docker cp "$SCRIPT_DIR/plugin.yaml" "$CONTAINER:$PLUGIN_BASE/plugin.yaml"

# ── Core src modules ───────────────────────────────────────────────────────────

SRC="$SCRIPT_DIR/src"
DEST="$CONTAINER:$PLUGIN_BASE/src"

docker cp "$SRC/__init__.py"     "$DEST/"
docker cp "$SRC/db.py"           "$DEST/"
docker cp "$SRC/profiles.py"     "$DEST/"
docker cp "$SRC/predictor.py"    "$DEST/"
docker cp "$SRC/aggregator.py"   "$DEST/"
docker cp "$SRC/calibration.py"  "$DEST/"

# ── API handlers ───────────────────────────────────────────────────────────────

API_SRC="$SCRIPT_DIR/api"
API_DEST="$CONTAINER:$PLUGIN_BASE/api"

docker cp "$API_SRC/api_swarmfish_predict.py"     "$API_DEST/"
docker cp "$API_SRC/api_swarmfish_session.py"     "$API_DEST/"
docker cp "$API_SRC/api_swarmfish_sessions.py"    "$API_DEST/"
docker cp "$API_SRC/api_swarmfish_calibration.py" "$API_DEST/"
docker cp "$API_SRC/api_swarmfish_outcome.py"     "$API_DEST/"

# ── Tool documentation (picked up by _11_tools_prompt scan) ───────────────────

PROMPT_SRC="$SCRIPT_DIR/prompts"
PROMPT_DEST="$CONTAINER:$PLUGIN_BASE/prompts"

docker cp "$PROMPT_SRC/agent.system.tool.swarmfish.md" "$PROMPT_DEST/"

# ── Tool files (deployed to A0 native tools dir — where A0 dispatches from) ──
# A0 loads tool classes from /a0/tools/. Plugin subdirs are text-injection only.

A0_TOOLS="$CONTAINER:/a0/tools"
TOOLS_SRC="$SCRIPT_DIR/../../tools"

docker cp "$TOOLS_SRC/swarmfish_predict.py"     "$A0_TOOLS/"
docker cp "$TOOLS_SRC/swarmfish_session.py"     "$A0_TOOLS/"
docker cp "$TOOLS_SRC/swarmfish_sessions.py"    "$A0_TOOLS/"
docker cp "$TOOLS_SRC/swarmfish_calibration.py" "$A0_TOOLS/"
docker cp "$TOOLS_SRC/swarmfish_outcome.py"     "$A0_TOOLS/"
docker cp "$TOOLS_SRC/swarmfish_panel.py"       "$A0_TOOLS/"

# Tool documentation also goes to Exocortex plugin prompts
EXOCORTEX_PROMPTS="$CONTAINER:/a0/usr/plugins/exocortex/prompts"
docker cp "$PROMPT_SRC/agent.system.tool.swarmfish.md" "$EXOCORTEX_PROMPTS/"

# ── Clear pycache ──────────────────────────────────────────────────────────────

_exec "$CONTAINER" find "$PLUGIN_BASE" -name "*.pyc" -delete 2>/dev/null || true
_exec "$CONTAINER" find "$PLUGIN_BASE" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ── Syntax check ──────────────────────────────────────────────────────────────

echo "  Syntax checking src modules..."
for f in db.py profiles.py predictor.py aggregator.py calibration.py; do
  _exec "$CONTAINER" python3 -m py_compile "$PLUGIN_BASE/src/$f" && echo "    ✓ $f" || echo "    ✗ $f FAILED"
done

echo "  Syntax checking API handlers..."
for f in api_swarmfish_predict.py api_swarmfish_session.py api_swarmfish_sessions.py api_swarmfish_calibration.py api_swarmfish_outcome.py; do
  _exec "$CONTAINER" python3 -m py_compile "$PLUGIN_BASE/api/$f" && echo "    ✓ $f" || echo "    ✗ $f FAILED"
done

echo "  Syntax checking tools..."
A0_TOOLS_PATH="/a0/tools"
for f in swarmfish_predict.py swarmfish_session.py swarmfish_sessions.py swarmfish_calibration.py swarmfish_outcome.py swarmfish_panel.py; do
  _exec "$CONTAINER" python3 -m py_compile "$A0_TOOLS_PATH/$f" && echo "    ✓ $f" || echo "    ✗ $f FAILED"
done

# ── Summary ────────────────────────────────────────────────────────────────────

echo ""
echo "  SWARMFISH V2 plugin deployed."
echo "  Plugin path: $PLUGIN_BASE"
echo "  Data path:   $DATA_DIR"
echo "  API base:    /api/plugins/swarmfish/"
echo ""
echo "  V1 external Docker service (swarmfish_app, swarmfish_postgres, swarmfish_redis)"
echo "  can now be stopped — V2 runs entirely within the A0 container."
echo ""
echo "  Reload the browser tab to activate (no agent restart needed for API handler changes)."
echo "  For tool file changes: restart the A0 container or wait for next session."
