#!/usr/bin/env bash
# install_write_guard.sh
# Deploy Write Guard + Write Validator to the active container.
#
# Installs the paired _25_write_guard (tool_execute_before) and
# _26_write_validator (tool_execute_after) extensions.
#
# Usage: ./scripts/install_write_guard.sh [container_name]
# Default container: exocortex_v16

set -e

CONTAINER="${1:-exocortex_v16}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

GUARD_SRC="$REPO_ROOT/extensions/tool_execute_before/_25_write_guard.py"
VALIDATOR_SRC="$REPO_ROOT/extensions/tool_execute_after/_26_write_validator.py"

# Profile path (persistent across container updates — highest priority)
PROFILE_BEFORE="/a0/usr/agents/agent0/extensions/tool_execute_before"
PROFILE_AFTER="/a0/usr/agents/agent0/extensions/tool_execute_after"

echo "[WRITE-GUARD] Deploying write validation gate to container: $CONTAINER"

# ── Verify source files ───────────────────────────────────────────────────────
for f in "$GUARD_SRC" "$VALIDATOR_SRC"; do
  if [ ! -f "$f" ]; then
    echo "[WRITE-GUARD] ERROR: Source not found: $f"
    exit 1
  fi
done

# ── Deploy to profile path (A1 subordinate agent) ────────────────────────────
echo "[1/4] Creating profile extension directories..."
docker exec "$CONTAINER" mkdir -p "$PROFILE_BEFORE"
docker exec "$CONTAINER" mkdir -p "$PROFILE_AFTER"

echo "[2/4] Copying extension files..."
docker cp "$GUARD_SRC"     "$CONTAINER:$PROFILE_BEFORE/_25_write_guard.py"
docker cp "$VALIDATOR_SRC" "$CONTAINER:$PROFILE_AFTER/_26_write_validator.py"

# ── Clear pycache ─────────────────────────────────────────────────────────────
echo "[3/4] Clearing pycache..."
docker exec "$CONTAINER" rm -f \
  "$PROFILE_BEFORE/__pycache__/_25_write_guard.cpython-312.pyc" \
  "$PROFILE_AFTER/__pycache__/_26_write_validator.cpython-312.pyc" \
  2>/dev/null || true

# ── Compile check ─────────────────────────────────────────────────────────────
echo "[4/4] Verifying compilation..."
docker exec "$CONTAINER" /opt/venv-a0/bin/python3 -m py_compile \
  "$PROFILE_BEFORE/_25_write_guard.py" && echo "  _25_write_guard.py OK"
docker exec "$CONTAINER" /opt/venv-a0/bin/python3 -m py_compile \
  "$PROFILE_AFTER/_26_write_validator.py" && echo "  _26_write_validator.py OK"

echo ""
echo "[WRITE-GUARD] Done. Extensions active immediately (no restart required)."
echo ""
echo "Verification:"
echo "  Ask the agent to write a Python file with a syntax error."
echo "  Check logs for: [WRITE-VAL] REJECTED"
echo "  Check logs for: [WRITE-GUARD] Backed up:"
