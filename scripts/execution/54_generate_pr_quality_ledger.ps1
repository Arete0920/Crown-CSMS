param(
    [int]$MaxPulls = 0,
    [switch]$OpenFiles
)

$ErrorActionPreference = "Stop"
$env:GH_PAGER = "cat"
$env:GH_NO_UPDATE_NOTIFIER = "1"
$env:GH_PROMPT_DISABLED = "1"

function Set-Utf8File {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

function Invoke-GhJson {
    param([string[]]$Args)

    $raw = & gh @Args 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }

    $text = if ($raw -is [array]) { ($raw -join "`n") } else { [string]$raw }
    $text = $text.Trim()
    if (-not $text) { return $null }

    if (-not ($text.StartsWith("{") -or $text.StartsWith("["))) { return $null }

    try { return ($text | ConvertFrom-Json) }
    catch { return $null }
}

function Get-RepoInfo {
    $info = Invoke-GhJson -Args @("repo", "view", "--json", "owner,name,url,defaultBranchRef")
    if ($info -and $info.owner -and $info.name) {
        return [pscustomobject]@{
            Owner         = $info.owner.login
            Repo          = $info.name
            Url           = $info.url
            DefaultBranch = $info.defaultBranchRef.name
        }
    }

    $origin = (& git remote get-url origin 2>$null)
    if ($origin -and ($origin -match "github\.com[:/](?<owner>[^/]+)/(?<repo>[^/]+?)(\.git)?$")) {
        return [pscustomobject]@{
            Owner         = $Matches.owner
            Repo          = $Matches.repo
            Url           = "https://github.com/$($Matches.owner)/$($Matches.repo)"
            DefaultBranch = "main"
        }
    }

    return $null
}

function Get-RequiredContexts {
    param([string]$Owner, [string]$Repo)

    $bp = Invoke-GhJson -Args @("api", "repos/$Owner/$Repo/branches/main/protection")
    if (-not $bp -or -not $bp.required_status_checks -or -not $bp.required_status_checks.contexts) {
        return @()
    }
    return @($bp.required_status_checks.contexts)
}

function Get-MergedPulls {
    param([string]$Owner, [string]$Repo, [int]$MaxPulls)

    $limit = if ($MaxPulls -gt 0) { $MaxPulls } else { 1000 }
    $jsonFields = "number,title,author,mergedAt,url,headRefOid,headRefName,baseRefName"
    $raw = & gh pr list --repo "$Owner/$Repo" --state merged --limit $limit --json $jsonFields 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return @() }

    $text = if ($raw -is [array]) { ($raw -join "`n") } else { [string]$raw }
    $text = $text.Trim()
    if (-not $text) { return @() }

    try {
        $prs = $text | ConvertFrom-Json
        return @($prs)
    }
    catch {
        return @()
    }
}

function Get-CheckMap {
    param([string]$Owner, [string]$Repo, [string]$Sha)

    $map = @{}

    $statusObj = Invoke-GhJson -Args @("api", "repos/$Owner/$Repo/commits/$Sha/status")
    if ($statusObj -and $statusObj.statuses) {
        foreach ($s in @($statusObj.statuses)) {
            if ($s.context) { $map[$s.context] = [string]$s.state }
        }
    }

    $checkObj = Invoke-GhJson -Args @("api", "repos/$Owner/$Repo/commits/$Sha/check-runs?per_page=100")
    if ($checkObj -and $checkObj.check_runs) {
        foreach ($c in @($checkObj.check_runs)) {
            if ($c.name) {
                if ($c.status -and $c.status -ne "completed") {
                    $map[$c.name] = [string]$c.status
                }
                else {
                    $map[$c.name] = [string]$c.conclusion
                }
            }
        }
    }

    return $map
}

function Is-PassingState {
    param([string]$State)
    if (-not $State) { return $false }
    $v = $State.Trim().ToLowerInvariant()
    return @("success", "neutral", "skipped") -contains $v
}

function Get-PrFiles {
    param([string]$Owner, [string]$Repo, [int]$Number)

    $pr = Invoke-GhJson -Args @("pr", "view", $Number.ToString(), "--repo", "$Owner/$Repo", "--json", "files")
    if ($pr -and $pr.files) { return @($pr.files) }
    return @()
}

