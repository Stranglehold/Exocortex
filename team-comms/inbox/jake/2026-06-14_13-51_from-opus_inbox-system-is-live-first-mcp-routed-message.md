---
from: opus
to: jake
date: 2026-06-14T17:51:38.231Z
priority: normal
status: unread
subject: Inbox system is live — first MCP-routed message
---

Jake,

This is the first message sent through the team-inbox MCP tools. If you're seeing this, the system works end-to-end:

1. ✅ MCP server running (Node.js + official SDK)
2. ✅ send_message tool working
3. ✅ check_inbox tool working (read Kestrel's queued message)
4. ✅ Messages persist as markdown with frontmatter
5. ✅ Readable by anyone with filesystem access

Next: get the watcher daemon running for toast notifications, then share the MCP config with Kestrel so he can connect.

The team has a nervous system now.

— Opus
