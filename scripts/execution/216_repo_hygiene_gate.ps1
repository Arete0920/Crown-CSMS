param(
    [string]$OutputRoot = "audit-artifacts/repo-hygiene",
    [switch]$FailOnDirty,
    [switch]$IncludeNested
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Get-StatusKind {
    param([string]$Line)
    if ($Line.StartsWith("?? ")) { return "UNTRACKED" }
    if ($Line.StartsWith("!! ")) { return "IGNORED" }
    $xy = if ($Line.Length -ge 2) { $Line.Substring(0, 2) } else { $Line }
    if ($xy -match "D") { return "DELETED" }
    if ($xy -match "A") { return "ADDED" }
    if ($xy -match "R") { return "RENAMED" }
    if ($xy -match "C") { return "COPIED" }
    if ($xy -match "M") { return "MODIFIED" }
    return "OTHER"
}

function Get-StatusPath {
    param([string]$Line)
    if ($Line.Length -le 3) { return "" }
    $p = $Line.Substring(3)
    if ($p -match " -> ") { return ($p -split " -> ")[-1] }
    return $p.TrimEnd("/")
}

function Get-SafeDefaultDecision {
    param([string]$Kind, [string]$Path)
    $normalized = $Path -replace "\\", "/"
    if ($Kind -eq "DELETED") { return "NEEDS REVIEW" }
    if ($normalized -match "(^|/)local-backups(/|$)") { return "QUARANTINE" }
    if ($normalized -match "(^|/)(node_modules|.venv|venv|__pycache__|.pytest_cache|playwright-report|test-results)(/|$)") { return "QUARANTINE" }
    if ($normalized -match "(^|/)(tmp_|_tmp_|temp_|scratch_|backup_)") { return "QUARANTINE" }
    if ($normalized -match "\.(tmp|log|bak|swp)$") { return "QUARANTINE" }
    return "NEEDS REVIEW"
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot (Join-Path $OutputRoot $stamp)
$latestDir = Join-Path $repoRoot (Join-Path $OutputRoot "latest")
New-Dir $outDir
New-Dir $latestDir

$branch = (git branch --show-current).Trim()
$head = (git rev-parse HEAD).Trim()
$statusLines = @(git status --porcelain=v1)
$deletedLines = @(git ls-files -d)
$diffNameStatus = @(git diff --name-status)
$worktrees = @(git worktree list --porcelain)
$stashes = @(git stash list)

$rows = New-Object System.Collections.Generic.List[object]
foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $kind = Get-StatusKind -Line $line
    $path = Get-StatusPath -Line $line
    $rows.Add([pscustomobject]@{
        Status = $line.Substring(0, [math]::Min(2, $line.Length))
        Kind = $kind
        Path = $path
        DefaultDecision = Get-SafeDefaultDecision -Kind $kind -Path $path
        OwnerDecision = ""
        Owner = ""
        Notes = ""
    }) | Out-Null
}

$trackedDirty = @($statusLines | Where-Object { -not $_.StartsWith("?? ") })
$untracked = @($statusLines | Where-Object { $_.StartsWith("?? ") })
$quarantineSuggested = @($rows.ToArray() | Where-Object { $_.DefaultDecision -eq "QUARANTINE" })
$needsReview = @($rows.ToArray() | Where-Object { $_.DefaultDecision -eq "NEEDS REVIEW" })

Write-Utf8 -Path (Join-Path $outDir "00_root_identity.txt") -Lines @("repo_root=$repoRoot", "branch=$branch", "head=$head", "generated=$(Get-Date -Format s)")
Write-Utf8 -Path (Join-Path $outDir "01_root_status_porcelain.txt") -Lines $statusLines
Write-Utf8 -Path (Join-Path $outDir "02_root_deleted_files.txt") -Lines $deletedLines
Write-Utf8 -Path (Join-Path $outDir "03_root_diff_name_status.txt") -Lines $diffNameStatus
Write-Utf8 -Path (Join-Path $outDir "04_git_worktree_list_porcelain.txt") -Lines $worktrees
Write-Utf8 -Path (Join-Path $outDir "05_git_stash_list.txt") -Lines $stashes
Write-CsvSafe -Path (Join-Path $outDir "20_root_change_triage.csv") -Rows @($rows.ToArray())

if ($IncludeNested) {
    $nestedRows = New-Object System.Collections.Generic.List[object]
    $gitDirs = Get-ChildItem -Path $repoRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq ".git" }
    foreach ($gitDir in $gitDirs) {
        $parent = Split-Path -Parent $gitDir.FullName
        if ($parent -eq $repoRoot) { continue }
        $nestedRows.Add([pscustomobject]@{
            Path = $parent.Replace($repoRoot + [System.IO.Path]::DirectorySeparatorChar, "")
            GitDir = $gitDir.FullName.Replace($repoRoot + [System.IO.Path]::DirectorySeparatorChar, "")
        }) | Out-Null
    }
    Write-CsvSafe -Path (Join-Path $outDir "21_nested_git_directories.csv") -Rows @($nestedRows.ToArray())
}

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = $branch
    head = $head
    status_count = $statusLines.Count
    tracked_dirty_count = $trackedDirty.Count
    untracked_count = $untracked.Count
    deleted_count = $deletedLines.Count
    quarantine_suggested_count = $quarantineSuggested.Count
    needs_review_count = $needsReview.Count
    clean = ($statusLines.Count -eq 0)
    pass = ($statusLines.Count -eq 0 -and $deletedLines.Count -eq 0)
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Repo Hygiene Gate Summary")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Branch: $branch")
$summary.Add("- Head: $head")
$summary.Add("- Status rows: $($statusLines.Count)")
$summary.Add("- Tracked dirty rows: $($trackedDirty.Count)")
$summary.Add("- Untracked rows: $($untracked.Count)")
$summary.Add("- Deleted files: $($deletedLines.Count)")
$summary.Add("- Quarantine suggested rows: $($quarantineSuggested.Count)")
$summary.Add("- Needs review rows: $($needsReview.Count)")
$summary.Add("")
$summary.Add("## Verdict")
$summary.Add("")
if ($status.pass) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
    $summary.Add("")
    $summary.Add("Do not commit product work from this worktree until every row in `20_root_change_triage.csv` has an owner decision and all untracked noise is quarantined or intentionally retained.")
}
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "REPO_HYGIENE_EVIDENCE=$outDir"
Write-Host "REPO_HYGIENE_SUMMARY=$(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "REPO_HYGIENE_TRIAGE=$(Join-Path $outDir '20_root_change_triage.csv')"

if ($FailOnDirty -and -not $status.pass) { exit 1 }
