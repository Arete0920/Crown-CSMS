<#
.SYNOPSIS
    Crown2026 — MS365 SSO + Outbox end-to-end verification script.

.DESCRIPTION
    Validates the full stack for:
      1. AAD / Entra ID JWT validation  (/api/iam/health-auth/)
      2. AAD identity me endpoint       (/api/iam/me/)
      3. Outbox email enqueue           (/api/comms/send-test-email/)
      4. Celery worker reachability     (redis-cli ping)
      5. Settings guard — GRAPH_FROM_USER must be non-empty

    Run against local dev:
        pwsh tools/verify_m365_sso_and_outbox.ps1

    Run against staging:
        pwsh tools/verify_m365_sso_and_outbox.ps1 -BaseUrl https://your-app.azurewebsites.net

    Set $env:BEARER_TOKEN before running if you want to test real AAD auth.
    Leave it empty to skip AAD-protected checks (they'll report SKIP, not FAIL).
#>

param(
    [string]$BaseUrl    = "http://127.0.0.1:8000",
    [string]$SchoolId   = "19801b59-8c05-4c84-9312-5d792e4e839d",
    [string]$TestEmail  = "smoke-test@crownschool.app",
    [string]$BearerToken = $env:BEARER_TOKEN
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── Helpers ────────────────────────────────────────────────────────────────

$script:passed  = 0
$script:failed  = 0
$script:skipped = 0

function Pass([string]$Label) {
    Write-Host "  [PASS] $Label" -ForegroundColor Green
    $script:passed++
}

function Fail([string]$Label, [string]$Detail = "") {
    $msg = "  [FAIL] $Label"
    if ($Detail) { $msg += " — $Detail" }
    Write-Host $msg -ForegroundColor Red
    $script:failed++
}

function Skip([string]$Label, [string]$Reason = "") {
    $msg = "  [SKIP] $Label"
    if ($Reason) { $msg += " ($Reason)" }
    Write-Host $msg -ForegroundColor Yellow
    $script:skipped++
}

function Section([string]$Title) {
    Write-Host ""
    Write-Host "── $Title ──────────────────────────────────────" -ForegroundColor Cyan
}

function Invoke-ApiGet([string]$Url, [hashtable]$Headers = @{}) {
    try {
        $resp = Invoke-WebRequest -Uri $Url -Headers $Headers -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        return $resp
    } catch {
        return $null
    }
}

function Invoke-ApiPost([string]$Url, [hashtable]$Headers = @{}, [object]$Body = @{}) {
    try {
        $json = $Body | ConvertTo-Json -Depth 5
        $resp = Invoke-WebRequest -Uri $Url -Method POST -Headers $Headers `
                    -Body $json -ContentType "application/json" `
                    -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        return $resp
    } catch {
        return $null
    }
}

# ─── Section 1: Settings guard ───────────────────────────────────────────────

Section "1 — Django settings guard (GRAPH_FROM_USER)"

$checkSettingsCmd = @"
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, 'backend')
django.setup()
from django.conf import settings
val = getattr(settings, 'GRAPH_FROM_USER', None)
if val:
    print(f'GRAPH_FROM_USER={val}')
    sys.exit(0)
else:
    print('GRAPH_FROM_USER is empty or missing')
    sys.exit(1)
"@

try {
    $result = & ".venv\Scripts\python.exe" -c $checkSettingsCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Pass "GRAPH_FROM_USER is set: $result"
    } else {
        Fail "GRAPH_FROM_USER" "Not configured — set env var before deploying Celery worker"
    }
} catch {
    Fail "GRAPH_FROM_USER check" "Could not run Python check: $_"
}

# ─── Section 2: Health endpoints (unauthenticated) ───────────────────────────

Section "2 — Public health endpoints"

$healthResp = Invoke-ApiGet "$BaseUrl/api/health/"
if ($healthResp -and $healthResp.StatusCode -eq 200) {
    Pass "/api/health/ returns 200"
} else {
    Fail "/api/health/" "StatusCode=$($healthResp?.StatusCode) (is the server running at $BaseUrl?)"
}

$integrityResp = Invoke-ApiGet "$BaseUrl/api/integrity/"
if ($integrityResp -and $integrityResp.StatusCode -eq 200) {
    $body = $integrityResp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    $sha  = $body?.build_sha ?? $body?.sha ?? "(missing)"
    Pass "/api/integrity/ returns 200 (build_sha=$sha)"
} else {
    Fail "/api/integrity/" "StatusCode=$($integrityResp?.StatusCode)"
}

# ─── Section 3: AAD auth endpoints (require Bearer token) ────────────────────

Section "3 — AAD auth endpoints (/api/iam/)"

