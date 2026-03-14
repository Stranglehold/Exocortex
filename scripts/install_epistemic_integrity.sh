#!/bin/bash
set -e

CONTAINER="${1:-agent-zero}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Installing Epistemic Integrity Layer ==="

# Create model profile directory in container if it doesn't exist
echo "[1/6] Ensuring model profile directory exists..."
docker exec "$CONTAINER" mkdir -p /a0/usr/Exocortex/eval/model_profiles

# Deploy evidence ledger recorder (tool_execute_after hook)
echo "[2/6] Deploying _25_evidence_ledger_recorder.py (tool_execute_after)..."
docker cp "$REPO_ROOT/extensions/tool_execute_after/_25_evidence_ledger_recorder.py" \
    "$CONTAINER:/a0/python/extensions/tool_execute_after/_25_evidence_ledger_recorder.py"

# Deploy main EI extension (monologue_end hook)
echo "[3/6] Deploying _25_epistemic_integrity.py (monologue_end)..."
docker cp "$REPO_ROOT/extensions/monologue_end/_25_epistemic_integrity.py" \
    "$CONTAINER:/a0/python/extensions/monologue_end/_25_epistemic_integrity.py"

# Deploy model profiles with temporal sections
echo "[4/6] Deploying model profiles..."
docker cp "$REPO_ROOT/eval/model_profiles/default.json" \
    "$CONTAINER:/a0/usr/Exocortex/eval/model_profiles/default.json"
docker cp "$REPO_ROOT/eval/model_profiles/qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json" \
    "$CONTAINER:/a0/usr/Exocortex/eval/model_profiles/qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json"

# Clear pycache for affected hook directories
echo "[5/6] Clearing pycache..."
docker exec "$CONTAINER" rm -rf /a0/python/extensions/tool_execute_after/__pycache__/
docker exec "$CONTAINER" rm -rf /a0/python/extensions/monologue_end/__pycache__/

# Verify compilation
echo "[6/6] Verifying compilation..."
docker exec "$CONTAINER" python3 -m py_compile \
    /a0/python/extensions/tool_execute_after/_25_evidence_ledger_recorder.py
docker exec "$CONTAINER" python3 -m py_compile \
    /a0/python/extensions/monologue_end/_25_epistemic_integrity.py

echo ""
echo "=== Epistemic Integrity Layer Installed ==="
echo "Restart the container to activate."
echo ""
echo "Verify with:"
echo "  docker logs $CONTAINER 2>&1 | grep -E '\\[EI\\]|\\[EPISTEMIC'"
echo ""
echo "Test trigger: ask the agent a question that requires financial data"
echo "without querying any external source first. EI should flag ungrounded claims."
