$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr"
Set-Location $Root

$Out = "$Root\crown-master-binder\06_release_readiness"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

$Log = Join-Path $Out "backend_pytest_full_gate_$(Get-Date -Format yyyyMMdd_HHmmss).txt"
$PytestLog = Join-Path $Out "backend_pytest_full_gate_raw_$(Get-Date -Format yyyyMMdd_HHmmss).txt"

Set-Location "$Root\backend"

$env:DJANGO_SECRET_KEY = "ci-not-secret"
$env:SECRET_KEY = "ci-not-secret"
$env:DATABASE_URL = "sqlite:///./ci.sqlite3"
$env:DJANGO_DEBUG = "0"
$env:DJANGO_ENV = "test"
$env:CROWN_ENV = "test"

"UTC=$((Get-Date).ToUniversalTime().ToString('o'))" | Out-File $Log -Encoding utf8
"BRANCH=$(git branch --show-current)" | Add-Content $Log
"HEAD=$(git rev-parse HEAD)" | Add-Content $Log
"========================================" | Add-Content $Log

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { $VenvPython = "python" }
& $VenvPython -m pytest -q --tb=short 2>&1 | Out-File -FilePath $PytestLog -Encoding utf8
$Code = $LASTEXITCODE

if (Test-Path $PytestLog) {
    Get-Content $PytestLog | Add-Content $Log
}

"========================================" | Add-Content $Log
"EXIT_CODE=$Code" | Add-Content $Log

Set-Location $Root

if ($Code -ne 0) {
    Write-Host "BACKEND_GATE=FAIL"
    Write-Host "LOG=$Log"
    exit $Code
}

Write-Host "BACKEND_GATE=PASS"
Write-Host "LOG=$Log"
