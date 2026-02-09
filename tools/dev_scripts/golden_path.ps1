# ============================================================
# CROWN2026 - GOLDEN PATH SMOKE HARNESS (LOCAL OR AZURE)
# ------------------------------------------------------------
# LOCAL (default):
#   .\tools\dev_scripts\golden_path.ps1
#
# AZURE DEV (API-only; no local Django shell against remote DB):
#   $env:GP_SCHOOL_ID="..."; $env:GP_YEAR_ID="..."; $env:GP_AID_AWARD_ID="..."; $env:GP_AID_APP_ID="..."; $env:GP_INVOICE_ID="..."
#   .\tools\dev_scripts\golden_path.ps1 -ApiBase "https://YOUR-DEV.azurewebsites.net" -SkipSeed
# ============================================================

param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$Username = "admin",
  [string]$Password = "Crown2026!",
  [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"

# --- CI env overrides ---
if (-not $ApiBase -and $env:GP_API_BASE) { $ApiBase = $env:GP_API_BASE }

$GP_USER = $env:GP_USERNAME
$GP_PASS = $env:GP_PASSWORD
$GP_SEED_KEY = $env:GP_SEED_KEY

# Resolve repo root from tools/dev_scripts

function Ensure-CiUser {
  param(
    [string]$ApiBase
  )

  if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
    throw "DEV_OPS_SECRET is not set. Cannot ensure CI user."
  }

  $headers = @{
    "X-Admin-Ops-Secret" = $env:DEV_OPS_SECRET
    "Content-Type"      = "application/json"
  }

  $payload = @{} | ConvertTo-Json
  return Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/system/ensure-ci-user/" -Headers $headers -Body $payload -TimeoutSec 12
}

function Get-JwtViaEnsure {
  param(
    [string]$ApiBase
  )

  $resp = Ensure-CiUser -ApiBase $ApiBase
  if (-not $resp) { throw "ensure-ci-user returned empty response" }
  if (-not $resp.access) { throw "ensure-ci-user response missing 'access' JWT" }
  return $resp.access
}

$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PY   = Join-Path $ROOT ".venv\Scripts\python.exe"
$MANAGE = Join-Path $ROOT "backend\manage.py"

# Force repo-root working directory regardless of where user runs from
Set-Location $ROOT

function Is-LocalApiBase([string]$base) {
  return ($base -match '^http://(127\.0\.0\.1|localhost)(:\d+)?$')
}

function Invoke-JsonPost([string]$Url, [hashtable]$Headers, $Obj, [int]$TimeoutSec = 25) {
  $json = $Obj | ConvertTo-Json -Depth 10
  return Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Url -Headers $Headers -Body $json -TimeoutSec $TimeoutSec
}

