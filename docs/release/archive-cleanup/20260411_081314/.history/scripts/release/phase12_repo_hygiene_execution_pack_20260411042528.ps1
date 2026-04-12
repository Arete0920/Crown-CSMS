param(
    [switch]$ArchiveStaleDocs,
    [switch]$ApplyRemoteDeletes,
    [switch]$ApplyLocalDeletes
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

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase12"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$phase2MismatchCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase2\phase2_release_truth_mismatches.csv"
$phase3RemoteDeleteTxt = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_remote_branch_delete_commands.txt"
$phase3LocalDeleteTxt = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_local_branch_delete_commands.txt"
$phase3CandidateCsv = Join-Path $script:RepoRoot "docs\release\live-audit\phase3\phase3_branch_cleanup_candidates.csv"

$staleDocs = @()
if (Test-Path $phase2MismatchCsv) {
    $staleDocs = @(Import-Csv -Path $phase2MismatchCsv | Select-Object -ExpandProperty doc_path -Unique)
}

$remoteDeleteCommands = @()
if (Test-Path $phase3RemoteDeleteTxt) {
    $remoteDeleteCommands = @(Get-Content -Path $phase3RemoteDeleteTxt -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$localDeleteCommands = @()
if (Test-Path $phase3LocalDeleteTxt) {
    $localDeleteCommands = @(Get-Content -Path $phase3LocalDeleteTxt -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$candidateRows = @()
if (Test-Path $phase3CandidateCsv) {
    $candidateRows = @(Import-Csv -Path $phase3CandidateCsv)
}

$archiveDir = Join-Path $script:RepoRoot ("docs\release\archive-stale\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$archivedRows = New-Object System.Collections.Generic.List[object]

if ($ArchiveStaleDocs -and @($staleDocs).Count -gt 0) {
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
    foreach ($doc in $staleDocs) {
        $source = Join-Path $script:RepoRoot ($doc -replace '/', '\')
        if (Test-Path $source) {
            $dest = Join-Path $archiveDir ([IO.Path]::GetFileName($source))
            Copy-Item -Path $source -Destination $dest -Force
            $archivedRows.Add([pscustomobject]@{
                source_path = $doc
                archive_path = ($dest.Substring($script:RepoRoot.Length).TrimStart('\') -replace '\\','/')
            }) | Out-Null
        }
    }
}

$executedRows = New-Object System.Collections.Generic.List[object]
if ($ApplyRemoteDeletes) {
    foreach ($cmd in $remoteDeleteCommands) {
        cmd /c $cmd | Out-Null
        $executedRows.Add([pscustomobject]@{
            command = $cmd
            command_type = "remote_delete"
            executed = $true
        }) | Out-Null
    }
}
if ($ApplyLocalDeletes) {
    foreach ($cmd in $localDeleteCommands) {
        cmd /c $cmd | Out-Null
        $executedRows.Add([pscustomobject]@{
            command = $cmd
            command_type = "local_delete"
            executed = $true
        }) | Out-Null
    }
}

$generatedDir = Join-Path $script:RepoRoot "scripts\release\generated"
New-Item -ItemType Directory -Force -Path $generatedDir | Out-Null

$applyScript = Join-Path $generatedDir "phase12_apply_repo_hygiene.ps1"
$applyScriptContent = @"
param(
    [switch]`$ApplyRemoteDeletes,
    [switch]`$ApplyLocalDeletes
)

`$ErrorActionPreference = "Stop"

`$remoteCommands = @(
$(
    ($remoteDeleteCommands | ForEach-Object { '    "' + ($_ -replace '"','`"') + '"' }) -join ",`r`n"
)
)

`$localCommands = @(
$(
    ($localDeleteCommands | ForEach-Object { '    "' + ($_ -replace '"','`"') + '"' }) -join ",`r`n"
)
)

if (`$ApplyRemoteDeletes) {
    foreach (`$cmd in `$remoteCommands) {
        cmd /c `$cmd
    }
}

if (`$ApplyLocalDeletes) {
    foreach (`$cmd in `$localCommands) {
        cmd /c `$cmd
    }
}
"@
Set-Content -Path $applyScript -Value $applyScriptContent -Encoding UTF8

$planMd = Join-Path $script:RepoRoot "docs\release\LIVE_REPO_HYGIENE_PLAN.md"
$planJson = Join-Path $script:RepoRoot "docs\release\LIVE_REPO_HYGIENE_PLAN.json"
$phaseSummaryJson = Join-Path $outDir "phase12_repo_hygiene_execution_pack.json"
$phaseSummaryMd = Join-Path $outDir "phase12_repo_hygiene_execution_pack.md"
$staleCsv = Join-Path $outDir "phase12_stale_release_docs.csv"
$executedCsv = Join-Path $outDir "phase12_hygiene_executed_commands.csv"
$archivedCsv = Join-Path $outDir "phase12_archived_stale_docs.csv"

($staleDocs | ForEach-Object { [pscustomobject]@{ doc_path = $_ } }) | Export-Csv -Path $staleCsv -NoTypeInformation -Encoding UTF8
$executedRows | Export-Csv -Path $executedCsv -NoTypeInformation -Encoding UTF8
$archivedRows | Export-Csv -Path $archivedCsv -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    generated_at_utc       = (Get-Date).ToUniversalTime().ToString("o")
    stale_doc_count        = $staleDocs.Count
    remote_delete_count    = $remoteDeleteCommands.Count
    local_delete_count     = $localDeleteCommands.Count
    archived_doc_count     = $archivedRows.Count
    executed_command_count = $executedRows.Count
    apply_script_path      = "scripts/release/generated/phase12_apply_repo_hygiene.ps1"
}

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    stale_docs       = $staleDocs
    remote_commands  = $remoteDeleteCommands
    local_commands   = $localDeleteCommands
    archived_docs    = $archivedRows
    executed         = $executedRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $planJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
} | ConvertTo-Json -Depth 6 | Set-Content -Path $phaseSummaryJson -Encoding UTF8

$staleLines = if (@($staleDocs).Count -gt 0) {
    ($staleDocs | ForEach-Object { "- $_" }) -join "`r`n"
} else { "- none" }

$remoteLines = if (@($remoteDeleteCommands).Count -gt 0) {
    ($remoteDeleteCommands | ForEach-Object { "- $_" }) -join "`r`n"
} else { "- none" }

$localLines = if (@($localDeleteCommands).Count -gt 0) {
    ($localDeleteCommands | ForEach-Object { "- $_" }) -join "`r`n"
} else { "- none" }

$planMarkdown = @"
# LIVE REPO HYGIENE PLAN

Generated UTC: $($summary.generated_at_utc)

## Stale Release Docs
$staleLines

## Remote Delete Commands
$remoteLines

## Local Delete Commands
$localLines

## Apply Script
- $($summary.apply_script_path)

## Summary
- stale doc count: $($summary.stale_doc_count)
- remote delete count: $($summary.remote_delete_count)
- local delete count: $($summary.local_delete_count)
- archived doc count: $($summary.archived_doc_count)
- executed command count: $($summary.executed_command_count)
"@

$phaseMarkdown = @"
# Phase 12 Repo Hygiene Execution Pack

Generated UTC: $($summary.generated_at_utc)

## Outputs
- docs/release/LIVE_REPO_HYGIENE_PLAN.md
- scripts/release/generated/phase12_apply_repo_hygiene.ps1

## Summary
- stale doc count: $($summary.stale_doc_count)
- remote delete count: $($summary.remote_delete_count)
- local delete count: $($summary.local_delete_count)
- archived doc count: $($summary.archived_doc_count)
- executed command count: $($summary.executed_command_count)

## Artifacts
- phase12_stale_release_docs.csv
- phase12_hygiene_executed_commands.csv
- phase12_archived_stale_docs.csv
"@

Set-Content -Path $planMd -Value $planMarkdown -Encoding UTF8
Set-Content -Path $phaseSummaryMd -Value $phaseMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 12 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live hygiene plan: $planMd"
Write-Host "Apply script: $applyScript"
Write-Host ""