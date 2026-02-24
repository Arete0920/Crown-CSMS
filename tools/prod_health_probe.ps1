param(
  [string]$Url = $env:CROWN_PROD_HEALTH_URL
)

$ErrorActionPreference = "Stop"

if (-not $Url) {
  throw "Missing URL. Set `$env:CROWN_PROD_HEALTH_URL or pass -Url https://.../health/"
}

Write-Host "Probing: $Url" -ForegroundColor Cyan

try {
  $resp = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 20
} catch {
  Write-Host "FAILED: health endpoint not reachable" -ForegroundColor Red
  throw
}

$json = $resp | ConvertTo-Json -Depth 6
Write-Host "Health JSON:" -ForegroundColor Cyan
Write-Host $json

$sha = $resp.build_sha
if (-not $sha) { $sha = $resp.sha }
if (-not $sha) { $sha = $resp.version }

if (-not $sha) {
  throw "Health response missing build SHA field (build_sha/sha/version not found)."
}

Write-Host "OK: build SHA => $sha" -ForegroundColor Green
