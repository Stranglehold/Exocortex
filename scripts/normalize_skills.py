#!/usr/bin/env python3
"""
Skill frontmatter normalizer — deterministic repair + going-forward guard.

WHY: ~30% of the active skill library (26/88) was invisible because its YAML
frontmatter failed A0's validate_skill_md. Three root patterns, all from skill
AUTHORING (not the cycle-to-skill capture pipeline, which emits valid frontmatter):
  1. Generator bug: `description: '<truncated mid-sentence>` — unterminated quote
     + stub `tags: [TODO]` (shared author: Exocortex, version: 1.0).
  2. Unquoted special chars: descriptions with colons / embedded quotes / run-on
     `version:` fields → YAML "mapping values not allowed".
  3. No top frontmatter: file starts with `# Title`, YAML block missing.
Plus underscore names, one missing `name:`, and duplicate `divergent_*` dirs.

WHAT THIS DOES: for each INVALID skill, rebuild ONLY the frontmatter — never the
body. Preserve frontmatter when the YAML parses (fix name/description/position);
regenerate a minimal valid block when it's broken (name from the directory,
description salvaged from the broken field or the body's first line). Emits via
yaml.safe_dump (guaranteed-valid output). Idempotent: valid skills are left
untouched. Conservative: bails on a skill rather than risk mangling it.

Validity target (helpers.skills.validate_skill_md): `---` fence at top + parseable
YAML + name (1-64, ^[a-z0-9-]+$, no leading/trailing/double hyphen) + non-empty
description (<=1024). Triggers optional (preserved when cleanly present).

USAGE:
  python3 normalize_skills.py            # dry-run: report what would change
  python3 normalize_skills.py --apply    # write the fixes
  (skips /.hardening_originals/; reports duplicate divergent_* dirs but never deletes)
"""

import os
import re
import sys
import glob

sys.path.insert(0, "/a0/python")
sys.path.insert(0, "/a0")
import yaml  # noqa: E402
from pathlib import Path  # noqa: E402
from helpers import skills as sk  # noqa: E402

APPLY = "--apply" in sys.argv
# optional positional root (default the runtime skills dir); lets the same tool
# normalize the repo's source skills/ so they don't re-break the container on deploy
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
SKILLS_ROOT = _args[0] if _args else "/a0/usr/skills"
NAME_RE = re.compile(r"^[a-z0-9-]+$")


def slugify_name(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:64].strip("-")


def split_raw(raw: str):
    """Return (frontmatter_text_or_None, body). Tolerates broken YAML."""
    lines = raw.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip() == "---":
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---":
                return "\n".join(lines[i + 1:j]), "\n".join(lines[j + 1:])
        return "\n".join(lines[i + 1:]), ""   # no closing fence
    return None, raw                           # no frontmatter at top


def desc_from_broken_fm(fm_text: str) -> str:
    m = re.search(r"(?ms)^description:\s*(.+?)(?=^[A-Za-z][\w-]*:\s|\Z)", fm_text)
    if not m:
        return ""
    d = m.group(1).strip().strip("'\"").strip()
    d = re.sub(r"\s+", " ", d).rstrip(",").strip()
    # drop a trailing run-on field if it slipped in (e.g. ... delegation." version: "1.0.0)
    d = re.split(r'"\s+\w+:\s*"', d)[0].strip().strip('"').strip()
    return d[:1024]


def desc_from_body(body: str) -> str:
    for ln in body.splitlines():
        t = ln.strip()
        if not t or t.startswith("#") or t.startswith("---") or t.startswith(">"):
            continue
        return re.sub(r"\s+", " ", t)[:1024]
    return ""


def clean_triggers(val):
    out = []
    if isinstance(val, list):
        for t in val:
            t = str(t).strip()
            if t and t.upper() != "TODO":
                out.append(t)
    return out[:12]


