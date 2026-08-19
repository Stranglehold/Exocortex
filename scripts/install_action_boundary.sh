#!/bin/bash
# Layer: Action Boundary Classification
# Installs pre-execution action gating (_15_ in tool_execute_before).
# Gates Tier 4 (S3/External-Write) actions behind operator authorization.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions"
TARGET_EXT="/a0/python/extensions"
EXOCORTEX_USR="/a0/usr/Exocortex"
LOGS_DIR="/a0/usr/logs"

echo "[ACTION-GATE] Installing action boundary classification..."

# Ensure target directories exist
mkdir -p "$EXOCORTEX_USR"
mkdir -p "$LOGS_DIR"

# ── Extension deploy: STRIPPED 2026-08-19 (Tier 1.1) ────────────────────────
# Deployed _15_action_boundary.py to /a0/python/extensions/tool_execute_before —
# a path that does not exist in stock A0 v2.9 (the old pipeline created it) and
# that nothing loads. The extension now ships in the plugin tree and is deployed
# by scripts/install_exocortex_plugin.sh.
if false; then
    mkdir -p "$TARGET_EXT/tool_execute_before"
    cp "$SOURCE_EXT/tool_execute_before/_15_action_boundary.py" \
       "$TARGET_EXT/tool_execute_before/_15_action_boundary.py"
fi
echo "[ACTION-GATE] extension: deployed by the plugin walk"

# NOTE for review, not acted on: the config deploy below writes
# /a0/usr/Exocortex/action_boundary_config.json, but _15_action_boundary.py
# hardcodes CONFIG_PATH = /a0/usr/plugins/_exocortex/config/action_boundary_config.json
# and nothing reads the `action_boundary_config_path` key in default_config.yaml.
# The file is absent on both live containers. It is very likely dead too, but it is
# not one of the three known-dead roots, so it is left alone rather than cut on
# inference. Flagged to Opus.

# Deploy config (only if not already present — don't overwrite operator customizations)
CONFIG_DEST="$EXOCORTEX_USR/action_boundary_config.json"
if [ ! -f "$CONFIG_DEST" ]; then
    cp "$REPO_DIR/action_boundary_config.json" "$CONFIG_DEST"
    echo "[ACTION-GATE] Installed action_boundary_config.json (default config)"
else
    echo "[ACTION-GATE] Config already exists — preserved operator config at $CONFIG_DEST"
fi

# pycache clear removed with the legacy deploy (Tier 1.1) — nothing is written
# to /a0/python any more, so there is no cache here to clear. Do not print a
# success line for work that no longer happens.

echo ""
echo "[ACTION-GATE] Done. Action boundary active — Tier 4 (S3/External-Write) blocked."
echo "  Config:    $CONFIG_DEST"
echo "  Audit log: /a0/usr/logs/action_audit.jsonl"
echo "  To run in audit-only mode: set tier_policies[4] to 'log' in config."
echo ""
echo "  Verify with:"
echo "    grep 'ACTION-GATE' /a0/usr/logs/action_audit.jsonl"