function Get-JwtToken {
  param(
    [string]$ApiBase,
    [string]$Username,
    [string]$Password
  )

  $body = @{ username = $Username; password = $Password } | ConvertTo-Json
  return (Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/auth/token/" -ContentType "application/json" -Body $body -TimeoutSec 12).access
}

function Ensure-CiUser {
  param(
    [string]$ApiBase,
    [string]$Username,
    [string]$Password
  )

  if ([string]::IsNullOrWhiteSpace($env:DEV_OPS_SECRET)) {
    throw "DEV_OPS_SECRET is not set. Cannot ensure CI user."
  }

  Write-Host "DEV_OPS_SECRET present: True (length: $($env:DEV_OPS_SECRET.Length) chars)"

  $headers = @{
    "X-Admin-Ops-Secret" = $env:DEV_OPS_SECRET
    "Content-Type"       = "application/json"
  }

  $payload = @{} | ConvertTo-Json

  $resp = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/system/ensure-ci-user/" -Headers $headers -Body $payload -TimeoutSec 12
  Write-Host "✅ CI user ensured. Response: $($resp | ConvertTo-Json -Depth 2)"
  return $resp
}

Write-Host "=== CROWN2026 - GOLDEN PATH ==="
Write-Host "ApiBase: $ApiBase"
Write-Host "Mode:   " -NoNewline
if (Is-LocalApiBase $ApiBase) { Write-Host "LOCAL" } else { Write-Host "REMOTE (Azure/API-only)" }

# ------------------------------------------------------------
# A) Local-only prep: migrate + dev_bootstrap + runserver
# ------------------------------------------------------------
if (Is-LocalApiBase $ApiBase) {
  if (-not (Test-Path $PY)) { throw "Python venv not found: $PY" }
  if (-not (Test-Path $MANAGE)) { throw "manage.py not found: $MANAGE" }

  Set-Location $ROOT

  Write-Host ""
  Write-Host "=== A1) Repo hygiene (local) ==="
  git status -sb

  Write-Host ""
  Write-Host "=== A2) Migrate + dev_bootstrap (local) ==="
  & $PY $MANAGE migrate
  & $PY $MANAGE dev_bootstrap

  Write-Host ""
  Write-Host "=== A3) Restart backend on :8000 (local) ==="
  $p = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
  if ($p) {
    "Stopping PID $($p.OwningProcess) on 8000"
    Stop-Process -Id $p.OwningProcess -Force
    Start-Sleep -Milliseconds 300
  } else {
    "No listener on 8000"
  }

  Start-Process powershell -ArgumentList "-NoExit","-Command","cd `"$ROOT`"; & `"$PY`" `"$MANAGE`" runserver 127.0.0.1:8000 --noreload"
  Start-Sleep -Seconds 2
}

# ------------------------------------------------------------
# B) Health check (local or remote) - with retry for Azure cold starts
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== B) Health ==="
$maxRetries = 6
$retryDelay = 5
$healthOk = $false

for ($attempt = 1; $attempt -le $maxRetries; $attempt++) {
  try {
    $h = Invoke-RestMethod "$ApiBase/health/" -TimeoutSec 8
    $healthOk = $true
    break
  } catch {
    try {
      $h = Invoke-RestMethod "$ApiBase/api/health/" -TimeoutSec 8
      $healthOk = $true
      break
    } catch {
      Write-Host "Health check attempt $attempt/$maxRetries failed: $($_.Exception.Message)"
      if ($attempt -lt $maxRetries) {
        Write-Host "Retrying in $retryDelay seconds..."
        Start-Sleep -Seconds $retryDelay
        $retryDelay = [Math]::Min($retryDelay + 2, 10)  # Increase delay up to 10s
      }
    }
  }
}

if (-not $healthOk) {
  throw "Health check failed after $maxRetries attempts. Azure app may be down or restarting."
}

$h | ConvertTo-Json -Depth 6

# ------------------------------------------------------------
# C) JWT (with auto-heal: ensure CI user if "No active account" error)
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== C) JWT ==="

# CI auth is sourced from the server (Azure App Service CI_SMOKE_*). We do NOT hardcode usernames in GitHub.
try {
  $ciUserResponse = Ensure-CiUser -ApiBase $ApiBase
  $tok = $ciUserResponse.access
  Write-Host "✅ ensure-ci-user returned JWT."
} catch {
  throw "FAILED: ensure-ci-user could not return JWT. Root cause: $($_.Exception.Message)"
}

if (Is-LocalApiBase $ApiBase) {
  Write-Host "=== D) Seed context (LOCAL) ==="
  $seedJson = & $PY $seedScript
  $seed = ($seedJson | Select-Object -Last 1) | ConvertFrom-Json
  $seed | ConvertTo-Json -Depth 6
} else {
  Write-Host ""
  Write-Host "=== D) Seed context (REMOTE/API-only) ==="
  $seed = [pscustomobject]@{
    school_id          = $ciUserResponse.school_id
    year_id            = $env:GP_YEAR_ID
    aid_award_id       = $env:GP_AID_AWARD_ID
    aid_application_id = $env:GP_AID_APP_ID
    invoice_id         = $env:GP_INVOICE_ID
  }

  # Require the minimum: school_id from CI user
  if (-not $seed.school_id) { throw "ensure-ci-user response missing 'school_id'" }
}

