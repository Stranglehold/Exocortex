@echo off
REM AR baseline — no draft, no speculative decoding
REM Used to establish throughput ceiling for comparison with DFlash

set BUUN_DIR=D:\Vibecode\Agent-Zero\Exocortex\inference\buun-llama-cpp
set TARGET=D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf
set SERVER=%BUUN_DIR%\build\bin\llama-server.exe

set PORT=8001
if not "%1"=="" set PORT=%1

echo Starting AR baseline server (no draft)
echo   target : %TARGET%
echo   port   : %PORT%
echo.

"%SERVER%" ^
    -m   "%TARGET%" ^
    -ngl 99 ^
    -np 1 -c 8192 ^
    -fa on -b 512 -ub 512 ^
    --reasoning off ^
    --host 0.0.0.0 --port %PORT% --jinja
