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

# Lane 2: billing loop wiring (JWT auth on billing/ledger endpoints)
$billingApi = Get-Content "backend/billing/api.py" -Raw
Assert ($billingApi -match "IsAuthenticated") "Lane 2: billing/api.py missing IsAuthenticated (billing_runs/installment_plans still @login_required)"

$ledgerApi = Get-Content "backend/ledger/api.py" -Raw
Assert ($ledgerApi -match "IsAuthenticated") "Lane 2: ledger/api.py missing IsAuthenticated (open_charges/open_invoices still @login_required)"

Assert (Test-Path "tools/verify_lane2_billing_loop.ps1") "Lane 2: missing tools/verify_lane2_billing_loop.ps1"
Assert (Test-Path "backend/billing/tests/test_lane2_billing_smoke.py") "Lane 2: missing backend/billing/tests/test_lane2_billing_smoke.py"

# Lane 2: payment loop proof script + no session-auth redirect guard
Assert (Test-Path "tools/verify_lane2_payment_loop.ps1") "Lane 2: missing tools/verify_lane2_payment_loop.ps1"
Assert (Test-Path "backend/billing/tests/test_lane2_payment_endpoints.py") "Lane 2: missing backend/billing/tests/test_lane2_payment_endpoints.py"

$middleware = Get-Content "backend/core/middleware.py" -Raw
Assert ($middleware -match "ledger/accounts/ensure") "Lane 2: middleware missing ledger/accounts/ensure/ exemption"
Assert ($middleware -match "ledger/charges") "Lane 2: middleware missing ledger/charges/ exemption"
Assert ($middleware -match "ledger/payments") "Lane 2: middleware missing ledger/payments/ exemption"
Assert ($middleware -match "billing/payments") "Lane 2: middleware missing billing/payments/ exemption"

Write-Host "PHASE1_CONTRACT=PASS" -ForegroundColor Green
