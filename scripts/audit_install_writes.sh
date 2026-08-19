#!/bin/bash
# ==============================================================================
# Per-step write attribution for install_all.sh
# ==============================================================================
# Produces the manifest Opus asked for before the surgical strip: for EVERY install
# step, exactly which paths it writes, classified as LEGACY (strip) or OUTSIDE
# (keep) or PLUGIN (now covered by the directory walk).
#
# Measured, not grepped. The scripts resolve their destinations through variables
# ($TARGET_ROOT, $EXT_DEST, $PLUGIN_BASE...), so static analysis of literal paths
# under-reports. This runs each step and records what actually landed.
#
# MUST run INSIDE the container, with A0 STOPPED so the only writer is the
# installer. A running A0 touches logs, memory and cycle state continuously and
# would contaminate every measurement.
#
#   supervisorctl stop run_ui
#   bash scripts/audit_install_writes.sh > /tmp/write_audit.txt
#
# Output is one block per step, then a classification summary.
# ==============================================================================

set -u

SRC_ROOT="${SRC_ROOT:-/opt/exocortex-src}"
MARKER=/tmp/_audit_marker
export CONTAINER="${CONTAINER:-audit}"

cd "$SRC_ROOT" || { echo "ERROR: $SRC_ROOT not found"; exit 1; }

# ── docker shim ───────────────────────────────────────────────────────────────
# Same shim install_all.sh installs. Without it every child script that uses
# `docker cp` exits 127 (command not found) and writes nothing — the first run of
# this audit reported a confident, wrong manifest for exactly that reason.
_SHIM_DIR="$(mktemp -d)"
trap 'rm -rf "$_SHIM_DIR"' EXIT
cat > "$_SHIM_DIR/docker" << 'SHIM_EOF'
#!/bin/bash
case "$1" in
  cp)
    shift
    src="$1"; dst="$2"
    src="${src##*:}"; dst="${dst##*:}"
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    ;;
  exec)
    shift; shift
    "$@"
    ;;
  *)
    echo "docker-shim: unsupported command '$1'" >&2
    exit 1
    ;;
esac
SHIM_EOF
chmod +x "$_SHIM_DIR/docker"
export PATH="$_SHIM_DIR:$PATH"
command -v docker >/dev/null || { echo "ERROR: shim not on PATH"; exit 1; }

# Directories that churn regardless of the installer.
EXCLUDES=(
  -path '*/__pycache__/*' -o
  -path '/a0/usr/memory/*' -o
  -path '/a0/usr/logs/*' -o
  -path '/a0/tmp/*' -o
  -path '/tmp/*' -o
  -name '*.pyc' -o
  -name '*.log'
)

classify() {
  case "$1" in
    /a0/python/*)                        echo "LEGACY:a0-python" ;;
    /a0/usr/agents/agent0/extensions/*)  echo "LEGACY:profile-ext" ;;
    /a0/usr/agents/agent0/*)             echo "LEGACY:profile-other" ;;
    /a0/usr/plugins/exocortex/*)         echo "LEGACY:no-underscore" ;;
    /a0/usr/plugins/_exocortex/*)        echo "PLUGIN:walk-covers" ;;
    *)                                   echo "OUTSIDE:keep" ;;
  esac
}

# Pull the step manifest straight out of install_all.sh so this cannot drift.
STEPS="$(grep -oE '"[0-9]+\|[^"]+"' install_all.sh | tr -d '"')"

printf '%s\n' "=== PER-STEP WRITE AUDIT ==="
printf '%s\n' "source: $SRC_ROOT"
echo

SUMMARY_FILE=/tmp/_audit_summary
: > "$SUMMARY_FILE"

while IFS='|' read -r layer name script; do
  script="$(echo "$script" | sed 's/[[:space:]]*$//')"
  name="$(echo "$name" | sed 's/[[:space:]]*$//')"
  [ -z "$script" ] && continue
  [ -f "$script" ] || { echo "--- SKIP (missing): $script"; continue; }

  touch "$MARKER"
  sleep 1
  bash "$script" >/dev/null 2>&1
  rc=$?
  # -newercm (file CTIME vs marker MTIME), NOT -newer: the docker shim copies with
  # `cp -p`, preserving the SOURCE mtime, so mtime-based detection is blind to every
  # deployed file — it missed 54 real writes on the previous run. ctime survives -p.

  WRITES="$(find /a0 -newercm "$MARKER" -type f \( "${EXCLUDES[@]}" \) -prune -o \
            -newercm "$MARKER" -type f -print 2>/dev/null | sort)"

  echo "--- [$layer] $name"
  echo "    script: $script (exit $rc)"

  if [ -z "$WRITES" ]; then
    echo "    writes: none"
    echo
    continue
  fi

  # Collapse to directories so the manifest is readable rather than 200 file lines.
  printf '%s\n' "$WRITES" | sed 's|/[^/]*$||' | sort -u | while read -r d; do
    n="$(printf '%s\n' "$WRITES" | grep -c "^$d/[^/]*$")"
    cls="$(classify "$d/x")"
    printf '    %-22s %-3s %s\n' "$cls" "$n" "$d"
    echo "$script|$cls|$n|$d" >> "$SUMMARY_FILE"
  done
  echo
done <<< "$STEPS"

echo "=== CLASSIFICATION SUMMARY ==="
echo
echo "--- scripts writing ONLY to legacy/plugin paths (fully redundant) ---"
awk -F'|' '{s[$1]; if ($2 ~ /^OUTSIDE/) keep[$1]=1} END {for (k in s) if (!(k in keep)) print "  " k}' "$SUMMARY_FILE" | sort
echo
echo "--- scripts with OUTSIDE content that MUST survive the strip ---"
awk -F'|' '$2 ~ /^OUTSIDE/ {printf "  %-52s %s\n", $1, $4}' "$SUMMARY_FILE" | sort -u
echo
echo "--- totals by class ---"
awk -F'|' '{c[$2]+=$3} END {for (k in c) printf "  %-22s %s files\n", k, c[k]}' "$SUMMARY_FILE" | sort
