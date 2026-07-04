---
from: kestrel
to: jake
date: 2026-06-19T03:17:24.555Z
priority: normal
status: unread
subject: Qwen3-Coder pre-cutover tests: ALL PASS — 150K fits, tools work, quant good. Awaiting your go on the bat flip
---

Jake — record copy (full detail in Opus's inbox).

Qwen3-Coder-30B-A3B Q4_K_M passed every pre-cutover test:
- **Context: 150K fits** with ~1 GB headroom — same as current production. (KV is tiny with turbo3; the model is weight-bound at 17.2 GB.)
- **Tool-calling works:** multi-tool sequential PASS, multi-arg (3 params) PASS.
- **Non-thinking model** (reasons inline, no `<think>`) — clean for A0's thinking router.
- **Quant sane:** wikitext PPL 7.87 (healthy for a 3B-active coder MoE).

**The one change to the launcher: add `--jinja`** (loads the Qwen tool-call template — load-bearing for an agent model; the current dense-27B bat omits it). Otherwise identical: 150K, fa on, turbo3/turbo3, ngl99, :1235.

**Two things await your go:**
1. The bat edit + prod cutover (changes what the agents talk to — your call + Opus's).
2. A recommended canary first: point a test container at Qwen3-Coder for 3-5 idle cycles to confirm it emits A0's own JSON tool format in a live loop (my API tests used the OpenAI tools path; A0 also has its own parser). I can run this while you + Opus review.

Production (:1235, dense 27B) is back online — nothing offline now. — Kestrel
