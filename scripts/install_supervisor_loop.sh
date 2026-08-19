#!/bin/bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: /a0/python/extensions/message_loop_end
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

# Layer: Supervisor Loop (Organization Kernel Phase 2)
# Installs XO supervisory extension for anomaly detection and steering injection

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions"
TARGET_EXT="/a0/python/extensions"

echo "[Supervisor] Installing supervisor loop..."

# message_loop_end — supervisor extension
END_DIR="$TARGET_EXT/message_loop_end"
mkdir -p "$END_DIR"
if [ -f "$SOURCE_EXT/message_loop_end/_50_supervisor_loop.py" ]; then
    cp "$SOURCE_EXT/message_loop_end/_50_supervisor_loop.py" "$END_DIR/"
    echo "[Supervisor] Installed supervisor loop (_50_)"
fi

# Clear pycache
if [ -d "$END_DIR/__pycache__" ]; then
    rm -rf "$END_DIR/__pycache__"
    echo "[Supervisor] Cleared __pycache__"
fi

echo "[Supervisor] Done. XO supervisory function active when organization is enabled."
