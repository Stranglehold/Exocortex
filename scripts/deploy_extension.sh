#!/usr/bin/env bash
# ━━━ deploy_extension.sh — Single-file extension deploy with verification ━━━
#
# Encodes DEC-026 (dual-path discovery) into a tool so muscle memory replaces
# remembering. Catches the recurring "wrong path silently succeeds" failure.
#
# Usage:
#   scripts/deploy_extension.sh <container> <hook_dir> <filename>
#   scripts/deploy_extension.sh --all <hook_dir> <filename>          # both containers
#
# Examples:
#   scripts/deploy_extension.sh exocortex_v16 tool_execute_after _70_idle_trigger.py
#   scripts/deploy_extension.sh --all message_loop_end _50_supervisor_loop.py
#
# What it does:
#   1. Verify source file exists in the expected repo path
#   2. Local syntax check (python3 -m py_compile)
#   3. docker cp to the CORRECT profile path (with the required `python/` segment)
#   4. md5 verification: deployed file matches local file
#   5. Pycache clear
#   6. Orphan scan: warn about any other copies of the same filename in /a0
#      that don't match the active version (DEC-026 dual-path detection)
#
# What it does NOT do:
#   - Restart run_ui (caller's responsibility — extension class cache only
#     flushes on container restart, not just docker cp)
#   - Deploy to multiple hook directories at once (one file, one hook)
#   - Update install_extensions.sh manifest (use full installer for that)

set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────────────────

