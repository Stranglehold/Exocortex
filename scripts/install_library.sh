#!/usr/bin/env bash
# install_library.sh
# Deploy the Exocortex Document Library to the active container.
#
# Deploys:
#   tools/library.py
#     → /a0/python/tools/library.py
#     → /a0/usr/agents/agent0/tools/library.py  (profile path, DEC-030)
#
#   extensions/before_main_llm_call/_17_library_catalog.py
#     → /a0/usr/agents/agent0/extensions/before_main_llm_call/_17_library_catalog.py
#
#   Creates persistent storage directories in the container:
#     /a0/usr/library/           (catalog root)
#     /a0/usr/library/docs/      (file copies)
#     /a0/usr/memory/library/    (FAISS index, created on first add)
#
# Usage: ./scripts/install_library.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

echo "[LIBRARY] Deploying to container: $CONTAINER"

# ── Tool ─────────────────────────────────────────────────────────────────────

TOOL_SRC="$REPO_ROOT/tools/library.py"
TOOL_DST_PYTHON="/a0/python/tools/library.py"
TOOL_DST_PROFILE="/a0/usr/agents/agent0/tools/library.py"

if [ -f "$TOOL_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/tools
  _exec "$CONTAINER" mkdir -p /a0/usr/agents/agent0/tools
  docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DST_PYTHON"
  docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DST_PROFILE"
  _exec "$CONTAINER" bash -c "rm -rf /a0/python/tools/__pycache__" 2>/dev/null || true
  _exec "$CONTAINER" bash -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$TOOL_DST_PYTHON' && echo '[LIBRARY] tools/library.py OK'"
  echo "[LIBRARY] tools/library.py deployed (python + profile paths)."
else
  echo "[LIBRARY] WARNING: $TOOL_SRC not found — skipped."
fi

# ── Extension ─────────────────────────────────────────────────────────────────

EXT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_17_library_catalog.py"
EXT_DST="/a0/usr/agents/agent0/extensions/before_main_llm_call/_17_library_catalog.py"
EXT_PYCACHE="/a0/usr/agents/agent0/extensions/before_main_llm_call/__pycache__"

if [ -f "$EXT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/agents/agent0/extensions/before_main_llm_call
  docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$EXT_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$EXT_DST' && echo '[LIBRARY] _17_library_catalog.py OK'"
  echo "[LIBRARY] extensions/before_main_llm_call/_17_library_catalog.py deployed."
else
  echo "[LIBRARY] WARNING: $EXT_SRC not found — skipped."
fi

# ── Persistent storage directories ───────────────────────────────────────────

_exec "$CONTAINER" mkdir -p /a0/usr/library/docs
_exec "$CONTAINER" bash -c \
  "[ -f /a0/usr/library/catalog.json ] || echo '{\"version\":\"1.0\",\"documents\":[]}' > /a0/usr/library/catalog.json"
echo "[LIBRARY] Storage directories ready (/a0/usr/library/, /a0/usr/library/docs/)."

# ── Verify tool names resolve ────────────────────────────────────────────────

_exec "$CONTAINER" bash -c "
/opt/venv-a0/bin/python3 -c \"
import sys; sys.path.insert(0, '/a0'); sys.path.insert(0, '/a0/python')
from tools.library import LibraryAdd, LibraryList, LibrarySearch, LibraryRemove
print('[LIBRARY] All 4 tool classes import OK')
\"" 2>&1 | grep -E "OK|Error|Traceback" || true

echo "[LIBRARY] Done. Send a message to load the extension, then use library_add to ingest documents."
