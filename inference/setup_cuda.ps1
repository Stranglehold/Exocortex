# Exocortex Inference Wrapper — CUDA Setup Script
# Run once from an Administrator PowerShell to enable GPU inference.
#
# This script:
#   1. Copies CUDA 12.8 MSBuild integration files to VS 2022 BuildTools
#   2. Builds and installs llama-cpp-python with CUDA support
#
# Usage (from Admin PowerShell):
#   cd D:\Vibecode\Agent-Zero\Exocortex\inference
#   .\setup_cuda.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Exocortex Inference Wrapper: CUDA Setup ===" -ForegroundColor Cyan

# Step 1: Copy CUDA VS integration files (requires admin)
Write-Host "`n[1/3] Copying CUDA 12.8 integration files to VS 2022 BuildTools..." -ForegroundColor Yellow

$cudaIntegration = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\extras\visual_studio_integration\MSBuildExtensions"
$vsCustomizations = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Microsoft\VC\v170\BuildCustomizations"

if (-not (Test-Path $cudaIntegration)) {
    Write-Error "CUDA 12.8 integration files not found at: $cudaIntegration"
    Write-Host "Ensure CUDA Toolkit 12.8 is installed." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $vsCustomizations)) {
    Write-Error "VS 2022 BuildTools not found at: $vsCustomizations"
    Write-Host "Ensure Visual Studio 2022 BuildTools with C++ workload is installed." -ForegroundColor Red
    exit 1
}

Copy-Item "$cudaIntegration\*" "$vsCustomizations" -Force
Write-Host "   CUDA integration files copied." -ForegroundColor Green

# Step 2: Uninstall CPU-only version
Write-Host "`n[2/3] Removing CPU-only llama-cpp-python..." -ForegroundColor Yellow
& "C:\Users\Jake\miniconda3\python.exe" -m pip uninstall llama-cpp-python -y
Write-Host "   Removed." -ForegroundColor Green

# Step 3: Build with CUDA support
Write-Host "`n[3/3] Building llama-cpp-python with CUDA 12.8 support..." -ForegroundColor Yellow
Write-Host "   This takes 5-10 minutes. Coffee time." -ForegroundColor Gray

$env:CMAKE_ARGS = "-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86"
# sm_86 = Ampere (RTX 3090). Add 89 for RTX 4090 if needed.

& "C:\Users\Jake\miniconda3\python.exe" -m pip install llama-cpp-python `
    --no-binary llama-cpp-python `
    --no-cache-dir

if ($LASTEXITCODE -eq 0) {
    # Verify GPU support
    $gpuCheck = & "C:\Users\Jake\miniconda3\python.exe" -c "from llama_cpp import llama_supports_gpu_offload; print(llama_supports_gpu_offload())"
    Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
    Write-Host "GPU offload supported: $gpuCheck" -ForegroundColor $(if ($gpuCheck -eq "True") { "Green" } else { "Red" })

    if ($gpuCheck -eq "True") {
        Write-Host "`nReady to run the inference wrapper:" -ForegroundColor Green
        Write-Host "  cd D:\Vibecode\Agent-Zero\Exocortex\inference" -ForegroundColor White
        Write-Host "  C:\Users\Jake\miniconda3\python.exe inference_wrapper.py" -ForegroundColor White
    } else {
        Write-Host "GPU support not detected. Check CUDA installation." -ForegroundColor Red
    }
} else {
    Write-Error "Build failed. Check error output above."
}
