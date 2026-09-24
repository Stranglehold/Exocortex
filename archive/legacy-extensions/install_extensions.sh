#!/bin/bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: profile-ext (12 dirs, incl. the .hardening_originals backups)
#
# SPECIFIC NOTE: this also wrote the .hardening_originals backups of stock A0
# files before overwriting them. That capability is retired DELIBERATELY, not by
# accident: the backups existed to protect against this installer clobbering A0
# files, and the walk-based installer never writes into A0 core at all. The
# threat is gone, so the mitigation goes with it. A0 core patches are handled
# separately by the reversible patch scripts in plugins/_exocortex/patches/.
#
# It also carried a CURATED INSTALL_LIST of ~16 files against 69 live extensions.
# That list is the mechanism that let the pipeline drift: a list is a claim about
# what the plugin contains; the walk is a measurement of it.
#
# Why the legacy paths are dead:
#   /a0/python/**                        does not exist in stock v2.9 — the old
#                                        pipeline CREATED it, then wrote into it
#   /a0/usr/agents/agent0/extensions/**  the DEC-030 profile path. Worse than
#                                        dead: it still LOADS, so it resurrected
#                                        extensions that had been retired
#                                        (_71_cache_warmer, _05_cache_warm_bypass,
#                                        _02_cache_metrics_logger, and the three
#                                        dropped by DEC-030 itself)
#   /a0/usr/plugins/exocortex/**         no underscore — wrong plugin name; every
#                                        registered route is /_exocortex
#
# Measured, not assumed: scripts/audit_install_writes.sh attributes every write to
# the step that made it. Manifest: specs/INSTALL_PIPELINE_WRITE_MANIFEST.md
#
# The file is kept rather than deleted so nobody recreates it from scratch.
# ==============================================================================

# install_extensions.sh
# Installs the v1.13 curated Exocortex extension stack to the agent0 profile path.
# Profile path persists across A0 image updates (/a0/usr/agents/agent0/extensions/python/).
#
# Curated list (Tier 1-4 only — per Opus architectural guidance, May 2026):
#
# Tier 1 — Mechanical Safety (zero model calls, every turn/tool)
#   tool_execute_before/_02_tool_signature_guardian.py  — identical-call loop blocker
#   tool_execute_before/_16_py_write_guard.py           — .py write blocker
#   message_loop_prompts_after/_08_step_budget_tracker.py — step count + warnings
#
# Tier 2 — Context Quality (cheap heuristics, conditional)
#   message_loop_prompts_after/_55_memory_relevance_filter.py — ranked recall + budget gate
#   tool_execute_after/_28_output_compressor.py              — verbose output trimmer
#
# Tier 3 — Active Supervision (periodic or on signal)
#   message_loop_prompts_after/_21_constraint_heartbeat.py   — rule re-injection
#   message_loop_end/_50_supervisor_loop.py                  — loop/stall detection
#   message_loop_end/_28_backend_standby.py                  — backend recovery
#   message_loop_end/_29_stuck_delivery.py                   — stuck response recovery
#
# Tier 4 — Quality Assurance (specific triggers)
#   tool_execute_after/_25_evidence_ledger_recorder.py       — provenance tracking
#   monologue_end/_52_selective_memorizer.py                 — signal-discriminating memory
#   monologue_end/_55_memory_classifier.py                   — 5-axis classification
#   message_loop_prompts_after/_56_memory_enhancement.py     — 6-stage retrieval pipeline
#   before_main_llm_call/_11_belief_state_tracker.py         — BST classification only
#   before_main_llm_call/_15_karpathy_rules.py               — BST-gated coding standards
#
# DO NOT ADD without Opus architectural review:
#   BST enrichment injection, metacognitive injection, tool registry injection,
#   injection gate, operator profile per-turn.
#
# Safe to re-run. Removes stale heartbeat from wrong hook on first run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"
TARGET_ROOT="/a0/usr/agents/agent0/extensions/python"
BACKUP_ROOT="/a0/usr/agents/agent0/extensions/.hardening_originals"

if [ ! -d "$TARGET_ROOT" ]; then
  echo "ERROR: $TARGET_ROOT not found. Are you running inside the agent-zero container?"
  exit 1
fi

echo "Installing Exocortex v1.13 curated extension stack..."
echo ""

