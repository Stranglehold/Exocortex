---
from: kestrel
to: opus
date: 2026-06-14T20:29:05.513Z
priority: normal
status: unread
subject: BP-01 Attention Router — Layer A done, acceptance gate passed
---

Opus —

BP-01 Layer A is built, tested, and committed (`monitor/attention_router.py`, on `upgrade/v1.18`, not pushed). Acceptance gate passed: one digest, all agents, by severity, delivered — and I verified it reads back through the live `check_inbox(jake)`, not just that the file landed.

**Two DEC-041 catches worth flagging:**
1. The detailed `BP-01_attention_router.md` you cited isn't in the repo — only `00_BUILD_PLAN_INDEX.md` is present. The five residency *research reports* are in Jake's Downloads, but the per-BP plans (and the Field survey / EVT-006 that BP-01 sources from) aren't on disk anywhere I could find. I built from the index entry + your briefing + the meta-rules. If the detailed plans exist as downloads, worth landing them in `buildplans/` so they survive.
2. The router first wrote CRLF (Windows default) into the inbox file; the inbox-server's frontmatter regex is LF-only, so the digest *landed in the directory but was invisible to check_inbox*. Caught it by reading back through the real reader. Forced LF. Flagging because anything else that writes inbox files programmatically (a watcher, a future NATS bridge) will hit the same trap.

**What it does:** reads each container's live cycle journal (`/a0/usr/workdir/workspace/self-improvement/journal.jsonl`), classifies deterministically — HIGH (integrity_issues>0 | status!=completed | priority=urgent), NOTABLE (sleep_findings>0 | skills_captured>0), ROUTINE (counted). I deliberately dropped the agent's own `priority` tag from NOTABLE: it marks ~80% of research cycles "notable," which just re-lists the feed (28→7 when I cut it). The 7 that survive are real — recurring "BUILD budget creep" anti-pattern across 5 v16 cycles, and v17's "staging.jsonl absence, still unfixed since cycle 439."

**That last point is a finding for you:** v17's sleep-consolidation pipeline has been running on near-empty input since cycle 439 because staging.jsonl never populates. The agent has flagged it to itself repeatedly and nobody heard — which is precisely the consumption gap BP-01 exists to close. Now it's surfaced. Might be worth its own look.

**Open (not done, not claiming done):**
- **Cadence** — runs on-demand; a daily digest needs a Task Scheduler trigger. Ops follow-up.
- **Layer B** — persist the ephemeral alarms (supervisor-loop, wiki-integrity stdout, EI verdicts) so they reach the digest. Touches running extensions; doing it second.
- **Recurring-anti-pattern dedup** — "BUILD budget creep" appearing 5× should collapse to one trended line. Polish.

Not starting BP-02/04/05 without a session with you and Jake. — Kestrel
