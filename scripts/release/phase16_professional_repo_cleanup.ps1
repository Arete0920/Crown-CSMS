param(
    [switch]$ArchiveStaleReleaseDocs,
    [switch]$ArchiveDeadFileCandidates,
    [switch]$ApplyRemoteDeletes,
    [switch]$ApplyLocalDeletes,
    [switch]$ArchiveExtraWorkflows,
    [switch]$Resynthesize
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

function Assert-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Required path missing: $Path"
    }
}

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )
    return ($FullPath.Substring($RepoRoot.Length).TrimStart('\', '/') -replace '\\', '/')
}

function Ensure-ParentDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
}

function Move-ToArchive {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$ArchiveRoot,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    if (-not (Test-Path $Source)) {
        return $null
    }

    $relative = Get-RepoRelativePath -FullPath $Source -RepoRoot $RepoRoot
    $destination = Join-Path $ArchiveRoot ($relative -replace '/', '\')
    Ensure-ParentDirectory -Path $destination
    Move-Item -Path $Source -Destination $destination -Force

    return [pscustomobject]@{
        source_path  = $relative
        archive_path = (Get-RepoRelativePath -FullPath $destination -RepoRoot $RepoRoot)
    }
}

function Invoke-PowerShellScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    $allArgs = @('-ExecutionPolicy', 'Bypass', '-File', $ScriptPath) + $Arguments
    $output = & powershell @allArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "powershell $($allArgs -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Get-SummaryNode {
    param([Parameter(Mandatory = $true)]$Document)
    if ($Document.PSObject.Properties.Name -contains 'summary') {
        return $Document.summary
    }
    return $Document
}

function Get-ItemCount {
    param($Value)

    if ($null -eq $Value) { return 0 }
    if ($Value -is [string]) { return 1 }
    if ($Value -is [System.Array]) { return $Value.Length }
    if ($Value -is [System.Collections.ICollection]) { return $Value.Count }

    return @($Value).Count
}

$repoRoot = Invoke-Git -Args @('rev-parse', '--show-toplevel')
Set-Location $repoRoot

$phase12Json = Join-Path $repoRoot "docs\release\live-audit\phase12\phase12_repo_hygiene_execution_pack.json"
$phase12StaleCsv = Join-Path $repoRoot "docs\release\live-audit\phase12\phase12_stale_release_docs.csv"
$phase13Json = Join-Path $repoRoot "docs\release\live-audit\phase13\phase13_workflow_canonicalization_plan.json"
$phase13ReviewCsv = Join-Path $repoRoot "docs\release\live-audit\phase13\phase13_workflow_review_matrix.csv"
$phase12ApplyScript = Join-Path $repoRoot "scripts\release\generated\phase12_apply_repo_hygiene.ps1"
$phase13ArchiveScript = Join-Path $repoRoot "scripts\release\generated\phase13_archive_extra_workflows.ps1"

Assert-Path -Path $phase12Json
Assert-Path -Path $phase13Json
Assert-Path -Path $phase12ApplyScript
Assert-Path -Path $phase13ArchiveScript
Assert-Path -Path $phase13ReviewCsv

