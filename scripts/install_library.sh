#!/usr/bin/env bash
# install_library.sh  v2.0
# Deploy the Exocortex Document Library (v2: collection tree + two-stage search).
#
# Deploys:
#   tools/library.py
#     → /a0/python/tools/library.py
#     → /a0/usr/agents/agent0/tools/library.py  (profile path, DEC-030)
#
#   extensions/before_main_llm_call/_17_library_catalog.py
#     → /a0/usr/agents/agent0/extensions/python/before_main_llm_call/_17_library_catalog.py
#
#   scripts/library_batch_ingest.py
#     → /a0/usr/Exocortex/library_batch_ingest.py  (runnable inside container)
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

echo "[LIBRARY] Deploying v2.0 to container: $CONTAINER"

# ── Python dependencies ───────────────────────────────────────────────────────

PYTHON="/opt/venv-a0/bin/python3"

echo "[LIBRARY] Installing Python dependencies..."
_exec "$CONTAINER" "$PYTHON" -m pip install --quiet \
  langchain-text-splitters \
  simpleeval
echo "[LIBRARY] Dependencies installed."

# ── Tool ──────────────────────────────────────────────────────────────────────

TOOL_SRC="$REPO_ROOT/tools/library.py"
TOOL_DST_PYTHON="/a0/python/tools/library.py"
TOOL_DST_PROFILE="/a0/usr/agents/agent0/tools/library.py"

if [ -f "$TOOL_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/python/tools
  _exec "$CONTAINER" mkdir -p /a0/usr/agents/agent0/tools
  docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DST_PYTHON"
  docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DST_PROFILE"
  _exec "$CONTAINER" bash -c "rm -rf /a0/python/tools/__pycache__ /a0/usr/agents/agent0/tools/__pycache__" 2>/dev/null || true
  _exec "$CONTAINER" bash -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$TOOL_DST_PYTHON' && echo '[LIBRARY] tools/library.py OK'"
  echo "[LIBRARY] tools/library.py deployed (python + profile paths)."
else
  echo "[LIBRARY] WARNING: $TOOL_SRC not found — skipped."
fi

# ── Extension ─────────────────────────────────────────────────────────────────

EXT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_17_library_catalog.py"
EXT_DST="/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_17_library_catalog.py"
EXT_PYCACHE="/a0/usr/agents/agent0/extensions/python/before_main_llm_call/__pycache__"

if [ -f "$EXT_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/agents/agent0/extensions/python/before_main_llm_call
  docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
  _exec "$CONTAINER" bash -c "rm -rf '$EXT_PYCACHE'" 2>/dev/null || true
  _exec "$CONTAINER" bash -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$EXT_DST' && echo '[LIBRARY] _17_library_catalog.py OK'"
  echo "[LIBRARY] _17_library_catalog.py deployed."
else
  echo "[LIBRARY] WARNING: $EXT_SRC not found — skipped."
fi

# ── Batch ingest script ───────────────────────────────────────────────────────

BATCH_SRC="$REPO_ROOT/scripts/library_batch_ingest.py"
BATCH_DST="/a0/usr/Exocortex/library_batch_ingest.py"

if [ -f "$BATCH_SRC" ]; then
  _exec "$CONTAINER" mkdir -p /a0/usr/Exocortex
  docker cp "$BATCH_SRC" "$CONTAINER:$BATCH_DST"
  _exec "$CONTAINER" bash -c \
    "/opt/venv-a0/bin/python3 -m py_compile '$BATCH_DST' && echo '[LIBRARY] library_batch_ingest.py OK'"
  echo "[LIBRARY] library_batch_ingest.py deployed to /a0/usr/Exocortex/."
else
  echo "[LIBRARY] WARNING: $BATCH_SRC not found — skipped."
fi

# ── Persistent storage directories ───────────────────────────────────────────
# catalog + docs live under workdir (Docker volume, survives container updates)
# FAISS lives under /a0/usr/memory/library/ (Agent Zero memory volume)

_exec "$CONTAINER" mkdir -p /a0/usr/workdir/library/docs
# Initialize v2 catalog if none exists; migrate v1 on first library_add
_exec "$CONTAINER" bash -c \
  "[ -f /a0/usr/workdir/library/catalog.json ] || printf '{\"version\":\"2.0\",\"collections\":{},\"documents\":[]}' > /a0/usr/workdir/library/catalog.json"
echo "[LIBRARY] Storage directories ready (/a0/usr/workdir/library/, /a0/usr/workdir/library/docs/)."

# ── Verify tool classes import ───────────────────────────────────────────────

_exec "$CONTAINER" bash -c "
/opt/venv-a0/bin/python3 -c \"
import sys; sys.path.insert(0, '/a0'); sys.path.insert(0, '/a0/python')
from tools.library import LibraryAdd, LibraryList, LibrarySearch, LibraryRemove, LibraryCollections
print('[LIBRARY] All 5 tool classes import OK')
\"" 2>&1 | grep -E "OK|Error|Traceback" || true

echo ""
echo "[LIBRARY] Deploy complete."
echo "  Tools   : library_add, library_list, library_search, library_remove, library_collections"
echo "  Catalog : /a0/usr/workdir/library/catalog.json  (workdir — persistent)"
echo "  FAISS   : /a0/usr/memory/library/               (memory volume — persistent)"
echo "  Docs    : /a0/usr/workdir/library/docs/"
echo "  Batch   : /opt/venv-a0/bin/python3 /a0/usr/Exocortex/library_batch_ingest.py <dir> --direct"
echo ""
echo "  Send a message in Agent Zero to load, then:"
echo "    library_add path=\"/a0/usr/workdir/book.pdf\"   — single book"
echo "    python /a0/usr/Exocortex/library_batch_ingest.py /a0/usr/workdir/books --direct"
