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
#   extensions/before_main_llm_call/_18_memory_catalog.py
#     → injects compact memory domain catalog once at session start
#     → gives agent visibility into what's stored before querying blind
#
# Usage: ./scripts/install_core_patches.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_DIR="$REPO_ROOT/patches"

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "[PATCH] Deploying core patches to container: $CONTAINER"

# ── 0. Tool: browser_agent.py + captcha_solver.py ────────────────────────────

BROWSER_TOOL_SRC="$PATCH_DIR/tools/browser_agent.py"
BROWSER_TOOL_DST="/a0/python/tools/browser_agent.py"
CAPTCHA_SRC="$PATCH_DIR/tools/captcha_solver.py"
CAPTCHA_DST="/a0/python/tools/captcha_solver.py"
TOOLS_PYCACHE="/a0/python/tools/__pycache__"

if [ -f "$BROWSER_TOOL_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/tools
  docker cp "$BROWSER_TOOL_SRC" "$CONTAINER:$BROWSER_TOOL_DST"
  echo "[PATCH] tools/browser_agent.py deployed."
else
  echo "[PATCH] WARNING: $BROWSER_TOOL_SRC not found — skipped."
fi

if [ -f "$CAPTCHA_SRC" ]; then
  docker cp "$CAPTCHA_SRC" "$CONTAINER:$CAPTCHA_DST"
  echo "[PATCH] tools/captcha_solver.py deployed."
else
  echo "[PATCH] WARNING: $CAPTCHA_SRC not found — skipped."
fi

if [ -f "$BROWSER_TOOL_SRC" ] || [ -f "$CAPTCHA_SRC" ]; then
  _exec "$CONTAINER" bash -c "rm -rf '$TOOLS_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "cd /a0 && /opt/venv-a0/bin/python3 -m py_compile python/tools/browser_agent.py && echo '[PATCH] browser_agent.py OK'"
  _exec "$CONTAINER" bash -c "cd /a0 && /opt/venv-a0/bin/python3 -m py_compile python/tools/captcha_solver.py && echo '[PATCH] captcha_solver.py OK'"
fi

# ── 1. Python helper: extract_tools.py ────────────────────────────────────────

HELPER_SRC="$PATCH_DIR/helpers/extract_tools.py"
HELPER_DST="/a0/python/helpers/extract_tools.py"
HELPER_PYCACHE="/a0/python/helpers/__pycache__"

if [ -f "$HELPER_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/helpers
  docker cp "$HELPER_SRC" "$CONTAINER:$HELPER_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$HELPER_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "python3 -m py_compile '$HELPER_DST' && echo '[PATCH] extract_tools.py OK'"
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

# ── 2b. Prompt: browser_agent.system.md (CAPTCHA guidance) ───────────────────

BROWSER_PROMPT_SRC="$PATCH_DIR/prompts/browser_agent.system.md"
BROWSER_PROMPT_DST="/a0/prompts/browser_agent.system.md"

if [ -f "$BROWSER_PROMPT_SRC" ]; then
  docker cp "$BROWSER_PROMPT_SRC" "$CONTAINER:$BROWSER_PROMPT_DST"
  echo "[PATCH] prompts/browser_agent.system.md (CAPTCHA guidance) deployed."
else
  echo "[PATCH] WARNING: $BROWSER_PROMPT_SRC not found — skipped."
fi

# ── 3. Extension: _21_plain_text_response.py ─────────────────────────────────

EXT_SRC="$REPO_ROOT/extensions/response_stream_chunk/_21_plain_text_response.py"
EXT_DST="/a0/python/extensions/response_stream_chunk/_21_plain_text_response.py"
EXT_PYCACHE="/a0/python/extensions/response_stream_chunk/__pycache__"

if [ -f "$EXT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/extensions/response_stream_chunk
  docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$EXT_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "python3 -m py_compile '$EXT_DST' && echo '[PATCH] _21_plain_text_response.py OK'"
  echo "[PATCH] extensions/response_stream_chunk/_21_plain_text_response.py deployed."
else
  echo "[PATCH] WARNING: $EXT_SRC not found — skipped."
fi

# ── 4. Extension: _18_memory_catalog.py ──────────────────────────────────────

CAT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_18_memory_catalog.py"
CAT_DST="/a0/python/extensions/before_main_llm_call/_18_memory_catalog.py"
CAT_PYCACHE="/a0/python/extensions/before_main_llm_call/__pycache__"

if [ -f "$CAT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/extensions/before_main_llm_call
  docker cp "$CAT_SRC" "$CONTAINER:$CAT_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$CAT_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c "python3 -m py_compile '$CAT_DST' && echo '[PATCH] _18_memory_catalog.py OK'"
  echo "[PATCH] extensions/before_main_llm_call/_18_memory_catalog.py deployed."
else
  echo "[PATCH] WARNING: $CAT_SRC not found — skipped."
fi

echo "[PATCH] Done. Restart agent-zero or start a fresh chat to load changes."
