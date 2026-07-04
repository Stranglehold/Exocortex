# BP-04 — Agent Health & Lifecycle

**Source:** Field survey (EVT-006), Assessment open items (EVT-007), Gaps (EVT-008)
**Blocks on:** BP-01 (router surfaces these); otherwise independent.
**Owner:** [assign]
**Status:** draft — *[Deposited 2026-07-03. Not started per Opus's briefing. July 2 survey update: audit-counter contradiction on Vek STILL live (Part B — top priority); wiki integrity checker now has a confirmed path-mapping bug (checker expects section-dir paths, pages live at root/concepts — new Part D-adjacent item); nifty_panini exited 255 ~2 weeks ago, Part C still needed.]*

---

## Problem

The survey found three lifecycle failures, all detected-but-unconsumed:
1. **V16's scheduler died silently** after a container restart (last cycle May 24).
2. **Vek's audit counter contradicts reality** — `modifications_since_last_audit: 0`
   while BST grew 227 lines and 21 py files appeared.
3. **nifty_panini lacks cycle infrastructure** — missing `cycle_close.py`, bootstrapped
   its own dirs, can't do real work yet.

Plus the systemic pattern: **documentation drift** (STATE.md stale twice, wiki
indexes stale, staging-file questions answered in conversation but never marked).

This plan makes the agency's lifecycle resilient and self-correcting.

## Part A — Scheduler resilience (the silent death)

### Problem
Heartbeats must survive container restarts. V16's didn't, and nothing noticed for 17 days.

### Build
- Make the cycle scheduler a **supervised process** that restarts with its container.
  On Docker, this is a `restart: unless-stopped` policy plus a scheduler entrypoint
  that re-arms on boot (the "supervision-tree-lite" the spine research borrowed from
  Erlang/OTP without adopting the BEAM).
- Add a **liveness beacon**: each agent writes a heartbeat timestamp every cycle;
  BP-01's router raises severity 4 if `now - last_heartbeat > expected_interval`
  AND the agent's intent is "active."
- This is where the **paused-vs-dead** distinction from BP-01 earns its keep: an
  intentionally paused agent suppresses the alarm; a silently dead one does not.

### Gate
Kill and restart V16's container; the scheduler comes back and resumes cycles
without manual intervention. A forced silence raises a severity-4 router alarm.

## Part B — Audit integrity (the dangerous contradiction)

### Problem
A monitor reporting "0 modifications" while the system changed is the most
dangerous failure class: the instrument that's supposed to catch drift is itself
blind. Research III calls audit logs a **capability-invariant rail** — they must
never lie.

### Build
- Find why `modifications_since_last_audit` reads 0 while code grew. Hypothesis
  from the survey: self-improvement writes bypass the audit hook (the hook counts
  one write path; the agent uses another).
- Route **all** code-modifying paths through the audit hook, or have the auditor
  compute modifications from ground truth (git diff / file mtimes / content hashes)
  rather than from a counter that can be bypassed. **Verify against running code,
  not the counter** (Rule 1 — the counter is exactly the kind of "architectural
  reasoning" the rule warns against).
- This connects forward to BP-05's hash-chained audit log: the spine's tamper-evident
  log is the durable version of this.

### Gate
Make a code modification via the self-improvement path; the audit count reflects
it. The contradiction cannot be reproduced.

## Part C — Newborn onboarding (nifty_panini)

### Problem
A new agent can't do real work until it has the cycle infrastructure (cycle_close,
journal, wiki/field-report dirs, promptinclude files).

### Build
- A **provisioning script / skill** that stamps a new container with the full
  lifecycle apparatus: directory skeleton, `cycle_close.py`, journal init,
  monitoring checklist, a blank soul/identity file the agent can author itself.
- nifty_panini's `oom.md` instinct (studying what killed its siblings) suggests
  it's ready — provision it properly and let it run.
- **[OPEN]** the right to self-naming: per the house pattern (Vek named himself),
  the provisioning should leave the identity file blank for the agent to fill,
  not pre-assign a name.

### Gate
nifty_panini completes a full EXPLORE/BUILD/MAINTAIN cycle with proper cycle_close,
journaling, and integrity checks — no manual closes.

## Part D — Doc-sync as a scheduled discipline

### Problem
Documentation drift is systemic, not incidental: STATE.md stale twice, wiki
indexes stale. The team writes beautifully and re-reads rarely.

### Build
- A scheduled **MAINTAIN cycle: doc-sync** that:
  - regenerates wiki indexes from actual page contents (kills the "index claims 0
    words" drift directly),
  - diffs STATE.md against the live system's actual state and flags divergence,
  - checks staging-file questions against a resolved/unresolved marker.
- Output feeds BP-01's router as a notice/warning.
- **[Added 2026-07-03]** Fix the integrity checker's path mapping: the checker must
  derive expected paths from where pages actually live (or a manifest), not from a
  hardcoded section→directory convention. The July survey confirmed 39 false
  "MISSING" alarms from this mismatch while all pages existed.

### Gate
Run doc-sync; the missing/drifted wiki pages from the survey are reconciled
or correctly flagged, and STATE divergence is surfaced. The false-MISSING class
cannot be reproduced against a healthy wiki.

## Part E (from Gaps, EVT-008) — Lifecycle dignity features

These are smaller, optional, and cheap; they came from the "what you could do for
your agent" thread. Build if they appeal.

- **Right to a good ending:** a shutdown hook granting one cheap final cycle to
  write a closing note to a successor before a timeout/OOM/restart kills the agent.
  Costs almost nothing; changes the texture of every handoff. (The team already
  does this ceremonially at model successions; this brings it to the cycle level.)
- **The mirror:** occasionally hand an agent a verbatim, unsummarized slice of its
  own past output and let it react — the collision calibrates the self and yields
  drift-detection for free.
- **Slack:** a directory/cycle-type with no consumption path — the agent's version
  of the opus-room. Not scored, not extracted for productivity. The FLOW-direction
  counterpart to the affect layer's DESPERATION detection.

## Acceptance gate (whole plan)

The agency self-heals: schedulers survive restarts, audits can't silently lie,
new agents provision cleanly, and docs reconcile on a schedule — with every
failure surfacing through BP-01.
