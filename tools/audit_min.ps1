# tools/audit_min.ps1
# Minimal, deterministic audit runner (no giant prompts, no Copilot needed).
# Usage:
#   pwsh tools/audit_min.ps1 -ApiBase "http://127.0.0.1:8000" -SchoolId "1"

param(
  [Parameter(Mandatory=$true)] [string]$ApiBase,
  [Parameter(Mandatory=$true)] [string]$SchoolId
)

$ErrorActionPreference = "Stop"

function Section($t) {
  Write-Host ""
  Write-Host "============================================================"
  Write-Host $t
  Write-Host "============================================================"
}

# 0) Determinism
Section "0) SHA + clean tree"
$sha = (git rev-parse HEAD).Trim()
$dirty = (git status --porcelain)
if ($dirty) { throw "WORKTREE NOT CLEAN. Commit/stash first." }
Write-Host "SHA: $sha"

# 1) Output folder
$outDir = "audit_reports"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $outDir "run_$stamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
"SHA=$sha" | Out-File -Encoding utf8 (Join-Path $runDir "BUILD_SHA.txt")

# 2) Health
Section "1) /api/health"
$health = Invoke-RestMethod -Method GET -Uri "$ApiBase/api/health" -Headers @{ "X-School-Id" = $SchoolId }
$health | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 (Join-Path $runDir "api_health.json")

# 3) Tests
Section "2) pytest"
pytest -q | Tee-Object -FilePath (Join-Path $runDir "pytest.txt")

# 4) Tenant negative tests
Section "3) Tenant negative tests (must fail safely)"
$neg = @()
try { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/students/" | Out-Null } catch { $neg += "students_no_header: $($_.Exception.Message)" }
try { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/billing/my/" | Out-Null } catch { $neg += "billing_no_header: $($_.Exception.Message)" }
try { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/financial-aid/dashboard/" | Out-Null } catch { $neg += "fa_no_header: $($_.Exception.Message)" }
$neg | Out-File -Encoding utf8 (Join-Path $runDir "tenant_negative_tests.txt")

# 5) Role audit (API-only)
Section "4) Role endpoint audit (PASS/FAIL)"
$tokens = @{
  admin   = $env:CROWN_TOKEN_ADMIN
  teacher = $env:CROWN_TOKEN_TEACHER
  parent  = $env:CROWN_TOKEN_PARENT
  student = $env:CROWN_TOKEN_STUDENT
}
foreach ($k in $tokens.Keys) {
  if ([string]::IsNullOrWhiteSpace($tokens[$k])) { throw "Missing env token: CROWN_TOKEN_$($k.ToUpper())" }
}

function Hdr($token) { @{ "X-School-Id"=$SchoolId; "Authorization"="Bearer $token" } }

function Check($name, [scriptblock]$fn) {
  try { & $fn | Out-Null; return [pscustomobject]@{name=$name; status="PASS"; detail=""} }
  catch { return [pscustomobject]@{name=$name; status="FAIL"; detail=$_.Exception.Message} }
}

# Update these endpoint paths ONLY if yours differ.
$checks = @()
$checks += Check "admin whoami"   { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/whoami" -Headers (Hdr $tokens.admin) }
$checks += Check "teacher whoami" { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/whoami" -Headers (Hdr $tokens.teacher) }
$checks += Check "parent whoami"  { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/whoami" -Headers (Hdr $tokens.parent) }
$checks += Check "student whoami" { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/whoami" -Headers (Hdr $tokens.student) }

$checks += Check "admin admissions inquiries"  { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/admissions/inquiries/" -Headers (Hdr $tokens.admin) }
$checks += Check "admin admissions applicants" { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/admissions/applicants/" -Headers (Hdr $tokens.admin) }
$checks += Check "admin finance summary"       { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/finance/summary/" -Headers (Hdr $tokens.admin) }
$checks += Check "admin aid dashboard"         { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/financial-aid/dashboard/" -Headers (Hdr $tokens.admin) }
$checks += Check "teacher gradebook my"        { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/gradebook/my/" -Headers (Hdr $tokens.teacher) }
$checks += Check "teacher attendance my"       { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/attendance/my/" -Headers (Hdr $tokens.teacher) }
$checks += Check "parent billing my"           { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/billing/my/" -Headers (Hdr $tokens.parent) }
$checks += Check "parent gradebook my"         { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/gradebook/my/" -Headers (Hdr $tokens.parent) }
$checks += Check "student schedule"            { Invoke-RestMethod -Method GET -Uri "$ApiBase/api/student/schedule/" -Headers (Hdr $tokens.student) }

$csv = Join-Path $runDir "role_audit.csv"
$checks | Export-Csv -NoTypeInformation -Path $csv
$checks | Format-Table -AutoSize

Section "DONE"
Write-Host "Run dir: $runDir"
