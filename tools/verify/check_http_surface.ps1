param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$out = Join-Path $RepoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$healthCandidates = @(
    "$BaseUrl/api/health/",
    "$BaseUrl/api/system/health/"
)

$healthOk = $false
$healthFile = Join-Path $out "http-health-check.txt"
"" | Set-Content $healthFile

foreach ($url in $healthCandidates) {
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 15
        "PASS $url" | Add-Content $healthFile
        ($resp | ConvertTo-Json -Depth 20) | Add-Content $healthFile
        $healthOk = $true
        break
    } catch {
        "FAIL $url" | Add-Content $healthFile
        ($_ | Out-String) | Add-Content $healthFile
    }
}

if (-not $healthOk) {
    throw "No health endpoint responded successfully. See artifacts\wiring-proof\http-health-check.txt"
}

$docsTargets = @(
    "$BaseUrl/api/docs/",
    "$BaseUrl/api/schema/"
)

$docsFile = Join-Path $out "http-docs-check.txt"
"" | Set-Content $docsFile

foreach ($url in $docsTargets) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        "PASS $url => HTTP $($resp.StatusCode)" | Add-Content $docsFile
    } catch {
        "FAIL $url" | Add-Content $docsFile
        ($_ | Out-String) | Add-Content $docsFile
        throw "HTTP docs surface failed for $url"
    }
}

Write-Host "PASS: HTTP health/docs surface check clean." -ForegroundColor Green
exit 0