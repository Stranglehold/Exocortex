@echo off

echo ============================================================
echo  MTP build  ^| am17an/llama.cpp mtp-clean  ^| RTX 3090
echo ============================================================
echo.

set CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin
set PATH=%PATH%;%CUDA_BIN%
set LLAMA_DIR=%~dp0llama-cpp-mtp

if exist "%LLAMA_DIR%\.git" goto update
echo [INFO] Cloning am17an/llama.cpp branch mtp-clean...
git clone https://github.com/am17an/llama.cpp.git -b mtp-clean "%LLAMA_DIR%"
if errorlevel 1 goto err_clone
goto build

:update
echo [INFO] Pulling latest mtp-clean...
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
cmake -B build -G "Ninja" -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86-real -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler -DCMAKE_C_FLAGS=/D_USE_MATH_DEFINES -DCMAKE_CXX_FLAGS=/D_USE_MATH_DEFINES
if errorlevel 1 goto err_cmake

echo.
echo [INFO] Building...
cmake --build build
if errorlevel 1 goto err_build

echo.
echo [INFO] Verifying MTP support in binary...
"%LLAMA_DIR%\build\bin\llama-server.exe" --help 2>&1 | findstr /i "spec mtp draft"
echo.
echo ============================================================
echo  Build complete.
echo  Binary: %LLAMA_DIR%\build\bin\llama-server.exe
echo  Run start_mtp.bat to launch.
echo  If --help shows no spec/mtp/draft flags, MTP did not build.
echo ============================================================
echo.
pause
exit /b 0

:err_clone
echo [ERROR] Clone failed. Check network and that the mtp-clean branch exists.
pause & exit /b 1

:err_cmake
echo [ERROR] CMake configuration failed.
echo  CUDA: %CUDA_BIN%
pause & exit /b 1

:err_build
echo [ERROR] Build failed. See output above.
echo  Common issue: MTP PR has merge conflicts with main — check PR discussion.
pause & exit /b 1
