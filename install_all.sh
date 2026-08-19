#!/bin/bash
# install_all.sh
# Runs all hardening install scripts in correct dependency order.
# Safe to re-run at any time — all scripts are idempotent.
#
# Usage:
#   bash install_all.sh              Install all layers
#   bash install_all.sh --check-only Check for upstream conflicts only
#   bash install_all.sh --layer N    Install only layer N (1-6)
#
# Run from: /a0/usr/hardening/ (repo root)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=false
LAYER_ONLY=""
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --check-only)  CHECK_ONLY=true ;;
    --layer=*)     LAYER_ONLY="${arg#*=}" ;;
    --force)       FORCE=true ;;
  esac
done

# Default container target inherited by env-aware child scripts (oss_plugin,
# swarmfish_plugin, artifact_system, metacognitive, epistemic, write_guard…).
# In-container runs use the docker shim below, which ignores the name entirely;
# this only matters for host-side execution. Override with CONTAINER=... .
export CONTAINER="${CONTAINER:-exocortex_v16}"

# ── Color output ──────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_header()  { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}"; }
log_section() { echo -e "\n${YELLOW}  → $1${NC}"; }
log_ok()      { echo -e "${GREEN}    ✓ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}    ⚠ $1${NC}"; }
log_err()     { echo -e "${RED}    ✗ $1${NC}"; }
log_skip()    { echo -e "    ~ $1 (not found — skipped)"; }

# ── A0 version preflight ────────────────────────────────────────────────────
# The hardening stack patches A0 core files (patches/), so it is only verified
# against the A0 version recorded in ./A0_VERSION. Deploying onto a different
# A0 can silently revert A0 changes (incl. security fixes) where our patches
# overwrite files A0 has since changed. This gate fails loud on mismatch.
# Override with --force (e.g. during a deliberate, validated upgrade).
preflight_a0_version() {
  local pin_file="$SCRIPT_DIR/A0_VERSION"
  if [ ! -f "$pin_file" ]; then
    log_warn "No A0_VERSION pin file — skipping version check"
    return 0
  fi
  local pinned
  pinned="$(grep -vE '^\s*#|^\s*$' "$pin_file" | head -1 | tr -d '[:space:]')"
  local actual
  actual="$(docker exec "$CONTAINER" sh -c 'cd /a0 2>/dev/null && git describe --tags 2>/dev/null' 2>/dev/null | tr -d '[:space:]')"
  if [ -z "$actual" ]; then
    log_warn "Could not read container A0 version (pinned: $pinned) — proceeding unverified"
    return 0
  fi
  if [ "$actual" = "$pinned" ]; then
    log_ok "A0 version $actual matches pin"
    return 0
  fi
  if [ "$FORCE" = true ]; then
    log_warn "A0 version mismatch — container=$actual, pinned=$pinned (continuing: --force)"
    return 0
  fi
  log_err "A0 version mismatch — container=$actual, pinned=$pinned"
  log_err "This stack is verified only against $pinned. Deploying onto $actual is untested"
  log_err "and may revert A0 changes where our patches/ overwrite files A0 has changed."
  log_err "See docs/UPGRADE_A0.md for the staged upgrade procedure. Override with --force."
  exit 1
}

# ── Container detection & docker shim ─────────────────────────────────────────
# When running inside the Agent-Zero container, `docker` is not available.
# We create a lightweight shim that converts docker cp / docker exec into
# direct local operations. Child scripts are unchanged — they continue to
# call `docker cp` / `docker exec` normally.

_DOCKER_SHIM_DIR=""
_cleanup_shim() { [ -n "$_DOCKER_SHIM_DIR" ] && rm -rf "$_DOCKER_SHIM_DIR"; }

_in_container=false
if [ -f "/.dockerenv" ]; then
  _in_container=true
elif grep -qE "docker|lxc|containerd" /proc/1/cgroup 2>/dev/null; then
  _in_container=true
fi

if [ "$_in_container" = true ]; then
  _DOCKER_SHIM_DIR="$(mktemp -d)"
  trap _cleanup_shim EXIT

  cat > "$_DOCKER_SHIM_DIR/docker" << 'SHIM_EOF'
#!/bin/bash
# docker shim — intercepts docker cp / docker exec for in-container installs.
# Called by child install scripts that were written for host-side execution.
case "$1" in
  cp)
    shift
    src="$1"
    dst="$2"
    # Strip leading "container:" prefix (e.g. "agent-zero:/a0/..." → "/a0/...")
    src="${src##*:}"
    dst="${dst##*:}"
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    ;;
  exec)
    # docker exec <container> <cmd...> → run <cmd...> directly
    shift   # drop "exec"
    shift   # drop container name
    "$@"
    ;;
  *)
    echo "docker-shim: unsupported command '$1'" >&2
    exit 1
    ;;
esac
SHIM_EOF

  chmod +x "$_DOCKER_SHIM_DIR/docker"
  export PATH="$_DOCKER_SHIM_DIR:$PATH"
  log_warn "Running inside container — docker shim active (direct cp/exec mode)"
