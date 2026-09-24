#!/bin/bash
# ==============================================================================
# RETIRED 2026-08-19 — DO NOT ADD BACK TO install_all.sh
# ==============================================================================
# Every path this script wrote is one A0 v2.9 does not load from, and its content
# now lives in plugins/_exocortex/ and is deployed by the directory walk in
# scripts/install_exocortex_plugin.sh.
#
# It used to write: /a0/python/extensions/{error_format,tool_execute_after}
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

# install_failure_tracker.sh
# Installs failure tracker extensions into agent-zero extension points
# Safe to re-run — backs up existing files before overwriting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTENSIONS_DIR="/a0/python/extensions"
BACKUP_DIR="$EXTENSIONS_DIR/.hardening_originals"

EXTENSIONS=(
  "error_format/_30_failure_tracker.py"
  "tool_execute_after/_20_reset_failure_counter.py"
)

echo "Installing failure tracker extensions..."

mkdir -p "$BACKUP_DIR/error_format"
mkdir -p "$BACKUP_DIR/tool_execute_after"

for ext in "${EXTENSIONS[@]}"; do
  src="$SCRIPT_DIR/$ext"
  dst="$EXTENSIONS_DIR/$ext"
  dst_dir="$(dirname "$dst")"

  if [ ! -f "$src" ]; then
    echo "  ERROR: Source not found: $src"
    exit 1
  fi

  mkdir -p "$dst_dir"

  # Backup existing file if present and not already backed up
  backup="$BACKUP_DIR/$ext"
  if [ -f "$dst" ] && [ ! -f "$backup" ]; then
    cp "$dst" "$backup"
    echo "  Backed up: $ext"
  fi

  cp "$src" "$dst"
  echo "  Installed: $ext"
done

echo ""
echo "Failure tracker installed (${#EXTENSIONS[@]} extensions)."
echo "Backup location: $BACKUP_DIR"
