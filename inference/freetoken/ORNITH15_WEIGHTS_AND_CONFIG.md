---
type: reference
author: kestrel
date: 2026-08-22
subject: Ornith-1.5-35B-A3B — available weights, vendor configs, and what applies to our hardware
---

# Ornith 1.5-35B-A3B — Weights and Example Configs

Everything here was pulled from the HF repos and the vendor model card on 2026-08-22.
Sizes are from the repos' reported parameter counts, not estimates.

## 1. Weights

| repo | format | params | ~on disk | usable by |
|---|---|---|---|---|
| [`ornith-ai/Ornith-1.5-35B-A3B-NVFP4`](https://hf.co/ornith-ai/Ornith-1.5-35B-A3B-NVFP4) | safetensors, NVFP4 (modelopt) | 18,684 M | **~19 GB** | FreeToken, vLLM |
| [`ornith-ai/Ornith-1.5-35B-A3B-FP8`](https://hf.co/ornith-ai/Ornith-1.5-35B-A3B-FP8) | safetensors, compressed-tensors | 35,952 M | ~36 GB | FreeToken, vLLM |
| [`ornith-ai/Ornith-1.5-35B-A3B`](https://hf.co/ornith-ai/Ornith-1.5-35B-A3B) | safetensors, BF16 | 35,952 M | ~72 GB | FreeToken, vLLM, SGLang |
| [`ornith-ai/Ornith-1.5-35B-A3B-GGUF`](https://hf.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF) | GGUF | — | 20.2 GB | **llama.cpp only** |

**Already on disk:** the GGUF, at
`D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\Ornith-1.5-35B-Q4_K_M.gguf`
(20.2 GB, plus `mmproj-Ornith-1.5-35B-BF16.gguf` for vision). That is what
`inference/start_ornith15_prod.bat` uses. **FreeToken cannot read it** — it takes
safetensors / HF repo id / its own FTW format, never GGUF.

**No manual download needed for FreeToken:** `ft serve --model <hf-repo-id>` resolves an HF
repo id directly and fetches on first run. Pre-downloading only avoids a first-launch wait.

### Which one for this box

WSL RAM is the binding constraint, not VRAM — FreeToken's `offload` backend keeps experts
in **host** RAM, and WSL2 reports **62 GB total / 55 available** here (it defaults to about
half of host RAM; the buildplan's 128 GB is the Windows figure).

- **NVFP4 (~19 GB)** — default in the launcher. Smallest, and explicitly on FreeToken's
  supported-format list. **Caveat: NVFP4 is Blackwell-native and this is Ampere (sm_86).**
  FreeToken documents RTX 30/40/50 support for the engine but publishes nothing per-format,
  so native / emulated / unsupported on sm_86 is untested. This is the first thing to find out.
- **FP8 (~36 GB)** — the fallback, one line to switch. Fits comfortably.
- **BF16 (~72 GB)** — **does not fit** without raising the WSL limit in `.wslconfig`.

## 2. Vendor's own serving configs

Quoted from the model card. Note the vendor targets **2× 80 GB GPUs** at 256K context — we
have one 24 GB card, which is the entire reason quantization + expert offload matters here.
Do not copy `--tensor-parallel-size 2` / `--tp 2`; we have one GPU.

**vLLM (>= 0.19.1)** — relevant when Stack 3 of the serving-stack buildplan is tested:

```bash
vllm serve ornith-ai/Ornith-1.5-35B-A3B \
  --tensor-parallel-size 2 --max-model-len 262144 \
  --enable-prefix-caching --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml --reasoning-parser qwen3
```

**SGLang (>= 0.5.9):**

```bash
python -m sglang.launch_server \
  --model-path ornith-ai/Ornith-1.5-35B-A3B --tp 2 \
  --context-length 262144 --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3
```

**FreeToken** — no Qwen3-A3B example is published. Its quickstart states that "dtype,
attention and MoE backends, cache sizes, tool-call and reasoning parsers — resolve from the
checkpoint and the GPU", so the parsers the vLLM/SGLang commands set explicitly are
auto-detected. Our launcher is `inference/start_ornith15_freetoken.bat` →
`inference/freetoken/start_ornith15_freetoken.sh`.

## 3. Sampling — belongs in A0's preset, NOT the launcher

The vendor recommends:

| setting | value |
|---|---|
| temperature | **0.6** (general) · **1.0** to reproduce reported benchmarks |
| top_p | **0.95** |
| top_k | **20** |

These are per-request parameters, which is why neither vendor command sets them. On our
stack they live in `presets.yaml` under the active preset's `chat.kwargs`.

**This is a live discrepancy worth knowing before any comparison run.** The current preset
sets `temperature: '0'`. Benchmarking Ornith 1.5 at temperature 0 against a vendor spec of
0.6 measures a different configuration than the one the published numbers describe. Jake's
call — model configuration is his domain — but any throughput/quality figure taken before
it is reconciled should say which temperature it used.

## 4. Reasoning and tool calling — check the A0 router

The model card: *"by default the assistant turn opens with a `<think> … </think>` block
before the final answer"*, reasoning separates into a distinct field via the reasoning
parser, and tool calls emit as standard OpenAI-style `tool_calls`.

Two consequences for us:

1. **Separated `reasoning_content`.** `inference/start_ornith_prod.bat` already carries the
   note for 1.0: *"Ornith emits separated reasoning_content — confirm A0's thinking
   router."* Still unconfirmed, and it applies to 1.5 identically.
2. **OpenAI-style `tool_calls` are a different channel from A0's JSON-in-content.** A0 asks
   the model to emit its tool call as JSON *inside message content* (`a0_api_mode:
   chat_completions`), which is what produced the prose-leak failure measured 2026-08-22
   (see `specs/WRITE_GATE_INVERSION_DESIGN_NOTE.md`). A server that emits native
   `tool_calls` sidesteps that channel entirely. Worth measuring, not assuming — it may
   make the prose-leak class disappear on this stack, which would be a stronger argument
   for migrating than throughput alone.

## 5. What the installed binary told us that the docs did not

FreeToken 0.1.2 is installed (`~/freetoken-env`). `ft serve --help` on the real binary
carries flags absent from the published docs, and two of them matter a great deal.

**`--nvfp4-backend {auto,marlin,flashinfer,triton}` — resolves the Ampere question.**
Help text: *"auto picks by GPU (marlin on sm80-99 + vLLM; flashinfer b12x on sm120+ &
CUDA>=13; else triton, the portable inline-dequant kernel)."* This card is **sm_86**, inside
sm80-99, so NVFP4 runs — via marlin, or triton if marlin's vLLM dependency is missing.
**NVFP4 on Ampere was the main risk and it is not a risk.**

**`--sampling-defaults {model,none}` — and a possible root cause for an open bug.**
Help text: *"fills temperature/top_k/top_p from the checkpoint's `generation_config.json`
(recommended for reasoning models to avoid greedy repetition loops)."*

Our A0 preset sets `temperature: '0'`. That is greedy decoding, on a reasoning model, which
is precisely the configuration that sentence warns about. Two open items in this repo may
be downstream of it:

- `KESTREL.md` seam #20, the unexplained *"Qwen mid-response token-repetition pattern"*,
  currently attributed to one of three hypotheses (`enable_thinking` not sent,
  context-length degradation, quantization).
- The supervisor firing `[PS-ANALYZE] SIGNAL repeated_sentence severity=1.00` during the
  code-shaped write ladder on 2026-08-22.

**Stated as a hypothesis, not a finding** — nothing here has been tested, and the
repetition was observed on qwen3.8-27b rather than Ornith. But "greedy decoding on a
reasoning model causes repetition loops" is now vendor-documented behaviour, and we have
been running greedy on reasoning models for months. It is cheap to test: raise the
temperature and see whether the repetition signal drops.

Other confirmed flags now pinned in the launcher: `--served-model-name` (so A0's preset
name and the served model finally agree), `--reasoning-parser qwen3` and
`--tool-call-parser qwen3_coder` (the vendor's own choices), `--moe-backend auto` (resolves
to hybrid when an `ft bench bw` profile recommends it).

Every flag the launcher passes was validated against the installed argparse.

## 6. Open questions, in the order they should be answered

1. ~~Does NVFP4 load on Ampere?~~ **Answered above — yes, sm_86 is in marlin's range.**
2. Does `host.docker.internal:1235` reach a server inside the Ubuntu WSL2 distro from the
   containers? Untested, and this project has been bitten by WSL2 networking before.
3. What does `ft bench bw` report for the CPU/GPU split? That is the calibrated basis for
   `--moe-cpu-layers`, which the launcher deliberately leaves unset.
4. Does A0's thinking router handle separated `reasoning_content`?
5. Does the native `tool_calls` path remove the prose-leak failure mode?
6. Does raising temperature off 0 reduce the repetition signal? (New, from
   `--sampling-defaults` above — and testable on the CURRENT stack without FreeToken.)
