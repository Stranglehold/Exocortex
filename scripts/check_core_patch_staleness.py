"""Which A0 core files does our install pipeline overwrite with a STALE version?

Mechanical test, run inside the container: for every core .py the installer
modified, compare our deployed version against the v2.9 stock (from git) and
report any top-level symbol that stock defines and ours DROPS.

A dropped symbol is how the two bricks found today happened:
  model_config.py  lost DEFAULT_PRESET_NAME / _ensure_default_preset -> A0 crash-loops
  extract_tools.py lost extract_tool_request                        -> every turn 500s

Adding symbols is fine (that is what a patch does). Removing them is the defect.
"""
import ast
import subprocess
import sys


def symbols(src, label):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, f"unparseable ({e.msg})"
    out = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out, None


def git_show(path):
    r = subprocess.run(
        ["git", "-C", "/a0", "show", f"HEAD:{path}"],
        capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else None


modified = subprocess.run(
    ["git", "-C", "/a0", "status", "--porcelain"],
    capture_output=True, text=True,
).stdout.splitlines()

paths = [ln[3:].strip() for ln in modified if ln[:2].strip() == "M"]
pyfiles = [p for p in paths if p.endswith(".py")]

print(f"{len(paths)} core files modified by the installer; {len(pyfiles)} are Python\n")

verdicts = []
for p in pyfiles:
    stock_src = git_show(p)
    if stock_src is None:
        verdicts.append((p, "SKIP", "not in git HEAD"))
        continue
    try:
        ours_src = open("/a0/" + p, encoding="utf-8").read()
    except Exception as e:
        verdicts.append((p, "SKIP", f"unreadable: {e}"))
        continue

    stock_syms, err1 = symbols(stock_src, "stock")
    our_syms, err2 = symbols(ours_src, "ours")
    if err1 or err2:
        verdicts.append((p, "SKIP", err1 or err2))
        continue

    dropped = sorted(s for s in stock_syms - our_syms if not s.startswith("__"))
    added = sorted(s for s in our_syms - stock_syms if not s.startswith("__"))
    if dropped:
        verdicts.append((p, "STALE", f"drops {len(dropped)}: {', '.join(dropped[:6])}"))
    elif added:
        verdicts.append((p, "PATCH", f"adds {len(added)}: {', '.join(added[:4])}"))
    else:
        verdicts.append((p, "OK", "same symbol set"))

width = max(len(p) for p, _, _ in verdicts) if verdicts else 10
for p, v, note in sorted(verdicts, key=lambda x: {"STALE": 0, "SKIP": 1, "PATCH": 2, "OK": 3}[x[1]]):
    print(f"  {v:<6} {p:<{width}}  {note}")

stale = [p for p, v, _ in verdicts if v == "STALE"]
print(f"\nSTALE (drops symbols v2.9 defines): {len(stale)}")
sys.exit(1 if stale else 0)
