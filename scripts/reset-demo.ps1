# DEV-only reset: credentials come from the operator environment, never source.
# Rotate any operations credential that was committed previously; removing it here
# does not invalidate copies in git history.
$ErrorActionPreference = "Stop"
$API = "https://crown-api-dev.azurewebsites.net"
$OPS = $env:CROWN_OPS_SECRET
$SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"

if ([string]::IsNullOrWhiteSpace($OPS)) {
    throw "Set CROWN_OPS_SECRET from the approved secret store before resetting the DEV demo."
}

Write-Host "Resetting DEV demo..." -ForegroundColor Cyan
$responseJson = curl.exe --max-time 30 -f -sS "$API/api/v1/system/demo-reset/?verbosity=1" `
    -X POST `
    -H "X-Admin-Ops-Secret: $OPS" `
    -H "X-School-Id: $SCHOOL_ID" `
    -H "Content-Type: application/json" `
    -d "{}"
if ($LASTEXITCODE -ne 0) {
    throw "DEV demo reset request failed (curl exit code $LASTEXITCODE)."
}
$response = $responseJson | ConvertFrom-Json
if ($response.ok -ne $true) {
    throw "DEV demo reset did not report success."
}
Write-Host "Demo reset complete" -ForegroundColor Green
Write-Host "   School: $($response.school_id)" -ForegroundColor Gray
Write-Host "   Environment: $($response.env)" -ForegroundColor Gray
