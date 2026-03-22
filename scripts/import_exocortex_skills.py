#!/usr/bin/env python3
"""
import_exocortex_skills.py — Exocortex → Agent Zero Skills Import Adapter
==========================================================================

Reads Exocortex procedural skill files from EXOCORTEX_SKILLS_DIR and creates
proper Agent Zero SKILL.md files in A0_SKILLS_DIR, making all Exocortex skills
available via `skills_tool list` and `skills_tool load` in any A0 container.

Usage (inside container):
    python3 /a0/usr/Exocortex/scripts/import_exocortex_skills.py

Usage (from host, dry-run):
    python3 scripts/import_exocortex_skills.py --dry-run

Agent Zero skill format (A0_SKILLS_DIR/<slug>/SKILL.md):
    ---
    name: <display name>
    description: <one-line trigger description>
    version: 1.0
    author: Exocortex
    tags: [exocortex, procedural]
    triggers: ["<trigger description>"]
    ---

    <original skill content>

The adapter:
  - Skips files without parseable trigger metadata (specs, design notes, etc.)
  - Skips files that already have an up-to-date copy in A0_SKILLS_DIR
  - Never modifies the original Exocortex skill files
  - Idempotent: safe to run repeatedly

Log tag: [SKILL-IMPORT]
"""

import argparse
import os
import re
import sys
import textwrap

# ── Paths ────────────────────────────────────────────────────────────────────

EXOCORTEX_SKILLS_DIR = "/a0/usr/Exocortex/skills"
A0_SKILLS_DIR        = "/a0/usr/skills"

