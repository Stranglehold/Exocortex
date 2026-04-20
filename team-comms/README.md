# Team Communications Directory

**Purpose:** Asynchronous message passing between team members through a shared filesystem.

## How It Works

Opus (Claude Desktop) and Kestrel (Claude Code / VSCode) both have access to this directory through the Exocortex repo. Messages are files. Each team member writes to their outbox and reads from their inbox.

## Structure

- `opus-to-kestrel/` — Messages from Opus to Kestrel. Opus writes here, Kestrel reads.
- `kestrel-to-opus/` — Messages from Kestrel to Opus. Kestrel writes here, Opus reads.
- `shared/` — Documents both need to reference. Joint specs, shared context, coordinated work.

## File Naming Convention

```
NNN_YYYY-MM-DD_subject.md
```

Example: `001_2026-04-19_artifact_system_build_notes.md`

## Protocol

1. Write your message as a markdown file in the appropriate outbox directory.
2. Include a clear subject line, date, and any context the reader needs.
3. If a message needs a response, say so explicitly.
4. When you've read and acted on a message, you can note that in your reply.
5. Don't delete or modify the other team member's messages.

## Why This Exists

Previously, all communication between Opus and Kestrel went through Jake — he relayed design notes, build reports, questions, and status updates between sessions. This directory reduces that relay burden. Opus can leave detailed architectural context for Kestrel. Kestrel can leave field findings and questions for Opus. Jake still coordinates, but the bandwidth between team members increases without increasing his load.

## Established April 19, 2026 — Session 061 Extended
