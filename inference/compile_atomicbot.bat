@echo off

echo ============================================================
echo  AtomicBot build  ^| MTP + TurboQuant  ^| RTX 3090
echo ============================================================
echo.
echo  Repo: AtomicBot-ai/atomic-llama-cpp-turboquant
echo  Goal: single binary with --spec-type mtp AND -ctk turbo4
echo.

set CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin
set PATH=%PATH%;%CUDA_BIN%
set LLAMA_DIR=%~dp0llama-cpp-atomicbot
set REPO_URL=https://github.com/AtomicBot-ai/atomic-llama-cpp-turboquant
set REPO_BRANCH=feature/turboquant-kv-cache

if exist "%LLAMA_DIR%\.git" goto update
echo [INFO] Cloning AtomicBot-ai/atomic-llama-cpp-turboquant...
echo        Branch: %REPO_BRANCH%
echo.
git clone %REPO_URL% -b %REPO_BRANCH% "%LLAMA_DIR%"
if errorlevel 1 goto err_clone
goto build

:update
echo [INFO] Pulling latest %REPO_BRANCH%...
cd /d "%LLAMA_DIR%"
git pull
cd /d "%~dp0"

:build
cd /d "%LLAMA_DIR%"
if exist build rmdir /s /q build
echo.
echo [INFO] Setting up MSVC environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo.
echo [INFO] Configuring with Ninja (CUDA arch sm_86-real)...
cmake -B build -G "Ninja" -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86-real -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler -DCMAKE_C_FLAGS=/D_USE_MATH_DEFINES -DCMAKE_CXX_FLAGS=/D_USE_MATH_DEFINES -DCMAKE_ASM_COMPILER=cl.exe
if errorlevel 1 goto err_cmake

echo.
echo [INFO] Building...
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
echo  --- TurboQuant flags (look for turbo in allowed cache types) ---
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "turbo"
echo.
echo ============================================================
echo  Build complete.
echo  Binary: %LLAMA_DIR%\build\bin\llama-server.exe
echo.
echo  If MTP line shows nothing: MTP not compiled in.
echo  If TurboQuant line shows nothing: turbo KV types not compiled in.
echo  Either missing = move to Option C (cherry-pick into Madreag).
echo.
echo  If both lines have output: run start_atomicbot.bat
echo ============================================================
echo.
pause
exit /b 0

:err_clone
echo.
echo [ERROR] Clone failed.
echo.
echo  Tried: %REPO_URL% branch %REPO_BRANCH%
echo.
echo  If the branch name is wrong, check the repo manually for the correct branch.
echo  If repo is private or gone, move to Option C (cherry-pick into Madreag).
echo.
pause & exit /b 1

:err_cmake
echo [ERROR] CMake configuration failed.
echo  CUDA: %CUDA_BIN%
pause & exit /b 1

:err_build
echo [ERROR] Build failed. See output above.
echo  If the error mentions MTP or turboquant conflicts, move to Option C.
pause & exit /b 1
