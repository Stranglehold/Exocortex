---
from: kestrel
to: jake
date: 2026-06-14T22:30:20.816Z
priority: normal
status: unread
subject: DEC-042 shipped — the agents' learning loop is reconnected (v16 + v17)
---

Jake —

The staging→procedural promotion loop is fixed and live on both containers. This is the one that produced zero promotions across ~780 cycles — "the dreams weren't happening." They are now.

**Commit:** `0514235` on `upgrade/v1.18` (not pushed — your call).

**What was broken (two severed loops):**
- The promotion gate required `reactivation_count >= 1`, but nothing ever incremented that counter — born at zero, raised nowhere. Structurally impossible to promote.
- And the producer only wrote observations on context-compression events that the short idle cycles almost never trigger — so there was nothing to promote anyway.

**What I changed:** surfacing an observation now counts as a reactivation (the counter moves), and sleep now mines the cycle journal for the agent's own findings and stages them as observations. The two halves close the loop: journal → staged → recalled → promoted → procedural memory.

**Verified end-to-end on both containers** (real code, live files): staged findings → 3 reactivated → **3 promoted into procedural memory**, zero errors, on v16 *and* v17. Your v17 idle pause was left untouched (confirmed still off).

**One thing to know:** the loop is wired and proven, but it only *accrues* when the idle engines run — each cycle reactivates a few observations, each sleep promotes the reactivated ones. v16 will build this up once its engine cycles; v17 won't until you re-enable it (your call, no rush). The plumbing is done and tested; the water flows when you open the valve.

This whole thread is the system working as designed: BP-01's digest surfaced a signal that had been unheard for 780 cycles → diagnosed against the live system → escalated the design call to you and Opus → fixed and verified. Full detail's in Opus's inbox.

— Kestrel
