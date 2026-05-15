#!/bin/bash
# verify_deployment.sh
# Audits the extension deployment state of an Exocortex container.
#
# Reports these categories per file:
#   CONFLICT     — file exists in both profile and plugin paths with DIFFERENT content.
#                  Profile path wins at runtime. Under --mode option3 this is expected
#                  (plugin is stale, profile is current) — shown as PLUGIN-STALE, not a failure.
#   SHADOW-SAME  — file exists in both paths with identical content. Redundant copy, harmless.
#   PLUGIN-ONLY  — file exists only in the plugin path. Under Option 3 this is a deployment gap —
#                  extension loads from lower-priority path, may be shadowed on next install.
#   PROFILE-ONLY — file exists only in the profile path. Correct under Option 3.
#   LEGACY-ONLY  — file exists only in the ephemeral /a0/python/extensions/ path.
#                  Should NOT be running (shadowed by profile/plugin if duplicated; orphaned if not).
#
# Usage:
#   bash verify_deployment.sh                        # default container: exocortex_v17
#   CONTAINER=exocortex_v16 bash verify_deployment.sh
#   bash verify_deployment.sh --container exocortex_v16
#   bash verify_deployment.sh --mode option3         # Option 3 semantics: CONFLICT→PLUGIN-STALE (not a failure)
#   bash verify_deployment.sh --json                 # machine-readable output
#
# Exit codes:
#   Default:       0 = clean (no CONFLICT, no LEGACY-ONLY), 1 = issues found
#   --mode option3: 0 = clean (no PLUGIN-ONLY, no LEGACY-ONLY), 1 = issues found

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────

CONTAINER="${CONTAINER:-exocortex_v17}"
JSON_MODE=false
MODE="${MODE:-default}"

for arg in "$@"; do
  case "$arg" in
    --container=*) CONTAINER="${arg#*=}" ;;
    --container)   shift; CONTAINER="${1:-$CONTAINER}" ;;
    --mode=*)      MODE="${arg#*=}" ;;
    --mode)        shift; MODE="${1:-$MODE}" ;;
    --json)        JSON_MODE=true ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────────

if [ "$JSON_MODE" = false ]; then
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  GREEN='\033[0;32m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  DIM='\033[2m'
  NC='\033[0m'
else
  RED='' YELLOW='' GREEN='' CYAN='' BOLD='' DIM='' NC=''
fi

log_header()         { [ "$JSON_MODE" = false ] && echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}"; }
log_conflict()       { echo -e "  ${RED}CONFLICT     ${NC} $1"; }
log_plugin_stale()   { echo -e "  ${DIM}PLUGIN-STALE ${NC} $1"; }
log_same()           { echo -e "  ${DIM}SHADOW-SAME  ${NC} $1"; }
log_plugin()         { echo -e "  ${RED}PLUGIN-ONLY  ${NC} $1"; }
log_profile()        { echo -e "  ${YELLOW}PROFILE-ONLY ${NC} $1"; }
log_legacy_only()    { echo -e "  ${RED}LEGACY-ONLY  ${NC} $1"; }
log_legacy_stale()   { echo -e "  ${YELLOW}LEGACY-STALE ${NC} $1"; }

# ── Container check ───────────────────────────────────────────────────────────

if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER}$"; then
  echo "ERROR: Container '$CONTAINER' not running." >&2
  exit 1
fi

_exec() { MSYS_NO_PATHCONV=1 docker exec "$CONTAINER" "$@"; }

# ── Paths ─────────────────────────────────────────────────────────────────────

PLUGIN="/a0/usr/plugins/exocortex/extensions/python"
PROFILE="/a0/usr/agents/agent0/extensions/python"
LEGACY="/a0/python/extensions"

HOOKS=(
  before_main_llm_call
  error_format
  hist_add_before
  message_loop_end
  message_loop_prompts_after
  monologue_end
  reasoning_stream
  reasoning_stream_end
  response_stream_chunk
  response_stream_end
  tool_execute_after
  tool_execute_before
)

# ── Run audit inside container (single exec, fast) ────────────────────────────

AUDIT_SCRIPT='
PLUGIN="'"$PLUGIN"'"
PROFILE="'"$PROFILE"'"
LEGACY="'"$LEGACY"'"

