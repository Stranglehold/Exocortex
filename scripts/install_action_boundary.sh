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
mkdir -p "$TARGET_EXT/tool_execute_before"
mkdir -p "$EXOCORTEX_USR"
mkdir -p "$LOGS_DIR"

# Deploy action boundary extension
if [ -f "$SOURCE_EXT/tool_execute_before/_15_action_boundary.py" ]; then
    cp "$SOURCE_EXT/tool_execute_before/_15_action_boundary.py" \
       "$TARGET_EXT/tool_execute_before/_15_action_boundary.py"
    echo "[ACTION-GATE] Installed _15_action_boundary.py"
else
    echo "[ACTION-GATE] ERROR: source file not found" >&2
    exit 1
fi

# Deploy config (only if not already present — don't overwrite operator customizations)
CONFIG_DEST="$EXOCORTEX_USR/action_boundary_config.json"
if [ ! -f "$CONFIG_DEST" ]; then
    cp "$REPO_DIR/action_boundary_config.json" "$CONFIG_DEST"
    echo "[ACTION-GATE] Installed action_boundary_config.json (default config)"
else
    echo "[ACTION-GATE] Config already exists — preserved operator config at $CONFIG_DEST"
fi

# Clear pycache
rm -rf "$TARGET_EXT/tool_execute_before/__pycache__/"
echo "[ACTION-GATE] Cleared pycache"

echo ""
echo "[ACTION-GATE] Done. Action boundary active — Tier 4 (S3/External-Write) blocked."
echo "  Config:    $CONFIG_DEST"
echo "  Audit log: /a0/usr/logs/action_audit.jsonl"
echo "  To run in audit-only mode: set tier_policies[4] to 'log' in config."
echo ""
echo "  Verify with:"
echo "    grep 'ACTION-GATE' /a0/usr/logs/action_audit.jsonl"
