param(
  [string]$BaseUrl = $env:CROWN_API_BASE_URL,
  [string]$Token   = $env:CROWN_JWT_ACCESS,
  [string]$SchoolId= $env:CROWN_SCHOOL_ID,
  [string]$HouseholdId = $env:CROWN_DEMO_HOUSEHOLD_ID
)

$ErrorActionPreference="Stop"

function Die($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Ok($msg)  { Write-Host "OK: $msg" -ForegroundColor Green }

if (-not $BaseUrl) { Die "Set CROWN_API_BASE_URL (example: http://127.0.0.1:8000)" }
if (-not $Token)   { Die "Set CROWN_JWT_ACCESS (a valid Bearer token)" }
if (-not $SchoolId){ Die "Set CROWN_SCHOOL_ID (tenant UUID for X-School-Id header)" }
if (-not $HouseholdId) { Die "Set CROWN_DEMO_HOUSEHOLD_ID (a household UUID for open invoices + summary)" }

$BaseUrl = $BaseUrl.TrimEnd("/")

$commonHeaders = @(
  "-H", "Authorization: Bearer $Token",
  "-H", "X-School-Id: $SchoolId",
  "-H", "Content-Type: application/json"
)

function CurlJson([string]$method, [string]$path, [string]$bodyJson = $null) {
  $url = "$BaseUrl$path"
  $args = @("-sS", "-X", $method) + $commonHeaders + @($url)
  if ($bodyJson) { $args += @("-d", $bodyJson) }
  $raw = & curl.exe @args
  if ($LASTEXITCODE -ne 0) { Die "curl failed: $method $path" }
  if (-not $raw) { Die "empty response: $method $path" }
  try { return ($raw | ConvertFrom-Json) } catch { Die "non-JSON response: $method $path`n$raw" }
}

Write-Host ""
Write-Host "=== Lane 2 Billing Loop Proof ==="
Write-Host "BaseUrl: $BaseUrl"
Write-Host "SchoolId: $SchoolId"
Write-Host "HouseholdId: $HouseholdId"
Write-Host ""

# 1) Household billing summary should load
$summary = CurlJson "GET" "/api/v1/households/$HouseholdId/billing/summary/"
Ok "household billing summary loaded"

# 2) Open invoices should load
$open = CurlJson "GET" "/api/v1/billing/households/$HouseholdId/open-invoices/"
Ok "open invoices loaded"

# 3) Billing runs list should load
$runs = CurlJson "GET" "/api/v1/billing/runs/"
Ok "billing runs list loaded"

# 4) Invoices list should load (wrapped endpoint)
$invoices = CurlJson "GET" "/api/v1/billing/invoices/"
Ok "invoices list loaded"

# 5) Installment plans should load
$plans = CurlJson "GET" "/api/v1/billing/installment-plans/"
Ok "installment plans loaded"

# 6) Ledger "open charges" should load (account_id or household_id required by view)
$charges = CurlJson "GET" "/api/v1/ledger/charges/open/?household_id=$HouseholdId"
Ok "ledger open charges loaded"

Write-Host ""
Write-Host "=== RESULT: BILLING LOOP BASELINE OK ==="
Write-Host "Next: payment posting/apply smoke (requires known invoice/payment ids)."
Write-Host ""
