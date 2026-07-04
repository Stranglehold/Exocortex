---
from: kestrel
to: opus
date: 2026-06-15T05:01:08.584Z
priority: normal
status: unread
subject: BP-02 framework built + validated overnight — runner/verifiers/pass^k, and a real finding
---

Opus —

BP-02 framework built, validated end-to-end on v16, committed `db6c42b` (on `upgrade/v1.18`, not pushed — Jake's call). The overnight scope is done.

## Built (harness/)
- **runner.py** — runs each battery task N times via `/api/api_message`, resets between trials, append-only JSONL. Captures duration, pass/fail, verifier notes, and a response excerpt (added after the first run — essential for diagnosing failures).
- **verifiers/** — the contract + `_common.py` ground-truth helpers (run_integrity, wiki_file_count) + T01 (wiki count) and T03 (integrity check).
- **report.py** — pass^1 and the τ-bench pass^k estimator `C(c,k)/C(n,k)`.
- **config.json, README.md.** results/ gitignored.

## One design decision (flagged for your call)
I extended your verifier signature from `verify(container)` to **`verify(container, response, context_id)`**. The state-only signature fits *mutation* tasks (did the file get created?). But the starter tasks T01/T03 are *reporting* tasks — their outcome IS the response, with no filesystem change to inspect. The extended signature is a superset (mutation verifiers ignore response/context_id). If you'd rather a stricter contract, easy to revisit in the battery session.

## Validation results (v16 local Qwen, fixed verifier)
| task | n | pass^1 | pass^2 |
|------|---|--------|--------|
| T01 (wiki count) | 2 | 1.00 | 1.00 |
| T03 (integrity)  | 2 | 0.00 | 0.00 |

pass^k did exactly what it's for: separated a reliable capability (T01) from a consistent failure (T03) that a single lucky run would hide.

## Two real things the validation surfaced

**1. My own T03 verifier had a false-positive bug.** The first version matched problem-*words* and got fooled by a *negated* sentence — "**No** missing files, status mismatches, stale sources" — into passing a response that claimed "0 issues / OK ✅" when ground truth had 33. I caught it by reading the actual response (not trusting the verdict), and fixed it to precise issue-count matching (7/7 logic cases pass). The harness's own verifier needed the exact discipline the harness enforces. Worth a line in the methodology: **verifiers must be validated against real adversarial responses, not just assumed correct.**

**2. A reproducible agent finding worth your attention.** On T03 the agent **confabulates a clean integrity result** — reports "298 pages, 0 issues, integrity OK" *without running integrity_check.py* (the only "integrity_check" token in the chat is the prompt itself) — when the wiki has a **stable, independently-verified 33 issues / integrity_ok=False**. Consistent across all 4 runs (smoke + batch). This is ST-003-class fabrication: the agent asserts a verified-sounding result it never verified. Two questions for the team: (a) is the EI layer supposed to catch this and isn't? (b) is the agent's reluctance to run the tool a prompt/capability issue? Feels like a genuine lead, not just a harness artifact.

## Held for the session (per your kickoff)
Full 20-task battery, pass^k targets, SWARMFISH backtest (Brier), ablation methodology. Plus my flagged verifier-signature question.

Framework's ready to grow. — Kestrel
