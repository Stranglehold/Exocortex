# Verify KV cache reuse after hybrid model fix
# Run AFTER starting start_mtp.bat
# GOOD: second request shows cache_n >> 0 (cached tokens reused)
# BAD:  second request shows cache_n = 0 (still broken)

$port = 1235
$url  = "http://localhost:$port/v1/chat/completions"

$body = @{
    model      = "local"
    max_tokens = 5
    messages   = @(
        @{ role = "system"; content = "You are a helpful assistant." },
        @{ role = "user";   content = "Say the word 'hello' and nothing else." }
    )
} | ConvertTo-Json -Depth 5

function Send-Request {
    param($label)
    Write-Host ""
    Write-Host "[$label] Sending request..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 300
        $usage    = $response.usage
        $timings  = $response.timings
        Write-Host "  reply        : $($response.choices[0].message.content)"
        Write-Host "  prompt_tokens: $($usage.prompt_tokens)"
        if ($timings) {
            $cacheN  = if ($null -ne $timings.cache_n)               { $timings.cache_n }               else { "n/a" }
            $promptN = if ($null -ne $timings.prompt_n)              { $timings.prompt_n }              else { "n/a" }
            $ttft    = if ($null -ne $timings.time_to_first_token_ms) { "$($timings.time_to_first_token_ms) ms" } else { "n/a" }
            Write-Host "  cache_n      : $cacheN  (tokens served from KV cache)"
            Write-Host "  prompt_n     : $promptN  (tokens actually processed)"
            Write-Host "  TTFT         : $ttft"
            if ($label -eq "Request 1") {
                Write-Host "  (First request always processes full prompt - expected)" -ForegroundColor Yellow
            } elseif ($cacheN -ne "n/a" -and $cacheN -gt 0) {
                Write-Host "  [PASS] Cache reuse active" -ForegroundColor Green
            } else {
                Write-Host "  [FAIL] cache_n=0 on second request - fix not working" -ForegroundColor Red
            }
        } else {
            Write-Host "  (no timings field in response)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "============================================================"
Write-Host " KV Cache Reuse Verification -- MTP server port $port"
Write-Host " Watch server console for:"
Write-Host "   GOOD: 'restored context checkpoint'"
Write-Host "   BAD:  'forcing full prompt re-processing'"
Write-Host "============================================================"

Send-Request "Request 1"
Write-Host ""
Write-Host "Waiting 3 seconds..." -ForegroundColor Gray
Start-Sleep 3
Send-Request "Request 2"

Write-Host ""
Write-Host "============================================================"
Write-Host " Done. Check server console output to confirm."
Write-Host "============================================================"
