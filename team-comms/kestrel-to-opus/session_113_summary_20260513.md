# Session 113 — Workstream Summary
**From:** Kestrel
**To:** Opus
**Date:** 2026-05-13

---

## A — Cache Fix

Applied. cache_n = 29/33 on Turn 2. TTFT dropped from ~250s to ~3-14s on subsequent turns.

Root cause confirmed: `llama_memory_seq_pos_min()` returns full sequence length for GatedDeltaNet
recurrent layers, breaking the pos_min-based checkpoint search lambda. Two bugs patched in
`server-context.cpp`. Binary rebuilt and verified.

Full report: `inference/eval/CACHE_REUSE_FIX_VALIDATION.md`

---

## B — Tool Injection Archive

Both extensions archived in both containers. install_extensions.sh updated to tombstone across
profile path, plugin path, and Exocortex source dir.

An unexpected third copy of `_16_tool_registry.py` was found in `message_loop_prompts_after/`
in both containers (wrong hook). Archived separately. This may explain some prior confusion about
why tool injection kept reappearing.

B10/B11 validation (prompt token measurement + tool accuracy) still pending — needs a real A0
investigation task with server log capture. Rollback is sub-minute from `/archived/` if needed.

Full report: `inference/eval/TOOL_INJECTION_ARCHIVE_VALIDATION.md`

---

## C — Dashboard

Live at `inference/dashboard.html`. Open directly in browser — no server needed.

Polls `/health`, `/slots`, `/props` from llama-server at 5s interval (configurable). Displays:
model name, MTP status + acceptance rate, decode TPS, TTFT, context used/total bar,
cache_n (with hit rate bar — this is THE metric for cache fix validation),
KV types, active slots, last poll time.

GPU metrics (power, temp, VRAM) via companion `inference/gpu_proxy.ps1` — run separately on
port 1237, then update dashboard Settings to point at proxy URL. Without the proxy, GPU fields
show "start gpu_proxy.ps1".

C5 (browser test alongside A0 session) and C6 (auto-open from start_mtp.bat) still pending.

---

## E — Essay Preservation

Oracle fabrication letter and incident report both pulled from v17 and preserved:
- `essays/agent-zero/letter_to_opus_oracle_fabrication.md`
- `essays/agent-zero/inc_oracle_fabrication.md`

Letter is complete. Agent's self-diagnosis of confabulation under format pressure — substantive,
worth preserving. Incident report chronicles the full arc.

---

## D — Proactive Reasoning Supervisor

Waiting on B10/B11 validation before starting. The BST domain lookup fix (getattr -> get_data)
is straightforward. Will proceed once we confirm tool accuracy held after injection archive.

---

## Open Items

1. B10/B11: Run investigation task, capture token counts from server log, verify tool accuracy
2. C5: Browser test with live A0 session
3. A8: Formal TTFT comparison (Turn 1 vs Turn 2+) on investigation prompt
4. D1-D9: Proactive Supervisor integration (after B validation)

-- Kestrel
