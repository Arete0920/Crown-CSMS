param(
    [switch]$ApplyArchiveExtra
)

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

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )
    return ($FullPath.Substring($RepoRoot.Length).TrimStart('\', '/') -replace '\\', '/')
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase13"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$phase3WorkflowCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_workflow_inventory_enriched.csv"
$phase3GroupCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_workflow_consolidation_groups.csv"

$required = @($phase3WorkflowCsv, $phase3GroupCsv)
foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        throw "Required artifact missing: $file"
    }
}

$workflowRows = @(Import-Csv -Path $phase3WorkflowCsv)
$groupRows = @(Import-Csv -Path $phase3GroupCsv)

$workflowDir = Join-Path $script:RepoRoot ".github\workflows"
$disabledDir = Join-Path $workflowDir "_disabled_review"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$reviewRows = New-Object System.Collections.Generic.List[object]

foreach ($group in $groupRows) {
    $groupKey = $group.group_key
    $groupMembers = @($workflowRows | Where-Object { $_.consolidation_group_key -eq $groupKey } | Sort-Object workflow_name)

    if (@($groupMembers).Count -eq 1) {
        $row = $groupMembers[0]
        $reviewRows.Add([pscustomobject]@{
            workflow_name     = $row.workflow_name
            path              = $row.path
            group_key         = $groupKey
            review_action     = "KEEP_UNIQUE"
            archive_candidate = $false
        }) | Out-Null
        continue
    }

    $primary = $groupMembers | Sort-Object @{Expression = { if ($_.has_workflow_dispatch -eq "True") { 0 } else { 1 } }}, @{Expression = { $_.workflow_name }} | Select-Object -First 1
    foreach ($row in $groupMembers) {
        $isPrimary = ($row.path -eq $primary.path)
        $reviewRows.Add([pscustomobject]@{
            workflow_name     = $row.workflow_name
            path              = $row.path
            group_key         = $groupKey
            review_action     = if ($isPrimary) { "KEEP_PRIMARY_REVIEW" } else { "REVIEW_DUPLICATE_CLUSTER" }
            archive_candidate = (-not $isPrimary)
        }) | Out-Null
    }
}

$archiveCandidates = @($reviewRows | Where-Object { $_.archive_candidate })
$archivedRows = New-Object System.Collections.Generic.List[object]

