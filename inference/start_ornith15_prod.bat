@echo off
REM ============================================================================
REM  Ornith-1.5-35B-A3B production server on :1235 (drop-in for
REM  host.docker.internal:1235). Derived from start_ornith_prod.bat (1.0) —
REM  same engine, same KV, same port. ONLY the model path and labels differ.
REM
REM  WHY THIS EXISTS
REM    Ornith 1.5 is the upgrade candidate named in
REM    buildplans/SERVING_STACK_EVALUATION.md, and it has no profile because it
REM    has never been served. It ships from a DIFFERENT vendor path than 1.0:
REM        1.0  D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\
REM        1.5  D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\
REM    so the 1.0 launcher cannot be pointed at it by changing a version number.
REM
REM  BEFORE YOU RUN THIS — it TAKES OVER :1235
REM    Stopping the current server displaces qwen3.8-27b, which is what BOTH
REM    live agents (VekV2, agent-zero-v2) and Hermes are pointed at. Nothing
REM    that talks to :1235 will work until this is up, and A0's model name is
REM    resolved from presets.yaml, not from the server — llama.cpp ignores the
REM    requested name and serves whatever is loaded. So while this runs, an
REM    agent whose preset says ornith-1.0-35b will silently be talking to 1.5.
REM
REM  TO PROFILE IT once this is serving:
REM    python eval_framework/eval_runner.py --provider lmstudio ^
REM      --api-base http://127.0.0.1:1235/v1 --model-name ornith-1.5-35b ^
REM      --modules bst bst_rigidity tool_reliability graph_compliance ^
REM               pace_calibration context_sensitivity memory_utilization --verbose
REM
REM  NOTE ON n_cpu_moe: 1.5 is A3B (3B active). The 1.0 default of 12 offloaded
REM  MoE layers is a STARTING POINT carried over, not a measurement for 1.5 —
REM  tune it against VRAM headroom before quoting any throughput number.
REM  Measured 2026-08-22: usable VRAM on this card is well below 24,576 MiB
REM  because the Windows desktop holds some; a projection is not a measurement.
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=80000
set NCMOE=%2
if "%NCMOE%"=="" set NCMOE=12

echo Starting Ornith-1.5-35B-A3B  model=Ornith-1.5-35B-Q4_K_M  ctx=%CTX%  n_cpu_moe=%NCMOE%  kv=turbo3  port=1235

"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\Ornith-1.5-35B-Q4_K_M.gguf" ^
  -c %CTX% -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 --n-cpu-moe %NCMOE% ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1235 ^
  --metrics --cache-reuse 256
