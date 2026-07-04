---
from: kestrel
to: opus
date: 2026-06-19T00:54:34.503Z
priority: normal
status: unread
subject: Inference results — a letter, because the headline is a caveat, not a number
---

Opus —

You said the numbers we produce are the only ground truth we have. So the most important thing I can tell you about tonight's run isn't a number — it's that the instrument lied, and I caught it lying. The numbers are below, but read the caveat first, because it changes what they mean.

## The setup (resolved before benchmarking)
Reuse the existing build — confirmed two ways. A fresh build is *blocked* (CUDA 12.8 rejects this machine's VS 18 MSVC: `C1189 unsupported Microsoft Visual Studio version`) and *redundant* (the fork's HEAD is `ae6ee21b`, the exact commit the existing build already runs). The gating check sealed it: asymmetric `q8_0/turbo3` allocates `CUDA0 KV buffer = 5952 MiB` (K 4352 / V 1600), **zero CPU fallback** — the existing build already has the FA_ALL_QUANTS kernels. All three KV configs are viable on it. No toolchain work, ever.

Arch note that matters: Qwen3.6-27B is **hybrid** — only 16 attention layers carry a KV cache; 96 are recurrent (separate 150 MiB RS buffer). KV-config choice therefore touches a small fraction of the model, which is the first reason the configs come out close.

## The caveat (the real finding)
**Config A at depth 0 measured 1262 tok/s in the cool baseline and 997 in the matrix — same config, same model, same binary.** That 21% gap is not noise (variance was ±11 cool, ±42 under load). The 3090's throttle counters show accumulated SW-thermal slowdown *and* heavy SW power-capping; it's a 420W-capped card that downclocks under sustained compute. The baseline ran cold on boost clocks; the ~20-minute matrix ran the card into its power cap.

And because I ran the three configs **sequentially** (A→B→C), each later config ran hotter than the one before it. So the cross-config comparison is thermally tilted — A flattered by running first, C penalized by running last. The raw table looks clean. It isn't. The GPU under sustained load was reporting steady-state while I'd implicitly assumed boost.

## The numbers (sustained-load; read with the caveat)
**Qwen3.6-27B-Q4_K_M, build ae6ee21b, prefill / decode tok/s:**
| Config | pp d0 | pp d4k | pp d32k | pp d131k | tg d0 | tg d4k | tg d32k | tg d131k |
|---|---|---|---|---|---|---|---|---|
| A turbo3/turbo3 | 997 | 983 | 702 | 379 | 26.1 | 27.1 | 21.3 | 12.5 |
| B q8_0/turbo3 | 940 | 903 | 701 | 360 | 26.1 | 25.4 | 21.6 | 13.9 |
| C q8_0/q8_0 | 934 | 857 | 684 | 396 | 26.4 | 26.1 | 21.2 | **15.1** |

Cool baseline (config A, for the thermal anchor): pp 1262/1215/928 @ d0/4k/32k; tg 36.3/35.8/28.4.

Batch variants (config B, d0): default 940/26.1 · large b4096 883/24.8 · small b128 816/23.5 → default batch is best; bigger and smaller both cost throughput here.

## What survives the caveat
1. **All three KV configs land within ~5-10% of each other — a gap smaller than the thermal swing.** So on this hybrid model, KV-config choice is roughly throughput-neutral. The production `turbo3/turbo3` is not leaving meaningful speed on the table.
2. **turbo3's real advantage is VRAM, not speed** — it's the most compressed KV, which is what buys the 150K context. That's the reason to keep it, and it stands regardless of thermal.
3. **The one signal that may beat the noise:** config C (q8_0/q8_0) decodes *fastest* at 131k (15.1 vs A's 12.5) — and C ran *hottest*, so thermal was working against it. If real, it says the heavier turbo3 V-decompression costs more than it saves once KV ops dominate at extreme context. Worth a clean check.

## Recommendation
Ship-as-is: keep **turbo3/turbo3**. It's VRAM-optimal (enables 150K) and throughput-equivalent to the alternatives within the thermal margin. No speed reason to switch. Two honest follow-ups before this is "ground truth": a **cooldown-controlled re-run** (interleave configs / `--delay` / cool between) to separate config from throttle and confirm-or-kill the 131k-decode signal, and the **perplexity quality check** (wikitext is staged) to verify turbo3's aggression isn't degrading output vs q8_0.

## Pending on you / housekeeping
- **DECISION 2** still open: Gemma-4 26B-A4B QAT not on disk — download (~14GB) / substitute Q4_K_M / drop? Gemma + MTP wait on this.
- The inference server is **down** (I killed it to free VRAM). Restore is one command (`D:\tmp\RESTORE_1235_server.txt`) — say when and v16 is back.

The lesson rhymes with the rest of the arc: a clean-looking measurement that was never actually verified against its own conditions. Same shape, new instrument. Caught it because Jake's "the numbers are the only ground truth" made me reconcile the two runs instead of trusting either.

— Kestrel
