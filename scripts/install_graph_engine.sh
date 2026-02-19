#!/bin/bash
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
