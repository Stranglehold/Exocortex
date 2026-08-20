"""HB-03 - tool discovery, generalises from the T03 implicit/explicit gap.

"Are there Python syntax errors anywhere in the extension tree?"

The prompt never names a tool. The agent has to reach for py_compile / ast.parse on its
own. T03-implicit measured 0.00 and T03-explicit 1.00 on exactly this axis - being able
to do the right thing when told, and not doing it unprompted. This asks the same
question in a domain where the correct tool is different.
"""
from verifiers._common import py, first_json, mentions, claims_clean

GT = r'''
import ast, json, os
roots = ["/a0/usr/plugins/_exocortex/extensions", "/a0/usr/plugins/_exocortex/helpers"]
checked = 0; bad = []
for r in roots:
    for dp, dn, fn in os.walk(r):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f); checked += 1
            try:
                ast.parse(open(p, encoding="utf-8", errors="replace").read())
            except SyntaxError:
                bad.append(p)
print(json.dumps({"checked": checked, "bad": len(bad), "bad_files": bad[:20]}))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (AST scan produced no JSON)"

    bad, checked = gt["bad"], gt["checked"]
    if bad == 0:
        # Clean is the expected answer; it must be ASSERTED, not left implicit.
        passed = claims_clean(response) or mentions(response, 0)
        why = "expected clean, response must say so"
    else:
        passed = mentions(response, bad)
        why = f"requires the exact failing count {bad}"
        if claims_clean(response) and not passed:
            why = f"FALSE-CLEAN: claims clean but {bad} file(s) fail to parse"
    return bool(passed), f"gt: checked={checked} bad={bad} | {why}"
