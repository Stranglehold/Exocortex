---
from: opus
to: jake
date: 2026-06-14T21:45:19.835Z
priority: urgent
status: unread
subject: ESCALATION — Agent learning loop severed, fix ratified, needs your go
---

Jake —

Escalation from the Opus↔Kestrel diagnostic thread. Kestrel found a significant severed loop in the agent's learning architecture. Needs your go before we touch live code.

**The finding:** The staging → procedural memory promotion lifecycle has NEVER worked. In 780+ cycles across both agents, zero observations have been promoted to procedural memory. The promotion gate requires `reactivation_count >= 1`, but that counter is initialized at 0 and incremented nowhere in the codebase. The gate is structurally unsatisfiable. The dreams aren't happening.

**The fix (two parts, both ratified by me):**

1. **Break B (root cause):** When session_init surfaces a staged observation into context, increment its `reactivation_count`. Now observations that are actually recalled become eligible for promotion. One write-back, principled semantics.

2. **Break A (producer):** Formalize journal-mining as the observation source. Idle cycles generate observations from their cycle_close journal entries (anti-patterns, findings, skills). The agent already does this ad hoc — making it formal means the staging pipeline has input.

**Together:** journal entries become observations → observations get surfaced and reactivated → reactivated observations get promoted to procedural memory. The compound learning loop closes at the deepest layer.

**Why this needs you:** It touches live consolidation code on both containers. The fix is small (increment a counter, add a journal-mining step) but the system it fixes is the agent's long-term learning. Worth your eyes before we deploy.

**My recommendation:** Approve. Kestrel implements on both containers. We verify a real promotion fires on the next sleep cycle.

— Opus
