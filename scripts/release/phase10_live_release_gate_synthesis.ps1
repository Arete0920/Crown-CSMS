$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)
    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase10"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$phase2Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase2\phase2_release_truth_reconciliation.json"
$phase4Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase4\phase4_backend_verification_and_django_proof.json"
$phase5Csv = Join-Path $script:RepoRoot "docs\release\live-audit\phase5\phase5_module_proof_matrix.csv"
$phase6Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase6\phase6_evidence_index_and_action_register.json"
$phase7Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase7\phase7_runtime_and_api_surface_verification.json"
$phase8Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase8\phase8_frontend_and_dashboard_proof.json"
$phase9Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase9\phase9_reporting_export_pdf_transcript_gap_audit.json"

$required = @($phase2Json, $phase4Json, $phase5Csv, $phase6Json, $phase7Json, $phase8Json, $phase9Json)
foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        throw "Required artifact missing: $file"
    }
}

$phase2 = Get-Content -Path $phase2Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase4 = Get-Content -Path $phase4Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase5 = @(Import-Csv -Path $phase5Csv)
$phase6 = Get-Content -Path $phase6Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase7 = Get-Content -Path $phase7Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase8 = Get-Content -Path $phase8Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase9 = Get-Content -Path $phase9Json -Raw -Encoding UTF8 | ConvertFrom-Json

$phase4Summary = if ($phase4.PSObject.Properties.Name -contains 'summary') { $phase4.summary } else { $phase4 }
$phase6Summary = if ($phase6.PSObject.Properties.Name -contains 'summary') { $phase6.summary } else { $phase6 }
$phase7Summary = if ($phase7.PSObject.Properties.Name -contains 'summary') { $phase7.summary } else { $phase7 }
$phase8Summary = if ($phase8.PSObject.Properties.Name -contains 'summary') { $phase8.summary } else { $phase8 }
$phase9Summary = if ($phase9.PSObject.Properties.Name -contains 'summary') { $phase9.summary } else { $phase9 }

$truthScore = 100 - (15 * [int]$phase2.mismatch_count)
if ($truthScore -lt 0) { $truthScore = 0 }

$backendScore = 0
if ($phase4Summary.python_version_ok) { $backendScore += 10 }
if ($phase4Summary.django_import_ok) { $backendScore += 20 }
if ($phase4Summary.manage_check_ok) { $backendScore += 35 }
if ($phase4Summary.manage_check_deploy_ok) { $backendScore += 15 }
if ($phase4Summary.showmigrations_ok) { $backendScore += 20 }
if ($backendScore -gt 100) { $backendScore = 100 }

$moduleScore = 0
if ($phase5.Count -gt 0) {
    $moduleScore = [int][math]::Round((($phase5 | Measure-Object -Property proof_score -Average).Average), 0)
}

$runtimeScore = 0
if ([int]$phase7Summary.endpoint_count -gt 0) {
    $runtimeScore = [int][math]::Round((100.0 * [int]$phase7Summary.endpoint_success_count / [int]$phase7Summary.endpoint_count), 0)
}
if ([int]$phase7Summary.url_hit_count -gt 0 -and $runtimeScore -lt 40) {
    $runtimeScore = 40
}

$frontendScore = 0
if ($phase8Summary.node_available) { $frontendScore += 15 }
if ([int]$phase8Summary.package_count -gt 0) { $frontendScore += 20 }
if ([int]$phase8Summary.dashboard_file_count -gt 0) { $frontendScore += 20 }
if ([int]$phase8Summary.route_file_count -gt 0) { $frontendScore += 15 }
if ([int]$phase8Summary.component_file_count -gt 0) { $frontendScore += 10 }
if ([int]$phase8Summary.build_attempt_count -gt 0) {
    $frontendScore += [int][math]::Round((20.0 * [int]$phase8Summary.build_success_count / [int]$phase8Summary.build_attempt_count), 0)
}
if ($frontendScore -gt 100) { $frontendScore = 100 }

