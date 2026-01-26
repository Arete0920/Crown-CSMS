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

# Resolve repo root from tools/dev_scripts
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
# B) Health check (local or remote)
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== B) Health ==="
try {
  $h = Invoke-RestMethod "$ApiBase/health/" -TimeoutSec 8
} catch {
  $h = Invoke-RestMethod "$ApiBase/api/health/" -TimeoutSec 8
}
$h | ConvertTo-Json -Depth 6

# ------------------------------------------------------------
# C) JWT
# ------------------------------------------------------------
Write-Host ""
Write-Host "=== C) JWT ==="
$body = @{ username = $Username; password = $Password } | ConvertTo-Json
$tok = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/auth/token/" -ContentType "application/json" -Body $body -TimeoutSec 12
$token = $tok.access
if (-not $token) { throw "JWT failed. Check Username/Password." }
Write-Host ("Token prefix: " + $token.Substring(0, [Math]::Min(24, $token.Length)) + "...")

# ------------------------------------------------------------
# D) Seed context
#   - Local: run golden_path_seed.py (safe)
#   - Remote: require GP_* env vars (no Django shell against remote DB)
# ------------------------------------------------------------
$seed = $null

if ((Is-LocalApiBase $ApiBase) -and (-not $SkipSeed)) {
  $seedScript = Join-Path $ROOT "tools\dev_scripts\golden_path_seed.py"
  if (-not (Test-Path $seedScript)) { throw "Missing seed script: $seedScript" }

  Write-Host ""
  Write-Host "=== D) Seed context (LOCAL) ==="
  $seedJson = & $PY $seedScript
  $seed = ($seedJson | Select-Object -Last 1) | ConvertFrom-Json
  $seed | ConvertTo-Json -Depth 6
} else {
  Write-Host ""
  Write-Host "=== D) Seed context (REMOTE/API-only) ==="
  $seed = [pscustomobject]@{
    school_id          = $env:GP_SCHOOL_ID
    year_id            = $env:GP_YEAR_ID
    aid_award_id       = $env:GP_AID_AWARD_ID
    aid_application_id = $env:GP_AID_APP_ID
    invoice_id         = $env:GP_INVOICE_ID
  }

  # Require the minimum IDs for the smoke
  if (-not $seed.school_id)    { throw "Missing env var GP_SCHOOL_ID" }
  if (-not $seed.year_id)      { throw "Missing env var GP_YEAR_ID" }
  if (-not $seed.aid_award_id) { throw "Missing env var GP_AID_AWARD_ID" }
}

$headers = @{
  Authorization       = "Bearer $token"
  "Content-Type"      = "application/json"
  "X-Crown-School-Id" = $seed.school_id
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

if (Is-LocalApiBase $ApiBase) {
  Write-Host ""
  Write-Host "=== H) Repo hygiene (local) ==="
  git restore -- backend/db.sqlite3 | Out-Null
  git status -sb
}

Write-Host ""
Write-Host "=== DONE ==="
