@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  CONFIGURATION — edit these before first run
:: ============================================================

:: Full path to your .gguf model file
set MODEL_PATH=D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf

:: Context size (tokens). Estimates for RTX 3090 + Q4_K_M weights + turbo3 KV:
::   32768  — safe baseline,  ~18GB VRAM
::   80000  — comfortable,    ~19GB VRAM (NousResearch reference point)
::   131072 — extended,       ~20GB VRAM
::   160000 — stress test,    ~21GB VRAM  (see eval/TURBOQUANT_BUILD_VALIDATION.md Test 5)
::   196608 — near-maximum,   ~22GB VRAM  (estimate — validate with nvidia-smi)
:: Run Test 5 in the validation doc before pushing past 131k.
set CTX_SIZE=163840

:: KV cache quantization — set K and V independently for asymmetric configs.
::
::   Turbo types (WHT-rotated, purpose-built compression):
::     turbo4  — ~q8_0 quality, good compression     (K: recommended)
::     turbo3  — ~1% PPL delta, 5.1x vs fp16         (V: recommended)
::     turbo2  — more compression, more quality loss
::   Standard types (fallback/comparison):
::     q4_0    — baseline, high kurtosis, less efficient than turbo
::     q8_0    — near-lossless, ~2x memory vs turbo3
::     f16     — full precision (LM Studio default)
::
:: Config A (default): asymmetric turbo4/turbo3 — highest quality at good compression
:: Config B:           turbo3/turbo3             — best balance, saves more VRAM
:: Config C:           turbo4/turbo4             — safest, closest to q8_0
::
:: IMPORTANT: -fa (flash attention) is REQUIRED when KV_TYPE_V=turbo3.
::            Without it, turbo3 V materializes O(n^2) attention and will OOM.
set KV_TYPE_K=turbo4
set KV_TYPE_V=turbo3

:: CPU threads for prompt ingestion (physical core count, not logical)
set THREADS=8

:: Port — 1234 matches LM Studio default.
:: All existing Exocortex + OSS config works without changes.
set PORT=1234

:: ============================================================

set LLAMA_BIN=%~dp0turbo3-cuda\build\bin\llama-server.exe
set DASHBOARD_PATH=%~dp0

cls
echo ============================================================
echo  llama-server  ^|  RTX 3090
echo ============================================================
echo.
echo  Model:   %MODEL_PATH%
echo  Context: %CTX_SIZE% tokens
echo  KV type: K=%KV_TYPE_K%  V=%KV_TYPE_V%
echo  Port:    %PORT%
echo.
echo  Dashboard: http://localhost:%PORT%/dashboard.html
echo  API:       http://localhost:%PORT%/v1
echo.
echo ============================================================
echo.

:: Validate binary
if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found.
    echo         Run compile.bat first ^(clones Madreag/turbo3-cuda + builds^).
    echo         Expected: %LLAMA_BIN%
    pause & exit /b 1
)

:: Validate model
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found:
    echo         %MODEL_PATH%
    echo         Edit MODEL_PATH at the top of this file.
    pause & exit /b 1
)

:: Launch — dashboard served from this directory via --path
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
    --path "%DASHBOARD_PATH%"

:: If server exits unexpectedly, hold the window
echo.
echo [INFO] Server stopped.
pause
