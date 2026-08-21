#!/usr/bin/env python3
"""Extension survey, PASS 1 — does it still RESOLVE?

Opus promoted this to the first pass because an extension that cannot reach its inputs
looks IDENTICAL to one the model has outgrown: same symptom (no effect), opposite
remedy (repair vs retire). Precedent: the entire model-profile system was inert on A0
v2.9 - Opus's Qwen3.6 supervisor overrides had never once applied - and nothing looked
broken from the outside.

Three deterministic checks per extension. No LLM calls, no driven turns.

  IMPORTS   module imports cleanly in-container (a broken import is silently dead)
  PATHS     every literal /a0/... path in the source exists
  FIRES     its log tag(s) appear in the container log

WHAT THIS PASS CANNOT TELL YOU: whether what it delivers is CORRECT or USEFUL. An
extension can import, resolve every path, and fire thousands of times while shipping
garbage - _24 surfaced 6,224 times while delivering 88% research notes. That is pass 3.

TAG REGEX NOTE: the character class includes DIGITS. A previous audit used
[A-Z][A-Z-]+ which structurally could not match [REASON-INJ-22] or [PACE-INJ-23], and
reported them as tagless. Those tags fire 928 and 424 times a day. A null result from a
grep is a claim about the grep.

Usage (in-container):
    docker cp scripts/survey_pass1_resolves.py <c>:/tmp/s1.py
    docker exec <c> /opt/venv-a0/bin/python3 /tmp/s1.py [--log /tmp/container.log]
"""
import os, re, sys, json, importlib.util

# Extensions import A0 symbols (agent, helpers.extension) at module scope. Without
# these the import check reports 73/73 dead, which is a statement about sys.path and
# not about the stack - the built-in sanity guard below catches exactly that.
sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

ROOT = "/a0/usr/plugins/_exocortex/extensions"
LOGF = None
for i, a in enumerate(sys.argv):
    if a == "--log" and i + 1 < len(sys.argv):
        LOGF = sys.argv[i + 1]

# Digits AND mixed case, both deliberately - see module docstring.
# v1 required all-caps after the first character and therefore could not match
# [MetaGate-SIZE], which appears in the container log 84 times. It reported _20 as
# never having fired. That is the SAME failure class the docstring warns about, made a
# second time in the same file: the tag vocabulary is whatever the code emits, not
# whatever shape the auditor assumed.
TAG_RE = re.compile(r'["\']\s*\[([A-Z][A-Za-z0-9 _:-]{2,28})\]')
PATH_RE = re.compile(r'["\'](/a0/[^"\'\s]{3,120})["\']')


def extensions():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        for f in sorted(fn):
            if f.startswith("_") and f.endswith(".py") and f != "__init__.py":
                out.append(os.path.join(dp, f))
    return sorted(out)


def load_log():
    if LOGF and os.path.exists(LOGF):
        return open(LOGF, encoding="utf-8", errors="replace").read()
    return None


def main():
    log = load_log()
    rows = []
    for path in extensions():
        rel = path.replace(ROOT + "/", "").replace("python/", "")
        src = open(path, encoding="utf-8", errors="replace").read()

        # IMPORTS
        try:
            spec = importlib.util.spec_from_file_location("surv_%d" % len(rows), path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            imp = "ok"
        except Exception as e:
            imp = type(e).__name__

        # PATHS - literal /a0/... references that do not exist.
        #
        # CRITICAL: a missing path is NOT automatically a defect. Several extensions
        # carry deliberate FALLBACK CHAINS for portability across container layouts
        # (v16/v17 used /a0/usr/Exocortex/..., v2.9 uses /a0/usr/plugins/_exocortex/...),
        # so the legacy arm is EXPECTED to be absent. The first version of this check
        # flagged those as broken - accusing working code, which is the expensive
        # direction and the same failure mode the skill-audit critics had.
        #
        # Discriminator: if a path that DOES exist appears within a few lines of the
        # missing one, they are alternatives in a chain, not a broken read.
        lines = src.splitlines()
        line_of = {}
        for idx, ln in enumerate(lines):
            for p in PATH_RE.findall(ln):
                line_of.setdefault(p, idx)

        paths = sorted(set(PATH_RE.findall(src)))
        # Exclude what cannot be literally checked: format placeholders, globs, and
        # prose fragments like "/a0/..." that appear inside docstrings.
        checkable = [p for p in paths
                     if "{" not in p and "%" not in p and "*" not in p
                     and not p.endswith("...") and not p.endswith("/")]
        present = [p for p in checkable if os.path.exists(p)]
        raw_missing = [p for p in checkable if not os.path.exists(p)]

        missing, fallback = [], []
        for p in raw_missing:
            i = line_of.get(p, -99)
            has_alt = any(abs(line_of.get(q, 10**6) - i) <= 4 for q in present)
            (fallback if has_alt else missing).append(p)

        # FIRES
        tags = sorted(set(TAG_RE.findall(src)))
        hits = None
        if log is not None and tags:
            hits = sum(log.count("[" + t + "]") for t in tags)

        rows.append({"ext": rel, "imports": imp, "paths": len(checkable),
                     "missing": missing, "fallback": fallback,
                     "tags": tags, "hits": hits})

    # SANITY: if nothing imported, the harness is the suspect, not the stack.
    ok_imports = sum(1 for r in rows if r["imports"] == "ok")
    print("extensions surveyed : %d" % len(rows))
    print("imported cleanly    : %d" % ok_imports)
    if rows and ok_imports == 0:
        print("!! HARNESS-FAULT: zero extensions imported. sys.path or the loader is the"
              " suspect, not the stack.")
        return 2

    bad_imports = [r for r in rows if r["imports"] != "ok"]
    missing_paths = [r for r in rows if r["missing"]]
    tagless = [r for r in rows if not r["tags"]]
    silent = [r for r in rows if r["tags"] and r["hits"] == 0] if log is not None else []

    print("with missing paths  : %d" % len(missing_paths))
    print("no log tag at all   : %d" % len(tagless))
    if log is not None:
        print("tagged but SILENT   : %d" % len(silent))
    else:
        print("(no --log given; FIRES check skipped)")

    if bad_imports:
        print("\n== IMPORT FAILURES (dead on arrival) ==")
        for r in bad_imports:
            print("  %-58s %s" % (r["ext"], r["imports"]))

    fb = [r for r in rows if r.get("fallback")]
    print("legacy fallback arms: %d ext(s) - NOT defects, a working alternative sits"
          " alongside" % len(fb))

    if missing_paths:
        print("\n== UNRESOLVED PATHS - no working alternative nearby ==")
        for r in missing_paths:
            print("  %s" % r["ext"])
            for p in r["missing"][:4]:
                print("      MISSING %s" % p)

    if silent:
        print("\n== TAGGED BUT NEVER FIRED in this log ==")
        for r in silent:
            print("  %-58s tags=%s" % (r["ext"], ",".join(r["tags"][:3])))

    if tagless:
        print("\n== NO LOG TAG - unobservable, cannot be surveyed by evidence ==")
        for r in tagless:
            print("  %s" % r["ext"])

    with open("/tmp/survey_pass1.json", "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    print("\nraw -> /tmp/survey_pass1.json")
    return 0


sys.exit(main())
