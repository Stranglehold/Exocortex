#!/bin/bash
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
