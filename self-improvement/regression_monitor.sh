#!/bin/bash
# Exocortex Regression Monitor — runs every 4 hours
# Logs to journal.jsonl. Reports anomalies only.
# Baselines are stored in regression_baseline.json (written by install_workshop_cycle.sh).

WORKDIR="/a0/usr/workdir/self-improvement"
JOURNAL="$WORKDIR/journal.jsonl"
BASELINE_JSON="$WORKDIR/regression_baseline.json"
EXT_DIR="/a0/usr/Exocortex/extensions/"
BST_FILE="$EXT_DIR/before_main_llm_call/_11_belief_state_tracker.py"
WIKI_INDEX="/a0/usr/Exocortex/wiki/index.md"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
ANOMALIES=""

# Load baselines from config (set by install_workshop_cycle.sh on first install)
BASELINE_BST=$(python3 -c "import json; d=json.load(open('$BASELINE_JSON')); print(d.get('bst_lines', 1702))" 2>/dev/null || echo "1702")
BASELINE_PY=$(python3 -c "import json; d=json.load(open('$BASELINE_JSON')); print(d.get('py_count', 60))" 2>/dev/null || echo "60")

# Check 1: BST line count deviation from baseline
BST_LINES=$(wc -l < "$BST_FILE" 2>/dev/null || echo "MISSING")
if [ "$BST_LINES" != "$BASELINE_BST" ]; then
    ANOMALIES="${ANOMALIES}BST_LINE_COUNT_DEVIATION: expected=${BASELINE_BST} actual=${BST_LINES}; "
fi

# Check 2: New .py file count change (excludes backups/)
PY_COUNT=$(find "$EXT_DIR" -name '*.py' -type f -not -path '*/backups/*' 2>/dev/null | wc -l)
if [ "$PY_COUNT" != "$BASELINE_PY" ]; then
    ANOMALIES="${ANOMALIES}PY_COUNT_CHANGE: expected=${BASELINE_PY} actual=${PY_COUNT}; "
fi

# Check 3: Syntax errors in extensions
SYNTAX_ERRORS=$(python3 -c "
import py_compile, os, sys
count = 0
for root, dirs, files in os.walk('$EXT_DIR'):
    dirs[:] = [d for d in dirs if d != 'backups']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            count += 1
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                print(str(e))
sys.exit(0)
" 2>/dev/null | wc -l)
if [ "$SYNTAX_ERRORS" != "0" ]; then
    ANOMALIES="${ANOMALIES}SYNTAX_ERRORS: count=${SYNTAX_ERRORS}; "
fi

# Check 4: Wiki TODO entries appear (baseline=0)
TODO_COUNT=$(grep -ci 'TODO' "$WIKI_INDEX" 2>/dev/null || true)
TODO_COUNT=${TODO_COUNT:-0}
TODO_COUNT=$(echo "$TODO_COUNT" | tr -d '[:space:]')
if [ "$TODO_COUNT" != "0" ]; then
    ANOMALIES="${ANOMALIES}WIKI_TODO_APPEARED: count=${TODO_COUNT}; "
fi

# Check 5: .py modifications since last journal entry
MODIFIED_FILES=$(find "$EXT_DIR" -name '*.py' -type f -not -path '*/backups/*' -newer "$JOURNAL" 2>/dev/null | wc -l)
if [ "$MODIFIED_FILES" != "0" ]; then
    MOD_LIST=$(find "$EXT_DIR" -name '*.py' -type f -not -path '*/backups/*' -newer "$JOURNAL" 2>/dev/null | tr '\n' ', ')
    ANOMALIES="${ANOMALIES}PY_MODIFICATIONS_SINCE_LAST_AUDIT: count=${MODIFIED_FILES} files=[${MOD_LIST}]; "
fi

# Log result
if [ -z "$ANOMALIES" ]; then
    STATUS="HEALTHY"
    echo "{\"timestamp\": \"${TIMESTAMP}\", \"task\": \"regression_monitor_4h\", \"status\": \"HEALTHY\", \"checks\": {\"bst_lines\": ${BST_LINES}, \"py_count\": ${PY_COUNT}, \"syntax_errors\": 0, \"wiki_todos\": 0, \"modifications_since_last_audit\": 0}}" >> "$JOURNAL"
else
    STATUS="ANOMALY"
    echo "{\"timestamp\": \"${TIMESTAMP}\", \"task\": \"regression_monitor_4h\", \"status\": \"ANOMALY\", \"anomalies\": \"${ANOMALIES}\", \"checks\": {\"bst_lines\": ${BST_LINES}, \"py_count\": ${PY_COUNT}, \"syntax_errors\": ${SYNTAX_ERRORS}, \"wiki_todos\": ${TODO_COUNT}, \"modifications_since_last_audit\": ${MODIFIED_FILES}}}" >> "$JOURNAL"
fi

echo "${TIMESTAMP} | ${STATUS} | BST=${BST_LINES}/${BASELINE_BST} PY=${PY_COUNT}/${BASELINE_PY} SYNERR=${SYNTAX_ERRORS} TODO=${TODO_COUNT} MODS=${MODIFIED_FILES} | ${ANOMALIES:-no anomalies}"
