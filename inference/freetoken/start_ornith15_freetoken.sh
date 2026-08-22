#!/usr/bin/env bash
# =============================================================================
#  Ornith-1.5-35B-A3B on FreeToken — WSL2 (Ubuntu), drop-in on :1235
#
#  Stack 2 of buildplans/SERVING_STACK_EVALUATION.md. FreeToken is edge-native
#  MoE serving with bandwidth-adaptive CPU-GPU co-execution; Ornith-1.5-35B-A3B
#  is precisely its target class (35B total, 3B active).
#  Repo:  https://github.com/FlashML-org/FreeToken
#  Paper: arXiv:2608.16157
#
#  ---------------------------------------------------------------------------
#  VERIFIED ON THIS MACHINE 2026-08-22 (not assumed):
#    driver 596.36            >= r580 required            OK
#    CUDA 13.2                CUDA 13 required            OK
#    WSL2 2.7.11.0, k6.18     Linux x86_64 required       OK
#    Ubuntu python 3.12.3     >= 3.10 required            OK
#    uv 0.10.10               recommended installer       OK
#    nvidia-smi inside WSL    sees the RTX 3090           OK  (GPU passthrough works)
#    WSL rootfs free          951 GB                      OK
#
#  ---------------------------------------------------------------------------
#  THE FORMAT DECISION — WHY NOT OUR LOCAL GGUF
#
#  FreeToken does NOT load GGUF. `--model` takes "Local dir, HF repo id, or an
#  FTW dir"; FTW is FreeToken's own format, converted from HF safetensors. The
#  documented quantizations are MXFP4 / NVFP4 / FP8 / BF16. So
#  D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\...Q4_K_M.gguf — what
#  start_ornith15_prod.bat uses for llama.cpp — is unusable here. Different
#  engine, different weights.
#
#  WSL RAM is the binding constraint, NOT VRAM. The offload backend keeps
#  experts in HOST RAM. WSL2 reports 62 GB total / 55 available on this box
#  (it defaults to ~half of host RAM), so:
#      NVFP4  ~20 GB   fits comfortably      <- default below
#      FP8    ~35 GB   fits                  <- first fallback
#      BF16   ~70 GB   DOES NOT FIT unless .wslconfig raises the WSL limit
#
#  RESOLVED 2026-08-22 — NVFP4 DOES run on Ampere. I had flagged this as the main
#  risk, on the strength of NVFP4 being a Blackwell-native format. `ft serve --help`
#  on the INSTALLED 0.1.2 settles it:
#      --nvfp4-backend  "auto picks by GPU (marlin on sm80-99 + vLLM; flashinfer
#                        b12x on sm120+ & CUDA>=13; else triton, the portable
#                        inline-dequant kernel)"
#  This card is sm_86, inside sm80-99, so auto selects marlin — and if marlin's
#  vLLM dependency is absent it falls back to triton, which is portable. Either
#  way it loads. The published docs never mention this flag; it came from the
#  installed binary. FP8 stays a one-line fallback if throughput disappoints.
#
#  ---------------------------------------------------------------------------
#  NOT YET INSTALLED. One-time, inside WSL Ubuntu:
#      uv pip install --system "freetoken[accel]"
#  Then calibrate the CPU/GPU split EMPIRICALLY rather than guessing at
#  --moe-cpu-layers:
#      ft bench bw
#
#  ---------------------------------------------------------------------------
#  OPEN NETWORK QUESTION — TEST THIS BEFORE POINTING AN AGENT AT IT
#
#  --host 0.0.0.0 is mandatory: FreeToken defaults to 127.0.0.1, which no Docker
#  container can reach. But whether `host.docker.internal:1235` from VekV2 /
#  agent-zero-v2 routes through to a server inside the *Ubuntu* WSL2 distro is
#  NOT verified. Docker Desktop runs in its own WSL2 distro, and this project
#  has been bitten by WSL2 networking before (see memory: WSL2 NAT mode could
#  not reach Windows-hosted services without an explicit host IP + firewall
#  rule). Check from the host first, then from a container:
#      curl -s http://127.0.0.1:1235/v1/models                     # Windows host
#      docker exec VekV2 curl -s http://host.docker.internal:1235/v1/models
#  If the container cannot reach it, the fix is likely the WSL IP rather than
#  host.docker.internal — `hostname -I` inside Ubuntu.
# =============================================================================
set -euo pipefail

