#!/usr/bin/env python3
"""
integrity_check.py — Phase 0 Wiki Integrity Check
==================================================
Run at the start of every MAINTAIN cycle to verify system health.

Checks:
  1. Wiki index vs filesystem: every page in index.md exists on disk
  2. Status header consistency: page frontmatter status matches index entry
  3. Stale arXiv sources: wiki pages whose primary arXiv source is > 60 days old

Output: JSON summary + human-readable findings to stdout.

Usage:
  python3 /a0/usr/workdir/workspace/self-improvement/integrity_check.py
  python3 /a0/usr/workdir/workspace/self-improvement/integrity_check.py --json-only
  python3 /a0/usr/workdir/workspace/self-improvement/integrity_check.py --stale-days 60
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

_WIKI_DIR   = "/a0/usr/workdir/workspace/wiki"
_INDEX_PATH = "/a0/usr/workdir/workspace/wiki/index.md"
_STALE_DAYS_DEFAULT = 60
_SKILLS_ROOT     = "/a0/usr/skills"
_NORMALIZER_PATH = "/a0/usr/Exocortex/scripts/normalize_skills.py"


def _heal_skills(apply: bool = True) -> dict:
    """Check 4: skill-frontmatter integrity self-heal. Runs the deterministic normalizer
    (scripts/normalize_skills.py) so authored/captured skills with malformed frontmatter
    are repaired and stay discoverable — the same maintenance sweep that verifies wiki
    consistency now also keeps the skill library valid. Graceful no-op if unavailable."""
    try:
        import importlib.util
        sys.path.insert(0, "/a0/python")
        sys.path.insert(0, "/a0")
        spec = importlib.util.spec_from_file_location("_exo_skill_norm", _NORMALIZER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.normalize_root(_SKILLS_ROOT, apply=apply)
    except Exception as e:
        return {"error": str(e), "fixed": [], "already_valid": 0, "cruft": [], "skipped": []}


def _parse_index(index_path: str) -> list[dict]:
    """Parse wiki/index.md into a list of {title, path, status} entries.

    Looks for lines like:
      - [Title](path/to/page.md) — DRAFT/STABLE/VERIFIED
    or
      - TODO: Title
    """
    entries = []
    if not os.path.exists(index_path):
        return entries
    try:
        with open(index_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Linked entry: - [Title](path) — STATUS
                m = re.match(r"-\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+[—–]\s+(\w+))?", line)
                if m:
                    entries.append({
                        "title":  m.group(1),
                        "path":   m.group(2),
                        "status": m.group(3) or "UNKNOWN",
                        "todo":   False,
                    })
                    continue
                # TODO entry: - TODO: Title
                m = re.match(r"-\s+TODO:\s+(.+)", line)
                if m:
                    entries.append({
                        "title":  m.group(1).strip(),
                        "path":   None,
                        "status": "TODO",
                        "todo":   True,
                    })
    except Exception as e:
        print(f"[integrity] WARNING: could not parse index: {e}", file=sys.stderr)
    return entries


def _read_page_metadata(abs_path: str) -> dict:
    """Read YAML frontmatter from a wiki page. Returns {} if absent or unreadable."""
    try:
        with open(abs_path, encoding="utf-8") as f:
            content = f.read(4096)
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            return {}
        meta = {}
        for line in m.group(1).splitlines():
            kv = line.split(":", 1)
            if len(kv) == 2:
                meta[kv[0].strip()] = kv[1].strip()
        return meta
    except Exception:
        return {}


def _extract_arxiv_date(meta: dict) -> datetime | None:
    """Extract arXiv paper date from 'source' or 'arxiv' metadata field.

    Looks for dates like 2024-11 or 2025-03-15 in the source/arxiv field.
    Returns a datetime or None if not parseable.
    """
    source = meta.get("source", "") or meta.get("arxiv", "") or meta.get("primary_source", "")
    # arxiv IDs like 2501.12345 encode year+month
    m = re.search(r"(\d{2})(\d{2})\.\d+", source)
    if m:
        year  = int("20" + m.group(1))
        month = int(m.group(2))
        if 1 <= month <= 12:
            try:
                return datetime(year, month, 1, tzinfo=timezone.utc)
            except ValueError:
                pass
    # Explicit date fields
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", source)
    if m:
        year  = int(m.group(1))
        month = int(m.group(2))
        day   = int(m.group(3) or 1)
        try:
            return datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def run_checks(stale_days: int = _STALE_DAYS_DEFAULT) -> dict:
    """Run all integrity checks. Returns a structured results dict."""
    now   = datetime.now(timezone.utc)
    index = _parse_index(_INDEX_PATH)

    missing_files    = []
    status_mismatches = []
    stale_sources    = []
    todo_count       = 0

    for entry in index:
        if entry["todo"]:
            todo_count += 1
            continue

        rel_path = entry["path"]
        if not rel_path:
            continue

        # Resolve to absolute path
        if rel_path.startswith("/"):
            abs_path = rel_path
        else:
            abs_path = os.path.join(_WIKI_DIR, rel_path)

        # Check 1: file existence
        if not os.path.exists(abs_path):
            missing_files.append({
                "title": entry["title"],
                "path":  rel_path,
                "index_status": entry["status"],
            })
            continue

        # Check 2: status consistency
        meta = _read_page_metadata(abs_path)
        page_status = meta.get("status", "").upper()
        index_status = (entry["status"] or "").upper()
        if page_status and index_status and page_status != index_status and index_status != "UNKNOWN":
            status_mismatches.append({
                "title":        entry["title"],
                "path":         rel_path,
                "index_status": index_status,
                "page_status":  page_status,
            })

        # Check 3: stale arXiv sources
        arxiv_date = _extract_arxiv_date(meta)
        if arxiv_date:
            age_days = (now - arxiv_date).days
            if age_days > stale_days:
                stale_sources.append({
                    "title":     entry["title"],
                    "path":      rel_path,
                    "age_days":  age_days,
                    "source":    meta.get("source", meta.get("arxiv", "")),
                })

    total_pages  = len([e for e in index if not e["todo"] and e["path"]])
    total_issues = len(missing_files) + len(status_mismatches) + len(stale_sources)

    # Check 4: skill-frontmatter integrity self-heal (deterministic; repairs invalid SKILL.md)
    skills = _heal_skills(apply=True)

    return {
        "timestamp":          now.isoformat(),
        "total_pages":        total_pages,
        "todo_count":         todo_count,
        "total_issues":       total_issues,
        "missing_files":      missing_files,
        "status_mismatches":  status_mismatches,
        "stale_sources":      stale_sources,
        "integrity_ok":       total_issues == 0,
        "skills_healed":      skills.get("fixed", []),
        "skills_valid":       skills.get("already_valid", 0),
        "skills_cruft":       skills.get("cruft", []),
        "skills_skipped":     skills.get("skipped", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 0 wiki integrity check")
    parser.add_argument("--json-only",  action="store_true",
                        help="Output only JSON (no human-readable text)")
    parser.add_argument("--stale-days", type=int, default=_STALE_DAYS_DEFAULT,
                        help=f"Days before arXiv source is flagged stale (default: {_STALE_DAYS_DEFAULT})")
    args = parser.parse_args()

    results = run_checks(stale_days=args.stale_days)

    if args.json_only:
        print(json.dumps(results, indent=2))
        return

    # Human-readable output
    print(f"\n=== Wiki Integrity Check — {results['timestamp'][:10]} ===")
    print(f"  Total pages indexed: {results['total_pages']}")
    print(f"  TODO entries:        {results['todo_count']}")
    print(f"  Total issues:        {results['total_issues']}")

    if results["missing_files"]:
        print(f"\n[MISSING FILES] {len(results['missing_files'])} page(s) in index but not on disk:")
        for item in results["missing_files"]:
            print(f"  - {item['title']} ({item['path']}) — index says {item['index_status']}")

    if results["status_mismatches"]:
        print(f"\n[STATUS MISMATCH] {len(results['status_mismatches'])} page(s) where index and frontmatter disagree:")
        for item in results["status_mismatches"]:
            print(f"  - {item['title']}: index={item['index_status']}, page={item['page_status']}")

    if results["stale_sources"]:
        print(f"\n[STALE SOURCES] {len(results['stale_sources'])} page(s) with arXiv source > {args.stale_days} days old:")
        for item in results["stale_sources"]:
            print(f"  - {item['title']}: {item['age_days']} days old ({item['source'][:60]})")

    healed = results.get("skills_healed", [])
    cruft = results.get("skills_cruft", [])
    if healed or cruft:
        print(f"\n[SKILLS] valid={results.get('skills_valid', 0)} | "
              f"healed={len(healed)} | cruft(dup dirs)={len(cruft)}")
        if healed:
            print(f"  repaired frontmatter -> discoverable: {', '.join(healed)}")
    else:
        print(f"\n[SKILLS] valid={results.get('skills_valid', 0)} | all frontmatter clean")

    if results["integrity_ok"]:
        print("\n[OK] No integrity issues found.")
    else:
        print(f"\n[ACTION REQUIRED] {results['total_issues']} issue(s) need attention before sleep consolidation.")

    # Also output JSON for machine consumption
    print("\n--- JSON ---")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
