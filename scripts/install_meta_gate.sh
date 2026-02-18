#!/bin/bash
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