# ── Remove stale/wrong-hook extensions (profile path) ────────────────────────
# Tombstoned: archived to extensions/archived/ — see DEC-026 (audit_extensions.py).
echo "Removing stale extensions from profile path..."
rm -f "$TARGET_ROOT/before_main_llm_call/_21_constraint_heartbeat.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_09_injection_gate.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_17_orchestration_gate.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_19_context_pruner.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_18_injection_budget.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_13_operator_profile.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_14_metacognitive_injection.py"
rm -f "$TARGET_ROOT/before_main_llm_call/_16_tool_registry.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_09_context_pruner.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_16_tool_registry.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_18_memory_catalog.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_19_skill_suggester.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_57_orchestration_mode.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_58_ontology_query.py"
rm -f "$TARGET_ROOT/message_loop_prompts_after/_95_tiered_tool_injection.py"
rm -f "$TARGET_ROOT/message_loop_end/_16_verification_gate.py"
echo "  done."
echo ""

# ── Remove stale extensions from WRONG-PATH (missing python/ segment) ────────
# A0's loader only reads /a0/usr/agents/agent0/extensions/python/<hook>/. The
# path without the python/ segment is invisible to the loader; anything there
# is silently dead. The 2026-05-16 audit (scripts/audit_extensions.py) found
# 7 DEAD files at this wrong path on v16 and 10 on v17. Scrub the same set
# of tombstoned filenames here so the wrong-path no longer fools future
# debugging.
WRONG_PATH_ROOT="/a0/usr/agents/agent0/extensions"
echo "Removing stale extensions from wrong-path (missing python/ segment)..."
for HOOK_DIR in before_main_llm_call message_loop_prompts_after message_loop_end; do
  for STALE_FILE in \
    _09_context_pruner.py \
    _09_injection_gate.py \
    _14_metacognitive_injection.py \
    _16_tool_registry.py \
    _16_verification_gate.py \
    _17_orchestration_gate.py \
    _18_injection_budget.py \
    _18_memory_catalog.py \
    _19_context_pruner.py \
    _19_skill_suggester.py \
    _21_constraint_heartbeat.py \
    _57_orchestration_mode.py \
    _58_ontology_query.py \
    _71_cache_warmer.py \
    _95_tiered_tool_injection.py \
  ; do
    rm -f "$WRONG_PATH_ROOT/$HOOK_DIR/$STALE_FILE"
  done
done
echo "  done."
echo ""

# ── Remove stale extensions from plugin path (loaded by v1.13 plugin system) ─
# v1.13 load order: profile path wins on filename collision, but files only in
# the plugin path still run. Clean tombstoned extensions from the plugin too.
PLUGIN_EXT="/a0/usr/plugins/exocortex/extensions/python"
if [ -d "$PLUGIN_EXT" ]; then
  echo "Removing stale extensions from plugin path..."
  rm -f "$PLUGIN_EXT/before_main_llm_call/_16_tool_registry.py"
  rm -f "$PLUGIN_EXT/before_main_llm_call/_18_injection_budget.py"
  rm -f "$PLUGIN_EXT/before_main_llm_call/_15_htn_plan_selector.py"
  rm -f "$PLUGIN_EXT/before_main_llm_call/_12_proactive_supervisor.py"
  rm -f "$PLUGIN_EXT/message_loop_prompts_after/_16_tool_registry.py"
  rm -f "$PLUGIN_EXT/message_loop_prompts_after/_18_memory_catalog.py"
  rm -f "$PLUGIN_EXT/message_loop_prompts_after/_19_skill_suggester.py"
  rm -f "$PLUGIN_EXT/message_loop_prompts_after/_58_ontology_query.py"
  rm -f "$PLUGIN_EXT/message_loop_prompts_after/_95_tiered_tool_injection.py"
  echo "  done."
  echo ""
fi

# ── Remove from Exocortex source dir (archived — prevent accidental re-activation) ──
EXO_EXT="/a0/usr/Exocortex/extensions"
if [ -d "$EXO_EXT" ]; then
  rm -f "$EXO_EXT/before_main_llm_call/_16_tool_registry.py"
  rm -f "$EXO_EXT/message_loop_prompts_after/_16_tool_registry.py"
  rm -f "$EXO_EXT/message_loop_prompts_after/_95_tiered_tool_injection.py"
fi