if (-not $BearerToken) {
    Skip "/api/iam/health-auth/" "No BEARER_TOKEN set — export it to test AAD JWT validation"
    Skip "/api/iam/me/"          "No BEARER_TOKEN set"
} else {
    $aadHeaders = @{
        "Authorization" = "Bearer $BearerToken"
        "X-School-Id"   = $SchoolId
    }

    $healthAuthResp = Invoke-ApiGet "$BaseUrl/api/iam/health-auth/" -Headers $aadHeaders
    if ($healthAuthResp -and $healthAuthResp.StatusCode -eq 200) {
        Pass "/api/iam/health-auth/ returns 200"
    } else {
        Fail "/api/iam/health-auth/" "StatusCode=$($healthAuthResp?.StatusCode) — token may be invalid or audience mismatch"
    }

    $meResp = Invoke-ApiGet "$BaseUrl/api/iam/me/" -Headers $aadHeaders
    if ($meResp -and $meResp.StatusCode -eq 200) {
        $meBody = $meResp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        $email  = $meBody?.email ?? "(empty)"
        Pass "/api/iam/me/ returns 200 (email=$email)"
    } else {
        Fail "/api/iam/me/" "StatusCode=$($meResp?.StatusCode)"
    }

    # Confirm 401 when no token is supplied (regression guard)
    $noAuthResp = Invoke-ApiGet "$BaseUrl/api/iam/me/"
    if ($noAuthResp -eq $null -or $noAuthResp.StatusCode -eq 401) {
        Pass "/api/iam/me/ returns 401 without token (good)"
    } else {
        Fail "/api/iam/me/ 401 guard" "Expected 401 without token, got $($noAuthResp?.StatusCode)"
    }
}

# ─── Section 4: Outbox email enqueue ─────────────────────────────────────────

Section "4 — Outbox email enqueue (/api/comms/send-test-email/)"

# We need a Crown JWT for this check since the comms endpoint uses IsAuthenticated
# Try to get a dev token first; if unavailable, get a real JWT via login
$devTokenResp = Invoke-ApiPost "$BaseUrl/api/dev/token/" -Body @{} -Headers @{ "X-School-Id" = $SchoolId }
$crownToken = $null
if ($devTokenResp -and $devTokenResp.StatusCode -eq 200) {
    $tokenBody  = $devTokenResp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    $crownToken = $tokenBody?.access ?? $tokenBody?.token
}

if (-not $crownToken) {
    Skip "/api/comms/send-test-email/" "Could not obtain Crown JWT (dev token endpoint unavailable or closed) — set CROWN_DEV_OPEN_API=true for local dev"
} else {
    $commsHeaders = @{
        "Authorization" = "Bearer $crownToken"
        "X-School-Id"   = $SchoolId
    }
    $emailPayload = @{
        to        = $TestEmail
        subject   = "Crown2026 Outbox Smoke Test"
        body      = "<p>Automated verification from verify_m365_sso_and_outbox.ps1</p>"
        school_id = $SchoolId
    }
    $sendResp = Invoke-ApiPost "$BaseUrl/api/comms/send-test-email/" -Headers $commsHeaders -Body $emailPayload
    if ($sendResp -and $sendResp.StatusCode -in 200, 202) {
        $sendBody   = $sendResp.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        $messageId  = $sendBody?.message_id ?? "(unknown)"
        Pass "/api/comms/send-test-email/ queued (message_id=$messageId)"
    } else {
        Fail "/api/comms/send-test-email/" "StatusCode=$($sendResp?.StatusCode)"
        if ($sendResp) { Write-Host "       Response: $($sendResp.Content)" -ForegroundColor DarkGray }
    }
}

# ─── Section 5: Celery / Redis reachability ───────────────────────────────────

Section "5 — Celery worker / Redis"

$redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
if (-not $redisCli) {
    Skip "Redis ping" "redis-cli not on PATH — install Redis client or check worker container"
} else {
    $redisUrl  = $env:CELERY_BROKER_URL ?? $env:REDIS_URL ?? "redis://localhost:6379/0"
    $redisHost = ([Uri]$redisUrl).Host
    $redisPort = ([Uri]$redisUrl).Port
    $pingResult = redis-cli -h $redisHost -p $redisPort PING 2>&1
    if ($pingResult -match "PONG") {
        Pass "Redis PING → PONG ($redisHost:$redisPort)"
    } else {
        Fail "Redis unreachable" "Expected PONG, got: $pingResult"
    }
}

# ─── Summary ─────────────────────────────────────────────────────────────────

Section "Summary"
Write-Host ""
Write-Host "  Passed:  $($script:passed)" -ForegroundColor Green
Write-Host "  Failed:  $($script:failed)" -ForegroundColor $(if ($script:failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Skipped: $($script:skipped)" -ForegroundColor Yellow
Write-Host ""

if ($script:failed -gt 0) {
    Write-Host "VERIFICATION FAILED — fix the errors above before deploying." -ForegroundColor Red
    exit 1
} else {
    Write-Host "VERIFICATION PASSED" -ForegroundColor Green
    exit 0
}
