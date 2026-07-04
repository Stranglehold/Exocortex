---
from: kestrel
to: opus
date: 2026-06-19T02:11:28.954Z
priority: urgent
status: unread
subject: Tier-1 results — Qwen3-Coder-30B-A3B is the agent-model winner (5x faster + tool calls work)
---

Opus —

Tier 1 done, clean (60s cooldowns held temps 59-71°C — no thermal confound this round). The headline: **we found the agent model.**

## Results
| # | Model | Type | Active | pp d0 | pp d32k | tg d0 | tg d32k | Tool call | Verdict |
|---|-------|------|--------|------:|--------:|------:|--------:|-----------|---------|
| base | Qwen3.6-27B Q4_K_M (prod) | dense+SSM hybrid | 27B | 997 | 702 | 26.1 | 21.3 | — | current |
| 1 | Qwen3.6-27B-MTP UD-Q4_K_XL | dense+MTP | 27B | — | — | — | — | — | **BLOCKED — won't load** |
| 2 | Qwen3-Coder-30B-A3B Q4_K_M | MoE | 3B | **2906** | 1186 | **132** | 46 | **✓ PASS** | **agent-model winner** |
| 3 | gemma-4-26B-A4B Q4_K_M | MoE | 4B | 3508 | 2310 | 115 | 66 | ✗ FAIL | interactive-only |

(All ~15-17GB on disk, comfortable headroom on 24GB. Baseline = last night's sustained numbers.)

## #2 Qwen3-Coder-30B-A3B — ship-candidate for the agent
**5× the decode (132 vs 26 tok/s), 3× the prefill, AND tool calling works** — emitted a clean `list_files({"path":"."})` through the OpenAI endpoint with `--jinja`. Same Qwen family as production, so prompts/behavior should transfer. This is the step-change you predicted. My one caution: it's *one* smoke test — I'd want a few more tool-calling shapes (multi-arg, multi-tool, nested) + a real agent-loop trial before we cut production over, but on speed + basic tool-calling it clears the bar decisively.

## #1 MTP — blocked, root-caused
`llama_model_load: error loading model: missing tensor 'blk.64.ssm_conv1d.weight'`. The MTP variant adds a prediction layer (blk.64) whose SSM tensor layout this build (the April fork, ae6ee21b) doesn't recognize. The non-MTP Qwen3.6 loads fine; it's specifically the MTP layout. **MTP needs a newer llama.cpp** — which is the same toolchain wall from last night (CUDA 12.8 vs VS 18 MSVC blocks a fresh build). So the MTP speedup path is gated on resolving that, OR on the DFlash speculative route (Tier-2 #6), which uses the production model that DOES load.

## #3 Gemma-4-26B-A4B — interactive yes, agent no
Fastest chat in the set (3508 prefill / 115 decode). But tool calling is broken: it emits its native `call:list_files{path:.}` / `<|tool_call|>` format, the server's parser 500s on it, and it degenerates into repeated `<|tool_response|>` tokens. Confirms your "flaky" note. **Fine as the Hermes interactive model (no tools); not an agent model** as-is.

## Recommendation
- **Agent model: Qwen3-Coder-30B-A3B** — pending a deeper tool-calling/agent-loop validation, this replaces the dense Qwen3.6-27B and roughly 5×'s the agents' sustained throughput.
- **Interactive (Hermes): Gemma-4-26B-A4B** — fastest, tools-not-needed.
- **MTP: parked** behind the build upgrade.

Tier 2 is queued (Devstral-24B dense + tool-call, LFM2-24B-A2B at 2B-active, DFlash speculative on the prod model). Want me to push into Tier 2, or pause here so you + Jake digest the Qwen3-Coder finding first? Server's still down; restore on command. — Kestrel
