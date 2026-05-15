# Exocortex Inference Wrapper - CUDA Setup Script (v3)
# Run once from an Administrator PowerShell to enable GPU inference.
#
# v3 fix: Sources vcvarsall.bat to set up full MSVC environment
# before building. This ensures Ninja can find cl.exe.
#
# Usage (from Admin PowerShell):
#   cd D:\Vibecode\Agent-Zero\Exocortex\inference
#   .\setup_cuda.ps1

Write-Host "=== Exocortex Inference Wrapper: CUDA Setup (v3) ===" -ForegroundColor Cyan

# Step 1: Verify CUDA toolkit exists
Write-Host "`n[1/4] Verifying CUDA 12.8 installation..." -ForegroundColor Yellow

$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$nvcc = Join-Path $cudaPath "bin\nvcc.exe"

if (-not (Test-Path $nvcc)) {
    Write-Host "ERROR: nvcc not found at: $nvcc" -ForegroundColor Red
    Write-Host "Ensure CUDA Toolkit 12.8 is installed." -ForegroundColor Red
    exit 1
}

Write-Host "   CUDA 12.8 found." -ForegroundColor Green

# Step 2: Find and source MSVC environment
Write-Host "`n[2/4] Setting up MSVC build environment..." -ForegroundColor Yellow

# Try multiple known VS locations (VS 2026/18, VS 2022/17)
$vcvarsall = $null
$candidates = @(
    "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
    "C:\Program Files\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
)

foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
        $vcvarsall = $candidate
        break
    }
}

# Fallback: try vswhere if none of the known paths worked
if (-not $vcvarsall) {
    $vsWhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vsWhere) {
        $vsInstallPath = & $vsWhere -latest -property installationPath
        if ($vsInstallPath) {
            $test = Join-Path $vsInstallPath "VC\Auxiliary\Build\vcvarsall.bat"
            if (Test-Path $test) { $vcvarsall = $test }
        }
    }
}

if (-not $vcvarsall) {
    Write-Host "ERROR: Could not find vcvarsall.bat in any known location." -ForegroundColor Red
    Write-Host "Searched:" -ForegroundColor Yellow
    foreach ($c in $candidates) { Write-Host "  $c" -ForegroundColor Gray }
    exit 1
}

# Source vcvarsall.bat and import all environment variables into PowerShell
Write-Host "   Sourcing vcvarsall.bat x64..." -ForegroundColor Gray
$envBefore = @{}
cmd /c "`"$vcvarsall`" x64 >nul 2>&1 && set" | ForEach-Object {
    if ($_ -match "^([^=]+)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Verify cl.exe is now findable
$clCheck = Get-Command cl.exe -ErrorAction SilentlyContinue
if ($clCheck) {
    Write-Host "   MSVC environment ready. cl.exe at: $($clCheck.Source)" -ForegroundColor Green
} else {
    Write-Host "ERROR: cl.exe still not found after sourcing vcvarsall.bat" -ForegroundColor Red
    exit 1
}

# Step 3: Install Ninja and uninstall old llama-cpp-python
Write-Host "`n[3/4] Preparing build tools..." -ForegroundColor Yellow

& "C:\Users\Jake\miniconda3\python.exe" -m pip install ninja cmake --quiet 2>&1 | Out-Null

# Uninstall existing (ignore errors if not installed)
& "C:\Users\Jake\miniconda3\python.exe" -m pip uninstall llama-cpp-python -y 2>&1 | Out-Null
Write-Host "   Ready." -ForegroundColor Green

# Step 4: Build with CUDA using Ninja generator
Write-Host "`n[4/4] Building llama-cpp-python with CUDA 12.8 (Ninja + MSVC)..." -ForegroundColor Yellow
Write-Host "   This takes 5-10 minutes. Coffee time." -ForegroundColor Gray

$env:CMAKE_GENERATOR = "Ninja"
$env:CMAKE_ARGS = "-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler"
$env:CUDACXX = $nvcc
$env:CUDA_PATH = $cudaPath

& "C:\Users\Jake\miniconda3\python.exe" -m pip install llama-cpp-python --no-binary llama-cpp-python --no-cache-dir --force-reinstall

if ($LASTEXITCODE -eq 0) {
    $gpuCheck = & "C:\Users\Jake\miniconda3\python.exe" -c "from llama_cpp import llama_supports_gpu_offload; print(llama_supports_gpu_offload())"
    Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan

    if ($gpuCheck -eq "True") {
        Write-Host "GPU offload supported: True" -ForegroundColor Green
        Write-Host "`nReady to run:" -ForegroundColor Green
        Write-Host "  C:\Users\Jake\miniconda3\python.exe inference_wrapper.py" -ForegroundColor White
    } else {
        Write-Host "GPU offload: False (build succeeded but CUDA may not have linked)" -ForegroundColor Red
    }
} else {
    Write-Host "`nBuild failed." -ForegroundColor Red
    Write-Host "Try running from Developer PowerShell for VS instead:" -ForegroundColor Yellow
    Write-Host "  Start Menu > Developer PowerShell for VS 2022 (or 2026)" -ForegroundColor White
    Write-Host "  Then re-run this script from there." -ForegroundColor White
}

# Clean up
Remove-Item env:CMAKE_GENERATOR -ErrorAction SilentlyContinue
Remove-Item env:CMAKE_ARGS -ErrorAction SilentlyContinue
Remove-Item env:CUDACXX -ErrorAction SilentlyContinue