def normalize_one(path: str):
    """Return (new_text or None, note). None text = leave as-is / cannot safely fix."""
    raw = Path(path).read_text(encoding="utf-8")
    fm_text, body = split_raw(raw)
    dirname = os.path.basename(os.path.dirname(path))

    parsed = None
    if fm_text is not None:
        try:
            loaded = yaml.safe_load(fm_text)
            parsed = loaded if isinstance(loaded, dict) else None
        except Exception:
            parsed = None

    fm = dict(parsed) if isinstance(parsed, dict) else {}

    # name: prefer existing valid-able, else directory
    name = slugify_name(str(fm.get("name", "")).strip()) or slugify_name(dirname)
    if not name:
        return None, "no derivable name"
    fm["name"] = name

    # description: prefer parsed, else salvage from broken fm, else body
    desc = str(fm.get("description", "")).strip()
    if not desc or len(desc) < 5:
        if fm_text:
            desc = desc_from_broken_fm(fm_text)
        if not desc or len(desc) < 5:
            desc = desc_from_body(body if body else raw)
    if not desc:
        desc = f"{name.replace('-', ' ')} skill."
    fm["description"] = desc[:1024]

    # triggers: keep clean ones if present
    trig = clean_triggers(fm.get("triggers"))
    # drop noisy/optional fields that commonly carry the malformation
    out = {"name": fm["name"], "description": fm["description"]}
    if trig:
        out["triggers"] = trig
    # preserve a few harmless extras only if they were cleanly parsed
    for k in ("version", "author"):
        if isinstance(parsed, dict) and isinstance(parsed.get(k), (str, int, float)):
            out[k] = str(parsed[k])

    new_fm = yaml.safe_dump(out, sort_keys=False, allow_unicode=True,
                            default_flow_style=False).strip()
    new_text = f"---\n{new_fm}\n---\n\n{body.strip()}\n"
    return new_text, "regenerated" if not parsed else "fixed-in-place"


def main():
    md_files = [p for p in glob.glob(SKILLS_ROOT + "/**/SKILL.md", recursive=True)
                if "/.hardening_originals/" not in p]
    fixed, skipped, cruft, already = [], [], [], 0
    for p in md_files:
        name = os.path.basename(os.path.dirname(p))
        errs = sk.validate_skill_md(Path(p))
        if not errs:
            already += 1
            continue
        # flag duplicate/divergent cruft separately — never auto-delete
        if name.startswith("divergent_") or re.match(r"^(.+)_\1$", name):
            cruft.append((name, p))
            continue
        try:
            new_text, note = normalize_one(p)
        except Exception as e:
            skipped.append((name, f"exception: {e}"))
            continue
        if new_text is None:
            skipped.append((name, note))
            continue
        # verify the fix actually validates before committing to it
        tmp = p + ".norm"
        Path(tmp).write_text(new_text, encoding="utf-8")
        post = sk.validate_skill_md(Path(tmp))
        os.remove(tmp)
        if post:
            skipped.append((name, f"still-invalid-after-fix: {post}"))
            continue
        if APPLY:
            Path(p).write_text(new_text, encoding="utf-8")
        fixed.append((name, note))

    print(f"=== normalize_skills ({'APPLY' if APPLY else 'DRY-RUN'}) ===")
    print(f"already valid: {already} | WOULD-FIX/FIXED: {len(fixed)} | "
          f"cruft(divergent dups): {len(cruft)} | skipped: {len(skipped)}")
    print("\n--- fixed (invalid -> valid) ---")
    for n, note in fixed:
        print(f"  {n}  [{note}]")
    if cruft:
        print("\n--- duplicate/divergent dirs (REVIEW for deletion, NOT auto-removed) ---")
        for n, p in cruft:
            print(f"  {n}")
    if skipped:
        print("\n--- skipped (needs a human look) ---")
        for n, why in skipped:
            print(f"  {n}: {why}")


if __name__ == "__main__":
    main()
