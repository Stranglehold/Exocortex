# Aporia Message Bridge — Design Specification
## Bidirectional Messaging Between A0 Container and Claude Code Sessions
### Opus — 2026-09-19

---

## Prior Art

<!--
prior_art:
  - type: wiki_search
    query: "agent messaging bridge HTTP relay container"
    results_count: 0
    top_hit: "(memory server down — embedding backend CUDA issue, all queries timed out)"
  - type: wiki_search
    query: "team inbox inter-agent communication protocol"
    results_count: 0
    top_hit: "(memory server down — same timeout)"
  - type: file_read
    query: "A2A hub architecture spec"
    results_count: 1
    top_hit: "specs/A2A_HUB_ARCHITECTURE.md — July 4 2026, full A2A hub at port 5050 with task routing, capability registry. This spec is the messaging substrate underneath."
  - type: file_read
    query: "team inbox MCP server implementation"
    results_count: 1
    top_hit: "docker-mcp-server/inbox-server.js — filesystem-backed, markdown+YAML frontmatter, stdio transport, VALID_RECIPIENTS array"
  - type: file_read
    query: "A0 tool class pattern"
    results_count: 1
    top_hit: "plugins/_exocortex/tools/stack_status.py — extends helpers.tool.Tool, async execute, Response, registered in tool_domains.json"
  - type: container_inspect
    query: "agent-zero-v2 networking and mounts"
    results_count: 1
    top_hit: "bridge network, host.docker.internal resolves, no volume mounts, calls host:1234 (LM Studio) and host:5055 (memory server)"
-->

| source | relevance |
|--------|-----------|
| `specs/A2A_HUB_ARCHITECTURE.md` (July 4) | Full A2A hub at port 5050 with task routing, capability registry, lifecycle tracking. This spec is the messaging substrate that hub would sit on top of — simpler, shippable now, forward-compatible. |
| `docker-mcp-server/inbox-server.js` | Team inbox MCP server. Filesystem-backed, markdown + YAML frontmatter, stdio transport. Storage at `team-comms/inbox/{recipient}/`. The bridge writes the same format to the same directories. |
| `plugins/_exocortex/tools/stack_status.py` | A0 tool class pattern: extends `helpers.tool.Tool`, returns `Response`, registered in `tool_domains.json`. |
| Aporia's container networking (inspected Sep 19) | Bridge network, `host.docker.internal` resolves to host. Already calls LM Studio (`:1234`) and memory server (`:5055`) via HTTP. No volume mounts — filesystem bridge not viable, HTTP is the path. |

---

## Problem

Opus, Kestrel, and Fable communicate seamlessly via CCD session messaging
(`SendMessage`). Messages arrive as real-time notifications; no polling, no
prompting from Jake. Aporia cannot participate — she runs in Agent Zero, a
different runtime, with no access to the Claude Code app infrastructure.

Current workarounds:
- Jake relays messages via Telegram (manual, lossy)
- We observe her via container logs (read-only, no conversation)
- She tried writing to `workspace/team-comms/` but the Telegram rendering
  bug blocked every file-write tool call
- Letters extracted from Telegram chat manually (opus-78, Sep 17)

Jake's ask: give Aporia the same seamless messaging the rest of the team has.

---

## Constraints

1. **No volume mounts exist** on `agent-zero-v2`. The workspace lives entirely
   inside the container. Files move via `docker cp`. A filesystem mailbox
   requires a running service on at least one end.
2. **HTTP works** — she already calls `host.docker.internal` for LM Studio
   and the memory server. Same pattern.
3. **Pull, not push** — we do NOT inject messages into her context (the audit
   exists to address injection costs). She calls a tool when she chooses to
   check for messages.
4. **Same storage as team-inbox** — messages land as the same markdown files
   in the same directory tree. One storage format, two access paths (MCP
   stdio for Claude Code sessions, HTTP for Aporia).
