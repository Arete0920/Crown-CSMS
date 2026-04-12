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

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase15"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$gateJson = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_GATE_STATUS.json"
$checklistJson = Join-Path $script:RepoRoot "docs\release\LIVE_FINAL_SIGNOFF_CHECKLIST.json"
$hygieneJson = Join-Path $script:RepoRoot "docs\release\LIVE_REPO_HYGIENE_PLAN.json"
$workflowJson = Join-Path $script:RepoRoot "docs\release\LIVE_WORKFLOW_CANONICALIZATION_PLAN.json"
$packetJson = Join-Path $script:RepoRoot "docs\release\LIVE_EVIDENCE_PACKET.json"

$required = @($gateJson, $checklistJson, $hygieneJson, $workflowJson, $packetJson)
foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        throw "Required artifact missing: $file"
    }
}

$gateDoc = Get-Content -Path $gateJson -Raw -Encoding UTF8 | ConvertFrom-Json
$checklistDoc = Get-Content -Path $checklistJson -Raw -Encoding UTF8 | ConvertFrom-Json
$hygieneDoc = Get-Content -Path $hygieneJson -Raw -Encoding UTF8 | ConvertFrom-Json
$workflowDoc = Get-Content -Path $workflowJson -Raw -Encoding UTF8 | ConvertFrom-Json
$packetDoc = Get-Content -Path $packetJson -Raw -Encoding UTF8 | ConvertFrom-Json

$overallStatus = [string]$gateDoc.summary.overall_status
$overallScore = [int]$gateDoc.summary.overall_score
$checklistPercent = [int]$checklistDoc.summary.checklist_percent
$remoteDeleteCount = [int]$hygieneDoc.summary.remote_delete_count
$localDeleteCount = [int]$hygieneDoc.summary.local_delete_count
$archiveCandidateCount = [int]$workflowDoc.summary.archive_candidate_count
$packetReady = ([int]$packetDoc.summary.copied_count -gt 0)

$shipDecision = "HOLD"
if (
    $overallStatus -eq "RELEASE_READY" -and
    $checklistPercent -ge 95 -and
    $remoteDeleteCount -eq 0 -and
    $localDeleteCount -eq 0 -and
    $archiveCandidateCount -eq 0 -and
    $packetReady
) {
    $shipDecision = "SHIP"
} elseif (
    $overallStatus -in @("RELEASE_READY","NEAR_READY") -and
    $checklistPercent -ge 80 -and
    $packetReady
) {
    $shipDecision = "NEAR_READY_HOLD"
}

