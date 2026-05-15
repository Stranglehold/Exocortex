# gpu_proxy.ps1
# Tiny HTTP server that serves nvidia-smi metrics as JSON on /api/gpu
# Used by dashboard.html when llama-server doesn't expose GPU data.
#
# Run alongside start_mtp.bat in a separate terminal window:
#   powershell -ExecutionPolicy Bypass -File gpu_proxy.ps1
#
# Dashboard settings: change Server URL to point at this proxy's port,
# OR update the dashboard's /api/gpu fetch URL to this port directly.
#
# Default: listens on http://localhost:1237/api/gpu

param(
    [int]$Port = 1237,
    [int]$PollIntervalSec = 3
)

$url = "http://localhost:$Port/"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($url)

try {
    $listener.Start()
} catch {
    Write-Host "[gpu_proxy] Failed to start listener on $url" -ForegroundColor Red
    Write-Host "[gpu_proxy] Try running as Administrator, or use a different port." -ForegroundColor Yellow
    exit 1
}

Write-Host "[gpu_proxy] Listening on $url" -ForegroundColor Cyan
Write-Host "[gpu_proxy] Serving nvidia-smi metrics at ${url}api/gpu" -ForegroundColor Cyan
Write-Host "[gpu_proxy] Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

function Get-GpuMetrics {
    try {
        $raw = nvidia-smi --query-gpu=power.draw,memory.used,memory.total,memory.free,temperature.gpu --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }

        $parts = $raw.Trim() -split ',\s*'
        if ($parts.Count -lt 5) { return $null }

        $power = [double]$parts[0]
        $usedM = [double]$parts[1]
        $totM  = [double]$parts[2]
        $freeM = [double]$parts[3]
        $temp  = [double]$parts[4]

        return @{
            vram_used_mib  = $usedM
            vram_total_mib = $totM
            vram_free_mib  = $freeM
            power_draw_w   = $power
            temperature_c  = $temp
            timestamp_ms   = [long]([datetime]::UtcNow - [datetime]::new(1970,1,1)).TotalMilliseconds
        }
    } catch {
        return $null
    }
}

function ConvertTo-JsonSimple($obj) {
    if ($null -eq $obj) { return '{"error":"nvidia-smi unavailable"}' }
    $pairs = @()
    foreach ($key in $obj.Keys) {
        $val = $obj[$key]
        if ($val -is [long] -or $val -is [int]) {
            $pairs += '"' + $key + '":' + $val
        } else {
            $pairs += '"' + $key + '":' + ([string]$val)
        }
    }
    return '{' + ($pairs -join ',') + '}'
}

$corsHeaders = @{
    'Access-Control-Allow-Origin'  = '*'
    'Access-Control-Allow-Methods' = 'GET, OPTIONS'
    'Access-Control-Allow-Headers' = 'Content-Type'
}

while ($listener.IsListening) {
    try {
        $ctx  = $listener.GetContext()
        $req  = $ctx.Request
        $resp = $ctx.Response

        foreach ($h in $corsHeaders.GetEnumerator()) {
            $resp.Headers[$h.Key] = $h.Value
        }

        if ($req.HttpMethod -eq 'OPTIONS') {
            $resp.StatusCode = 204
            $resp.Close()
            continue
        }

        $path = $req.Url.AbsolutePath.TrimEnd('/')
        $body = ''

        if ($path -eq '/api/gpu') {
            $metrics = Get-GpuMetrics
            $body    = ConvertTo-JsonSimple $metrics
            $resp.ContentType   = 'application/json'
            $resp.StatusCode    = 200
        } elseif ($path -eq '/health') {
            $body = '{"status":"ok","service":"gpu_proxy"}'
            $resp.ContentType = 'application/json'
            $resp.StatusCode  = 200
        } else {
            $body = '{"error":"not found"}'
            $resp.ContentType = 'application/json'
            $resp.StatusCode  = 404
        }

        $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
        $resp.ContentLength64 = $bytes.Length
        $resp.OutputStream.Write($bytes, 0, $bytes.Length)
        $resp.Close()

        if ($path -eq '/api/gpu') {
            Write-Host ("[gpu_proxy] " + $req.RemoteEndPoint + " -> " + $path + " (" + $body.Length + " bytes)") -ForegroundColor DarkGray
        }

    } catch [System.Net.HttpListenerException] {
        break
    } catch {
        Write-Host "[gpu_proxy] Error: $_" -ForegroundColor Red
    }
}

$listener.Stop()
Write-Host "[gpu_proxy] Stopped." -ForegroundColor Gray
