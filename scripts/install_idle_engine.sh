#!/usr/bin/env bash
# ━━━ Idle Time Engine — Install ━━━
# Deploys the idle-time engine to both Agent Zero containers.
#
# Deploys:
#   _70_idle_trigger.py     → profile extension path (tool_execute_after)
#   idle_activation.md      → /a0/usr/Exocortex/prompts/
#   interests.md            → /a0/usr/Exocortex/   (if not already present)
#   config.json update      → merges idle_time_engine section
#   office_feed.py          → /a0/api/
#   idle_control.py         → /a0/api/
#   office.html             → /a0/webui/
#   register-workshop.js    → exocortex plugin right_canvas_register_surfaces/
#   workshop-panel.html     → exocortex plugin right-canvas-panels/
#
# Creates runtime directories:
#   /a0/usr/Exocortex/office/
#   /a0/usr/Exocortex/prompts/
#   /a0/usr/Exocortex/field-reports/
#   /a0/usr/Exocortex/self-improvement/checkpoints/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
EXT_DEST="/a0/usr/agents/agent0/extensions/python/tool_execute_after"
EXOCORTEX_DEST="/a0/usr/Exocortex"
API_DEST="/a0/api"
WEBUI_DEST="/a0/webui"
PLUGIN_WEBUI="/a0/usr/plugins/exocortex/extensions/webui"
ERRORS=0

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

# ── Container list ────────────────────────────────────────────────────────────

CONTAINERS=()
for name in "${CONTAINER_NAME:-}" exocortex_v16 exocortex_v17; do
    [[ -z "$name" ]] && continue
    if docker inspect "$name" &>/dev/null 2>&1; then
        CONTAINERS+=("$name")
    fi
done

