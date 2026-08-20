"""Acceptance tests for A1 — three-strike quarantine with failure fingerprinting.

Run:  python scripts/test_failure_quarantine.py

A plain local process is a valid instrument here: the module is pure string
handling, arithmetic and file I/O, with no in-process singleton. (Contrast
_02_mcp_health, where a fresh process gets an unloaded MCPConfig and would go
green for the wrong reason.) The module's real paths are redirected to a temp
directory so the real ledger is never touched.

The load-bearing test is T1. Everything else is bookkeeping: if the normalizer
does not collapse realistic variation, every occurrence looks unique, strikes
never accumulate, and the mechanism is silently inert while appearing installed.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_TARGET = os.path.normpath(os.path.join(
    _HERE, "..", "plugins", "_exocortex", "helpers", "failure_fingerprint.py"))

spec = importlib.util.spec_from_file_location("ff", _TARGET)
ff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ff)

TMP = tempfile.mkdtemp(prefix="a1test_")
ff.OFFICE = TMP
ff.LEDGER_PATH = os.path.join(TMP, "failure_fingerprints.json")
ff.ENGINE_STATE = os.path.join(TMP, "engine_state.json")

_INV_FILE = os.path.join(TMP, "gate.py")
with open(_INV_FILE, "w") as fh:
    fh.write("# v1\n")
ff._INVALIDATORS = [_INV_FILE]

ff.CONFIG_PATH = os.path.join(TMP, "config.json")   # absent -> defaults

results = []


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + (f"   {detail}" if detail else ""))


def set_cycle(n):
    with open(ff.ENGINE_STATE, "w") as fh:
        json.dump({"cycle_count": n}, fh)


def reset_ledger():
    if os.path.exists(ff.LEDGER_PATH):
        os.remove(ff.LEDGER_PATH)


set_cycle(100)

# ── T1: the normalizer collapses realistic incidental variation ──────────────
print("\nT1 — same failure, different incidental detail, must share a fingerprint")
a = "Traceback: File \"/a0/usr/skills/foo/bar.py\", line 412, in write\nOSError: [Errno 28] No space left on device (id 3f2a9bc41d)"
b = "Traceback: File \"/a0/usr/skills/baz/qux.py\", line 87, in write\nOSError: [Errno 28] No space left on device (id 91ee0aa7cc)"
c = "Traceback: File \"/a0/usr/skills/foo/bar.py\", line 412, in write\nPermissionError: [Errno 13] Permission denied"
fa = ff.fingerprint("text_editor", "disk_full", a)
fb = ff.fingerprint("text_editor", "disk_full", b)
fc = ff.fingerprint("text_editor", "perm_denied", c)
ok("same failure, different path/line/id -> same fingerprint", fa == fb, f"{fa} == {fb}")
ok("different failure -> different fingerprint", fa != fc)
ok("same message, different tool -> different fingerprint",
   ff.fingerprint("text_editor", "disk_full", a) != ff.fingerprint("browser", "disk_full", a))
ok("timestamps collapse",
   ff.fingerprint("t", "e", "failed at 2026-08-19T22:10:03Z") ==
   ff.fingerprint("t", "e", "failed at 2026-01-02T03:04:05Z"))

# ── T2: op signature is stable pre-execution, and separates targets ──────────
print("\nT2 — op signature")
s1 = ff.op_signature("text_editor", {"path": "/a0/usr/wiki/a.md", "op": "write", "content": "x" * 20000})
s2 = ff.op_signature("text_editor", {"path": "/a0/usr/wiki/a.md", "op": "write", "content": "y" * 20000})
s3 = ff.op_signature("text_editor", {"path": "/a0/usr/wiki/DIFFERENT.md", "op": "write", "content": "x" * 20000})
ok("same target, different bulk content -> same signature", s1 == s2)
ok("different target -> different signature", s1 != s3)
ok("arg order does not matter",
   ff.op_signature("t", {"a": 1, "b": 2}) == ff.op_signature("t", {"b": 2, "a": 1}))

# ── T3: three strikes quarantines, and preserves evidence ───────────────────
print("\nT3 — three strikes")
reset_ledger()
ev = {"causal_chain": "disk filled during write", "raw_output_tail": a}
r1 = ff.record_failure("text_editor", "disk_full", a, s1, ev)
r2 = ff.record_failure("text_editor", "disk_full", b, s1, ev)
ok("strike 1 not quarantined", r1["strikes"] == 1 and not r1["quarantined"])
ok("strike 2 counts the VARIANT message as the same failure",
   r2["strikes"] == 2, f"strikes={r2['strikes']}")
r3 = ff.record_failure("text_editor", "disk_full", a, s1, ev)
ok("strike 3 quarantines", r3["strikes"] == 3 and r3["quarantined"])
q = ff.find_quarantine(s1)
ok("quarantine is findable by op signature (pre-execution)", q is not None)
ok("evidence preserved", bool(q and q["evidence"]["causal_chain"]), str(q and q["evidence"])[:60])
ok("unrelated attempt is NOT quarantined", ff.find_quarantine(s3) is None)

# ── T4: rolling window resets stale strikes ─────────────────────────────────
print("\nT4 — rolling window")
reset_ledger()
set_cycle(100)
ff.record_failure("t", "e", "boom", "sigA")
ff.record_failure("t", "e", "boom", "sigA")
set_cycle(100 + ff.DEFAULTS["window_cycles"] + 1)     # fell out of the window
r = ff.record_failure("t", "e", "boom", "sigA")
ok("strike count restarts outside the window", r["strikes"] == 1 and not r["quarantined"],
   f"strikes={r['strikes']}")

# ── T5: quarantines are NOT aged out by the window ──────────────────────────
print("\nT5 — quarantine persists past the window")
reset_ledger()
set_cycle(200)
for _ in range(3):
    ff.record_failure("t", "e", "boom", "sigB")
ok("quarantined at cycle 200", ff.find_quarantine("sigB") is not None)
set_cycle(200 + ff.DEFAULTS["window_cycles"] + 10)
ff.record_failure("other", "x", "unrelated", "sigC")   # forces a prune
ok("still quarantined long after the window elapsed", ff.find_quarantine("sigB") is not None)

# ── T6: invalidation on gating-code change ──────────────────────────────────
print("\nT6 — invalidation")
reset_ledger()
set_cycle(300)
for _ in range(3):
    ff.record_failure("t", "e", "boom", "sigD")
ok("quarantined before the code change", ff.find_quarantine("sigD") is not None)
with open(_INV_FILE, "w") as fh:
    fh.write("# v2 - gate changed\n")
ok("quarantine released when the gating code changes", ff.find_quarantine("sigD") is None)

# ── T7: explicit release ────────────────────────────────────────────────────
print("\nT7 — maintainer override")
reset_ledger()
set_cycle(400)
last = None
for _ in range(3):
    last = ff.record_failure("t", "e", "boom", "sigE")
ok("quarantined", ff.find_quarantine("sigE") is not None)
ff.release(last["fingerprint"])
ok("release clears it", ff.find_quarantine("sigE") is None)

# ── T8: the store survives a torn write / garbage file ──────────────────────
print("\nT8 — robustness")
with open(ff.LEDGER_PATH, "w") as fh:
    fh.write("{ this is not json")
led = ff.load_ledger()
ok("garbage ledger degrades to empty rather than raising", isinstance(led.get("entries"), dict))
ok("record_failure still works after a corrupt ledger",
   ff.record_failure("t", "e", "boom", "sigF")["strikes"] == 1)

shutil.rmtree(TMP, ignore_errors=True)
print("\n" + (f"ALL {len(results)} PASS" if all(results)
              else f"FAILURES: {results.count(False)} of {len(results)}"))
sys.exit(0 if all(results) else 1)
