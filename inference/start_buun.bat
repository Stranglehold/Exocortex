@echo off
REM Start DFlash via buun-llama-cpp (spiritbuun fork)
REM Qwen3.6-27B target + Qwen3.6-DFlash-Q8_0 draft, flat DFlash (~38 tok/s, 1.56x AR)
REM DDTree is NOT available in llama-server (speculative-simple binary only)
REM
REM Usage:
REM   start_buun.bat          -- port 8000 (default)
REM   start_buun.bat 8080     -- custom port

set BUUN_DIR=D:\Vibecode\Agent-Zero\Exocortex\inference\buun-llama-cpp
set TARGET=D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf
set DRAFT=D:\LMStudio\Models\spiritbuun\Qwen3.6-27B-DFlash-GGUF\dflash-draft-3.6-q8_0.gguf
set SERVER=%BUUN_DIR%\build\bin\llama-server.exe

set PORT=8000
if not "%1"=="" set PORT=%1

echo Starting buun DFlash server
echo   target : %TARGET%
echo   draft  : %DRAFT%
echo   port   : %PORT%
echo.

"%SERVER%" ^
    -m   "%TARGET%" ^
    -md  "%DRAFT%" ^
    --spec-dflash-default ^
    -ngl 99 -ngld 99 ^
    -np 1 -c 8192 -cd 2048 ^
    -fa on -b 256 -ub 64 ^
    --reasoning off ^
    --host 0.0.0.0 --port %PORT% --jinja
