#!/usr/bin/env python3
"""
scan_container.py — GENERATE the wiring map from the running container.

Fable's idea, 2026-09-03: the wiring diagram should be generated, not written.
A hand-written diagram is a description, and descriptions drift from the thing
they describe — ours has been drifting since May. A generated one is a
measurement with a timestamp.

Runs INSIDE the container. Read-only. Emits JSON on stdout.

Subsumes three one-off instruments built 2026-09-02/03:
  - the path audit          (does every referenced path resolve?)
  - the severed-loop scan   (is every written state key read?)
  - the firing sweep        (which extensions actually emit?)

Instrument notes, learned the hard way and encoded here so they are not
re-learned:
  * Tag extraction must scan the WHOLE FILE, not lines containing print( —
    multi-line print() calls put the tag on the next line.
  * A state key read via a CONSTANT (get_data(EI_VERDICT_KEY)) is invisible to
    a string-literal regex. Resolve module constants first.
  * An extension with zero stdout prints is UNDETECTABLE, not silent.
  * Prints inside `except` blocks mean silence == healthy.
"""
import ast, json, os, re, sys
from collections import defaultdict

# Web UI section contributed by Fable (2026-09-03). Optional by design: if the
# module is absent the rest of the scan still runs and says so, rather than the
# whole generator dying over one section.
try:
    from scan_flags import scan as scan_flags  # type: ignore
except Exception as _fe:  # noqa: BLE001
    _flags_err = str(_fe)
    def scan_flags():
        return {"error": "scan_flags.py not importable: %s" % _flags_err,
                "limits": ["enabled-flag coverage not measured this run"]}

try:
    from scan_webui import scan_webui  # type: ignore
except Exception as _e:  # noqa: BLE001
    _webui_err = str(_e)
    def scan_webui():
        return {"error": "scan_webui.py not importable: %s" % _webui_err,
                "limits": ["web UI not measured this run"]}

CORE_ROOTS = ["/a0/extensions/python", "/a0/plugins"]
PLUGIN_ROOT = "/a0/usr/plugins/_exocortex/extensions/python"
PLUGIN_ALL = "/a0/usr/plugins/_exocortex"

TAG_RE   = re.compile(r"\[([A-Z][A-Za-z0-9_-]{2,26})\]")
PATH_RE  = re.compile(r'["\'](/a0/[A-Za-z0-9_./-]{3,120})["\']')
GLOBBY   = re.compile(r"[*?\[\]{}]")
SETD_RE  = re.compile(r'set_data\(\s*(?:"([A-Za-z0-9_]+)"|([A-Z_][A-Z0-9_]*))')
GETD_RE  = re.compile(r'get_data\(\s*(?:"([A-Za-z0-9_]+)"|([A-Z_][A-Z0-9_]*))')
SETA_RE  = re.compile(r'setattr\(\s*(?:self\.)?agent,\s*(?:"([A-Za-z0-9_]+)"|([A-Z_][A-Z0-9_]*))')
GETA_RE  = re.compile(r'getattr\(\s*(?:self\.)?agent,\s*(?:"([A-Za-z0-9_]+)"|([A-Z_][A-Z0-9_]*))')
CONST_RE = re.compile(r'^([A-Z_][A-Z0-9_]*)\s*=\s*["\']([A-Za-z0-9_]+)["\']', re.M)


def first_doc(text):
    try:
        mod = ast.parse(text)
        d = ast.get_docstring(mod) or ""
        for line in d.splitlines():
            line = line.strip()
            if line and not line.startswith(("=", "-")):
                return line[:150]
    except SyntaxError:
        pass
    return ""


def err_only_prints(text):
    """True when EVERY print() sits within 6 lines after an `except`."""
    lines = text.splitlines()
    total = err = 0
    countdown = 0
    for ln in lines:
        if "except" in ln:
            countdown = 6
        if "print(" in ln:
            total += 1
            if countdown > 0:
                err += 1
        if countdown:
            countdown -= 1
    return total > 0 and total == err, total


def scan_tree(root, kind):
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, _d, files in os.walk(root):
        if "__pycache__" in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith(".py") or not fn.startswith("_"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                text = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            hook = os.path.basename(dirpath)
            if hook == os.path.basename(root):
                hook = "(root)"
            m = re.match(r"_(\d+)_", fn)
            consts = dict((k, v) for k, v in CONST_RE.findall(text))

            def keys(rx):
                found = set()
                for lit, const in rx.findall(text):
                    if lit:
                        found.add(lit)
                    elif const in consts:
                        found.add(consts[const])
                return sorted(found)

            eo, nprints = err_only_prints(text)
            paths = sorted({p for p in PATH_RE.findall(text)
                            if not GLOBBY.search(p) and p.count("/") >= 2})
            out.append({
                "file": fn,
                "hook": hook,
                "order": int(m.group(1)) if m else None,
                "kind": kind,
                "path": fp,
                "lines": text.count("\n") + 1,
                "purpose": first_doc(text),
                "tags": sorted(set(TAG_RE.findall(text)))[:4],
                "writes": sorted(set(keys(SETD_RE)) | set(keys(SETA_RE))),
                "reads": sorted(set(keys(GETD_RE)) | set(keys(GETA_RE))),
                "n_prints": nprints,
                "error_only_prints": eo,
                "paths": paths,
                "paths_missing": [p for p in paths if not os.path.exists(p)],
            })
    return out


exts = scan_tree(PLUGIN_ROOT, "plugin")
for cr in CORE_ROOTS:
    exts += scan_tree(cr, "core")

# ── cross-file state-key wiring ─────────────────────────────────────────────
writers, readers = defaultdict(list), defaultdict(list)
for e in exts:
    for k in e["writes"]:
        writers[k].append(e["file"])
    for k in e["reads"]:
        readers[k].append(e["file"])
severed = sorted(k for k in writers if k not in readers)
orphan_reads = sorted(k for k in readers if k not in writers)

hooks = defaultdict(list)
for e in exts:
    hooks[e["hook"]].append(e)
for h in hooks:
    hooks[h].sort(key=lambda e: (e["order"] is None, e["order"] or 0, e["file"]))

print(json.dumps({
    "generated": __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).isoformat()[:19] + "Z",
    "container_paths": {"plugin": PLUGIN_ROOT, "core": CORE_ROOTS},
    "counts": {
        "extensions_total": len(exts),
        "plugin": sum(1 for e in exts if e["kind"] == "plugin"),
        "core": sum(1 for e in exts if e["kind"] == "core"),
        "hooks": len(hooks),
        "undetectable": sum(1 for e in exts if e["n_prints"] == 0),
        "error_only": sum(1 for e in exts if e["error_only_prints"]),
        "paths_missing": sum(len(e["paths_missing"]) for e in exts),
    },
    "state_keys": {
        "written": len(writers), "read": len(readers),
        "severed_write_no_read": severed,
        "read_never_written": orphan_reads,
    },
    "webui": scan_webui(),
    "flags": scan_flags(),
    "hooks": {h: hooks[h] for h in sorted(hooks)},
}, indent=1))
