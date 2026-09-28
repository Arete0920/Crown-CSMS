$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        $joined = ($output | ForEach-Object { "$_" }) -join "`n"
        throw "git $($Args -join ' ') failed.`n$joined"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Try-InvokeGit {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    try {
        return Invoke-Git -Args $Args
    } catch {
        return $null
    }
}

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FullPath,
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $relative = $FullPath.Substring($RepoRoot.Length).TrimStart('\', '/')
    return ($relative -replace '\\', '/')
}

function Get-GitFileCommitMeta {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $fullPath = Join-Path $script:RepoRoot ($RelativePath -replace '/', '\')
    if (-not (Test-Path $fullPath)) {
        return [pscustomobject]@{
            path            = $RelativePath
            exists          = $false
            last_commit_sha = $null
            last_commit_iso = $null
            commit_count    = 0
        }
    }

    $sha = Try-InvokeGit -Args @("log", "-1", "--format=%H", "--", $RelativePath)
    $iso = Try-InvokeGit -Args @("log", "-1", "--format=%cI", "--", $RelativePath)
    $countRaw = Try-InvokeGit -Args @("rev-list", "--count", "HEAD", "--", $RelativePath)

    $count = 0
    if ($countRaw) {
        [void][int]::TryParse($countRaw, [ref]$count)
    }

    return [pscustomobject]@{
        path            = $RelativePath
        exists          = $true
        last_commit_sha = $sha
        last_commit_iso = $iso
        commit_count    = $count
    }
}

function Invoke-GitHubPublicApi {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    $headers = @{
        "Accept"               = "application/vnd.github+json"
        "User-Agent"           = "Crown2026-Phase1-LiveRepoBaseline"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    try {
        return Invoke-RestMethod -Uri $Uri -Headers $headers -Method Get -TimeoutSec 30
    } catch {
        return $null
    }
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$requiredPaths = @(
    "backend",
    "frontend",
    ".github/workflows",
    "docs/release"
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path (Join-Path $script:RepoRoot $path))) {
        throw "Required path missing: $path"
    }
}

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase1"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$currentBranch = Invoke-Git -Args @("branch", "--show-current")
$headSha = Invoke-Git -Args @("rev-parse", "HEAD")
$shortSha = Invoke-Git -Args @("rev-parse", "--short", "HEAD")
$commitCount = [int](Invoke-Git -Args @("rev-list", "--count", "HEAD"))
$originUrl = Try-InvokeGit -Args @("remote", "get-url", "origin")
$statusShort = Try-InvokeGit -Args @("status", "--short")
$dirty = -not [string]::IsNullOrWhiteSpace($statusShort)

$localBranchLines = Invoke-Git -Args @(
    "for-each-ref",
    "--sort=-committerdate",
    "--format=%(refname:short)|%(objectname:short)|%(committerdate:iso8601)|%(upstream:short)",
    "refs/heads"
)

$localBranches = @()
if (-not [string]::IsNullOrWhiteSpace($localBranchLines)) {
    foreach ($line in ($localBranchLines -split "`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line.Split('|')
        $localBranches += [pscustomobject]@{
            branch          = $parts[0]
            short_sha       = $parts[1]
            committer_date  = $parts[2]
            upstream_branch = if ($parts.Length -ge 4) { $parts[3] } else { "" }
        }
    }
}

$workflowFiles = Get-ChildItem -Path (Join-Path $script:RepoRoot ".github\workflows") -File |
    Where-Object { $_.Extension -in @(".yml", ".yaml") } |
    Sort-Object Name

$workflowInventory = foreach ($wf in $workflowFiles) {
    $content = Get-Content -Path $wf.FullName -Raw
    $relativePath = Get-RepoRelativePath -FullPath $wf.FullName -RepoRoot $script:RepoRoot

    [pscustomobject]@{
        name                  = $wf.Name
        path                  = $relativePath
        size_bytes            = [int64]$wf.Length
        has_workflow_dispatch = ($content -match '(?m)^\s*workflow_dispatch\s*:')
        has_push              = ($content -match '(?m)^\s*push\s*:')
        has_pull_request      = ($content -match '(?m)^\s*pull_request\s*:')
        has_schedule          = ($content -match '(?m)^\s*schedule\s*:')
        has_proof             = ($wf.Name -match 'proof|gate|smoke|deploy|security|stale|health')
        last_commit_iso       = (Get-GitFileCommitMeta -RelativePath $relativePath).last_commit_iso
    }
}

$backendDirs = Get-ChildItem -Path (Join-Path $script:RepoRoot "backend") -Directory |
    Sort-Object Name

$backendModuleInventory = foreach ($dir in $backendDirs) {
    $hasAppSignals = @(
        (Test-Path (Join-Path $dir.FullName "apps.py")),
        (Test-Path (Join-Path $dir.FullName "models.py")),
        (Test-Path (Join-Path $dir.FullName "views.py")),
        (Test-Path (Join-Path $dir.FullName "urls.py")),
        (Test-Path (Join-Path $dir.FullName "admin.py")),
        (Test-Path (Join-Path $dir.FullName "migrations"))
    ) -contains $true

    if (-not $hasAppSignals) { continue }

    $relativePath = Get-RepoRelativePath -FullPath $dir.FullName -RepoRoot $script:RepoRoot

    $recursiveFileCount = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count

    [pscustomobject]@{
        module_name      = $dir.Name
        path             = $relativePath
        has_models       = Test-Path (Join-Path $dir.FullName "models.py")
        has_views        = Test-Path (Join-Path $dir.FullName "views.py")
        has_urls         = Test-Path (Join-Path $dir.FullName "urls.py")
        has_migrations   = Test-Path (Join-Path $dir.FullName "migrations")
        has_tests_dir    = Test-Path (Join-Path $dir.FullName "tests")
        file_count_total = $recursiveFileCount
        last_commit_iso  = (Get-GitFileCommitMeta -RelativePath $relativePath).last_commit_iso
    }
}

$frontendSurfaceInventory = Get-ChildItem -Path (Join-Path $script:RepoRoot "frontend") -Directory |
    Sort-Object Name |
    ForEach-Object {
        [pscustomobject]@{
            name             = $_.Name
            path             = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot
            file_count_total = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
            last_commit_iso  = (Get-GitFileCommitMeta -RelativePath (Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot)).last_commit_iso
        }
    }

$releaseDocTargets = @(
    "docs/release/FINAL_RELEASE_GATE.md",
    "docs/release/FINAL_SIGNOFF_CHECKLIST.md",
    "docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md",
    "docs/release/MODULE_INVENTORY.md",
    "docs/release/WORKFLOW_CONSOLIDATION_PLAN.md",
    "docs/release/BRANCH_PROTECTION_EVIDENCE.md",
    "docs/release/SECURITY_GATES_EVIDENCE.md"
)

$releaseDocFreshness = foreach ($doc in $releaseDocTargets) {
    Get-GitFileCommitMeta -RelativePath $doc
}

$rootRulesetFiles = Get-ChildItem -Path $script:RepoRoot -File -Filter "ruleset_*.json" |
    Sort-Object Name |
    ForEach-Object {
        [pscustomobject]@{
            name            = $_.Name
            path            = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot
            size_bytes      = [int64]$_.Length
            last_commit_iso = (Get-GitFileCommitMeta -RelativePath (Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot)).last_commit_iso
        }
    }

$repoApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS"
$pullsApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/pulls?state=open&per_page=100"
$issuesApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/issues?state=open&per_page=100"
$releasesApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/releases?per_page=100"

$openPulls = @()
if ($pullsApi) { $openPulls = @($pullsApi) }

$openIssues = @()
if ($issuesApi) {
    $openIssues = @($issuesApi | Where-Object { -not $_.pull_request })
}

$releases = @()
if ($releasesApi) { $releases = @($releasesApi) }

$workflowCount = @($workflowInventory).Count
$backendModuleCount = @($backendModuleInventory).Count
$frontendSurfaceCount = @($frontendSurfaceInventory).Count
$localBranchCount = @($localBranches).Count
$releaseDocCount = @($releaseDocFreshness).Count
$rootRulesetCount = @($rootRulesetFiles).Count

$workflowDispatchCount = @($workflowInventory | Where-Object { $_.has_workflow_dispatch }).Count
$workflowPushCount = @($workflowInventory | Where-Object { $_.has_push }).Count
$workflowPullRequestCount = @($workflowInventory | Where-Object { $_.has_pull_request }).Count
$workflowScheduleCount = @($workflowInventory | Where-Object { $_.has_schedule }).Count

$summary = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    repo = [ordered]@{
        name               = "Arete0920/Crown-CSMS"
        repo_root          = $script:RepoRoot
        origin_url         = $originUrl
        current_branch     = $currentBranch
        head_sha           = $headSha
        head_short_sha     = $shortSha
        commit_count       = $commitCount
        dirty_working_tree = $dirty
    }
    inventories = [ordered]@{
        local_branch_count     = $localBranchCount
        workflow_count         = $workflowCount
        backend_module_count   = $backendModuleCount
        frontend_surface_count = $frontendSurfaceCount
        release_doc_count      = $releaseDocCount
        root_ruleset_count     = $rootRulesetCount
    }
    github_public = [ordered]@{
        default_branch     = if ($repoApi) { $repoApi.default_branch } else { $null }
        open_pull_requests = @($openPulls).Count
        open_issues        = @($openIssues).Count
        release_count      = @($releases).Count
        pushed_at          = if ($repoApi) { $repoApi.pushed_at } else { $null }
        updated_at         = if ($repoApi) { $repoApi.updated_at } else { $null }
        watchers_count     = if ($repoApi) { $repoApi.watchers_count } else { $null }
        forks_count        = if ($repoApi) { $repoApi.forks_count } else { $null }
    }
    workflow_triggers = [ordered]@{
        workflow_dispatch = $workflowDispatchCount
        push              = $workflowPushCount
        pull_request      = $workflowPullRequestCount
        schedule          = $workflowScheduleCount
    }
}

$summaryJsonPath = Join-Path $outDir "phase1_live_repo_baseline.json"
$summaryMdPath = Join-Path $outDir "phase1_live_repo_baseline.md"
$branchCsvPath = Join-Path $outDir "phase1_branch_inventory.csv"
$workflowCsvPath = Join-Path $outDir "phase1_workflow_inventory.csv"
$backendCsvPath = Join-Path $outDir "phase1_backend_module_inventory.csv"
$frontendCsvPath = Join-Path $outDir "phase1_frontend_surface_inventory.csv"
$releaseDocCsvPath = Join-Path $outDir "phase1_release_doc_freshness.csv"
$rootRulesetCsvPath = Join-Path $outDir "phase1_root_ruleset_inventory.csv"
$githubPublicJsonPath = Join-Path $outDir "phase1_github_public_state.json"

$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryJsonPath -Encoding UTF8
@{
    repo          = $summary.repo
    github_public = $summary.github_public
    open_pulls    = $openPulls
    open_issues   = $openIssues
    releases      = $releases
} | ConvertTo-Json -Depth 8 | Set-Content -Path $githubPublicJsonPath -Encoding UTF8

$localBranches | Export-Csv -Path $branchCsvPath -NoTypeInformation -Encoding UTF8
$workflowInventory | Export-Csv -Path $workflowCsvPath -NoTypeInformation -Encoding UTF8
$backendModuleInventory | Export-Csv -Path $backendCsvPath -NoTypeInformation -Encoding UTF8
$frontendSurfaceInventory | Export-Csv -Path $frontendCsvPath -NoTypeInformation -Encoding UTF8
$releaseDocFreshness | Export-Csv -Path $releaseDocCsvPath -NoTypeInformation -Encoding UTF8
$rootRulesetFiles | Export-Csv -Path $rootRulesetCsvPath -NoTypeInformation -Encoding UTF8

$topBackendModules = ($backendModuleInventory | Sort-Object module_name | Select-Object -First 40 | ForEach-Object { "- $($_.module_name)" }) -join "`r`n"
$topWorkflows = ($workflowInventory | Sort-Object name | Select-Object -First 60 | ForEach-Object { "- $($_.name)" }) -join "`r`n"
$releaseDocLines = ($releaseDocFreshness | ForEach-Object {
    "- $($_.path) | exists=$($_.exists) | last_commit_iso=$($_.last_commit_iso) | commit_count=$($_.commit_count)"
}) -join "`r`n"

$markdown = @"
# Phase 1 Live Repo Baseline

Generated UTC: $($summary.generated_at_utc)

## Repo
- Name: Arete0920/Crown-CSMS
- Repo root: $($summary.repo.repo_root)
- Origin URL: $($summary.repo.origin_url)
- Current branch: $($summary.repo.current_branch)
- HEAD: $($summary.repo.head_short_sha)
- Commit count: $($summary.repo.commit_count)
- Dirty working tree: $($summary.repo.dirty_working_tree)

## Public GitHub State
- Default branch: $($summary.github_public.default_branch)
- Open pull requests: $($summary.github_public.open_pull_requests)
- Open issues: $($summary.github_public.open_issues)
- Release count: $($summary.github_public.release_count)
- Pushed at: $($summary.github_public.pushed_at)
- Updated at: $($summary.github_public.updated_at)

## Inventory Counts
- Local branches: $($summary.inventories.local_branch_count)
- Workflow files: $($summary.inventories.workflow_count)
- Backend modules: $($summary.inventories.backend_module_count)
- Frontend surfaces: $($summary.inventories.frontend_surface_count)
- Release docs tracked: $($summary.inventories.release_doc_count)
- Root ruleset json files: $($summary.inventories.root_ruleset_count)

## Workflow Trigger Counts
- workflow_dispatch: $($summary.workflow_triggers.workflow_dispatch)
- push: $($summary.workflow_triggers.push)
- pull_request: $($summary.workflow_triggers.pull_request)
- schedule: $($summary.workflow_triggers.schedule)

## Backend Modules Snapshot
$topBackendModules

## Workflow Files Snapshot
$topWorkflows

## Release Doc Freshness
$releaseDocLines

## Generated Artifacts
- phase1_live_repo_baseline.json
- phase1_github_public_state.json
- phase1_branch_inventory.csv
- phase1_workflow_inventory.csv
- phase1_backend_module_inventory.csv
- phase1_frontend_surface_inventory.csv
- phase1_release_doc_freshness.csv
- phase1_root_ruleset_inventory.csv
"@

Set-Content -Path $summaryMdPath -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 1 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Summary markdown: $summaryMdPath"
Write-Host "Summary json: $summaryJsonPath"
Write-Host ""
