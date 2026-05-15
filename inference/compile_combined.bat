@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  Combined build  ^| Madreag TurboQuant + am17an MTP  ^| RTX 3090
echo ============================================================
echo.
echo  Strategy: clone Madreag/turbo3-cuda (turbo4/turbo3 KV) into
echo            llama-cpp-combined, then cherry-pick 7 MTP commits
echo            from am17an/mtp-clean onto it.
echo.
echo  If a cherry-pick conflicts: resolve in a second terminal,
echo  then re-run this script — progress is saved and it resumes
echo  from where it left off.
echo.
echo ============================================================
echo.

set CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin
set PATH=%PATH%;%CUDA_BIN%
set LLAMA_DIR=%~dp0llama-cpp-combined
set MTP_REMOTE=https://github.com/am17an/llama.cpp.git
set MTP_BRANCH=mtp-clean
set PROGRESS_FILE=%LLAMA_DIR%\.picks_progress

:: 7 MTP commits, oldest first.
:: Skipped: Metal (038d78760), Vulkan (b8ec08554),
::          Python converter (d6c4de878), test-llama-arch (267f8afe8)
set PICK_1=1a4fe4e6c
set PICK_1_DESC=llama: allow partial seq_rm for GDN models
set PICK_2=589490f09
set PICK_2_DESC=add enum for part sequence removal to enable checkpoints
set PICK_3=c5e02271c
set PICK_3_DESC=review: rename rollback to rs_seq and remove public API
set PICK_4=10829dbcc
set PICK_4_DESC=llama + spec: MTP support  [CORE]
set PICK_5=f8c6b03da
set PICK_5_DESC=add qwen35moe_mtp
set PICK_6=86d9f15e9
set PICK_6_DESC=fix double free
set PICK_7=5d5f1b46e
set PICK_7_DESC=fix: use rs for only MTP

:: ============================================================
:: SETUP: Clone (first run) or skip (resume)
:: ============================================================

if exist "%LLAMA_DIR%\.git" (
    echo [INFO] llama-cpp-combined already exists — skipping clone.
    echo        ^(will NOT git pull to preserve cherry-picks^)
    echo.
    goto setup_remote
)

echo [INFO] Cloning Madreag/turbo3-cuda into llama-cpp-combined...
echo        ^(uses the existing local copy to avoid re-downloading^)
echo.
git clone "%~dp0turbo3-cuda" "%LLAMA_DIR%"
if errorlevel 1 (
    echo.
    echo [INFO] Local clone failed — trying GitHub directly...
    git clone https://github.com/Madreag/turbo3-cuda "%LLAMA_DIR%"
    if errorlevel 1 goto err_clone
)

:setup_remote
cd /d "%LLAMA_DIR%"

echo [INFO] Checking am17an remote...
git remote get-url mtp >nul 2>&1
if errorlevel 1 (
    echo [INFO] Adding am17an remote...
    git remote add mtp %MTP_REMOTE%
)

echo [INFO] Fetching am17an/%MTP_BRANCH%...
git fetch mtp %MTP_BRANCH%
if errorlevel 1 goto err_fetch

:: Verify the core commit exists locally after fetch
git cat-file -e %PICK_4% >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Core MTP commit %PICK_4% not found after fetch.
    echo         The commit hash may have changed — check the am17an repo:
    echo           git log mtp/mtp-clean --oneline ^| head -20
    echo         Update PICK_4 in this script if needed.
    pause & exit /b 1
)

:: ============================================================
:: CHERRY-PICK PHASE
:: ============================================================

:: If CHERRY_PICK_HEAD exists, a conflict is unresolved.
if exist "%LLAMA_DIR%\.git\CHERRY_PICK_HEAD" (
    echo.
    echo ============================================================
    echo  CONFLICT IN PROGRESS
    echo ============================================================
    echo.
    echo  A cherry-pick conflict is not yet resolved.
    echo  Steps to continue:
    echo.
    echo    cd %LLAMA_DIR%
    echo    git status              ^(shows conflicted files with ^<^<^<^<^<^<^<^)
    echo    ^(edit each file: keep TurboQuant KV code + add MTP additions^)
    echo    git add ^<resolved-files^>
    echo    git cherry-pick --continue
    echo.
    echo  Then re-run this script — it will resume from the saved progress.
    echo.
    pause & exit /b 1
)

:: Read progress — how many picks have been successfully applied.
set PICKS_DONE_STR=0
if exist "%PROGRESS_FILE%" (
    set /p PICKS_DONE_STR=<"%PROGRESS_FILE%"
)
set /a PICKS_DONE=%PICKS_DONE_STR%

echo.
if %PICKS_DONE% gtr 0 (
    echo [INFO] Resuming — %PICKS_DONE%/7 cherry-picks already applied.
) else (
    echo [INFO] Starting cherry-pick phase.
    echo.
    echo  Commits to apply ^(oldest → newest^):
    echo    1: %PICK_1%  %PICK_1_DESC%
    echo    2: %PICK_2%  %PICK_2_DESC%
    echo    3: %PICK_3%  %PICK_3_DESC%
    echo    4: %PICK_4%  %PICK_4_DESC%
    echo    5: %PICK_5%  %PICK_5_DESC%
    echo    6: %PICK_6%  %PICK_6_DESC%
    echo    7: %PICK_7%  %PICK_7_DESC%
    echo.
    echo  Press any key to begin cherry-picks...
    pause >nul
)
echo.

