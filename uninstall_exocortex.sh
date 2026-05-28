#!/bin/bash
# uninstall_exocortex.sh
# Cleanly revert an Exocortex install, returning Agent-Zero to working stock state.
#
# This is the inverse of install_all.sh. It is designed to be SAFE and REVERSIBLE:
#   - Dry-run by DEFAULT: prints the full plan and changes nothing. Use --apply to execute.
#   - Backs up the entire footprint to a timestamped tarball BEFORE deleting (so the
#     uninstall is itself reversible — restore with: tar xzf <backup> -C / ).
#   - Restores A0 core files from A0's OWN git tree (git checkout), which is more
#     complete and version-correct than the installers' partial .fw_originals backups.
#   - NEVER touches user/model config or agent data (see PRESERVE list below).
#
# Runs INSIDE the container (all operations are local: rm, git, supervisord). If invoked
# from the host it re-execs itself inside $CONTAINER via docker cp + docker exec.
#
# Usage:
#   bash uninstall_exocortex.sh                  # dry-run (default) against $CONTAINER
#   bash uninstall_exocortex.sh --apply          # execute
#   CONTAINER=nifty_panini bash uninstall_exocortex.sh --apply
#   bash uninstall_exocortex.sh --apply --remove-repo   # also remove the /a0/usr/Exocortex repo clone
#   bash uninstall_exocortex.sh --apply --no-backup     # skip the safety tarball (not recommended)
#
# What is PRESERVED (never removed/altered):
#   /a0/usr/plugins/_model_config   (model/provider config — e.g. DeepSeek; user's domain)
#   /a0/usr/plugins/{_browser,_office,_whisper_stt}   (A0 core plugins)
#   /a0/usr/settings.json, /a0/usr/secrets.env        (A0 settings / credentials)
#   /a0/usr/{chats,knowledge,logs,projects,scheduler,workdir}   (A0 + agent data)
#   /a0/usr/memory/default            (A0's default memory area; only OUR config files are scrubbed)

set -e

APPLY=false
DO_BACKUP=true
REMOVE_REPO=false
for arg in "$@"; do
  case "$arg" in
    --apply)        APPLY=true ;;
    --no-backup)    DO_BACKUP=false ;;
    --remove-repo)  REMOVE_REPO=true ;;
    --dry-run)      APPLY=false ;;
  esac
done

# ── Host → container re-exec ──────────────────────────────────────────────────
# If not running inside a container, copy this script into $CONTAINER and re-run it
# there. All teardown ops are local-to-container, so in-container is the clean mode.
_in_container=false
if [ -f "/.dockerenv" ] || grep -qE "docker|lxc|containerd" /proc/1/cgroup 2>/dev/null; then
  _in_container=true
fi

if [ "$_in_container" = false ]; then
  CONTAINER="${CONTAINER:-exocortex_v16}"
  echo "[UNINSTALL] Host mode — re-exec inside container: $CONTAINER"
  if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "[UNINSTALL] ERROR: container '$CONTAINER' not found. Set CONTAINER=<name>."
    exit 1
  fi
  _self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  docker cp "$_self" "$CONTAINER:/tmp/uninstall_exocortex.sh"
  # Forward the original args verbatim.
  MSYS_NO_PATHCONV=1 docker exec "$CONTAINER" bash /tmp/uninstall_exocortex.sh "$@"
  exit $?
fi

# ── From here: running INSIDE the container ───────────────────────────────────

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "$1"; }
plan() { echo -e "${CYAN}  [plan]${NC} $1"; }
doit() { echo -e "${GREEN}  [done]${NC} $1"; }
warn() { echo -e "${YELLOW}  [warn]${NC} $1"; }

A0=/a0
REPO="${REPO:-/a0/usr/Exocortex}"          # where install_all.sh lives in-container
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/a0/usr/exocortex_uninstall_backup_${TS}.tgz"

log "${BOLD}${CYAN}━━━ Exocortex Uninstall ━━━${NC}"
if [ "$APPLY" = true ]; then
  log "  Mode: ${RED}${BOLD}APPLY (changes will be made)${NC}"
else
  log "  Mode: ${GREEN}DRY-RUN${NC} (no changes — pass --apply to execute)"
fi
log "  A0 root: $A0    Repo: $REPO"
echo ""

# Helper: remove a path (dir or file) with dry-run + existence awareness.
rm_path() {
  local p="$1"
  if [ ! -e "$p" ]; then return 0; fi
  if [ "$APPLY" = true ]; then rm -rf "$p"; doit "removed $p"; else plan "rm -rf $p"; fi
}

# ── Phase 0: enumerate the deployed profile-extension files from the repo ─────
# Mirror install_exocortex_profile.sh: for each hook, our files land in BOTH
# /a0/usr/agents/agent0/extensions/<hook>/  and  .../python/<hook>/ .
HOOKS="before_main_llm_call error_format hist_add_before message_loop_end \
message_loop_prompts_after monologue_end reasoning_stream reasoning_stream_end \
response_stream_chunk response_stream_end tool_execute_after tool_execute_before"
PROF=/a0/usr/agents/agent0/extensions

