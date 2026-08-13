$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at $python"
}

Set-Location $backendDir
$env:DJANGO_SETTINGS_MODULE = 'crown_api.settings'
& $python manage.py runserver 127.0.0.1:8000 --noreload
