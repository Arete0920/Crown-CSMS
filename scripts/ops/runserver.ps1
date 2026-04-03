# Crown2026 - Run Django server (stable mode)
Set-Location "$PSScriptRoot\backend"

if (!(Test-Path ".\venv\Scripts\python.exe")) {
  Write-Host "ERROR: venv not found at backend\venv. Create it first." -ForegroundColor Red
  exit 1
}

$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONUNBUFFERED="1"
# Dev toggle: set to 1 only when you intentionally want open endpoints
# $env:CROWN_DEV_OPEN_API="1"

Write-Host "Starting Django server (no reload) on http://127.0.0.1:8000 ..." -ForegroundColor Green
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
