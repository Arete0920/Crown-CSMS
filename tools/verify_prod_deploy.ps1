<#
.SYNOPSIS
  Verifies that a prod-deploy-* tag is deployed and /health/ reports the correct build_sha.

.DESCRIPTION
  1. Validates the tag exists locally (git must have it).
  2. Pushes the tag to origin — this triggers deploy-prod.yml (push.tags: prod-deploy-*).
  3. Waits for the GitHub Actions deploy-prod.yml run to appear and complete.
  4. Polls /health/ until build_sha matches the commit SHA the tag points to.
  Fails hard at any step.

.PARAMETER Tag
  The prod-deploy-* tag to push and verify (e.g. prod-deploy-v0.5.0).

.PARAMETER HealthUrl
  URL of the production health endpoint (e.g. https://crown-api-prod.azurewebsites.net/health/).

.PARAMETER TimeoutSeconds
  Max seconds to wait for health SHA match after deploy workflow succeeds. Default 300.

.EXAMPLE
  .\tools\verify_prod_deploy.ps1 -Tag prod-deploy-v0.5.0 -HealthUrl https://crown-api-prod.azurewebsites.net/health/
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$Tag,

  [Parameter(Mandatory = $true)]
  [string]$HealthUrl,

  [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
$env:GH_PAGER = "cat"

function Fail([string]$msg) {
  Write-Host "VERIFY=FAIL  $msg" -ForegroundColor Red
  exit 1
}

function Step([string]$msg) {
  Write-Host "`n== $msg ==" -ForegroundColor Cyan
}

Write-Host "CROWN PROD DEPLOY VERIFIER" -ForegroundColor Green
Write-Host "Tag        : $Tag"
Write-Host "HealthUrl  : $HealthUrl"
Write-Host "Timeout    : $TimeoutSeconds sec"

# ── 1) Validate tag format ───────────────────────────────────────────────────
Step "Validate tag"
if ($Tag -notmatch "^prod-deploy-") {
  Fail "Tag must start with 'prod-deploy-' (got: $Tag)"
}

# ── 2) Resolve tag SHA locally ───────────────────────────────────────────────
Step "Resolve tag SHA"
git fetch --tags --quiet
$tagSha = (git rev-list -n 1 $Tag 2>$null).Trim()
if ([string]::IsNullOrEmpty($tagSha) -or $tagSha.Length -lt 40) {
  Fail "Tag '$Tag' not found or could not resolve to a commit SHA. Run: git tag $Tag <commit> && git push origin $Tag"
}
$tagShaShort = $tagSha.Substring(0, 7)
Write-Host "Tag SHA    : $tagSha"
Write-Host "Short SHA  : $tagShaShort" -ForegroundColor Green

# ── 3) Push tag to origin (triggers deploy-prod.yml via push.tags) ───────────
Step "Push tag to origin"
$already = (git ls-remote origin "refs/tags/$Tag" 2>$null).Trim()
if ($already) {
  Write-Host "Tag already on origin — skipping push (workflow may already be running or ran)."
} else {
  Write-Host "Pushing $Tag to origin..."
  git push origin $Tag
  Write-Host "Tag pushed." -ForegroundColor Green
}

# ── 4) Wait for deploy-prod.yml run triggered by this tag ────────────────────
Step "Wait for deploy-prod workflow run"
$runId = $null
$deadline = (Get-Date).AddSeconds(120)

while ((Get-Date) -lt $deadline) {
  try {
    $runs = gh run list --workflow="deploy-prod.yml" --repo Arete0920/Crown-CSMS --limit 5 `
      --json databaseId,status,conclusion,headSha,headBranch,event,createdAt 2>$null | ConvertFrom-Json
    $match = $runs | Where-Object { $_.headSha -eq $tagSha -or $_.headBranch -eq $Tag }
    if ($match) {
      $runId = $match[0].databaseId
      Write-Host "Found run: $runId  status=$($match[0].status)" -ForegroundColor Green
      break
    }
  } catch { }
  Write-Host "Waiting for workflow run to appear..."
  Start-Sleep -Seconds 10
}

if (-not $runId) {
  # Fallback: just grab the most recent run and warn
  $runs = gh run list --workflow="deploy-prod.yml" --repo Arete0920/Crown-CSMS --limit 1 `
    --json databaseId,status,conclusion,headSha | ConvertFrom-Json
  if ($runs -and $runs[0]) {
    $runId = $runs[0].databaseId
    Write-Host "WARNING: Could not match run by SHA. Using most recent run: $runId" -ForegroundColor Yellow
  } else {
    Fail "No deploy-prod.yml workflow run found. Check that the tag push triggered the workflow."
  }
}

# ── 5) Watch run to completion ───────────────────────────────────────────────
Step "Watch deploy workflow run $runId"
gh run watch $runId --repo Arete0920/Crown-CSMS | Out-Host

$final = gh run view $runId --repo Arete0920/Crown-CSMS --json status,conclusion,headSha | ConvertFrom-Json
if ($final.conclusion -ne "success") {
  Fail "Deploy workflow failed. conclusion=$($final.conclusion)  See: https://github.com/Arete0920/Crown-CSMS/actions/runs/$runId"
}
Write-Host "Workflow complete: conclusion=$($final.conclusion)" -ForegroundColor Green

# ── 6) Poll /health/ until build_sha matches ─────────────────────────────────
Step "Poll health endpoint for build_sha=$tagShaShort"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$attempt = 0

while ((Get-Date) -lt $deadline) {
  $attempt++
  try {
    $resp = Invoke-RestMethod -Uri $HealthUrl -Method GET `
      -Headers @{ "Accept" = "application/json" } -TimeoutSec 15
    $sha = "$($resp.build_sha)".Trim()
    $status = $resp.status
    Write-Host "[#$attempt] status=$status  build_sha=$sha"

    # Accept: full sha match, or 7-char short sha match (what build_info.py bakes in)
    if ($sha -and (
      $sha -eq $tagSha -or
      $sha -eq $tagShaShort -or
      $tagSha.StartsWith($sha) -or
      $sha.StartsWith($tagShaShort)
    )) {
      Write-Host "`nVERIFY=PASS  build_sha matches tag SHA" -ForegroundColor Green
      Write-Host "  tag        = $Tag"
      Write-Host "  tag SHA    = $tagSha"
      Write-Host "  health SHA = $sha"
      exit 0
    }
  } catch {
    Write-Host "[#$attempt] health probe error: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 10
}

Fail "Timed out after ${TimeoutSeconds}s. health build_sha did not match tag SHA $tagShaShort.`nCheck $HealthUrl manually."