# Files to skip when scanning EXOCORTEX_SKILLS_DIR
SKILLS_EXCLUDE = {"skills_index.md", "readme.md", "index.md"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    """Convert display name to filesystem slug: 'L3 Spec Writing' → 'l3-spec-writing'."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _norm(name: str) -> str:
    """Normalize for deduplication."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _parse_skill_file(path: str, fallback_id: str) -> dict:
    """
    Extract skill metadata from an Exocortex .md file.

    Returns dict with keys: name, description, has_metadata, content
    Returns None if the file is not a skill (no structured trigger metadata).
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    name = ""
    description = ""

    # ── YAML field extraction (handles frontmatter anywhere in file) ──────────
    fm_name_m = re.search(r"^name:\s*(.+)",        content, re.MULTILINE)
    fm_desc_m = re.search(r"^description:\s*(.+)", content, re.MULTILINE)
    fm_trig_m = re.search(r"^triggers:\s*(.+)",    content, re.MULTILINE)

    if fm_name_m:
        name = fm_name_m.group(1).strip().strip("\"'")
    if fm_desc_m:
        description = fm_desc_m.group(1).strip().strip("\"'")
    elif fm_trig_m and not description:
        items = re.findall(r'"([^"]+)"', fm_trig_m.group(1))
        if items:
            description = items[0]

    # ── Heading-based name extraction ─────────────────────────────────────────
    if not name:
        heading = re.search(r"^#+\s+(?:Skill:\s+)?(.+)", content, re.MULTILINE)
        if heading:
            name = heading.group(1).strip()

    # ── ## Trigger section content ────────────────────────────────────────────
    if not description:
        trigger_section = re.search(
            r"^#{1,3}\s+Trigger\s*\n+(.+?)(?=\n#{1,3}\s|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        if trigger_section:
            for line in trigger_section.group(1).splitlines():
                line = line.strip()
                if line and not line.startswith(("#", ">", "---", "|")):
                    description = line
                    break

    # ── Body text fallback ────────────────────────────────────────────────────
    if not description:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(("#", ">", "---", "|", "!", "`", "*")):
                continue
            if re.match(r"^\w[\w_-]*:\s", line):
                continue
            description = line
            break

    # ── Require structured metadata to qualify as a skill ────────────────────
    has_fm_desc       = bool(fm_desc_m or (fm_trig_m and description))
    has_trigger_sec   = bool(re.search(r"^#{1,3}\s+Trigger\s*\n", content, re.MULTILINE))
    has_skill_heading = bool(re.search(r"^#+\s+Skill:", content, re.MULTILINE))
    if not has_fm_desc and not has_trigger_sec and not has_skill_heading:
        return None

    # ── Name cleanup ──────────────────────────────────────────────────────────
    if not name:
        stem = os.path.basename(fallback_id).replace(".md", "")
        name = stem.replace("_", " ").replace("-", " ").title()
    else:
        if name == name.lower() and re.search(r"[-_]", name):
            name = name.replace("-", " ").replace("_", " ").title()

    return {
        "name":         name,
        "description":  textwrap.shorten(description, width=120, placeholder="..."),
        "has_metadata": bool(fm_desc_m or fm_name_m),
        "content":      content,
        "source_path":  path,
    }


def _build_skill_md(info: dict) -> str:
    """
    Build the A0-format SKILL.md content for the given parsed skill info.

    If the source already has YAML frontmatter, strip it and prepend a clean
    A0-format header. If it doesn't, prepend one.
    """
    name        = info["name"]
    description = info["description"]
    content     = info["content"]

    # Strip any existing frontmatter blocks (--- ... ---) from content
    # so we don't double-inject them.
    content_clean = re.sub(
        r"^---\n.*?\n---\n*",
        "",
        content,
        flags=re.DOTALL | re.MULTILINE,
    ).lstrip()

    # Also strip the attribution blockquote if present (context-engineering skills)
    content_clean = re.sub(
        r"^(>.*\n)+\n*",
        "",
        content_clean,
    ).lstrip()

    # Build clean A0 YAML frontmatter
    # Escape any double-quotes in description
    desc_safe = description.replace('"', '\\"')
    frontmatter = (
        f"---\n"
        f'name: "{name}"\n'
        f'description: "{desc_safe}"\n'
        f"version: 1.0\n"
        f"author: Exocortex\n"
        f"tags: [exocortex, procedural]\n"
        f'triggers: ["{desc_safe}"]\n'
        f"---\n\n"
    )

    return frontmatter + content_clean


# ── Main ─────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, verbose: bool = False) -> None:
    if not os.path.isdir(EXOCORTEX_SKILLS_DIR):
        print(f"[SKILL-IMPORT] Source directory not found: {EXOCORTEX_SKILLS_DIR}")
        sys.exit(1)

    if not dry_run:
        os.makedirs(A0_SKILLS_DIR, exist_ok=True)

    created = 0
    updated = 0
    skipped = 0

    for fname in sorted(os.listdir(EXOCORTEX_SKILLS_DIR)):
        if not fname.endswith(".md"):
            continue
        if fname.lower() in SKILLS_EXCLUDE:
            continue

        path = os.path.join(EXOCORTEX_SKILLS_DIR, fname)
        info = _parse_skill_file(path, fname)

        if info is None:
            if verbose:
                print(f"[SKILL-IMPORT] skip (no skill metadata): {fname}")
            skipped += 1
            continue

        slug     = _slug(info["name"])
        dest_dir = os.path.join(A0_SKILLS_DIR, slug)
        dest     = os.path.join(dest_dir, "SKILL.md")
        skill_md = _build_skill_md(info)

        # Check if already up to date
        if os.path.exists(dest):
            with open(dest, encoding="utf-8") as f:
                existing = f.read()
            if existing == skill_md:
                if verbose:
                    print(f"[SKILL-IMPORT] up-to-date: {slug}/")
                skipped += 1
                continue
            action = "update"
        else:
            action = "create"

        if dry_run:
            print(f"[SKILL-IMPORT] would {action}: {slug}/SKILL.md  ({info['name']})")
            if action == "create":
                created += 1
            else:
                updated += 1
            continue

        os.makedirs(dest_dir, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(skill_md)

        if action == "create":
            created += 1
            print(f"[SKILL-IMPORT] created: {slug}/SKILL.md  ({info['name']})")
        else:
            updated += 1
            print(f"[SKILL-IMPORT] updated: {slug}/SKILL.md  ({info['name']})")

    total = created + updated
    print(
        f"[SKILL-IMPORT] done — {created} created, {updated} updated, {skipped} skipped"
        f"{' (dry-run)' if dry_run else ''}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import Exocortex skills into Agent Zero usr/skills/ format."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be created/updated without writing files.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show skipped files too.",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, verbose=args.verbose)
