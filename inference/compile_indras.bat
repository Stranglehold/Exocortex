@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  Indras-Mirror build  ^| MTP + TBQ4 fused FA  ^| RTX 3090
echo ============================================================
echo.
echo  Ref: team-comms/opus-to-kestrel/indras_mirror_fused_build_brief_20260514.md
echo  Key claim: 200K ctx at 97 tok/s (4090) ~65-80 tok/s expected on 3090
echo  Fused: MTP + TurboQuant TBQ4 KV inside flash-attn CUDA kernel + shared tensors
echo.

set CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin
set PATH=%PATH%;%CUDA_BIN%
set LLAMA_DIR=%~dp0llama-cpp-indras

if exist "%LLAMA_DIR%\.git" goto update
echo [INFO] Cloning Indras-Mirror/llama.cpp-mtp...
git clone https://github.com/Indras-Mirror/llama.cpp-mtp.git "%LLAMA_DIR%"
if errorlevel 1 goto err_clone
goto build

:update
echo [INFO] Pulling latest...
cd /d "%LLAMA_DIR%"
git pull
cd /d "%~dp0"

:build
cd /d "%LLAMA_DIR%"

:: ============================================================
:: CACHE REUSE BUG CHECK (Issue #22384)
:: ============================================================
:: The am17an build had a checkpoint search bug (pos_min) in server-context.cpp
:: that caused every turn to re-process the full context instead of using the
:: cached prefix. The fix was two lines in common/chat.cpp and/or src/llama.cpp.
:: Indras-Mirror is based on upstream + PR #22673 — the same bug may exist.
:: After build, run verify_cache_fix.ps1 to check. If Turn 2 still shows
:: full prefill (not delta), apply the same patch from the am17an build.
:: ============================================================
echo.
echo [WARN] After build, verify cache reuse with verify_cache_fix.ps1
echo        If Turn2 TTFT equals Turn1 TTFT, the cache bug is present.
echo        Apply the am17an patch from: eval/CACHE_REUSE_FIX_VALIDATION.md
echo.

if exist build rmdir /s /q build

echo [INFO] Setting up MSVC environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo.

echo [INFO] Configuring with Ninja (CUDA arch sm_86-real)...
echo [WARN] sm_86 = Ampere (RTX 3090). Fork developed on sm_89 (Ada/4090).
echo        If TBQ4 fused FA kernel uses Ada-only intrinsics, build may fail
echo        or binary may crash at runtime. If so, check Issues tab on GitHub.
echo.
cmake -B build -G "Ninja" ^
    -DGGML_CUDA=ON ^
    -DCMAKE_CUDA_ARCHITECTURES=86-real ^
    -DCMAKE_BUILD_TYPE=Release ^
    "-DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler" ^
    -DCMAKE_C_FLAGS=/D_USE_MATH_DEFINES ^
    -DCMAKE_CXX_FLAGS=/D_USE_MATH_DEFINES
if errorlevel 1 goto err_cmake

echo.
echo [INFO] Building (this takes 5-10 min)...
cmake --build build
if errorlevel 1 goto err_build

echo.
echo [INFO] Verifying MTP and turbo KV support in binary...
echo --- MTP flags (should show spec/draft): ---
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "spec draft"
echo --- TurboQuant KV types (should show tbq4_0): ---
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "tbq"
echo.
echo ============================================================
echo  Build complete.
echo  Binary: %LLAMA_DIR%\build\bin\llama-server.exe
echo  Next: run start_indras.bat to launch the server
echo  Then: run eval/INDRAS_BUILD_VALIDATION.md test protocol
echo ============================================================
echo.
pause
exit /b 0

:err_clone
echo [ERROR] Clone failed.
echo         Check: https://github.com/Indras-Mirror/llama.cpp-mtp exists
pause & exit /b 1

:err_cmake
echo [ERROR] CMake configuration failed.
echo  CUDA: %CUDA_BIN%
echo  Possible cause: TBQ4 FA kernel may require CUDA features not in 12.8.
pause & exit /b 1

:err_build
echo [ERROR] Build failed. See output above.
echo  If sm_86 incompatibility, check: https://github.com/Indras-Mirror/llama.cpp-mtp/issues
pause & exit /b 1
