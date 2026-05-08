#!/usr/bin/env bash
# ━━━ Sleep Consolidation — Install ━━━
# Deploys Phase 1 sleep consolidation files to Agent-Zero paths.
#
# Deploys:
#   - sleep_consolidation.py  → /a0/usr/Exocortex/
#   - sleep_config.json       → /a0/usr/Exocortex/
#   - _60_sleep_trigger.py    → /a0/python/extensions/tool_execute_after/
#
# Creates runtime directories:
#   - /a0/usr/Exocortex/sleep_reports/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
EXT_DEST="/a0/python/extensions/tool_execute_after"
EXT_BEFORE_LLM="/a0/python/extensions/before_main_llm_call"
EXOCORTEX_DEST="/a0/usr/Exocortex"
ERRORS=0

echo ""
echo "━━━ Sleep Consolidation — Install ━━━"
echo "  Source : ${REPO_DIR}"
echo "  Target : ${EXOCORTEX_DEST}"
echo ""

install_file() {
    local src="$1" dest="$2" label="${3:-$(basename "$1")}"
    if [[ ! -f "$src" ]]; then
        echo "  SKIP  ${label} (not found at ${src})"
        return 0
    fi
    # Skip if source and destination resolve to the same path (in-container install)
    local src_real dest_real
    src_real="$(realpath "$src" 2>/dev/null || echo "$src")"
    dest_real="$(realpath "$dest" 2>/dev/null || echo "$dest")"
    if [[ "$src_real" == "$dest_real" ]]; then
        echo "  OK    ${label} (already in place)"
        return 0
    fi
    if docker cp "${src}" "${CONTAINER_NAME}:${dest}" 2>/dev/null; then
        echo "  OK    ${label} → ${dest}"
    else
        cp -p "${src}" "${dest}" 2>/dev/null || {
            echo "  ERR   ${label} — deploy failed"
            ERRORS=$((ERRORS + 1))
            return 1
        }
        echo "  OK    ${label} → ${dest} (direct copy)"
    fi
}

install_file_if_missing() {
    local src="$1" dest="$2" label="${3:-$(basename "$1")}"
    if [[ ! -f "$src" ]]; then
        echo "  SKIP  ${label} (not found at ${src})"
        return 0
    fi
    # Check if destination already exists in container
    if _exec "${CONTAINER_NAME}" test -f "${dest}" 2>/dev/null; then
        echo "  OK    ${label} (already present — skipping)"
        return 0
    fi
    if docker cp "${src}" "${CONTAINER_NAME}:${dest}" 2>/dev/null; then
        echo "  OK    ${label} → ${dest} (initial deploy)"
    else
        cp -p "${src}" "${dest}" 2>/dev/null || {
            echo "  ERR   ${label} — deploy failed"
            ERRORS=$((ERRORS + 1))
            return 1
        }
        echo "  OK    ${label} → ${dest} (direct copy)"
    fi
}

clear_pycache() {
    local pyc="$1"
    _exec "${CONTAINER_NAME}" rm -f "${pyc}" 2>/dev/null || rm -f "${pyc}" 2>/dev/null || true
}

# Prevent Git Bash on Windows from translating Unix paths in docker exec arguments.
_exec() { MSYS_NO_PATHCONV=1 docker exec "$@"; }

CONTAINER_NAME="${CONTAINER_NAME:-flamboyant_bell}"

# ── Exocortex module files ────────────────────────────────────────────────────

install_file \
    "${REPO_DIR}/sleep_consolidation.py" \
    "${EXOCORTEX_DEST}/sleep_consolidation.py" \
    "sleep_consolidation.py"

install_file \
    "${REPO_DIR}/sleep_episode_chunker.py" \
    "${EXOCORTEX_DEST}/sleep_episode_chunker.py" \
    "sleep_episode_chunker.py"

install_file \
    "${REPO_DIR}/sleep_interaction_analyzer.py" \
    "${EXOCORTEX_DEST}/sleep_interaction_analyzer.py" \
    "sleep_interaction_analyzer.py"

install_file \
    "${REPO_DIR}/sleep_config.json" \
    "${EXOCORTEX_DEST}/sleep_config.json" \
    "sleep_config.json"

# Deploy Exocortex config.json (only if not already present — preserves user edits)
install_file_if_missing \
    "${REPO_DIR}/config.json" \
    "${EXOCORTEX_DEST}/config.json" \
    "config.json"

# ── Extension files ───────────────────────────────────────────────────────────

install_file \
    "${REPO_DIR}/extensions/tool_execute_after/_60_sleep_trigger.py" \
    "${EXT_DEST}/_60_sleep_trigger.py" \
    "_60_sleep_trigger.py"

install_file \
    "${REPO_DIR}/extensions/before_main_llm_call/_13_operator_profile.py" \
    "${EXT_BEFORE_LLM}/_13_operator_profile.py" \
    "_13_operator_profile.py"

# Clear pycache for extensions
clear_pycache "${EXT_DEST}/__pycache__/_60_sleep_trigger.cpython-312.pyc"
clear_pycache "${EXT_BEFORE_LLM}/__pycache__/_13_operator_profile.cpython-312.pyc"

# ── Runtime directories ───────────────────────────────────────────────────────

_exec "${CONTAINER_NAME}" mkdir -p "${EXOCORTEX_DEST}/sleep_reports" 2>/dev/null || \
    mkdir -p "${EXOCORTEX_DEST}/sleep_reports" 2>/dev/null || true
_exec "${CONTAINER_NAME}" mkdir -p "${EXOCORTEX_DEST}/operator_profile_versions" 2>/dev/null || \
    mkdir -p "${EXOCORTEX_DEST}/operator_profile_versions" 2>/dev/null || true

echo "  OK    sleep_reports/ directory"
echo "  OK    operator_profile_versions/ directory"

# ── Syntax check ─────────────────────────────────────────────────────────────

py_check() {
    local f="$1"
    [[ ! -f "$f" ]] && { echo "  SKIP  $(basename "$f") syntax check (not found)"; return 0; }
    python3 -m py_compile "$f" && \
        echo "  OK    $(basename "$f") syntax check" || \
        { echo "  ERR   $(basename "$f") syntax check failed"; ERRORS=$((ERRORS + 1)); }
}

if command -v python3 &>/dev/null; then
    py_check "${REPO_DIR}/sleep_consolidation.py"
    py_check "${REPO_DIR}/sleep_episode_chunker.py"
    py_check "${REPO_DIR}/sleep_interaction_analyzer.py"
    py_check "${REPO_DIR}/extensions/tool_execute_after/_60_sleep_trigger.py"
    py_check "${REPO_DIR}/extensions/before_main_llm_call/_13_operator_profile.py"
fi

# ── Result ────────────────────────────────────────────────────────────────────

echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo "  Sleep consolidation installed successfully."
    echo "  Config: ${EXOCORTEX_DEST}/sleep_config.json"
    echo "  Reports: ${EXOCORTEX_DEST}/sleep_reports/"
    echo "  Idle threshold: 10 minutes (default, set in sleep_config.json)"
else
    echo "  ${ERRORS} error(s) during install. Review output above."
    exit 1
fi
