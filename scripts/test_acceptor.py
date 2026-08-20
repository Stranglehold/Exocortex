"""Acceptance tests for the Phase B commit gate (PACE / e-process).

Run:  python scripts/test_acceptor.py

The load-bearing tests are T1 and T2, and they must BOTH hold:

  T1  a candidate with NO real advantage is committed at most alpha of the time.
      Without this the gate is decorative.
  T2  a candidate with a REAL advantage is committed nearly always, and early.
      Without this the gate is just "reject everything", which also passes T1 and
      is equally useless.

A gate that only satisfies one of those is worse than no gate, because it looks
like control while providing none.

Deterministic seed so the numbers are reproducible.
"""
import importlib.util
import os
import random
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_H = os.path.normpath(os.path.join(_HERE, "..", "plugins", "_exocortex", "helpers"))
spec = importlib.util.spec_from_file_location("acc", os.path.join(_H, "acceptor.py"))
acc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acc)

TMP = tempfile.mkdtemp(prefix="acctest_")
acc.OFFICE = TMP
acc.LEDGER_PATH = os.path.join(TMP, "acceptor_trials.json")
acc.CONFIG_PATH = os.path.join(TMP, "config.json")     # absent -> defaults

results = []


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + (f"   {detail}" if detail else ""))


def reset():
    if os.path.exists(acc.LEDGER_PATH):
        os.remove(acc.LEDGER_PATH)


def simulate(p_candidate_better, conf, rng, max_inst=400):
    """Run one trial through the PURE e-process — no disk.

    T1/T2 are claims about the STATISTICS, not the storage, so they exercise
    update_wealth/verdict/classify_pair directly. Driving 300 simulated trials
    through the persisted API instead would do a full JSON load+save per instance
    and test the filesystem slowly while proving nothing extra. Persistence gets
    its own tests (T5, T7).
    """
    wealth, pairs = 1.0, 0
    for _ in range(max_inst):
        if rng.random() < 0.4:                       # discordant
            cand = rng.random() < p_candidate_better
            w = acc.classify_pair(cand, not cand)
            wealth = acc.update_wealth(wealth, w, conf["lambda"])
            pairs += 1
        else:                                        # tie -> discarded, no bet
            both = rng.random() < 0.5
            assert acc.classify_pair(both, both) is None
        v = acc.verdict(wealth, pairs, conf)
        if v in (acc.COMMIT, acc.REJECT):
            return v, pairs
    return acc.verdict(wealth, pairs, conf), pairs


CONF = dict(acc.DEFAULTS)

# ── T1: the null — no real advantage ────────────────────────────────────────
print("\nT1 — null candidate (no real advantage). False commits must be <= alpha.")
rng = random.Random(20260820)
RUNS = 400
commits = sum(1 for _ in range(RUNS) if simulate(0.5, CONF, rng)[0] == acc.COMMIT)
rate = commits / RUNS
ok(f"false-commit rate {rate:.3f} <= alpha 0.05 (+ sampling slack)", rate <= 0.08,
   f"{commits}/{RUNS}")
print("       (greedy 'keep it if the score went up' commits ~50% of these)")

# ── T2: a genuine improvement ───────────────────────────────────────────────
print("\nT2 — real advantage. Must commit nearly always, and stop early.")
rng = random.Random(999)
RUNS2 = 200
decided = [simulate(0.80, CONF, rng) for _ in range(RUNS2)]
c2 = sum(1 for v, _ in decided if v == acc.COMMIT)
used = [n for v, n in decided if v == acc.COMMIT]
ok(f"commit rate {c2/RUNS2:.2f} > 0.90 on a true +30pp edge", c2 / RUNS2 > 0.90,
   f"{c2}/{RUNS2}")
avg = sum(used) / max(len(used), 1)
ok(f"early stopping: mean {avg:.1f} pairs << budget {CONF['max_pairs']}",
   avg < CONF["max_pairs"] / 2, f"mean={avg:.1f}")

# ── T3: ties carry no information ───────────────────────────────────────────
print("\nT3 — ties")
reset()
acc.open_trial("ties")
for _ in range(50):
    t = acc.record_pair("ties", True, True)      # both correct
for _ in range(50):
    t = acc.record_pair("ties", False, False)    # both wrong
ok("ties do not move wealth", abs(t["wealth"] - 1.0) < 1e-9, f"wealth={t['wealth']}")
ok("ties do not count as pairs", t["pairs"] == 0, f"pairs={t['pairs']}")
ok("ties are counted separately", t["ties"] == 100)
ok("a trial of pure ties never commits", t["status"] == acc.CONTINUE)

# ── T4: budget exhaustion rejects ───────────────────────────────────────────
print("\nT4 — budget")
reset()
acc.open_trial("budget")
t = None
for _ in range(acc.DEFAULTS["max_pairs"] + 5):
    t = acc.record_pair("budget", False, True)   # incumbent wins every time
ok("a losing candidate is REJECTED, not left open", t["status"] == acc.REJECT,
   f"status={t['status']} pairs={t['pairs']}")

# ── T5: a decided trial does not reopen ─────────────────────────────────────
print("\nT5 — no optional-stopping abuse")
reset()
acc.open_trial("decided")
for _ in range(40):
    t = acc.record_pair("decided", True, False)
ok("committed on a clean sweep", t["status"] == acc.COMMIT, f"pairs={t['pairs']}")
w_at_decision, p_at_decision = t["wealth"], t["pairs"]
for _ in range(20):
    t = acc.record_pair("decided", False, True)  # contradicting evidence afterwards
ok("further evidence does not reopen a decided trial",
   t["status"] == acc.COMMIT and t["pairs"] == p_at_decision,
   f"pairs still {t['pairs']}")

# ── T6: parameter sanity ────────────────────────────────────────────────────
print("\nT6 — parameters")
n = acc.pairs_to_commit()
ok(f"defaults need {n} consecutive wins to commit (not a trivial number)", n >= 6, f"n={n}")
ok("tighter alpha demands more evidence", acc.pairs_to_commit(alpha=0.01) > n)
ok("bigger bets decide faster", acc.pairs_to_commit(lam=0.9) < n)

# ── T7: persistence + invalidation ──────────────────────────────────────────
print("\nT7 — persistence")
reset()
acc.open_trial("persist", {"kind": "skill"})
acc.record_pair("persist", True, False)
ok("trial survives a reload", acc.get_trial("persist")["pairs"] == 1)
ok("meta is retained", acc.get_trial("persist")["meta"]["kind"] == "skill")
ok("resuming does not reset evidence", acc.open_trial("persist")["pairs"] == 1)
ok("invalidate removes it", acc.invalidate("persist") and acc.get_trial("persist") is None)

shutil.rmtree(TMP, ignore_errors=True)
print("\n" + (f"ALL {len(results)} PASS" if all(results)
              else f"FAILURES: {results.count(False)} of {len(results)}"))
sys.exit(0 if all(results) else 1)
