@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  CONFIGURATION
:: ============================================================

set MODEL_PATH=D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf

:: Context size — same as MTP and AtomicBot builds for fair comparison.
set CTX_SIZE=130000

:: TurboQuant KV cache (from Madreag base).
set KV_TYPE_K=turbo4
set KV_TYPE_V=turbo3

:: MTP draft tokens (am17an flag: --spec-draft-n-max, not AtomicBot's --mtp-head).
:: Set to 0 for Config 2 run (TurboQuant only, no MTP).
:: Set to 3 for Config 4 run (both combined).
set MTP_DRAFT_N=3

:: Port — distinct from TurboQuant (1234), MTP (1235), AtomicBot (1236).
set PORT=1237

set THREADS=8

:: ============================================================

set LLAMA_BIN=%~dp0llama-cpp-combined\build\bin\llama-server.exe

cls
echo ============================================================
echo  llama-server (Combined: Madreag TurboQuant + am17an MTP)  ^|  RTX 3090
echo ============================================================
echo.
echo  Model:   %MODEL_PATH%
echo  Context: %CTX_SIZE% tokens
echo  KV type: K=%KV_TYPE_K%  V=%KV_TYPE_V%
echo  MTP:     draft-n-max=%MTP_DRAFT_N% ^(0 = TurboQuant-only^)
echo  Port:    %PORT%
echo.
echo  API:     http://localhost:%PORT%/v1
echo.
echo  Config 2 test ^(TurboQuant only^): set MTP_DRAFT_N=0 and restart.
echo  Config 4 test ^(both^):            MTP_DRAFT_N=3 ^(current default^).
echo ============================================================
echo.

if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found.
    echo         Run compile_combined.bat first.
    echo         Expected: %LLAMA_BIN%
    pause & exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found:
    echo         %MODEL_PATH%
    pause & exit /b 1
)

set MTP_FLAGS=
if not "%MTP_DRAFT_N%"=="0" (
    set MTP_FLAGS=--spec-type mtp --spec-draft-n-max %MTP_DRAFT_N%
)

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
