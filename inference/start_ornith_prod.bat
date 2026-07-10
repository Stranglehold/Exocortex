@echo off
REM ============================================================================
REM  Ornith-1.0-35B production server on :1235 (drop-in for host.docker.internal:1235).
REM  qwen35moe hybrid (34.66B total / ~3B active, fused Gated-Delta-Net + 10 attn
REM  layers). turbo3-cuda build + turbo3 KV. Native context 262K.
REM
REM  Validated 2026-06-27 (Kestrel eval, see opus/jake inboxes):
REM    - loads clean on turbo3 build (no tensor errors)
REM    - decode ~95 tok/s @ d0 -> ~72 @ d32k (~3-3.6x the dense Qwen3.6-27B's ~26)
REM    - prefill ~2000 tok/s (~2x dense 27B); 144*17 correct
REM    - structured tool_calls: single + multi-arg both PASS (needs --jinja)
REM    - reasoning lands in choices[].message.reasoning_content (NOT <think> tags)
REM
REM  arg1 = CTX (default 80000).
REM    Weights ~19.7 GB dominate VRAM; KV is tiny (~4 MiB / 1K tokens, turbo3,
REM    only 10 attn layers). So the context ceiling is gated by DESKTOP GPU
REM    overhead, NOT by KV:
REM      desktop ~2.7 GB free-on-card -> 100-120K safe (150K is cliff-edge)
REM      desktop ~4.7 GB              -> keep CTX <= 64K
REM    Cliff warning: if decode collapses to ~3 tok/s, VRAM headroom was eaten
REM    by desktop apps and compute buffers spilled to system memory. Lower CTX,
REM    raise arg2 (MoE offload below), or close GPU-using desktop apps.
REM
REM  arg2 = N_CPU_MOE  (default 12). THE ANTI-BOG DIAL.
REM    Ornith is MoE: 40 layers, 256 experts (8 used/token). The routed experts
REM    ARE ~all of the 19.7 GB, but only 8/256 fire per token. --n-cpu-moe N keeps
REM    the FIRST N layers' experts in system RAM (fetched over PCIe on demand),
REM    freeing ~0.49 GB of VRAM per offloaded layer:
REM       0   -> all experts on GPU  (fastest ~95 tok/s; bogs if VRAM overcommits)
REM       12  -> frees ~6 GB         (default: fits a 2.7-4.7 GB desktop; ~60-75 tok/s)
REM       16  -> frees ~8 GB         (heavy desktop / more headroom)
REM       40  -> ALL experts on CPU  (~1-2 GB VRAM footprint; slowest, most headroom)
REM    Tune live: load, check `nvidia-smi` used-VRAM, raise N until ~3-4 GB free.
REM
REM  *** DO THIS ONCE (kills the whole-machine bog for good) ***
REM    NVIDIA Control Panel -> Manage 3D Settings -> Program Settings ->
REM    add llama-server.exe -> "CUDA - Sysmem Fallback Policy" = "Prefer No
REM    Sysmem Fallback". Then a VRAM overcommit fails CLEANLY (OOM you can see)
REM    instead of silently spilling to system RAM and thrashing the desktop.
REM    With this set, a too-low arg2 just OOMs at load -> bump arg2, relaunch.
REM
REM  Rollback to the dense MTP Qwen3.6-27B: inference\start_mtp_prod.bat
REM
REM  JAKE'S DOMAIN (model config) -- do before relying on idle cycles:
REM    1. Set A0 chat_model.ctx_length to match CTX (100000) so A0 never overruns.
REM    2. Ornith emits separated reasoning_content -- confirm A0's thinking router
REM       handles it (not just <think> stripping). Run the A0-native canary first.
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=80000
set NCMOE=%2
if "%NCMOE%"=="" set NCMOE=12

echo Starting Ornith-1.0-35B  model=ornith-1.0-35b-Q4_K_M  ctx=%CTX%  n_cpu_moe=%NCMOE%  kv=turbo3  port=1235

"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\ornith-1.0-35b-Q4_K_M.gguf" ^
  -c %CTX% -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 --n-cpu-moe %NCMOE% ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1235 ^
  --metrics --cache-reuse 256
