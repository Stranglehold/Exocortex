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

clear_pycache() {
    local pyc="$1"
    docker exec "${CONTAINER_NAME}" rm -f "${pyc}" 2>/dev/null || rm -f "${pyc}" 2>/dev/null || true
}

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

docker exec "${CONTAINER_NAME}" mkdir -p "${EXOCORTEX_DEST}/sleep_reports" 2>/dev/null || \
    mkdir -p "${EXOCORTEX_DEST}/sleep_reports" 2>/dev/null || true
docker exec "${CONTAINER_NAME}" mkdir -p "${EXOCORTEX_DEST}/operator_profile_versions" 2>/dev/null || \
    mkdir -p "${EXOCORTEX_DEST}/operator_profile_versions" 2>/dev/null || true

echo "  OK    sleep_reports/ directory"
echo "  OK    operator_profile_versions/ directory"

# ── Syntax check ─────────────────────────────────────────────────────────────

if command -v python3 &>/dev/null; then
    python3 -m py_compile "${REPO_DIR}/sleep_consolidation.py" && \
        echo "  OK    sleep_consolidation.py syntax check" || \
        { echo "  ERR   sleep_consolidation.py syntax check failed"; ERRORS=$((ERRORS + 1)); }
    python3 -m py_compile "${REPO_DIR}/sleep_episode_chunker.py" && \
        echo "  OK    sleep_episode_chunker.py syntax check" || \
        { echo "  ERR   sleep_episode_chunker.py syntax check failed"; ERRORS=$((ERRORS + 1)); }
    python3 -m py_compile "${REPO_DIR}/sleep_interaction_analyzer.py" && \
        echo "  OK    sleep_interaction_analyzer.py syntax check" || \
        { echo "  ERR   sleep_interaction_analyzer.py syntax check failed"; ERRORS=$((ERRORS + 1)); }
    python3 -m py_compile "${REPO_DIR}/extensions/tool_execute_after/_60_sleep_trigger.py" && \
        echo "  OK    _60_sleep_trigger.py syntax check" || \
        { echo "  ERR   _60_sleep_trigger.py syntax check failed"; ERRORS=$((ERRORS + 1)); }
    python3 -m py_compile "${REPO_DIR}/extensions/before_main_llm_call/_13_operator_profile.py" && \
        echo "  OK    _13_operator_profile.py syntax check" || \
        { echo "  ERR   _13_operator_profile.py syntax check failed"; ERRORS=$((ERRORS + 1)); }
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
