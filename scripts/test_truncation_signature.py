import sys, re, json
sys.path.insert(0, '/a0'); sys.path.insert(0, '/a0/python')
from helpers import extract_tools as et

def truncated(content: str) -> bool:
    c = (content or "").lstrip()
    if not re.match(r'^\{\s*"thoughts"', c):
        return False
    if c.rstrip().endswith("}"):
        return False
    return et.extract_tool_request(content) is None

full = json.dumps({"thoughts": ["a"], "headline": "h",
                   "tool_name": "text_editor",
                   "tool_args": {"action": "write", "path": "/x", "content": "y" * 200}})
cases = [
    ("T1 truncated at 50%",        full[:len(full)//2],                 True),
    ("T2 complete valid call",     full,                                False),
    ("T3 ordinary prose response", "Sure, here is what I found. No JSON here.", False),
    ("T4 thoughts-leak (ends }) ", '{"thoughts": ["headline\\": x tool_name\\": y tool_args\\": z"]}', False),
    ("   truncated mid-string",    full[:len(full)-3],                  True),
    ("   json but not tool-shaped",'{"foo": 1}',                        False),
]
print("%-30s %-8s %-8s %-8s %s" % ("case", "trunc?", "expect", "misfmt?", "verdict"))
ok = True
for name, content, expect in cases:
    got = truncated(content)
    mis = et.is_misformatted_tool_request(content)
    good = (got == expect)
    disjoint = not (got and mis)     # the two detectors must never both fire
    ok &= good and disjoint
    print("%-30s %-8s %-8s %-8s %s%s" % (
        name, got, expect, mis,
        "OK" if good else "*** WRONG ***",
        "" if disjoint else "  *** OVERLAP WITH MISFORMAT ***"))
print()
print("RESULT:", "PASS — signature sound and disjoint" if ok else "FAIL")
