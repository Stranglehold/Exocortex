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
REM  arg1 = CTX (default 100000).
REM    Weights ~19.9 GB dominate VRAM; KV is tiny (~4 MiB / 1K tokens, turbo3,
REM    only 10 attn layers). So the context ceiling is gated by DESKTOP GPU
REM    overhead, NOT by KV:
REM      desktop ~2.7 GB free-on-card -> 100-120K safe (150K is cliff-edge)
REM      desktop ~4.7 GB              -> keep CTX <= 64K
REM    Cliff warning: if decode collapses to ~3 tok/s, VRAM headroom was eaten
REM    by desktop apps and compute buffers spilled to system memory. Lower CTX
REM    or close GPU-using desktop apps.
REM
REM  Rollback to the dense MTP Qwen3.6-27B: inference\start_mtp_prod.bat
REM
REM  JAKE'S DOMAIN (model config) -- do before relying on idle cycles:
REM    1. Set A0 chat_model.ctx_length to match CTX (100000) so A0 never overruns.
REM    2. Ornith emits separated reasoning_content -- confirm A0's thinking router
REM       handles it (not just <think> stripping). Run the A0-native canary first.
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=100000

echo Starting Ornith-1.0-35B  model=ornith-1.0-35b-Q4_K_M  ctx=%CTX%  kv=turbo3  port=1235

"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\ornith-1.0-35b-Q4_K_M.gguf" ^
  -c %CTX% -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1235 ^
  --metrics --cache-reuse 256
