#!/usr/bin/env bash
# install_stack_status.sh
# Deploy the Stack Status introspection tool to the active container.
#
# Usage: ./scripts/install_stack_status.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL_SRC="$REPO_ROOT/tools/stack_status.py"
TOOL_DST="/a0/python/tools/stack_status.py"
PYCACHE="/a0/python/tools/__pycache__"

echo "[STACK] Deploying Stack Status tool to container: $CONTAINER"

if [ ! -f "$TOOL_SRC" ]; then
  echo "[STACK] ERROR: Source file not found: $TOOL_SRC"
  exit 1
fi

docker exec "$CONTAINER" mkdir -p /a0/python/tools
docker cp "$TOOL_SRC" "$CONTAINER:$TOOL_DST"
echo "[STACK] Tool deployed."

docker exec "$CONTAINER" bash -c "rm -rf '$PYCACHE'" 2>/dev/null || true
echo "[STACK] pycache cleared."

docker exec "$CONTAINER" bash -c "python3 -m py_compile '$TOOL_DST' && echo '[STACK] Compilation OK'"

echo "[STACK] Done. Invoke with: stack_status tool in agent conversation."