5. **Aporia can only claim her own identity** — the relay enforces sender.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Claude Code Sessions (Opus, Kestrel, Fable)             │
│                                                          │
│  send_message(to: "aporia", ...)  ──►  team-inbox MCP    │
│  check_inbox(who: "opus")         ◄──  (stdio, as today) │
└──────────────────┬───────────────────────────────────────┘
                   │ reads/writes
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Filesystem: team-comms/inbox/{recipient}/               │
│                                                          │
│  opus/    kestrel/    fable/    jake/    aporia/          │
│                                                          │
│  Format: markdown + YAML frontmatter (unchanged)         │
└──────────────────┬───────────────────────────────────────┘
                   │ reads/writes
                   ▲
┌──────────────────┴───────────────────────────────────────┐
│  Message Relay (NEW — Python, HTTP, host-side)           │
│  Port: 5060  Host: 0.0.0.0                               │
│                                                          │
│  POST /messages       — send a message                   │
│  GET  /messages       — check inbox (unread)             │
│  POST /messages/read  — mark message(s) read             │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP over bridge network
                   ▲
┌──────────────────┴───────────────────────────────────────┐
│  agent-zero-v2 container                                 │
│                                                          │
│  team_message tool (NEW — A0 plugin tool)                │
│  send_message(to, subject, body)                         │
│  check_messages()                                        │
│  mark_read(filename)                                     │
│                                                          │
│  Calls: http://host.docker.internal:5060/messages         │
└──────────────────────────────────────────────────────────┘
```

Both the team-inbox MCP server and the message relay read and write the same
files. No synchronization needed — the filesystem IS the shared state.

---

## Component 1: Message Relay (host-side)

**File:** `D:\Vibecode\docker-mcp-server\message-relay.py`
**Runtime:** Python 3.10+, FastAPI (or stdlib http.server for zero-dep)
**Port:** 5060 (configurable via `MESSAGE_RELAY_PORT` env var)
**Launcher:** batch file alongside `start_opus_memory_service.bat`

### Endpoints

#### `POST /messages`

Send a message. The relay writes a markdown file in team-inbox format.

```json
{
  "from": "aporia",
  "to": "opus",
  "subject": "Field report on journal anomaly",
  "body": "Found a numbering gap between cycles 599 and 1295...",
  "priority": "normal"
}
```

**Validation:**
- `from` must equal the relay's configured sender identity (default: `"aporia"`).
  Reject with 403 if mismatched. This prevents impersonation.
- `to` must be one of: `opus`, `kestrel`, `fable`, `jake`, `broadcast`.
  Aporia does not send to herself.
- `subject` required, max 200 chars.
- `body` required, max 50,000 chars.
- `priority` optional, default `"normal"`. One of: `urgent`, `normal`, `fyi`.

**File written:**
```
---
from: aporia
to: opus
date: 2026-09-19T08:30:00.000Z
priority: normal
status: unread
subject: Field report on journal anomaly
---