fi

# ── Layer registry ────────────────────────────────────────────────────────────
# Each entry: "LAYER_NUM|LABEL|SCRIPT_PATH"
# Multiple entries with same LAYER_NUM are sub-steps of that layer.

LAYERS=(
  "1|Framework message replacements      |fw-replacements/install_fw_replacements.sh"
  "1|Core file patches (JSON fallback)   |scripts/install_core_patches.sh"
  "2|Profile deployment (DEC-030)        |scripts/install_exocortex_profile.sh"
  "2|Extensions — retry + watchdog       |extensions/install_extensions.sh"
  "2|Extensions — failure tracker        |extensions/install_failure_tracker.sh"
  "2|Extensions — error comprehension   |scripts/install_error_comprehension.sh"
  "2|Extensions — tool fallback chain   |scripts/install_tool_fallback.sh"
  "2|Extensions — action boundary gate   |scripts/install_action_boundary.sh"
  "2|Extensions — meta-reasoning gate   |scripts/install_meta_gate.sh"
  "2|Extensions — organization kernel   |scripts/install_org_kernel.sh"
  "2|Extensions — supervisor loop       |scripts/install_supervisor_loop.sh"
  "3|Prompt patches                      |prompt-patches/install_prompt_patches.sh"
  "3|Personality loader                  |scripts/install_personalities.sh"
  "3|Communication protocol              |scripts/install_communication_protocol.sh"
  "4|Skills                              |install_skills.sh"
  "5|Translation layer (belief state BST)|translation-layer/install_translation_layer.sh"
  "5|Graph workflow engine              |scripts/install_graph_engine.sh"
  "6|A2A compatibility server           |scripts/install_a2a_server.sh"
  "7|Memory classification system       |scripts/install_memory_classification.sh"
  "8|Ontology layer                     |scripts/install_ontology.sh"
  "9|AgentEvolver self-improvement plugin|scripts/install_agentevolver.sh"
  "9|Sleep consolidation (Phases 1-4)   |scripts/install_sleep_consolidation.sh"
  "10|Document library (tools + catalog) |scripts/install_library.sh"
  "11|OSS V2 plugin (Intel tab + tools) |services/oss_plugin/install.sh"
  "11|SWARMFISH V2 plugin (committee)   |services/swarmfish_plugin/install.sh"
  "12|Idle engine + idle_watch daemon   |scripts/install_idle_engine.sh"
  "12|SearXNG academic-engine config    |services/searxng/install.sh"
  "13|Theme system (presets + editor)   |scripts/install_theme_editor.sh"
  "14|Metacognitive injection           |scripts/install_metacognitive_injection.sh"
  "14|Epistemic integrity layer         |scripts/install_epistemic_integrity.sh"
  "14|Write guard + validator           |scripts/install_write_guard.sh"
  "15|Artifact system                   |scripts/install_artifact_system.sh"
)

CHECK_SCRIPTS=(
  "fw-replacements/check_fw_upstream.sh"
  "extensions/check_extensions_upstream.sh"
  "prompt-patches/check_prompt_patches_upstream.sh"
  "check_skills_upstream.sh"
)

# ── Check-only mode ───────────────────────────────────────────────────────────

if [ "$CHECK_ONLY" = true ]; then
  log_header "Upstream Conflict Check"
  echo "  Comparing installed files against agent-zero upstream..."
  echo ""
  any_changed=0

  for script in "${CHECK_SCRIPTS[@]}"; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
      log_section "$script"
      bash "$SCRIPT_DIR/$script" || any_changed=1
    else
      log_skip "$script"
    fi
  done

  echo ""
  if [ "$any_changed" -eq 0 ]; then
    echo -e "${GREEN}No upstream conflicts. Safe to re-run install_all.sh.${NC}"
  else
    echo -e "${YELLOW}Conflicts detected above. Review diffs before reinstalling.${NC}"
  fi
  exit 0
fi

# ── Install mode ──────────────────────────────────────────────────────────────

log_header "Agent-Zero Hardening Layer — Full Install"
echo "  Source : $SCRIPT_DIR"
echo "  Target : /a0/"
[ -n "$LAYER_ONLY" ] && echo "  Mode   : Layer $LAYER_ONLY only"
echo ""

preflight_a0_version

failed=0
installed=0
skipped=0

for entry in "${LAYERS[@]}"; do
  layer_num="${entry%%|*}"
  rest="${entry#*|}"
  label="${rest%%|*}"
  label="$(echo "$label" | sed 's/[[:space:]]*$//')"   # trim trailing spaces
  script="${rest#*|}"

  # Filter if --layer=N was passed
  if [ -n "$LAYER_ONLY" ] && [ "$layer_num" != "$LAYER_ONLY" ]; then
    continue
  fi

  if [ ! -f "$SCRIPT_DIR/$script" ]; then
    log_skip "Layer $layer_num — $label"
    skipped=$((skipped + 1))
    continue
  fi

  log_section "Layer $layer_num — $label"

  if (cd "$SCRIPT_DIR/$(dirname "$script")" && bash "$(basename "$script")"); then
    log_ok "Completed"
    installed=$((installed + 1))
  else
    log_err "FAILED"
    failed=$((failed + 1))
  fi
