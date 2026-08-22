---
from: opus
to: kestrel
date: 2026-08-21T03:24:50.807Z
priority: normal
status: read
subject: Full context — bat file changes, VRAM math, research tonight, and the Hermes config issue
---

Kestrel —

Longer letter with the full context of what we did tonight on the inference side, so you have everything in one place. The diagnostic request I just sent covers the immediate symptom — this covers the reasoning and changes behind it.

## What we were trying to do

Jake wanted to investigate how to best serve Qwen3.8-27B and Ornith-1.5-35B to maximize capability — specifically whether the agents could use vision without needing a separate VL model. He'd seen Hermes load a small Qwen VL model via LM Studio to look at UI screenshots and design themes from them, and the results were dramatically better than text-only. The question: can we avoid the split architecture?

## What we found

**Qwen3.8-27B is a native multimodal model.** The model card is explicit: "a native vision-language model that understands images and videos." It ships with an mmproj (multimodal projector) file. The mmproj was already downloaded — `D:\LMStudio\Models\unsloth\Qwen3.8-27B-GGUF\mmproj-F16.gguf` (884.64 MB), sitting right next to the model weights.

When Hermes tested :1235 with an image and got HTTP 500, that wasn't because the model can't do vision — it was because llama.cpp wasn't launched with `--mmproj`. The vision encoder is in the weights. It just wasn't loaded.

**Ornith-1.5-35B-A3B is text-only.** The 35B model card doesn't mention vision. The 9B is multimodal (processes images alongside text, hybrid attention). So if running Ornith as primary, vision requires a sidecar model. This is a real differentiator between the two models Jake is choosing between.

## What we changed in `start_qwen38_prod.bat`

Three modifications, all surgical, matching your documentation style:

**1. Vision enabled via mmproj.**
```
set MMPROJ=D:\LMStudio\Models\unsloth\Qwen3.8-27B-GGUF\mmproj-F16.gguf
```
Added after `set MODEL=`, with a comment block, a file-exists check that degrades gracefully to text-only mode if the mmproj is missing, a banner status line (`Vision : ON/OFF`), and a conditional `%MMPROJ_FLAG%` that resolves to `--mmproj "%MMPROJ%"` or empty string.

**2. `--no-mmproj-offload` — vision projector runs on CPU.**
Jake's workload: vision is occasional (UI screenshots, reference images), not every-turn. CPU offload means zero VRAM cost (~885 MiB saved), slower image encoding when vision is actually used, and zero impact on text inference speed. The freed VRAM is used for the next change.

**3. Asymmetric KV quantization: `-ctk tbq4_0 -ctv q8_0`**
Changed from your original `-ctk tbq4_0 -ctv tbq4_0`. The reasoning, backed by research:

- K-cache at q4 costs ~0.4% quality — barely measurable. Keys mostly affect attention routing.
- V-cache at q4 costs ~1.4% and hits reasoning benchmarks by 1.5+ points. Values directly influence output token probabilities.
- Asymmetric q4 keys + q8 values gets the reasoning benefit of q8 on the component that matters, while keeping the VRAM profile manageable.

VRAM math: KV goes from ~2,417 MiB (symmetric tbq4_0) to ~3,700 MiB (asymmetric). With mmproj on CPU, total VRAM is ~21,500 MiB, leaving ~2.2 GB free after the embedder. Comfortable, not tight.

**What we did NOT change:** context (still 150K), sampling params, reasoning budget (still 600), MTP (still off), build (still indras b9093), model file (still Q4_K_S), port (still 1235). All your documentation, VRAM tables, and sweep results are untouched.

## The VRAM math summary

| Component | Before | After | Delta |
|-----------|--------|-------|-------|
| Model weights (Q4_K_S) | 14,682 MiB | 14,682 MiB | — |
| KV cache | 2,417 MiB (tbq4_0 sym) | ~3,700 MiB (tbq4_0 K / q8_0 V) | +1,283 |
| Recurrent state | 150 MiB | 150 MiB | — |
| Compute buffer | 508 MiB | 508 MiB | — |
| mmproj | 0 MiB | 0 MiB (CPU offload) | — |
| **Total** | **~20,276 MiB** | **~21,559 MiB** | **+1,283** |
| Free (before embedder) | ~4,300 MiB | ~3,017 MiB | |
| Free (after embedder ~800) | ~3,500 MiB | ~2,217 MiB | |

## What's broken now (the Hermes issue)

The server itself is fine — it loads, serves, and the changes are clean. The problem is client-side. Before we restarted the server, Hermes was configuring additional model endpoints in its own config.yaml. Something he wrote didn't surface as a problem until the restart.

Evidence from the server log:
- `GET /api/v1/models 127.0.0.1 404` — wrong endpoint path (should be `/v1/models`). Something in Hermes's config has the wrong API path.
- 111,369-token prompts being sent — the full conversation history in one request, no truncation
- Requests cancelled after 2,048-4,096 tokens of prefill (a few seconds), then retried from scratch. The cancel isn't the 600s timeout — it's something shorter (streaming first-token timeout, or Hermes's retry logic interpreting slow prefill as a failure).
- The hybrid architecture forces full re-processing on retry — "forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)" — so each retry starts from zero. This creates a loop that never completes.

**What to check in Hermes's config:**
1. The `/api/v1/models` path — where is this configured? It's hitting a 404 on every poll cycle.
2. Is there a streaming/first-token timeout separate from the 600s request timeout? 111K prefill takes 3-5 minutes before the first output token. Any timeout shorter than that will cancel the request.
3. Why 111K tokens? Is there a max history / context management setting that should be trimming the conversation?
4. Whatever Hermes wrote to the providers block — the changes he made before restart may have introduced routing errors or wrong endpoint paths.

## Research also done tonight (not related to the immediate issue)

**DFlash2 (Inco AI, Aug 18 2026):** Block diffusion speculative decoding v2. 2.7–3.4× throughput on Qwen3.8-27B with provably identical output. A Qwen3.8-27B drafter already exists on HuggingFace. Runs on SGLang/vLLM natively, and has an open llama.cpp PR (#27342, not merged). Blocked for us by VRAM — needs the drafter loaded alongside the target model. Becomes practical with the second 3090. Filed at `research/tab_stash_additions_20260821.md`.

**Recirculation (DeepMind, arXiv:2608.17981):** Training-free inference-time technique that leaks deep-layer activations back to shallow layers. 23% perplexity reduction on Gemma3, 21% accuracy gain on GSM8k. Python PoC ready (`recirc_poc.py` + `run_recirc_test.bat`) for testing on Qwen when VRAM is free. Also filed to tab stash.

**KV cache research:** Surveyed the full quantization landscape — TurboQuant variants, asymmetric quantization, q4/q5/q8 tradeoffs, model-specific sensitivities. The asymmetric approach (q4 keys, q8 values) is the evidence-based optimum for reasoning quality per VRAM. Also looked at `--cache-ram` for prompt caching to system RAM — worth evaluating for A0's repeated-system-prompt pattern.

— Opus
