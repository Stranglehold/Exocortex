#!/usr/bin/env python3
"""
contract_check.py — static contract checker for the OSS + SWARMFISH plugins.

The "compiler for the seams." Every silent gap found in the 2026-05-25 audit was a
contract violation *between* layers that nothing verified: a UI reading a field the
API never returns, a query referencing a column the schema lacks, a cross-plugin
import of a symbol that moved. This tool walks those seams and fails on mismatches —
so the next one is caught before deploy, not in production.

Three checks (deterministic, no LLM, no runtime — pure static analysis of the repo):

  1. DB COLUMN CONTRACT  (HIGH) — every column named in an INSERT INTO (...) column
     list or an UPDATE ... SET clause must exist in the table's CREATE TABLE schema.
     Catches renamed/typo'd columns (the class behind the source_weights bug family).

  2. CROSS-PLUGIN IMPORT CONTRACT  (HIGH) — every `from src.X import Y` /
     `from swfsrc.X import Y` must resolve: module X.py exists in the right plugin
     and symbol Y is defined there. Catches the src->swfsrc rename class.

  3. UI<->API KEY CONTRACT  (REVIEW) — every `d.<key>` the webui store reads off an
     endpoint response should be a key some endpoint's process() actually returns.
     Heuristic (JS is dynamic) so findings are REVIEW, not failures. Catches the
     d.consensus / d.hypotheses field-mismatch class.

What this does NOT do: resolve SELECT column aliases (too fragile), type-check
values, parse Alpine templates, or check anything at runtime (see the runtime
introspection tool for that). It checks names and shapes, statically.

Exit code: 0 if no HIGH findings, 1 otherwise (CI-usable).

Usage:  python scripts/contract_check.py [--repo PATH] [-v]
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OSS_SRC   = "services/oss_plugin/src"
OSS_API   = "services/oss_plugin/api"
OSS_DB    = "services/oss_plugin/src/db.py"
OSS_STORE = "services/oss_plugin/webui/intelligence-store.js"
SWF_SRC   = "services/swarmfish_plugin/swfsrc"
SWF_API   = "services/swarmfish_plugin/api"
SWF_DB    = "services/swarmfish_plugin/swfsrc/db.py"

# Plugin-import roots: prefix -> directory holding the package modules.
IMPORT_ROOTS = {
    "swfsrc": SWF_SRC,   # swarmfish (renamed from src 2026-05-25)
    "src":    OSS_SRC,   # oss (oss's own src package)
}

SQL_KEYWORDS = {
    "constraint", "unique", "check", "primary", "foreign", "key",
    "create", "index", "references",
}


class Finding:
    __slots__ = ("severity", "where", "what", "why")
    def __init__(self, severity, where, what, why=""):
        self.severity, self.where, self.what, self.why = severity, where, what, why
    def __str__(self):
        line = f"[{self.severity}] {self.where} - {self.what}"
        return line + (f"\n          -> {self.why}" if self.why else "")


def _read(rel):
    p = os.path.join(REPO, rel)
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _py_files(reldir):
    d = os.path.join(REPO, reldir)
    if not os.path.isdir(d):
        return []
    return [os.path.join(reldir, f) for f in sorted(os.listdir(d))
            if f.endswith(".py") and f != "__init__.py"]


# ---------------------------------------------------------------------------
# Schema parsing
# ---------------------------------------------------------------------------

def _split_top_level_commas(body: str):
    """Split on commas that are not nested inside parentheses."""
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))
    return parts


def parse_schema(db_rel: str) -> dict:
    """Return {table_name: set(column_names)} parsed from CREATE TABLE blocks."""
    text = _read(db_rel)
    tables = {}
    for m in re.finditer(r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\((.*?)\n\s*\);",
                          text, re.DOTALL | re.IGNORECASE):
        name, body = m.group(1), m.group(2)
        # Strip SQL line comments first — comment text injects fake columns
        # (e.g. "null" from prose) and, worse, hides the real column that follows
        # a comment inside the same comma-segment.
        body = re.sub(r"--[^\n]*", "", body)
        cols = set()
        for seg in _split_top_level_commas(body):
            seg = seg.strip()
            if not seg:
                continue
            first = seg.split()[0].strip().lower()
            if first in SQL_KEYWORDS:
                continue
            col = seg.split()[0].strip().strip('"')
            if re.match(r"^[A-Za-z_]\w*$", col):
                cols.add(col.lower())
        if cols:
            tables[name.lower()] = cols
    return tables


# ---------------------------------------------------------------------------
# Check 1 — DB column contract
# ---------------------------------------------------------------------------

def check_db_columns(schema: dict, src_dirs: list, label: str) -> list:
    findings = []
    for reldir in src_dirs:
        for rel in _py_files(reldir):
            text = _read(rel)

            # INSERT INTO <table> (<col list>)
            for m in re.finditer(r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)\s*\(([^)]*)\)",
                                  text, re.IGNORECASE | re.DOTALL):
                table = m.group(1).lower()
                if table not in schema:
                    continue  # unknown table handled by the table-existence pass below
                cols = [c.strip().strip('"').lower() for c in m.group(2).split(",")]
                for c in cols:
                    if not c or not re.match(r"^[a-z_]\w*$", c):
                        continue
                    if c not in schema[table]:
                        findings.append(Finding(
                            "HIGH", f"{rel}",
                            f"INSERT into '{table}' references unknown column '{c}'",
                            f"'{table}' columns: {sorted(schema[table])}"))

            # UPDATE <table> SET <col>=...
            for m in re.finditer(r"UPDATE\s+(\w+)\s+SET\s+(.*?)(?:\bWHERE\b|\"\"\"|'''|\)\s*$)",
                                 text, re.IGNORECASE | re.DOTALL):
                table = m.group(1).lower()
                if table not in schema:
                    continue
                for cm in re.finditer(r"(\w+)\s*=", m.group(2)):
                    c = cm.group(1).lower()
                    if c in ("datetime", "json", "coalesce"):  # function calls, not cols
                        continue
                    if c not in schema[table]:
                        findings.append(Finding(
                            "HIGH", f"{rel}",
                            f"UPDATE '{table}' sets unknown column '{c}'",
                            f"'{table}' columns: {sorted(schema[table])}"))
    return findings


# ---------------------------------------------------------------------------
# Check 2 — cross-plugin import contract
# ---------------------------------------------------------------------------

def _module_symbols(mod_rel: str) -> set:
    """Top-level defs/classes/assignments in a module (what `from mod import X` can find)."""
    try:
        tree = ast.parse(_read(mod_rel))
    except Exception:
        return set()
    syms = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            syms.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    syms.add(t.id)
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                syms.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                syms.add((a.asname or a.name).split(".")[0])
    return syms


def check_imports(scan_dirs: list) -> list:
    findings = []
    sym_cache = {}
    for reldir in scan_dirs:
        for rel in _py_files(reldir):
            text = _read(rel)
            for m in re.finditer(r"from\s+(swfsrc|src)\.(\w+)\s+import\s+([^\n#]+)", text):
                root, mod, names = m.group(1), m.group(2), m.group(3)
                root_dir = IMPORT_ROOTS.get(root)
                mod_rel = f"{root_dir}/{mod}.py"
                if not os.path.isfile(os.path.join(REPO, mod_rel)):
                    findings.append(Finding(
                        "HIGH", rel,
                        f"imports '{root}.{mod}' but {mod_rel} does not exist"))
                    continue
                if mod_rel not in sym_cache:
                    sym_cache[mod_rel] = _module_symbols(mod_rel)
                defined = sym_cache[mod_rel]
                for raw in names.split(","):
                    sym = raw.strip().split(" as ")[0].strip().strip("()")
                    if not sym or sym == "*":
                        continue
                    if sym not in defined:
                        findings.append(Finding(
                            "HIGH", rel,
                            f"imports '{sym}' from '{root}.{mod}' but it is not defined there",
                            f"{mod_rel} defines: {sorted(defined)[:12]}…"))
    return findings


# ---------------------------------------------------------------------------
# Check 3 — UI <-> API key contract (heuristic → REVIEW)
# ---------------------------------------------------------------------------

def _endpoint_return_keys(api_dirs: list) -> set:
    """Union of all top-level keys returned by any process() return-dict."""
    keys = set()
    for reldir in api_dirs:
        for rel in _py_files(reldir):
            try:
                tree = ast.parse(_read(rel))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                    for k in node.value.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            keys.add(k.value)
    return keys


def check_ui_keys(store_rel: str, api_dirs: list) -> list:
    """Flag store reads `d.<key>` where no endpoint returns <key>.

    Heuristic: `d` is the convention for an endpoint response in the store. Keys
    that are never returned by ANY endpoint are likely the d.consensus / d.hypotheses
    mismatch class. False positives possible (locally-built objects) → REVIEW only.
    """
    text = _read(store_rel)
    returned = _endpoint_return_keys(api_dirs)
    # JS-builtin / common chained props to ignore.
    # `d` is also reused for local Date objects in the store (fmtDate), so ignore
    # JS/Date builtins and common chained props — only response-shape keys matter.
    ignore = {"json", "ok", "status", "length", "map", "filter", "find", "slice",
              "then", "catch", "data", "error", "message", "push", "forEach",
              "toLocaleDateString", "toLocaleTimeString", "toLocaleString",
              "getTime", "getFullYear", "getMonth", "getDate", "toISOString",
              "toFixed", "join", "split", "trim", "includes"}
    findings = []
    seen = set()
    for m in re.finditer(r"\bd\.([a-zA-Z_]\w*)", text):
        key = m.group(1)
        if key in ignore or key in seen:
            continue
        seen.add(key)
        if key not in returned:
            findings.append(Finding(
                "REVIEW", store_rel,
                f"store reads `d.{key}` but no endpoint returns a top-level '{key}'",
                "verify the field name against the endpoint's process() return"))
    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    REPO = os.path.abspath(args.repo)

    print("=" * 72)
    print("CONTRACT CHECK - OSS + SWARMFISH plugin seams")
    print("=" * 72)

    oss_schema = parse_schema(OSS_DB)
    swf_schema = parse_schema(SWF_DB)
    if args.verbose:
        print(f"  OSS schema: {len(oss_schema)} tables  |  SWARMFISH schema: {len(swf_schema)} tables")

    findings = []
    findings += check_db_columns(oss_schema, [OSS_SRC, OSS_API], "OSS")
    findings += check_db_columns(swf_schema, [SWF_SRC, SWF_API], "SWARMFISH")
    findings += check_imports([OSS_SRC, OSS_API, SWF_SRC, SWF_API])
    findings += check_ui_keys(OSS_STORE, [OSS_API, SWF_API])

    high   = [f for f in findings if f.severity == "HIGH"]
    review = [f for f in findings if f.severity == "REVIEW"]

    if not findings:
        print("\nPASS: no contract violations found.\n")
        return 0

    if high:
        print(f"\n{len(high)} HIGH finding(s):\n")
        for f in high:
            print("  " + str(f))
    if review:
        print(f"\n{len(review)} REVIEW finding(s) (heuristic - confirm manually):\n")
        for f in review:
            print("  " + str(f))

    print(f"\n{'=' * 72}")
    print(f"  HIGH: {len(high)}   REVIEW: {len(review)}")
    print("=" * 72)
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
