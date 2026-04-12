$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (-not (Test-Path $Path)) {
        throw "Missing required artifact: $Path"
    }
}

function Read-Json {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    Assert-PathExists -Path $Path
    return Get-Content -Path $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Read-CsvSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    Assert-PathExists -Path $Path
    return @(Import-Csv -Path $Path)
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$requiredArtifacts = @(
    "docs/release/live-audit/phase1/phase1_live_repo_baseline.json",
    "docs/release/live-audit/phase2/phase2_release_truth_reconciliation.json",
    "docs/release/live-audit/phase3/phase3_workflow_branch_rationalization.json",
    "docs/release/live-audit/phase4/phase4_backend_verification_and_django_proof.json",
    "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv",
    "docs/release/live-audit/phase6/phase6_evidence_index_and_action_register.json",
    "docs/release/live-audit/phase7/phase7_runtime_and_api_surface_verification.json",
    "docs/release/live-audit/phase8/phase8_frontend_and_dashboard_proof.json",
    "docs/release/live-audit/phase9/phase9_reporting_export_pdf_transcript_gap_audit.json",
    "docs/release/live-audit/phase10/phase10_live_release_gate_synthesis.json",
    "docs/release/live-audit/phase11/phase11_live_release_docs_refresh.json",
    "docs/release/live-audit/phase12/phase12_repo_hygiene_execution_pack.json",
    "docs/release/live-audit/phase13/phase13_workflow_canonicalization_plan.json",
    "docs/release/live-audit/phase14/phase14_live_evidence_pack_builder.json",
    "docs/release/live-audit/phase15/phase15_final_ship_decision_and_completion.json",
    "docs/release/LIVE_RELEASE_TRUTH.md",
    "docs/release/LIVE_BACKEND_VERIFICATION.md",
    "docs/release/LIVE_MODULE_PROOF_MATRIX.md",
    "docs/release/LIVE_EVIDENCE_INDEX.md",
    "docs/release/LIVE_ACTION_REGISTER.md",
    "docs/release/LIVE_RUNTIME_API_VERIFICATION.md",
    "docs/release/LIVE_FRONTEND_DASHBOARD_PROOF.md",
    "docs/release/LIVE_REPORTING_EXPORT_AUDIT.md",
    "docs/release/LIVE_RELEASE_GATE_STATUS.md",
    "docs/release/LIVE_FINAL_RELEASE_GATE.md",
    "docs/release/LIVE_FINAL_SIGNOFF_CHECKLIST.md",
    "docs/release/LIVE_MODULE_STATUS_SUMMARY.md",
    "docs/release/LIVE_REPO_HYGIENE_PLAN.md",
    "docs/release/LIVE_WORKFLOW_CANONICALIZATION_PLAN.md",
    "docs/release/LIVE_EVIDENCE_PACKET.md",
    "docs/release/LIVE_SHIP_DECISION.md",
    "docs/release/LIVE_15_PHASE_COMPLETION.md"
)

foreach ($artifact in $requiredArtifacts) {
    Assert-PathExists -Path $artifact
}

$phase4 = Read-Json "docs/release/live-audit/phase4/phase4_backend_verification_and_django_proof.json"
$phase6 = Read-Json "docs/release/live-audit/phase6/phase6_evidence_index_and_action_register.json"
$phase7 = Read-Json "docs/release/live-audit/phase7/phase7_runtime_and_api_surface_verification.json"
$phase8 = Read-Json "docs/release/live-audit/phase8/phase8_frontend_and_dashboard_proof.json"
$phase9 = Read-Json "docs/release/live-audit/phase9/phase9_reporting_export_pdf_transcript_gap_audit.json"
$phase10 = Read-Json "docs/release/live-audit/phase10/phase10_live_release_gate_synthesis.json"
$phase11 = Read-Json "docs/release/live-audit/phase11/phase11_live_release_docs_refresh.json"
$phase12 = Read-Json "docs/release/live-audit/phase12/phase12_repo_hygiene_execution_pack.json"
$phase13 = Read-Json "docs/release/live-audit/phase13/phase13_workflow_canonicalization_plan.json"
$phase14 = Read-Json "docs/release/live-audit/phase14/phase14_live_evidence_pack_builder.json"
$phase15 = Read-Json "docs/release/live-audit/phase15/phase15_final_ship_decision_and_completion.json"
$phase5 = Read-CsvSafe "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv"

$errors = New-Object System.Collections.Generic.List[string]

if (-not $phase4.summary.manage_py_exists) {
    $errors.Add("Phase 4: manage.py missing")
}
if (-not $phase4.summary.python_version_ok) {
    $errors.Add("Phase 4: python unavailable")
}
if (-not $phase4.summary.django_import_ok) {
    $errors.Add("Phase 4: django import failed")
}
if (-not $phase4.summary.showmigrations_ok) {
    $errors.Add("Phase 4: showmigrations failed")
}

if ([int]$phase6.summary.evidence_count -lt 4) {
    $errors.Add("Phase 6: evidence index too small")
}

if ([int]$phase7.summary.endpoint_count -lt 4) {
    $errors.Add("Phase 7: endpoint verification set too small")
}

if ([int]$phase8.summary.package_count -lt 1) {
    $errors.Add("Phase 8: no frontend package detected")
}

if ([int]$phase9.summary.area_count -lt 5) {
    $errors.Add("Phase 9: reporting/export audit incomplete")
}

if ([int]$phase10.summary.overall_score -lt 0 -or [int]$phase10.summary.overall_score -gt 100) {
    $errors.Add("Phase 10: overall score out of range")
}

if ([int]$phase11.summary.module_count -ne @($phase5).Count) {
    $errors.Add("Phase 11: module summary count does not match phase 5")
}

if (-not $phase14.summary.zip_path) {
    $errors.Add("Phase 14: evidence packet zip path missing")
}
if (-not (Test-Path $phase14.summary.zip_path)) {
    $errors.Add("Phase 14: evidence packet zip file missing")
}

if ([int]$phase15.summary.phase_completion_percent -lt 100) {
    $errors.Add("Phase 15: not all phases completed")
}

if ([string]::IsNullOrWhiteSpace([string]$phase15.summary.ship_decision)) {
    $errors.Add("Phase 15: ship decision missing")
}

$report = [pscustomobject]@{
    generated_at_utc           = (Get-Date).ToUniversalTime().ToString("o")
    artifact_check_passed      = ($requiredArtifacts.Count -gt 0)
    required_artifact_count    = $requiredArtifacts.Count
    phase4_manage_check_ok     = [bool]$phase4.summary.manage_check_ok
    phase4_deploy_check_ok     = [bool]$phase4.summary.manage_check_deploy_ok
    phase6_high_actions        = [int]$phase6.summary.high_priority_count
    phase6_medium_actions      = [int]$phase6.summary.medium_priority_count
    phase7_runtime_any_success = [bool]$phase7.summary.runtime_any_success
    phase8_build_success_count = [int]$phase8.summary.build_success_count
    phase9_reporting_score     = [int]$phase9.summary.reporting_score
    phase10_overall_score      = [int]$phase10.summary.overall_score
    phase10_overall_status     = [string]$phase10.summary.overall_status
    phase11_checklist_percent  = [int]$phase11.summary.checklist_percent
    phase12_remote_delete_count = [int]$phase12.summary.remote_delete_count
    phase12_local_delete_count = [int]$phase12.summary.local_delete_count
    phase13_archive_candidate_count = [int]$phase13.summary.archive_candidate_count
    phase14_packet_ready       = ([int]$phase14.summary.copied_count -gt 0)
    phase15_ship_decision      = [string]$phase15.summary.ship_decision
    phase15_completion_percent = [int]$phase15.summary.phase_completion_percent
    error_count                = $errors.Count
    passed                     = ($errors.Count -eq 0)
}

$reportJson = "docs/release/FINAL_15_PHASE_VERIFICATION.json"
$reportMd = "docs/release/FINAL_15_PHASE_VERIFICATION.md"
$reportCsv = "docs/release/live-audit/final_15_phase_verification_errors.csv"

$report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportJson -Encoding UTF8

$errors |
    ForEach-Object { [pscustomobject]@{ error = $_ } } |
    Export-Csv -Path $reportCsv -NoTypeInformation -Encoding UTF8

$errorLines = if ($errors.Count -gt 0) {
    ($errors | ForEach-Object { "- $_" }) -join "`r`n"
} else {
    "- none"
}

$markdown = @"
# FINAL 15 PHASE VERIFICATION

Generated UTC: $($report.generated_at_utc)

## Summary
- passed: $($report.passed)
- error count: $($report.error_count)
- phase 10 overall score: $($report.phase10_overall_score)
- phase 10 overall status: $($report.phase10_overall_status)
- phase 11 checklist percent: $($report.phase11_checklist_percent)
- phase 15 ship decision: $($report.phase15_ship_decision)
- phase 15 completion percent: $($report.phase15_completion_percent)

## Key Checks
- phase 4 manage check ok: $($report.phase4_manage_check_ok)
- phase 4 deploy check ok: $($report.phase4_deploy_check_ok)
- phase 6 high actions: $($report.phase6_high_actions)
- phase 6 medium actions: $($report.phase6_medium_actions)
- phase 7 runtime any success: $($report.phase7_runtime_any_success)
- phase 8 build success count: $($report.phase8_build_success_count)
- phase 9 reporting score: $($report.phase9_reporting_score)
- phase 12 remote delete count: $($report.phase12_remote_delete_count)
- phase 12 local delete count: $($report.phase12_local_delete_count)
- phase 13 archive candidate count: $($report.phase13_archive_candidate_count)
- phase 14 packet ready: $($report.phase14_packet_ready)

## Errors
$errorLines
"@

Set-Content -Path $reportMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "FINAL VERIFICATION COMPLETE"
Write-Host "JSON: $reportJson"
Write-Host "Markdown: $reportMd"
Write-Host "Errors CSV: $reportCsv"
Write-Host ""