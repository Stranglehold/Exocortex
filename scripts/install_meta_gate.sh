#!/bin/bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: /a0/python/extensions/tool_execute_before
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

# Layer: Meta-Reasoning Gate
# Installs parameter validation and auto-correction for tool calls

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions"
TARGET_EXT="/a0/python/extensions"

echo "[MetaGate] Installing meta-reasoning gate..."

# tool_execute_before — parameter validator
BEFORE_DIR="$TARGET_EXT/tool_execute_before"
mkdir -p "$BEFORE_DIR"
if [ -f "$SOURCE_EXT/tool_execute_before/_20_meta_reasoning_gate.py" ]; then
    cp "$SOURCE_EXT/tool_execute_before/_20_meta_reasoning_gate.py" "$BEFORE_DIR/"
    echo "[MetaGate] Installed parameter validation gate"
fi

echo "[MetaGate] Done. Tool argument validation and auto-correction active."
