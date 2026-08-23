@echo off
REM ============================================================================
REM  Ornith-1.5-35B-A3B on NATIVE FreeToken (Windows) -- port 1235
REM
REM  VERIFIED WORKING 2026-08-22 21:44 on :1235. Reproduces the exact invocation
REM  that served: 66.3 tok/s, native structured tool_calls, reasoning_content
REM  separated, and BOTH containers reaching it (verified on :1236; moved to :1235
REM
REM  so existing agent/Hermes configs need no change).
REM
REM  WHY NATIVE AND NOT WSL
REM    The WSL launchers (start_ornith15_freetoken.bat / freetoken/*.sh) are
REM    RETIRED -- see their headers. FreeToken's offload backend pins expert
REM    banks with cudaHostRegister, and WSL2 caps cumulative pinned host memory
REM    at ~1.00 GiB against the 16.9 GiB needed. Measured natively on this box:
REM    40 GiB pinned with NO failure (test stopped there, not the limit). That
REM    single difference is why this works and thirteen WSL attempts did not.
REM
REM  WHY --model POINTS AT THE RAW SAFETENSORS, NOT OUR FTW
REM    We built an FTW in WSL with freetoken 0.1.2. The desktop app pins engine
REM    0.1.1+g30aa89115, and 0.1.2's converter keeps modelopt's `input_scale`
REM    activation scales (for W8A8 batched decode) which 0.1.1's model class does
REM    not declare. Loading it dies with:
REM        RuntimeError: Unexpected keys in state_dict:
REM        ['model.layers.0.linear_attn.in_proj_qkvz.input_scale', ...]
REM    Serving the RAW safetensors sidesteps it entirely -- 0.1.1 reads only the
REM    keys it expects. Conversion is an optional fast-load step, not a
REM    requirement (docs: "ft serve --model auto-detects the result").
REM    The 0.1.2 FTW at ...\Ornith-1.5-35B-A3B-FTW becomes valid again if/when
REM    the desktop engine moves past 0.2.0-beta.13.
REM
REM  LOAD TIME: ~26 MIN COLD, ~4.5 MIN WARM. Neither is a hang.
REM    MEASURED both: 26 min on the first load of a session, 4.5 min on a reload
REM    while the safetensors were still in the OS file cache.
REM    The serial expert-bank build is genuinely slow ("slow path (serial
REM    build)"). Host RAM climbs to ~27 GB and CPU sits around 3 cores the whole
REM    time. /health reports {"status":"loading"} throughout, then flips to
REM    {"status":"ok"}. Do not kill a COLD start at 10 minutes. Converting to FTW with the
REM    NATIVE 0.1.1 `ft checkpoint` is what would shorten this -- untried, and it
REM    needs cuda:0 free (i.e. nothing else serving).
REM
REM  PORT 1235 -- THE SAME PORT AS llama.cpp, DELIBERATELY
REM    Everything already points here: both A0 containers via
REM    host.docker.internal:1235, and the Hermes desktop interface. Using 1235
REM    means no config changes anywhere to switch engines.
REM    It DOES collide with start_ornith15_prod.bat (llama.cpp). Only one can run
REM    at a time -- both abort cleanly on the port pre-flight rather than
REM    half-starting, so pick an engine and run that launcher. For reference, on
REM    identical weights:
REM        llama.cpp    50.3 tok/s, ~4 min load,  vision working ~2.8 s/image
REM        FreeToken    66.3 tok/s, 26 min cold / 4.5 min warm, vision untested
REM    NOTE: an earlier reading put FreeToken at 45.3 tok/s. That was measured
REM    while the desktop app's Qwen engine was ALSO resident and competing for
REM    the card. With the GPU dedicated it is 66-69 tok/s -- FreeToken is the
REM    FASTER engine here, not the slower one. Close the desktop app before
REM    benchmarking, or you are measuring contention.
REM
REM  AGENTS REACH IT AT host.docker.internal:1235 (verified 200 from both
REM  VekV2 and agent-zero-v2). 172.27.x.x and 172.17.0.1 do NOT work.
REM ============================================================================

set FT=%LOCALAPPDATA%\FreeToken\venv\Scripts\ft.exe
set MODEL=D:\LMStudio\Models\ornith-ai\Ornith-1.5-35B-A3B-NVFP4
set PORT=1235
set CTX=%1
if "%CTX%"=="" set CTX=32768
set BACKEND=%2
if "%BACKEND%"=="" set BACKEND=offload

if not exist "%FT%" (
    echo [ERROR] ft.exe not found: %FT%
    echo         Install FreeToken Desktop, or correct FT above.
    pause & exit /b 1
)
if not exist "%MODEL%" (
    echo [ERROR] Model not found: %MODEL%
    pause & exit /b 1
)

REM  Pre-flight: refuse to start if something already owns the port, rather than
REM  burying a bind error 26 minutes into a load.
for /f %%P in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /c:":%PORT% "') do (
    echo [ABORT] Port %PORT% is already in use.
    netstat -ano | findstr /c:":%PORT% "
    pause & exit /b 1
)

echo Starting Ornith-1.5-35B-A3B on NATIVE FreeToken
echo   model=%MODEL%
echo   port=%PORT%  ctx=%CTX%  moe-backend=%BACKEND%
echo   EXPECT ~26 MINUTES to reach status=ok. Watch with:
echo     curl http://127.0.0.1:%PORT%/health
echo.

"%FT%" serve ^
  --model "%MODEL%" ^
  --served-model-name ornith-1.5-35b ^
  --host 0.0.0.0 --port %PORT% ^
  --moe-backend %BACKEND% ^
  --nvfp4-backend auto ^
  --sampling-defaults model ^
  --reasoning-parser qwen3 ^
  --tool-call-parser qwen3_coder ^
  --max-seq-len-override %CTX%
