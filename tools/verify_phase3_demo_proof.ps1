param(
  [ValidateSet("static","strict")]
  [string]$Mode = "static"
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
  exit 1
}

function Ok($msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

function Require-File($path) {
  if (!(Test-Path $path)) { Fail "Missing file: $path" }
  Ok "Found file: $path"
}

function Require-Pattern($path, $pattern, $label) {
  if (!(Test-Path $path)) { Fail "Missing file for pattern check: $path" }
  $m = Select-String -Path $path -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
  if (!$m) { Fail "Missing pattern ($label) in $path :: $pattern" }
  Ok "Pattern present ($label): $pattern"
}

Write-Host "=== Phase 3 Demo Proof Pack (Mode=$Mode) ===" -ForegroundColor Cyan

# ------------------------------------------------------------
# A) Backend demo API surface (routes must exist)
# ------------------------------------------------------------
$apiUrls = "backend/crown_api/api_urls.py"
Require-File $apiUrls

# Ledger core (Phase 2 gates, Phase 3 regression prevention)
Require-Pattern $apiUrls 'path("ledger/charges/",'            "ledger charges create"
Require-Pattern $apiUrls 'path("ledger/payments/",'           "ledger payments record"
Require-Pattern $apiUrls 'ledger/payments/<str:payment_id>/allocate/' "ledger payment allocate"
Require-Pattern $apiUrls 'path("ledger/invariants/",'         "ledger invariants endpoint"

# Void endpoints (Phase 2 P5)
Require-Pattern $apiUrls 'ledger/charges/<str:charge_id>/void/'  "ledger void charge"
Require-Pattern $apiUrls 'ledger/payments/<str:payment_id>/void/' "ledger void payment"

# Billing surface used by dashboards
Require-Pattern $apiUrls 'ledger/charges/open/'  "ledger open charges"
Require-Pattern $apiUrls 'ledger/invoices/open/' "ledger open invoices"

# ------------------------------------------------------------
# B) Frontend demo surface (pages must exist)
#    Names match the actual files in frontend/dashboards/src/pages/
# ------------------------------------------------------------
$router = "frontend/dashboards/src/routes/router.jsx"
Require-File $router

$pages = @(
  "frontend/dashboards/src/pages/BillingDashboard.jsx",
  "frontend/dashboards/src/pages/FinanceInvoicesList.jsx",
  "frontend/dashboards/src/pages/AdmissionsPipelineList.jsx",
  "frontend/dashboards/src/pages/FinancialAidDashboard.jsx"
)

foreach ($p in $pages) { Require-File $p }

# Router must reference these components (import + route usage)
Require-Pattern $router "BillingDashboard"       "router: BillingDashboard"
Require-Pattern $router "FinanceInvoicesList"     "router: FinanceInvoicesList"
Require-Pattern $router "AdmissionsPipelineList" "router: AdmissionsPipelineList"
Require-Pattern $router "FinancialAidDashboard"  "router: FinancialAidDashboard"

# In strict mode, fail if router doesn't include key route path segments
if ($Mode -eq "strict") {
  Require-Pattern $router "/billing"    "router path: /billing"
  Require-Pattern $router "/finance"    "router path: /finance"
  Require-Pattern $router "/admissions" "router path: /admissions"
}

# ------------------------------------------------------------
# C) Repo integrity checks (Phase 3 baseline expectations)
# ------------------------------------------------------------
Require-File ".github/workflows"
Require-File "backend"
Require-File "frontend"

Ok "Phase 3 Demo Proof Pack gate PASSED."
exit 0
