# CROWN Environment Configuration
$ErrorActionPreference = 'Stop'

$CROWN_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PY = Join-Path $CROWN_ROOT '.venv\Scripts\python.exe'
if (-not (Test-Path $PY)) { throw "Python virtual environment not found at $PY" }

$API = 'http://127.0.0.1:8000'
$SCHOOL_ID = 'a5351136-98fe-4d48-add0-fa8f62d9ceff'
$USERNAME = 'head@crown-demo.local'
if (-not $env:CROWN_PASSWORD) {
    throw 'CROWN_PASSWORD is not set. Supply an approved development value through the environment.'
}
$env:DJANGO_SETTINGS_MODULE = 'crown_api.settings'
Write-Host 'CROWN environment ready' -ForegroundColor Green
