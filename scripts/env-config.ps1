# Crown2026 Environment Configuration
$ErrorActionPreference = 'Stop'
$CROWN_ROOT = 'C:\Users\JMega\OneDrive\Desktop\Crown2026'
$PY = "$CROWN_ROOT\.venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { throw "Python venv not found" }
$API = 'http://127.0.0.1:8000'
$SCHOOL_ID = 'a5351136-98fe-4d48-add0-fa8f62d9ceff'
$USERNAME = 'head@crown-demo.local'
if (-not $env:CROWN_PASSWORD) { $env:CROWN_PASSWORD = 'demo1234' }
$env:DJANGO_SETTINGS_MODULE = 'crown_api.settings'
Write-Host 'Crown env ready' -ForegroundColor Green
