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

function Invoke-GitHubPublicApi {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    $headers = @{
        "Accept"               = "application/vnd.github+json"
        "User-Agent"           = "Crown2026-Phase3-WorkflowBranch"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    try {
        return Invoke-RestMethod -Uri $Uri -Headers $headers -Method Get -TimeoutSec 30
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

function Get-WorkflowCategory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $text = ($Name + "`n" + $Content).ToLowerInvariant()

    if ($text -match 'deploy|prod|staging|azure') { return "deploy" }
    if ($text -match 'proof|gate|smoke|health|integrity|cert') { return "proof_gate" }
    if ($text -match 'security|secret|codeql|dependency|audit') { return "security" }
    if ($text -match 'ui|frontend|dashboard|gradebook') { return "ui" }
    if ($text -match 'release|rc|tag') { return "release" }
    if ($text -match 'stale|cleanup|branch|repo-hygiene') { return "hygiene" }
    return "general"
}

function Get-DefaultBranchName {
    $repoApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS"
    if ($repoApi -and $repoApi.default_branch) {
        return $repoApi.default_branch
    }

    $originHead = Try-InvokeGit -Args @("symbolic-ref", "refs/remotes/origin/HEAD")
    if ($originHead -and $originHead -match 'refs/remotes/origin/(?<name>.+)$') {
        return $Matches["name"]
    }

    return "main"
}

function Get-DateAgeDays {
    param(
        [Parameter(Mandatory = $true)]
        [string]$IsoLike
    )

    if ([string]::IsNullOrWhiteSpace($IsoLike)) { return $null }
    $dt = [datetimeoffset]::Parse($IsoLike)
    return [int][math]::Floor(((Get-Date).ToUniversalTime() - $dt.UtcDateTime).TotalDays)
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$phase1Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase1\phase1_live_repo_baseline.json"
if (-not (Test-Path $phase1Json)) {
    throw "Phase 1 baseline not found: $phase1Json"
}

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase3"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$defaultBranch = Get-DefaultBranchName
$defaultRemoteRef = "origin/$defaultBranch"

$fetchResult = Try-InvokeGit -Args @("fetch", "origin", "--prune", "--tags")
if ($null -eq $fetchResult) {
    Try-InvokeGit -Args @("remote", "prune", "origin") | Out-Null
    Invoke-Git -Args @("fetch", "origin", "--tags") | Out-Null
} else {
    Try-InvokeGit -Args @("remote", "prune", "origin") | Out-Null
}

$liveRemoteHeadLines = Try-InvokeGit -Args @("ls-remote", "--heads", "origin")
$liveRemoteBranchSet = New-Object System.Collections.Generic.HashSet[string]
if ($liveRemoteHeadLines) {
    foreach ($line in ($liveRemoteHeadLines -split "`n")) {
        if ($line -match 'refs/heads/(?<name>.+)$') {
            [void]$liveRemoteBranchSet.Add($Matches["name"].Trim())
        }
    }
}

$workflowFiles = Get-ChildItem -Path (Join-Path $script:RepoRoot ".github\workflows") -File |
    Where-Object { $_.Extension -in @(".yml", ".yaml") } |
    Sort-Object Name

$workflowRows = @(foreach ($wf in $workflowFiles) {
    $content = Get-Content -Path $wf.FullName -Raw -Encoding UTF8
    $relativePath = Get-RepoRelativePath -FullPath $wf.FullName -RepoRoot $script:RepoRoot
    $category = Get-WorkflowCategory -Name $wf.Name -Content $content

    [pscustomobject]@{
        workflow_name           = $wf.Name
        path                    = $relativePath
        category                = $category
        size_bytes              = [int64]$wf.Length
        has_workflow_dispatch   = ($content -match '(?m)^\s*workflow_dispatch\s*:')
        has_push                = ($content -match '(?m)^\s*push\s*:')
        has_pull_request        = ($content -match '(?m)^\s*pull_request\s*:')
        has_schedule            = ($content -match '(?m)^\s*schedule\s*:')
        mentions_prod           = ($content -match '(?im)\bprod\b|\bproduction\b')
        mentions_deploy         = ($content -match '(?im)\bdeploy\b')
        mentions_security       = ($content -match '(?im)\bsecurity\b|\bcodeql\b|\bsecret\b|\bdependency\b')
        mentions_ui             = ($content -match '(?im)\bui\b|\bfrontend\b|\bdashboard\b|\bgradebook\b')
        consolidation_group_key = $category
    }
})

$workflowGroupRows = @($workflowRows |
    Group-Object consolidation_group_key |
    Sort-Object Name |
    ForEach-Object {
        [pscustomobject]@{
            group_key               = $_.Name
            workflow_count          = $_.Count
            has_multiple_candidates = ($_.Count -gt 1)
            workflow_names          = ($_.Group.workflow_name -join ', ')
            workflow_dispatch_count = @($_.Group | Where-Object { $_.has_workflow_dispatch }).Count
            push_count              = @($_.Group | Where-Object { $_.has_push }).Count
            pull_request_count      = @($_.Group | Where-Object { $_.has_pull_request }).Count
            schedule_count          = @($_.Group | Where-Object { $_.has_schedule }).Count
        }
    })

$openPulls = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/pulls?state=open&per_page=100"
$openPullHeadRefs = @()
if ($openPulls) {
    $openPullHeadRefs = @($openPulls | ForEach-Object { $_.head.ref } | Select-Object -Unique)
}

$mergedRemoteRefs = Try-InvokeGit -Args @("for-each-ref", "--merged=$defaultRemoteRef", "--format=%(refname:short)", "refs/remotes/origin")
$mergedRemoteSet = New-Object System.Collections.Generic.HashSet[string]
if ($mergedRemoteRefs) {
    foreach ($line in ($mergedRemoteRefs -split "`n")) {
        $trimmed = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            [void]$mergedRemoteSet.Add($trimmed)
        }
    }
}

$mergedLocalRefs = Try-InvokeGit -Args @("for-each-ref", "--merged=$defaultRemoteRef", "--format=%(refname:short)", "refs/heads")
$mergedLocalSet = New-Object System.Collections.Generic.HashSet[string]
if ($mergedLocalRefs) {
    foreach ($line in ($mergedLocalRefs -split "`n")) {
        $trimmed = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            [void]$mergedLocalSet.Add($trimmed)
        }
    }
}

$protectedBranchRegex = '^(main|master|develop|development|release|spine|prod|production|staging)$'
$protectedPrefixRegex = '^(release/|hotfix/|prod/|protect/|spine/)'

$remoteRefLines = Invoke-Git -Args @(
    "for-each-ref",
    "--sort=-committerdate",
    "--format=%(refname:short)|%(objectname:short)|%(committerdate:iso8601)",
    "refs/remotes/origin"
)

$remoteBranchRows = New-Object System.Collections.Generic.List[object]
foreach ($line in ($remoteRefLines -split "`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Split('|')
    if ($parts.Count -lt 3) { continue }

    $remoteRef = $parts[0].Trim()
    if ($remoteRef -eq "origin/HEAD" -or -not $remoteRef.StartsWith("origin/")) { continue }

    $branchName = $remoteRef.Substring("origin/".Length)
    if ($liveRemoteBranchSet.Count -gt 0 -and -not $liveRemoteBranchSet.Contains($branchName)) {
        continue
    }
    $ageDays = Get-DateAgeDays -IsoLike $parts[2]
    $isProtectedLike = ($branchName -match $protectedBranchRegex) -or ($branchName -match $protectedPrefixRegex)
    $hasOpenPr = $openPullHeadRefs -contains $branchName
    $isMerged = $mergedRemoteSet.Contains($remoteRef)

    $deleteCandidate = $false
    if ($isMerged -and -not $isProtectedLike -and -not $hasOpenPr -and $ageDays -ge 14) {
        $deleteCandidate = $true
    }

    $remoteBranchRows.Add([pscustomobject]@{
        remote_ref        = $remoteRef
        branch_name       = $branchName
        short_sha         = $parts[1]
        committer_date    = $parts[2]
        age_days          = $ageDays
        merged_to_default = $isMerged
        protected_like    = $isProtectedLike
        has_open_pr       = $hasOpenPr
        delete_candidate  = $deleteCandidate
    }) | Out-Null
}

$localRefLines = Invoke-Git -Args @(
    "for-each-ref",
    "--sort=-committerdate",
    "--format=%(refname:short)|%(objectname:short)|%(committerdate:iso8601)|%(upstream:short)",
    "refs/heads"
)

$localBranchRows = New-Object System.Collections.Generic.List[object]
foreach ($line in ($localRefLines -split "`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Split('|')
    if ($parts.Count -lt 3) { continue }

    $branchName = $parts[0].Trim()
    $ageDays = Get-DateAgeDays -IsoLike $parts[2]
    $isProtectedLike = ($branchName -match $protectedBranchRegex) -or ($branchName -match $protectedPrefixRegex)
    $hasOpenPr = $openPullHeadRefs -contains $branchName
    $isMerged = $mergedLocalSet.Contains($branchName)

    $deleteCandidate = $false
    if ($isMerged -and -not $isProtectedLike -and -not $hasOpenPr -and $ageDays -ge 14) {
        $deleteCandidate = $true
    }

    $localBranchRows.Add([pscustomobject]@{
        branch_name       = $branchName
        short_sha         = $parts[1]
        committer_date    = $parts[2]
        age_days          = $ageDays
        upstream_branch   = if ($parts.Count -ge 4) { $parts[3] } else { "" }
        merged_to_default = $isMerged
        protected_like    = $isProtectedLike
        has_open_pr       = $hasOpenPr
        delete_candidate  = $deleteCandidate
    }) | Out-Null
}

$remoteDeleteCandidateRows = @($remoteBranchRows | Where-Object { $_.delete_candidate } | Sort-Object branch_name)
$localDeleteCandidateRows = @($localBranchRows | Where-Object { $_.delete_candidate } | Sort-Object branch_name)

$remoteDeleteCommands = @($remoteDeleteCandidateRows | ForEach-Object { "git push origin --delete $($_.branch_name)" })
$localDeleteCommands = @($localDeleteCandidateRows | ForEach-Object { "git branch -d $($_.branch_name)" })

$summary = [ordered]@{
    generated_at_utc              = (Get-Date).ToUniversalTime().ToString("o")
    default_branch                = $defaultBranch
    workflow_count                = $workflowRows.Count
    workflow_group_count          = $workflowGroupRows.Count
    remote_branch_count           = $remoteBranchRows.Count
    local_branch_count            = $localBranchRows.Count
    remote_delete_candidate_count = $remoteDeleteCandidateRows.Count
    local_delete_candidate_count  = $localDeleteCandidateRows.Count
    open_pull_request_count       = $openPullHeadRefs.Count
}

$summaryJson = Join-Path $outDir "phase3_workflow_branch_rationalization.json"
$workflowCsv = Join-Path $outDir "phase3_workflow_inventory_enriched.csv"
$workflowGroupCsv = Join-Path $outDir "phase3_workflow_consolidation_groups.csv"
$remoteBranchCsv = Join-Path $outDir "phase3_remote_branch_inventory.csv"
$remoteDeleteCsv = Join-Path $outDir "phase3_branch_cleanup_candidates.csv"
$localBranchCsv = Join-Path $outDir "phase3_local_branch_inventory.csv"
$mdPath = Join-Path $outDir "phase3_workflow_branch_rationalization.md"
$remoteDeleteCmdPath = Join-Path $outDir "phase3_remote_branch_delete_commands.txt"
$localDeleteCmdPath = Join-Path $outDir "phase3_local_branch_delete_commands.txt"

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
$workflowRows | Export-Csv -Path $workflowCsv -NoTypeInformation -Encoding UTF8
$workflowGroupRows | Export-Csv -Path $workflowGroupCsv -NoTypeInformation -Encoding UTF8
$remoteBranchRows | Export-Csv -Path $remoteBranchCsv -NoTypeInformation -Encoding UTF8
$remoteDeleteCandidateRows | Export-Csv -Path $remoteDeleteCsv -NoTypeInformation -Encoding UTF8
$localBranchRows | Export-Csv -Path $localBranchCsv -NoTypeInformation -Encoding UTF8
if ($remoteDeleteCommands.Count -gt 0) {
    $remoteDeleteCommands | Set-Content -Path $remoteDeleteCmdPath -Encoding UTF8
} else {
    Set-Content -Path $remoteDeleteCmdPath -Value "" -Encoding UTF8
}
if ($localDeleteCommands.Count -gt 0) {
    $localDeleteCommands | Set-Content -Path $localDeleteCmdPath -Encoding UTF8
} else {
    Set-Content -Path $localDeleteCmdPath -Value "" -Encoding UTF8
}

$workflowGroupLines = ($workflowGroupRows | ForEach-Object {
    "- $($_.group_key) | workflow_count=$($_.workflow_count) | workflow_names=$($_.workflow_names)"
}) -join "`r`n"

$remoteBranchCandidateLines = if ($remoteDeleteCommands.Count -gt 0) {
    ($remoteDeleteCommands | ForEach-Object { "- $_" }) -join "`r`n"
} else {
    "- none"
}

$localBranchCandidateLines = if ($localDeleteCommands.Count -gt 0) {
    ($localDeleteCommands | ForEach-Object { "- $_" }) -join "`r`n"
} else {
    "- none"
}

$phase3Markdown = @"
# Phase 3 Workflow and Branch Rationalization

Generated UTC: $($summary.generated_at_utc)

## Default Branch
- $($summary.default_branch)

## Workflow Inventory
- Workflow count: $($summary.workflow_count)
- Workflow group count: $($summary.workflow_group_count)

## Workflow Consolidation Groups
$workflowGroupLines

## Branch Inventory
- Remote branch count: $($summary.remote_branch_count)
- Local branch count: $($summary.local_branch_count)
- Open pull request count: $($summary.open_pull_request_count)

## Remote Branch Delete Candidates
$remoteBranchCandidateLines

## Local Branch Delete Candidates
$localBranchCandidateLines

## Generated Artifacts
- phase3_workflow_branch_rationalization.json
- phase3_workflow_inventory_enriched.csv
- phase3_workflow_consolidation_groups.csv
- phase3_remote_branch_inventory.csv
- phase3_branch_cleanup_candidates.csv
- phase3_local_branch_inventory.csv
- phase3_remote_branch_delete_commands.txt
- phase3_local_branch_delete_commands.txt
"@

Set-Content -Path $mdPath -Value $phase3Markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 3 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Summary markdown: $mdPath"
Write-Host ""
