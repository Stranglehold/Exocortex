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
# -- REPOINTED 2026-08-19 (Tier 1.1) -----------------------------------------
# Was /a0/usr/plugins/exocortex (NO underscore) - the wrong plugin name, so every
# webui asset landed in a directory A0 never reads. These files also ship in the
# plugin tree and are deployed by the walk; repointing keeps this script correct
# rather than merely inert.
PLUGIN_WEBUI="/a0/usr/plugins/_exocortex/extensions/webui"
ERRORS=0

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

# ── Container list ────────────────────────────────────────────────────────────

CONTAINERS=()
if [ -f "/.dockerenv" ] || grep -qE "docker|lxc|containerd" /proc/1/cgroup 2>/dev/null; then
    # Running INSIDE a container (install_all.sh shim active). `docker inspect`
    # doesn't exist here, so discovery would fail. The shim intercepts docker
    # cp/exec to local ops, making the container name a label — set it and move on.
    CONTAINERS=("${CONTAINER:-in-container}")
elif [[ -n "${CONTAINER:-}" ]]; then
    # Host-side targeted install — honor the CONTAINER env (install_all exports it).
    # Without this, a single-container install would fan out to prod (v16/v17).
    docker inspect "$CONTAINER" &>/dev/null 2>&1 && CONTAINERS+=("$CONTAINER")
else
    for name in "${CONTAINER_NAME:-}" exocortex_v16 exocortex_v17; do
        [[ -z "$name" ]] && continue
        if docker inspect "$name" &>/dev/null 2>&1; then
            CONTAINERS+=("$name")
        fi
    done
