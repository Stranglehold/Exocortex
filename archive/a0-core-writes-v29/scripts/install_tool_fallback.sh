#!/bin/bash
# Layer: Tool Fallback Chain
# Installs tool failure classification and fallback advisory extensions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions"
TARGET_EXT="/a0/python/extensions"

echo "[ToolFallback] Installing tool fallback chain..."

# ── STRIPPED 2026-08-19 (Tier 1.1): wrote to a dead root; the plugin walk deploys this ──
AFTER_DIR="$TARGET_EXT/tool_execute_after"
BEFORE_DIR="$TARGET_EXT/tool_execute_before"
if false; then
    mkdir -p "$AFTER_DIR" "$BEFORE_DIR"
    cp "$SOURCE_EXT/tool_execute_after/_30_tool_fallback_logger.py"   "$AFTER_DIR/"
    cp "$SOURCE_EXT/tool_execute_before/_30_tool_fallback_advisor.py" "$BEFORE_DIR/"
    rm -rf "$AFTER_DIR/__pycache__/" "$BEFORE_DIR/__pycache__/" 2>/dev/null
fi
echo "[ToolFallback] extensions: deployed by the plugin walk"
echo "[ToolFallback] Done. Prompt content (kept) installed above."

# Install updated dialog detection prompt
PROMPT_SRC="$REPO_DIR/prompts"
PROMPT_TARGET="/a0/prompts"
if [ -f "$PROMPT_SRC/fw.code.pause_dialog.md" ]; then
    cp "$PROMPT_SRC/fw.code.pause_dialog.md" "$PROMPT_TARGET/"
    echo "[ToolFallback] Installed updated dialog detection prompt"
fi
