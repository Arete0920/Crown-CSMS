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

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase6"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$phase1Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase1\phase1_live_repo_baseline.json"
$phase2MismatchCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase2\phase2_release_truth_mismatches.csv"
$phase3BranchCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_branch_cleanup_candidates.csv"
$phase4Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase4\phase4_backend_verification_and_django_proof.json"
$phase5Csv = Join-Path $script:RepoRoot "docs\release\live-audit\phase5\phase5_module_proof_matrix.csv"

$required = @($phase1Json, $phase4Json, $phase5Csv)
foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        throw "Required prior phase artifact missing: $file"
    }
}

$phase1 = Get-Content -Path $phase1Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase4 = Get-Content -Path $phase4Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase5 = Import-Csv -Path $phase5Csv
$phase2Mismatches = @()
if (Test-Path $phase2MismatchCsv) {
    $phase2Mismatches = @(Import-Csv -Path $phase2MismatchCsv)
}
$phase3BranchCandidates = @()
if (Test-Path $phase3BranchCsv) {
    $phase3BranchCandidates = @(Import-Csv -Path $phase3BranchCsv)
}

$evidenceRows = New-Object System.Collections.Generic.List[object]
$actionRows = New-Object System.Collections.Generic.List[object]

$evidenceRows.Add([pscustomobject]@{
    area        = "repo_baseline"
    artifact    = "phase1_live_repo_baseline.json"
    path        = "docs/release/live-audit/phase1/phase1_live_repo_baseline.json"
    status      = "READY"
    detail      = "Repo baseline generated"
}) | Out-Null

if (Test-Path $phase2MismatchCsv) {
    $evidenceRows.Add([pscustomobject]@{
        area        = "release_truth"
        artifact    = "phase2_release_truth_mismatches.csv"
        path        = "docs/release/live-audit/phase2/phase2_release_truth_mismatches.csv"
        status      = if (@($phase2Mismatches).Count -eq 0) { "READY" } else { "ACTION" }
        detail      = "Mismatch count: $(@($phase2Mismatches).Count)"
    }) | Out-Null
}

$evidenceRows.Add([pscustomobject]@{
    area        = "backend_verification"
    artifact    = "phase4_backend_verification_and_django_proof.json"
    path        = "docs/release/live-audit/phase4/phase4_backend_verification_and_django_proof.json"
    status      = if ($phase4.summary.manage_check_ok -and $phase4.summary.showmigrations_ok) { "READY" } else { "ACTION" }
    detail      = "manage_check_ok=$($phase4.summary.manage_check_ok); showmigrations_ok=$($phase4.summary.showmigrations_ok)"
}) | Out-Null

$evidenceRows.Add([pscustomobject]@{
    area        = "module_proof"
    artifact    = "phase5_module_proof_matrix.csv"
    path        = "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv"
    status      = "READY"
    detail      = "Module proof rows: $(@($phase5).Count)"
}) | Out-Null

if (Test-Path $phase3BranchCsv) {
    $evidenceRows.Add([pscustomobject]@{
        area        = "branch_cleanup"
        artifact    = "phase3_branch_cleanup_candidates.csv"
        path        = "docs/release/live-audit/phase3/phase3_branch_cleanup_candidates.csv"
        status      = if (@($phase3BranchCandidates).Count -eq 0) { "READY" } else { "ACTION" }
        detail      = "Delete candidate count: $(@($phase3BranchCandidates).Count)"
    }) | Out-Null
}

if (@($phase2Mismatches).Count -gt 0) {
    $actionRows.Add([pscustomobject]@{
        phase          = "2"
        priority       = "HIGH"
        action_key     = "refresh_release_truth_docs"
        owner_hint     = "release"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase2/phase2_release_truth_mismatches.csv"
        next_step      = "Reconcile stale release docs against live repo state"
    }) | Out-Null
}

if (-not $phase4.summary.manage_check_ok) {
    $actionRows.Add([pscustomobject]@{
        phase          = "4"
        priority       = "HIGH"
        action_key     = "fix_manage_check"
        owner_hint     = "backend"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase4/phase4_manage_check.txt"
        next_step      = "Resolve Django check failures"
    }) | Out-Null
}

if (-not $phase4.summary.manage_check_deploy_ok) {
    $actionRows.Add([pscustomobject]@{
        phase          = "4"
        priority       = "HIGH"
        action_key     = "fix_manage_check_deploy"
        owner_hint     = "backend_ops"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase4/phase4_manage_check_deploy.txt"
        next_step      = "Resolve Django deploy check findings"
    }) | Out-Null
}

if (@($phase3BranchCandidates).Count -gt 0) {
    $actionRows.Add([pscustomobject]@{
        phase          = "3"
        priority       = "MEDIUM"
        action_key     = "cleanup_merged_branches"
        owner_hint     = "repo_admin"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase3/phase3_branch_cleanup_candidates.csv"
        next_step      = "Delete merged stale branches after review"
    }) | Out-Null
}