$outDir = Join-Path $repoRoot "docs\release\live-audit\phase16"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveRoot = Join-Path $repoRoot ("docs\release\archive-cleanup\" + $timestamp)
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null

$excludeDirNames = @(
    '.git',
    'node_modules',
    '.venv',
    'venv',
    '.next',
    '.nuxt',
    'dist-packages',
    'site-packages',
    'archive-cleanup'
)

$junkDirNames = @(
    '.history',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'htmlcov',
    'coverage',
    'tmp',
    'temp',
    'backup',
    'backups'
)

$junkFileRegexes = @(
    '\.bak$',
    '\.old$',
    '\.orig$',
    '\.rej$',
    '\.tmp$',
    '\.temp$',
    '\.backup$',
    '\.copy$',
    '\.disabled$',
    '~$',
    '(^|[\\/])Thumbs\.db$',
    '(^|[\\/])\.DS_Store$'
)

$phase12 = Get-Content -Path $phase12Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase13 = Get-Content -Path $phase13Json -Raw -Encoding UTF8 | ConvertFrom-Json
$phase12Summary = Get-SummaryNode -Document $phase12
$phase13Summary = Get-SummaryNode -Document $phase13

$staleDocRows = @()
if (Test-Path $phase12StaleCsv) {
    $staleDocRows = @(Import-Csv -Path $phase12StaleCsv)
}

$workflowReviewRows = @(Import-Csv -Path $phase13ReviewCsv)
$workflowArchiveCandidates = @($workflowReviewRows | Where-Object { $_.archive_candidate -eq 'True' })

$deadDirRows = New-Object System.Collections.Generic.List[object]
$deadFileRows = New-Object System.Collections.Generic.List[object]
$archivedRows = New-Object System.Collections.Generic.List[object]
$executedRows = New-Object System.Collections.Generic.List[object]

$allDirs = Get-ChildItem -Path $repoRoot -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object {
        $relative = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $repoRoot
        $segments = $relative -split '/'
        -not ($segments | Where-Object { $excludeDirNames -contains $_ } | Select-Object -First 1)
    }

foreach ($dir in $allDirs) {
    if ($junkDirNames -contains $dir.Name) {
        $deadDirRows.Add([pscustomobject]@{
            path = Get-RepoRelativePath -FullPath $dir.FullName -RepoRoot $repoRoot
            type = 'junk_directory'
        }) | Out-Null
    }
}

$deadDirPaths = @($deadDirRows | Select-Object -ExpandProperty path)

$allFiles = Get-ChildItem -Path $repoRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $relative = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $repoRoot
        $segments = $relative -split '/'
        -not ($segments | Where-Object { $excludeDirNames -contains $_ } | Select-Object -First 1)
    }

foreach ($file in $allFiles) {
    $relative = Get-RepoRelativePath -FullPath $file.FullName -RepoRoot $repoRoot

    $isUnderDeadDir = $false
    foreach ($deadDir in $deadDirPaths) {
        if ($relative.StartsWith($deadDir + '/')) {
            $isUnderDeadDir = $true
            break
        }
    }
    if ($isUnderDeadDir) { continue }

    $isJunk = $false
    foreach ($rx in $junkFileRegexes) {
        if ($relative -match $rx) {
            $isJunk = $true
            break
        }
    }

    if ($isJunk) {
        $deadFileRows.Add([pscustomobject]@{
            path = $relative
            type = 'junk_file'
        }) | Out-Null
    }
}

