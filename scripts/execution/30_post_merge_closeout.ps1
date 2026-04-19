param(
    [int]$PR = 729,
    [string]$Branch = "main",
    [string]$FeatureBranch = "chore/deep-platform-audit",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$DeleteMergedLocalBranches,
    [switch]$StashDirtyWorktree
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param(
        [string]$Path,
        [string]$Title
    )
    "=== $Title ===" | Set-Content $Path
}

function Append-Text {
    param(
        [string]$Path,
        [string]$Text
    )
    $Text | Add-Content $Path
}

function Invoke-LoggedCommand {
    param(
        [string]$Title,
        [string]$Path,
        [scriptblock]$Command
    )

    Write-Section -Path $Path -Title $Title
    try {
        & $Command 2>&1 | Out-File -FilePath $Path -Append -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Out-File -FilePath $Path -Append -Encoding utf8
    }
}

function Save-Json {
    param(
        [string]$Path,
        [object]$Object
    )
    $Object | ConvertTo-Json -Depth 50 | Set-Content -Path $Path -Encoding utf8
}

function Try-Json {
    param(
        [scriptblock]$Command
    )
    try {
        $raw = & $Command
        if (-not $raw) { return $null }
        return ($raw | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot ("audit-artifacts\post-merge-closeout\" + $timestamp)
$baselineDir = Join-Path $base "01_post_merge_baseline"
$normalizeDir = Join-Path $base "02_local_normalization"
$evidenceDir = Join-Path $base "03_release_readiness"
$launchDir = Join-Path $base "04_launch_trackers"

New-Item -ItemType Directory -Force -Path $baselineDir, $normalizeDir, $evidenceDir, $launchDir | Out-Null

# ----------------------------
# 1) Post-merge baseline
# ----------------------------
$repoInfo = Try-Json { gh repo view --json "owner,name,url,defaultBranchRef" }
if (-not $repoInfo) {
    throw "GitHub CLI repo context could not be read. Confirm gh auth and repo context first."
}

$owner = $repoInfo.owner.login
$repoName = $repoInfo.name

$prInfo = Try-Json { gh pr view $PR --json "state,mergedAt,mergeCommit,isDraft,baseRefName,headRefName,url,title" }
$protection = Try-Json { gh api ("repos/{0}/{1}/branches/{2}/protection" -f $owner, $repoName, $Branch) }
$openPrs = Try-Json { gh pr list --state open --limit 100 --json "number,title,headRefName,baseRefName,isDraft,url" }
$mainRuns = Try-Json { gh run list --branch $Branch --limit 25 --json "workflowName,status,conclusion,createdAt,displayTitle,url,headSha" }
$remoteBranchExists = $false

try {
    $remoteRef = git ls-remote --heads origin $FeatureBranch
    if ($remoteRef) { $remoteBranchExists = $true }
}
catch {
    $remoteBranchExists = $false
}

if ($repoInfo) { Save-Json (Join-Path $baselineDir "repo_info.json") $repoInfo }
if ($prInfo) { Save-Json (Join-Path $baselineDir "pr_729.json") $prInfo }
if ($protection) { Save-Json (Join-Path $baselineDir "main_branch_protection.json") $protection }
if ($openPrs) { Save-Json (Join-Path $baselineDir "open_prs.json") $openPrs }
if ($mainRuns) { Save-Json (Join-Path $baselineDir "main_runs.json") $mainRuns }

Invoke-LoggedCommand "Repo status" (Join-Path $baselineDir "repo_status.txt") { git status --short --branch }
Invoke-LoggedCommand "Git remotes" (Join-Path $baselineDir "git_remotes.txt") { git remote -v }
Invoke-LoggedCommand "Recent main history" (Join-Path $baselineDir "main_log.txt") { git log --oneline -20 }
Invoke-LoggedCommand "Open PR count" (Join-Path $baselineDir "open_pr_count.txt") {
    gh pr list --state open --limit 100 --json number | ConvertFrom-Json | Measure-Object | Select-Object -ExpandProperty Count
}
Invoke-LoggedCommand "Feature branch on origin" (Join-Path $baselineDir "feature_branch_origin_check.txt") {
    if ($remoteBranchExists) { "EXISTS: $FeatureBranch" } else { "ABSENT: $FeatureBranch" }
}

# ----------------------------
# 2) Safe local normalization
# ----------------------------
$currentBranch = (git branch --show-current).Trim()
$dirtyBefore = (git status --short)

Invoke-LoggedCommand "Pre-normalization status" (Join-Path $normalizeDir "01_pre_status.txt") { git status --short --branch }

if ($dirtyBefore -and $StashDirtyWorktree) {
    Invoke-LoggedCommand "Stash dirty worktree" (Join-Path $normalizeDir "02_stash.txt") {
        git stash push -u -m ("post-merge-normalize-{0}" -f $timestamp)
    }
}
else {
    Write-Section (Join-Path $normalizeDir "02_stash.txt") "Stash dirty worktree"
    if ($dirtyBefore) {
        Append-Text (Join-Path $normalizeDir "02_stash.txt") "Dirty worktree detected."
        Append-Text (Join-Path $normalizeDir "02_stash.txt") "No stash was created because -StashDirtyWorktree was not used."
    }
    else {
        Append-Text (Join-Path $normalizeDir "02_stash.txt") "Worktree already clean."
    }
}

Invoke-LoggedCommand "Fetch all with prune and tags" (Join-Path $normalizeDir "03_fetch_prune.txt") { git fetch --all --prune --tags }
Invoke-LoggedCommand "Remote prune origin" (Join-Path $normalizeDir "04_remote_prune.txt") { git remote prune origin }
Invoke-LoggedCommand "Git gc" (Join-Path $normalizeDir "05_git_gc.txt") { git gc --prune=now }
Invoke-LoggedCommand "Pack refs" (Join-Path $normalizeDir "06_pack_refs.txt") { git pack-refs --all }
Invoke-LoggedCommand "Git fsck" (Join-Path $normalizeDir "07_git_fsck.txt") { git fsck --full }

$mergedLocalBranches = @()
try {
    $mergedLocalBranches = git branch --merged ("origin/" + $Branch) --format="%(refname:short)" |
    ForEach-Object { $_.Trim() } |
    Where-Object {
        $_ -and
        $_ -ne $currentBranch -and
        $_ -ne $Branch -and
        $_ -ne "main" -and
        $_ -ne "master" -and
        $_ -ne "develop"
    }
}
catch {
    $mergedLocalBranches = @()
}

$mergedLocalBranches | Set-Content (Join-Path $normalizeDir "08_merged_local_branches.txt") -Encoding utf8

if ($DeleteMergedLocalBranches -and $mergedLocalBranches.Count -gt 0) {
    Invoke-LoggedCommand "Delete merged local branches" (Join-Path $normalizeDir "09_delete_merged_local_branches.txt") {
        foreach ($b in $mergedLocalBranches) {
            git branch -d $b
        }
    }
}
else {
    Write-Section (Join-Path $normalizeDir "09_delete_merged_local_branches.txt") "Delete merged local branches"
    if ($mergedLocalBranches.Count -eq 0) {
        Append-Text (Join-Path $normalizeDir "09_delete_merged_local_branches.txt") "No merged local branches eligible for deletion."
    }
    else {
        Append-Text (Join-Path $normalizeDir "09_delete_merged_local_branches.txt") "Eligible merged branches were listed in 08_merged_local_branches.txt."
        Append-Text (Join-Path $normalizeDir "09_delete_merged_local_branches.txt") "No deletion was performed because -DeleteMergedLocalBranches was not used."
    }
}

Invoke-LoggedCommand "Post-normalization status" (Join-Path $normalizeDir "10_post_status.txt") { git status --short --branch }

# ----------------------------
# 3) Release-readiness evidence
# ----------------------------
Invoke-LoggedCommand "Branch protection export" (Join-Path $evidenceDir "01_branch_protection_export.txt") {
    gh api ("repos/{0}/{1}/branches/{2}/protection" -f $owner, $repoName, $Branch)
}

Invoke-LoggedCommand "Latest main runs" (Join-Path $evidenceDir "02_latest_main_runs.txt") {
    gh run list --branch $Branch --limit 25 --json "workflowName,status,conclusion,createdAt,displayTitle,url"
}

Invoke-LoggedCommand "Required checks currently enforced" (Join-Path $evidenceDir "03_required_checks.txt") {
    if ($protection -and $protection.required_status_checks -and $protection.required_status_checks.contexts) {
        $protection.required_status_checks.contexts
    }
    else {
        "Could not read required check contexts."
    }
}

if (Test-Path "backend\manage.py") {
    Invoke-LoggedCommand "Django check" (Join-Path $evidenceDir "04_django_check.txt") { python backend\manage.py check }
    Invoke-LoggedCommand "Django showmigrations" (Join-Path $evidenceDir "05_showmigrations.txt") { python backend\manage.py showmigrations }
    Invoke-LoggedCommand "Django deploy check" (Join-Path $evidenceDir "06_deploy_check.txt") { python backend\manage.py check --deploy }
}
else {
    Write-Section (Join-Path $evidenceDir "04_django_check.txt") "Django check"
    Append-Text (Join-Path $evidenceDir "04_django_check.txt") "backend\manage.py not found."
    Write-Section (Join-Path $evidenceDir "05_showmigrations.txt") "Django showmigrations"
    Append-Text (Join-Path $evidenceDir "05_showmigrations.txt") "backend\manage.py not found."
    Write-Section (Join-Path $evidenceDir "06_deploy_check.txt") "Django deploy check"
    Append-Text (Join-Path $evidenceDir "06_deploy_check.txt") "backend\manage.py not found."
}

Invoke-LoggedCommand "Health endpoint" (Join-Path $evidenceDir "07_health_endpoint.txt") {
    try {
        Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/health/") -Method Get -TimeoutSec 20 | ConvertTo-Json -Depth 20
    }
    catch {
        $_ | Out-String
    }
}

Invoke-LoggedCommand "Integrity endpoint" (Join-Path $evidenceDir "08_integrity_endpoint.txt") {
    try {
        Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/integrity/") -Method Get -TimeoutSec 20 | ConvertTo-Json -Depth 20
    }
    catch {
        $_ | Out-String
    }
}

$workflowFiles = @()
if (Test-Path ".github\workflows") {
    $workflowFiles = Get-ChildItem ".github\workflows" -File -Recurse | Where-Object { $_.Extension -in ".yml", ".yaml" }
}

$workflowListPath = Join-Path $evidenceDir "09_workflow_inventory.txt"
Write-Section $workflowListPath "Workflow inventory"
if ($workflowFiles.Count -gt 0) {
    $workflowFiles.FullName | Add-Content $workflowListPath
}
else {
    Add-Content $workflowListPath "No workflow files found."
}

$gateHitPath = Join-Path $evidenceDir "10_gate_hits.txt"
Write-Section $gateHitPath "Gate hits"
$gatePatterns = @(
    "CodeQL",
    "backend-gate",
    "contract-gate",
    "routes-gate",
    "pytest-gate",
    "dashboards-build-gate",
    "secret-scan",
    "workflow_dispatch:",
    "pull_request:",
    "push:",
    "schedule:"
)

if ($workflowFiles.Count -gt 0) {
    foreach ($pattern in $gatePatterns) {
        Add-Content $gateHitPath ("===== " + $pattern + " =====")
        try {
            Select-String -Path $workflowFiles.FullName -Pattern $pattern -SimpleMatch |
            ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
            Add-Content $gateHitPath
        }
        catch {
            Add-Content $gateHitPath ("ERROR: " + ($_ | Out-String))
        }
        Add-Content $gateHitPath ""
    }
}
else {
    Add-Content $gateHitPath "No workflow files found."
}

Invoke-LoggedCommand "API route search" (Join-Path $evidenceDir "11_route_search.txt") {
    $allFiles = Get-ChildItem -Recurse -File "backend" -ErrorAction SilentlyContinue | ForEach-Object FullName
    $patterns = @("/api/health/", "/api/integrity/", "urlpatterns", "include(", "path(")
    foreach ($p in $patterns) {
        "===== $p ====="
        Select-String -Path $allFiles -Pattern $p -SimpleMatch -ErrorAction SilentlyContinue |
        ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() }
        ""
    }
}

# ----------------------------
# 4) Launch-readiness trackers
# ----------------------------
$paymentTracker = @'
# Payment Validation Checklist

## Owner
- Primary:
- Secondary:

## Status
- Current status:
- Target date:

## Required evidence
- Executed payment agreement on file
- Sandbox credentials verified
- Live test transaction completed
- Reconciliation proof captured
- Refund / reversal path verified
- Finance sign-off recorded

## Notes
-
'@

$legalTracker = @'
# Legal / DPA Readiness

## Owner
- Primary:
- Secondary:

## Status
- Current status:
- Target date:

## Required evidence
- DPA template finalized
- Legal review completed
- School-facing version approved
- Signature workflow defined
- Data handling responsibilities confirmed
- Retention / deletion language confirmed

## Notes
-
'@

$pilotTracker = @'
# Pilot / LOI Tracker

| School | Contact | Stage | LOI | Pilot Start | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
'@

$taxonomyTracker = @'
# Core / Module / Add-on Classification Worksheet

| Item | Layer | Keep / Rewrite / Drop | Owner | Notes |
|---|---|---|---|---|
|  | Core |  |  |  |
|  | Module |  |  |  |
|  | Add-on |  |  |  |
'@

$paymentTracker | Set-Content (Join-Path $launchDir "01_payment_validation_checklist.md") -Encoding utf8
$legalTracker   | Set-Content (Join-Path $launchDir "02_legal_dpa_readiness.md") -Encoding utf8
$pilotTracker   | Set-Content (Join-Path $launchDir "03_pilot_loi_tracker.md") -Encoding utf8
$taxonomyTracker | Set-Content (Join-Path $launchDir "04_core_module_addon_tracker.md") -Encoding utf8

@"
School,Contact,Stage,LOI,PilotStart,Notes
"@ | Set-Content (Join-Path $launchDir "05_pilot_loi_tracker.csv") -Encoding utf8

# ----------------------------
# 5) Final summary
# ----------------------------
$requiredChecks = @()
if ($protection -and $protection.required_status_checks -and $protection.required_status_checks.contexts) {
    $requiredChecks = @($protection.required_status_checks.contexts)
}

$openPrCount = 0
if ($openPrs) {
    $openPrCount = @($openPrs).Count
}

$latestRunLines = @()
if ($mainRuns) {
    $latestRunLines = @($mainRuns | Select-Object -First 10 | ForEach-Object {
            "- {0} | {1} | {2} | {3}" -f $_.workflowName, $_.status, $_.conclusion, $_.createdAt
        })
}

$summary = @()
$summary += "# Post-Merge Closeout Summary"
$summary += ""
$summary += "## Repo"
$summary += "- Repo: $owner/$repoName"
$summary += "- Branch: $Branch"
$summary += "- Baseline artifact root: $base"
$summary += ""
$summary += "## PR 729"
if ($prInfo) {
    $summary += "- State: $($prInfo.state)"
    $summary += "- Merged at: $($prInfo.mergedAt)"
    $summary += "- Merge commit: $($prInfo.mergeCommit.oid)"
    $summary += "- URL: $($prInfo.url)"
}
else {
    $summary += "- PR details could not be read."
}
$summary += ""
$summary += "## Governance"
$summary += "- Admin enforcement: " + ($(if ($protection.enforce_admins.enabled) { "enabled" } else { "disabled or unknown" }))
$summary += "- Conversation resolution: " + ($(if ($protection.required_conversation_resolution.enabled) { "enabled" } else { "disabled or unknown" }))
$summary += "- Required checks:"
if ($requiredChecks.Count -gt 0) {
    foreach ($check in $requiredChecks) { $summary += "  - $check" }
}
else {
    $summary += "  - Could not read required checks"
}
$summary += ""
$summary += "## Queue / Branch Hygiene"
$summary += "- Open PR count: $openPrCount"
$summary += "- Remote feature branch present: " + ($(if ($remoteBranchExists) { "yes" } else { "no" }))
$summary += "- Current local branch: $currentBranch"
$summary += ""
$summary += "## Latest Main Runs"
if ($latestRunLines.Count -gt 0) {
    $summary += $latestRunLines
}
else {
    $summary += "- Could not read latest main runs."
}
$summary += ""
$summary += "## Local normalization"
$summary += "- Delete merged local branches used: $($DeleteMergedLocalBranches.IsPresent)"
$summary += "- Stash dirty worktree used: $($StashDirtyWorktree.IsPresent)"
$summary += ""
$summary += "## Output folders"
$summary += "- 01_post_merge_baseline"
$summary += "- 02_local_normalization"
$summary += "- 03_release_readiness"
$summary += "- 04_launch_trackers"
$summary += ""
$summary += "## Next manual items"
$summary += "- Review 03_release_readiness outputs."
$summary += "- Complete payment validation checklist."
$summary += "- Complete legal / DPA readiness."
$summary += "- Fill pilot / LOI tracker."
$summary += "- Continue Core / Module / Add-on classification."
$summary += ""

$summaryPath = Join-Path $base "SUMMARY.md"
$summary -join "`r`n" | Set-Content $summaryPath -Encoding utf8

Write-Host ""
Write-Host "Done: $base"
Write-Host "Summary: $summaryPath"
