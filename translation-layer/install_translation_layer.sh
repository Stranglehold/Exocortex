#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYER_DIR="$SCRIPT_DIR"
# ── STRIPPED 2026-08-19 (Tier 1.1): wrote to a dead root; the plugin walk deploys this ──
# The BST and its taxonomy ship in the plugin tree. This variable is retained
# only because later lines reference it inside disabled blocks.
TARGET_DIR="/a0/python/extensions/before_main_llm_call"   # DEAD ROOT — do not write

echo "================================================================"
echo "Installing Translation Layer (Belief State Tracker)"
echo "================================================================"

# Verify source files exist
if [[ ! -f "$LAYER_DIR/_11_belief_state_tracker.py" ]]; then
    echo "ERROR: _11_belief_state_tracker.py not found in $LAYER_DIR"
    exit 1
fi

if [[ ! -f "$LAYER_DIR/slot_taxonomy.json" ]]; then
    echo "ERROR: slot_taxonomy.json not found in $LAYER_DIR"
    exit 1
fi

# ── STRIPPED 2026-08-19 (Tier 1.1) ──────────────────────────────────────────
# This deployed _11_belief_state_tracker.py and slot_taxonomy.json to
# /a0/python/extensions/before_main_llm_call — a root that does not exist in stock
# A0 v2.9 (the old pipeline created it) and that nothing loads. Both files ship in
# plugins/_exocortex/extensions/python/before_main_llm_call/ and are deployed by
# scripts/install_exocortex_plugin.sh.
#
# The prompt content this script also installs is OUTSIDE the plugin and is kept
# above, untouched.
if false; then
    mkdir -p "$TARGET_DIR"
    timestamp=$(date +%Y%m%d_%H%M%S)
    for f in _11_belief_state_tracker.py slot_taxonomy.json; do
        [ -f "$TARGET_DIR/$f" ] && cp "$TARGET_DIR/$f" "$TARGET_DIR/$f.backup_$timestamp"
        cp "$LAYER_DIR/$f" "$TARGET_DIR/"
        chmod 644 "$TARGET_DIR/$f"
    done
    rm -rf "$TARGET_DIR/__pycache__"
fi

echo ""
echo "✓ Translation layer: BST + taxonomy deployed by the plugin walk"
echo ""
echo "  - _11_belief_state_tracker.py"
echo "  - slot_taxonomy.json"
echo ""
echo "Next: Start a fresh agent chat and send an ambiguous message like"
echo "      'refactor agent.py' to verify BST is running."
echo "      Check logs for [BST] lines."
echo ""
echo "================================================================"