# ── Phase 1: safety backup of the whole footprint ─────────────────────────────
log "${BOLD}Phase 1 — Backup footprint${NC}"
if [ "$DO_BACKUP" = true ]; then
  # Collect the paths that exist so tar doesn't error on missing ones.
  BK_PATHS=()
  for p in \
    "$PROF" \
    /a0/usr/plugins/exocortex /a0/usr/plugins/oss /a0/usr/plugins/swarmfish \
    /a0/usr/oss /a0/usr/swarmfish /a0/usr/ontology /a0/usr/organizations \
    /a0/usr/artifact_templates /a0/usr/memory/classification_config.json \
    /a0/python ; do
    [ -e "$p" ] && BK_PATHS+=("$p")
  done
  # Also snapshot A0 core files we will revert (so the backup is complete).
  if [ "$APPLY" = true ]; then
    ( cd "$A0" && git diff > "/tmp/a0_core_patches_${TS}.diff" 2>/dev/null ) || true
    [ -f "/tmp/a0_core_patches_${TS}.diff" ] && BK_PATHS+=("/tmp/a0_core_patches_${TS}.diff")
    tar czf "$BACKUP" "${BK_PATHS[@]}" 2>/dev/null && doit "backup → $BACKUP ($(du -h "$BACKUP" | cut -f1))"
  else
    plan "tar czf $BACKUP  (${#BK_PATHS[@]} paths)  + git diff of A0 core → /tmp/a0_core_patches_${TS}.diff"
  fi
else
  warn "backup skipped (--no-backup)"
fi
echo ""

# ── Phase 2: stop idle_watch daemon + remove supervisord program (if present) ─
log "${BOLD}Phase 2 — Stop daemons${NC}"
SVD_CONF="$(grep -rl 'program:idle_watch' /etc/supervisor* 2>/dev/null | head -1 || true)"
if [ -n "$SVD_CONF" ]; then
  if [ "$APPLY" = true ]; then
    supervisorctl stop idle_watch 2>/dev/null || true
    # Strip the [program:idle_watch] block (from its header to the next blank line / next [program).
    python3 - "$SVD_CONF" << 'PY'
import sys,re
p=sys.argv[1]; s=open(p).read()
s=re.sub(r'\n?\[program:idle_watch\].*?(?=\n\[program:|\Z)', '\n', s, flags=re.S)
open(p,'w').write(s)
PY
    supervisorctl reread 2>/dev/null || true; supervisorctl update 2>/dev/null || true
    doit "stopped idle_watch + removed [program:idle_watch] from $SVD_CONF"
  else
    plan "supervisorctl stop idle_watch; strip [program:idle_watch] from $SVD_CONF; reread/update"
  fi
else
  warn "no idle_watch supervisord program found — skipping"
fi
echo ""

# ── Phase 3: restore A0 core files (git) + remove our additions in tracked dirs ─
log "${BOLD}Phase 3 — Restore A0 core (git checkout) + remove tracked-dir additions${NC}"
if [ -d "$A0/.git" ] || ( cd "$A0" && git rev-parse --git-dir >/dev/null 2>&1 ); then
  MODIFIED="$(cd "$A0" && git ls-files -m 2>/dev/null || true)"
  if [ -n "$MODIFIED" ]; then
    if [ "$APPLY" = true ]; then
      ( cd "$A0" && echo "$MODIFIED" | xargs -r git checkout -- )
      doit "git checkout restored $(echo "$MODIFIED" | wc -l) modified core file(s)"
    else
      plan "git checkout -- (restore $(echo "$MODIFIED" | wc -l) modified core files):"
      echo "$MODIFIED" | sed 's/^/         /'
    fi
  else
    warn "no modified tracked files — A0 core already pristine"
  fi
