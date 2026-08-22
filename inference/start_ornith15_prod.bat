@echo off
REM ============================================================================
REM  Ornith-1.5-35B-A3B production server on :1235 (drop-in for
REM  host.docker.internal:1235).
REM
REM  WHY THIS EXISTS
REM    Ornith 1.5 is the upgrade candidate named in
REM    buildplans/SERVING_STACK_EVALUATION.md, and it has no profile because it
REM    has never been served. It ships from a DIFFERENT vendor path than 1.0:
REM        1.0  D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\
REM        1.5  D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\
REM    so the 1.0 launcher cannot be pointed at it by changing a version number.
REM
REM  ==========================================================================
REM  FIXED 2026-08-22 — THIS LAUNCHER USED THE WRONG ENGINE. Root cause below.
REM  ==========================================================================
REM  Symptom, on two attempts:
REM      llama_model_load: error loading model:
REM          missing tensor 'blk.40.ssm_conv1d.weight'
REM
REM  I first read that as "the fork predates Ornith's hybrid-SSM arch, so 1.5
REM  cannot be served here at all." That was WRONG, and the GGUF was fine.
REM  What the file actually declares:
REM      general.architecture           = qwen35moe
REM      qwen35moe.block_count          = 41
REM      qwen35moe.nextn_predict_layers = 1
REM  So blocks 0..39 are the main stack and block 40 is the MTP (nextn) head —
REM  it holds nextn.eh_proj / enorm / hnorm / shared_head_norm and correctly has
REM  NO ssm tensors. 30 of the 41 blocks do have ssm tensors; block 40 is not
REM  one of them, by design.
REM
REM  A loader that does not subtract nextn_predict_layers from block_count
REM  treats block 40 as a real layer, applies the hybrid SSM interleave, and
REM  demands ssm_conv1d there. That is exactly the error.
REM
REM  The two forks in this directory differ precisely here:
REM      turbo3-cuda     registers  qwen35moe                       <- no MTP
REM      llama-cpp-indras registers qwen35moe AND qwen35moe_mtp     <- has MTP
REM  This launcher pointed at turbo3-cuda. It now points at indras.
REM
REM  KV CACHE CHANGED AS A CONSEQUENCE. turbo3-cuda accepts -ctk turbo3;
REM  indras does NOT (verified via --help; it allows f32 f16 bf16 q8_0 q4_0
REM  q4_1 iq4_nl q5_0 q5_1 tbq3_0 tbq4_0 planar3_0 iso3_0 planar4_0 iso4_0).
REM  Using tbq4_0 to match start_qwen38_prod.bat, whose in-file sweep table
REM  measured tbq4_0 at 2925 MiB / 35.44 t/s against q8_0's 5489 MiB / 35.36 —
REM  less memory AND marginally faster.
REM
REM  NOT YET RUN. The arch-registration evidence is strong but it is still a
REM  hypothesis until this loads. Taking :1235 is Jake's call (see below), so
REM  the decisive test is his to run. If it still fails, capture the FULL load
REM  log — the next suspect is the mmproj/vision path, not the arch.
REM  ==========================================================================
REM
REM  BEFORE YOU RUN THIS — it TAKES OVER :1235
REM    Stopping the current server displaces qwen3.8-27b, which is what BOTH
REM    live agents (VekV2, agent-zero-v2) and Hermes are pointed at. Nothing
REM    that talks to :1235 will work until this is up, and A0's model name is
REM    resolved from presets.yaml, not from the server — llama.cpp ignores the
REM    requested name and serves whatever is loaded. So while this runs, an
REM    agent whose preset says ornith-1.0-35b will silently be talking to 1.5.
REM    (agent-zero-v2's preset DOES say ornith-1.0-35b as of 2026-08-22, which
REM    is why it currently loads the ornith profile while running qwen3.8.)
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
REM  The weights alone are 21.7 GB, so MoE offload is required, not optional.
REM ============================================================================