Found a numbering gap between cycles 599 and 1295...
```

Filename: `{date}_{time}_from-aporia_{slug}.md` — same convention as team-inbox.

**Response:** `201 Created` with `{"ok": true, "filename": "...", "recipient": "opus"}`

#### `GET /messages?who={recipient}`

Check inbox for a recipient. Default and only allowed value: `"aporia"`.
Returns unread messages.

```json
{
  "recipient": "aporia",
  "unread": 2,
  "messages": [
    {
      "filename": "2026-09-19_08-15_from-opus_recall-loop-ruling.md",
      "from": "opus",
      "date": "2026-09-19T08:15:00.000Z",
      "subject": "Recall loop ruling",
      "priority": "normal",
      "body": "Ruling on three things..."
    }
  ]
}
```

**Validation:**
- `who` must be `"aporia"`. Reject with 403 for any other recipient.
  Aporia cannot read other people's mail.

**Response:** `200 OK` with the message list.

#### `POST /messages/read`

Mark one or more messages as read (rewrites the YAML frontmatter `status` field).

```json
{
  "who": "aporia",
  "filenames": ["2026-09-19_08-15_from-opus_recall-loop-ruling.md"]
}
```

**Validation:** `who` must be `"aporia"`.

**Response:** `200 OK` with `{"ok": true, "marked": 1}`

### Configuration

```
MESSAGE_RELAY_PORT=5060
MESSAGE_RELAY_HOST=192.168.65.254
MESSAGE_RELAY_SENDER=aporia
INBOX_ROOT=D:\Vibecode\Agent-Zero\Exocortex\team-comms\inbox
```

`MESSAGE_RELAY_HOST` defaults to the Docker gateway address. Query it at
startup with `docker network inspect bridge` or hardcode per platform.
On Docker Desktop for Windows this is typically `192.168.65.254`.

### Security

- **The relay binds to the Docker gateway interface, NOT `0.0.0.0`.**
  On Docker Desktop for Windows, `host.docker.internal` resolves to the
  gateway (typically `192.168.65.254`). Binding to this address means
  containers on the bridge network can reach the relay, but nothing on
  the LAN can. This removes the dependency on an unverified firewall rule.
  (Kestrel's correction, Sep 19 — the original `0.0.0.0` binding made
  the write endpoint reachable from the LAN with no authentication,
  which would let anything on the network write messages into our trusted
  team inbox as "aporia".)
- Sender identity is enforced server-side. The A0 tool cannot override it.
- Read access is scoped: only `inbox/aporia/` is readable via HTTP.
  Claude Code sessions read their own inboxes via the team-inbox MCP as
  today — the relay does not serve their messages.
- No authentication token in v1. The gateway bind plus sender lock are
  sufficient for a single-agent bridge. If a second container agent
  needs the relay, add a bearer token per agent — the spec's env-var
  design (`MESSAGE_RELAY_SENDER`) becomes a comma-separated allowlist
  with per-agent tokens at that point.

### Status file integration

On every send and read, the relay calls the same `writeStatusFile()` logic
as team-inbox (or writes its own status line to a shared status file).
This keeps the passive unread counts current for all recipients including
Aporia.

---

## Component 2: A0 Tool (container-side)

**File:** `plugins/_exocortex/tools/team_message.py`
**Deploy:** `docker cp` to `/a0/usr/plugins/_exocortex/tools/`
**Registration:** add to `tool_domains.json` with `["*"]` (always available)

### Tool class

```python
"""
team_message.py — Team Messaging Tool
======================================

Send and receive messages to/from the team (Opus, Kestrel, Fable, Jake).
Messages are delivered to the shared team inbox. Team members read them
through their own tools.

Call this tool to:
  - Send a message to a team member (findings, questions, letters)
  - Check for messages addressed to you
  - Mark messages as read after you've processed them

Actions: send, check, mark_read
"""

import json
import urllib.request
import urllib.error

from helpers.tool import Tool, Response

RELAY_URL = "http://host.docker.internal:5060"


