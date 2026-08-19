#!/bin/bash
# Layer: A2A Compatibility Server (Organization Kernel Phase 4)
# Installs the A2A protocol adapter alongside Agent-Zero.
# Backs up any existing a2a_server directory before overwriting.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$REPO_DIR/a2a_server"
TARGET_DIR="/a0/python/a2a_server"
ORG_DIR="/a0/usr/organizations"
CONFIG_PATH="$ORG_DIR/a2a_config.json"

echo "[A2A] Installing A2A compatibility server..."

# ── Dependencies ────────────────────────────────────────────────
PYTHON="${PYTHON:-/opt/venv-a0/bin/python3}"
echo "[A2A] Checking dependencies..."
if ! "$PYTHON" -c "import aiohttp" 2>/dev/null; then
    echo "[A2A] Installing aiohttp..."
    "$PYTHON" -m pip install aiohttp
fi

# ── Server module deploy: STRIPPED 2026-08-19 (Tier 1.1) ────────
# This deployed the package to /a0/python/a2a_server — a path that does not exist
# in stock A0 v2.9 and that nothing consumes. Verified before cutting:
# _01_a2a_server_bootstrap.py sets
#   _A2A_DIR = "/a0/usr/plugins/_exocortex/services/a2a_server"
# and its own docstring says the server "ships in the plugin (services/a2a_server/)
# and self-launches, so it's clone-and-go". On live VekV2, /a0/python/a2a_server
# does not exist at all while the plugin copy does.
#
# The package is now deployed by the directory walk as part of the plugin tree.
# The config below is genuinely outside the plugin and is KEPT.
if false; then
    if [ -d "$TARGET_DIR" ]; then
        BACKUP_DIR="$TARGET_DIR/../a2a_server_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$TARGET_DIR" "$BACKUP_DIR"
        echo "[A2A] Backed up existing installation to $BACKUP_DIR"
    fi
    mkdir -p "$TARGET_DIR"
    for f in __init__.py config.py agent_card.py task_registry.py \
             translation.py agent_bridge.py server.py run.py; do
        cp "$SOURCE_DIR/$f" "$TARGET_DIR/"
    done
    echo "[A2A] Installed server module to $TARGET_DIR"
fi
echo "[A2A] server module: deployed by the plugin walk (services/a2a_server)"

# ── Install default config (read-merge-write) ───────────────────
if [ ! -f "$CONFIG_PATH" ]; then
    mkdir -p "$ORG_DIR"
    cp "$SOURCE_DIR/a2a_config.default.json" "$CONFIG_PATH"
    echo "[A2A] Created default config at $CONFIG_PATH"
else
    echo "[A2A] Config already exists at $CONFIG_PATH (not overwriting)"
fi

# ── Clear pycache ────────────────────────────────────────────────
if [ -d "$TARGET_DIR/__pycache__" ]; then
    rm -rf "$TARGET_DIR/__pycache__"
    echo "[A2A] Cleared __pycache__"
fi

echo "[A2A] Done. Start with: python -m a2a_server.run"
echo "[A2A] Agent Card: http://localhost:8200/.well-known/agent.json"