if ($ApplyArchiveExtra -and @($archiveCandidates).Count -gt 0) {
    New-Item -ItemType Directory -Force -Path (Join-Path $disabledDir $timestamp) | Out-Null

    foreach ($row in $archiveCandidates) {
        $source = Join-Path $script:RepoRoot ($row.path -replace '/', '\')
        if (Test-Path $source) {
            $destDir = Join-Path $disabledDir $timestamp
            $dest = Join-Path $destDir ([IO.Path]::GetFileName($source) + ".disabled")
            Move-Item -Path $source -Destination $dest -Force
            $archivedRows.Add([pscustomobject]@{
                source_path  = $row.path
                archive_path = (Get-RepoRelativePath -FullPath $dest -RepoRoot $script:RepoRoot)
            }) | Out-Null
        }
    }
}

$generatedDir = Join-Path $script:RepoRoot "scripts\release\generated"
New-Item -ItemType Directory -Force -Path $generatedDir | Out-Null

$archiveScript = Join-Path $generatedDir "phase13_archive_extra_workflows.ps1"
$archiveLines = @()
$archiveLines += 'param([switch]$Apply)'
$archiveLines += '$ErrorActionPreference = "Stop"'
$archiveLines += '$repoRoot = (git rev-parse --show-toplevel).Trim()'
$archiveLines += '$destRoot = Join-Path $repoRoot (".github\workflows\_disabled_review\" + (Get-Date -Format "yyyyMMdd_HHmmss"))'
$archiveLines += 'if ($Apply) { New-Item -ItemType Directory -Force -Path $destRoot | Out-Null }'
foreach ($row in $archiveCandidates) {
    $pathEscaped = $row.path -replace '"','`"'
    $archiveLines += ('$src = Join-Path $repoRoot "{0}"' -f ($pathEscaped -replace '/','\'))
    $archiveLines += 'if ($Apply -and (Test-Path $src)) {'
    $archiveLines += '    $dst = Join-Path $destRoot ((Split-Path $src -Leaf) + ".disabled")'
    $archiveLines += '    Move-Item -Path $src -Destination $dst -Force'
    $archiveLines += '}'
}
Set-Content -Path $archiveScript -Value ($archiveLines -join "`r`n") -Encoding UTF8

$planMd = Join-Path $script:RepoRoot "docs\release\LIVE_WORKFLOW_CANONICALIZATION_PLAN.md"
$planJson = Join-Path $script:RepoRoot "docs\release\LIVE_WORKFLOW_CANONICALIZATION_PLAN.json"
$phaseSummaryJson = Join-Path $outDir "phase13_workflow_canonicalization_plan.json"
$phaseSummaryMd = Join-Path $outDir "phase13_workflow_canonicalization_plan.md"
$reviewCsv = Join-Path $outDir "phase13_workflow_review_matrix.csv"
$archivedCsv = Join-Path $outDir "phase13_archived_workflows.csv"

$reviewMatrix = if ($reviewRows.Count -gt 0) { $reviewRows.ToArray() } else { @() }
$archivedItems = if ($archivedRows.Count -gt 0) { $archivedRows.ToArray() } else { @() }

$reviewMatrix | Export-Csv -Path $reviewCsv -NoTypeInformation -Encoding UTF8
$archivedItems | Export-Csv -Path $archivedCsv -NoTypeInformation -Encoding UTF8

$duplicateGroups = @($groupRows | Where-Object { [int]$_.workflow_count -gt 1 })

$summary = [ordered]@{
    generated_at_utc        = (Get-Date).ToUniversalTime().ToString("o")
    workflow_count          = $reviewRows.Count
    duplicate_cluster_count = $duplicateGroups.Count
    archive_candidate_count = $archiveCandidates.Count
    archived_count          = $archivedRows.Count
    archive_script_path     = "scripts/release/generated/phase13_archive_extra_workflows.ps1"
}

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    review_matrix    = $reviewMatrix
    archived         = $archivedItems
} | ConvertTo-Json -Depth 8 | Set-Content -Path $planJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
} | ConvertTo-Json -Depth 6 | Set-Content -Path $phaseSummaryJson -Encoding UTF8

$reviewLines = ($reviewRows | ForEach-Object {
    "- $($_.workflow_name) | group=$($_.group_key) | action=$($_.review_action)"
}) -join "`r`n"

$planMarkdown = @"
# LIVE WORKFLOW CANONICALIZATION PLAN

Generated UTC: $($summary.generated_at_utc)

## Summary
- workflow count: $($summary.workflow_count)
- duplicate cluster count: $($summary.duplicate_cluster_count)
- archive candidate count: $($summary.archive_candidate_count)
- archived count: $($summary.archived_count)

## Review Matrix
$reviewLines

## Archive Script
- $($summary.archive_script_path)
"@

$phaseMarkdown = @"
# Phase 13 Workflow Canonicalization Plan

Generated UTC: $($summary.generated_at_utc)

## Outputs
- docs/release/LIVE_WORKFLOW_CANONICALIZATION_PLAN.md
- scripts/release/generated/phase13_archive_extra_workflows.ps1

## Summary
- duplicate cluster count: $($summary.duplicate_cluster_count)
- archive candidate count: $($summary.archive_candidate_count)
- archived count: $($summary.archived_count)

## Artifacts
- phase13_workflow_review_matrix.csv
- phase13_archived_workflows.csv
"@

Set-Content -Path $planMd -Value $planMarkdown -Encoding UTF8
Set-Content -Path $phaseSummaryMd -Value $phaseMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 13 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live workflow plan: $planMd"
Write-Host "Archive script: $archiveScript"
Write-Host ""