if %PICKS_DONE% geq 1 goto do_pick_2
echo [INFO] 1/7: %PICK_1_DESC%
git cherry-pick %PICK_1%
if errorlevel 1 ( call :conflict_help 1 "%PICK_1%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 1

:do_pick_2
if %PICKS_DONE% geq 2 goto do_pick_3
echo [INFO] 2/7: %PICK_2_DESC%
git cherry-pick %PICK_2%
if errorlevel 1 ( call :conflict_help 2 "%PICK_2%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 2

:do_pick_3
if %PICKS_DONE% geq 3 goto do_pick_4
echo [INFO] 3/7: %PICK_3_DESC%
git cherry-pick %PICK_3%
if errorlevel 1 ( call :conflict_help 3 "%PICK_3%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 3

:do_pick_4
if %PICKS_DONE% geq 4 goto do_pick_5
echo [INFO] 4/7: %PICK_4_DESC%
git cherry-pick %PICK_4%
if errorlevel 1 (
    echo.
    echo  [NOTE] This is the CORE MTP commit. Conflicts in llama.cpp and llama.h
    echo         are expected — both forks modify these files.
    echo.
    echo  Conflict resolution guidance for the CORE commit:
    echo    - In llama.cpp: keep ALL TurboQuant KV-cache code unchanged.
    echo                    ADD the MTP additions alongside it.
    echo    - In llama.h:   keep TurboQuant struct fields, ADD MTP fields
    echo                    ^(mtp_pool, spec_mtp_*, MTP head counts^).
    echo    - MTP adds NEW functions — you should rarely need to modify
    echo      existing lines, mostly just accept both sets of additions.
    call :conflict_help 4 "%PICK_4%"
    exit /b 1
)
> "%PROGRESS_FILE%" echo 4

:do_pick_5
if %PICKS_DONE% geq 5 goto do_pick_6
echo [INFO] 5/7: %PICK_5_DESC%
git cherry-pick %PICK_5%
if errorlevel 1 ( call :conflict_help 5 "%PICK_5%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 5

:do_pick_6
if %PICKS_DONE% geq 6 goto do_pick_7
echo [INFO] 6/7: %PICK_6_DESC%
git cherry-pick %PICK_6%
if errorlevel 1 ( call :conflict_help 6 "%PICK_6%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 6

:do_pick_7
if %PICKS_DONE% geq 7 goto build
echo [INFO] 7/7: %PICK_7_DESC%
git cherry-pick %PICK_7%
if errorlevel 1 ( call :conflict_help 7 "%PICK_7%" & exit /b 1 )
> "%PROGRESS_FILE%" echo 7

echo.
echo  All 7 cherry-picks applied cleanly.
echo.

:: ============================================================
:: BUILD
:: ============================================================

:build
cd /d "%LLAMA_DIR%"

if exist build rmdir /s /q build
echo.
echo [INFO] Setting up MSVC environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo.
echo [INFO] Configuring with Ninja (CUDA sm_86-real)...
cmake -B build -G "Ninja" ^
    -DGGML_CUDA=ON ^
    -DCMAKE_CUDA_ARCHITECTURES=86-real ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler ^
    -DCMAKE_C_FLAGS=/D_USE_MATH_DEFINES ^
    -DCMAKE_CXX_FLAGS=/D_USE_MATH_DEFINES ^
    -DCMAKE_ASM_COMPILER=cl.exe
if errorlevel 1 goto err_cmake

echo.
echo [INFO] Building (this takes several minutes)...
cmake --build build
if errorlevel 1 goto err_build

echo.
echo ============================================================
echo  Verifying both features in binary:
echo ============================================================
echo.
echo  --- MTP flags (look for spec, mtp, draft) ---
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "spec mtp draft"
echo.
echo  --- TurboQuant flags (look for turbo in cache types) ---
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "turbo"
echo.
echo ============================================================
echo  Build complete.
echo  Binary: %LLAMA_DIR%\build\bin\llama-server.exe
echo.
echo  If BOTH lines above have output: run start_combined.bat
echo  If MTP line is empty:    cherry-picks didn't compile in.
echo  If TurboQuant line empty: TurboQuant base missing — reclone.
echo ============================================================
echo.
pause
exit /b 0

:: ============================================================
:: SUBROUTINES
:: ============================================================

:conflict_help
echo.
echo ============================================================
echo  CONFLICT at commit %1/7: %~2
echo ============================================================
echo.
echo  In a second terminal:
echo    cd %LLAMA_DIR%
echo    git status              ^(conflicted files marked with ^<^<^<^<^<^<^<^)
echo    ^(edit each conflicted file to merge both sets of changes^)
echo    git add ^<resolved-files^>
echo    git cherry-pick --continue
echo.
echo  Then re-run this script — progress is at commit %1, it will
echo  skip commits 1 through %1 and continue from the next one.
echo.
echo  To abort all cherry-picks and start over:
echo    cd %LLAMA_DIR%
echo    git cherry-pick --abort
echo    del .picks_progress
echo.
pause
goto :eof

:err_clone
echo.
echo [ERROR] Clone failed.
echo         Ensure turbo3-cuda exists locally or internet access is available.
pause & exit /b 1

:err_fetch
echo.
echo [ERROR] Fetch failed from am17an remote.
echo         Check internet connection. Repo: %MTP_REMOTE%
echo         Branch: %MTP_BRANCH%
pause & exit /b 1

:err_cmake
echo.
echo [ERROR] CMake configuration failed.
echo  CUDA: %CUDA_BIN%
echo  MSVC: vcvars64.bat must have run without errors above.
pause & exit /b 1

:err_build
echo.
echo [ERROR] Build failed.
echo  Common causes after cherry-pick:
echo    - Conflict not fully resolved (missing symbol or misplaced code)
echo    - CUDA arch mismatch
echo  Check the error lines above — they point to the file and line.
pause & exit /b 1
