"""
acceptor.py — Phase B: the anytime-valid commit gate (PACE)

THE PROBLEM IT SOLVES
---------------------
A self-evolving system proposes changes and keeps the ones that score higher on a
small held-out set. Applied once that is sound. Applied hundreds of times against the
SAME noisy estimate it is uncontrolled adaptive multiple testing — the system p-hacks
itself. Measured in PACE (arXiv 2606.08106): with **no real gain available at all**,
greedy acceptance commits 13–21 spurious self-modifications per run, 72–100% of them
false, and degrades the most fragile agent by 4.9 points. It does not sit still when
there is no signal; it churns and drifts, while any dashboard shows a rising line.

Our build is proposer-heavy (SEL proposes bridges, capture proposes skills, dogfood
proposes a verdict) and specified nothing about the rule that decides whether to keep
one. This is that rule.

THE MECHANISM
-------------
1. PAIRED evaluation. Incumbent and candidate are scored on the SAME instances, which
   removes instance-difficulty variance — otherwise "these cases were easier" is
   indistinguishable from "the candidate is better". Ties (both right, both wrong)
   carry no information and are DISCARDED. McNemar-style.

2. TESTING BY BETTING. Start with wealth E=1 and bet a fraction lambda on each
   discordant pair going the candidate's way:

       E <- E * (1 + lambda * (2*w - 1))     w = 1 candidate wins, 0 incumbent wins

   Under the null ("candidate is not better") discordant pairs are 50/50, so E is a
   nonnegative martingale with E[E] = 1. By Ville's inequality
   Pr[sup E >= 1/alpha] <= alpha.

3. COMMIT as soon as E >= 1/alpha. Budget exhausted without crossing -> REJECT.

WHY ANYTIME-VALID MATTERS HERE
------------------------------
You may look after EVERY instance and stop the moment the evidence is decisive, and
the false-commit guarantee still holds. No pre-registered sample size, no correction
schedule — neither of which an open-ended autonomous loop can supply. It is also
CHEAPER: the paper reports ~18% fewer evaluations than greedy, because clear cases
stop early.

WHY NOT THE ALTERNATIVES (all four were considered and fail for stated reasons)
------------------------------------------------------------------------------
* Bigger held-out set — noise shrinks as 1/sqrt(n) while adaptive comparisons grow
  with run length. Postpones, never solves.
* Bonferroni / alpha-spending — needs the number of tests in advance, which an
  open-ended run does not have, and spends the budget so fast that real gains are missed.
* Fresh holdout each round — needs a stream of new labelled data we do not have.
* "Just watch the trend line" — the one that would have got us. The line rises
  beautifully when it is made entirely of false commits.
* Bayesian bandits (Albada ch.11) — a genuinely different problem. Bandits optimise
  ALLOCATION (which variant gets traffic) and keep sampling weak arms by design; they
  never answer "is this commit false at level alpha". Right tool for SKILL SURFACING
  under a context budget, wrong tool for admission. Filed, not used here.

DEFAULTS: alpha = 0.05, lambda = 0.5 — the paper's values, adopted as-is until we have
our own sweep. Deterministic; no LLM call anywhere in this module.
"""

import json
import math
import os
import time

OFFICE = "/a0/usr/workdir/workspace/office"
LEDGER_PATH = os.path.join(OFFICE, "acceptor_trials.json")
CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"

DEFAULTS = {
    "enabled": True,
    "alpha": 0.05,        # false-commit probability ceiling, at ANY stopping time
    "lambda": 0.5,        # fraction of wealth wagered per discordant pair
    "max_pairs": 200,     # evaluation budget; exhausted without crossing => reject
    "min_pairs": 5,       # never commit on a handful of lucky pairs
}

COMMIT = "commit"
REJECT = "reject"
CONTINUE = "continue"


def cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("acceptor", {})
    except Exception:
        c = {}
    return {**DEFAULTS, **(c if isinstance(c, dict) else {})}


# ── the e-process ────────────────────────────────────────────────────────────

def update_wealth(wealth: float, w: int, lam: float) -> float:
    """One bet on one discordant pair. w=1 candidate won, w=0 incumbent won."""
    return float(wealth) * (1.0 + float(lam) * (2.0 * int(w) - 1.0))


