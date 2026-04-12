$ErrorActionPreference = "Stop"

param(
    [string]$BaseBranch = "origin/main",
    [int]$MaxPRs = 20
)

$base = "audit-artifacts\pr-reconcile"
New-Item -ItemType Directory -Force -Path $base | Out-Null

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Get-RepoSlug {
    $remote = git remote get-url origin 2>$null
    if (-not $remote) { return "" }

    if ($remote -match 'github\.com[:/](.+?)(?:\.git)?$') {
        return $matches[1]
    }

    return ""
}

function Test-GhReady {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) { return $false }

    try {
        gh auth status 1>$null 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Get-RiskLevel {
    param(
        [int]$OverlapCount,
        [int]$HighRiskOverlapCount
    )

    $score = $OverlapCount + ($HighRiskOverlapCount * 3)

    if ($HighRiskOverlapCount -ge 5 -or $score -ge 20) { return "CRITICAL" }
    if ($HighRiskOverlapCount -ge 3 -or $score -ge 12) { return "HIGH" }
    if ($HighRiskOverlapCount -ge 1 -or $score -ge 5) { return "MEDIUM" }
    if ($OverlapCount -ge 1) { return "LOW" }
    return "NONE"
}

function Test-HighRiskPath {
    param([string]$Path)

    $patterns = @(
        '^\.github/workflows/',
        '^scripts/release/',
        '^backend/.+/api(?:_views)?\.py$',
        '^backend/.+/views\.py$',
        '^backend/.+/urls\.py$',
        '^backend/core/auth/views\.py$',
        '^frontend/dashboards/',
        '^docs/release/',
        '^release_closeout/',
        '^backend/core/api_schema\.py$'
    )

    foreach ($pattern in $patterns) {
        if ($Path -match $pattern) { return $true }
    }

    return $false
}

Write-Host "=== FETCH / REPO BASELINE ===" -ForegroundColor Cyan
git fetch origin --prune

"=== GIT STATUS ===" | Out-File "$base\00_git_status.txt"
git status --short | Add-Content "$base\00_git_status.txt"

"=== CURRENT BRANCH ===" | Out-File "$base\01_current_branch.txt"
git branch --show-current | Add-Content "$base\01_current_branch.txt"

"=== RECENT COMMITS ===" | Out-File "$base\02_recent_commits.txt"
git log --oneline -20 | Add-Content "$base\02_recent_commits.txt"

"=== LOCAL UNIQUE COMMITS VS BASE ===" | Out-File "$base\03_local_unique_commits.txt"
git log --oneline "$BaseBranch..HEAD" | Add-Content "$base\03_local_unique_commits.txt"

"=== LOCAL CHANGED FILES VS BASE ===" | Out-File "$base\04_local_changed_files.txt"
git diff --name-only "$BaseBranch...HEAD" | Add-Content "$base\04_local_changed_files.txt"

$localChanged = @()
if (Test-Path "$base\04_local_changed_files.txt") {
    $localChanged = Get-Content "$base\04_local_changed_files.txt" | Where-Object { $_.Trim() -ne "" } | Sort-Object -Unique
}

$localSet = @{}
foreach ($file in $localChanged) {
    $localSet[$file] = $true
}

$localRisk = foreach ($file in $localChanged) {
    [pscustomobject]@{
        File = $file
        HighRisk = (Test-HighRiskPath -Path $file)
    }
}
$localRisk | Export-Csv "$base\05_local_risk_files.csv" -NoTypeInformation

$repoSlug = Get-RepoSlug
$ghReady = Test-GhReady

$summaryLines = @()
$summaryLines += "# PR OVERLAP RECONCILIATION"
$summaryLines += ""
$summaryLines += "## Local Branch"
$summaryLines += ""
$summaryLines += "- Base branch: $BaseBranch"
$summaryLines += "- Local changed files: $($localChanged.Count)"
$summaryLines += "- GitHub CLI ready: $ghReady"
$summaryLines += ""

if (-not $ghReady -or -not $repoSlug) {
    $summaryLines += "## GitHub PR Audit"
    $summaryLines += ""
    $summaryLines += "GitHub CLI is not available/authenticated, or the origin remote is not a GitHub repo."
    $summaryLines += "Local reconciliation files were still generated."
    $summaryLines += ""
    $summaryLines += "### Next"
    $summaryLines += ""
    $summaryLines += '1. Authenticate GitHub CLI: `gh auth login`'
    $summaryLines += "2. Re-run this script"
    $summaryLines += ""
    Write-Utf8File -Path "docs/release/PR_OVERLAP_RECONCILIATION.md" -Content ($summaryLines -join "`r`n")
    Write-Host "DONE - local audit only. Authenticate gh and rerun for PR overlap." -ForegroundColor Yellow
    exit 0
}

Write-Host "=== OPEN PR LIST ===" -ForegroundColor Cyan
$prJsonPath = "$base\06_open_prs.json"
gh pr list --state open --limit $MaxPRs --json number,title,headRefName,baseRefName,isDraft,url,updatedAt > $prJsonPath

$prs = @()
if (Test-Path $prJsonPath) {
    $prs = Get-Content $prJsonPath -Raw | ConvertFrom-Json
}

$overlapRows = @()
$highRiskRows = @()

foreach ($pr in $prs) {
    Write-Host ("Checking PR #" + $pr.number + " " + $pr.title) -ForegroundColor DarkCyan

    $prFilePath = "$base\pr_$($pr.number)_files.txt"
    $prMetaPath = "$base\pr_$($pr.number)_meta.json"

    $pr | ConvertTo-Json -Depth 6 | Out-File $prMetaPath -Encoding utf8

    $apiPath = "repos/$repoSlug/pulls/$($pr.number)/files?per_page=100"
    gh api $apiPath --jq '.[].filename' > $prFilePath

    $prFiles = @()
    if (Test-Path $prFilePath) {
        $prFiles = Get-Content $prFilePath | Where-Object { $_.Trim() -ne "" } | Sort-Object -Unique
    }

    $overlap = foreach ($file in $prFiles) {
        if ($localSet.ContainsKey($file)) { $file }
    }

    $overlap = $overlap | Sort-Object -Unique
    $highRiskOverlap = $overlap | Where-Object { Test-HighRiskPath -Path $_ }

    $risk = Get-RiskLevel -OverlapCount $overlap.Count -HighRiskOverlapCount $highRiskOverlap.Count

    foreach ($file in $overlap) {
        $row = [pscustomobject]@{
            PRNumber = $pr.number
            PRTitle = $pr.title
            PRBranch = $pr.headRefName
            File = $file
            HighRisk = (Test-HighRiskPath -Path $file)
            Risk = $risk
            Url = $pr.url
        }
        $overlapRows += $row
        if ($row.HighRisk) { $highRiskRows += $row }
    }

    $single = @()
    $single += "# PR #$($pr.number) OVERLAP"
    $single += ""
    $single += "- Title: $($pr.title)"
    $single += "- Branch: $($pr.headRefName)"
    $single += "- Base: $($pr.baseRefName)"
    $single += "- Draft: $($pr.isDraft)"
    $single += "- Updated: $($pr.updatedAt)"
    $single += "- URL: $($pr.url)"
    $single += "- PR files scanned: $($prFiles.Count)"
    $single += "- Local overlap count: $($overlap.Count)"
    $single += "- High-risk overlap count: $($highRiskOverlap.Count)"
    $single += "- Risk: $risk"
    $single += ""
    $single += "## Overlapping Files"
    $single += ""
    if ($overlap.Count -eq 0) {
        $single += "_None_"
    }
    else {
        foreach ($file in $overlap) {
            $flag = if (Test-HighRiskPath -Path $file) { "HIGH-RISK" } else { "normal" }
            $single += "- [$flag] $file"
        }
    }

    Write-Utf8File -Path "$base\pr_$($pr.number)_overlap.md" -Content ($single -join "`r`n")
}

$overlapRows | Export-Csv "$base\07_pr_overlap_detail.csv" -NoTypeInformation
$highRiskRows | Export-Csv "$base\08_pr_overlap_high_risk.csv" -NoTypeInformation

$rollup = foreach ($pr in $prs) {
    $prOverlap = $overlapRows | Where-Object { $_.PRNumber -eq $pr.number }
    $prHigh = $prOverlap | Where-Object { $_.HighRisk -eq $true }
    [pscustomobject]@{
        PRNumber = $pr.number
        Title = $pr.title
        Branch = $pr.headRefName
        Draft = $pr.isDraft
        UpdatedAt = $pr.updatedAt
        OverlapCount = @($prOverlap).Count
        HighRiskOverlapCount = @($prHigh).Count
        Risk = Get-RiskLevel -OverlapCount @($prOverlap).Count -HighRiskOverlapCount @($prHigh).Count
        Url = $pr.url
    }
}

$rollup = $rollup | Sort-Object @{Expression = "HighRiskOverlapCount"; Descending = $true }, @{Expression = "OverlapCount"; Descending = $true }, @{Expression = "PRNumber"; Descending = $false }
$rollup | Export-Csv "$base\09_pr_overlap_rollup.csv" -NoTypeInformation

$summaryLines += "## Open PR Overlap Rollup"
$summaryLines += ""
$summaryLines += "| PR | Branch | Overlap | High-Risk | Risk |"
$summaryLines += "|---|---|---:|---:|---|"
foreach ($row in $rollup) {
    $summaryLines += "| #$($row.PRNumber) | `" + $row.Branch + "` | $($row.OverlapCount) | $($row.HighRiskOverlapCount) | $($row.Risk) |"
}

$summaryLines += ""
$summaryLines += "## Local High-Risk Areas"
$summaryLines += ""
$localHigh = $localRisk | Where-Object { $_.HighRisk -eq $true }
if (@($localHigh).Count -eq 0) {
    $summaryLines += "_None_"
}
else {
    foreach ($row in $localHigh) {
        $summaryLines += "- $($row.File)"
    }
}

$summaryLines += ""
$summaryLines += "## Required Action"
$summaryLines += ""
$summaryLines += "1. Do not merge any PR marked HIGH or CRITICAL until its overlap files are reviewed."
$summaryLines += '2. Start with `.github/workflows`, `scripts/release`, backend auth/url/api/views, and `frontend/dashboards`.'
$summaryLines += "3. Keep one canonical recovery branch and cherry-pick only the non-overlapping useful work from other PRs."
$summaryLines += "4. Close or supersede overlapping PRs after extraction."
$summaryLines += ""
$summaryLines += "## Output Files"
$summaryLines += ""
$summaryLines += '- `audit-artifacts/pr-reconcile/07_pr_overlap_detail.csv`'
$summaryLines += '- `audit-artifacts/pr-reconcile/08_pr_overlap_high_risk.csv`'
$summaryLines += '- `audit-artifacts/pr-reconcile/09_pr_overlap_rollup.csv`'
$summaryLines += '- `audit-artifacts/pr-reconcile/pr_<number>_overlap.md`'
$summaryLines += '- `docs/release/PR_OVERLAP_RECONCILIATION.md`'

Write-Utf8File -Path "docs/release/PR_OVERLAP_RECONCILIATION.md" -Content ($summaryLines -join "`r`n")

Write-Host "DONE" -ForegroundColor Green
Write-Host "Open docs\release\PR_OVERLAP_RECONCILIATION.md" -ForegroundColor Yellow
Write-Host "Open audit-artifacts\pr-reconcile\09_pr_overlap_rollup.csv" -ForegroundColor Yellow
