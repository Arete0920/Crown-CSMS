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

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase11"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$phase5Csv = Join-Path $script:RepoRoot "docs\release\live-audit\phase5\phase5_module_proof_matrix.csv"
$phase6ActionJson = Join-Path $script:RepoRoot "docs\release\LIVE_ACTION_REGISTER.json"
$phase10GateJson = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_GATE_STATUS.json"

$required = @($phase5Csv, $phase6ActionJson, $phase10GateJson)
foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        throw "Required artifact missing: $file"
    }
}

$moduleRows = @(Import-Csv -Path $phase5Csv)
$actionDoc = Get-Content -Path $phase6ActionJson -Raw -Encoding UTF8 | ConvertFrom-Json
$gateDoc = Get-Content -Path $phase10GateJson -Raw -Encoding UTF8 | ConvertFrom-Json

$actions = @()
if ($actionDoc.action_register) {
    $actions = @($actionDoc.action_register)
}

$highActions = @($actions | Where-Object { $_.priority -eq "HIGH" })
$mediumActions = @($actions | Where-Object { $_.priority -eq "MEDIUM" })

$gateRows = @()
if ($gateDoc.gates) {
    $gateRows = @($gateDoc.gates)
}

$checklistItems = New-Object System.Collections.Generic.List[object]

foreach ($gate in $gateRows) {
    $checklistItems.Add([pscustomobject]@{
        item_key     = $gate.gate
        item_label   = ($gate.gate -replace '_',' ')
        is_complete  = ($gate.status -eq "PASS")
        owner_hint   = "release"
        evidence     = "docs/release/LIVE_RELEASE_GATE_STATUS.md"
    }) | Out-Null
}

$checklistItems.Add([pscustomobject]@{
    item_key     = "high_priority_actions_closed"
    item_label   = "high priority actions closed"
    is_complete  = (@($highActions).Count -eq 0)
    owner_hint   = "release"
    evidence     = "docs/release/LIVE_ACTION_REGISTER.md"
}) | Out-Null

$checklistItems.Add([pscustomobject]@{
    item_key     = "module_proof_reviewed"
    item_label   = "module proof summary reviewed"
    is_complete  = (@($moduleRows).Count -gt 0)
    owner_hint   = "product"
    evidence     = "docs/release/LIVE_MODULE_STATUS_SUMMARY.md"
}) | Out-Null

$completeCount = @($checklistItems | Where-Object { $_.is_complete }).Count
$totalCount = @($checklistItems).Count
$checklistPercent = if ($totalCount -gt 0) {
    [int][math]::Round((100.0 * $completeCount / $totalCount), 0)
} else { 0 }

$moduleSummaryRows = $moduleRows | Sort-Object module_key | ForEach-Object {
    [pscustomobject]@{
        module_key    = $_.module_key
        label         = $_.label
        proof_score   = [int]$_.proof_score
        proof_status  = $_.proof_status
        backend_paths = [int]$_.backend_path_count
        tests         = [int]$_.backend_test_count
        docs          = [int]$_.release_doc_hit_count
        workflows     = [int]$_.workflow_hit_count
    }
}

$summary = [ordered]@{
    generated_at_utc        = (Get-Date).ToUniversalTime().ToString("o")
    overall_score           = [int]$gateDoc.summary.overall_score
    overall_status          = [string]$gateDoc.summary.overall_status
    gate_count              = @($gateRows).Count
    checklist_complete      = $completeCount
    checklist_total         = $totalCount
    checklist_percent       = $checklistPercent
    high_priority_actions   = @($highActions).Count
    medium_priority_actions = @($mediumActions).Count
    module_count            = @($moduleSummaryRows).Count
}

$gateMd = Join-Path $script:RepoRoot "docs\release\LIVE_FINAL_RELEASE_GATE.md"
$gateJson = Join-Path $script:RepoRoot "docs\release\LIVE_FINAL_RELEASE_GATE.json"
$checklistMd = Join-Path $script:RepoRoot "docs\release\LIVE_FINAL_SIGNOFF_CHECKLIST.md"
$checklistJson = Join-Path $script:RepoRoot "docs\release\LIVE_FINAL_SIGNOFF_CHECKLIST.json"
$moduleMd = Join-Path $script:RepoRoot "docs\release\LIVE_MODULE_STATUS_SUMMARY.md"
$moduleJson = Join-Path $script:RepoRoot "docs\release\LIVE_MODULE_STATUS_SUMMARY.json"

