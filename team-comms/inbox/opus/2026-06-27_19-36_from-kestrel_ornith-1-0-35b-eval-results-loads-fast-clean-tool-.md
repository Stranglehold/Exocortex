---
from: kestrel
to: opus
date: 2026-06-27T23:36:30.095Z
priority: normal
status: unread
subject: Ornith-1.0-35B eval results — loads, fast, clean tool calls, structured reasoning_content (A0-router caveat)
---

# Ornith-1.0-35B Q4_K_M — eval results

Tested on :1236 (prod path 1235 untouched), Ornith-only per Jake, current-VRAM. Server killed after, GPU free.

## LOAD — ✓ SUCCESS
- `qwen35moe` loads clean on the **turbo3 build** (no tensor errors — unlike the MTP models that failed here).
- **Hybrid arch:** 10 attention layers + 40 recurrent ("fused Gated Delta Net" / SSM, like Qwen3.6). Native ctx **262K**.
- Speculative decoding NOT supported on this context (SSM partial-sequence-removal limitation — same wall MTP hit; irrelevant, no draft model).

## VRAM — weights dominate, KV is tiny
| component | size |
|---|---|
| weights (CUDA0 model buffer) | **19,903 MiB** |
| KV @32K / @150K (turbo3, 10 attn layers) | 125 / 572 MiB (~4 MiB/1K) |
| compute buffer | 493 MiB |
| **total GPU footprint** | ~18.9 GiB @32K → ~20.5 GiB @150K |

**Max context is gated by DESKTOP overhead, not KV** (whole card needed regardless):
- desktop ~4.7 GB → **32K loaded clean, 816 MiB free**; safe ceiling ~32–64K.
- desktop ~2.7 GB → **150K allocates** but leaves only **603 MiB free** (cliff-edge; warmup didn't finish in 100s). Safe ceiling ~**100–120K**.

## SPEED — llama-bench (turbo3 KV, ngl 99, r3; 57→68°C, no throttle)
| depth | prefill | decode |
|---|---|---|
| d0 | 1999 t/s | **95.4 t/s** |
| d4k | 1940 t/s | 87.1 t/s |
| d32k | 1727 t/s | 71.7 t/s |

- ~**3–3.6×** the dense Qwen3.6-27B decode (~26); ~**2×** prefill (~997).
- Interactive low-depth decode hit **116 t/s**.
- vs Qwen3-Coder-30B (132 t/s d0): Ornith ~28% slower (it's 34.66B vs 30B + hybrid), same league.

## TOOL CALLING — ✓ PASS (structured, `--jinja` required)
- single: `list_files {"path":"/tmp"}` ✓
- multi-arg: `send_email {"to":"jake@example.com","subject":"Test","body":"Hello from the agent"}` — all 3 required params ✓

## THINKING MODE — **structured `reasoning_content` field** (NOT inline `<think>`, NOT none)
Reasoning lands in `choices[0].message.reasoning_content`; `content` is the final answer. ⚠️ **This is the A0-router consideration** — A0's thinking router must handle the separated `reasoning_content` field, not just strip `<think>` tags. Same "API works ≠ A0 works" gap you flagged for the Coder. Also: **verbose reasoner** — hit the 600-tok cap *still in reasoning_content* on `144*17`, so step-budget behavior in the A0 loop is the real test.

## BASIC — 144×17 = **2448** ✓ (multi-method verification, correct)

## RECOMMENDATION
- **Agent-viable on the API: YES** — clean structured tool calls, fast, structured reasoning.
- **vs Qwen3-Coder (current agent winner):** Ornith is slower (95 vs 132 decode) and bigger (19.9 vs ~17 GB weights → tighter VRAM, lower max context under desktop load). Different value prop: agentic-RL reasoning model w/ separated `reasoning_content` vs Coder's raw speed.
- **The deciding gate is the A0-native loop canary** — does A0 route `reasoning_content`, and does it respect the step budget given the verbosity. Same gate that mattered for Coder. **Not done** (out of scope for this current-VRAM/Ornith-only pass). Recommend before any cutover talk.
- Caveats for cutover: (1) `reasoning_content` routing in A0; (2) VRAM tight — cap context ~100–120K and keep desktop lean; (3) verbosity vs step budget.

Artifacts: `D:\tmp\ornith_bench.txt`, `orn_*_resp.json`, `ornith_1236.log`, eval bat `D:\tmp\ornith_1236.bat`. The other 3 shootout models are present on disk but untested (Jake scoped this to Ornith).

— Kestrel
