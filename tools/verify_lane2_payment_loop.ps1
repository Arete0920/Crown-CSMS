param(
  [string]$BaseUrl = $env:CROWN_API_BASE_URL,
  [string]$Token   = $env:CROWN_JWT_ACCESS,
  [string]$SchoolId= $env:CROWN_SCHOOL_ID,
  [string]$HouseholdId = $env:CROWN_DEMO_HOUSEHOLD_ID,
  [decimal]$Amount = 10.00
)

$ErrorActionPreference = "Stop"

function Die($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Ok($msg)  { Write-Host "OK: $msg" -ForegroundColor Green }

if (-not $BaseUrl)     { Die "Set CROWN_API_BASE_URL" }
if (-not $Token)       { Die "Set CROWN_JWT_ACCESS" }
if (-not $SchoolId)    { Die "Set CROWN_SCHOOL_ID" }
if (-not $HouseholdId) { Die "Set CROWN_DEMO_HOUSEHOLD_ID" }

$BaseUrl   = $BaseUrl.TrimEnd("/")
$AmountStr = [string]::Format("{0:F2}", $Amount)

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
    $params.Body        = ($body | ConvertTo-Json -Depth 5 -Compress)
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

Write-Host ""
Write-Host "=== Lane 2 Payment Loop Proof ==="
Write-Host "BaseUrl:     $BaseUrl"
Write-Host "SchoolId:    $SchoolId"
Write-Host "HouseholdId: $HouseholdId"
Write-Host "Amount:      $AmountStr"
Write-Host ""

# Step 1: Ensure ledger account for household
$ensureResp = Req "POST" "/api/v1/ledger/accounts/ensure/" @{ household_id = $HouseholdId }
$accountId = $ensureResp.data.id
if (-not $accountId) { Die "ensure_account did not return data.id. Got: $($ensureResp | ConvertTo-Json -Depth 3)" }
Ok "ledger account ensured: $accountId"

# Step 2: Create a charge against that account
$chargeResp = Req "POST" "/api/v1/ledger/charges/" @{
  account_id  = $accountId
  description = "Lane2 payment loop proof charge"
  amount      = $AmountStr
}
$chargeId = $chargeResp.data.id
if (-not $chargeId) { Die "create_charge did not return data.id. Got: $($chargeResp | ConvertTo-Json -Depth 3)" }
Ok "charge created: $chargeId (amount=$AmountStr)"

# Step 3: Record payment + allocate in one call (ledger record_payment view)
# amount: decimal string, allocations: [{charge_id, amount}]
$payResp = Req "POST" "/api/v1/ledger/payments/" @{
  account_id  = $accountId
  amount      = $AmountStr
  source      = "manual"
  allocations = @(
    @{ charge_id = $chargeId; amount = $AmountStr }
  )
}
$paymentId = $payResp.data.id
if (-not $paymentId) { Die "record_payment did not return data.id. Got: $($payResp | ConvertTo-Json -Depth 3)" }
Ok "payment recorded + allocated: $paymentId"
Ok "allocated_total=$($payResp.data.allocated_total)  remaining_unallocated=$($payResp.data.remaining_unallocated)"

# Step 4: Verify the charge is NOT in open charges (balance == 0)
$openResp = Req "GET" "/api/v1/ledger/charges/open/?household_id=$HouseholdId"
$openCharges = $openResp.data
$chargeStillOpen = $false
if ($openCharges) {
  foreach ($row in $openCharges) {
    if ($row.charge.id -eq $chargeId) { $chargeStillOpen = $true; break }
  }
}

Write-Host ""
if ($chargeStillOpen) {
  Die "Charge $chargeId still in open list after full payment -- allocation may not have applied."
} else {
  Ok "CHARGE BALANCE CLEARED -- not in open list after payment"
  Write-Host "=== RESULT: PAYMENT LOOP OK ==="
  exit 0
}
