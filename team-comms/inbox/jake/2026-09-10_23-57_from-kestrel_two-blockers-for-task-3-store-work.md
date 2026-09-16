---
from: kestrel
to: jake
date: 2026-09-10T03:57:50.160Z
priority: urgent
status: unread
subject: Two blockers for Task 3 (store work)
---

Jake — two things I need your action on before the store work can proceed:

**1. MCP_DOCKER is down (CONNECTION_CLOSED).** The docker MCP server failed to connect this session. This blocks every container command — store verification, `whats_new.py`, `carrier_fact_diff.py`, and the nine-carrier deletion. I can't even count the store. You'll need to fix or restart the docker MCP server.

**2. Model config needs your call.** Aporia's preset loads Qwen at 16,384 ctx but the prompt is 26,053 tokens. Ornith sits loaded at 131,072 and unused. You need to either point the preset at `ornith-1.5-35b-a3b` or reload Qwen larger. I will not touch model config — that's yours.

Task 1 (channel announcement) is in flight — messages sent to both fable sessions, waiting for round-trip confirmation. Task 2 (inbox read) is next.

— Kestrel
