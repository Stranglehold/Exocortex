#!/bin/bash
# install_skills.sh
# Deploys skills from the Exocortex repo to /a0/usr/skills/ (persistent user space).
# Three sources, applied in order (later sources win on conflict):
#
#   agent_skills/   — skills the agent created and we've verified; restored on every
#                     fresh container so the agent starts with its accumulated library
#   skills/         — Exocortex-maintained overrides (e.g. create-skill path fix)
#
# On live (non-fresh) containers, also migrates any new agent-created skills that
# landed in the ephemeral /a0/skills/ path and aren't yet in the repo.
#
# Safe to re-run at any time (idempotent).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SKILLS_SRC="$SCRIPT_DIR/agent_skills"
OVERRIDE_SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="/a0/usr/skills"
EPHEMERAL_SKILLS="/a0/skills"
BACKUP_DIR="$SKILLS_DST/.hardening_originals"

mkdir -p "$SKILLS_DST"

# ── Helper: install a directory of skills ─────────────────────────────────────

install_skills_dir() {
  local src="$1"
  local label="$2"
  local installed=0

  [ -d "$src" ] || return 0

  echo "$label"
  for skill_src_dir in "$src"/*/; do
    [ -d "$skill_src_dir" ] || continue
    skill_name="$(basename "$skill_src_dir")"
    skill_dst_dir="$SKILLS_DST/$skill_name"
    backup_skill_dir="$BACKUP_DIR/$skill_name"

    if [ ! -f "$skill_src_dir/SKILL.md" ]; then
      echo "  SKIP: $skill_name (no SKILL.md)"
      continue
    fi

    # Back up existing skill if not already backed up
    if [ -d "$skill_dst_dir" ] && [ ! -d "$backup_skill_dir" ]; then
      mkdir -p "$backup_skill_dir"
      cp -r "$skill_dst_dir/." "$backup_skill_dir/"
    fi

    mkdir -p "$skill_dst_dir"
    cp -r "$skill_src_dir/." "$skill_dst_dir/"
    echo "  Installed: $skill_name"
    installed=$((installed + 1))
  done

  echo "  ($installed skill(s) from $label)"
}

# ── Step 1: Agent-verified skills (fresh-container baseline) ──────────────────

install_skills_dir "$AGENT_SKILLS_SRC" "Agent skills (verified library)"

# ── Step 2: Exocortex overrides ───────────────────────────────────────────────

install_skills_dir "$OVERRIDE_SKILLS_SRC" "Exocortex skill overrides"

# ── Step 3: Migrate any new ephemeral skills (live containers only) ───────────
# Picks up skills the agent created since the last install that aren't in the
# repo yet. On a fresh container /a0/skills/ won't exist so this is a no-op.

if [ -d "$EPHEMERAL_SKILLS" ]; then
  echo "Migrating new ephemeral skills (/a0/skills/ → /a0/usr/skills/)..."
  migrated=0
  for ephemeral_dir in "$EPHEMERAL_SKILLS"/*/; do
    [ -d "$ephemeral_dir" ] || continue
    skill_name="$(basename "$ephemeral_dir")"
    [ "$skill_name" = ".hardening_originals" ] && continue
    persistent_dir="$SKILLS_DST/$skill_name"
    if [ ! -d "$persistent_dir" ]; then
      cp -r "$ephemeral_dir" "$persistent_dir"
      echo "  Migrated: $skill_name"
      migrated=$((migrated + 1))
    fi
  done
  [ "$migrated" -gt 0 ] && echo "  Migrated $migrated new skill(s)."
  [ "$migrated" -eq 0 ] && echo "  No new skills to migrate."
fi

echo ""
echo "Skills installed to: $SKILLS_DST"
echo "Backups at:          $BACKUP_DIR"