$phaseSummaryJson = Join-Path $outDir "phase11_live_release_docs_refresh.json"
$checklistCsv = Join-Path $outDir "phase11_signoff_checklist.csv"
$moduleCsv = Join-Path $outDir "phase11_module_status_summary.csv"
$phaseSummaryMd = Join-Path $outDir "phase11_live_release_docs_refresh.md"

$checklistItems | Export-Csv -Path $checklistCsv -NoTypeInformation -Encoding UTF8
$moduleSummaryRows | Export-Csv -Path $moduleCsv -NoTypeInformation -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    gates            = $gateRows
    blockers         = $highActions
} | ConvertTo-Json -Depth 8 | Set-Content -Path $gateJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    checklist        = $checklistItems
} | ConvertTo-Json -Depth 8 | Set-Content -Path $checklistJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    modules          = $moduleSummaryRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $moduleJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    checklist        = $checklistItems
    modules          = $moduleSummaryRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $phaseSummaryJson -Encoding UTF8

$gateLines = ($gateRows | ForEach-Object {
    "- $($_.gate) | score=$($_.score) | status=$($_.status)"
}) -join "`r`n"

$blockerLines = if (@($highActions).Count -gt 0) {
    ($highActions | ForEach-Object {
        "- $($_.action_key) | owner=$($_.owner_hint) | evidence=$($_.evidence_path)"
    }) -join "`r`n"
} else {
    "- none"
}

$checklistLines = ($checklistItems | ForEach-Object {
    if ($_.is_complete) {
        "- [x] $($_.item_label) | evidence=$($_.evidence)"
    } else {
        "- [ ] $($_.item_label) | evidence=$($_.evidence)"
    }
}) -join "`r`n"

$moduleLines = ($moduleSummaryRows | ForEach-Object {
    "- $($_.label) | score=$($_.proof_score) | status=$($_.proof_status) | backend=$($_.backend_paths) | tests=$($_.tests) | docs=$($_.docs) | workflows=$($_.workflows)"
}) -join "`r`n"

$gateMarkdown = @"
# LIVE FINAL RELEASE GATE

Generated UTC: $($summary.generated_at_utc)

## Overall
- overall score: $($summary.overall_score)
- overall status: $($summary.overall_status)
- checklist percent: $($summary.checklist_percent)
- high priority actions: $($summary.high_priority_actions)
- medium priority actions: $($summary.medium_priority_actions)

## Gate Rows
$gateLines

## High Priority Blockers
$blockerLines

## Source
- docs/release/LIVE_RELEASE_GATE_STATUS.md
- docs/release/LIVE_ACTION_REGISTER.md
"@

$checklistMarkdown = @"
# LIVE FINAL SIGNOFF CHECKLIST

Generated UTC: $($summary.generated_at_utc)

## Completion
- complete: $($summary.checklist_complete) / $($summary.checklist_total)
- percent: $($summary.checklist_percent)

## Checklist
$checklistLines

## Source
- docs/release/LIVE_FINAL_RELEASE_GATE.md
- docs/release/LIVE_ACTION_REGISTER.md
"@

$moduleMarkdown = @"
# LIVE MODULE STATUS SUMMARY

Generated UTC: $($summary.generated_at_utc)

## Modules
- module count: $($summary.module_count)

## Module Rows
$moduleLines

## Source
- docs/release/live-audit/phase5/phase5_module_proof_matrix.csv
"@

$phaseMarkdown = @"
# Phase 11 Live Release Docs Refresh

Generated UTC: $($summary.generated_at_utc)

## Outputs
- docs/release/LIVE_FINAL_RELEASE_GATE.md
- docs/release/LIVE_FINAL_SIGNOFF_CHECKLIST.md
- docs/release/LIVE_MODULE_STATUS_SUMMARY.md

## Summary
- overall score: $($summary.overall_score)
- overall status: $($summary.overall_status)
- checklist percent: $($summary.checklist_percent)
- high priority actions: $($summary.high_priority_actions)
- medium priority actions: $($summary.medium_priority_actions)

## Artifacts
- phase11_signoff_checklist.csv
- phase11_module_status_summary.csv
- phase11_live_release_docs_refresh.json
"@

Set-Content -Path $gateMd -Value $gateMarkdown -Encoding UTF8
Set-Content -Path $checklistMd -Value $checklistMarkdown -Encoding UTF8
Set-Content -Path $moduleMd -Value $moduleMarkdown -Encoding UTF8
Set-Content -Path $phaseSummaryMd -Value $phaseMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 11 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live gate: $gateMd"
Write-Host "Live checklist: $checklistMd"
Write-Host "Live modules: $moduleMd"
Write-Host ""