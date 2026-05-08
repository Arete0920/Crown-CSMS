$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackDir = "audit-artifacts\prod-run-270-orderfix-verification\claude-second-opinion"
$MainResponsePath = Join-Path $PackDir "CLAUDE_RESPONSE_MAIN.md"
$RedTeamResponsePath = Join-Path $PackDir "CLAUDE_RESPONSE_RED_TEAM.md"
$OutputReportPath = Join-Path $PackDir "01_CLAUDE_SECOND_OPINION_FINAL_REPORT.md"
$OutputJsonPath = Join-Path $PackDir "01_claude_second_opinion_final_result.json"

function Mark {
  param([bool]$Ok)
  if ($Ok) { return "PASS" }
  return "FAIL"
}

function ContainsText {
  param(
    [AllowEmptyString()][string]$Text,
    [Parameter(Mandatory=$true)][string]$Needle
  )

  if ([string]::IsNullOrEmpty($Text)) {
    return $false
  }

  return ($Text.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
}

if (-not (Test-Path $PackDir)) {
  throw "Pack directory missing: $PackDir"
}

$checks = [ordered]@{}
$checks["main_response_exists"] = Test-Path $MainResponsePath
$checks["red_team_response_exists"] = Test-Path $RedTeamResponsePath

$mainText = if ($checks["main_response_exists"]) { Get-Content -Raw -Path $MainResponsePath } else { "" }
$redText = if ($checks["red_team_response_exists"]) { Get-Content -Raw -Path $RedTeamResponsePath } else { "" }

$checks["main_mentions_pass"] = ContainsText -Text $mainText -Needle "PASS"
$checks["main_mentions_production_scope"] =
  ((ContainsText -Text $mainText -Needle "production deploy/runtime gate") -or
   (ContainsText -Text $mainText -Needle "production gate"))
$checks["main_includes_confidence"] = ContainsText -Text $mainText -Needle "confidence"
$checks["main_handles_unproven"] = ContainsText -Text $mainText -Needle "UNPROVEN"

$checks["red_mentions_no_unrefuted_blocker"] = ContainsText -Text $redText -Needle "NO_UNREFUTED_BLOCKER"
$checks["red_mentions_failure_modes"] =
  ((ContainsText -Text $redText -Needle "failure mode") -or
   (ContainsText -Text $redText -Needle "failure modes"))
$checks["red_marks_blocker_status"] =
  ((ContainsText -Text $redText -Needle "BLOCKER_FOUND") -or
   (ContainsText -Text $redText -Needle "NO_UNREFUTED_BLOCKER"))

$hasBlockerFoundToken = ContainsText -Text $redText -Needle "BLOCKER_FOUND"
$hasExplicitNoBlocker =
  ((ContainsText -Text $redText -Needle "BLOCKER_FOUND: no") -or
   (ContainsText -Text $redText -Needle "BLOCKER_FOUND = no") -or
   (ContainsText -Text $redText -Needle "BLOCKER_FOUND false") -or
   (ContainsText -Text $redText -Needle "BLOCKER_FOUND: false") -or
   (ContainsText -Text $redText -Needle "NO_UNREFUTED_BLOCKER"))

$checks["red_does_not_assert_blocker_found"] = ((-not $hasBlockerFoundToken) -or $hasExplicitNoBlocker)

$allPass = $true
foreach ($entry in $checks.GetEnumerator()) {
  if (-not [bool]$entry.Value) {
    $allPass = $false
  }
}

$overall = Mark $allPass
$generatedAt = (Get-Date).ToString("o")

$rows = New-Object System.Collections.Generic.List[string]
foreach ($entry in $checks.GetEnumerator()) {
  $rows.Add("| $($entry.Key) | $(Mark ([bool]$entry.Value)) |")
}

$decision = if ($allPass) {
  "External second-opinion review closure criteria are satisfied."
}
else {
  "External second-opinion review closure criteria are not yet satisfied."
}

$report = @"
# Claude Second-Opinion Finalization Report

Generated: $generatedAt

## Verdict

**$overall**

## Inputs

| Item | Path |
|---|---|
| Main response | $MainResponsePath |
| Red-team response | $RedTeamResponsePath |
| Output JSON | $OutputJsonPath |

## Checks

| Check | Result |
|---|---:|
$($rows -join "`n")

## Decision

$decision

## Scope boundary

This report closes only the external second-opinion review workflow for the production deploy/runtime gate evidence package. It does not independently close compliance, founder/product acceptance, controlled pilot authority, or GA authority.
"@

$json = [ordered]@{
  generated_at = $generatedAt
  verdict = $overall
  decision = $decision
  inputs = [ordered]@{
    main_response = $MainResponsePath
    red_team_response = $RedTeamResponsePath
  }
  checks = $checks
  scope = [ordered]@{
    production_deploy_runtime_second_opinion_workflow = "CLOSED_IF_PASS"
    pilot_or_ga_approval_implied = $false
  }
}

$report | Out-File -FilePath $OutputReportPath -Encoding utf8
($json | ConvertTo-Json -Depth 8) | Out-File -FilePath $OutputJsonPath -Encoding utf8

Write-Host "============================================================"
Write-Host "CLAUDE SECOND-OPINION FINALIZATION: $overall"
Write-Host "Report: $OutputReportPath"
Write-Host "JSON:   $OutputJsonPath"
Write-Host "============================================================"

Get-Content $OutputReportPath

if (-not $allPass) {
  throw "Second-opinion finalization failed. Review $OutputReportPath for failed checks."
}