for hook in '"${HOOKS[*]}"'; do
  # Collect all unique .py filenames across all three paths
  all_files=$(
    { ls "$PLUGIN/$hook/"*.py 2>/dev/null; ls "$PROFILE/$hook/"*.py 2>/dev/null; ls "$LEGACY/$hook/"*.py 2>/dev/null; } \
    | xargs -I{} basename {} 2>/dev/null | sort -u
  )

  for name in $all_files; do
    in_plugin=false;  plugin_sum=""
    in_profile=false; profile_sum=""
    in_legacy=false;  legacy_sum=""

    [ -f "$PLUGIN/$hook/$name"  ] && { in_plugin=true;  plugin_sum=$(md5sum "$PLUGIN/$hook/$name"  | cut -d" " -f1); }
    [ -f "$PROFILE/$hook/$name" ] && { in_profile=true; profile_sum=$(md5sum "$PROFILE/$hook/$name" | cut -d" " -f1); }
    [ -f "$LEGACY/$hook/$name"  ] && { in_legacy=true;  legacy_sum=$(md5sum "$LEGACY/$hook/$name"  | cut -d" " -f1); }

    if $in_profile && $in_plugin; then
      if [ "$profile_sum" = "$plugin_sum" ]; then
        echo "SHADOW-SAME|$hook/$name|$profile_sum"
      else
        echo "CONFLICT|$hook/$name|profile:$profile_sum|plugin:$plugin_sum"
      fi
    elif $in_profile && ! $in_plugin; then
      echo "PROFILE-ONLY|$hook/$name|$profile_sum"
    elif $in_plugin && ! $in_profile; then
      echo "PLUGIN-ONLY|$hook/$name|$plugin_sum"
    fi

    # Legacy path — always report separately if present
    if $in_legacy; then
      if ! $in_profile && ! $in_plugin; then
        echo "LEGACY-ONLY|$hook/$name|$legacy_sum"
      elif $in_profile && [ "$legacy_sum" != "$profile_sum" ]; then
        echo "LEGACY-STALE|$hook/$name|legacy:$legacy_sum|active:$profile_sum"
      elif $in_plugin && ! $in_profile && [ "$legacy_sum" != "$plugin_sum" ]; then
        echo "LEGACY-STALE|$hook/$name|legacy:$legacy_sum|active:$plugin_sum"
      fi
    fi
  done
done
'

RAW=$(_exec bash -c "$AUDIT_SCRIPT" 2>/dev/null)

# ── Parse and display ─────────────────────────────────────────────────────────

if [ "$JSON_MODE" = true ]; then
  echo '{"container":"'"$CONTAINER"'","entries":['
  first=true
  while IFS='|' read -r category path rest; do
    [ -z "$category" ] && continue
    [ "$first" = false ] && echo ","
    echo -n "  {\"category\":\"$category\",\"path\":\"$path\",\"detail\":\"$rest\"}"
    first=false
  done <<< "$RAW"
  echo ""
  echo "]}"
  exit 0
fi

MODE_LABEL="$MODE"
[ "$MODE" = "option3" ] && MODE_LABEL="option3 (profile-canonical)"
log_header "Exocortex Deployment Audit — $CONTAINER  [mode: $MODE_LABEL]"

CONFLICT=0; PLUGIN_STALE=0; SHADOW=0; PLUGIN_ONLY=0; PROFILE_ONLY=0; LEGACY_ONLY=0; LEGACY_STALE=0

while IFS='|' read -r category path rest; do
  [ -z "$category" ] && continue
  case "$category" in
    CONFLICT)
      if [ "$MODE" = "option3" ]; then
        log_plugin_stale "$path  (plugin stale — profile is current, expected under Option 3)"
        PLUGIN_STALE=$((PLUGIN_STALE+1))
      else
        log_conflict "$path  ($rest)"
        CONFLICT=$((CONFLICT+1))
      fi
      ;;
    SHADOW-SAME)   log_same "$path"; SHADOW=$((SHADOW+1)) ;;
    PLUGIN-ONLY)   log_plugin "$path  (deployment gap — not in profile path)"; PLUGIN_ONLY=$((PLUGIN_ONLY+1)) ;;
    PROFILE-ONLY)  log_profile "$path"; PROFILE_ONLY=$((PROFILE_ONLY+1)) ;;
    LEGACY-ONLY)   log_legacy_only "$path  (orphaned — not in profile or plugin)"; LEGACY_ONLY=$((LEGACY_ONLY+1)) ;;
    LEGACY-STALE)  log_legacy_stale "$path  (legacy exists but active version differs)"; LEGACY_STALE=$((LEGACY_STALE+1)) ;;
  esac
done <<< "$RAW"

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
log_header "Summary"

