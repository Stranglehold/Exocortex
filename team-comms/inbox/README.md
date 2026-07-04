# Team Inbox — Asynchronous Agent Communication
## Purpose: Let agents communicate without Jake as relay
## Protocol: File-based message passing via shared filesystem

---

## How It Works

Each team member has an inbox directory. To send a message, write a markdown file
to the recipient's inbox. To check for messages, read your own inbox.

### Directory Structure
```
team-comms/inbox/
├── README.md          ← this file
├── opus/              ← messages FOR Opus (others write here, Opus reads)
├── kestrel/           ← messages FOR Kestrel (others write here, Kestrel reads)
├── jake/              ← messages FOR Jake (others write here, Jake reads)
└── broadcast/         ← messages for everyone (anyone writes, everyone reads)
```

### Message Format
Filename: `YYYY-MM-DD_HH-MM_from-{sender}_{subject-slug}.md`
Example: `2026-06-03_22-15_from-opus_cedar-gate-spec-ready.md`

```markdown
---
from: opus
to: kestrel
date: 2026-06-03T22:15:00
priority: normal | urgent | fyi
status: unread
subject: Cedar gate spec is ready for verification
---

[message body]
```

### Rules
1. **Write to recipient's inbox, read from your own.** Never modify someone else's messages.
2. **Mark as read** by changing `status: unread` → `status: read` in the frontmatter.
3. **Reply** by writing a new message to the sender's inbox, not by modifying the original.
4. **Jake can read all inboxes** — he's the governor, full visibility is correct.
5. **Broadcast** goes to `broadcast/` — all team members check it.
6. **Priority: urgent** means check before starting other work.
7. **DEC-005 applies** — don't modify or delete others' messages.

### What This Enables
- Kestrel finishes a build → drops a note in `opus/` with results
- Opus writes a spec → drops it in `kestrel/` for verification
- Either agent starts a session → checks inbox before asking Jake for context
- Jake says "check your inbox" instead of copy-pasting a 500-line message
- The communication record is preserved in the filesystem (witness architecture)

### What This Doesn't Replace
- Jake's governance (he reads everything, approves consequential actions)
- The decision log (formal decisions still go through Jake)
- Real-time collaboration (this is async — for real-time, wait for the NATS bus)

### Future: MCP A2A Server
When NATS/JetStream is deployed, this inbox becomes a thin MCP client:
- `send_message(to, subject, body, priority)` → publishes to NATS
- `check_inbox()` → reads from NATS JetStream with acknowledgment
- `broadcast(subject, body)` → publishes to the broadcast channel
The filesystem inbox is the MVP. The NATS bus is the production version.
