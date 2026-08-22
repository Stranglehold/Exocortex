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
#  UNVERIFIED AND WORTH KNOWING: NVFP4 is a Blackwell-native format and this is
#  an Ampere card (RTX 3090, sm_86). FreeToken's docs state RTX 30/40/50 support
#  for the ENGINE but do not publish per-format architecture requirements, so
#  whether NVFP4 runs natively, emulated, or not at all on sm_86 is untested.
#  If it fails to load or is pathologically slow, switch MODEL to the FP8 repo —
#  that is the expected failure and it has a one-line fix.
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

PORT="${PORT:-1235}"          # drop-in for the existing stack, so no agent config changes
HOST="${HOST:-0.0.0.0}"       # NOT 127.0.0.1 — containers cannot reach loopback
CTX="${CTX:-80000}"           # matches start_ornith_prod.bat's default
MOE_BACKEND="${MOE_BACKEND:-offload}"   # experts in host RAM, LRU expert slots on GPU
MEMORY_RATIO="${MEMORY_RATIO:-0.85}"    # fraction of FREE VRAM the engine may use

# 0.85 not 0.95: measured 2026-08-22, the Windows desktop holds VRAM on this card
# (explorer, Discord, iCUE, EdgeWebView). A projection said 2,217 MiB free when the
# card actually had 113. Leave headroom rather than trusting the arithmetic.

echo "FreeToken | model=${MODEL}"
echo "          | ${HOST}:${PORT}  ctx=${CTX}  moe-backend=${MOE_BACKEND}  memory-ratio=${MEMORY_RATIO}"

if ! command -v ft >/dev/null 2>&1; then
  echo "ERROR: 'ft' not found. Install first, inside WSL Ubuntu:" >&2
  echo "         uv pip install --system \"freetoken[accel]\"" >&2
  exit 127
fi

exec ft serve \
  --model "${MODEL}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --moe-backend "${MOE_BACKEND}" \
  --memory-ratio "${MEMORY_RATIO}" \
  --max-seq-len-override "${CTX}" \
  --moe-cache-auto
