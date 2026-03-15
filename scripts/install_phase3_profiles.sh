#!/bin/bash
# install_phase3_profiles.sh — Deploy Phase 3 Adaptive Supervisor (Success Profiles)
#
# Deploys:
#   - success_profile_store.py  → /a0/usr/Exocortex/
#   - _30_tool_fallback_logger.py → /a0/python/extensions/tool_execute_after/
#   - _50_supervisor_loop.py    → /a0/python/extensions/message_loop_end/
#
# Phase 3 adds behavioral success profile learning to the Adaptive Supervisor.
# The supervisor now accumulates a prior for failures_before_success per
# (tool_name, domain) and uses that distribution to calibrate thresholds
# instead of relying solely on hand-tuned static DOMAIN_THRESHOLDS.

set -e

CONTAINER="flamboyant_bell"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXOCORTEX_DEST="/a0/usr/Exocortex"
EXT_DEST="/a0/python/extensions"

echo "[install_phase3_profiles] Starting Phase 3 deployment..."

# --- Deploy success_profile_store.py ---
echo "[install_phase3_profiles] Deploying success_profile_store.py..."
docker cp "${REPO_DIR}/success_profile_store.py" "${CONTAINER}:${EXOCORTEX_DEST}/success_profile_store.py"

# --- Deploy fallback logger (Phase 3: episode buffering) ---
echo "[install_phase3_profiles] Deploying _30_tool_fallback_logger.py..."
docker cp "${REPO_DIR}/extensions/tool_execute_after/_30_tool_fallback_logger.py" \
    "${CONTAINER}:${EXT_DEST}/tool_execute_after/_30_tool_fallback_logger.py"

# --- Deploy supervisor loop (Phase 3: three-layer threshold selection) ---
echo "[install_phase3_profiles] Deploying _50_supervisor_loop.py..."
docker cp "${REPO_DIR}/extensions/message_loop_end/_50_supervisor_loop.py" \
    "${CONTAINER}:${EXT_DEST}/message_loop_end/_50_supervisor_loop.py"

# --- Clear pycache ---
echo "[install_phase3_profiles] Clearing pycache..."
docker exec "${CONTAINER}" sh -c "
    find /a0/usr/Exocortex -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    find /a0/python/extensions/tool_execute_after -name '*.pyc' -delete 2>/dev/null || true
    find /a0/python/extensions/message_loop_end -name '*.pyc' -delete 2>/dev/null || true
"

# --- Compile verify ---
echo "[install_phase3_profiles] Verifying compilation..."
docker exec "${CONTAINER}" sh -c "
    python3 -m py_compile /a0/usr/Exocortex/success_profile_store.py && echo 'success_profile_store OK' &&
    python3 -m py_compile /a0/python/extensions/tool_execute_after/_30_tool_fallback_logger.py && echo 'fallback_logger OK' &&
    python3 -m py_compile /a0/python/extensions/message_loop_end/_50_supervisor_loop.py && echo 'supervisor_loop OK'
"

echo "[install_phase3_profiles] Phase 3 deployment complete."
echo ""
echo "To activate: restart the container or reload Agent Zero."
echo "Verify: look for '[SUPERVISOR] Phase 3 observation:' in logs after a session"
echo "        with tool failures followed by success."