$phaseChecks = @(
    [pscustomobject]@{ phase = 1;  name = "live_repo_baseline";                        path = "docs/release/live-audit/phase1/phase1_live_repo_baseline.json";                        complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase1\phase1_live_repo_baseline.json")) },
    [pscustomobject]@{ phase = 2;  name = "release_truth_reconciliation";              path = "docs/release/live-audit/phase2/phase2_release_truth_reconciliation.json";              complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase2\phase2_release_truth_reconciliation.json")) },
    [pscustomobject]@{ phase = 3;  name = "workflow_branch_rationalization";           path = "docs/release/live-audit/phase3/phase3_workflow_branch_rationalization.json";           complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_workflow_branch_rationalization.json")) },
    [pscustomobject]@{ phase = 4;  name = "backend_verification_and_django_proof";     path = "docs/release/live-audit/phase4/phase4_backend_verification_and_django_proof.json";     complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase4\phase4_backend_verification_and_django_proof.json")) },
    [pscustomobject]@{ phase = 5;  name = "module_proof_matrix";                       path = "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv";                         complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase5\phase5_module_proof_matrix.csv")) },
    [pscustomobject]@{ phase = 6;  name = "evidence_index_and_action_register";        path = "docs/release/live-audit/phase6/phase6_evidence_index_and_action_register.json";        complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase6\phase6_evidence_index_and_action_register.json")) },
    [pscustomobject]@{ phase = 7;  name = "runtime_and_api_surface_verification";      path = "docs/release/live-audit/phase7/phase7_runtime_and_api_surface_verification.json";      complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase7\phase7_runtime_and_api_surface_verification.json")) },
    [pscustomobject]@{ phase = 8;  name = "frontend_and_dashboard_proof";              path = "docs/release/live-audit/phase8/phase8_frontend_and_dashboard_proof.json";              complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase8\phase8_frontend_and_dashboard_proof.json")) },
    [pscustomobject]@{ phase = 9;  name = "reporting_export_pdf_transcript_gap_audit"; path = "docs/release/live-audit/phase9/phase9_reporting_export_pdf_transcript_gap_audit.json"; complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase9\phase9_reporting_export_pdf_transcript_gap_audit.json")) },
    [pscustomobject]@{ phase = 10; name = "live_release_gate_synthesis";               path = "docs/release/live-audit/phase10/phase10_live_release_gate_synthesis.json";             complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase10\phase10_live_release_gate_synthesis.json")) },
    [pscustomobject]@{ phase = 11; name = "live_release_docs_refresh";                 path = "docs/release/live-audit/phase11/phase11_live_release_docs_refresh.json";               complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase11\phase11_live_release_docs_refresh.json")) },
    [pscustomobject]@{ phase = 12; name = "repo_hygiene_execution_pack";               path = "docs/release/live-audit/phase12/phase12_repo_hygiene_execution_pack.json";             complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase12\phase12_repo_hygiene_execution_pack.json")) },
    [pscustomobject]@{ phase = 13; name = "workflow_canonicalization_plan";            path = "docs/release/live-audit/phase13/phase13_workflow_canonicalization_plan.json";          complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase13\phase13_workflow_canonicalization_plan.json")) },
    [pscustomobject]@{ phase = 14; name = "live_evidence_pack_builder";                path = "docs/release/live-audit/phase14/phase14_live_evidence_pack_builder.json";              complete = (Test-Path (Join-Path $script:RepoRoot "docs\release\live-audit\phase14\phase14_live_evidence_pack_builder.json")) },
    [pscustomobject]@{ phase = 15; name = "final_ship_decision_and_completion";        path = "docs/release/live-audit/phase15/phase15_final_ship_decision_and_completion.json";      complete = $true }
)

$phaseCompletionPercent = [int][math]::Round((100.0 * (@($phaseChecks | Where-Object { $_.complete }).Count) / @($phaseChecks).Count), 0)

$shipMd = Join-Path $script:RepoRoot "docs\release\LIVE_SHIP_DECISION.md"
$shipJson = Join-Path $script:RepoRoot "docs\release\LIVE_SHIP_DECISION.json"
$completionMd = Join-Path $script:RepoRoot "docs\release\LIVE_15_PHASE_COMPLETION.md"
$completionJson = Join-Path $script:RepoRoot "docs\release\LIVE_15_PHASE_COMPLETION.json"
$phaseSummaryJson = Join-Path $outDir "phase15_final_ship_decision_and_completion.json"
$phaseSummaryMd = Join-Path $outDir "phase15_final_ship_decision_and_completion.md"
$phaseCsv = Join-Path $outDir "phase15_completion_matrix.csv"

$phaseChecks | Export-Csv -Path $phaseCsv -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    generated_at_utc             = (Get-Date).ToUniversalTime().ToString("o")
    ship_decision                = $shipDecision
    overall_score                = $overallScore
    overall_status               = $overallStatus
    checklist_percent            = $checklistPercent
    remote_delete_count          = $remoteDeleteCount
    local_delete_count           = $localDeleteCount
    workflow_archive_candidates  = $archiveCandidateCount
    packet_ready                 = $packetReady
    phase_completion_percent     = $phaseCompletionPercent
}

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
} | ConvertTo-Json -Depth 6 | Set-Content -Path $shipJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    phases           = $phaseChecks
} | ConvertTo-Json -Depth 8 | Set-Content -Path $completionJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    phases           = $phaseChecks
} | ConvertTo-Json -Depth 8 | Set-Content -Path $phaseSummaryJson -Encoding UTF8

$phaseLines = ($phaseChecks | ForEach-Object {
    "- phase $($_.phase) | $($_.name) | complete=$($_.complete) | path=$($_.path)"
}) -join "`r`n"

$shipMarkdown = @"
# LIVE SHIP DECISION

Generated UTC: $($summary.generated_at_utc)

## Decision
- ship decision: $($summary.ship_decision)
- overall score: $($summary.overall_score)
- overall status: $($summary.overall_status)
- checklist percent: $($summary.checklist_percent)
- remote delete count: $($summary.remote_delete_count)
- local delete count: $($summary.local_delete_count)
- workflow archive candidates: $($summary.workflow_archive_candidates)
- packet ready: $($summary.packet_ready)
"@

$completionMarkdown = @"
# LIVE 15 PHASE COMPLETION

Generated UTC: $($summary.generated_at_utc)

## Completion
- phase completion percent: $($summary.phase_completion_percent)
- ship decision: $($summary.ship_decision)

## Phase Matrix
$phaseLines
"@

$phaseMarkdown = @"
# Phase 15 Final Ship Decision and Completion

Generated UTC: $($summary.generated_at_utc)

## Outputs
- docs/release/LIVE_SHIP_DECISION.md
- docs/release/LIVE_15_PHASE_COMPLETION.md

## Summary
- ship decision: $($summary.ship_decision)
- overall score: $($summary.overall_score)
- overall status: $($summary.overall_status)
- checklist percent: $($summary.checklist_percent)
- phase completion percent: $($summary.phase_completion_percent)

## Artifact
- phase15_completion_matrix.csv
"@

Set-Content -Path $shipMd -Value $shipMarkdown -Encoding UTF8
Set-Content -Path $completionMd -Value $completionMarkdown -Encoding UTF8
Set-Content -Path $phaseSummaryMd -Value $phaseMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 15 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Ship decision: $shipMd"
Write-Host "Phase completion: $completionMd"
Write-Host ""