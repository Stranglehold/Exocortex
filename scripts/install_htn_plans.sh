#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET="/a0/python/extensions/before_main_llm_call"

echo "[HTN] Installing Plan Selector..."
cp "$REPO_ROOT/extensions/before_main_llm_call/_15_htn_plan_selector.py" "$TARGET/_15_htn_plan_selector.py"
echo "  Installed _15_htn_plan_selector.py"

cp "$REPO_ROOT/extensions/before_main_llm_call/htn_plan_library.json" "$TARGET/htn_plan_library.json"
echo "  Installed htn_plan_library.json"

# Clear pycache
rm -rf "$TARGET/__pycache__"
echo "  Cleared __pycache__"

echo "[HTN] Plan Templates installed."
