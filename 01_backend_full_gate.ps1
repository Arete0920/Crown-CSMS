param(
    [string]$Root = "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr",
    [string]$RunStamp = $null,
    [switch]$Worker
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location $Root

$Out = "$Root\crown-master-binder\06_release_readiness"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

if (-not $RunStamp) {
    $RunStamp = Get-Date -Format yyyyMMdd_HHmmss
}

$Log = Join-Path $Out "backend_pytest_full_gate_$RunStamp.txt"
$PytestLog = Join-Path $Out "backend_pytest_full_gate_raw_$RunStamp.txt"
$PytestErrLog = Join-Path $Out "backend_pytest_full_gate_err_$RunStamp.txt"

if (-not $Worker) {
    $workerArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-Root", $Root,
        "-RunStamp", $RunStamp,
        "-Worker"
    )

    $workerProc = Start-Process -FilePath "powershell.exe" -ArgumentList $workerArgs -WindowStyle Hidden -Wait -PassThru
    Write-Host "LOG=$Log"
    exit $workerProc.ExitCode
}

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

"PYTEST_CMD=$VenvPython -m pytest -q --tb=short" | Add-Content $Log
"RAW_LOG=$PytestLog" | Add-Content $Log
"ERR_LOG=$PytestErrLog" | Add-Content $Log

$Proc = Start-Process -FilePath $VenvPython -ArgumentList @("-m", "pytest", "-q", "--tb=short") -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $PytestLog -RedirectStandardError $PytestErrLog
$Code = $Proc.ExitCode

if (Test-Path $PytestLog) {
    Get-Content $PytestLog | Add-Content $Log
}

if (Test-Path $PytestErrLog) {
    "========================================" | Add-Content $Log
    "STDERR" | Add-Content $Log
    Get-Content $PytestErrLog | Add-Content $Log
}

# Normalize and persist terminal gate status.
# This block must run after pytest completes and after raw/err paths are defined.
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) {
    $exitCode = $Code
}
if ($null -eq $exitCode) {
    $exitCode = -1
}

$rawText = ""
$errText = ""

if (Test-Path $PytestLog) {
    $rawText = Get-Content $PytestLog -Raw -ErrorAction SilentlyContinue
}
if (Test-Path $PytestErrLog) {
    $errText = Get-Content $PytestErrLog -Raw -ErrorAction SilentlyContinue
}

$combinedText = "$rawText`n$errText"

"`n========================================" | Add-Content $Log
"TERMINAL STATUS" | Add-Content $Log
"========================================" | Add-Content $Log
"EXIT_CODE=$exitCode" | Add-Content $Log

if ($combinedText -match "KeyboardInterrupt") {
    "INTERRUPTED=YES" | Add-Content $Log
    "INTERRUPT_SIGNAL=KeyboardInterrupt" | Add-Content $Log
} else {
    "INTERRUPTED=NO" | Add-Content $Log
}

if ($combinedText -match "Timeout|timed out|pytest-timeout") {
    "TIMEOUT_DETECTED=YES" | Add-Content $Log
} else {
    "TIMEOUT_DETECTED=NO" | Add-Content $Log
}

if ($exitCode -eq 0) {
    "BACKEND_GATE=PASS" | Add-Content $Log
} else {
    "BACKEND_GATE=FAIL" | Add-Content $Log
}

Set-Location $Root
Write-Host "LOG=$Log"
exit $exitCode
