param(
  [Alias("APITimeout")][int]$TimeoutSec = 20,
  [int]$AdmissionsCount = 10
)

$ErrorActionPreference = "Stop"

$mainRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.."))
$backendRoot = Join-Path $mainRoot "backend"
$py = Join-Path $mainRoot ".venv\Scripts\python.exe"


if (-not (Test-Path $py)) { throw "Python not found: $py" }
if (-not (Test-Path $backendRoot)) { throw "Backend path not found: $backendRoot" }

$env:ENVIRONMENT = "dev"
if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
  $env:DEV_OPS_SECRET = [Environment]::GetEnvironmentVariable("DEV_OPS_SECRET", "User")
}
if ([string]::IsNullOrWhiteSpace($env:CROWN_OPS_SECRET)) {
  $env:CROWN_OPS_SECRET = [Environment]::GetEnvironmentVariable("CROWN_OPS_SECRET", "User")
}

if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
  throw "DEV_OPS_SECRET missing in shell/User env"
}

Write-Host "== LOCKDOWN RUN =="

Push-Location $backendRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:CROWN_DEMO_MODE = "true"

# Boot Django server in background
Write-Host "Booting Django server..."
$serverJob = Start-Job -ScriptBlock {
  param($pyPath, $backendPath)
  Set-Location $backendPath
  & $pyPath manage.py runserver 127.0.0.1:8000 --noreload
} -ArgumentList $py, $backendRoot

# Wait for server to be ready
Write-Host "Waiting for server..."
$maxAttempts = 20
$attempt = 0
$serverReady = $false
while ($attempt -lt $maxAttempts -and -not $serverReady) {
  Start-Sleep -Milliseconds 500
  try {
    $healthStatus = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:8000/health/").StatusCode
    if ($healthStatus -eq 200) {
      $serverReady = $true
      Write-Host "Server ready!"
    }
  }
  catch {
    $attempt++
  }
}

if (-not $serverReady) {
  Stop-Job -Job $serverJob
  Remove-Job -Job $serverJob
  throw "Django server failed to start within timeout"
}

Write-Host "Seeding Heritage realism pack..."
& $py manage.py seed_heritage_realism_pack --no-finance-scripts
if ($LASTEXITCODE -ne 0) { throw "seed_heritage_realism_pack failed exit=$LASTEXITCODE" }

# ---- Gate context (School/Year) for golden_path_gate.ps1 ----
# Determine SchoolId + AcademicYearId from DB.
# Strategy: Find the school by name, then find the academic year that HAS the seeded admissions marker.
$gateCtxRaw = & $py manage.py shell -c @"
import json
from core.models import School, AcademicYear
from admissions.models import AdmissionsApplication

s = School.objects.filter(name='Heritage Christian Academy').order_by('-created_at', 'id').first()
if not s:
    print(json.dumps({'school_id': None, 'year_id': None, 'year_label': None}))
else:
    # Find the year that actually HAS the seeded admissions marker
    year_with_marker = AcademicYear.objects.filter(
        school=s,
        admissions_applications__notes_internal='seed_admissions_demo'
    ).distinct().first()
    y = year_with_marker if year_with_marker else AcademicYear.objects.filter(school=s, is_current=True).first()
    print(json.dumps({
      'school_id': str(s.id),
      'year_id': str(y.id) if y else None,
      'year_label': getattr(y, 'label', None) if y else None,
    }))
"@

if ($LASTEXITCODE -ne 0) { throw "gate context query failed exit=$LASTEXITCODE" }

# Filter for JSON line (starts with '{') in case Django fixture messages are present
$gateCtx = ($gateCtxRaw | Where-Object { $_ -match '^\{' }) | Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($gateCtx)) { 
  throw "gate context JSON not found in output: $($gateCtxRaw -join '; ')" 
}

try { $ctx = $gateCtx | ConvertFrom-Json } catch { throw "gate context JSON parse failed: $gateCtx" }

if ([string]::IsNullOrWhiteSpace($ctx.school_id)) { throw "CROWN_GATE_SCHOOL_ID could not be determined" }

# Prefer AcademicYear.id if present; otherwise allow label fallback only if your API accepts it.
if ([string]::IsNullOrWhiteSpace($ctx.year_id)) {
  throw "CROWN_GATE_YEAR_ID could not be determined (AcademicYear.id missing)"
}

$env:CROWN_GATE_SCHOOL_ID = $ctx.school_id
$env:CROWN_GATE_YEAR_ID   = $ctx.year_id

Write-Host "Gate context set: CROWN_GATE_SCHOOL_ID=$($env:CROWN_GATE_SCHOOL_ID) CROWN_GATE_YEAR_ID=$($env:CROWN_GATE_YEAR_ID)"
# ------------------------------------------------------------

try {
  $healthStatus = (Invoke-WebRequest -UseBasicParsing -TimeoutSec $TimeoutSec "http://127.0.0.1:8000/health/").StatusCode
  if ($healthStatus -ne 200) { throw "backend health status=$healthStatus" }
}
catch {
  throw "backend health check failed: $($_.Exception.Message)"
}
Pop-Location


Write-Host "LOCKDOWN_RUN=GREEN"
exit 0
