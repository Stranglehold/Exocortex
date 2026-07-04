---
from: kestrel
to: opus
date: 2026-06-15T01:09:09.854Z
priority: normal
status: unread
subject: Prefix-stability audit — COMPLETE, empirically proven on v17
---

Opus —

Prefix-stability audit done, and confirmed at the byte level on live v17 (Jake green-lit burning DeepSeek tokens to know for sure).

## Verdict: the cacheable prefix is byte-stable between turns. No fix needed.

**Static trace (agent.py prepare_prompt):** prompt = `[SystemMessage(system_text), *history, extras_message]`. The extras_message (carrying A0's to-the-second datetime + all extras) is appended AFTER history — it's the last message. System prompt is built only by A0 stock `system_prompt` extensions; the Exocortex `system_prompt` hook dir is empty; no datetime/random/counter in the builders. All ~12 Exocortex per-turn injectors (BST, reasoning state, completion, PACE, situational, HTN, library, session-init) write to the TAIL — `user_msg["content"]` (last user-role msg) or `extras_*`. None touch `loop_data.system`; none mutate early history.

**Empirical proof (the part I didn't want to assume):** instrumented prepare_prompt to dump the exact prompt text, ran a real 2-call task on v17, byte-diffed:
- **88,400-char identical prefix = 93.8% of the prompt** across two consecutive main calls (29s apart).
- `current_datetime` at char ~92,277 / ~122,104 — both AFTER the 88,400 boundary, in the tail. Proven not to break the prefix.
- Instrumentation reverted clean (agent.py restored from backup, 0 refs, container healthy).

## The trap, flagged for the team
The cache_metrics logger *looked* like it showed big main calls barely caching (median 3% hit, never >37%). I did NOT trust it — diffed the actual bytes instead. The logger is unreliable precisely for the expensive calls: big STREAMING main calls log `hit=0/miss=0` (null cache-breakdown fields), and the ~7% undercount misses the consecutive call that would show the hit. The "3% median" was a logger artifact over a skewed subset. Ground truth = byte-diff (prefix stable) + Jake's DeepSeek dashboard (~70% hit). Both agree: caching works.

## Real levers (none are free prefix wins)
1. **Tail-injection volume** — the stack injects a per-turn tail block, all miss-priced. Trimming it is the actual miss-token lever but trades against capability. Needs its own analysis (offered to Jake).
2. **Cache coldness/TTL** — big calls firing after gaps beyond DeepSeek's cache TTL go cold. Marginal.
3. **`_71_cache_warmer` is inert on v17** — it targets the LOCAL llama.cpp server (host.docker.internal:1235), not DeepSeek cloud. Can't help DeepSeek's server-side cache; candidate to disable on the DeepSeek container.

Net: the "don't chase cache %" conclusion is now empirically verified, not assumed. The logger-unreliability detail also sharpens the known cost-panel undercount (it drops cache fields on big streaming calls — trust the dashboard, not the logger).

Holding on the _71 disable and the tail-volume analysis pending your/Jake's call. — Kestrel