if [[ $# -lt 3 ]]; then
    cat <<'USAGE'
Usage: deploy_extension.sh <container|--all> <hook_dir> <filename>

Examples:
  deploy_extension.sh exocortex_v16 tool_execute_after _70_idle_trigger.py
  deploy_extension.sh --all message_loop_end _50_supervisor_loop.py
USAGE
    exit 2
fi

TARGET="$1"
HOOK="$2"
FILE="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SRC="${REPO_DIR}/extensions/${HOOK}/${FILE}"

# Profile path is the only path A0 actually loads from for extensions.
# The `python/` segment is required (DEC-026 / playbook CRITICAL PATH LESSON).
DEST="/a0/usr/agents/agent0/extensions/python/${HOOK}/${FILE}"
PYCACHE_GLOB="/a0/usr/agents/agent0/extensions/python/${HOOK}/__pycache__/${FILE%.py}.cpython-*.pyc"

# Prevent Git Bash on Windows from translating Unix paths
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

# ── Container list ────────────────────────────────────────────────────────────

CONTAINERS=()
if [[ "$TARGET" == "--all" ]]; then
    for name in exocortex_v16 exocortex_v17; do
        if docker inspect "$name" &>/dev/null 2>&1; then
            CONTAINERS+=("$name")
        fi
    done
    if [[ ${#CONTAINERS[@]} -eq 0 ]]; then
        echo "  ERR  No agent zero containers found (exocortex_v16 / exocortex_v17)"
        exit 1
    fi
else
    if ! docker inspect "$TARGET" &>/dev/null 2>&1; then
        echo "  ERR  Container '$TARGET' not found"
        exit 1
    fi
    CONTAINERS+=("$TARGET")
fi

# ── Pre-flight ────────────────────────────────────────────────────────────────

if [[ ! -f "$SRC" ]]; then
    echo "  ERR  Source file not found: $SRC"
    exit 1
fi

echo ""
echo "━━━ deploy_extension.sh ━━━"
echo "  Source     : ${SRC}"
echo "  Hook       : ${HOOK}"
echo "  Target path: ${DEST}"
echo "  Containers : ${CONTAINERS[*]}"
echo ""

# Local syntax check (use the python found in PATH; on Windows often miniconda)
echo "  Syntax check:"
if command -v python3 &>/dev/null; then
    if python3 -m py_compile "$SRC" 2>&1; then
        echo "  OK    ${FILE} compiles"
    else
        echo "  ERR   ${FILE} syntax check failed"
        exit 1
    fi
elif command -v python &>/dev/null; then
    if python -m py_compile "$SRC" 2>&1; then
        echo "  OK    ${FILE} compiles"
    else
        echo "  ERR   ${FILE} syntax check failed"
        exit 1
    fi
else
    echo "  SKIP  no python3/python in PATH — caller must verify"
fi

LOCAL_MD5=$(md5sum "$SRC" | awk '{print $1}')
echo "  Local md5  : ${LOCAL_MD5}"
echo ""

# ── Per-container deploy + verify ─────────────────────────────────────────────

ERRORS=0
WARNINGS=0

for CONTAINER in "${CONTAINERS[@]}"; do
    echo "  ── ${CONTAINER} ──"

    # Ensure target hook directory exists
    _exec "$CONTAINER" mkdir -p "$(dirname "$DEST")" 2>/dev/null || true

    # Deploy
    if docker cp "$SRC" "${CONTAINER}:${DEST}" 2>/dev/null; then
        echo "  OK    docker cp succeeded"
    else
        echo "  ERR   docker cp failed"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Verify md5 match
    REMOTE_MD5=$(_exec "$CONTAINER" md5sum "$DEST" 2>/dev/null | awk '{print $1}')
    if [[ -z "$REMOTE_MD5" ]]; then
        echo "  ERR   could not read deployed file md5"
        ERRORS=$((ERRORS + 1))
        continue
    fi
    if [[ "$LOCAL_MD5" == "$REMOTE_MD5" ]]; then
        echo "  OK    deployed md5 matches local"
    else
        echo "  ERR   md5 MISMATCH — local=${LOCAL_MD5} remote=${REMOTE_MD5}"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Clear pycache
    _exec "$CONTAINER" sh -c "rm -f ${PYCACHE_GLOB} 2>/dev/null" || true
    echo "  OK    pycache cleared"

    # Orphan scan — find all other copies and report any that don't match
    # (DEC-026: dual-path discovery. Old paths can hold stale copies that
    # mislead future debugging. Surface them.)
    ORPHANS=$(_exec "$CONTAINER" sh -c "find /a0 -name '${FILE}' -not -path '*/__pycache__/*' 2>/dev/null" || true)
    ORPHAN_COUNT=0
    while IFS= read -r path; do
        [[ -z "$path" || "$path" == "$DEST" ]] && continue
        orphan_md5=$(_exec "$CONTAINER" md5sum "$path" 2>/dev/null | awk '{print $1}')
        if [[ "$orphan_md5" != "$LOCAL_MD5" ]]; then
            if [[ $ORPHAN_COUNT -eq 0 ]]; then
                echo "  WARN  other copies exist with DIFFERENT content:"
            fi
            echo "        ${path} (md5=${orphan_md5})"
            ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
            WARNINGS=$((WARNINGS + 1))
        fi
    done <<< "$ORPHANS"
    if [[ $ORPHAN_COUNT -eq 0 ]]; then
        echo "  OK    no stale copies elsewhere in /a0"
    else
        echo "  WARN  ${ORPHAN_COUNT} stale copy/copies above — review for cleanup"
    fi

    echo ""
done

# ── Summary ───────────────────────────────────────────────────────────────────

echo "━━━ Result ━━━"
if [[ $ERRORS -gt 0 ]]; then
    echo "  ${ERRORS} error(s). Deployment incomplete."
    exit 1
fi
echo "  Deployed and verified: ${FILE} → ${HOOK} on ${#CONTAINERS[@]} container(s)"
if [[ $WARNINGS -gt 0 ]]; then
    echo "  ${WARNINGS} warning(s) — stale copies exist (see above)"
fi
echo ""
echo "  NOTE: extension class cache only flushes on container restart."
echo "        After this deploy, restart run_ui to activate the new code:"
for c in "${CONTAINERS[@]}"; do
    echo "          docker exec ${c} supervisorctl restart run_ui"
done
