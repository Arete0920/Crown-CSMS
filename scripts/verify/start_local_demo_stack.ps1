$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "==> Django check"
python manage.py check

Write-Host "==> Django migrate"
python manage.py migrate

$helpText = python manage.py help 2>&1 | Out-String
if ($helpText -match "load_heritage_demo") {
    Write-Host "==> Loading Heritage demo data"
    python manage.py load_heritage_demo --reset-passwords
} else {
    Write-Host "==> load_heritage_demo command not found. Skipping demo seed." -ForegroundColor Yellow
}

Write-Host "==> Starting backend on :8000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$repoRoot'; python manage.py runserver 8000"
)

Write-Host "==> Starting frontend on :3000"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:VITE_API_BASE='http://127.0.0.1:8000'; `$env:VITE_DEMO_MODE='1'; Set-Location '$repoRoot\frontend\dashboards'; npm install; npm run dev"
)

Start-Sleep -Seconds 8
Start-Process "http://localhost:3000/login"

Write-Host ""
Write-Host "Local stack started."
Write-Host "Default demo login: playwright@crown-demo.local / PlaywrightDemo1!"