fi

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
        "/a0/usr/skills/auto-generated" \
        "${PLUGIN_WEBUI}/right_canvas_register_surfaces" \
        "${PLUGIN_WEBUI}/right-canvas-panels"
    do
        _exec "${CONTAINER}" mkdir -p "${dir}" 2>/dev/null || true
    done
    echo "  OK    [${CONTAINER}] runtime directories"

    # ── Extension: STRIPPED 2026-08-19 (Tier 1.1) ──
    # EXT_DEST is the DEC-030 profile path, which still LOADS — so writing here
    # produced a SECOND copy of _70_idle_trigger.py alongside the plugin's. It
    # ships in plugins/_exocortex/extensions/python/tool_execute_after/ and is
    # deployed by the walk.
    if false; then
        install_file \
            "${REPO_DIR}/extensions/tool_execute_after/_70_idle_trigger.py" \
            "${EXT_DEST}/_70_idle_trigger.py" \
            "_70_idle_trigger.py" \
            "${CONTAINER}"

        clear_pycache \
            "${EXT_DEST}/__pycache__/_70_idle_trigger.cpython-312.pyc" \
            "${CONTAINER}"
    fi
    echo "  OK    [${CONTAINER}] _70_idle_trigger.py — deployed by the plugin walk"

    # ── Prompt template ──
    # 2026-08-19: this shipped a stale prompt to a path nothing reads.
    #   source — ${REPO_DIR}/prompts/idle_activation.md is stale (1fc58595) against
    #            what is live and in the plugin tree (92e2f034).
    #   dest   — ${EXOCORTEX_DEST}/prompts is the pre-DEC-030 path. It does not exist
    #            on either live container, and the daemon that is ACTUALLY running
    #            (plugins/_exocortex/services/idle_watch.py, spawned by the bootstrap
    #            extension) reads /a0/usr/plugins/_exocortex/prompts/idle_activation.md.
    #            A fresh install left that daemon with no activation prompt while the
    #            installer reported success.
    # Now: current source, installed to BOTH paths. The legacy supervisord variant
    # (services/idle_watch.py -> ${EXOCORTEX_DEST}/idle_watch.py, deployed below) still
    # reads the old path, and whether that variant should exist at all is an open
    # question for Jake/Opus — see the note at the idle_watch.py deploy block. Writing
    # both is non-destructive and leaves neither consumer broken in the meantime.
    install_file \
        "${REPO_DIR}/plugins/_exocortex/prompts/idle_activation.md" \
        "/a0/usr/plugins/_exocortex/prompts/idle_activation.md" \
        "idle_activation.md (plugin path — the live daemon reads this)" \
        "${CONTAINER}"

    install_file \
        "${REPO_DIR}/plugins/_exocortex/prompts/idle_activation.md" \
        "${EXOCORTEX_DEST}/prompts/idle_activation.md" \
        "idle_activation.md (legacy supervisord path)" \
        "${CONTAINER}"

    # ── Cycle bookkeeping: cycle_close.py → BOTH source + workspace runtime ──
    # The agent runs cycle_close.py from the workspace runtime path (idle_activation.md
    # references it explicitly). Without the runtime copy, the verify-before-log gate
    # inside cycle_close.py never reaches the agent. Principle: everything installs here.
    _exec "${CONTAINER}" mkdir -p /a0/usr/workdir/workspace/self-improvement 2>/dev/null || true
    install_file \
        "${REPO_DIR}/self-improvement/cycle_close.py" \
        "${EXOCORTEX_DEST}/self-improvement/cycle_close.py" \
        "cycle_close.py (source)" \
        "${CONTAINER}"
    install_file \
        "${REPO_DIR}/self-improvement/cycle_close.py" \
        "/a0/usr/workdir/workspace/self-improvement/cycle_close.py" \
        "cycle_close.py (runtime)" \
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

    # ── Right-canvas tab: EXO·OPS diegetic ops console ──
    # v1.20 canvas contract: thin .right-canvas-surface-panel wrapper (NO x-data)
    # delegates to a nested <x-component> holding the real UI. The wrapper goes to
    # right-canvas-panels/; the inner content goes to the PLUGIN webui root (served
    # at /plugins/exocortex/webui/). Mirrors the working Intelligence panel.
    install_file \
        "${REPO_DIR}/patches/webui/right_canvas_register_surfaces/register-exo-ops.js" \
        "${PLUGIN_WEBUI}/right_canvas_register_surfaces/register-exo-ops.js" \
        "register-exo-ops.js" \
        "${CONTAINER}"
    install_file \
        "${REPO_DIR}/patches/webui/right-canvas-panels/exo-ops-panel.html" \
        "${PLUGIN_WEBUI}/right-canvas-panels/exo-ops-panel.html" \
        "exo-ops-panel.html" \
        "${CONTAINER}"
    install_file \
        "${REPO_DIR}/patches/webui/exo-ops-content.html" \
        "/a0/usr/plugins/_exocortex/webui/exo-ops-content.html" \
        "exo-ops-content.html" \
        "${CONTAINER}"

    # ── Idle-watch daemon (the supervisord-managed firing engine) ──
    # Repo source of truth: services/idle_watch.py. Deployed to the persistent
    # Exocortex dir.
    #
    # !! OPEN QUESTION FOR JAKE/OPUS — 2026-08-19, verified but NOT changed !!
    # The comment below used to say "this is the daemon that actually runs the idle
    # cycles." On the live containers it is not. There are two idle_watch.py copies:
    #   services/idle_watch.py                   e037ee8b  <- this block; reads the
    #                                                         pre-DEC-030 prompt path
    #   plugins/_exocortex/services/idle_watch.py 0a1df4b6  <- matches what is LIVE on
    #                                                         VekV2, spawned by the
    #                                                         _00_idle_watch bootstrap
    # So a fresh install deploys the older daemon and points supervisord at it, while
    # the plugin bootstrap spawns the newer one. Either two daemons can race, or the
    # supervisord entry is dead weight. Deciding which is correct changes how the
    # agents' autonomous cycles launch, so it is flagged rather than fixed here.
    # (The activation prompt is now written to both paths above so neither breaks.)
    install_file \
        "${REPO_DIR}/services/idle_watch.py" \
        "${EXOCORTEX_DEST}/idle_watch.py" \
        "idle_watch.py (supervisord daemon)" \
        "${CONTAINER}"

    # ── Supervisord program entry for idle_watch ──
    # /etc/supervisor/conf.d/supervisord.conf is a BASE-image path (wiped on A0
    # update) — re-applied here on every install so the daemon is always wired.
    # Idempotent: only appended if [program:idle_watch] is absent.
    _exec "${CONTAINER}" python3 - <<'PYEOF'
import os
conf = "/etc/supervisor/conf.d/supervisord.conf"
block = """
[program:idle_watch]
command=/opt/venv-a0/bin/python3 -u /a0/usr/Exocortex/idle_watch.py
environment=
user=root
stopwaitsecs=5
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startretries=10
stopasgroup=true
killasgroup=true
"""
try:
    txt = open(conf).read() if os.path.exists(conf) else ""
    if "[program:idle_watch]" not in txt:
        with open(conf, "a") as f:
            f.write(block)
        print("  OK    supervisord [program:idle_watch] added")
    else:
        print("  OK    supervisord [program:idle_watch] already present")
except Exception as e:
    print(f"  ERR   supervisord entry failed: {e}")
PYEOF

    # Reload supervisord so the daemon is live (no-op if already running).
    _exec "${CONTAINER}" sh -c 'supervisorctl reread >/dev/null 2>&1; supervisorctl update >/dev/null 2>&1; echo "  OK    supervisorctl reread/update"' || echo "  ~ supervisorctl reload skipped (run manually if needed)"

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
    "workshop_field_ratio": "3:1",
    "cache_warmer_enabled": False,
    "cache_keepalive_interval_seconds": 600,
    "cache_warm_timeout_seconds": 900
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
