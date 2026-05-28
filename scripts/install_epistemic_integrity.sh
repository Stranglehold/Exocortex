#!/bin/bash
set -e

CONTAINER="${1:-${CONTAINER:-exocortex_v16}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Canonical profile path A0 v1.18 loads from (DEC-030).
PROF_AFTER="/a0/usr/agents/agent0/extensions/python/tool_execute_after"
PROF_MONO="/a0/usr/agents/agent0/extensions/python/monologue_end"
PROFILES_DIR="/a0/usr/Exocortex/eval/model_profiles"

# safe_cp: skip if src == dst (happens in-container when REPO_ROOT == /a0/usr/Exocortex).
# Otherwise docker cp; the install_all.sh shim turns this into local cp when in-container.
safe_cp() {
  local src="$1" dst_path="$2"
  if [ "$src" = "$dst_path" ]; then
    echo "    (skip self-copy: $dst_path already at source location)"
    return 0
  fi
  docker cp "$src" "$CONTAINER:$dst_path"
}

echo "=== Installing Epistemic Integrity Layer ==="

echo "[1/6] Ensuring directories exist..."
docker exec "$CONTAINER" mkdir -p "$PROFILES_DIR" "$PROF_AFTER" "$PROF_MONO"

echo "[2/6] Deploying _25_evidence_ledger_recorder.py (tool_execute_after)..."
safe_cp "$REPO_ROOT/extensions/tool_execute_after/_25_evidence_ledger_recorder.py" \
        "$PROF_AFTER/_25_evidence_ledger_recorder.py"

echo "[3/6] Deploying _25_epistemic_integrity.py (monologue_end)..."
safe_cp "$REPO_ROOT/extensions/monologue_end/_25_epistemic_integrity.py" \
        "$PROF_MONO/_25_epistemic_integrity.py"

echo "[4/6] Deploying model profiles..."
safe_cp "$REPO_ROOT/eval/model_profiles/default.json" \
        "$PROFILES_DIR/default.json"
safe_cp "$REPO_ROOT/eval/model_profiles/qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json" \
        "$PROFILES_DIR/qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json"

echo "[5/6] Clearing pycache..."
docker exec "$CONTAINER" rm -rf "$PROF_AFTER/__pycache__/" "$PROF_MONO/__pycache__/"

echo "[6/6] Verifying compilation..."
docker exec "$CONTAINER" /opt/venv-a0/bin/python3 -m py_compile \
    "$PROF_AFTER/_25_evidence_ledger_recorder.py"
docker exec "$CONTAINER" /opt/venv-a0/bin/python3 -m py_compile \
    "$PROF_MONO/_25_epistemic_integrity.py"

echo ""
echo "=== Epistemic Integrity Layer Installed ==="
echo "Restart the container to activate."
echo ""
echo "Verify with:"
echo "  docker logs $CONTAINER 2>&1 | grep -E '\\[EI\\]|\\[EPISTEMIC'"
echo ""
echo "Test trigger: ask the agent a question that requires financial data"
echo "without querying any external source first. EI should flag ungrounded claims."
