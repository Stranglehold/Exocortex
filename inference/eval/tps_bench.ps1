param(
    [int]$Port = 1235,
    [string]$OutFile = ""
)

$body = '{"model":"local","messages":[{"role":"user","content":"Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests."}],"max_tokens":500,"stream":false}'

Write-Host ""
Write-Host "  Running TPS benchmark against port $Port ..."
Write-Host "  (merge sort, 500 tokens)"
Write-Host ""

try {
    $r = Invoke-RestMethod `
        -Uri "http://localhost:$Port/v1/chat/completions" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 300

    $t = $r.timings

    Write-Host ("  Prompt tokens : " + $t.prompt_n)
    Write-Host ("  Prefill tok/s : " + [math]::Round($t.prompt_per_second, 2))
    Write-Host ("  Decode tok/s  : " + [math]::Round($t.predicted_per_second, 2))
    Write-Host ("  Wall time (s) : " + [math]::Round($t.predicted_ms / 1000, 2))

    if ($t.draft_n -and $t.draft_n -gt 0) {
        $acc = [math]::Round($t.draft_n_accepted / $t.draft_n * 100, 1)
        Write-Host ("  Acceptance    : " + $t.draft_n_accepted + "/" + $t.draft_n + " (" + $acc + "%)")
    }

    if ($OutFile -ne "") {
        $r | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $OutFile
        Write-Host ""
        Write-Host "  Saved to: $OutFile"
    }
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)"
    exit 1
}
