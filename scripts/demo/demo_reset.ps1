#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$REPO = "$env:USERPROFILE\OneDrive\Desktop\Crown2026"

if (-not $env:CROWN_DEMO_PASSWORD) {
    throw "CROWN_DEMO_PASSWORD is required."
}
if (-not $env:CROWN_DEMO_KEY) {
    throw "CROWN_DEMO_KEY is required."
}

Write-Host "`n=== DEMO AUTH RESET ===" -ForegroundColor Cyan
Write-Host "Resetting configured demo-user credentials without printing secret values.`n"

Set-Location "$REPO\backend"
python manage.py reset_demo_passwords
if ($LASTEXITCODE -ne 0) {
    throw "reset_demo_passwords failed."
}

Write-Host ""
Write-Host "=== DEMO AUTH RESET COMPLETE ===" -ForegroundColor Green
Write-Host "CROWN_DEMO_MODE must be enabled only in an approved non-production runtime."
Write-Host "CROWN_DEMO_PASSWORD and CROWN_DEMO_KEY were supplied through the environment."
Write-Host "Restart the backend after changing environment values."
Write-Host "================================" -ForegroundColor Green
