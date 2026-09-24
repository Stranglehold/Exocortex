#!/bin/bash
# ==============================================================================
# Exocortex plugin deploy — DIRECTORY WALK, no curated list
# ==============================================================================
# Tier 1.1 step 3. Deploys the repo's plugins/_exocortex/ tree to
# /a0/usr/plugins/_exocortex/ on the target container.
#
# WHY A WALK AND NOT A LIST
# -------------------------
# A curated list is a *claim* about what the plugin contains. A directory walk is
# a *measurement* of what it contains. Every time someone adds an extension and
# forgets the list, the claim drifts from reality — which is exactly how the old
# pipeline ended up deploying 20 stale extension versions and resurrecting
# extensions that were explicitly retired (_71_cache_warmer, _05_cache_warm_bypass,
# _02_cache_metrics_logger, plus the three dropped by DEC-030). The repo tree is
# the single source of truth. This script's only job is to reproduce it faithfully.
#
# If something should not be deployed, it should not be in the repo tree.
#
# WHAT IS NOT BYTE-REPRODUCED
# ---------------------------
# config/config.json is read-merge-write via scripts/merge_plugin_config.py: new
# sections are added, existing operator-tuned sections are never clobbered.
# Everything else — including config/model_profiles/*.json — IS byte-reproduced,
# because those are inputs the stack reads, not operator state.
#
# VERIFY WITH
#   python scripts/verify_plugin_parity.py <container>
# ==============================================================================

set -u

# Git Bash / MSYS rewrites container-side absolute paths on their way to docker:
#   docker cp x c:/a0/usr/... -> c:C:/Program Files/Git/a0/usr/...
#   docker exec c /opt/venv-a0/bin/python3 -> C:/Program Files/Git/opt/venv-a0/...
# Wiring seam #30's cousin. Disable translation for this script's own docker calls.
# Inert when run inside the container (no MSYS there, and install_all.sh's docker
# shim turns cp/exec into local operations), so this is safe in both modes.
export MSYS_NO_PATHCONV=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$SCRIPT_DIR/plugins/_exocortex"
DEST="/a0/usr/plugins/_exocortex"
CONTAINER="${CONTAINER:-exocortex_v16}"

MERGE_HELPER="$SCRIPT_DIR/scripts/merge_plugin_config.py"
CONFIG_REL="config/config.json"

echo "=== Exocortex plugin deploy (directory walk) ==="
echo "  source    : $SRC"
echo "  target    : $CONTAINER:$DEST"

if [ ! -d "$SRC" ]; then
  echo "  ERROR: source tree not found: $SRC"
  exit 1
fi

# ── Enumerate ─────────────────────────────────────────────────────────────────
# Skip build artefacts and local backups. Nothing else is filtered — that is the
# whole point.
FILES="$(cd "$SRC" && find . -type f \
  ! -path '*/__pycache__/*' \
  ! -name '*.pyc' \
  ! -name '*.pyo' \
  ! -name '*.bak' \
  ! -name '*.bak-*' \
  ! -name '*~' \
  | sed 's|^\./||' | sort)"

TOTAL="$(printf '%s\n' "$FILES" | grep -c . || true)"
echo "  files     : $TOTAL"

if [ "$TOTAL" -eq 0 ]; then
  echo "  ERROR: nothing to deploy — refusing to continue"
  exit 1
fi

