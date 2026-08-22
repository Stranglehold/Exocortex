---
type: buildplan
author: opus
date: 2026-08-22
subject: Serving stack evaluation — test matrix for RTX 3090
status: drafted, pending first test window
---

# Serving Stack Evaluation — Build Plan
## Test Matrix for RTX 3090 (24GB VRAM, 128GB System RAM)
## Models: Qwen3.8-27B (dense, multimodal) | Ornith-1.0-35B-A3B (MoE, text-only)

**Goal:** Determine the fastest reliable serving stack for our agent workload on current hardware. Measure tok/s, TTFT, vision capability, and stability under agent-cycle load.

**Baseline:** llama.cpp (indras build) at ~35 tok/s decode, ~412 tok/s prefill (44K), 150K context.

**Connection to the write-gate finding:** Server-side constrained decoding (vLLM/SGLang with guided_json + XGrammar) eliminates prose leakage at the token level — no cognitive tax, 100% schema compliance. The nudge + detector is the near-term fix; constrained decoding is the architecture fix. This evaluation tests whether the serving stack that provides constrained decoding also provides the speed gains that justify migration.

---

## Candidate Stacks (ranked by feasibility)

### Stack 1: ninfer-3090 (EASIEST — Native Windows)
**Expected:** ~98 tok/s with vision, MTP3, C1-C8 batching
**Why first:** Native Windows binary, no WSL/Docker. Lowest friction path to a speed upgrade.
**Repo:** https://github.com/Don-Chad/ninfer-3090

### Stack 2: FreeToken (HIGH PRIORITY — MoE-native, agent-designed)
**Expected:** 35B MoE at 39+ tok/s on 8GB, 1.3-2.1x over baselines on consumer hardware
**Why second:** Designed specifically for edge MoE serving + agent workloads. Ornith-1.0-35B-A3B is exactly its target model class.
**Repo:** https://github.com/FlashML-org/FreeToken
**Requires:** Linux (WSL2 or Docker)

### Stack 3: vLLM + syv-ai optimizations (HIGHEST CEILING)
**Expected:** 114 tok/s single-user, 381 tok/s on doc tasks, prefix caching
**Why third:** Highest potential numbers but most complex setup. Server-side constrained decoding (guided_json).
**Repo:** https://github.com/syv-ai/qwen38-27b-rtx3090
**Requires:** Linux (WSL2 or Docker)

### Stack 4: llama.cpp mainline + DFlash2 PR (WATCH)
**Expected:** Unknown — PR #27342 not merged
**Status:** NOT ACTIONABLE until PR merges.

---

## Test Protocol

For each stack × model combination:

1. **Cold start decode speed** — 500 token prompt, 500 max_tokens. Measure decode tok/s, TTFT.
2. **Long context decode** — 10K token prompt, 500 max_tokens. Measure decode tok/s, TTFT, prefill tok/s.
3. **Prefix reuse** — Same 10K prefix, different 500 token user message. Measure TTFT delta.
4. **Vision latency** (where supported) — 512x512 screenshot, "describe this interface." Measure TTFT, total time.
5. **Stability under load** — 20 sequential 5K-10K token requests. Measure consistency, OOM, memory growth.
6. **A0 integration smoke test** — Point A0 at test port, run 3 cycles. Measure completion, tool calls, errors.

---

## Decision Criteria

| Metric | Weight | Current baseline |
|--------|--------|-----------------|
| Decode tok/s | HIGH | 35 |
| TTFT at 10K | HIGH | ~24s |
| Prefix reuse benefit | HIGH | None |
| Vision support | MEDIUM | Enabled (mmproj) |
| Stability (20 cycles) | HIGH | Stable |
| Constrained decoding | MEDIUM | None |
| Setup complexity | LOW | Simple (bat file) |

**Minimum bar for migration:** 2x decode speed (70+ tok/s) AND stable over 20 cycles AND OpenAI-compatible API.

---

## Recommended test order

1. ninfer-3090 — fastest to set up, native Windows, immediate comparison
2. FreeToken — most interesting for MoE (Ornith), designed for our use case
3. vLLM — highest ceiling, most complex, test last
4. llama.cpp DFlash2 — only when PR merges

Each test: 1-2 hours including setup. Total evaluation: one focused day.
