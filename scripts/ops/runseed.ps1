# CROWN local-only fictional Heritage reset. Requires explicit school ID and opt-in.
param(
    [Parameter(Mandatory=$true)][string]$HeritageSchoolId,
    [switch]$ConfirmDemoWipe
)
$ErrorActionPreference = "Stop"
if (-not $ConfirmDemoWipe) { throw "Explicit -ConfirmDemoWipe switch is required" }
if ($env:CROWN_ENV -notin @("local", "test")) { throw "CROWN_ENV must be local or test" }
if ($env:CROWN_ALLOW_DEMO_WIPE -ne "true") { throw "CROWN_ALLOW_DEMO_WIPE=true is required" }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backend = Join-Path $repoRoot "backend"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
Push-Location $backend
try {
    & $python manage.py seed_demo_school --wipe --confirm-demo-wipe --school-id $HeritageSchoolId --students 300 --tuition 12000 --aid_pct 35
    if ($LASTEXITCODE -ne 0) { throw "Local Heritage seeding failed" }
} finally { Pop-Location }