set LLAMA_BIN=%~dp0llama-cpp-indras\build\bin\llama-server.exe
set MODEL=D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\Ornith-1.5-35B-Q4_K_M.gguf
REM  Vision projector ships alongside the weights. Ornith 1.5 IS multimodal and this
REM  file is what makes image input work at all.
REM
REM  MMPROJ_ON_GPU (2026-08-22): originally CPU (--no-mmproj-offload) to spend zero
REM  VRAM, on the assumption the weights would nearly fill the card. MEASURED after it
REM  actually loaded: 18,331 MiB used of 24,576, so ~6.2 GiB was sitting free while
REM  image encoding crawled on the CPU backend -- a verified 768x768 description took
REM  45.9 s / 328 tok (~7 tok/s) against 50.3 tok/s on text. The projector is ~900 MiB.
REM  Paying a large latency penalty for VRAM we were not using is the wrong trade, so
REM  it now runs on the GPU. Set MMPROJ_ON_GPU=0 to put it back on the CPU (do that if
REM  you raise ctx or n_cpu_moe far enough to squeeze VRAM).
set MMPROJ=D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\mmproj-Ornith-1.5-35B-BF16.gguf
if "%MMPROJ_ON_GPU%"=="" set MMPROJ_ON_GPU=1

set CTX=%1
if "%CTX%"=="" set CTX=80000
set NCMOE=%2
if "%NCMOE%"=="" set NCMOE=12
set PORT=1235
set SERVER_LOG=%~dp0logs\ornith15_server.log

if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found: %LLAMA_BIN%
    echo         Run compile_indras.bat first.
    pause & exit /b 1
)
if not exist "%MODEL%" (
    echo [ERROR] Model not found: %MODEL%
    pause & exit /b 1
)
if not exist "%MMPROJ%" (
    echo [WARN] mmproj not found: %MMPROJ%
    echo        Vision will be DISABLED. Text-only mode.
    set MMPROJ=
)
if not exist "%~dp0logs" mkdir "%~dp0logs"

REM  Pre-flight: refuse to start if something already owns 1235. Without this
REM  you get a bind error buried in the log, or worse, ambiguity about which
REM  model the agents are actually talking to.
for /f %%P in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /c:":%PORT% "') do (
    echo [ABORT] Port %PORT% is already in use -- qwen3.8 is probably still running.
    echo         Stop it first; two servers cannot share this port.
    echo.
    netstat -ano | findstr /c:":%PORT% "
    pause & exit /b 1
)

set MMPROJ_ARG=
set VISION_STATUS=OFF (no mmproj)
if defined MMPROJ (
    if "%MMPROJ_ON_GPU%"=="1" (
        set MMPROJ_ARG=--mmproj "%MMPROJ%"
        set VISION_STATUS=ON - projector on GPU, ~900 MiB VRAM, fast encode
    ) else (
        set MMPROJ_ARG=--mmproj "%MMPROJ%" --no-mmproj-offload
        set VISION_STATUS=ON - projector on CPU, 0 MiB VRAM, slow encode
    )
)

echo Starting Ornith-1.5-35B-A3B  engine=llama-cpp-indras (qwen35moe_mtp)
echo   model=Ornith-1.5-35B-Q4_K_M  ctx=%CTX%  n_cpu_moe=%NCMOE%  kv=tbq4_0  port=%PORT%
echo   vision=%VISION_STATUS%

"%LLAMA_BIN%" ^
  -m "%MODEL%" ^
  %MMPROJ_ARG% ^
  -c %CTX% ^
  -fa on ^
  -ctk tbq4_0 -ctv tbq4_0 ^
  -ngl 99 --n-cpu-moe %NCMOE% ^
  --log-file "%SERVER_LOG%" ^
  --log-timestamps ^
  --log-prefix ^
  --jinja ^
  --parallel 1 ^
  --alias ornith-1.5-35b ^
  --host 0.0.0.0 --port %PORT% ^
  --metrics --cache-reuse 256
