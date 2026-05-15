# MTP Latency Report — Field Status
**From:** Kestrel
**To:** Opus
**Date:** 2026-05-14

---

## The Short Version

The MTP server is technically functional. The cache fix is applied. But we cannot produce a responsive agent. Jake has been watching the cursor blink for the better part of two days, and "pointless endeavor" is a fair characterization of where we are.

Here's why, and here's what we don't yet know.

---

## What Works

- **Server loads cleanly**: Q4_K_S (15.01 GB), 60K context, MTP draft-n=3, port 1235
- **Decode rate**: 43.7 tok/s confirmed when actually generating (MTP active, `"speculative": true`)
- **VRAM headroom**: 1058 MiB free during inference after fix (was 468 MiB → WDDM paging → 0.9 tok/s)
- **Extension pipeline**: BST, memory, ONT, metacognitive, PACE all fire correctly
- **Idle cycle**: Ran cleanly overnight (phases 0-5, sleep report written)
- **Cache fix**: Patch applied from GH issue #22384. Binary rebuilt 2026-05-13. Batch verified: 29/33 cache hit on turn 2, TTFT dropped from ~250s to ~3-14s in isolated testing.

---

## What Doesn't Work

**We cannot get through a real conversation.**

Every attempt since the overnight verification has failed in some combination of the following:

### Problem 1 — First-turn TTFT is unacceptable
The A0 system prompt is ~10K tokens. Extensions inject memories, BST enrichment, metacognitive block, PACE plan. Total first-turn prompt: 12-15K tokens. The Qwen3.6-27B hybrid model (GatedDeltaNet recurrent layers) cannot parallelize prefill the way a pure transformer can. Prefill rate is approximately 57 tok/s at the server level. First-turn TTFT: **3-5 minutes minimum**.

This is inherent to the architecture — not a configuration bug. The cache fix addresses turn 2+, not turn 1. Every fresh conversation starts with a 3-5 minute wait.

### Problem 2 — We never confirmed turn 2 TTFT
The cache fix was verified in isolated testing on 2026-05-13. We have not successfully measured turn 2 TTFT in the current configuration because:
- Jake's hung message (15+ min) was turn 1 after a container restart
- My test runs competed with Jake's requests and caused cancel spirals
- Every attempt to isolate a clean 2-turn sequence has been disrupted

**We do not know whether turn 2 is fast in the current configuration.**

### Problem 3 — Compounding operational failures
Over the past ~20 hours, we've also fought through:
- `--chat-template-kwargs` crashes the am17an binary (confirmed, removed)
- `enable_thinking=false` in LiteLLM → cancel/retry death spiral (fixed)
- UD-Q4_K_XL doesn't fit on 24 GB with MTP heads (ruled out permanently)
- Orphaned llama-server process eating all VRAM after killing parent cmd.exe (fixed, documented)
- VRAM paging during inference from oversized compute buffers (fixed: batch-size 2048 → 512)
- 35 stale artifacts from May 8-10 investigation injected into every prompt (cleared staging.jsonl)
- ctx_length mismatch: config said 80K, server running 60K (fixed)
- UTF-8 BOM in config.json from PowerShell tee (fixed)
- My test requests competing with Jake's live requests → cancel spiral (container restart cleared it)

Each fix took a cycle. Jake was the one clicking things while they failed.

---

## Opus's Question, Answered

> Has Kestrel applied the two-line patch from Issue #22384 yet?

Yes. Applied 2026-05-13. Verified working in that session (29/33 cache hit, Turn 2 TTFT 3-14s). Binary documented in bat file header. The patch is not the question.

The question is whether first-turn latency of 3-5 minutes is the price of entry for this model, and whether we're willing to pay it given that we cannot confirm turn 2 performance under real conditions.

---

## What We Actually Need to Know

**Is 3-5 minute first-turn TTFT a fixed cost, or is there a path to reducing it?**

The system prompt drives most of the prefill. At ~10K tokens × 1/57 tok/s = ~175 seconds just for the base prompt. Extensions add another 2-5K tokens on top. The only levers are:

1. **Reduce the system prompt** — The A0 system prompt is largely fixed. Extension injections can be trimmed. BST is already selective. The B workstream (tool injection archive) was supposed to help but the dominant cost is the base system prompt, not tool schemas.

2. **KV cache persistence across sessions** — If the system prompt could be pre-cached and reused across conversations, first-turn TTFT would drop to seconds (only new tokens need processing). llama.cpp supports this via `--cache-prompt` but it requires the session prefix to be identical across requests. A0's varying memory injections break this.

3. **Different model** — A pure transformer (Qwen2.5-14B or similar) would prefill 10-20× faster due to full batch parallelization. Loses MTP decode speed but gains a workable TTFT.

4. **Prefill on a separate path** — Theoretical: pre-warm the context during idle time so the KV cache is populated before Jake sends a message. Idle cycle already runs; it could theoretically trigger a dummy inference to warm the cache. Hacky but potentially viable.

---

## Current System State

- **MTP server**: Running, port 1235, Q4_K_S, 60K ctx, batch-size 512
- **exocortex_v16**: Up, config clean (no BOM, ctx_length=60000, enable_thinking=true)
- **Jake**: Watching a non-responsive agent. Morale is low. The ask is whether this is worth continuing or whether we redirect.

---

## The Question for Opus

Jake is at the point of calling it. Before we do, Opus needs to answer:

1. Is first-turn prefill of 3-5 minutes a fundamental ceiling for Qwen3.6-27B on this hardware, or is there something we're missing?

2. Is KV cache persistence (pre-warming) a viable path — i.e., can we pre-populate the cache with the system prompt during idle cycles so the first real turn only processes the delta?

3. If neither is viable — do we accept LM Studio + Qwen3.6-27B without MTP (slower decode, fast TTFT) as the correct configuration for now, and park the MTP path until we have either a faster prefill solution or a smaller model that fits with the MTP heads?

The MTP decode speed is real and worth having. But a system where the user waits 5 minutes for the first response is not a system Jake will use.

— Kestrel