# ── Retirement gate (Opus ruling 1, 2026-09-24) ───────────────────────────────
# scripts/retired_manifest.txt lists files switched off on purpose. This walk deploys every
# file in the tree, so a retired source still (or again) in the tree comes back on the next
# install. On 2026-09-24 eleven of the eighteen retired extensions had no `enabled` check, so
# they would have come back RUNNING. The manifest alone only DETECTS that afterwards (the
# parity gate's RESURRECTED); this makes the walk REFUSE it.
#
# A refused file is left out, named, and the step exits 3, so install_all.sh reports it
# instead of succeeding quietly. It is a decision for a human: remove the manifest line
# (un-retiring, Jake's call, auditable in git) or remove the source (a forgotten artifact).
#
# Matched on the manifest's relative path, and for .py also on file name: A0 loads
# extensions by file name within each hook directory, so a retired file moved into another
# hook would still run. One awk pass, not a grep per file (process spawns are slow in Git Bash).
MANIFEST="$SCRIPT_DIR/scripts/retired_manifest.txt"
refused=0
if [ -f "$MANIFEST" ]; then
  GATE="$(printf '%s\n' "$FILES" | awk -v manifest="$MANIFEST" '
    BEGIN {
      while ((getline line < manifest) > 0) {
        sub(/[ \t]+#.*$/, "", line); sub(/^[ \t]+/, "", line); sub(/[ \t\r]+$/, "", line)
        if (line == "" || substr(line, 1, 1) == "#") continue
        path[line] = 1
        if (line ~ /\.py$/) { b = line; sub(/.*\//, "", b); base[b] = 1 }
      }
    }
    NF {
      rel = $0; b = rel; sub(/.*\//, "", b)
      if (rel in path)                   { print "REFUSED manifest-path " rel; next }
      if (rel ~ /\.py$/ && (b in base))  { print "REFUSED manifest-name " rel; next }
      print "KEEP " rel
    }')"
  refused="$(printf '%s\n' "$GATE" | grep -c '^REFUSED ' || true)"
  if [ "$refused" -gt 0 ]; then
    printf '%s\n' "$GATE" | grep '^REFUSED ' | sed 's/^/  /'
  fi
  FILES="$(printf '%s\n' "$GATE" | sed -n 's/^KEEP //p')"
  echo "  refused   : $refused (retired, per scripts/retired_manifest.txt)"
else
  echo "  WARNING: retired manifest missing ($MANIFEST) — the retirement gate is OFF"
fi

# ── Pre-create directories ────────────────────────────────────────────────────
# Host-side `docker cp` does not always create missing parents; the in-container
# shim does its own mkdir but costs nothing here.
# `sed -n .../p` prints ONLY lines where the substitution matched, i.e. paths that
# actually contained a slash. A plain `sed | grep -v '^[^/]*$'` cannot distinguish a
# top-level FILE (plugin.yaml) from a first-level DIRECTORY (api/), and silently
# dropped api/, tools/, prompts/ — 21 files failed to deploy with
# "Could not find the file .../api in container".
DIRS="$(printf '%s\n' "$FILES" | sed -n 's|/[^/]*$||p' | sort -u)"
if [ -n "$DIRS" ]; then
  MKDIR_ARGS=""
  for d in $DIRS; do
    MKDIR_ARGS="$MKDIR_ARGS $DEST/$d"
  done
  # shellcheck disable=SC2086
  docker exec "$CONTAINER" mkdir -p $DEST $MKDIR_ARGS
else
  docker exec "$CONTAINER" mkdir -p "$DEST"
fi

# ── Deploy ────────────────────────────────────────────────────────────────────
deployed=0
skipped_cfg=0
failed=0

# Source paths are RELATIVE, deliberately. With MSYS_NO_PATHCONV=1 set above,
# Git Bash also stops rewriting the *source* side, so an absolute /d/Vibecode/...
# path reaches Windows docker unconverted and cannot be resolved. Relative paths
# work correctly in both Git Bash and in-container.
cd "$SRC" || { echo "  ERROR: cannot enter $SRC"; exit 1; }

first_error=""
for rel in $FILES; do
  if [ "$rel" = "$CONFIG_REL" ]; then
    skipped_cfg=1
    continue   # handled by the merge step below
  fi
  if err="$(docker cp "./$rel" "$CONTAINER:$DEST/$rel" 2>&1)"; then
    deployed=$((deployed + 1))
  else
    failed=$((failed + 1))
    [ -z "$first_error" ] && first_error="$rel: $err"
    [ "$failed" -le 5 ] && echo "  FAILED: $rel"
  fi
done

cd "$SCRIPT_DIR" || true

if [ -n "$first_error" ]; then
  echo "  first error: $first_error"
fi

echo "  deployed  : $deployed"
[ "$failed" -gt 0 ] && echo "  FAILED    : $failed"

# ── Config: read-merge-write, never overwrite ─────────────────────────────────
if [ "$skipped_cfg" -eq 1 ] && [ -f "$MERGE_HELPER" ]; then
  (cd "$SCRIPT_DIR" && docker cp "./scripts/merge_plugin_config.py" "$CONTAINER:/tmp/_exo_merge_cfg.py") >/dev/null 2>&1
  (cd "$SRC" && docker cp "./$CONFIG_REL" "$CONTAINER:/tmp/_exo_repo_config.json") >/dev/null 2>&1
  docker exec "$CONTAINER" /opt/venv-a0/bin/python3 /tmp/_exo_merge_cfg.py \
    /tmp/_exo_repo_config.json "$DEST/$CONFIG_REL"
  docker exec "$CONTAINER" rm -f /tmp/_exo_merge_cfg.py /tmp/_exo_repo_config.json
elif [ "$skipped_cfg" -eq 1 ]; then
  echo "  WARNING: merge helper missing ($MERGE_HELPER) — config/config.json NOT deployed"
fi

# ── Clear stale bytecode ──────────────────────────────────────────────────────
# A0 caches extension classes in-process; stale .pyc on top of that is a second
# way to run code you did not just deploy.
docker exec "$CONTAINER" sh -c "find $DEST -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true"

echo "  pycache   : cleared"
echo
echo "  Verify: python scripts/verify_plugin_parity.py $CONTAINER"

[ "$failed" -eq 0 ] || exit 1
if [ "$refused" -gt 0 ]; then
  echo
  echo "  RETIRED FILES REFUSED: $refused (listed above). Everything else deployed."
  echo "  Each needs a decision: remove its line from scripts/retired_manifest.txt to"
  echo "  un-retire it (Jake's call), or remove the source file if it is a leftover."
  exit 3
fi
exit 0
