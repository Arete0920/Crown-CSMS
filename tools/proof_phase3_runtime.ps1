param(
  [string]$BaseUrl   = ($env:CROWN_API_BASE_URL   ?? "http://127.0.0.1:8000/"),
  [string]$SchoolId  = ($env:CROWN_DEMO_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d"),
  [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

Write-Host "=== Phase 3 P2 Runtime Proof Ceremony ===" -ForegroundColor Cyan
Write-Host "BaseUrl:  $BaseUrl"
Write-Host "SchoolId: $SchoolId"
Write-Host ""
Write-Host "Requires: Django server running at $BaseUrl" -ForegroundColor Yellow
Write-Host "Note: CROWN_DEMO_MODE must be set to 'true' for the demo auth endpoint to work." -ForegroundColor Yellow
Write-Host ""

$python = Join-Path $repo ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
  Write-Error "venv not found at $python. Activate your venv first."
  exit 1
}

$manage = Join-Path $repo "backend\manage.py"

$args = @(
  $manage,
  "proof_phase3_runtime",
  "--base-url", $BaseUrl,
  "--school-id", $SchoolId
)

if ($Verbose) { $args += "--verbose" }

$env:CROWN_DEMO_MODE = "true"

& $python @args
if ($LASTEXITCODE -ne 0) {
  Write-Host "FAIL: Phase 3 runtime proof ceremony FAILED." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "PASS: Phase 3 runtime proof ceremony complete." -ForegroundColor Green


$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

Write-Host "=== Phase 3 P2 Runtime Proof Ceremony ===" -ForegroundColor Cyan
Write-Host "BaseUrl:  $BaseUrl"
Write-Host "SchoolId: $SchoolId"
Write-Host "AuthPath: $($env:CROWN_DEMO_AUTH_PATH ?? 'api/dev/token/')"
Write-Host ""
Write-Host "Requires: Django server running at $BaseUrl" -ForegroundColor Yellow
Write-Host ""

$python = Join-Path $repo ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
  Write-Error "venv not found at $python. Activate your venv first."
  exit 1
}

$manage = Join-Path $repo "backend\manage.py"

$args = @(
  $manage,
  "proof_phase3_runtime",
  "--base-url", $BaseUrl,
  "--school-id", $SchoolId,
  "--demo-key", $DemoKey
)

if ($Verbose) { $args += "--verbose" }

$env:CROWN_DEMO_MODE = "true"

& $python @args
if ($LASTEXITCODE -ne 0) {
  Write-Host "FAIL: Phase 3 runtime proof ceremony FAILED." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "PASS: Phase 3 runtime proof ceremony complete." -ForegroundColor Green