# NVFP4 by default: smallest, and explicitly on FreeToken's supported list.
# Fallbacks, in order of preference if this one will not load on Ampere:
#   ornith-ai/Ornith-1.5-35B-A3B-FP8    (~35 GB, compressed-tensors)
#   ornith-ai/Ornith-1.5-35B-A3B        (~70 GB BF16 — needs a .wslconfig bump)
MODEL="${MODEL:-ornith-ai/Ornith-1.5-35B-A3B-NVFP4}"

SERVED_NAME="${SERVED_NAME:-ornith-1.5-35b}"   # what /v1/models reports; match A0's preset
PORT="${PORT:-1235}"          # drop-in for the existing stack, so no agent config changes
HOST="${HOST:-0.0.0.0}"       # NOT 127.0.0.1 — containers cannot reach loopback
CTX="${CTX:-80000}"           # matches start_ornith_prod.bat's default
MOE_BACKEND="${MOE_BACKEND:-auto}"      # auto -> offload family, or hybrid per `ft bench bw`
NVFP4_BACKEND="${NVFP4_BACKEND:-auto}"  # auto -> marlin on sm80-99 (this card is sm_86)
MEMORY_RATIO="${MEMORY_RATIO:-0.85}"    # fraction of FREE VRAM the engine may use

# 0.85 not 0.95: measured 2026-08-22, the Windows desktop holds VRAM on this card
# (explorer, Discord, iCUE, EdgeWebView). A projection said 2,217 MiB free when the
# card actually had 113. Leave headroom rather than trusting the arithmetic.

echo "FreeToken | model=${MODEL}"
echo "          | ${HOST}:${PORT}  ctx=${CTX}  moe-backend=${MOE_BACKEND}  memory-ratio=${MEMORY_RATIO}"

# FreeToken lives in a venv rather than --system, so the install is reversible with
# `rm -rf ~/freetoken-env` and cannot break the distro's python. Activate it here so the
# launcher works from a plain `wsl bash -lc` with no prior activation.
FT_VENV="${FT_VENV:-$HOME/freetoken-env}"
if [ -f "${FT_VENV}/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${FT_VENV}/bin/activate"
fi

if ! command -v ft >/dev/null 2>&1; then
  echo "ERROR: 'ft' not found (looked in ${FT_VENV} and PATH). Install inside WSL Ubuntu:" >&2
  echo "         uv venv ~/freetoken-env --python 3.12" >&2
  echo "         source ~/freetoken-env/bin/activate && uv pip install \"freetoken[accel]\"" >&2
  exit 127
fi

# Flags below were read from `ft serve --help` on the INSTALLED 0.1.2, not from the docs.
# The docs do not mention --nvfp4-backend, --sampling-defaults or --served-model-name, and
# the first two are the two that matter most here.
#
#   --moe-backend auto     resolves a MoE model to the offload family, and to HYBRID when
#                          an `ft bench bw` profile recommends it. auto beats hardcoding
#                          offload precisely because it consumes the calibration.
#   --nvfp4-backend auto   "marlin on sm80-99; flashinfer on sm120+; else triton". This
#                          card is sm_86, so NVFP4 IS supported on Ampere — the open
#                          question in the header is answered. Worst case it falls back to
#                          triton, the portable kernel. Force marlin/triton to override.
#   --sampling-defaults model
#                          fills temperature/top_k/top_p from the checkpoint's
#                          generation_config.json for requests that do not specify them.
#                          The help calls this "recommended for reasoning models to avoid
#                          greedy repetition loops" — and our A0 preset currently sends
#                          temperature '0', which IS greedy. A client-sent value still
#                          wins, so this does not replace fixing the preset
#                          (scripts/set_preset_sampling.py); it makes the default sane.
#   --served-model-name    what /v1/models reports. Set so A0's preset name and the served
#                          model finally agree — they have not, and that is why tiering
#                          resolves off a name rather than the running model.
#   --reasoning-parser qwen3 / --tool-call-parser qwen3_coder
#                          the vendor's own vLLM/SGLang commands set these explicitly.
#                          'auto' would likely pick them, but this model emits
#                          <think>...</think> with separated reasoning_content and native
#                          OpenAI tool_calls, and both are load-bearing for A0 — so they
#                          are pinned rather than inferred.
exec ft serve \
  --model "${MODEL}" \
  --served-model-name "${SERVED_NAME}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --moe-backend "${MOE_BACKEND}" \
  --nvfp4-backend "${NVFP4_BACKEND}" \
  --memory-ratio "${MEMORY_RATIO}" \
  --max-seq-len-override "${CTX}" \
  --sampling-defaults model \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder \
  --moe-cache-auto