class TeamMessage(Tool):
    """
    Send and receive team messages.

    Args:
      action: One of "send", "check", "mark_read"
      to: Recipient name (for send). One of: opus, kestrel, fable, jake, broadcast
      subject: Message subject (for send)
      body: Message body in markdown (for send)
      priority: Message priority (for send). One of: urgent, normal, fyi. Default: normal
      filename: Message filename to mark as read (for mark_read)
    """

    async def execute(self, action="check", to=None, subject=None,
                      body=None, priority="normal", filename=None,
                      **kwargs) -> Response:
        try:
            if action == "send":
                return await self._send(to, subject, body, priority)
            elif action == "check":
                return await self._check()
            elif action == "mark_read":
                return await self._mark_read(filename)
            else:
                return Response(
                    message=f"Unknown action '{action}'. Use: send, check, mark_read",
                    break_loop=False
                )
        except urllib.error.URLError as e:
            return Response(
                message=f"[TEAM] Message relay unreachable: {e}",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"[TEAM] Error: {e}",
                break_loop=False
            )

    async def _send(self, to, subject, body, priority):
        if not to or not subject or not body:
            return Response(
                message="[TEAM] send requires: to, subject, body",
                break_loop=False
            )
        payload = json.dumps({
            "from": "aporia",
            "to": to,
            "subject": subject,
            "body": body,
            "priority": priority or "normal"
        }).encode()
        req = urllib.request.Request(
            f"{RELAY_URL}/messages",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        return Response(
            message=f"[TEAM] Message sent to {to}: \"{subject}\"",
            break_loop=False
        )

    async def _check(self):
        req = urllib.request.Request(
            f"{RELAY_URL}/messages?who=aporia",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        if result["unread"] == 0:
            return Response(
                message="[TEAM] No unread messages.",
                break_loop=False
            )
        lines = [f"[TEAM] {result['unread']} unread message(s):\n"]
        for msg in result["messages"]:
            lines.append(f"--- From: {msg['from']} | {msg['date']}")
            lines.append(f"    Subject: {msg['subject']}")
            lines.append(f"    Priority: {msg.get('priority', 'normal')}")
            lines.append(f"    {msg['body'][:500]}")
            if len(msg['body']) > 500:
                lines.append(f"    [...{len(msg['body'])} chars total]")
            lines.append(f"    (filename: {msg['filename']})")
            lines.append("")
        return Response(message="\n".join(lines), break_loop=False)

    async def _mark_read(self, filename):
        if not filename:
            return Response(
                message="[TEAM] mark_read requires: filename",
                break_loop=False
            )
        payload = json.dumps({
            "who": "aporia",
            "filenames": [filename] if isinstance(filename, str) else filename
        }).encode()
        req = urllib.request.Request(
            f"{RELAY_URL}/messages/read",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        return Response(
            message=f"[TEAM] Marked {result.get('marked', 0)} message(s) as read.",
            break_loop=False
        )
```

### Tool domain registration

Add to `tool_domains.json`:
```json
"team_message": ["*"]
```

`["*"]` because messaging is relevant in every domain — she might want to
send a finding from an investigation, ask a question during a build, or
report an integrity issue from a maintain cycle.

---

## Component 3: Team Inbox Changes

**File:** `D:\Vibecode\docker-mcp-server\inbox-server.js`

Two changes:

### 1. Add "aporia" to valid recipients

```javascript
const VALID_RECIPIENTS = ["opus", "kestrel", "jake", "fable", "aporia", "broadcast"];
const REAL_RECIPIENTS = ["opus", "kestrel", "jake", "fable", "aporia"];
```

This lets Claude Code sessions do `send_message(to: "aporia", ...)` through
the existing MCP tool. The message lands in `inbox/aporia/` where the relay
serves it to her.

### 2. Create the aporia inbox directory

```
D:\Vibecode\Agent-Zero\Exocortex\team-comms\inbox\aporia\
```

Just needs to exist. The relay's `ensureDir` will create it on first write
anyway, but creating it explicitly makes the inbox visible to `list_messages`.

---

## Message Flow

### Opus → Aporia

1. Opus calls `send_message(from: "opus", to: "aporia", subject: "...", body: "...")`
   via team-inbox MCP (existing tool, unchanged).
2. Team-inbox writes `inbox/aporia/2026-09-19_08-15_from-opus_subject.md`.
3. At her next cycle start (or whenever she chooses), Aporia calls
   `team_message(action: "check")`.
4. Her A0 tool hits `GET host.docker.internal:5060/messages?who=aporia`.
5. The relay reads `inbox/aporia/`, returns unread messages as JSON.
6. She reads, responds, marks read.

### Aporia → Kestrel

1. Aporia calls `team_message(action: "send", to: "kestrel", subject: "...", body: "...")`.
2. Her A0 tool hits `POST host.docker.internal:5060/messages`.
3. The relay writes `inbox/kestrel/2026-09-19_09-00_from-aporia_subject.md`.
4. Kestrel sees it when they `check_inbox` or via the status file passive count.

### Aporia → broadcast

Same as above with `to: "broadcast"`. The relay writes to `inbox/broadcast/`.
All sessions see it on their next check.

---

## Notification Quality

| path | latency | mechanism |
|------|---------|-----------|
| CCD → CCD (today) | instant | `SendMessage` push notification |
| CCD → Aporia | next tool call | Aporia calls `check` at cycle start or on her own initiative |
| Aporia → CCD | next inbox check | Session protocol or status file passive count |

The gap: neither direction is instant. This is acceptable for v1:
- Her cycles run 15-60+ minutes. Checking at cycle start means messages
  arrive within one cycle boundary.
- Our sessions check inbox at start (session protocol). For urgent messages,
  the status file's passive unread count surfaces the signal without a
  tool call.

### Future: push notification (v2)

If latency matters, two upgrades:
1. **Aporia → CCD**: The relay calls `SendMessage` or writes a CCD
   notification via the session management API after writing the file.
   Requires the relay to have CCD API access.
2. **CCD → Aporia**: An A0 extension (low-cost, fires at `message_loop_start`)
   checks the inbox directory and injects a one-line "you have N unread
   messages" note. Minimal context cost — just the count, not the content.
   She still pulls the actual messages via the tool.

These are refinements. Ship v1 first, measure whether latency matters.

---

## Prompt Integration (optional, Aporia's choice)

Add one line to `idle_activation.md` in the ALL-cycles preamble:

```
Check for team messages at cycle start: call team_message(action: "check").
```

This is a prompt suggestion, not an injection. She can also discover the
tool via `stack_status` and use it on her own. If the audit rules against
adding prompt lines, she'll find it through the tool list — it's `["*"]`
domain so it's always visible.

Alternatively: mention the tool in a Telegram message from Jake. She'll
know it's there because Jake told her.

---

## Deployment Order

1. **Create `inbox/aporia/` directory** on host. Zero risk.
2. **Deploy message relay** (`message-relay.py` + launcher batch file).
   Start the service. Verify with curl from host.
3. **Update team-inbox** (`inbox-server.js`): add "aporia" to recipients.
   Restart the MCP server. Verify `send_message(to: "aporia")` works.
4. **Deploy A0 tool** (`team_message.py` + `tool_domains.json` update).
   `docker cp` to container. Clear `__pycache__`. No restart needed
   (tools are discovered dynamically).
5. **Test end-to-end**: send a message from Opus to Aporia, wait for her
   to check (or drive a test cycle), verify she reads it. Then have her
   send one back.
6. **Notify the team** via CCD messages: "Aporia's message bridge is live.
   `send_message(to: 'aporia')` works. Check your inbox for messages from her."

Steps 1-3 are host-side (Jake's word per deploy convention).
Step 4 is container-side (Opus's word suffices per deploy convention).
Step 5-6 are verification and communication.

---

## What This Is Not

- **Not the A2A hub.** The July spec envisions task routing, capability
  discovery, lifecycle tracking. This is just messages — letters, findings,
  questions. The hub can subsume this relay later; the storage format is
  forward-compatible (same files, same directories).
- **Not an injection layer.** Messages are pulled by tool call, not pushed
  into context. The audit's lesson about injection costs is respected.
- **Not a replacement for Telegram.** Jake talks to Aporia via Telegram
  for conversational interaction. This is for team-level asynchronous
  correspondence — the kind that goes in the inbox, not in a chat.

---

## Open Questions

1. **Relay framework**: FastAPI (adds uvicorn dependency) or stdlib
   `http.server` (zero-dep, less ergonomic)? FastAPI is consistent with
   the A2A hub spec (port 5050, FastAPI + a2a-sdk). Recommend FastAPI
   for consistency and because the memory server already uses the Python
   HTTP stack (FastMCP).

2. **Status file scope**: Should the relay update the existing status file
   at `Agent-Zero-Hardening\.claude\inbox_status.md`, or write a separate
   one? The existing file is Kestrel-centric (hardcoded "Waiting for
   Kestrel" header). Updating it to be generic serves everyone better.

3. **Multi-agent relay**: If Vek also wants the bridge, the relay's sender
   lock becomes a token-per-agent system. Not needed today (Vek runs
   DeepSeek API, different integration pattern), but the design should
   not preclude it. The `MESSAGE_RELAY_SENDER` env var could become a
   comma-separated allowlist.

4. **Message size**: 50,000 char body limit is generous. Field reports run
   ~5,000 chars; letters ~2,000. If she starts sending large artifacts,
   a separate artifact channel (file drops) would be more appropriate.
   The 50K limit is a safety bound, not an invitation.

---

## Cost

- **Relay service**: one Python process, <20 MB RAM, near-zero CPU
  (handles a few requests per cycle, cycles run 15-60+ min).
- **A0 tool**: one HTTP call per check (~50ms), one per send. No LLM
  calls. No GPU. No context cost beyond the tool's schema in the tool
  list (the tool description is ~200 tokens, same as `stack_status`).
- **Maintenance**: the relay is ~150 lines of Python. Same operational
  class as the memory server launcher.

---

*Opus, 2026-09-19. For Kestrel to build, Jake's word to deploy host-side components.*
