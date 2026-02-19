$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

function Assert([bool]$cond, [string]$msg) { if (-not $cond) { throw $msg } }

Write-Host "== Phase 1 Contract Check ==" -ForegroundColor Cyan

# Required frontend files
$requiredFiles = @(
  "frontend/dashboards/src/pages/ParentStudent360Page.jsx",
  "frontend/dashboards/src/pages/Student360Page.jsx",
  "frontend/dashboards/src/components/student360/GraduationBreakdownDrawer.jsx",
  "frontend/dashboards/src/routes/router.jsx"
)

foreach ($f in $requiredFiles) {
  Assert (Test-Path $f) ("Missing required file: " + $f)
}

# Required route strings (router)
$router = Get-Content "frontend/dashboards/src/routes/router.jsx" -Raw
Assert ($router -match "/students/:id") "router.jsx missing /students/:id route"
Assert ($router -match "/parent/students/:id") "router.jsx missing /parent/students/:id route"

# Required backend route wiring (graduation breakdown at minimum)
$gradUrls = Get-Content "backend/graduation/urls.py" -Raw
Assert ($gradUrls -match "breakdown") "backend/graduation/urls.py missing breakdown route"

# Lane 1: admissions enroll endpoint
Assert (Test-Path "backend/admissions/views_enroll.py") "Lane 1: missing backend/admissions/views_enroll.py"
$admUrls = Get-Content "backend/admissions/api_urls.py" -Raw
Assert ($admUrls -match "enroll") "Lane 1: admissions/api_urls.py missing enroll route"
$admJs = Get-Content "frontend/dashboards/src/api/admissions.js" -Raw
Assert ($admJs -match "enrollApplicant") "Lane 1: frontend/api/admissions.js missing enrollApplicant"

Write-Host "PHASE1_CONTRACT=PASS" -ForegroundColor Green
