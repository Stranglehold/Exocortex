@echo off
setlocal enabledelayedexpansion

set PYTHON=python
set EVAL_DIR=%~dp0
set SWEEP_SCRIPT=%EVAL_DIR%vram_sweep.py
set TPS_SCRIPT=%EVAL_DIR%tps_bench.ps1

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set _DT=%%I
set TIMESTAMP=%_DT:~0,8%_%_DT:~8,6%
set RESULTS_BASE=%EVAL_DIR%results
if not exist "%RESULTS_BASE%" mkdir "%RESULTS_BASE%"
set RESULTS_DIR=%RESULTS_BASE%\%TIMESTAMP%
mkdir "%RESULTS_DIR%" 2>nul

cls
echo ============================================================
echo  MTP Eval Suite
echo ============================================================
echo.
echo  Which config are you testing?
echo.
echo  [1] Config C - No MTP        (port 1235, MTP_DRAFT_N=0)
echo  [2] Config B - MTP n=2       (port 1235, MTP_DRAFT_N=2)
echo  [3] Config A - MTP n=3       (port 1235, MTP_DRAFT_N=3)
echo  [4] TurboQuant baseline      (port 1234)
echo  [5] AtomicBot TurboQuant only  (port 1236, MTP_DRAFT_N=0)
echo  [6] AtomicBot MTP + TurboQuant (port 1236, MTP_DRAFT_N=3)
echo  [7] Combined TurboQuant only   (port 1237, MTP_DRAFT_N=0)
echo  [8] Combined MTP + TurboQuant  (port 1237, MTP_DRAFT_N=3)
echo.
set CONFIG_CHOICE=
set /p CONFIG_CHOICE=Select [1-8]:

if "%CONFIG_CHOICE%"=="1" (
    set PORT=1235
    set CONFIG_LABEL=Config_C_NoMTP
    set CONFIG_DESC=Config C: No MTP
)
if "%CONFIG_CHOICE%"=="2" (
    set PORT=1235
    set CONFIG_LABEL=Config_B_MTP_n2
    set CONFIG_DESC=Config B: MTP n=2
)
if "%CONFIG_CHOICE%"=="3" (
    set PORT=1235
    set CONFIG_LABEL=Config_A_MTP_n3
    set CONFIG_DESC=Config A: MTP n=3
)
if "%CONFIG_CHOICE%"=="4" (
    set PORT=1234
    set CONFIG_LABEL=TurboQuant
    set CONFIG_DESC=TurboQuant baseline
)
if "%CONFIG_CHOICE%"=="5" (
    set PORT=1236
    set CONFIG_LABEL=AtomicBot_TurboQuant_only
    set CONFIG_DESC=AtomicBot: TurboQuant only (no MTP)
)
if "%CONFIG_CHOICE%"=="6" (
    set PORT=1236
    set CONFIG_LABEL=AtomicBot_MTP_plus_TurboQuant
    set CONFIG_DESC=AtomicBot: MTP n=3 + TurboQuant
)
if "%CONFIG_CHOICE%"=="7" (
    set PORT=1237
    set CONFIG_LABEL=Combined_TurboQuant_only
    set CONFIG_DESC=Combined: TurboQuant only (no MTP)
)
if "%CONFIG_CHOICE%"=="8" (
    set PORT=1237
    set CONFIG_LABEL=Combined_MTP_plus_TurboQuant
    set CONFIG_DESC=Combined: MTP n=3 + TurboQuant
)

if not defined PORT (
    echo.
    echo [ERROR] Invalid selection: "%CONFIG_CHOICE%"
    pause & exit /b 1
)

set TPS_OUT=%RESULTS_DIR%\tps_raw.json
set SWEEP_OUT=%RESULTS_DIR%\vram_sweep.txt

cls
echo ============================================================
echo  %CONFIG_DESC%  /  port %PORT%
echo  Results: %RESULTS_DIR%
echo ============================================================
echo.

echo [1/3] Connectivity check...
curl -s --max-time 5 http://localhost:%PORT%/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] No response from localhost:%PORT%
    echo         Start the llama-server first.
    echo         MTP build:  run start_mtp.bat
    echo         TurboQuant: run start.bat
    echo.
    pause & exit /b 1
)
echo        Server is up on port %PORT%.
echo.

echo [2/3] Raw TPS benchmark (merge sort, 500 tokens)...
echo        Takes 10-120 seconds depending on config.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%TPS_SCRIPT%" -Port %PORT% -OutFile "%TPS_OUT%"
echo.

echo [3/3] VRAM sweep across context lengths...
echo        Sends prompts of increasing length, records peak VRAM and tok/s.
echo        Takes 5-20 min. Press Ctrl+C to abort early.
echo.
%PYTHON% "%SWEEP_SCRIPT%" --port %PORT% --output "%SWEEP_OUT%"

echo.
echo ============================================================
echo  Eval complete: %CONFIG_DESC%
echo  Results saved to:
echo    %TPS_OUT%
echo    %SWEEP_OUT%
echo ============================================================
echo.
pause
