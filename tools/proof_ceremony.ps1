<#
.SYNOPSIS
    Phase 7C — Crown Proof Ceremony.

    Resolves a git tag to its full commit SHA, then asserts that:
      - The backend /api/health/ reports that exact SHA and the tag name via prod_deploy_tag
      - The frontend /build.json (baked at Vite build time) reports the same 7-char SHA and tag

    Exits 0 on PASS, exits 1 on FAIL.
    Prints structured evidence lines on every run regardless of outcome.

.PARAMETER Tag
    Git tag to prove (e.g. phase7b-deploy-contract-2026-02-23).

.PARAMETER ApiBase
    Backend base URL (e.g. https://crown-api-prod.azurewebsites.net).
    The script appends /api/health/ automatically.

.PARAMETER DashBase
    Frontend base URL (e.g. https://crown-dash.azurewebsites.net).
    The script appends /build.json automatically.
    If empty or omitted, the UI check is skipped and UI_FOOTER_SHA/UI_FOOTER_TAG print SKIP.

.EXAMPLE
    ./tools/proof_ceremony.ps1 `
        -Tag  "phase7b-deploy-contract-2026-02-23" `
        -ApiBase  "https://crown-api-prod.azurewebsites.net" `
        -DashBase "https://crown-dash.azurewebsites.net"
#>
param(
    [Parameter(Mandatory=$true)]  [string]$Tag,
    [Parameter(Mandatory=$true)]  [string]$ApiBase,
    [Parameter(Mandatory=$false)] [string]$DashBase = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Guard: fail loud immediately if ApiBase is missing or not a URL.
# Without this, an empty PROD_API_BASE secret produces a cryptic
# "The format of the URI could not be determined" error that looks
# like a network failure rather than a configuration problem.
if (-not $ApiBase -or $ApiBase -notmatch '^https?://') {
    Write-Host "RESULT=FAIL" -ForegroundColor Red
    Write-Host "FAIL: -ApiBase is empty or not a valid URL (got: '$ApiBase')" -ForegroundColor Red
    Write-Host "      Set the PROD_API_BASE repo secret to the backend prod URL." -ForegroundColor Red
    Write-Host "      Example: https://crown-api-prod.azurewebsites.net" -ForegroundColor Red
    exit 1
}

$failures = [System.Collections.Generic.List[string]]::new()

function Fail([string]$msg) {
    Write-Host "FAIL: $msg" -ForegroundColor Red
    $script:failures.Add($msg)
}
function Ok([string]$msg)   { Write-Host "OK:   $msg" -ForegroundColor Green }
function Info([string]$msg) { Write-Host "INFO: $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " CROWN PROOF CEREMONY (Phase 7C)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ─── Step 1: Resolve tag → full commit SHA ──────────────────────────────────────
Info "Resolving tag: $Tag"

$tagSha = ""
try {
    $raw = & git rev-list -n 1 $Tag 2>&1
    if ($raw -notmatch "fatal") { $tagSha = $raw.Trim() }
} catch { $tagSha = "" }

if (-not $tagSha -or $tagSha.Length -lt 40) {
    Fail "Cannot resolve tag '$Tag' to a 40-char commit SHA — is the tag fetched? (git fetch --tags)"
    $tagSha = "UNKNOWN"
}

$tagShaShort = if ($tagSha -ne "UNKNOWN") { $tagSha.Substring(0, 7) } else { "UNKNOWN" }

Write-Host "TAG=$Tag"
Write-Host "TAG_SHA=$tagSha"

# ─── Step 2: Probe backend /api/health/ ─────────────────────────────────────────
$healthUrl = ($ApiBase.TrimEnd("/")) + "/api/health/"
Info "Probing: $healthUrl"

$healthBody = $null
try {
    $resp = Invoke-WebRequest -Uri $healthUrl -Method GET -UseBasicParsing -TimeoutSec 25 -ErrorAction Stop
    if ($resp.StatusCode -ne 200) {
        Fail "Health endpoint returned HTTP $($resp.StatusCode) (expected 200)"
    } else {
        $healthBody = $resp.Content | ConvertFrom-Json
    }
} catch {
    Fail "Health endpoint unreachable: $($_.Exception.Message)"
}

$healthSha = if ($null -ne $healthBody -and $null -ne $healthBody.build_sha)      { [string]$healthBody.build_sha }      else { "" }
$healthTag = if ($null -ne $healthBody -and $null -ne $healthBody.prod_deploy_tag) { [string]$healthBody.prod_deploy_tag } else { "" }

if (-not $healthSha) { Fail "health response missing 'build_sha' field" }
if (-not $healthTag) { Fail "health response missing 'prod_deploy_tag' field — was PROD_DEPLOY_TAG set at deploy time?" }

Write-Host "HEALTH_SHA=$healthSha"
Write-Host "HEALTH_TAG=$healthTag"

# ─── Step 3: Assert backend SHA == tag SHA ───────────────────────────────────────
if ($healthSha -and $tagSha -ne "UNKNOWN") {
    # Accept: full-SHA match, or health returns a 7+ char prefix that starts tagSha
    $shaOk = ($healthSha -eq $tagSha) -or
             ($tagSha.StartsWith($healthSha) -and $healthSha.Length -ge 7) -or
             ($healthSha.StartsWith($tagSha.Substring(0, [Math]::Min(8, $tagSha.Length))))
    if ($shaOk) {
        Ok "build_sha matches tag SHA ($tagShaShort)"
    } else {
        Fail "build_sha mismatch — health='$healthSha'  tag='$tagSha'"
    }
}

# ─── Step 4: Assert backend prod_deploy_tag == $Tag ─────────────────────────────
if ($healthTag) {
    if ($healthTag -eq $Tag) {
        Ok "prod_deploy_tag matches ($healthTag)"
    } else {
        Fail "prod_deploy_tag mismatch — health='$healthTag'  expected='$Tag'"
    }
}

# ─── Step 5: UI /build.json check ────────────────────────────────────────────────
$uiSha = "SKIP"
$uiTag = "SKIP"

if ($DashBase) {
    $buildJsonUrl = ($DashBase.TrimEnd("/")) + "/build.json"
    Info "Probing: $buildJsonUrl"
    try {
        $uiResp = Invoke-WebRequest -Uri $buildJsonUrl -Method GET -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        if ($uiResp.StatusCode -ne 200) {
            Fail "UI /build.json returned HTTP $($uiResp.StatusCode) (expected 200)"
        } else {
            $uiJson = $uiResp.Content | ConvertFrom-Json
            $uiSha = if ($null -ne $uiJson.build_sha)  { [string]$uiJson.build_sha }  else { "" }
            $uiTag = if ($null -ne $uiJson.deploy_tag) { [string]$uiJson.deploy_tag } else { "" }

            if (-not $uiSha) { Fail "UI /build.json missing 'build_sha' field" }
            if (-not $uiTag) { Fail "UI /build.json missing 'deploy_tag' field" }

            # UI SHA is baked as 7-char short at build time (github.sha[:7] via VITE_BUILD_SHA)
            if ($uiSha -and $tagSha -ne "UNKNOWN") {
                if (($tagSha.StartsWith($uiSha) -and $uiSha.Length -ge 7) -or $uiSha -eq $tagShaShort) {
                    Ok "UI build_sha ($uiSha) matches tag SHA short ($tagShaShort)"
                } else {
                    Fail "UI build_sha mismatch — ui='$uiSha'  expected tag prefix='$tagShaShort'"
                }
            }

            if ($uiTag) {
                if ($uiTag -eq $Tag) {
                    Ok "UI deploy_tag matches ($uiTag)"
                } else {
                    Fail "UI deploy_tag mismatch — ui='$uiTag'  expected='$Tag'"
                }
            }
        }
    } catch {
        Fail "UI /build.json unreachable: $($_.Exception.Message)"
    }
} else {
    Info "DashBase not provided — UI /build.json check skipped (pass -DashBase <url> to enable)"
}

Write-Host "UI_FOOTER_SHA=$uiSha"
Write-Host "UI_FOOTER_TAG=$uiTag"

# ─── Final result ────────────────────────────────────────────────────────────────
Write-Host ""
if ($failures.Count -eq 0) {
    Write-Host "RESULT=PASS" -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Host "RESULT=FAIL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Failures ($($failures.Count)):" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
}