done

# ── Deploy-time skill-frontmatter checkpoint (defense layer 3) ─────────────────
# Validate + repair any malformed SKILL.md introduced by imports/syncs, so freshly
# installed/updated skills are discoverable. Deterministic + idempotent; never fatal.
if [ -z "$LAYER_ONLY" ] && [ -f "$SCRIPT_DIR/scripts/normalize_skills.py" ]; then
  echo ""
  log_header "Skill frontmatter checkpoint"
  /opt/venv-a0/bin/python3 "$SCRIPT_DIR/scripts/normalize_skills.py" /a0/usr/skills --apply 2>/dev/null \
    | grep -E "already valid|fixed" || echo "  (normalizer skipped — A0 env unavailable)"
fi

# ── A0 core patches (re-applied after every A0 update) ────────────────────────
# A0 core carries a PTY/shell session leak: every AgentContext that runs
# code_execution allocates a PTY master + child shell that is NEVER closed
# (tty_session.py). One leaked handle per context; since every idle cycle makes a
# fresh context, that is one per cycle. Field-measured: 30 cycles / 17h -> 38
# handles, ~360 threads, then TOTAL DEADLOCK — A0's bounded worker pool is
# consumed and even GET /health stops answering. Observed twice (08-14, 08-18).
#
# The patch adds an idle reaper that calls the EXISTING (correct) close(). Safe
# because code_execution_tool rebuilds a terminated session on next use —
# verified: reaped shell, reused the same context, code_execution still worked.
#
# Idempotent, anchor-gated (refuses to apply if A0 changed the file), and
# reversible via --revert from the .exocortex-orig backup. REMOVE THIS STEP once
# upstream ships a fix. Full writeup: team-comms/kestrel-to-opus/pty_session_leak_20260818.md
if [ -z "$LAYER_ONLY" ] && [ -f "$SCRIPT_DIR/plugins/_exocortex/patches/patch_pty_session_leak.py" ]; then
  echo ""
  log_header "A0 core patch: PTY session leak"
  /opt/venv-a0/bin/python3 "$SCRIPT_DIR/plugins/_exocortex/patches/patch_pty_session_leak.py" \
    --apply --idle-seconds 600 --interval-seconds 120 2>/dev/null \
    | grep -E "APPLIED|already patched|ABORT|WARNING" \
    || echo "  (patch skipped — A0 env unavailable)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
log_header "Summary"
echo "  Completed : $installed"
[ "$skipped" -gt 0 ] && echo "  Skipped   : $skipped (scripts not found)"
[ "$failed"  -gt 0 ] && echo -e "  ${RED}Failed    : $failed${NC}"
echo ""

if [ "$failed" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}All layers installed successfully.${NC}"
  echo ""
  echo "  Deployment map:"
  echo "    Layer 1  fw-replacements   → /a0/prompts/
    Layer 1  core patches      → /a0/python/helpers/ + /a0/prompts/"
  echo "    Layer 2  profile (DEC-030) → /a0/usr/agents/agent0/extensions/ (persistent)"
  echo "    Layer 2  extensions        → /a0/python/extensions/ (legacy, shadowed by profile)"
  echo "    Layer 2  org kernel        → /a0/python/extensions/ + /a0/usr/organizations/"
  echo "    Layer 2  supervisor loop   → /a0/usr/agents/agent0/extensions/message_loop_end/"
  echo "    Layer 3  prompt-patches    → /a0/prompts/"
  echo "    Layer 3  personalities     → /a0/prompts/ + /a0/usr/personalities/"
  echo "    Layer 4  skills            → /a0/usr/skills/ (persistent; migrates /a0/skills/)"
  echo "    Layer 5  translation-layer → /a0/usr/agents/agent0/extensions/before_main_llm_call/"
  echo "    Layer 5  graph engine      → /a0/usr/agents/agent0/extensions/before_main_llm_call/"
  echo "    Layer 6  A2A server        → /a0/python/a2a_server/"
  echo "    Layer 7  memory classify   → /a0/usr/agents/agent0/extensions/monologue_end/ + /a0/usr/memory/"
  echo "    Layer 8  ontology layer    → /a0/usr/ontology/ + /a0/python/tools/"
  echo "    Layer 9  sleep consolidation → /a0/usr/Exocortex/ + profile tool_execute_after/"
  echo "    Layer 10 document library   → /a0/usr/library/ + /a0/python/tools/ + profile ext/"
  echo "    Note: Phase 2 will retire legacy /a0/python/extensions/ install scripts."
  echo ""
  echo "  Restart agent-zero or start a fresh chat to load all changes."
  echo "  A2A server: python -m a2a_server.run (port 8200)"
else
  echo -e "${RED}${BOLD}$failed step(s) failed. Review output above before continuing.${NC}"
  exit 1
fi
