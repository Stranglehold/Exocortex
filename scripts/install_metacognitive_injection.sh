#!/usr/bin/env bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: /a0/python/extensions/before_main_llm_call
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

# install_metacognitive_injection.sh
# Deploy the Metacognitive Injection layer (_14_) to the active container.
#
# Usage: ./scripts/install_metacognitive_injection.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-${CONTAINER:-exocortex_v16}}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_14_metacognitive_injection.py"
EXT_DST="/a0/python/extensions/before_main_llm_call/_14_metacognitive_injection.py"
PYCACHE="/a0/python/extensions/before_main_llm_call/__pycache__"

echo "[META] Deploying Metacognitive Injection to container: $CONTAINER"

# 1. Verify source file exists
if [ ! -f "$EXT_SRC" ]; then
  echo "[META] ERROR: Source file not found: $EXT_SRC"
  exit 1
fi

# 2. Ensure target directory exists in container
docker exec "$CONTAINER" mkdir -p /a0/python/extensions/before_main_llm_call

# 3. Deploy extension
docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
echo "[META] Extension deployed."

# 4. Clear pycache
docker exec "$CONTAINER" bash -c "rm -rf '$PYCACHE'" 2>/dev/null || true
echo "[META] pycache cleared."

# 5. Verify compilation
docker exec "$CONTAINER" bash -c "python3 -m py_compile '$EXT_DST' && echo '[META] Compilation OK'"

echo "[META] Done. Extension active on next message loop iteration."
echo "[META] Verify: look for [META] Injected model config note. in container logs."