$headers = @{
  Authorization       = "Bearer $($tok.Trim())"
  "Content-Type"      = "application/json"
  "X-Crown-School-Id" = $seed.school_id
  "X-School-Id"       = $seed.school_id
}

if ((-not (Is-LocalApiBase $ApiBase)) -and (-not $seed.invoice_id)) {
  Write-Host "Creating invoice via JWT billing runs API..."
  $runBody = @{
    term               = "2026-2027"
    amount_per_student = "250.00"
    description        = "Golden Path API run"
  } | ConvertTo-Json

  $run = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/billing/runs/api/" -Headers $headers -Body $runBody -TimeoutSec 90
  $InvoiceId = $run.data.invoice_id
  if (-not $InvoiceId) { throw "No invoice_id returned from /api/billing/runs/api/" }
  $seed.invoice_id = $InvoiceId
  $env:GP_INVOICE_ID = $InvoiceId
}

$seed | ConvertTo-Json -Depth 6

# ------------------------------------------------------------
# E) Director Actions - POST_ACCEPTED_AWARDS (receipt)
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== E) Director Actions: POST_ACCEPTED_AWARDS (receipt) ==="
$payload = @{
  action    = "POST_ACCEPTED_AWARDS"
  school_id = $seed.school_id
  year_id   = $seed.year_id
  ids       = @($seed.aid_award_id)
}
$r = Invoke-JsonPost "$ApiBase/api/director/actions/" $headers $payload 25
Write-Host "HTTP $($r.StatusCode)"
Write-Host $r.Content

# ------------------------------------------------------------
# F) Director Actions - AID_GENERATE_NEEDS_INFO_EMAILS (optional)
# ------------------------------------------------------------
if ($seed.aid_application_id) {
  Write-Host ""
  Write-Host "=== F) Director Actions: AID_GENERATE_NEEDS_INFO_EMAILS (receipt) ==="
  $payload = @{
    action    = "AID_GENERATE_NEEDS_INFO_EMAILS"
    school_id = $seed.school_id
    year_id   = $seed.year_id
    ids       = @($seed.aid_application_id)
  }
  $r2 = Invoke-JsonPost "$ApiBase/api/director/actions/" $headers $payload 25
  Write-Host "HTTP $($r2.StatusCode)"
  Write-Host $r2.Content
} else {
  Write-Host ""
  Write-Host "=== F) AID_GENERATE_NEEDS_INFO_EMAILS skipped (no GP_AID_APP_ID) ==="
}

# ------------------------------------------------------------
# G) Billing - record payment (receipt)
#   API response already contains invoice totals/paid/balance.
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== G) Billing: record payment (receipt) ==="
if (-not $seed.invoice_id) { throw "Missing invoice_id (expected to be created via /api/billing/runs/api/)" }
$paymentRef = "GP-PAY-" + (Get-Date).ToString("yyyyMMdd-HHmmss")
$pay = @{
  invoice_id   = $seed.invoice_id
  amount_cents = 25000
  method       = "cash"
  reference    = $paymentRef
  received_on  = (Get-Date).ToString("yyyy-MM-dd")
}
$r3 = Invoke-JsonPost "$ApiBase/api/billing/payments/record/" $headers $pay 25
Write-Host "HTTP $($r3.StatusCode)"
Write-Host $r3.Content

# ------------------------------------------------------------
# H) Financial Aid Drilldown
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== H) Financial Aid: drilldown ==="
$r4 = Invoke-RestMethod -Method Get -Uri "$ApiBase/api/financial-aid/drilldown/" -Headers $headers -TimeoutSec 25
Write-Host "HTTP 200 (expected)"
$data = $r4
if (-not $data.PSObject.Properties.Match('rows')) { throw "Missing rows in drilldown" }
if (-not $data.PSObject.Properties.Match('total')) { throw "Missing total in drilldown" }
Write-Host "Drilldown response shape OK"

if (Is-LocalApiBase $ApiBase) {
  Write-Host ""
  Write-Host "=== I) Repo hygiene (local) ==="
  git restore -- backend/db.sqlite3 | Out-Null
  git status -sb
}

Write-Host ""
Write-Host "=== DONE ==="
