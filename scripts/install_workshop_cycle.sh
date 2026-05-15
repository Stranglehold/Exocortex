#!/bin/bash
# install_workshop_cycle.sh — Deploy workshop cycle infrastructure to a container
# Run inside the container: bash /tmp/install_workshop_cycle.sh
#
# Creates /a0/usr/workdir/self-improvement/ with:
#   - regression_monitor.sh  (copied from Exocortex repo in container)
#   - wiki_integrity_check.sh
#   - monitoring_checklist.json
#   - regression_baseline.json  (auto-detected from current extension state)
#   - journal.jsonl  (initialized if not present; migrated if at old path)
#   - backups/, checkpoints/, work-logs/  (directories)
#
# Safe to re-run: never overwrites existing journal or baselines unless --reset is passed.

set -e

EXOCORTEX="/a0/usr/Exocortex"
SELF_IMPROVEMENT="$EXOCORTEX/self-improvement"
WORKDIR="/a0/usr/workdir/self-improvement"
EXT_DIR="$EXOCORTEX/extensions"
BST_FILE="$EXT_DIR/before_main_llm_call/_11_belief_state_tracker.py"
RESET=${1:-""}

echo "[WORKSHOP-INSTALL] Starting workshop cycle install..."

# ── 1. Create workdir structure ────────────────────────────────────────────────
mkdir -p "$WORKDIR/backups" "$WORKDIR/checkpoints" "$WORKDIR/work-logs"
echo "[WORKSHOP-INSTALL] Workdir structure: OK"

# ── 2. Copy scripts from Exocortex repo to workdir ────────────────────────────
for script in regression_monitor.sh wiki_integrity_check.sh monitoring_checklist.json; do
    src="$SELF_IMPROVEMENT/$script"
    dst="$WORKDIR/$script"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        chmod +x "$dst" 2>/dev/null || true
        echo "[WORKSHOP-INSTALL] Copied: $script"
    else
        echo "[WORKSHOP-INSTALL] WARNING: $src not found — skipping"
    fi
done

# ── 3. Auto-detect and write baseline config ───────────────────────────────────
BASELINE_JSON="$WORKDIR/regression_baseline.json"

if [ ! -f "$BASELINE_JSON" ] || [ "$RESET" = "--reset" ]; then
    PY_COUNT=$(find "$EXT_DIR" -name '*.py' -type f -not -path '*/backups/*' 2>/dev/null | wc -l | tr -d ' ')
    BST_LINES=$(wc -l < "$BST_FILE" 2>/dev/null | tr -d ' ' || echo "0")

    python3 -c "
import json
baseline = {
    'py_count': $PY_COUNT,
    'bst_lines': $BST_LINES,
    'note': 'Auto-detected at install time. Update manually if baselines change deliberately.'
}
with open('$BASELINE_JSON', 'w') as f:
    json.dump(baseline, f, indent=2)
"
    echo "[WORKSHOP-INSTALL] Baseline written: py_count=$PY_COUNT, bst_lines=$BST_LINES"
else
    EXISTING_PY=$(python3 -c "import json; print(json.load(open('$BASELINE_JSON'))['py_count'])" 2>/dev/null || echo "?")
    EXISTING_BST=$(python3 -c "import json; print(json.load(open('$BASELINE_JSON'))['bst_lines'])" 2>/dev/null || echo "?")
    echo "[WORKSHOP-INSTALL] Baseline already set: py_count=$EXISTING_PY, bst_lines=$EXISTING_BST (use --reset to redetect)"
fi

# ── 4. Initialize or migrate journal ──────────────────────────────────────────
NEW_JOURNAL="$WORKDIR/journal.jsonl"
OLD_JOURNAL="$SELF_IMPROVEMENT/journal.jsonl"

if [ ! -f "$NEW_JOURNAL" ]; then
    if [ -f "$OLD_JOURNAL" ]; then
        cp "$OLD_JOURNAL" "$NEW_JOURNAL"
        echo "[WORKSHOP-INSTALL] Journal migrated from $OLD_JOURNAL to $NEW_JOURNAL"
    else
        touch "$NEW_JOURNAL"
        echo "[WORKSHOP-INSTALL] Journal initialized: $NEW_JOURNAL"
    fi
else
    LINES=$(wc -l < "$NEW_JOURNAL" | tr -d ' ')
    echo "[WORKSHOP-INSTALL] Journal already exists: $LINES entries"
fi

# ── 5. Run smoke test ─────────────────────────────────────────────────────────
echo "[WORKSHOP-INSTALL] Running regression monitor smoke test..."
OUTPUT=$(bash "$WORKDIR/regression_monitor.sh" 2>&1)
echo "[WORKSHOP-INSTALL] Monitor result: $OUTPUT"

echo "[WORKSHOP-INSTALL] Done."
