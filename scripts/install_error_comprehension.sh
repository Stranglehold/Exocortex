#!/bin/bash
set -e

CONTAINER="${1:-agent-zero}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Installing Error Comprehension Layer ==="

# Deploy new extension
echo "[1/4] Deploying _20_error_comprehension.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_after/_20_error_comprehension.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_after/_20_error_comprehension.py"

# Deploy modified fallback logger
echo "[2/4] Deploying updated _30_tool_fallback_logger.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_after/_30_tool_fallback_logger.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_after/_30_tool_fallback_logger.py"

# Deploy modified fallback advisor
echo "[3/4] Deploying updated _30_tool_fallback_advisor.py..."
docker cp "$REPO_ROOT/extensions/tool_execute_before/_30_tool_fallback_advisor.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_before/_30_tool_fallback_advisor.py"

# Clear pycache
echo "[4/4] Clearing pycache..."
docker exec "$CONTAINER" rm -rf /a0/python/extensions/tool_execute_after/__pycache__/
docker exec "$CONTAINER" rm -rf /a0/python/extensions/tool_execute_before/__pycache__/

echo ""
echo "=== Error Comprehension Layer Installed ==="
echo "Restart the container or wait for next agent loop to activate."
echo ""
echo "Verify with:"
echo "  docker logs $CONTAINER 2>&1 | grep 'ERROR-DX'"