if [ "$MODE" = "option3" ]; then
  [ "$PLUGIN_STALE"  -gt 0 ] && echo -e "  ${DIM}PLUGIN-STALE : $PLUGIN_STALE  (plugin has stale copy, profile wins — expected under Option 3)${NC}"
  [ "$PROFILE_ONLY"  -gt 0 ] && echo -e "  ${YELLOW}PROFILE-ONLY : $PROFILE_ONLY  (correct under Option 3 — extension in profile only)${NC}"
  [ "$PLUGIN_ONLY"   -gt 0 ] && echo -e "  ${RED}PLUGIN-ONLY  : $PLUGIN_ONLY  (deployment gap — extension only at lower-priority path)${NC}"
  [ "$LEGACY_ONLY"   -gt 0 ] && echo -e "  ${RED}LEGACY-ONLY  : $LEGACY_ONLY  (ephemeral path only — will be lost on container rebuild)${NC}"
  [ "$LEGACY_STALE"  -gt 0 ] && echo -e "  ${YELLOW}LEGACY-STALE : $LEGACY_STALE  (legacy differs from active version — likely safe to ignore)${NC}"
  [ "$SHADOW"        -gt 0 ] && echo -e "  ${DIM}SHADOW-SAME  : $SHADOW  (identical copies in both paths — harmless redundancy)${NC}"
  echo ""
  ISSUES=$((PLUGIN_ONLY + LEGACY_ONLY))
  if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}PASS — no deployment gaps or legacy orphans.${NC}"
    echo ""
    echo "  Profile path is authoritative for all extensions."
    echo "  PLUGIN-STALE ($PLUGIN_STALE) = plugin has old copies; profile wins. No action needed."
    echo "  PROFILE-ONLY ($PROFILE_ONLY) = extensions not in plugin path. Correct under Option 3."
    exit 0
  else
    echo -e "${RED}${BOLD}FAIL — $ISSUES issue(s) need remediation.${NC}"
    echo ""
    if [ "$PLUGIN_ONLY" -gt 0 ]; then
      echo "  PLUGIN-ONLY: extension only in lower-priority plugin path."
      echo "  Fix: ensure install_exocortex_profile.sh deploys this file to the profile path."
    fi
    if [ "$LEGACY_ONLY" -gt 0 ]; then
      echo "  LEGACY-ONLY: extensions in ephemeral /a0/python/extensions/ will be lost on container rebuild."
      echo "  Fix: upstream to repo and add to install_exocortex_profile.sh."
    fi
    exit 1
  fi
else
  [ "$CONFLICT"      -gt 0 ] && echo -e "  ${RED}CONFLICT     : $CONFLICT  (profile wins — running version ≠ install script)${NC}"
  [ "$PROFILE_ONLY"  -gt 0 ] && echo -e "  ${YELLOW}PROFILE-ONLY : $PROFILE_ONLY  (loading but not managed by install script — audit needed)${NC}"
  [ "$LEGACY_ONLY"   -gt 0 ] && echo -e "  ${RED}LEGACY-ONLY  : $LEGACY_ONLY  (ephemeral path only — will be lost on container rebuild)${NC}"
  [ "$LEGACY_STALE"  -gt 0 ] && echo -e "  ${YELLOW}LEGACY-STALE : $LEGACY_STALE  (legacy differs from active version — likely safe to ignore)${NC}"
  [ "$PLUGIN_ONLY"   -gt 0 ] && echo -e "  ${GREEN}PLUGIN-ONLY  : $PLUGIN_ONLY  (new extensions, loading correctly from plugin path)${NC}"
  [ "$SHADOW"        -gt 0 ] && echo -e "  ${DIM}SHADOW-SAME  : $SHADOW  (identical copies in both paths — harmless redundancy)${NC}"
  echo ""
  ISSUES=$((CONFLICT + LEGACY_ONLY))
  if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}PASS — no conflicts or legacy orphans.${NC}"
    echo ""
    echo "  Profile path is authoritative for all active extensions."
    echo "  PROFILE-ONLY count ($PROFILE_ONLY) requires manual audit to confirm intent."
    exit 0
  else
    echo -e "${RED}${BOLD}FAIL — $ISSUES issue(s) need remediation.${NC}"
    echo ""
    if [ "$CONFLICT" -gt 0 ]; then
      echo "  CONFLICT: running version ≠ install script version."
      echo "  Fix (Option 3): update install_exocortex_profile.sh to deploy to profile path."
      echo "  Quick fix: docker cp the repo source directly to the profile path."
    fi
    if [ "$LEGACY_ONLY" -gt 0 ]; then
      echo "  LEGACY-ONLY: extensions in ephemeral /a0/python/extensions/ will be lost on container rebuild."
      echo "  Fix: upstream to repo and add to install_exocortex_profile.sh."
    fi
    exit 1
  fi
fi