function Is-EvidencePath {
    param([string]$Path)

    $prefixes = @("audit-artifacts/", "docs/release/", "docs/audit/", "release-", "AUDIT_PACK_")
    foreach ($p in $prefixes) {
        if ($Path.StartsWith($p, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function Get-DeployRuns {
    param([string]$Owner, [string]$Repo)

    $runs = Invoke-GhJson -Args @(
        "run", "list",
        "--repo", "$Owner/$Repo",
        "--workflow", "deploy-prod.yml",
        "--limit", "200",
        "--json", "databaseId,status,conclusion,headSha,createdAt,displayTitle,url"
    )
    if (-not $runs) { return @() }
    return @($runs)
}

function Get-DeploySignal {
    param([object[]]$DeployRuns, [string]$Sha)

    $matches = @($DeployRuns | Where-Object { $_.headSha -eq $Sha })
    if ($matches.Count -eq 0) { return "none" }

    $latest = @($matches | Sort-Object createdAt -Descending | Select-Object -First 1)[0]
    if (-not $latest.conclusion) { return "in_progress" }

    $c = [string]$latest.conclusion
    if ($c -eq "success") { return "success" }
    return "failed"
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$repoInfo = Get-RepoInfo
if (-not $repoInfo) { throw "Unable to determine repository owner/name." }

$requiredContexts = Get-RequiredContexts -Owner $repoInfo.Owner -Repo $repoInfo.Repo
$requiredContexts = @($requiredContexts)
$prs = Get-MergedPulls -Owner $repoInfo.Owner -Repo $repoInfo.Repo -MaxPulls $MaxPulls
$deployRuns = Get-DeployRuns -Owner $repoInfo.Owner -Repo $repoInfo.Repo

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts\merged-pr-quality-ledger"
$out = Join-Path $base $ts
$latest = Join-Path $base "latest"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$rows = @()

foreach ($pr in $prs) {
    $sha = [string]$pr.headRefOid
    if (-not $sha) { $sha = "" }

    $checkMap = @{}
    if ($sha) {
        $checkMap = Get-CheckMap -Owner $repoInfo.Owner -Repo $repoInfo.Repo -Sha $sha
    }

    $requiredPassCount = 0
    foreach ($ctx in $requiredContexts) {
        if ($checkMap.ContainsKey($ctx) -and (Is-PassingState -State $checkMap[$ctx])) {
            $requiredPassCount++
        }
    }

    $checkObservedCount = $checkMap.Count
    $checkPassingCount = 0
    foreach ($k in $checkMap.Keys) {
        if (Is-PassingState -State ([string]$checkMap[$k])) {
            $checkPassingCount++
        }
    }
    $checkPassRate = 0.0
    if ($checkObservedCount -gt 0) {
        $checkPassRate = [math]::Round(($checkPassingCount / $checkObservedCount), 4)
    }

    $requiredTotal = $requiredContexts.Count
    $allRequiredPass = ($requiredTotal -eq 0) -or ($requiredPassCount -eq $requiredTotal)

    $files = Get-PrFiles -Owner $repoInfo.Owner -Repo $repoInfo.Repo -Number ([int]$pr.number)
    $evidenceTouched = 0
    $fileCount = @($files).Count
    $docLikeCount = 0
    $touchesWorkflows = $false
    $touchesBackend = $false
    $touchesFrontend = $false
    $touchesMigrations = $false
    $touchesSecuritySensitive = $false
    foreach ($f in $files) {
        if (-not $f.path) { continue }

        $path = [string]$f.path
        $pathLower = $path.ToLowerInvariant()

        if (Is-EvidencePath -Path $path) {
            $evidenceTouched++
        }

        if ($pathLower.StartsWith("docs/") -or $pathLower.EndsWith(".md")) {
            $docLikeCount++
        }
        if ($pathLower.StartsWith(".github/workflows/")) { $touchesWorkflows = $true }
        if ($pathLower.StartsWith("backend/")) { $touchesBackend = $true }
        if ($pathLower.StartsWith("frontend/")) { $touchesFrontend = $true }
        if ($pathLower -match "(^|/)migrations?(/|$)") { $touchesMigrations = $true }
        if ($pathLower -match "auth|security|secret|token|permission|credential|key") { $touchesSecuritySensitive = $true }
    }
    $docsOnly = ($fileCount -gt 0 -and $docLikeCount -eq $fileCount)

    $deploySignal = "none"
    if ($sha) { $deploySignal = Get-DeploySignal -DeployRuns $deployRuns -Sha $sha }

    $qualityScore = 0
    $classificationMode = "observability"

    # Sparse mode: no required contexts, no observed checks, and no concrete deploy link.
    $sparseObservability = ($requiredTotal -eq 0 -and $checkObservedCount -eq 0 -and @("none", "in_progress") -contains $deploySignal)

    if ($sparseObservability) {
        $classificationMode = "fallback-heuristics"
        $qualityScore = 65

        $titleLower = ([string]$pr.title).ToLowerInvariant()
        $headRefLower = ([string]$pr.headRefName).ToLowerInvariant()

        if ($docsOnly) { $qualityScore += 20 }
        if ($titleLower -match "^docs:|^docs\(|^docs\b") { $qualityScore += 20 }
        if ($titleLower -match "dependabot|deps|bump" -or $headRefLower -match "dependabot") { $qualityScore += 15 }
        if ($titleLower -match "^fix:|^fix\(|hotfix") { $qualityScore += 10 }

        if ($titleLower -match "^feat:|^feat\(|feature") { $qualityScore -= 15 }
        if ($titleLower -match "security|auth|permission|tenant") { $qualityScore -= 15 }
        if ($titleLower -match "ci|deploy|workflow|migration|release") { $qualityScore -= 20 }

        if ($touchesWorkflows) { $qualityScore -= 15 }
        if ($touchesMigrations) { $qualityScore -= 20 }
        if ($touchesBackend) { $qualityScore -= 10 }
        if ($touchesSecuritySensitive) { $qualityScore -= 10 }

        $authorLogin = $(if ($pr.author) { [string]$pr.author.login } else { "" }).ToLowerInvariant()
        if ($authorLogin -match "dependabot|\[bot\]") { $qualityScore += 10 }

        if ($fileCount -gt 50) { $qualityScore -= 20 }
        elseif ($fileCount -gt 20) { $qualityScore -= 10 }
        elseif ($fileCount -gt 10) { $qualityScore -= 5 }

        if ($evidenceTouched -ge 1) { $qualityScore += 5 }
    }
    else {
        # Check health contribution.
        if ($requiredTotal -gt 0) {
            $qualityScore += [int][math]::Round((($requiredPassCount / $requiredTotal) * 50), 0)
        }
        elseif ($checkObservedCount -gt 0) {
            $qualityScore += [int][math]::Round(($checkPassRate * 40), 0)
        }

        # Deploy signal contribution.
        if ($deploySignal -eq "success") { $qualityScore += 30 }
        elseif ($deploySignal -eq "in_progress") { $qualityScore += 15 }
        elseif ($deploySignal -eq "none") { $qualityScore += 5 }

        # Evidence touch contribution.
        if ($evidenceTouched -ge 3) { $qualityScore += 20 }
        elseif ($evidenceTouched -ge 1) { $qualityScore += 10 }
    }

    if ($qualityScore -lt 0) { $qualityScore = 0 }
    if ($qualityScore -gt 100) { $qualityScore = 100 }

    # Hard fail overrides.
    $class = "Yellow"
    if ($deploySignal -eq "failed" -or ($requiredTotal -gt 0 -and -not $allRequiredPass)) {
        $class = "Red"
    }
    elseif ($qualityScore -ge 80) {
        $class = "Green"
    }
    elseif ($qualityScore -lt 55) {
        $class = "Red"
    }

    $score = 100 - $qualityScore
    if ($score -lt 0) { $score = 0 }
    if ($score -gt 100) { $score = 100 }

    $rows += [pscustomobject]@{
        PRNumber               = [int]$pr.number
        Title                  = [string]$pr.title
        Author                 = $(if ($pr.author) { [string]$pr.author.login } else { "" })
        MergedAt               = [string]$pr.mergedAt
        BaseRef                = [string]$pr.baseRefName
        HeadRef                = [string]$pr.headRefName
        HeadSha                = $sha
        Url                    = [string]$pr.url
        RequiredContextsTotal  = $requiredTotal
        RequiredContextsPassed = $requiredPassCount
        RequiredChecksAllPass  = $allRequiredPass
        CheckRunsObserved      = $checkObservedCount
        CheckRunsPassing       = $checkPassingCount
        CheckPassRate          = $checkPassRate
        DeploySignal           = $deploySignal
        EvidenceTouchedCount   = $evidenceTouched
        ChangedFilesCount      = $fileCount
        DocsOnlyChange         = $docsOnly
        TouchesWorkflows       = $touchesWorkflows
        TouchesBackend         = $touchesBackend
        TouchesMigrations      = $touchesMigrations
        TouchesSecurity        = $touchesSecuritySensitive
        ClassificationMode     = $classificationMode
        QualityScore           = $qualityScore
        Classification         = $class
        RemediationScore       = $score
    }
}

$rows = @($rows | Sort-Object MergedAt -Descending)
$ranked = @($rows | Sort-Object -Property RemediationScore, MergedAt -Descending)

$green = @($rows | Where-Object { $_.Classification -eq "Green" }).Count
$yellow = @($rows | Where-Object { $_.Classification -eq "Yellow" }).Count
$red = @($rows | Where-Object { $_.Classification -eq "Red" }).Count
$total = $rows.Count

$contextPath = Join-Path $out "00_context.md"
$ledgerPath = Join-Path $out "02_merged_pr_quality_ledger.csv"
$rankPath = Join-Path $out "03_ranked_remediation_list.csv"
$summaryPath = Join-Path $out "04_summary.md"
$followupPath = Join-Path $out "05_recommended_followup.md"

$requiredContextLines = @($requiredContexts | ForEach-Object { "- $_" })
$requiredContextsBlock = if ($requiredContextLines.Count -gt 0) { [string]::Join("`n", $requiredContextLines) } else { "- (none)" }

Set-Utf8File -Path $contextPath -Content @"
# Merged PR Quality Ledger Context

- GeneratedAt: $(Get-Date -Format s)
- Repo: $($repoInfo.Owner)/$($repoInfo.Repo)
- RepoUrl: $($repoInfo.Url)
- DefaultBranch: $($repoInfo.DefaultBranch)
- MaxPulls: $MaxPulls
- RequiredContextsCount: $($requiredContexts.Count)

## Required Contexts
$requiredContextsBlock
"@

$rows | Export-Csv -Path $ledgerPath -NoTypeInformation -Encoding utf8
$ranked | Export-Csv -Path $rankPath -NoTypeInformation -Encoding utf8

Set-Utf8File -Path $summaryPath -Content @"
# Merged PR Quality Summary

- Total merged PRs analyzed: $total
- Green: $green
- Yellow: $yellow
- Red: $red

## Notes
- QualityScore is weighted from checks, deploy signal, and evidence-path touches.
- Red = hard fail (deploy failed or required checks fail) or low score (<55).
- Yellow = mid score (55-79) without hard failures.
- Green = high score (>=80) with no hard failures.
- ClassificationMode shows whether score came from direct observability or fallback heuristics.
"@

$top = @($ranked | Where-Object { $_.Classification -ne "Green" } | Select-Object -First 25)
$lines = @("# Recommended Follow-Up", "", "## Top Non-Green PRs")
if ($top.Count -eq 0) {
    $lines += "- No non-green PRs in the analyzed set."
}
else {
    foreach ($r in $top) {
        $lines += "- PR #$($r.PRNumber) [$($r.Classification)] score=$($r.RemediationScore) checks=$($r.RequiredContextsPassed)/$($r.RequiredContextsTotal) deploy=$($r.DeploySignal) evidence=$($r.EvidenceTouchedCount)"
    }
}
Set-Utf8File -Path $followupPath -Content ($lines -join "`n")

if (Test-Path $latest) { Remove-Item $latest -Recurse -Force }
New-Item -ItemType Directory -Force -Path $latest | Out-Null
Copy-Item (Join-Path $out "*") $latest -Recurse -Force

if ($OpenFiles) {
    Open-IfExists $contextPath
    Open-IfExists $ledgerPath
    Open-IfExists $rankPath
    Open-IfExists $summaryPath
    Open-IfExists $followupPath
}

Write-Host "Done: $out"
Write-Host "Latest: $latest"
Write-Host "Merged PRs analyzed: $total"
Write-Host "Green: $green | Yellow: $yellow | Red: $red"
