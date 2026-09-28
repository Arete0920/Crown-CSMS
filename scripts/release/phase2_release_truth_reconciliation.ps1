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
        "User-Agent"           = "Crown2026-Phase2-ReleaseTruth"
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

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$phase1Json = Join-Path $script:RepoRoot "docs\release\live-audit\phase1\phase1_live_repo_baseline.json"
if (-not (Test-Path $phase1Json)) {
    throw "Phase 1 baseline not found: $phase1Json"
}

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase2"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

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

$currentState = [ordered]@{
    generated_at_utc   = (Get-Date).ToUniversalTime().ToString("o")
    default_branch     = if ($repoApi) { $repoApi.default_branch } else { "main" }
    open_pull_requests = $openPulls.Count
    open_issues        = $openIssues.Count
    release_count      = $releases.Count
    latest_push_at     = if ($repoApi) { $repoApi.pushed_at } else { $null }
    latest_updated_at  = if ($repoApi) { $repoApi.updated_at } else { $null }
}

$targetDocs = @(
    "docs/release/FINAL_RELEASE_GATE.md",
    "docs/release/FINAL_SIGNOFF_CHECKLIST.md",
    "docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md",
    "docs/release/MODULE_INVENTORY.md",
    "docs/release/WORKFLOW_CONSOLIDATION_PLAN.md",
    "docs/release/BRANCH_PROTECTION_EVIDENCE.md",
    "docs/release/SECURITY_GATES_EVIDENCE.md"
)

$mismatchRows = New-Object System.Collections.Generic.List[object]
$referenceRows = New-Object System.Collections.Generic.List[object]
$docRows = New-Object System.Collections.Generic.List[object]
$allReferencedPrs = New-Object System.Collections.Generic.HashSet[string]

