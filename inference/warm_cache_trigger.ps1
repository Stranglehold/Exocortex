# warm_cache_trigger.ps1
# Polls for MTP server health, then triggers KV cache warm-up inside exocortex_v16.
# Called by start_mtp.bat in a minimized background window before server launch.
# Server health check runs while the main window starts llama-server.

param(
    [int]$Port = 1235,
    [int]$MaxWaitSec = 360,   # 6 min max wait for server to start
    [string]$Container = "exocortex_v16",
    [string]$ScriptPath = "/a0/usr/Exocortex/inference/warm_cache.py"
)

$url = "http://localhost:$Port/health"
$sw = [Diagnostics.Stopwatch]::StartNew()

Write-Host "[CACHE-WARM-TRIGGER] Waiting for MTP server at $url (max ${MaxWaitSec}s)..."

$ready = $false
while ($sw.Elapsed.TotalSeconds -lt $MaxWaitSec) {
    try {
        $r = Invoke-WebRequest $url -TimeoutSec 3 -UseBasicParsing 2>$null
        if ($r.Content -match '"status":"ok"') {
            $ready = $true
            break
        }
    } catch {}
    Start-Sleep 5
}

if (-not $ready) {
    Write-Host "[CACHE-WARM-TRIGGER] Server did not become healthy within ${MaxWaitSec}s. Skipping warm-up."
    exit 1
}

Write-Host "[CACHE-WARM-TRIGGER] Server healthy. Checking if $Container is running..."

$running = docker inspect $Container --format "{{.State.Running}}" 2>$null
if ($running -ne "true") {
    Write-Host "[CACHE-WARM-TRIGGER] Container '$Container' not running. Warm-up skipped."
    Write-Host "  The _71_cache_warmer.py extension handles the fallback at Turn 1."
    exit 0
}

Write-Host "[CACHE-WARM-TRIGGER] Launching warm-up in $Container..."
docker exec -d $Container python3 $ScriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "[CACHE-WARM-TRIGGER] Warm-up started. Takes 3-5 min. This window will close."
} else {
    Write-Host "[CACHE-WARM-TRIGGER] docker exec failed (exit $LASTEXITCODE). Check that warm_cache.py is deployed."
}
