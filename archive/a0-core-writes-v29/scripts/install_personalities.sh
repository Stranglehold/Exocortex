#!/bin/bash
# Layer: Personality Loader
# Installs personality prompt plugin and creates personalities directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_PROMPTS="/a0/prompts"
TARGET_PERSONALITIES="/a0/usr/personalities"

echo "[Personality] Installing personality loader..."

# Create personalities directory if it doesn't exist
mkdir -p "$TARGET_PERSONALITIES"

# Backup existing role prompt if not already backed up
if [ -f "$TARGET_PROMPTS/agent.system.main.role.md" ]; then
    if [ ! -f "$TARGET_PROMPTS/.prompt_patch_originals/agent.system.main.role.md" ]; then
        mkdir -p "$TARGET_PROMPTS/.prompt_patch_originals"
        cp "$TARGET_PROMPTS/agent.system.main.role.md" \
           "$TARGET_PROMPTS/.prompt_patch_originals/agent.system.main.role.md"
        echo "[Personality] Backed up original role prompt"
    fi
fi

# Deploy plugin and modified prompt
cp "$REPO_DIR/prompts/agent.system.main.role.py" "$TARGET_PROMPTS/"
cp "$REPO_DIR/prompts/agent.system.main.role.md" "$TARGET_PROMPTS/"

echo "[Personality] Installed role prompt plugin"
echo "[Personality] Personalities directory: $TARGET_PERSONALITIES"
echo "[Personality] Drop AIEOS JSON files there to activate"
