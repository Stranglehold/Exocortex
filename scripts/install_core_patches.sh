#!/usr/bin/env bash
# install_core_patches.sh
# Deploy core Agent Zero file patches to the active container.
#
# Patches:
#   patches/helpers/extract_tools.py
#     → adds plain-text fallback to json_parse_dirty()
#     → reasoning-distilled models no longer trigger the misformat loop
#       when they respond in natural language instead of JSON
#
#   patches/prompts/agent.system.main.communication.md
#     → clarifies that plain text is accepted for conversational replies
#
#   extensions/response_stream_chunk/_21_plain_text_response.py
#     → creates browser log item for plain text responses during streaming
#     → fixes responses not showing in web UI for reasoning-distilled models
#
# Usage: ./scripts/install_core_patches.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_DIR="$REPO_ROOT/patches"

echo "[PATCH] Deploying core patches to container: $CONTAINER"

# ── 1. Python helper: extract_tools.py ────────────────────────────────────────

HELPER_SRC="$PATCH_DIR/helpers/extract_tools.py"
HELPER_DST="/a0/python/helpers/extract_tools.py"
HELPER_PYCACHE="/a0/python/helpers/__pycache__"

if [ -f "$HELPER_SRC" ]; then
  docker exec "$CONTAINER" mkdir -p /a0/python/helpers
  docker cp "$HELPER_SRC" "$CONTAINER:$HELPER_DST"
  docker exec "$CONTAINER" bash -c "rm -rf '$HELPER_PYCACHE'" 2>/dev/null || true
  docker exec "$CONTAINER" bash -c "python3 -m py_compile '$HELPER_DST' && echo '[PATCH] extract_tools.py OK'"
  echo "[PATCH] helpers/extract_tools.py deployed."
else
  echo "[PATCH] WARNING: $HELPER_SRC not found — skipped."
fi

# ── 2. Prompt: agent.system.main.communication.md ────────────────────────────

PROMPT_SRC="$PATCH_DIR/prompts/agent.system.main.communication.md"
PROMPT_DST="/a0/prompts/agent.system.main.communication.md"

if [ -f "$PROMPT_SRC" ]; then
  docker cp "$PROMPT_SRC" "$CONTAINER:$PROMPT_DST"
  echo "[PATCH] prompts/agent.system.main.communication.md deployed."
else
  echo "[PATCH] WARNING: $PROMPT_SRC not found — skipped."
fi

# ── 3. Extension: _21_plain_text_response.py ─────────────────────────────────

EXT_SRC="$REPO_ROOT/extensions/response_stream_chunk/_21_plain_text_response.py"
EXT_DST="/a0/python/extensions/response_stream_chunk/_21_plain_text_response.py"
EXT_PYCACHE="/a0/python/extensions/response_stream_chunk/__pycache__"

if [ -f "$EXT_SRC" ]; then
  docker exec "$CONTAINER" mkdir -p /a0/python/extensions/response_stream_chunk
  docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
  docker exec "$CONTAINER" bash -c "rm -rf '$EXT_PYCACHE'" 2>/dev/null || true
  docker exec "$CONTAINER" bash -c "python3 -m py_compile '$EXT_DST' && echo '[PATCH] _21_plain_text_response.py OK'"
  echo "[PATCH] extensions/response_stream_chunk/_21_plain_text_response.py deployed."
else
  echo "[PATCH] WARNING: $EXT_SRC not found — skipped."
fi

echo "[PATCH] Done. Restart agent-zero or start a fresh chat to load changes."
