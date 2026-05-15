@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  CONFIGURATION
:: ============================================================

set MODEL_PATH=D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf

:: Context size. TurboQuant compresses KV cache, so the same VRAM fits more context.
:: Qwen3.6 has 16 attention layers (head_dim=256) — KV is larger than Qwen3.5.
:: At turbo4/turbo3: estimated ~3,200 MiB at 130K ctx vs ~4,318 MiB at q8_0.
:: Start at 130K, check VRAM headroom, push to 160K if comfortable.
set CTX_SIZE=130000

:: KV cache — TurboQuant types (the whole point of this build).
:: turbo4 = K-cache, turbo3 = V-cache. Same flags as Madreag TurboQuant build.
set KV_TYPE_K=turbo4
set KV_TYPE_V=turbo3

:: MTP draft tokens.
:: AtomicBot uses --spec-type mtp. Flag for draft count may differ from am17an:
::   am17an:    --spec-draft-n-max 3
::   AtomicBot: --mtp-head 3  (check --help if server errors on startup)
:: Set to 0 to disable MTP and test TurboQuant-only as Config 2 in the test protocol.
set MTP_DRAFT_N=3

:: Port — separate from TurboQuant (1234) and MTP (1235) so all three can run for comparison.
set PORT=1236

set THREADS=8

:: ============================================================

set LLAMA_BIN=%~dp0llama-cpp-atomicbot\build\bin\llama-server.exe

cls
echo ============================================================
echo  llama-server (AtomicBot: MTP + TurboQuant)  ^|  RTX 3090
echo ============================================================
echo.
echo  Model:   %MODEL_PATH%
echo  Context: %CTX_SIZE% tokens
echo  KV type: K=%KV_TYPE_K%  V=%KV_TYPE_V%
echo  MTP:     draft-n=%MTP_DRAFT_N% ^(0 = TurboQuant-only baseline^)
echo  Port:    %PORT%
echo.
echo  API:     http://localhost:%PORT%/v1
echo.
echo  Config 2 test (TurboQuant only): set MTP_DRAFT_N=0 and restart.
echo  Config 4 test (both):            MTP_DRAFT_N=3 (current default).
echo ============================================================
echo.

:: Validate binary
if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found.
    echo         Run compile_atomicbot.bat first.
    echo         Expected: %LLAMA_BIN%
    pause & exit /b 1
)

:: Validate model
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found:
    echo         %MODEL_PATH%
    pause & exit /b 1
)

:: Build MTP flags
set MTP_FLAGS=
if not "%MTP_DRAFT_N%"=="0" (
    set MTP_FLAGS=--spec-type mtp --mtp-head %MTP_DRAFT_N%
)

:: Launch
"%LLAMA_BIN%" ^
    --model "%MODEL_PATH%" ^
    --ctx-size %CTX_SIZE% ^
    -ngl 99 ^
    --flash-attn on ^
    --cache-type-k %KV_TYPE_K% ^
    --cache-type-v %KV_TYPE_V% ^
    --port %PORT% ^
    --host 0.0.0.0 ^
    --parallel 1 ^
    --threads %THREADS% ^
    --metrics ^
    %MTP_FLAGS%

echo.
echo [INFO] Server stopped.
pause
