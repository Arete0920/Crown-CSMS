# ============================================================
# CROWN2026 — GOLDEN PATH SMOKE: Admissions → Aid → Billing
# Deterministic-ish, route-aware (won’t guess endpoints you don’t have)
# ============================================================

$ErrorActionPreference = "Stop"

$ROOT="C:\Users\JMega\OneDrive\Desktop\Crown2026"
$PY="$ROOT\.venv\Scripts\python.exe"
$MANAGE="$ROOT\backend\manage.py"
$API="http://127.0.0.1:8000"
$USERNAME="admin"
$PASSWORD="Crown2026!"

Set-Location $ROOT

Write-Host "=== 0) Baseline hygiene ==="
git status -sb

Write-Host "`n=== 1) Migrate + bootstrap schools/admin ==="
& $PY $MANAGE migrate
& $PY $MANAGE dev_bootstrap

Write-Host "`n=== 2) Restart backend on :8000 (no reload) ==="
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

Write-Host "`n=== 3) Health ==="
try {
  Invoke-RestMethod "$API/health/" -TimeoutSec 5 | ConvertTo-Json -Depth 5
} catch {
  Invoke-RestMethod "$API/api/health/" -TimeoutSec 5 | ConvertTo-Json -Depth 5
}

Write-Host "`n=== 4) JWT ==="
$body=@{ username=$USERNAME; password=$PASSWORD } | ConvertTo-Json
$tokResp=Invoke-RestMethod -Method Post -Uri "$API/api/auth/token/" -ContentType "application/json" -Body $body -TimeoutSec 12
$token=$tokResp.access
if (-not $token) { throw "JWT failed. Check admin credentials." }
"Token prefix: $($token.Substring(0,[Math]::Min(24,$token.Length)))..."

Write-Host "`n=== 5) Seed Golden Path objects (DB) ==="
$seedJson = & $PY "$ROOT\tools\dev_scripts\golden_path_seed.py"
$seed = ($seedJson | Select-Object -Last 1) | ConvertFrom-Json
$seed | ConvertTo-Json -Depth 5

Write-Host "`n=== 6) Admissions step (only if endpoints exist) ==="
$admissionsCandidates=@(
  "/api/admissions/inquiries/",
  "/api/admissions/applicants/",
  "/api/admissions/applications/",
  "/api/admissions/leads/"
)
foreach ($ep in $admissionsCandidates) {
  try {
    $resp = Invoke-WebRequest -Method Options -Uri ($API+$ep) -Headers @{ Authorization="Bearer $token" } -TimeoutSec 5
    "Admissions endpoint exists: $ep (OPTIONS=$($resp.StatusCode))"
  } catch {
    # skip
  }
}

$headers=@{ Authorization = "Bearer $token"; "Content-Type"="application/json"; "X-Crown-School-Id"=$seed.school_id }

Write-Host "`n=== 7) Aid: Director Action — POST_ACCEPTED_AWARDS ==="
$payload=@{ action="POST_ACCEPTED_AWARDS"; school_id=$seed.school_id; year_id=$seed.year_id; ids=@($seed.aid_award_id) } | ConvertTo-Json -Depth 6
$resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$API/api/director/actions/" -Headers $headers -Body $payload -TimeoutSec 20
"Director Actions POST_ACCEPTED_AWARDS: HTTP $($resp.StatusCode)"
$resp.Content

Write-Host "`n=== 8) Aid: Director Action — AID_GENERATE_NEEDS_INFO_EMAILS ==="
$payload=@{ action="AID_GENERATE_NEEDS_INFO_EMAILS"; school_id=$seed.school_id; year_id=$seed.year_id; ids=@($seed.aid_application_id) } | ConvertTo-Json -Depth 6
$resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$API/api/director/actions/" -Headers $headers -Body $payload -TimeoutSec 20
"Director Actions AID_GENERATE_NEEDS_INFO_EMAILS: HTTP $($resp.StatusCode)"
$resp.Content

Write-Host "`n=== 9) Billing: Record Payment against invoice ==="
$paymentRef = "GP-PAY-" + (Get-Date).ToString("yyyyMMdd-HHmmss")
$pay=@{ invoice_id=$seed.invoice_id; amount_cents=25000; method="cash"; reference=$paymentRef; received_on=(Get-Date).ToString("yyyy-MM-dd") } | ConvertTo-Json -Depth 6
$resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$API/api/billing/payments/record/" -Headers $headers -Body $pay -TimeoutSec 20
"Billing record payment: HTTP $($resp.StatusCode)"
$resp.Content

Write-Host "`n=== 10) Receipt snapshot (DB proof points) ==="
& $PY "$ROOT\tools\dev_scripts\golden_path_receipt.py" \
  --school-id $seed.school_id \
  --invoice-id $seed.invoice_id \
  --aid-award-id $seed.aid_award_id \
  --aid-application-id $seed.aid_application_id

Write-Host "`n=== 11) Repo hygiene ==="
git restore -- backend/db.sqlite3 | Out-Null
git status -sb