else
  warn "/a0 is not a git tree — falling back to installer backups (.fw_originals / .prompt_patch_originals)"
  for bdir in "$A0/prompts/.fw_originals" "$A0/prompts/.prompt_patch_originals"; do
    if [ -d "$bdir" ]; then
      for f in "$bdir"/*; do
        [ -f "$f" ] || continue
        dest="$A0/prompts/$(basename "$f")"
        if [ "$APPLY" = true ]; then cp -p "$f" "$dest"; doit "restored $dest"; else plan "cp $f → $dest"; fi
      done
    fi
  done
fi

# Untracked additions we created inside A0's tracked dirs (NOT user data — our files only).
for p in \
  "$A0/api/artifacts_list.py" "$A0/api/idle_control.py" "$A0/api/office_feed.py" \
  "$A0/helpers/provider_interface.py" \
  "$A0/prompts/agent.system.main.communication_protocol.md" \
  "$A0/prompts/agent.system.main.role.py" \
  "$A0/prompts/browser_agent.system.md" \
  "$A0/prompts/fw.code.pause_dialog.md" \
  "$A0/prompts/.fw_originals" "$A0/prompts/.prompt_patch_originals" \
  "$A0/webui/js/themes.js" "$A0/webui/js/theme-editor.js" "$A0/webui/office.html" \
  "$A0/python" ; do
  rm_path "$p"
done
# OSS / SWARMFISH / investigation tool stubs A0 auto-discovers under /a0/tools/.
if [ -d "$A0/tools" ]; then
  for f in "$A0"/tools/oss*.py "$A0"/tools/swarmfish*.py "$A0/tools/investigation_tools.py"; do
    [ -e "$f" ] && rm_path "$f"
  done
fi
echo ""

# ── Phase 4: remove Exocortex-owned plugin + /a0/usr dirs ─────────────────────
log "${BOLD}Phase 4 — Remove Exocortex-owned dirs${NC}"
rm_path /a0/usr/plugins/exocortex
rm_path /a0/usr/plugins/oss
rm_path /a0/usr/plugins/swarmfish
rm_path /a0/usr/oss            # OSS runtime DB/FAISS (backed up in Phase 1)
rm_path /a0/usr/swarmfish      # SWARMFISH runtime DB  (backed up in Phase 1)
rm_path /a0/usr/ontology
rm_path /a0/usr/organizations
rm_path /a0/usr/artifact_templates
echo ""

# ── Phase 5: remove profile-path extensions (both <hook>/ and python/<hook>/) ──
log "${BOLD}Phase 5 — Remove profile extensions${NC}"
# Installer-created backup dir (holds copies our extensions installer saved before deploys).
# Named for the project's old name "Agent-Zero-Hardening" — A0 never creates this. Ours.
rm_path "$PROF/.hardening_originals"
if [ -d "$REPO/extensions" ]; then
  removed=0
  for hook in $HOOKS; do
    for src in "$REPO/extensions/$hook" "$REPO/extensions/python/$hook"; do
      [ -d "$src" ] || continue
      for f in "$src"/*.py "$src"/*.json; do
        [ -f "$f" ] || continue
        name="$(basename "$f")"
        for dest in "$PROF/$hook/$name" "$PROF/python/$hook/$name"; do
          if [ -f "$dest" ]; then
            if [ "$APPLY" = true ]; then rm -f "$dest"; removed=$((removed+1)); else plan "rm $dest"; fi
          fi
        done
      done
    done
  done
  [ "$APPLY" = true ] && doit "removed $removed profile extension file(s)"
  # Clear pycache + drop now-empty hook dirs we created.
  if [ "$APPLY" = true ]; then
    find "$PROF" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    find "$PROF" -depth -type d -empty -delete 2>/dev/null || true
  fi
else
  warn "repo extensions tree not found at $REPO/extensions — cannot derive extension list."
  warn "  (Re-run with REPO=<path-to-exocortex-repo> if the repo lives elsewhere.)"
fi
echo ""

# ── Phase 6: scrub Exocortex config files from SHARED dirs (additive, inert) ──
log "${BOLD}Phase 6 — Scrub Exocortex config from shared dirs${NC}"
rm_path /a0/usr/memory/classification_config.json   # only OUR file; /a0/usr/memory/default is A0's — preserved
echo ""

# ── Phase 7: optionally remove the repo clone (preserving agent runtime) ──────
log "${BOLD}Phase 7 — Repo clone${NC}"
if [ "$REMOVE_REPO" = true ]; then
  # Preserve any agent-authored / runtime content that may live inside the repo dir.
  for keep in field-reports office wiki self-improvement journals; do
    if [ -e "$REPO/$keep" ]; then
      warn "preserving agent runtime: $REPO/$keep  (NOT removed — move to /a0/usr/workdir/workspace if desired)"
    fi
  done
  if [ "$APPLY" = true ]; then
    # Remove repo contents except the preserved runtime dirs.
    for entry in "$REPO"/* "$REPO"/.[!.]*; do
      [ -e "$entry" ] || continue
      base="$(basename "$entry")"
      case "$base" in
        field-reports|office|wiki|self-improvement|journals) continue ;;
      esac
      rm -rf "$entry"
    done
    doit "removed repo clone contents (agent runtime preserved)"
  else
    plan "remove $REPO/* except {field-reports,office,wiki,self-improvement,journals}"
  fi
else
  warn "repo clone at $REPO left in place (inert once extensions/plugins are gone). Use --remove-repo to remove."
fi
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
log "${BOLD}${CYAN}━━━ Summary ━━━${NC}"
if [ "$APPLY" = true ]; then
  log "  ${GREEN}Uninstall applied.${NC}"
  [ "$DO_BACKUP" = true ] && log "  Backup: $BACKUP  (restore: tar xzf <backup> -C / )"
  log "  PRESERVED: _model_config (model config), settings.json, secrets.env, chats, workdir, memory/default."
  log ""
  log "  ${BOLD}Restart the container (or run_ui) to load stock A0:${NC}"
  log "    docker restart <container>   # or: supervisorctl restart run_ui"
  log "  Verify A0 core is pristine:  docker exec <container> sh -c 'cd /a0 && git status --short'"
else
  log "  ${GREEN}Dry-run complete.${NC} No changes were made."
  log "  Re-run with ${BOLD}--apply${NC} to execute (a safety backup is taken first unless --no-backup)."
fi