foreach ($relativeDoc in $targetDocs) {
    $fullDoc = Join-Path $script:RepoRoot ($relativeDoc -replace '/', '\')
    $meta = Get-GitFileCommitMeta -RelativePath $relativeDoc

    $content = ""
    if (Test-Path $fullDoc) {
        $content = Get-Content -Path $fullDoc -Raw -Encoding UTF8
    }

    $statusTokens = @()
    foreach ($m in [regex]::Matches($content, '(?im)\b(PARTIAL|READY|CERTIFIED|PASS|FAILED|DEFERRED)\b')) {
        $statusTokens += $m.Groups[1].Value.ToUpperInvariant()
    }
    $statusTokens = @($statusTokens | Select-Object -Unique)

    $prCountClaims = [regex]::Matches($content, '(?im)\b(?<count>\d+)\s+open\s+(?:pull\s+requests?|PRs?)\b')
    foreach ($claim in $prCountClaims) {
        $claimed = [int]$claim.Groups["count"].Value
        $referenceRows.Add([pscustomobject]@{
            doc_path        = $relativeDoc
            reference_type  = "open_pull_requests_claim"
            reference_value = $claimed
            live_value      = $currentState.open_pull_requests
            match           = ($claimed -eq $currentState.open_pull_requests)
            note            = $claim.Value.Trim()
        }) | Out-Null

        if ($claimed -ne $currentState.open_pull_requests) {
            $mismatchRows.Add([pscustomobject]@{
                doc_path      = $relativeDoc
                mismatch_type = "open_pull_requests_claim"
                claimed_value = $claimed
                live_value    = $currentState.open_pull_requests
                evidence      = $claim.Value.Trim()
            }) | Out-Null
        }
    }

    $issueCountClaims = [regex]::Matches($content, '(?im)\b(?<count>\d+)\s+open\s+issues?\b')
    foreach ($claim in $issueCountClaims) {
        $claimed = [int]$claim.Groups["count"].Value
        $referenceRows.Add([pscustomobject]@{
            doc_path        = $relativeDoc
            reference_type  = "open_issues_claim"
            reference_value = $claimed
            live_value      = $currentState.open_issues
            match           = ($claimed -eq $currentState.open_issues)
            note            = $claim.Value.Trim()
        }) | Out-Null

        if ($claimed -ne $currentState.open_issues) {
            $mismatchRows.Add([pscustomobject]@{
                doc_path      = $relativeDoc
                mismatch_type = "open_issues_claim"
                claimed_value = $claimed
                live_value    = $currentState.open_issues
                evidence      = $claim.Value.Trim()
            }) | Out-Null
        }
    }

    foreach ($prRef in [regex]::Matches($content, '(?im)(?:PR\s*#|pull request\s*#|#)(?<num>\d{2,5})\b')) {
        [void]$allReferencedPrs.Add($prRef.Groups["num"].Value)
    }

    $docRows.Add([pscustomobject]@{
        doc_path               = $relativeDoc
        exists                 = $meta.exists
        last_commit_iso        = $meta.last_commit_iso
        commit_count           = $meta.commit_count
        status_tokens          = ($statusTokens -join ', ')
        open_pr_claim_count    = @($prCountClaims).Count
        open_issue_claim_count = @($issueCountClaims).Count
        referenced_pr_count    = ([regex]::Matches($content, '(?im)(?:PR\s*#|pull request\s*#|#)(?<num>\d{2,5})\b')).Count
        line_count             = if ($content) { ($content -split "`r?`n").Count } else { 0 }
    }) | Out-Null
}

$referencedPrStates = New-Object System.Collections.Generic.List[object]
foreach ($prNumber in ($allReferencedPrs | Sort-Object { [int]$_ })) {
    $prApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/pulls/$prNumber"
    $issueApi = Invoke-GitHubPublicApi -Uri "https://api.github.com/repos/Arete0920/Crown-CSMS/issues/$prNumber"

    $state = $null
    $mergedAt = $null
    $title = $null
    $kind = $null

    if ($prApi) {
        $state = $prApi.state
        $mergedAt = $prApi.merged_at
        $title = $prApi.title
        $kind = "pull_request"
    } elseif ($issueApi) {
        $state = $issueApi.state
        $mergedAt = $null
        $title = $issueApi.title
        $kind = "issue"
    } else {
        $state = "not_found"
        $mergedAt = $null
        $title = $null
        $kind = "unknown"
    }

    $referencedPrStates.Add([pscustomobject]@{
        number         = [int]$prNumber
        item_type      = $kind
        state          = $state
        merged_at      = $mergedAt
        title          = $title
        currently_open = ($state -eq "open")
    }) | Out-Null
}

$latestRelease = $null
if ($releases.Count -gt 0) {
    $latestRelease = $releases | Sort-Object { [datetimeoffset]$_.published_at } -Descending | Select-Object -First 1
}

$phase2Summary = [ordered]@{
    generated_at_utc            = $currentState.generated_at_utc
    live_repo_state             = $currentState
    target_doc_count            = $docRows.Count
    mismatch_count              = $mismatchRows.Count
    referenced_pr_count         = $referencedPrStates.Count
    latest_release_tag          = if ($latestRelease) { $latestRelease.tag_name } else { $null }
    latest_release_published_at = if ($latestRelease) { $latestRelease.published_at } else { $null }
}

$phase2SummaryJson = Join-Path $outDir "phase2_release_truth_reconciliation.json"
$docCsv = Join-Path $outDir "phase2_release_doc_inventory.csv"
$mismatchCsv = Join-Path $outDir "phase2_release_truth_mismatches.csv"
$referenceCsv = Join-Path $outDir "phase2_release_truth_references.csv"
$prRefCsv = Join-Path $outDir "phase2_referenced_pr_states.csv"
$mdPath = Join-Path $outDir "phase2_release_truth_reconciliation.md"
$liveTruthMd = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_TRUTH.md"
$liveTruthJson = Join-Path $script:RepoRoot "docs\release\LIVE_RELEASE_TRUTH.json"

$phase2Summary | ConvertTo-Json -Depth 6 | Set-Content -Path $phase2SummaryJson -Encoding UTF8
$docRows | Export-Csv -Path $docCsv -NoTypeInformation -Encoding UTF8
$mismatchRows | Export-Csv -Path $mismatchCsv -NoTypeInformation -Encoding UTF8
$referenceRows | Export-Csv -Path $referenceCsv -NoTypeInformation -Encoding UTF8
$referencedPrStates | Export-Csv -Path $prRefCsv -NoTypeInformation -Encoding UTF8

$mismatchLines = if ($mismatchRows.Count -gt 0) {
    ($mismatchRows | ForEach-Object {
        "- $($_.doc_path) | $($_.mismatch_type) | claimed=$($_.claimed_value) | live=$($_.live_value) | evidence=$($_.evidence)"
    }) -join "`r`n"
} else {
    "- none"
}

$docLines = ($docRows | ForEach-Object {
    "- $($_.doc_path) | exists=$($_.exists) | last_commit_iso=$($_.last_commit_iso) | statuses=$($_.status_tokens) | referenced_pr_count=$($_.referenced_pr_count)"
}) -join "`r`n"

$prLines = if ($referencedPrStates.Count -gt 0) {
    ($referencedPrStates | ForEach-Object {
        "- #$($_.number) | type=$($_.item_type) | state=$($_.state) | merged_at=$($_.merged_at) | title=$($_.title)"
    }) -join "`r`n"
} else {
    "- none"
}

$phase2Markdown = @"
# Phase 2 Release Truth Reconciliation

Generated UTC: $($phase2Summary.generated_at_utc)

## Live Repo State
- Default branch: $($currentState.default_branch)
- Open pull requests: $($currentState.open_pull_requests)
- Open issues: $($currentState.open_issues)
- Release count: $($currentState.release_count)
- Latest push at: $($currentState.latest_push_at)
- Latest updated at: $($currentState.latest_updated_at)

## Target Release Docs
$docLines

## Mismatches
$mismatchLines

## Referenced PR and Issue State
$prLines

## Generated Artifacts
- phase2_release_truth_reconciliation.json
- phase2_release_doc_inventory.csv
- phase2_release_truth_mismatches.csv
- phase2_release_truth_references.csv
- phase2_referenced_pr_states.csv
"@

Set-Content -Path $mdPath -Value $phase2Markdown -Encoding UTF8

$liveTruthMarkdown = @"
# LIVE RELEASE TRUTH

Generated UTC: $($phase2Summary.generated_at_utc)

## Current Public Repo State
- Repository: Arete0920/Crown-CSMS
- Default branch: $($currentState.default_branch)
- Open pull requests: $($currentState.open_pull_requests)
- Open issues: $($currentState.open_issues)
- Release count: $($currentState.release_count)
- Latest push at: $($currentState.latest_push_at)
- Latest updated at: $($currentState.latest_updated_at)
- Latest release tag: $($phase2Summary.latest_release_tag)
- Latest release published at: $($phase2Summary.latest_release_published_at)

## Release Truth Reconciliation
- Release docs checked: $($phase2Summary.target_doc_count)
- Mismatch count: $($phase2Summary.mismatch_count)
- Referenced PR and issue items checked: $($phase2Summary.referenced_pr_count)

## Mismatch Detail
$mismatchLines

## Referenced PR and Issue State
$prLines

## Source Artifacts
- docs/release/live-audit/phase2/phase2_release_truth_reconciliation.md
- docs/release/live-audit/phase2/phase2_release_truth_mismatches.csv
- docs/release/live-audit/phase2/phase2_referenced_pr_states.csv
"@

Set-Content -Path $liveTruthMd -Value $liveTruthMarkdown -Encoding UTF8

@{
    generated_at_utc = $phase2Summary.generated_at_utc
    live_repo_state  = $currentState
    mismatches       = $mismatchRows
    referenced_items = $referencedPrStates
    checked_docs     = $docRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveTruthJson -Encoding UTF8

Write-Host ""
Write-Host "PHASE 2 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live release truth: $liveTruthMd"
Write-Host ""
