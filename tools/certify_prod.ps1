<#
.SYNOPSIS
    Pin certification tags to the correct SHAs and verify prod health.

.DESCRIPTION
    Enforces the doctrine:
        prod-certified-<date>  → SHA actually running in prod (from deploy tag)
        docs-certified-<date>  → proof packet HEAD (current main)

    Refuses to write tags unless:
        - /api/health build_sha matches the deploy tag SHA exactly
        - environment == prod
        - db == ok
        - ok == true

.PARAMETER DeployTag
    The existing deploy gate tag, e.g. prod-deploy-certify-2026-02-24

.PARAMETER Date
    The certification date suffix, e.g. 2026-02-24 (default: today)

.PARAMETER HealthUrl
    Override the health endpoint URL (default: https://crown-api-prod.azurewebsites.net/api/health/)

.PARAMETER Force
    Skip confirmation prompt.

.EXAMPLE
    .\tools\certify_prod.ps1 -DeployTag prod-deploy-certify-2026-02-24

.EXAMPLE
    .\tools\certify_prod.ps1 -DeployTag prod-deploy-certify-2026-02-24 -Force
#>

param(
    [Parameter(Mandatory)]
    [string]$DeployTag,

    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),

    [string]$HealthUrl = "https://crown-api-prod.azurewebsites.net/api/health/",

    [switch]$Force
)

$ErrorActionPreference = "Stop"

$prodCertTag   = "prod-certified-$Date"
$prodCertTagTs = "prod-certified-$Date-$(Get-Date -Format 'HHmm')"  # immutable: never force-move this tag
$docsCertTag   = "docs-certified-$Date"

Write-Host ""
Write-Host "=== CROWN2026 CERTIFICATION SCRIPT ===" -ForegroundColor Cyan
Write-Host "DeployTag:    $DeployTag"
Write-Host "ProdCertTag:  $prodCertTag"
Write-Host "DocsCertTag:  $docsCertTag"
Write-Host "HealthUrl:    $HealthUrl"
Write-Host ""

# ── 1. Resolve deploy SHA ──────────────────────────────────────────────────
Write-Host "Step 1: Resolving deploy SHA from tag..." -ForegroundColor Cyan
$deploySha = (git rev-parse $DeployTag 2>&1).Trim()
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Tag '$DeployTag' not found locally. Run: git fetch --tags --force" -ForegroundColor Red
    exit 1
}
Write-Host "  DEPLOY_SHA: $deploySha" -ForegroundColor Green

# ── 2. Resolve docs SHA (current main HEAD) ────────────────────────────────
Write-Host "Step 2: Resolving docs SHA from main HEAD..." -ForegroundColor Cyan
$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne "main") {
    Write-Host "ERROR: Not on main branch (currently on '$currentBranch'). Run: git checkout main && git pull --ff-only" -ForegroundColor Red
    exit 1
}
$docsSha = (git rev-parse HEAD).Trim()
Write-Host "  DOCS_SHA: $docsSha" -ForegroundColor Green

# ── 3. Fetch and assert prod health ───────────────────────────────────────
Write-Host "Step 3: Verifying prod health..." -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod $HealthUrl -TimeoutSec 15
} catch {
    Write-Host "ERROR: Health endpoint unreachable: $_" -ForegroundColor Red
    exit 1
}

$healthBuildSha  = $h.build_sha
$healthEnv       = if ($h.environment) { $h.environment } elseif ($h.env) { $h.env } else { "" }
$healthDb        = $h.db
$healthOk        = $h.ok

Write-Host ""
Write-Host "  build_sha:       $healthBuildSha"
Write-Host "  environment:     $healthEnv"
Write-Host "  db:              $healthDb"
Write-Host "  ok:              $healthOk"
Write-Host ""

$fail = $false

if ($healthBuildSha -ne $deploySha) {
    Write-Host "FAIL: build_sha ($healthBuildSha) != deploy SHA ($deploySha)" -ForegroundColor Red
    Write-Host "      Prod is not running the expected code. Re-deploy first." -ForegroundColor Red
    $fail = $true
}
if ($healthEnv -ne "prod") {
    Write-Host "FAIL: environment is '$healthEnv', expected 'prod'" -ForegroundColor Red
    $fail = $true
}
if ($healthDb -ne "ok") {
    Write-Host "FAIL: db is '$healthDb', expected 'ok'" -ForegroundColor Red
    $fail = $true
}
if (-not $healthOk) {
    Write-Host "FAIL: ok is not true" -ForegroundColor Red
    $fail = $true
}

if ($fail) {
    Write-Host ""
    Write-Host "Certification BLOCKED. Fix failures above before tagging." -ForegroundColor Red
    exit 1
}

Write-Host "  All health assertions PASS." -ForegroundColor Green

# ── 4. Confirm intent ─────────────────────────────────────────────────────
if (-not $Force) {
    Write-Host ""
    Write-Host "About to push:" -ForegroundColor Yellow
    Write-Host "  $prodCertTag   -> $deploySha (force-moveable: latest that day)"
    Write-Host "  $prodCertTagTs -> $deploySha (immutable: intra-day record)"
    Write-Host "  $docsCertTag   -> $docsSha"
    Write-Host ""
    Write-Host "Confirm? (type 'yes' to continue)"
    $confirm = Read-Host
    if ($confirm -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# ── 5. Write tags ──────────────────────────────────────────────────────────
Write-Host "Step 4: Writing tags..." -ForegroundColor Cyan

git tag -f $prodCertTag $deploySha
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to set $prodCertTag" -ForegroundColor Red; exit 1 }
git push -f origin $prodCertTag
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to push $prodCertTag" -ForegroundColor Red; exit 1 }

# Timestamped tag — no -f. If it already exists, the push will fail loudly.
# RULE: Never force-move prod-certified-YYYY-MM-DD-HHMM. If wrong, create a
#       correction tag (e.g. prod-certified-...-CORRECTED) and document why.
git tag $prodCertTagTs $deploySha
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to set $prodCertTagTs (already exists?)" -ForegroundColor Red; exit 1 }
git push origin $prodCertTagTs
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to push $prodCertTagTs" -ForegroundColor Red; exit 1 }

git tag -f $docsCertTag $docsSha
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to set $docsCertTag" -ForegroundColor Red; exit 1 }
git push -f origin $docsCertTag
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Failed to push $docsCertTag" -ForegroundColor Red; exit 1 }

# ── 6. Final proof table ──────────────────────────────────────────────────
Write-Host ""
Write-Host "=== CERTIFICATION COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Tag                          SHA"
Write-Host "  ─────────────────────────────────────────────────────────────"
Write-Host "  $prodCertTag   $((git rev-parse $prodCertTag).Trim())"
  Write-Host "  $prodCertTagTs $((git rev-parse $prodCertTagTs).Trim()) [immutable]"
  Write-Host "  $docsCertTag   $((git rev-parse $docsCertTag).Trim())"
Write-Host ""
Write-Host "  Prod health:"
Write-Host "    build_sha:   $healthBuildSha"
Write-Host "    environment: $healthEnv"
Write-Host "    db:          $healthDb"
Write-Host "    ok:          $healthOk"
Write-Host ""
Write-Host "  SHA_MATCH: PASS ($prodCertTag == build_sha)" -ForegroundColor Green
Write-Host ""
Write-Host "Rule: prod-certified-* = what is running. docs-certified-* = proof packet." -ForegroundColor DarkGray
