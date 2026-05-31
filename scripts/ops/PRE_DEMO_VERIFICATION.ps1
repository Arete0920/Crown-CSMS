# 60-Second Pre-Demo Verification
# Run this 5–10 minutes before the investor call

$ErrorActionPreference = "Stop"

Write-Host "=== PRE-DEMO CHECK ===" -ForegroundColor Cyan

git fetch origin --tags 2>&1 | Out-Null

$expected = "aec71930dffba0e1d186e49468ff67f77df5ead9"
$tag = (git rev-parse demo-feb16-gradebook-edit-pp-003).Trim()

Write-Host "Tag SHA: $tag"
if ($tag -ne $expected) { throw "Tag mismatch — STOP." }

git checkout demo-feb16-gradebook-edit-pp-003 2>&1 | Out-Null

Write-Host "Launching demo boot..." -ForegroundColor Cyan
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\tools\dev_scripts\demo_boot_feb16.ps1 -APITimeout 30

Write-Host "`n✓ Environment verified and booted." -ForegroundColor Green
