"""Acceptance tests for A3 — complexity-keyed, profile-sourced write threshold.

Run:  python scripts/test_write_threshold.py

The load-bearing assertion is T1: with plain prose the effective limit must equal the
historical flat 5000, so A3 ships a MECHANISM and not a behaviour change. Everything
after that checks the mechanism only ever tightens, never loosens, and never tightens
so far that the agent cannot write at all.
"""
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_H = os.path.normpath(os.path.join(_HERE, "..", "plugins", "_exocortex", "helpers"))
spec = importlib.util.spec_from_file_location("wt", os.path.join(_H, "write_threshold.py"))
wt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wt)

results = []


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + (f"   {detail}" if detail else ""))


PROSE = ("The quick brown fox jumps over the lazy dog. " * 200)          # ~8.8K, plain
CODE = ("```python\nx = 1\n```\n" * 40) + ("some prose. " * 100)          # fenced
JSONISH = ('{"key": "value with \\"escapes\\" and\nnewlines"} ' * 200)    # escape-dense

# ── T1: plain prose is unchanged from the historical constant ───────────────
print("\nT1 — no behaviour change on plain content")
lim, sig = wt.effective_limit("hello world, a plain sentence.")
ok("plain short content -> limit is the historical 5000", lim == 5000, f"limit={lim}")
ok("plain content scores 1.0 complexity", sig["score"] == 1.0, f"score={sig['score']}")
lim_p, sig_p = wt.effective_limit(PROSE)
ok("long plain prose still ~5000 (length alone does not tighten)",
   lim_p >= 4000, f"limit={lim_p} score={sig_p['score']}")

# ── T2: complexity tightens ────────────────────────────────────────────────
print("\nT2 — complexity tightens, and only tightens")
lim_c, sig_c = wt.effective_limit(CODE)
ok("fenced code tightens the limit", lim_c < 5000, f"limit={lim_c} fences={sig_c['fenced_blocks']}")
ok("fenced blocks counted as PAIRS not delimiters", sig_c["fenced_blocks"] == 40,
   f"fences={sig_c['fenced_blocks']}")
lim_j, sig_j = wt.effective_limit(JSONISH)
ok("escape-dense content tightens the limit", lim_j < 5000,
   f"limit={lim_j} density={sig_j['escape_density']}")
ok("no content type ever RAISES the limit above base",
   all(wt.effective_limit(t)[0] <= 5000 for t in (PROSE, CODE, JSONISH, "")))

# ── T3: the floor protects the agent ───────────────────────────────────────
print("\nT3 — floor")
pathological = '"\\\n\t' * 5000
lim_x, sig_x = wt.effective_limit(pathological)
ok("pathological content still leaves a usable limit",
   lim_x >= wt.DEFAULTS["floor_limit"], f"limit={lim_x}")
ok("score is capped", sig_x["score"] <= wt.DEFAULTS["max_score"], f"score={sig_x['score']}")

# ── T4: profile overrides are honoured ─────────────────────────────────────
print("\nT4 — profile override")
lim_o, _ = wt.effective_limit(PROSE, {"base_limit": 20000})
ok("a profile can raise the base limit", lim_o > 15000, f"limit={lim_o}")
lim_z, _ = wt.effective_limit(CODE, {"fence_penalty": 0.0, "escape_penalty": 0.0})
ok("penalties can be disabled entirely", lim_z == 5000, f"limit={lim_z}")

# ── T5: describe() reports its provenance ──────────────────────────────────
print("\nT5 — provenance")
d = wt.describe("a short plain sentence.")   # no container -> profile lookup -> "none"
ok("describe reports which profile supplied the numbers", "profile" in d, f"profile={d['profile']}")
ok("content under the limit is not flagged", d["over"] is False,
   f"len={d['length']} limit={d['effective_limit']}")
# PROSE is ~8.8K, genuinely over the 5000 default — the first version of this test
# asserted otherwise and the code was right.
ok("long prose IS over the default limit", wt.describe(PROSE)["over"] is True)
big = wt.describe("x" * 60000)
ok("oversized content is flagged over", big["over"] is True)

# ── T6: degradation ────────────────────────────────────────────────────────
print("\nT6 — degradation")
ok("empty content does not divide by zero", wt.effective_limit("")[0] > 0)
ok("None content is handled", wt.effective_limit(None)[0] > 0)

print("\n" + (f"ALL {len(results)} PASS" if all(results)
              else f"FAILURES: {results.count(False)} of {len(results)}"))
sys.exit(0 if all(results) else 1)
