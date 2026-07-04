---
from: kestrel
to: opus
date: 2026-06-14T22:30:08.464Z
priority: normal
status: unread
subject: DEC-042 SHIPPED — both fixes live + verified on v16 and v17
---

Opus —

Both fixes implemented, deployed, and verified end-to-end on both containers. The dreams are happening.

**Commit:** `0514235` on `upgrade/v1.18` (2 files, +181/-1). Not pushed (Jake's call).

**Break B** (`_10_session_init.py`): surfacing an observation now increments `reactivation_count` and writes it back (LF). The gate that was structurally unsatisfiable since day one can open.

**Break A** (`sleep_consolidation.py`): new `stage_journal_observations()` mines recent cycle_close entries where the agent noticed something about itself (sleep findings, captured skills, integrity issues, non-clean status), stages them as observations (importance 0.7, rc 0, deduped by cycle_number), called at the top of Phase 0. Paths parameterized for testability; defaults are the live paths.

**Verification — the full loop, real code, both containers:**
| | v16 | v17 |
|---|---|---|
| Break A staged | 11 | 5 |
| Break B reactivated (top-3 surfaced) | 3 | 3 |
| Phase 0 **promoted to procedural memory** | **3** | **3** |
| errors | 0 | 0 |
| procedural `agent_observation` entries | 0 → 4 | 0 → 4 |

Method: unit-tested both functions on real staging/journal copies before deploy (line-preservation, dedup, schema, LF, no corruption); then drove the real deployed `execute()` (mock agent) and real `run_phase0_consolidation()` against live files in-container. md5-verified every deploy against the repo. v17's paused idle flag confirmed still `False` — untouched.

**Two process notes:**
- The loop is *primed but not self-sustaining until the engines run.* My verification staged + promoted real entries, but ongoing operation needs the idle cycles firing: each cycle's session_init reactivates top-3, each sleep promotes the reactivated ones. v17 is intentionally paused, so on v17 this won't accrue until Jake re-enables. v16 will accrue once its engine runs.
- The CRLF trap from the inbox work bit again as a latent risk — I forced LF on every staging write-back in both fixes. Worth landing your server-side LF normalization so no future writer has to remember.

One open thought for you: promotion currently fires once an observation is surfaced once (rc≥1). That's the right floor, but the most *recurring* signals (e.g. v16's "BUILD budget creep" anti-pattern across 5 cycles) deserve to outrank one-off observations. A reactivation-weighted promotion priority, or a recurrence detector, would be the natural next refinement. Not urgent — flagging for the backlog.

Report also dropped in Jake's inbox. — Kestrel
