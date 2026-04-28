$ErrorActionPreference = "Continue"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = "audit-artifacts\runtime-reachability-proof\$Stamp"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$BackendBase = $env:CROWN_BACKEND_URL
if (-not $BackendBase) { $BackendBase = "http://127.0.0.1:8000" }

$FrontendBase = $env:CROWN_FRONTEND_URL
if (-not $FrontendBase) { $FrontendBase = "http://127.0.0.1:5173" }

"BACKEND=$BackendBase" | Set-Content -Encoding UTF8 "$OutDir\00_targets.txt"
"FRONTEND=$FrontendBase" | Add-Content "$OutDir\00_targets.txt"

try {
    Invoke-RestMethod -Uri "$BackendBase/api/health/" -Method Get -TimeoutSec 20 |
        ConvertTo-Json -Depth 10 |
        Set-Content -Encoding UTF8 "$OutDir\10_backend_health.json"

    "backend_health:true" | Set-Content -Encoding UTF8 "$OutDir\11_backend_health_status.txt"
} catch {
    $_ | Out-String | Set-Content -Encoding UTF8 "$OutDir\10_backend_health_error.txt"
    "backend_health:false" | Set-Content -Encoding UTF8 "$OutDir\11_backend_health_status.txt"
}

try {
    $r = Invoke-WebRequest -Uri $FrontendBase -Method Get -TimeoutSec 20

    [PSCustomObject]@{
        statusCode = $r.StatusCode
        statusDescription = $r.StatusDescription
        contentLength = $r.Content.Length
    } | ConvertTo-Json -Depth 10 |
        Set-Content -Encoding UTF8 "$OutDir\20_frontend_reachability.json"

    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
        "frontend_reachable:true" | Set-Content -Encoding UTF8 "$OutDir\21_frontend_status.txt"
    } else {
        "frontend_reachable:false" | Set-Content -Encoding UTF8 "$OutDir\21_frontend_status.txt"
    }
} catch {
    $_ | Out-String | Set-Content -Encoding UTF8 "$OutDir\20_frontend_reachability_error.txt"
    "frontend_reachable:false" | Set-Content -Encoding UTF8 "$OutDir\21_frontend_status.txt"
}

Get-Content "$OutDir\11_backend_health_status.txt"
Get-Content "$OutDir\21_frontend_status.txt"
Write-Host "Artifact directory:$OutDir"