if [[ ${#CONTAINERS[@]} -eq 0 ]]; then
    echo "  ERR  No agent zero containers found (exocortex_v16 / exocortex_v17)"
    exit 1
fi

# Deduplicate
IFS=" " read -r -a CONTAINERS <<< "$(echo "${CONTAINERS[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' ')"

echo ""
echo "━━━ Idle Time Engine — Install ━━━"
echo "  Source     : ${REPO_DIR}"
echo "  Containers : ${CONTAINERS[*]}"
echo ""

# ── Helper functions ──────────────────────────────────────────────────────────

install_file() {
    local src="$1" dest="$2" label="${3:-$(basename "$1")}" container="$4"
    if [[ ! -f "$src" ]]; then
        echo "  SKIP  ${label} (not found at ${src})"
        return 0
    fi
    local src_real dest_real
    src_real="$(realpath "$src" 2>/dev/null || echo "$src")"
    dest_real="$(realpath "$dest" 2>/dev/null || echo "$dest")"
    if [[ "$src_real" == "$dest_real" ]]; then
        echo "  OK    ${label} (already in place)"
        return 0
    fi
    if docker cp "${src}" "${container}:${dest}" 2>/dev/null; then
        echo "  OK    [${container}] ${label} → ${dest}"
    else
        echo "  ERR   [${container}] ${label} — deploy failed"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

install_file_if_missing() {
    local src="$1" dest="$2" label="${3:-$(basename "$1")}" container="$4"
    if [[ ! -f "$src" ]]; then
        echo "  SKIP  ${label} (not found at ${src})"
        return 0
    fi
    if _exec "${container}" test -f "${dest}" 2>/dev/null; then
        echo "  OK    [${container}] ${label} (already present — skipping)"
        return 0
    fi
    if docker cp "${src}" "${container}:${dest}" 2>/dev/null; then
        echo "  OK    [${container}] ${label} → ${dest} (initial deploy)"
    else
        echo "  ERR   [${container}] ${label} — deploy failed"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

clear_pycache() {
    local pyc="$1" container="$2"
    _exec "${container}" rm -f "${pyc}" 2>/dev/null || true
}

# ── Per-container deployment ──────────────────────────────────────────────────

py_check() {
    local f="$1"
    [[ ! -f "$f" ]] && { echo "  SKIP  $(basename "$f") syntax check (not found)"; return 0; }
    python3 -m py_compile "$f" && \
        echo "  OK    $(basename "$f") syntax check" || \
        { echo "  ERR   $(basename "$f") syntax check failed"; ERRORS=$((ERRORS + 1)); }
}

# Local syntax check before any deployment
echo "  Syntax checks:"
if command -v python3 &>/dev/null; then
    py_check "${REPO_DIR}/extensions/tool_execute_after/_70_idle_trigger.py"
    py_check "${REPO_DIR}/patches/api/office_feed.py"
    py_check "${REPO_DIR}/patches/api/idle_control.py"
else
    echo "  SKIP  python3 not available locally"
fi
echo ""

for CONTAINER in "${CONTAINERS[@]}"; do
    echo "  ── Container: ${CONTAINER} ──"

    # Create runtime directories
    for dir in \
        "${EXOCORTEX_DEST}/office" \
        "${EXOCORTEX_DEST}/prompts" \
        "${EXOCORTEX_DEST}/field-reports" \
        "${EXOCORTEX_DEST}/self-improvement" \
        "${EXOCORTEX_DEST}/self-improvement/checkpoints" \
        "${PLUGIN_WEBUI}/right_canvas_register_surfaces" \
        "${PLUGIN_WEBUI}/right-canvas-panels"
    do
        _exec "${CONTAINER}" mkdir -p "${dir}" 2>/dev/null || true
    done
    echo "  OK    [${CONTAINER}] runtime directories"

    # ── Extension ──
    install_file \
        "${REPO_DIR}/extensions/tool_execute_after/_70_idle_trigger.py" \
        "${EXT_DEST}/_70_idle_trigger.py" \
        "_70_idle_trigger.py" \
        "${CONTAINER}"

    clear_pycache \
        "${EXT_DEST}/__pycache__/_70_idle_trigger.cpython-312.pyc" \
        "${CONTAINER}"

    # ── Prompt template ──
    install_file \
        "${REPO_DIR}/prompts/idle_activation.md" \
        "${EXOCORTEX_DEST}/prompts/idle_activation.md" \
        "idle_activation.md" \
        "${CONTAINER}"

    # ── interests.md (if not present — user edits should survive reinstall) ──
    install_file_if_missing \
        "${REPO_DIR}/interests.md" \
        "${EXOCORTEX_DEST}/interests.md" \
        "interests.md" \
        "${CONTAINER}"

    # ── API handler ──
    install_file \
        "${REPO_DIR}/patches/api/office_feed.py" \
        "${API_DEST}/office_feed.py" \
        "office_feed.py" \
        "${CONTAINER}"

    # ── Control API handler ──
    install_file \
        "${REPO_DIR}/patches/api/idle_control.py" \
        "${API_DEST}/idle_control.py" \
        "idle_control.py" \
        "${CONTAINER}"

    # ── Office panel HTML ──
    install_file \
        "${REPO_DIR}/patches/webui/office.html" \
        "${WEBUI_DEST}/office.html" \
        "office.html" \
        "${CONTAINER}"

    # ── Right-canvas tab: surface registrar ──
    install_file \
        "${REPO_DIR}/patches/webui/right_canvas_register_surfaces/register-workshop.js" \
        "${PLUGIN_WEBUI}/right_canvas_register_surfaces/register-workshop.js" \
        "register-workshop.js" \
        "${CONTAINER}"

    # ── Right-canvas tab: panel HTML ──
    install_file \
        "${REPO_DIR}/patches/webui/right-canvas-panels/workshop-panel.html" \
        "${PLUGIN_WEBUI}/right-canvas-panels/workshop-panel.html" \
        "workshop-panel.html" \
        "${CONTAINER}"

    # ── config.json: merge idle_time_engine section ──
    # Read-merge-write: only adds the section if it doesn't already exist.
    _exec "${CONTAINER}" python3 - <<'PYEOF'
import json, os, sys
path = "/a0/usr/Exocortex/config.json"
default_section = {
    "enabled": False,
    "idle_threshold_seconds": 1800,
    "cooldown_seconds": 3600,
    "max_steps_per_cycle": 20,
    "workshop_field_ratio": "3:1"
}
try:
    cfg = {}
    if os.path.exists(path):
        with open(path) as f:
            cfg = json.load(f)
    if "idle_time_engine" not in cfg:
        cfg["idle_time_engine"] = default_section
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        print("  OK    config.json — added idle_time_engine section")
    else:
        print("  OK    config.json — idle_time_engine already present")
except Exception as e:
    print(f"  ERR   config.json merge failed: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    # ── Initial office/status.json (if not present) ──
    _exec "${CONTAINER}" python3 - <<'PYEOF'
import json, os
path = "/a0/usr/Exocortex/office/status.json"
if not os.path.exists(path):
    with open(path, "w") as f:
        json.dump({"state": "idle", "label": "Available"}, f)
    print("  OK    office/status.json (initial)")
else:
    print("  OK    office/status.json (already present)")
PYEOF

    # ── Initial office/control.json (if not present) ──
    if ! _exec "${CONTAINER}" test -f "${EXOCORTEX_DEST}/office/control.json" 2>/dev/null; then
        _exec "${CONTAINER}" python3 -c "import json; open('/a0/usr/Exocortex/office/control.json','w').write(json.dumps({'paused_until':0}))" 2>/dev/null || true
        echo "  OK    [${CONTAINER}] office/control.json (created)"
    else
        echo "  OK    [${CONTAINER}] office/control.json (already present)"
    fi

    # ── Initial office/feed.jsonl (if not present) ──
    if ! _exec "${CONTAINER}" test -f "${EXOCORTEX_DEST}/office/feed.jsonl" 2>/dev/null; then
        _exec "${CONTAINER}" touch "${EXOCORTEX_DEST}/office/feed.jsonl" 2>/dev/null || true
        echo "  OK    [${CONTAINER}] office/feed.jsonl (created empty)"
    else
        echo "  OK    [${CONTAINER}] office/feed.jsonl (already present)"
    fi

    echo ""
done

# ── Result ────────────────────────────────────────────────────────────────────

echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo "  Idle-time engine installed successfully."
    echo ""
    echo "  Restart both containers to activate:"
    echo "    docker restart exocortex_v16 exocortex_v17"
    echo ""
    echo "  Office panel (standalone):"
    echo "    http://localhost:<port>/office.html"
    echo ""
    echo "  Office canvas tab:"
    echo "    Open Agent Zero UI → right-canvas → 'Office' tab"
    echo ""
    echo "  Testing (set idle threshold to 2 min):"
    echo "    Edit config.json → idle_time_engine.idle_threshold_seconds: 120"
    echo "    Send any message, wait 3 minutes, verify [IDLE] Monitor started in logs"
    echo ""
    echo "  Default production thresholds:"
    echo "    idle_threshold_seconds: 1800  (30 min)"
    echo "    cooldown_seconds:       3600  (60 min)"
    echo "    workshop_field_ratio:   3:1"
else
    echo "  ${ERRORS} error(s) during install. Review output above."
    exit 1
fi
