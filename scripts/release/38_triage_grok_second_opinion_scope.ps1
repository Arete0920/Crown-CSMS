param(
  [string]$BaseDir = "audit-artifacts\prod-run-270-orderfix-verification\claude-second-opinion",
  [string]$InputFile = "GROK_RESPONSE_SCOPE_QUESTIONED.md"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$OutReview = Join-Path $BaseDir "GROK_RESPONSE_SCOPE_QUESTIONED.md"
$OutReport = Join-Path $BaseDir "03_GROK_SECOND_OPINION_SCOPE_TRIAGE.md"
$OutJson = Join-Path $BaseDir "03_grok_second_opinion_scope_triage.json"

$ExpectedTerms = @(
  "deploy-prod",
  "BUILD_SHA",
  "PROD_DEPLOY_TAG",
  "DEPLOY_RUN_ID",
  "25528614282",
  "500ec09461d583eaf309a852df16d510fb334c81",
  "prod-deploy-20260507-orderfix-195608",
  "/api/health",
  "/api/integrity",
  "runtime lineage",
  "app settings",
  "restart"
)

$OffScopeTerms = @(
  "duplicate charges",
  "fulfillments",
  "idempotency key",
  "compensation",
  "malformed orders",
  "order.fix.compensation",
  "financial operations",
  "retry storms"
)

function Contains-Term {
  param(
    [AllowEmptyString()][string]$Text,
    [Parameter(Mandatory=$true)][string]$Term
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return $false
  }

  return ($Text.IndexOf($Term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
}

if (-not (Test-Path $BaseDir)) {
  New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
}

$sourcePath = if ([System.IO.Path]::IsPathRooted($InputFile)) { $InputFile } else { Join-Path $BaseDir $InputFile }
if (-not (Test-Path $sourcePath)) {
  throw "Input file not found: $sourcePath"
}

$Review = Get-Content -Raw -Path $sourcePath
if ([string]::IsNullOrWhiteSpace($Review)) {
  throw "Input review file is empty: $sourcePath"
}

# Normalize: store canonical copy at fixed evidence path.
if ($sourcePath -ne $OutReview) {
  $Review | Out-File -FilePath $OutReview -Encoding utf8
}

$ExpectedHits = @()
foreach ($term in $ExpectedTerms) {
  if (Contains-Term $Review $term) {
    $ExpectedHits += $term
  }
}

$OffScopeHits = @()
foreach ($term in $OffScopeTerms) {
  if (Contains-Term $Review $term) {
    $OffScopeHits += $term
  }
}

$HasApprovedVerdict =
  (Contains-Term $Review "Overall Verdict: PASS") -or
  (Contains-Term $Review "Overall Verdict PASS") -or
  (Contains-Term $Review "Verdict: PASS") -or
  (Contains-Term $Review "Approved for production use") -or
  (Contains-Term $Review "APPROVED WITH MINOR CAVEATS") -or
  (Contains-Term $Review "Ship it") -or
  (Contains-Term $Review "Approved for production deployment")

$ScopeSpecificEnough = ($ExpectedHits.Count -ge 7) -and ($OffScopeHits.Count -eq 0)

$GateStatus = "SCOPE_CLARIFICATION_REQUIRED"
if ($ScopeSpecificEnough -and $HasApprovedVerdict) {
  $GateStatus = "PASS"
}

$Result = [ordered]@{
  generated_at = (Get-Date).ToString("o")
  review_file = $OutReview
  raw_grok_verdict_approved = $HasApprovedVerdict
  expected_scope_terms_found_count = $ExpectedHits.Count
  expected_scope_terms_found = $ExpectedHits
  off_scope_terms_found_count = $OffScopeHits.Count
  off_scope_terms_found = $OffScopeHits
  scope_specific_enough = $ScopeSpecificEnough
  gate_status = $GateStatus
  decision = if ($GateStatus -eq "PASS") {
    "Grok review can be treated as scope-aligned external review evidence."
  } else {
    "Grok review received, but do not use it as final gate closure until scope is corrected."
  }
}

$Result | ConvertTo-Json -Depth 10 |
  Out-File -FilePath $OutJson -Encoding utf8

$ExpectedRows = foreach ($term in $ExpectedTerms) {
  $hit = Contains-Term $Review $term
  "| $term | $hit |"
}

$OffScopeRows = foreach ($term in $OffScopeTerms) {
  $hit = Contains-Term $Review $term
  "| $term | $hit |"
}

$Report = @"
# Grok Second-Opinion Scope Triage

Generated: $((Get-Date).ToString("o"))

## Verdict

**$GateStatus**

## Raw Grok verdict detected

| Check | Result |
|---|---:|
| Approved-style verdict present | $HasApprovedVerdict |
| Expected scope terms found | $($ExpectedHits.Count) |
| Off-scope terms found | $($OffScopeHits.Count) |
| Scope-specific enough for gate closure | $ScopeSpecificEnough |

## Expected deploy/runtime scope terms

| Term | Found |
|---|---:|
$($ExpectedRows -join "`n")

## Off-scope terms

| Term | Found |
|---|---:|
$($OffScopeRows -join "`n")

## Decision

$($Result.decision)

## Required next step if not PASS

Ask Grok for a corrected review focused only on the deploy-prod workflow-ordering fix, run 270, app settings, restart, health/integrity runtime lineage, and production metadata proof.

Do not record this as final external-review closure unless the corrected review explicitly matches the deploy/runtime scope.
"@

$Report | Out-File -FilePath $OutReport -Encoding utf8

Write-Host ""
Write-Host "============================================================"
Write-Host "GROK SECOND-OPINION TRIAGE: $GateStatus"
Write-Host "Review: $OutReview"
Write-Host "Report: $OutReport"
Write-Host "JSON: $OutJson"
Write-Host "============================================================"
Write-Host ""

Get-Content $OutReport

if ($GateStatus -ne "PASS") {
  throw "Grok second-opinion scope triage did not pass. Review $OutReport."
}
