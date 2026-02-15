param(
  [Alias("APITimeout")][int]$TimeoutSec = 5,
  [int]$MinAdmissionsApplications = 5,
  [int]$MinAidApplications = 3,
  [int]$MinEnrolledStudents = 1,
  [int]$MinStudentsBilled = 1,
  [string]$SchoolId = "",
  [string]$AcademicYearId = ""
)

$ErrorActionPreference = "Stop"

$Backend = "http://127.0.0.1:8000"
$Frontend = "http://127.0.0.1:3000"

# CI-aware: relax demo environment checks when running in GitHub Actions
$IsCI = $env:GITHUB_ACTIONS -eq "true"
if ($IsCI) {
  Write-Host "Running in CI - relaxed demo environment checks"
}

function Fail([string]$msg) {
  Write-Host "GATE=RED"
  Write-Host "REASON=$msg"
  
  # Skip snapshot in CI (no demo clone expected)
  if ($IsCI) {
    Write-Host "AUTO_SNAPSHOT=SKIPPED reason=ci_environment"
    exit 1
  }
  
  try {
    $snap = Join-Path $PSScriptRoot "demo_snapshot.ps1"
    if (Test-Path $snap) {
      Write-Host "AUTO_SNAPSHOT=START"
      powershell -ExecutionPolicy Bypass -File $snap
      Write-Host "AUTO_SNAPSHOT=END"
    }
    else {
      Write-Host "AUTO_SNAPSHOT=SKIPPED reason=missing_demo_snapshot"
    }
  }
  catch {
    Write-Host "AUTO_SNAPSHOT=FAILED error=$($_.Exception.Message)"
  }
  exit 1
}

function Assert([bool]$cond, [string]$msg) {
  if (-not $cond) {
    Fail $msg
  }
}

function Assert-NonEmpty([string]$value, [string]$reason) {
  if ([string]::IsNullOrWhiteSpace($value)) {
    Fail "$reason got=empty expected=uuid"
  }
}

function Assert-UUID([string]$value, [string]$reason) {
  try {
    [void][guid]::Parse($value)
  }
  catch {
    Fail "$reason got=$value expected=uuid"
  }
}

function Get-Json([string]$url, [string]$reasonOnFail) {
  try {
    $res = Invoke-WebRequest -UseBasicParsing -TimeoutSec $TimeoutSec $url
    return ($res.Content | ConvertFrom-Json)
  }
  catch {
    Fail "$reasonOnFail url=$url err=$($_.Exception.Message)"
  }
}

Write-Host "== GOLDEN PATH GATE =="

$schoolId = if ($SchoolId) { $SchoolId } else { $env:CROWN_GATE_SCHOOL_ID }
$yearId = if ($AcademicYearId) { $AcademicYearId } else { $env:CROWN_GATE_YEAR_ID }

Assert-NonEmpty $schoolId "CTX_MISSING_SCHOOL_ID"
Assert-NonEmpty $yearId "CTX_MISSING_YEAR_ID"

Assert-UUID $schoolId "CTX_INVALID_SCHOOL_ID"
Assert-UUID $yearId "CTX_INVALID_YEAR_ID"

$qsYearId = "school_id=$schoolId&year_id=$yearId"
$qsAcademicYearId = "school_id=$schoolId&academic_year_id=$yearId"

$health = Get-Json "$Backend/health/" "SYS_HEALTH_HTTP_FAIL"
Assert ($health.demo_mode -eq $true) "SYS_DEMO_MODE_INACTIVE got=$($health.demo_mode) expected=true"`nAssert ([bool]$health.build_sha -and $health.build_sha -ne "local-dev") "SYS_BUILD_SHA_INVALID got=$($health.build_sha) expected!=local-dev"

try {
  $frontendStatus = (Invoke-WebRequest -UseBasicParsing -TimeoutSec $TimeoutSec "$Frontend/").StatusCode
  Assert ($frontendStatus -eq 200) "SYS_FRONTEND_NOT_200 got=$frontendStatus expected=200"
}
catch {
  Fail "SYS_FRONTEND_HTTP_FAIL url=$Frontend/ err=$($_.Exception.Message)"
}

$admissions = Get-Json "$Backend/api/admissions/metrics/?$qsYearId" "ADM_SUMMARY_HTTP_FAIL"
Assert ($admissions.metrics.applications_count -ge $MinAdmissionsApplications) "ADM_APPLICATIONS_LOW got=$($admissions.metrics.applications_count) expected>=$MinAdmissionsApplications"

$aid = Get-Json "$Backend/api/director/aid/summary/?$qsAcademicYearId" "AID_SUMMARY_HTTP_FAIL"
Assert ($aid.awards.total_awards -ge $MinAidApplications) "AID_TOTAL_AWARDS_LOW got=$($aid.awards.total_awards) expected>=$MinAidApplications"
Assert ($aid.awards.total_awarded_cents -gt 0) "AID_TOTAL_AWARDED_ZERO got=$($aid.awards.total_awarded_cents) expected>0"

$registrar = Get-Json "$Backend/api/director/registrar/summary/?$qsAcademicYearId" "REG_SUMMARY_HTTP_FAIL"
Assert ($registrar.enrollment.total_students -ge $MinEnrolledStudents) "REG_TOTAL_STUDENTS_EMPTY got=$($registrar.enrollment.total_students) expected>=$MinEnrolledStudents"

$finance = Get-Json "$Backend/api/director/finance/summary/?$qsAcademicYearId" "FIN_SUMMARY_HTTP_FAIL"
Assert ($finance.tuition.students_billed -ge $MinStudentsBilled) "FIN_STUDENTS_BILLED_LOW got=$($finance.tuition.students_billed) expected>=$MinStudentsBilled"
Assert ($finance.ledger.total_debits_cents -gt 0) "FIN_LEDGER_TOTAL_DEBITS_ZERO got=$($finance.ledger.total_debits_cents) expected>0"

$dashboard = Get-Json "$Backend/api/director/dashboard/?$qsYearId" "DASH_OVERVIEW_HTTP_FAIL"
Assert ($null -ne $dashboard.sections) "DASH_SECTIONS_MISSING got=sections expected=present"
Assert ($null -ne $dashboard.sections.aid) "DASH_SECTION_AID_MISSING got=sections.aid expected=present"
Assert ($null -ne $dashboard.sections.finance) "DASH_SECTION_FINANCE_MISSING got=sections.finance expected=present"
Assert ($null -ne $dashboard.sections.registrar) "DASH_SECTION_REGISTRAR_MISSING got=sections.registrar expected=present"

Write-Host "GATE=GREEN"
Write-Host "SCHOOL_ID=$schoolId"
Write-Host "ACADEMIC_YEAR_ID=$yearId"
Write-Host "BUILD_SHA=$($health.build_sha)"
exit 0