$thinModules = @($phase5 | Where-Object { $_.proof_status -eq "THIN" })
$partialModules = @($phase5 | Where-Object { $_.proof_status -eq "PARTIAL" })

foreach ($row in $thinModules) {
    $actionRows.Add([pscustomobject]@{
        phase          = "5"
        priority       = "HIGH"
        action_key     = "module_proof_$($row.module_key)"
        owner_hint     = "module_owner"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv"
        next_step      = "Raise proof coverage for $($row.label)"
    }) | Out-Null
}

foreach ($row in $partialModules) {
    $actionRows.Add([pscustomobject]@{
        phase          = "5"
        priority       = "MEDIUM"
        action_key     = "module_partial_$($row.module_key)"
        owner_hint     = "module_owner"
        status         = "OPEN"
        evidence_path  = "docs/release/live-audit/phase5/phase5_module_proof_matrix.csv"
        next_step      = "Strengthen coverage and evidence for $($row.label)"
    }) | Out-Null
}

$evidenceCsv = Join-Path $outDir "phase6_evidence_index.csv"
$actionCsv = Join-Path $outDir "phase6_action_register.csv"
$summaryJson = Join-Path $outDir "phase6_evidence_index_and_action_register.json"
$summaryMd = Join-Path $outDir "phase6_evidence_index_and_action_register.md"
$liveEvidenceMd = Join-Path $script:RepoRoot "docs\release\LIVE_EVIDENCE_INDEX.md"
$liveActionMd = Join-Path $script:RepoRoot "docs\release\LIVE_ACTION_REGISTER.md"
$liveEvidenceJson = Join-Path $script:RepoRoot "docs\release\LIVE_EVIDENCE_INDEX.json"
$liveActionJson = Join-Path $script:RepoRoot "docs\release\LIVE_ACTION_REGISTER.json"

$evidenceRows | Export-Csv -Path $evidenceCsv -NoTypeInformation -Encoding UTF8
$actionRows | Export-Csv -Path $actionCsv -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    generated_at_utc      = (Get-Date).ToUniversalTime().ToString("o")
    evidence_count       = @($evidenceRows).Count
    action_count         = @($actionRows).Count
    high_priority_count  = @($actionRows | Where-Object { $_.priority -eq "HIGH" }).Count
    medium_priority_count = @($actionRows | Where-Object { $_.priority -eq "MEDIUM" }).Count
    repo_branch_count    = $phase1.inventories.local_branch_count
    repo_workflow_count  = $phase1.inventories.workflow_count
    backend_app_count    = $phase4.summary.backend_app_count
    module_count         = @($phase5).Count
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    evidence_index   = $evidenceRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveEvidenceJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    action_register  = $actionRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveActionJson -Encoding UTF8

$evidenceLines = ($evidenceRows | ForEach-Object {
    "- $($_.area) | $($_.artifact) | status=$($_.status) | detail=$($_.detail)"
}) -join "`r`n"

$actionLines = if (@($actionRows).Count -gt 0) {
    ($actionRows | ForEach-Object {
        "- [$($_.priority)] $($_.action_key) | owner=$($_.owner_hint) | next=$($_.next_step) | evidence=$($_.evidence_path)"
    }) -join "`r`n"
} else {
    "- none"
}

$evidenceMarkdown = @"
# LIVE EVIDENCE INDEX

Generated UTC: $($summary.generated_at_utc)

## Summary
- evidence count: $($summary.evidence_count)
- action count: $($summary.action_count)
- high priority actions: $($summary.high_priority_count)
- medium priority actions: $($summary.medium_priority_count)
- local branches: $($summary.repo_branch_count)
- workflows: $($summary.repo_workflow_count)
- backend apps: $($summary.backend_app_count)
- modules: $($summary.module_count)

## Evidence Index
$evidenceLines

## Source
- docs/release/live-audit/phase6/phase6_evidence_index.csv
"@

$actionMarkdown = @"
# LIVE ACTION REGISTER

Generated UTC: $($summary.generated_at_utc)

## Open Actions
$actionLines

## Source
- docs/release/live-audit/phase6/phase6_action_register.csv
"@

$summaryMarkdown = @"
# Phase 6 Evidence Index and Action Register

Generated UTC: $($summary.generated_at_utc)

## Evidence Index
$evidenceLines

## Action Register
$actionLines

## Generated Artifacts
- phase6_evidence_index.csv
- phase6_action_register.csv
- phase6_evidence_index_and_action_register.json
"@

Set-Content -Path $liveEvidenceMd -Value $evidenceMarkdown -Encoding UTF8
Set-Content -Path $liveActionMd -Value $actionMarkdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $summaryMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 6 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live evidence index: $liveEvidenceMd"
Write-Host "Live action register: $liveActionMd"
Write-Host ""