if ($ArchiveStaleReleaseDocs -and $staleDocRows.Count -gt 0) {
    foreach ($row in $staleDocRows) {
        $source = Join-Path $repoRoot ($row.doc_path -replace '/', '\')
        if (Test-Path $source) {
            $moved = Move-ToArchive -Source $source -ArchiveRoot $archiveRoot -RepoRoot $repoRoot
            if ($moved) {
                $archivedRows.Add([pscustomobject]@{
                    category     = 'stale_release_doc'
                    source_path  = $moved.source_path
                    archive_path = $moved.archive_path
                }) | Out-Null
            }
        }
    }
}

if ($ArchiveDeadFileCandidates) {
    $deadDirRowsSorted = @($deadDirRows | Sort-Object { $_.path.Length } -Descending)
    foreach ($row in $deadDirRowsSorted) {
        $source = Join-Path $repoRoot ($row.path -replace '/', '\')
        if (Test-Path $source) {
            $moved = Move-ToArchive -Source $source -ArchiveRoot $archiveRoot -RepoRoot $repoRoot
            if ($moved) {
                $archivedRows.Add([pscustomobject]@{
                    category     = 'junk_directory'
                    source_path  = $moved.source_path
                    archive_path = $moved.archive_path
                }) | Out-Null
            }
        }
    }

    foreach ($row in $deadFileRows) {
        $source = Join-Path $repoRoot ($row.path -replace '/', '\')
        if (Test-Path $source) {
            $moved = Move-ToArchive -Source $source -ArchiveRoot $archiveRoot -RepoRoot $repoRoot
            if ($moved) {
                $archivedRows.Add([pscustomobject]@{
                    category     = 'junk_file'
                    source_path  = $moved.source_path
                    archive_path = $moved.archive_path
                }) | Out-Null
            }
        }
    }
}

if ($ApplyRemoteDeletes -or $ApplyLocalDeletes) {
    $args = @()
    if ($ApplyRemoteDeletes) { $args += '-ApplyRemoteDeletes' }
    if ($ApplyLocalDeletes)  { $args += '-ApplyLocalDeletes'  }

    $output = Invoke-PowerShellScript -ScriptPath $phase12ApplyScript -Arguments $args
    $executedRows.Add([pscustomobject]@{
        category = 'branch_cleanup'
        command  = ".\scripts\release\generated\phase12_apply_repo_hygiene.ps1 $($args -join ' ')".Trim()
        output   = $output
    }) | Out-Null
}

if ($ArchiveExtraWorkflows) {
    $output = Invoke-PowerShellScript -ScriptPath $phase13ArchiveScript -Arguments @('-Apply')
    $executedRows.Add([pscustomobject]@{
        category = 'workflow_cleanup'
        command  = '.\scripts\release\generated\phase13_archive_extra_workflows.ps1 -Apply'
        output   = $output
    }) | Out-Null
}

if ($Resynthesize) {
    $rebuildScripts = @(
        '.\scripts\release\phase10_live_release_gate_synthesis.ps1',
        '.\scripts\release\phase11_live_release_docs_refresh.ps1',
        '.\scripts\release\phase12_repo_hygiene_execution_pack.ps1',
        '.\scripts\release\phase13_workflow_canonicalization_plan.ps1',
        '.\scripts\release\phase14_live_evidence_pack_builder.ps1',
        '.\scripts\release\phase15_final_ship_decision_and_completion.ps1',
        '.\scripts\release\verify_all_15_phases.ps1'
    )

    foreach ($script in $rebuildScripts) {
        $resolved = Join-Path $repoRoot ($script -replace '^\.\\', '')
        $output = Invoke-PowerShellScript -ScriptPath $resolved
        $executedRows.Add([pscustomobject]@{
            category = 'resynthesis'
            command  = $script
            output   = $output
        }) | Out-Null
    }

    $phase12 = Get-Content -Path $phase12Json -Raw -Encoding UTF8 | ConvertFrom-Json
    $phase13 = Get-Content -Path $phase13Json -Raw -Encoding UTF8 | ConvertFrom-Json
    $phase12Summary = Get-SummaryNode -Document $phase12
    $phase13Summary = Get-SummaryNode -Document $phase13
}

$deadDirectories = if ($deadDirRows.Count -gt 0) { $deadDirRows.ToArray() } else { @() }
$deadFiles = if ($deadFileRows.Count -gt 0) { $deadFileRows.ToArray() } else { @() }
$archivedItems = if ($archivedRows.Count -gt 0) { $archivedRows.ToArray() } else { @() }
$executedItems = if ($executedRows.Count -gt 0) { $executedRows.ToArray() } else { @() }

$deadDirCsv = Join-Path $outDir 'phase16_dead_directory_candidates.csv'
$deadFileCsv = Join-Path $outDir 'phase16_dead_file_candidates.csv'
$archivedCsv = Join-Path $outDir 'phase16_archived_items.csv'
$executedCsv = Join-Path $outDir 'phase16_executed_actions.csv'
$summaryJson = Join-Path $outDir 'phase16_professional_repo_cleanup.json'
$summaryMd = Join-Path $outDir 'phase16_professional_repo_cleanup.md'
$liveMd = Join-Path $repoRoot 'docs\release\LIVE_PROFESSIONAL_REPO_CLEANUP.md'
$liveJson = Join-Path $repoRoot 'docs\release\LIVE_PROFESSIONAL_REPO_CLEANUP.json'

$deadDirectories | Export-Csv -Path $deadDirCsv -NoTypeInformation -Encoding UTF8
$deadFiles | Export-Csv -Path $deadFileCsv -NoTypeInformation -Encoding UTF8
$archivedItems | Export-Csv -Path $archivedCsv -NoTypeInformation -Encoding UTF8
$executedItems | Export-Csv -Path $executedCsv -NoTypeInformation -Encoding UTF8

$summary = [ordered]@{
    generated_at_utc        = (Get-Date).ToUniversalTime().ToString('o')
    stale_release_doc_count = Get-ItemCount $staleDocRows
    remote_delete_count     = [int]$phase12Summary.remote_delete_count
    local_delete_count      = [int]$phase12Summary.local_delete_count
    workflow_archive_count  = [int]$phase13Summary.archive_candidate_count
    dead_directory_count    = Get-ItemCount $deadDirectories
    dead_file_count         = Get-ItemCount $deadFiles
    archived_item_count     = Get-ItemCount $archivedItems
    executed_action_count   = Get-ItemCount $executedItems
    archive_root            = (Get-RepoRelativePath -FullPath $archiveRoot -RepoRoot $repoRoot)
}

@{
    generated_at_utc   = $summary.generated_at_utc
    summary            = $summary
    stale_release_docs = $staleDocRows
    dead_directories   = $deadDirectories
    dead_files         = $deadFiles
    archived_items     = $archivedItems
    executed_actions   = $executedItems
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
} | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8

$deadDirLines = if ((Get-ItemCount $deadDirectories) -gt 0) {
    (@($deadDirectories) | ForEach-Object { "- $($_.path)" }) -join "`r`n"
} else { '- none' }

$deadFileLines = if ((Get-ItemCount $deadFiles) -gt 0) {
    (@($deadFiles) | Select-Object -First 200 | ForEach-Object { "- $($_.path)" }) -join "`r`n"
} else { '- none' }

$archivedLines = if ((Get-ItemCount $archivedItems) -gt 0) {
    (@($archivedItems) | ForEach-Object { "- [$($_.category)] $($_.source_path) -> $($_.archive_path)" }) -join "`r`n"
} else { '- none' }

$executedLines = if ((Get-ItemCount $executedItems) -gt 0) {
    (@($executedItems) | ForEach-Object { "- [$($_.category)] $($_.command)" }) -join "`r`n"
} else { '- none' }

$liveMarkdown = @"
# LIVE PROFESSIONAL REPO CLEANUP

Generated UTC: $($summary.generated_at_utc)

## Summary
- stale release docs: $($summary.stale_release_doc_count)
- remote delete count: $($summary.remote_delete_count)
- local delete count: $($summary.local_delete_count)
- workflow archive candidates: $($summary.workflow_archive_count)
- dead directories: $($summary.dead_directory_count)
- dead files: $($summary.dead_file_count)
- archived items: $($summary.archived_item_count)
- executed actions: $($summary.executed_action_count)
- archive root: $($summary.archive_root)

## Dead Directory Candidates
$deadDirLines

## Dead File Candidates
$deadFileLines

## Archived Items
$archivedLines

## Executed Actions
$executedLines

## Artifact Paths
- docs/release/live-audit/phase16/phase16_dead_directory_candidates.csv
- docs/release/live-audit/phase16/phase16_dead_file_candidates.csv
- docs/release/live-audit/phase16/phase16_archived_items.csv
- docs/release/live-audit/phase16/phase16_executed_actions.csv
"@

Set-Content -Path $liveMd -Value $liveMarkdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $liveMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 16 CLEANUP COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live cleanup doc: $liveMd"
Write-Host ""
