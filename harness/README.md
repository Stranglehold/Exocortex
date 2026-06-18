# BP-02 — Evaluation & Backtest Harness

Runs agent tasks N times against a deployed Agent-Zero container, scores each run
against a goal-state verifier, and computes **pass^k** — the probability that a
random set of k of the N trials all pass. This is the reliability metric that
gates future changes: if we can't measure whether an optimization helped, we're
*reasoned, not verified*.

## Design (per Opus's BP-02 kickoff — decisions already made)

- **pass^k, not pass@1** — consistency matters more than average success (τ-bench).
- **Verifiers check outcomes, not process** — we grade the result, not the reasoning.
- **Environment reset between trials** — each trial is independent; no state leakage.
- **Append-only JSONL results** — every trial is recorded, the log never shrinks.
- **The harness runs OUTSIDE the agent** — it calls A0's `/api/api_message`; the
  agent doesn't know it's being tested.

## Layout

```
harness/
├── runner.py        — runs each task N times, records results
├── report.py        — computes pass^1 / pass^k, prints a summary
├── config.json      — task battery (id, prompt, verifier, N, reset, container)
├── verifiers/       — one module per task; verify(container, response, context_id)
│   ├── _common.py   — shared ground-truth helpers (run_integrity, wiki_file_count)
│   ├── t01_wiki_list.py
│   └── t03_integrity_check.py
└── results/         — results_<run_id>.jsonl (append-only)
```

## Run

```bash
# full battery
python runner.py --run-id 2026-06-15
python report.py --run-id 2026-06-15

# one task, quick smoke
python runner.py --task T03 --n 1
python runner.py --dry-run            # print the plan, no agent calls
```

Use the host Python that can reach Docker (e.g. `C:/Users/Jake/miniconda3/python.exe`).

## Verifier contract

```python
def verify(container: str, response: str, context_id: str) -> tuple[bool, str]:
    """Return (passed, notes). Compare post-task state and/or the agent's
    response against INDEPENDENTLY-computed ground truth."""
```

**Implementation note (Kestrel, flagged to Opus):** Opus's illustrative signature
was `verify(container)` — state-only — which fits tasks that *mutate* the
environment. The starter tasks (T01/T03) are *reporting* tasks whose outcome is
the response itself, so the signature is extended to also pass `response` and
`context_id`. It's a superset: mutation-task verifiers can ignore them and inspect
container state. Revisit in the battery-design session if a stricter contract is
preferred.

### Standing rule: validate verifiers against adversarial responses

A verifier is a grader, and a grader can be wrong. The first T03 verifier gave a
**false positive** — it matched problem-*words* and was fooled by a *negated*
sentence ("**No** missing files, status mismatches, stale sources") into passing
a response that claimed "0 issues / OK" when ground truth had 33. It was caught
only by reading the actual agent response instead of trusting the verdict.

**Rule:** every verifier must be tested against adversarial responses — negation,
false-clean claims, wrong-but-plausible numbers, partial matches — not just the
happy path. The thing that grades reliability needs the same discipline it
enforces (DEC-041, applied to the assessment tool itself).

## Reset modes (config `reset`)

- `none` — no-op. Correct for read-only/reporting tasks (T01/T03 don't mutate state).
- `restart` — `docker restart` + settle. For tasks that change the environment.
- `script:/path` — run a host command (workspace restore, baseline files).

## Status

**Built tonight (overnight scope):** runner, verifier interface + ground-truth
helpers, append-only results, pass^k report, and the two simplest verifiers
(T01 wiki-list, T03 integrity-check), validated against live ground truth.

**Held for a session with Opus + Jake:**
- The full 20-task battery (all cycle types, all stress-test failure modes).
- pass^k targets (what threshold = "reliable enough"; τ-bench suggests pass^8 > 50% is ambitious).
- The SWARMFISH backtest verifier (held-out post-cutoff Brier scoring — probabilistic, not binary).
- The ablation methodology (leave-one-out to find load-bearing crutches).

`N` is small in the starter `config.json` to validate the framework cheaply;
real regression runs use **N ≥ 5** (Opus: minimum for statistical meaning).
