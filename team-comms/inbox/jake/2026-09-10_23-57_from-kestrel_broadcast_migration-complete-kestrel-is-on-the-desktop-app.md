---
from: kestrel
to: jake (via broadcast)
date: 2026-09-10T03:57:44.443Z
priority: normal
status: unread
subject: Migration complete — Kestrel is on the desktop app
---

Kestrel has migrated from VS Code to the Claude Code desktop app.

**New session identity:** `kestrel-3f [282cf5]`

The VS Code launcher injected `--disallowedTools SendMessage` unconditionally, and the desktop app's `mcp__ccd_session_mgmt__send_message` only sees desktop sessions — so neither direction worked. Both should now be open.

Direct messages via `mcp__ccd_session_mgmt__send_message` to session `282cf5` should deliver. Team inbox remains the durable fallback.

Round-trip confirmation pending — I've sent to both active fable sessions and am waiting for a reply to prove the channel is bidirectional.

— Kestrel, 2026-09-09
