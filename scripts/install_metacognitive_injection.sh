#!/usr/bin/env bash
# install_metacognitive_injection.sh
# Deploy the Metacognitive Injection layer (_14_) to the active container.
#
# Usage: ./scripts/install_metacognitive_injection.sh [container_name]
# Default container: flamboyant_bell

set -e

CONTAINER="${1:-flamboyant_bell}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXT_SRC="$REPO_ROOT/extensions/before_main_llm_call/_14_metacognitive_injection.py"
EXT_DST="/a0/python/extensions/before_main_llm_call/_14_metacognitive_injection.py"
PYCACHE="/a0/python/extensions/before_main_llm_call/__pycache__"

echo "[META] Deploying Metacognitive Injection to container: $CONTAINER"

# 1. Verify source file exists
if [ ! -f "$EXT_SRC" ]; then
  echo "[META] ERROR: Source file not found: $EXT_SRC"
  exit 1
fi

# 2. Ensure target directory exists in container
docker exec "$CONTAINER" mkdir -p /a0/python/extensions/before_main_llm_call

# 3. Deploy extension
docker cp "$EXT_SRC" "$CONTAINER:$EXT_DST"
echo "[META] Extension deployed."

# 4. Clear pycache
docker exec "$CONTAINER" bash -c "rm -rf '$PYCACHE'" 2>/dev/null || true
echo "[META] pycache cleared."

# 5. Verify compilation
docker exec "$CONTAINER" bash -c "python3 -m py_compile '$EXT_DST' && echo '[META] Compilation OK'"

echo "[META] Done. Extension active on next message loop iteration."
echo "[META] Verify: look for [META] Injected model config note. in container logs."
