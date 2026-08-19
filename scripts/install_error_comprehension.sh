#!/bin/bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: /a0/python/extensions/{tool_execute_after,tool_execute_before}
#
# Why the legacy paths are dead:
#   /a0/python/**                        does not exist in stock v2.9 — the old
#                                        pipeline CREATED it, then wrote into it
#   /a0/usr/agents/agent0/extensions/**  the DEC-030 profile path. Worse than
#                                        dead: it still LOADS, so it resurrected
#                                        extensions that had been retired
#                                        (_71_cache_warmer, _05_cache_warm_bypass,
#                                        _02_cache_metrics_logger, and the three
#                                        dropped by DEC-030 itself)
#   /a0/usr/plugins/exocortex/**         no underscore — wrong plugin name; every
#                                        registered route is /_exocortex
#
# Measured, not assumed: scripts/audit_install_writes.sh attributes every write to
# the step that made it. Manifest: specs/INSTALL_PIPELINE_WRITE_MANIFEST.md
#
# The file is kept rather than deleted so nobody recreates it from scratch.
# ==============================================================================

set -e

CONTAINER="${1:-flamboyant_bell}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "=== Installing Error Comprehension Layer ==="

# Deploy new extension
echo "[1/4] Deploying _20_error_comprehension.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_after/_20_error_comprehension.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_after/_20_error_comprehension.py"

# Deploy modified fallback logger
echo "[2/4] Deploying updated _30_tool_fallback_logger.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_after/_30_tool_fallback_logger.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_after/_30_tool_fallback_logger.py"

# Deploy modified fallback advisor
echo "[3/4] Deploying updated _30_tool_fallback_advisor.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_before/_30_tool_fallback_advisor.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_before/_30_tool_fallback_advisor.py"

# Clear pycache
echo "[4/4] Clearing pycache..."
_exec "$CONTAINER" rm -rf /a0/python/extensions/tool_execute_after/__pycache__/
_exec "$CONTAINER" rm -rf /a0/python/extensions/tool_execute_before/__pycache__/

echo ""
echo "=== Error Comprehension Layer Installed ==="
echo "Restart the container or wait for next agent loop to activate."
echo ""
echo "Verify with:"
echo "  docker logs $CONTAINER 2>&1 | grep 'ERROR-DX'"
