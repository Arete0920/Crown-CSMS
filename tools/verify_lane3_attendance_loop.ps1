param(
  [string]$BaseUrl   = $env:CROWN_API_BASE_URL,
  [string]$Token     = $env:CROWN_JWT_ACCESS,
  [string]$SchoolId  = $env:CROWN_SCHOOL_ID,
  [string]$SectionId = $env:CROWN_DEMO_SECTION_ID,
  [string]$StudentId = $env:CROWN_DEMO_STUDENT_ID
)

$ErrorActionPreference = "Stop"
function Die($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Ok($msg)  { Write-Host "OK: $msg" -ForegroundColor Green }

if (-not $BaseUrl)  { Die "Set CROWN_API_BASE_URL" }
if (-not $Token)    { Die "Set CROWN_JWT_ACCESS" }
if (-not $SchoolId) { Die "Set CROWN_SCHOOL_ID" }

$BaseUrl = $BaseUrl.TrimEnd("/")
$hdrs = @{
  "Authorization" = "Bearer $Token"
  "X-School-Id"   = $SchoolId
}

function Req([string]$method, [string]$path, [hashtable]$body = $null) {
  $url = "$BaseUrl$path"
  $params = @{
    Uri             = $url
    Method          = $method
    Headers         = $hdrs
    UseBasicParsing = $true
    TimeoutSec      = 15
    ErrorAction     = "Stop"
  }
  if ($body) {
    $params.Body        = ($body | ConvertTo-Json -Depth 6 -Compress)
    $params.ContentType = "application/json"
  }
  try {
    $r = Invoke-WebRequest @params
    return ($r.Content | ConvertFrom-Json)
  } catch {
    $sc = $_.Exception.Response.StatusCode.value__
    try {
      $eb = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream()).ReadToEnd()
      Die "${method} ${path} => HTTP ${sc}: ${eb}"
    } catch {
      Die "${method} ${path} => HTTP ${sc}: (no body)"
    }
  }
}

$today = (Get-Date).ToString("yyyy-MM-dd")

Write-Host ""
Write-Host "=== Lane 3 Attendance Proof ===" -ForegroundColor Cyan
Write-Host "BaseUrl:   $BaseUrl"
Write-Host "SchoolId:  $SchoolId"
Write-Host "Date:      $today"
Write-Host ""

# --- Step 1: resolve section ---
if (-not $SectionId) {
  $sec = Req "GET" "/api/v1/academics/sections/"
  $list = if ($sec.results) { $sec.results } else { $sec }
  if (-not $list -or $list.Count -lt 1) { Die "No sections from /api/v1/academics/sections/" }
  # sections endpoint returns section_id (not id)
  $SectionId = if ($list[0].section_id) { $list[0].section_id } else { $list[0].id }
}
Ok "Using SectionId: $SectionId"

# --- Step 2: student ID must be a core.models.Student.id (what AttendanceRecord.student FK targets)
# The academics roster returns households.Student IDs which don't match — use $StudentId directly.
if (-not $StudentId) {
  Die "Set CROWN_DEMO_STUDENT_ID to a core.models.Student.id (run: python manage.py shell -c `"from core.models import Student; print(Student.objects.first().id)`")"
}
Ok "Using StudentId: $StudentId"

# --- Step 3: submit attendance for today ---
$body = @{
  date  = $today
  items = @(
    @{ student_id = $StudentId; status = "present" }
  )
}
$sub = Req "POST" "/api/v1/academics/sections/$SectionId/attendance/" $body
if ($sub.ok -ne $true) { Die "submit did not return ok=true. Response: $($sub | ConvertTo-Json -Depth 5)" }
Ok "submit accepted: created=$($sub.created) updated=$($sub.updated) date=$($sub.date)"

# --- Step 4: parent/student read — confirm record exists ---
$att = Req "GET" "/api/v1/academics/students/$StudentId/attendance/"
$rows = if ($att.results) { $att.results } else { $att }
if (-not $rows -or $rows.Count -lt 1) { Die "student attendance list returned empty" }

$found = $false
foreach ($r in $rows) {
  $d = if ($r.date) { $r.date } elseif ($r.day) { $r.day } else { $r.attendance_date }
  $s = if ($r.status) { $r.status } elseif ($r.code) { $r.code } else { $r.state }
  if ($d -eq $today -and $s) { $found = $true; break }
}
if (-not $found) { Die "today's record NOT in student attendance list after submit" }

Ok "PARENT READ CONFIRMED — today's record present in student attendance list"
Write-Host ""
Write-Host "=== RESULT: LANE3 OK ===" -ForegroundColor Green
