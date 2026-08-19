#!/bin/bash
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

# Layer: Graph Workflow Engine (replaces HTN Plan Templates)
# Installs graph-aware plan selector and updated plan library.
# Backs up originals before overwriting.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions/before_main_llm_call"
TARGET_EXT="/a0/python/extensions/before_main_llm_call"

echo "[GraphEngine] Installing graph workflow engine..."

# Back up existing files
BACKUP_DIR="$TARGET_EXT/backups/pre_graph_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f "$TARGET_EXT/_15_htn_plan_selector.py" ]; then
    cp "$TARGET_EXT/_15_htn_plan_selector.py" "$BACKUP_DIR/"
    echo "[GraphEngine] Backed up _15_htn_plan_selector.py"
fi
if [ -f "$TARGET_EXT/htn_plan_library.json" ]; then
    cp "$TARGET_EXT/htn_plan_library.json" "$BACKUP_DIR/"
    echo "[GraphEngine] Backed up htn_plan_library.json"
fi

# Install graph-aware plan selector
if [ -f "$SOURCE_EXT/_15_htn_plan_selector.py" ]; then
    cp "$SOURCE_EXT/_15_htn_plan_selector.py" "$TARGET_EXT/"
    echo "[GraphEngine] Installed graph workflow engine (_15_)"
fi

# Install graph plan library
if [ -f "$SOURCE_EXT/htn_plan_library.json" ]; then
    cp "$SOURCE_EXT/htn_plan_library.json" "$TARGET_EXT/"
    echo "[GraphEngine] Installed graph plan library (10 plans)"
fi

# Clear pycache
if [ -d "$TARGET_EXT/__pycache__" ]; then
    rm -rf "$TARGET_EXT/__pycache__"
    echo "[GraphEngine] Cleared __pycache__"
fi

echo "[GraphEngine] Done. Graph workflows active on next chat."
