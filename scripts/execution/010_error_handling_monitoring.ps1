param()

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $false }

$repoRootRaw = git rev-parse --show-toplevel 2>&1
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRootRaw)) {
  Write-Error "Not inside a git repository or git is unavailable."
  exit 1
}
$repoRoot = $repoRootRaw.ToString().Trim()
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "audit-artifacts\module-010\execution_$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null

"MODULE_010=Error Handling & Monitoring" | Out-File "$out\00_summary.txt"
"BRANCH=$(git branch --show-current)" | Add-Content "$out\00_summary.txt"
"HEAD=$(git rev-parse HEAD)" | Add-Content "$out\00_summary.txt"

$py = if (Test-Path ".venv\Scripts\python.exe") {
  ".venv\Scripts\python.exe"
} elseif (Test-Path "backend\venv\Scripts\python.exe") {
  "backend\venv\Scripts\python.exe"
} else {
  "python"
}

$env:PYTHONPATH = (Resolve-Path "backend").Path
$env:DJANGO_SETTINGS_MODULE = "crown_api.settings"
if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = "module-010-local-secret-key" }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "sqlite:///./ci.sqlite3" }

"=== DJANGO CHECK ===" | Out-File "$out\10_django_check.txt"
& $py "backend\manage.py" check *> "$out\10_django_check_console.txt"
"EXIT_CODE=$LASTEXITCODE" | Add-Content "$out\10_django_check.txt"
Get-Content "$out\10_django_check_console.txt" | Add-Content "$out\10_django_check.txt"
$djangoExit = $LASTEXITCODE

"=== MIDDLEWARE ORDER ===" | Out-File "$out\20_middleware_order.txt"
Select-String -Path "backend\crown_api\settings.py" -Pattern "AuthenticationMiddleware|RequestCorrelationMiddleware|TenantIsolationMiddleware|AuditMiddleware" |
  ForEach-Object { "$($_.LineNumber):$($_.Line)" } |
  Add-Content "$out\20_middleware_order.txt"

"=== OBSERVABILITY INCIDENT GATE ===" | Out-File "$out\30_observability_incident_gate.txt"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\execution\160_crown_observability_incident_gate.ps1" *> "$out\30_observability_incident_gate_console.txt"
"EXIT_CODE=$LASTEXITCODE" | Add-Content "$out\30_observability_incident_gate.txt"
Get-Content "$out\30_observability_incident_gate_console.txt" | Add-Content "$out\30_observability_incident_gate.txt"
$gateExit = $LASTEXITCODE

"=== FINAL STATUS ===" | Out-File "$out\90_final_status.txt"
"DJANGO_CHECK_EXIT=$djangoExit" | Add-Content "$out\90_final_status.txt"
"OBSERVABILITY_GATE_EXIT=$gateExit" | Add-Content "$out\90_final_status.txt"
"MODULE_010_STATUS=BLOCKED_UNTIL_MONITORING_AND_INCIDENT_EVIDENCE_ATTACHED" | Add-Content "$out\90_final_status.txt"

Write-Host "DONE: $out"
exit 0