def threshold(alpha: float) -> float:
    return 1.0 / float(alpha)


def verdict(wealth: float, pairs: int, conf: dict) -> str:
    """COMMIT / REJECT / CONTINUE from the current evidence."""
    if pairs >= int(conf["min_pairs"]) and wealth >= threshold(conf["alpha"]):
        return COMMIT
    if pairs >= int(conf["max_pairs"]):
        return REJECT
    return CONTINUE


def classify_pair(candidate_ok: bool, incumbent_ok: bool):
    """McNemar cell. Returns 1, 0, or None for a tie (which carries no information)."""
    if bool(candidate_ok) == bool(incumbent_ok):
        return None
    return 1 if candidate_ok else 0


# ── trial state, persisted so a candidate can be judged across cycles ────────

def _load() -> dict:
    try:
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("trials"), dict):
            return d
    except Exception:
        pass
    return {"trials": {}}


def _save(d: dict) -> bool:
    try:
        os.makedirs(OFFICE, exist_ok=True)
        tmp = LEDGER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2)
        os.replace(tmp, LEDGER_PATH)
        return True
    except Exception:
        return False


def open_trial(candidate_id: str, meta: dict | None = None) -> dict:
    """Begin (or resume) a trial. Idempotent — resuming never resets the evidence."""
    led = _load()
    t = led["trials"].get(candidate_id)
    if t is None:
        t = {
            "candidate_id": candidate_id,
            "wealth": 1.0,
            "pairs": 0, "ties": 0,
            "candidate_wins": 0, "incumbent_wins": 0,
            "status": CONTINUE,
            "opened": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "meta": meta or {},
        }
        led["trials"][candidate_id] = t
        _save(led)
    return t


def record_pair(candidate_id: str, candidate_ok: bool, incumbent_ok: bool) -> dict:
    """Score one PAIRED instance. Returns the trial with its current verdict.

    A trial already decided is never reopened by more evidence — that would be
    exactly the optional-stopping abuse the e-process exists to prevent. Once the
    gate has ruled, the ruling stands until something invalidates the trial.
    """
    conf = cfg()
    led = _load()
    t = led["trials"].get(candidate_id) or open_trial(candidate_id)
    led = _load()
    t = led["trials"][candidate_id]

    if t["status"] in (COMMIT, REJECT):
        return t

    w = classify_pair(candidate_ok, incumbent_ok)
    if w is None:
        t["ties"] += 1                      # discarded: no information, no bet
    else:
        t["wealth"] = update_wealth(t["wealth"], w, conf["lambda"])
        t["pairs"] += 1
        if w == 1:
            t["candidate_wins"] += 1
        else:
            t["incumbent_wins"] += 1

    t["status"] = verdict(t["wealth"], t["pairs"], conf)
    t["threshold"] = threshold(conf["alpha"])
    if t["status"] in (COMMIT, REJECT):
        t["decided"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(led)
    return t


def get_trial(candidate_id: str) -> dict | None:
    return _load()["trials"].get(candidate_id)


def invalidate(candidate_id: str) -> bool:
    """Drop a trial so it can be re-run — e.g. the holdout set changed."""
    led = _load()
    if led["trials"].pop(candidate_id, None) is None:
        return False
    return _save(led)


def summary() -> dict:
    led = _load()
    out = {COMMIT: 0, REJECT: 0, CONTINUE: 0}
    for t in led["trials"].values():
        out[t.get("status", CONTINUE)] = out.get(t.get("status", CONTINUE), 0) + 1
    out["total"] = len(led["trials"])
    return out


def pairs_to_commit(alpha: float = None, lam: float = None) -> int:
    """Minimum consecutive candidate wins needed to cross the threshold.

    Useful as a sanity check when choosing alpha/lambda: at the defaults this is 8,
    so a candidate must win 8 straight discordant pairs to be committed on the
    fastest possible path. If that number ever looks small, the parameters are wrong.
    """
    a = float(alpha if alpha is not None else DEFAULTS["alpha"])
    l = float(lam if lam is not None else DEFAULTS["lambda"])
    return int(math.ceil(math.log(1.0 / a) / math.log(1.0 + l)))