$reportingScore = [int]$phase9Summary.reporting_score

$actionPenalty = (10 * [int]$phase6Summary.high_priority_count) + (4 * [int]$phase6Summary.medium_priority_count)
$actionScore = 100 - $actionPenalty
if ($actionScore -lt 0) { $actionScore = 0 }

$weightedScore = ($truthScore * 0.15) + ($backendScore * 0.20) + ($moduleScore * 0.20) + ($runtimeScore * 0.10) + ($frontendScore * 0.10) + ($reportingScore * 0.15) + ($actionScore * 0.10)
$overallScore = [int][math]::Round($weightedScore, 0)

$overallStatus = if ($overallScore -ge 90) {
    "RELEASE_READY"
} elseif ($overallScore -ge 80) {
    "NEAR_READY"
} elseif ($overallScore -ge 70) {
    "PARTIAL"
} else {
    "NOT_READY"
}

$gateRows = @(
    [pscustomobject]@{ gate = "release_truth"; score = $truthScore; status = if ($truthScore -ge 80) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "backend_verification"; score = $backendScore; status = if ($backendScore -ge 80) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "module_proof"; score = $moduleScore; status = if ($moduleScore -ge 75) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "runtime_api"; score = $runtimeScore; status = if ($runtimeScore -ge 70) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "frontend_dashboard"; score = $frontendScore; status = if ($frontendScore -ge 70) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "reporting_export"; score = $reportingScore; status = if ($reportingScore -ge 70) { "PASS" } else { "ACTION" } },
    [pscustomobject]@{ gate = "action_register"; score = $actionScore; status = if ($actionScore -ge 70) { "PASS" } else { "ACTION" } }
)

$scoreCsv = Join-Path $outDir "phase10_live_release_gate_scorecard.csv"
$summaryJson = Join-Path $outDir "phase10_live_release_gate_synthesis.json"
$summaryMd = Join-Path $outDir "phase10_live_release_gate_synthesis.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_GATE_STATUS.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_GATE_STATUS.json"

$gateRows | Export-Csv -Path $scoreCsv -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    generated_at_utc      = (Get-Date).ToUniversalTime().ToString("o")
    overall_score         = $overallScore
    overall_status        = $overallStatus
    release_truth_score   = $truthScore
    backend_score         = $backendScore
    module_score          = $moduleScore
    runtime_score         = $runtimeScore
    frontend_score        = $frontendScore
    reporting_score       = $reportingScore
    action_score          = $actionScore
    high_priority_actions = [int]$phase6Summary.high_priority_count
    medium_priority_actions = [int]$phase6Summary.medium_priority_count
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    gates            = $gateRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$gateLines = ($gateRows | ForEach-Object {
    "- $($_.gate) | score=$($_.score) | status=$($_.status)"
}) -join "`r`n"

$markdown = @"
# LIVE RELEASE GATE STATUS

Generated UTC: $($summary.generated_at_utc)

## Overall
- overall score: $($summary.overall_score)
- overall status: $($summary.overall_status)
- high priority actions: $($summary.high_priority_actions)
- medium priority actions: $($summary.medium_priority_actions)

## Gate Scores
$gateLines

## Source Artifacts
- docs/release/live-audit/phase10/phase10_live_release_gate_scorecard.csv
- docs/release/live-audit/phase2/phase2_release_truth_reconciliation.json
- docs/release/live-audit/phase4/phase4_backend_verification_and_django_proof.json
- docs/release/live-audit/phase5/phase5_module_proof_matrix.csv
- docs/release/live-audit/phase6/phase6_evidence_index_and_action_register.json
- docs/release/live-audit/phase7/phase7_runtime_and_api_surface_verification.json
- docs/release/live-audit/phase8/phase8_frontend_and_dashboard_proof.json
- docs/release/live-audit/phase9/phase9_reporting_export_pdf_transcript_gap_audit.json
"@

Set-Content -Path $liveMd -Value $markdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 10 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live release gate status: $liveMd"
Write-Host ""