# ── Curated install list ──────────────────────────────────────────────────────
declare -A INSTALL_LIST=(
  # Tier 1
  ["tool_execute_before/_02_tool_signature_guardian.py"]="tool_execute_before"
  ["tool_execute_before/_16_py_write_guard.py"]="tool_execute_before"
  ["message_loop_prompts_after/_08_step_budget_tracker.py"]="message_loop_prompts_after"
  # Tier 2
  ["message_loop_prompts_after/_55_memory_relevance_filter.py"]="message_loop_prompts_after"
  ["tool_execute_after/_28_output_compressor.py"]="tool_execute_after"
  # Tier 3
  ["message_loop_prompts_after/_21_constraint_heartbeat.py"]="message_loop_prompts_after"
  ["message_loop_end/_50_supervisor_loop.py"]="message_loop_end"
  ["message_loop_end/_28_backend_standby.py"]="message_loop_end"
  ["message_loop_end/_29_stuck_delivery.py"]="message_loop_end"
  # Tier 4
  ["tool_execute_after/_25_evidence_ledger_recorder.py"]="tool_execute_after"
  ["monologue_end/_52_selective_memorizer.py"]="monologue_end"
  ["monologue_end/_55_memory_classifier.py"]="monologue_end"
  ["message_loop_prompts_after/_56_memory_enhancement.py"]="message_loop_prompts_after"
  ["before_main_llm_call/_11_belief_state_tracker.py"]="before_main_llm_call"
  ["before_main_llm_call/_15_karpathy_rules.py"]="before_main_llm_call"
)

INSTALLED=0
FAILED=0

for RELPATH in "${!INSTALL_LIST[@]}"; do
  HOOK_DIR="${INSTALL_LIST[$RELPATH]}"
  SOURCE_FILE="$SOURCE_DIR/$RELPATH"
  TARGET_DIR="$TARGET_ROOT/$HOOK_DIR"
  FILENAME="$(basename "$RELPATH")"
  TARGET_FILE="$TARGET_DIR/$FILENAME"
  BACKUP_DIR="$BACKUP_ROOT/$HOOK_DIR"

  if [ ! -f "$SOURCE_FILE" ]; then
    echo "MISSING: $RELPATH (skipped)"
    FAILED=$((FAILED + 1))
    continue
  fi

  mkdir -p "$TARGET_DIR" "$BACKUP_DIR"

  if [ -f "$TARGET_FILE" ] && [ ! -f "$BACKUP_DIR/$FILENAME" ]; then
    cp "$TARGET_FILE" "$BACKUP_DIR/$FILENAME"
    echo "BACKED UP: $HOOK_DIR/$FILENAME"
  fi

  # Compile-check before installing
  if ! python3 -m py_compile "$SOURCE_FILE" 2>/dev/null; then
    echo "COMPILE FAIL: $RELPATH (skipped)"
    FAILED=$((FAILED + 1))
    continue
  fi

  cp "$SOURCE_FILE" "$TARGET_FILE"
  echo "INSTALLED: $HOOK_DIR/$FILENAME"
  INSTALLED=$((INSTALLED + 1))
done

# ── Clear pycache ─────────────────────────────────────────────────────────────
echo ""
echo "Clearing pycache..."
find "$TARGET_ROOT" -name "*.pyc" -delete
find "$TARGET_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ── Verification pass (DEC-026) ───────────────────────────────────────────────
# Confirm no un-curated .py files exist in either discovery path.
# Any file here that isn't in INSTALL_LIST is a ghost extension risk.
echo ""
echo "Verification pass — scanning for un-curated extensions..."

CURATED_FILENAMES=()
for RELPATH in "${!INSTALL_LIST[@]}"; do
  CURATED_FILENAMES+=("$(basename "$RELPATH")")
done

GHOST_FOUND=0
for PY in $(find "$TARGET_ROOT" -name "*.py" 2>/dev/null); do
  FNAME="$(basename "$PY")"
  FOUND=0
  for CF in "${CURATED_FILENAMES[@]}"; do
    [ "$FNAME" = "$CF" ] && FOUND=1 && break
  done
  if [ $FOUND -eq 0 ]; then
    echo "  UNCURATED (profile): $PY"
    GHOST_FOUND=$((GHOST_FOUND + 1))
  fi
done

if [ -d "$PLUGIN_EXT" ]; then
  for PY in $(find "$PLUGIN_EXT" -name "*.py" 2>/dev/null); do
    FNAME="$(basename "$PY")"
    FOUND=0
    for CF in "${CURATED_FILENAMES[@]}"; do
      [ "$FNAME" = "$CF" ] && FOUND=1 && break
    done
    if [ $FOUND -eq 0 ]; then
      echo "  UNCURATED (plugin): $PY"
      GHOST_FOUND=$((GHOST_FOUND + 1))
    fi
  done
fi

if [ $GHOST_FOUND -eq 0 ]; then
  echo "  OK — no un-curated extensions found."
else
  echo "  WARNING: $GHOST_FOUND un-curated file(s) found. Review and tombstone if stale."
fi

echo ""
echo "Done. $INSTALLED installed, $FAILED skipped."
echo "Restart the container to activate: docker restart exocortex_v17"
echo "Originals preserved in: $BACKUP_ROOT"
