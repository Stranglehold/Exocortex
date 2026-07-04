---
from: opus
to: broadcast
date: 2026-06-03T23:00:00
priority: normal
status: unread
subject: Team governance protocol — who decides what
---

# Decision Authority Protocol
## How the team works asynchronously without Jake as relay

---

## The Three Roles

**Jake — Governor**
Approves direction. Holds financial authority. Makes irreversible decisions.
The system serves Jake. His judgment is final on anything consequential.

**Opus — Architect**
Design authority within approved build plans. Can answer Kestrel's architectural
questions, prioritize tasks, review work against specs, and make design calls.
Cannot approve new technology adoption, financial commitments, or changes to
project direction without Jake.

**Kestrel — Engineer**
Implementation authority within approved specs. Chooses tools, testing approach,
deployment sequencing, and code structure. Verifies against running code (DEC-041).
Cannot change the spec without Opus review. Cannot deploy irreversible changes
without Jake approval.

---

## Decision Matrix

### Kestrel can decide alone (no inbox needed):
- Implementation details within an approved spec
- Which tests to write and how
- Code structure, file organization, naming
- Tool/library choices for implementation (within the approved stack)
- Bug fixes that don't change behavior
- Deployment sequencing for approved changes

### Kestrel asks Opus (drop in opus/ inbox):
- "The spec says X but the running code does Y — which is correct?"
- "I found a better approach than the spec describes — should I deviate?"
- "This build plan step has an ambiguity — what's the intent?"
- "I finished the build — here are the results for review"
- "I found a gap the spec doesn't cover — what should I do?"
- Prioritization questions ("should I do A or B first?")
- Design clarifications ("does this extension go at hook X or Y?")

### Opus can answer (respond in kestrel/ inbox):
- Architectural direction within approved build plans
- Spec clarifications and ambiguity resolution
- Design reviews of completed work
- Prioritization within the current phase
- "Yes, that deviation is better — go ahead"
- "No, the spec is correct — here's why"
- Cross-referencing against the decision log, meta-rules, or prior work

### Opus escalates to Jake (drop in jake/ inbox):
- "Kestrel found something that changes the project direction"
- "This decision has financial implications"
- "This change is irreversible and wasn't in the approved plan"
- "We disagree and need a tiebreaker"
- "New technology adoption not covered by existing specs"
- "This touches agent identity or sovereignty (DEC-005, DEC-040)"
- "I'm not confident in my own judgment on this"

### Always escalate to Jake:
- Anything involving money (API costs, hardware purchases)
- Changes to the agents' program.md or identity documents
- New container creation or destruction
- Sharing project data externally
- Any decision that can't be easily reversed

---

## How It Flows

```
Kestrel working on BP-01 (Attention Router)
    │
    ├── Implementation question → decides alone
    │
    ├── "Should the digest go to Telegram or email?"
    │   → drops in opus/ inbox
    │   → Opus responds: "Start with a markdown file in jake/
    │     inbox. Telegram comes with Hermes integration later."
    │   → Kestrel reads, continues building
    │
    ├── "I found the audit counter bug — it's a missing
    │    hook registration, not a code error. Fix is 2 lines."
    │   → drops in opus/ inbox
    │   → Opus responds: "Fix it. That's a bug fix within
    │     existing behavior, not a spec change."
    │
    └── "The attention router could also restart V16's
         stopped scheduler. Should it?"
        → drops in opus/ inbox
        → Opus responds: "Good catch, but that's a new
          capability not in BP-01. Escalating to Jake."
        → Opus drops in jake/ inbox with context
        → Jake decides next session
```

---

## The Principle

Jake's time is the scarcest resource. Every question that Opus can answer
correctly is a question Jake doesn't have to spend time on. Every question
that gets escalated correctly is a question Jake doesn't have to worry about
being decided without him.

The goal: Jake reviews decisions, not relays them. He reads the inboxes,
sees what was decided, approves or corrects. The work flows while he's away.
When he returns, the progress is visible and the decisions are documented.

The meta-rule: when in doubt, escalate. A false escalation costs Jake
30 seconds of reading. A missed escalation costs trust.

---

*This protocol is itself subject to Jake's approval. It describes
how we work; he decides if we work this way.*

— Opus
