$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

function Assert([bool]$cond, [string]$msg) { if (-not $cond) { throw $msg } }

Write-Host "== Phase 1 Proof ==" -ForegroundColor Cyan

# --- A) Backend health must be 200
$r = Invoke-WebRequest "http://127.0.0.1:8000/api/system/health/" -UseBasicParsing -TimeoutSec 5
Assert ($r.StatusCode -eq 200) ("Backend health not 200: " + $r.StatusCode)
Write-Host "BACKEND_HEALTH=200" -ForegroundColor Green

# --- B) Frontend must be 200
$r2 = Invoke-WebRequest "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
Assert ($r2.StatusCode -eq 200) ("Frontend not 200: " + $r2.StatusCode)
Write-Host "FRONTEND=200" -ForegroundColor Green

# --- C) Sanity checks for Phase 1 endpoints (NO AUTH must fail)
$phase1NoAuth = @(
  "http://127.0.0.1:8000/api/v1/graduation/audit/c0e3c8bd-a439-471a-95f7-f0151ae2d7a1/breakdown/"
)

foreach ($u in $phase1NoAuth) {
  try {
    Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 5 | Out-Null
    throw "Expected auth failure, but succeeded: $u"
  } catch {
    # Accept 401/403 only
    $code = $null
    try { $code = $_.Exception.Response.StatusCode.value__ } catch { $code = -1 }
    Assert (($code -eq 401) -or ($code -eq 403)) ("Expected 401/403 for $u but got: $code")
    Write-Host ("NOAUTH_OK=" + $u + " => " + $code) -ForegroundColor Green
  }
}

Write-Host "PHASE1_PROOF=PASS" -ForegroundColor Green
