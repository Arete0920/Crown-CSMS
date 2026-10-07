param(
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$Commit = "",
    [switch]$UseRemoteHead = $true,
    [switch]$CreateTag,
    [string]$TagName = "",
    [switch]$OpenFiles,
    [switch]$RecreateWorktree
)

$ErrorActionPreference = "Stop"

function Set-Utf8File {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Add-Utf8Text {
    param([string]$Path, [string]$Content)
    $Content | Add-Content -Path $Path -Encoding utf8
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

function Run-Capture {
    param(
        [string]$Title,
        [string]$Path,
        [string]$CommandText
    )
    "=== $Title ===" | Set-Content -Path $Path -Encoding utf8
    "COMMAND: $CommandText" | Add-Content -Path $Path -Encoding utf8
    "" | Add-Content -Path $Path -Encoding utf8
    try {
        powershell -NoProfile -Command $CommandText 2>&1 | Out-File -FilePath $Path -Append -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Out-File -FilePath $Path -Append -Encoding utf8
    }
}

function Copy-TreeIfExists {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )
    if (Test-Path $SourceDir) {
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

        # Use robocopy for deep trees/long paths and tolerate partial copy warnings.
        $null = robocopy $SourceDir $TargetDir /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
        $rc = $LASTEXITCODE
        if ($rc -ge 8) {
            Write-Warning "Robocopy reported failures for source: $SourceDir (exit=$rc)"
        }
        return $true
    }
    return $false
}

function Get-LatestDir {
    param([string]$Root, [string]$Pattern = "*")
    if (-not (Test-Path $Root)) { return $null }
    return Get-ChildItem $Root -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like $Pattern } |
    Sort-Object Name -Descending |
    Select-Object -First 1
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$hardeningBase = Join-Path $repoRoot "audit-artifacts\release-truth-hardening"
$hardeningOut = Join-Path $hardeningBase $ts
$hardeningLatest = Join-Path $hardeningBase "latest"
New-Item -ItemType Directory -Force -Path $hardeningOut | Out-Null

# ----------------------------
# Local / remote state capture
# ----------------------------
Run-Capture -Title "Git status" -Path (Join-Path $hardeningOut "01_git_status.txt") -CommandText "git status --short --branch"
Run-Capture -Title "Recent local log" -Path (Join-Path $hardeningOut "02_git_log.txt") -CommandText "git log --oneline -20"
Run-Capture -Title "Fetch prune" -Path (Join-Path $hardeningOut "03_fetch_prune.txt") -CommandText "git fetch --all --prune"
Run-Capture -Title "Remote show" -Path (Join-Path $hardeningOut "04_remote_show.txt") -CommandText "git remote show $Remote"
Run-Capture -Title "Local diff summary" -Path (Join-Path $hardeningOut "05_diff_stat.txt") -CommandText "git diff --stat"
Run-Capture -Title "Untracked files" -Path (Join-Path $hardeningOut "06_untracked.txt") -CommandText "git ls-files --others --exclude-standard"
Run-Capture -Title "Modified tracked files" -Path (Join-Path $hardeningOut "07_modified_tracked.txt") -CommandText "git diff --name-only"
Run-Capture -Title "Staged files" -Path (Join-Path $hardeningOut "08_staged.txt") -CommandText "git diff --cached --name-only"

$localHead = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse ($Remote + "/" + $Branch)).Trim()
$currentBranch = (git branch --show-current).Trim()
$truthSha = ""
if ($Commit -ne "") {
    $truthSha = $Commit
}
elseif ($UseRemoteHead) {
    $truthSha = $remoteHead
}
else {
    $truthSha = $localHead
}

$shortTruth = $truthSha.Substring(0, 7)
$worktreeRoot = Join-Path (Split-Path $repoRoot -Parent) ("Crown2026_release_truth_" + $shortTruth)

Set-Utf8File -Path (Join-Path $hardeningOut "09_release_truth_selection.md") -Content @"
# Release Truth Selection

## Current branch
$currentBranch

## Local HEAD
$localHead

## Remote HEAD
$remoteHead

## Selected truth SHA
$truthSha

## Using remote head
$UseRemoteHead

## Requested commit override
$Commit

## Worktree root
$worktreeRoot
"@

# ----------------------------
# Full audit pack check
# ----------------------------
$auditPack = Get-LatestDir -Root $repoRoot -Pattern "AUDIT_PACK_*"
$expectedAuditFiles = @(
    "00_OVERVIEW.txt",
    "01_TREE.txt",
    "02_WORKFLOWS_INDEX.txt",
    "03_WORKFLOWS_TRIGGERS.txt",
    "04_JOB_LEVEL_IF.txt",
    "05_BRANCH_PROTECTION_MAIN.json",
    "06_BACKEND_URLS.txt",
    "07_MIGRATIONS.txt",
    "08_PY_DEPS.txt",
    "09_NODE_DEPS.txt",
    "10_SECRET_SCAN_FINDINGS.txt",
    "11_TRACKED_BINARIES.txt",
    "12_UNTRACKED_ARTIFACTS.txt",
    "13_HEALTH_PROBE.txt",
    "14_DEPLOY_PROD_RECENT.txt"
)

$auditReport = @()
$fullAuditPack = $false
if ($auditPack) {
    foreach ($f in $expectedAuditFiles) {
        $p = Join-Path $auditPack.FullName $f
        $auditReport += [pscustomobject]@{
            File   = $f
            Exists = (Test-Path $p)
            Path   = $p
        }
    }
    $fullAuditPack = ($auditReport | Where-Object { $_.Exists -eq $false }).Count -eq 0
}
$auditReport | Export-Csv (Join-Path $hardeningOut "10_audit_pack_completeness.csv") -NoTypeInformation -Encoding utf8

# ----------------------------
# Release artifact capture
# ----------------------------
$artifactMap = @(
    @{ Name = "release-master-gate"; Path = (Join-Path $repoRoot "audit-artifacts\release-master-gate\latest") },
    @{ Name = "release-control-center"; Path = (Join-Path $repoRoot "audit-artifacts\release-control-center\latest") },
    @{ Name = "release-candidate-packet"; Path = (Join-Path $repoRoot "audit-artifacts\release-candidate-packet\latest") },
    @{ Name = "release-day-command-pack"; Path = (Join-Path $repoRoot "audit-artifacts\release-day-command-pack\latest") },
    @{ Name = "release-execution-window"; Path = (Join-Path $repoRoot "audit-artifacts\release-execution-window\latest") },
    @{ Name = "release-launch"; Path = (Join-Path $repoRoot "audit-artifacts\release-launch\latest") },
    @{ Name = "release-war-room"; Path = (Join-Path $repoRoot "audit-artifacts\release-war-room") }
)

$copiedArtifacts = @()
foreach ($entry in $artifactMap) {
    $target = Join-Path $hardeningOut ("11_artifacts\" + $entry.Name)
    $copied = Copy-TreeIfExists -SourceDir $entry.Path -TargetDir $target
    $copiedArtifacts += [pscustomobject]@{
        Artifact = $entry.Name
        Source   = $entry.Path
        Copied   = $copied
    }
}
if ($auditPack) {
    $target = Join-Path $hardeningOut "11_artifacts\AUDIT_PACK"
    $copied = Copy-TreeIfExists -SourceDir $auditPack.FullName -TargetDir $target
    $copiedArtifacts += [pscustomobject]@{
        Artifact = "AUDIT_PACK"
        Source   = $auditPack.FullName
        Copied   = $copied
    }
}
$copiedArtifacts | Export-Csv (Join-Path $hardeningOut "11_artifacts_manifest.csv") -NoTypeInformation -Encoding utf8

# ----------------------------
# Deploy-prod history watch
# ----------------------------
$deployProdLog = Join-Path $hardeningOut "12_deploy_prod_recent.txt"
Run-Capture -Title "deploy-prod recent history" -Path $deployProdLog -CommandText "gh run list --limit 20 --workflow deploy-prod.yml --json databaseId,displayTitle,status,conclusion,createdAt,headSha,url"
$healthWatchLog = Join-Path $hardeningOut "14_prod_health_watch_recent.txt"
Run-Capture -Title "prod-health-watch recent history" -Path $healthWatchLog -CommandText "gh run list --limit 20 --workflow prod-health-watch.yml --json databaseId,displayTitle,status,conclusion,createdAt,headSha,url"

# ----------------------------
# Create safe worktree from release truth
# ----------------------------
if ((Test-Path $worktreeRoot) -and $RecreateWorktree) {
    try {
        git worktree remove $worktreeRoot --force | Out-Null
    }
    catch {}
    if (Test-Path $worktreeRoot) {
        Remove-Item $worktreeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path $worktreeRoot)) {
    git worktree add --detach $worktreeRoot $truthSha | Out-Null
}

$truthEvidenceRoot = Join-Path $worktreeRoot "_release_truth"
New-Item -ItemType Directory -Force -Path $truthEvidenceRoot | Out-Null

Set-Utf8File -Path (Join-Path $truthEvidenceRoot "01_RELEASE_TRUTH.md") -Content @"
# Release Truth

## Repo root
$repoRoot

## Worktree root
$worktreeRoot

## Selected truth SHA
$truthSha

## Local HEAD at capture
$localHead

## Remote HEAD at capture
$remoteHead

## Current branch at capture
$currentBranch

## Audit pack complete
$fullAuditPack

## Timestamp
$ts
"@

Set-Utf8File -Path (Join-Path $truthEvidenceRoot "02_OPERATING_RISKS.md") -Content @"
# Operating Risks

## High-priority controls
- release only from this clean worktree
- do not release from dirty local root
- use exact selected truth SHA
- keep latest full audit pack alongside release evidence
- treat deploy-prod recent history as active watch item

## Current evidence paths
- hardening root: $hardeningOut
- audit pack: $(if ($auditPack) { $auditPack.FullName } else { "MISSING" })
- release-control-center: $(Join-Path $repoRoot "audit-artifacts\release-control-center\latest")
- release-execution-window: $(Join-Path $repoRoot "audit-artifacts\release-execution-window\latest")
- release-launch: $(Join-Path $repoRoot "audit-artifacts\release-launch\latest")
"@

Set-Utf8File -Path (Join-Path $truthEvidenceRoot "03_DEPLOY_WATCH_MATRIX.csv") -Content @"
WatchArea,Owner,Status,Notes
deploy-prod recent history,Release owner,Open,Review 12_deploy_prod_recent.txt before release
prod-health-watch history,Verification owner,Open,Review 14_prod_health_watch_recent.txt before release
health probe after deploy,Verification owner,Open,Use release-launch latest probes
integrity probe after deploy,Verification owner,Open,Use release-launch latest probes
hypercare 15m,Verification owner,Open,Complete after release
hypercare 1h,Verification owner,Open,Complete after release
hypercare 4h,Verification owner,Open,Complete after release
hypercare next business day,Verification owner,Open,Complete after release
"@

Set-Utf8File -Path (Join-Path $truthEvidenceRoot "04_EXECUTE_FROM_TRUTH.ps1") -Content @'
param(
    [string]$DeployCommand = "",
    [string]$MigrationCommand = "",
    [string]$WarmupCommand = "",
    [string]$HealthUrl = "http://127.0.0.1:8000/api/health/",
    [string]$IntegrityUrl = "http://127.0.0.1:8000/api/integrity/"
)

$ErrorActionPreference = "Stop"

$worktreeRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $worktreeRoot

Write-Host "EXECUTING FROM CLEAN RELEASE TRUTH WORKTREE"
Write-Host "WORKTREE: $worktreeRoot"

if ($DeployCommand -ne "") {
    Write-Host "RUNNING DEPLOY COMMAND"
    powershell -NoProfile -Command $DeployCommand
}

if ($MigrationCommand -ne "") {
    Write-Host "RUNNING MIGRATION COMMAND"
    powershell -NoProfile -Command $MigrationCommand
}

if ($WarmupCommand -ne "") {
    Write-Host "RUNNING WARMUP COMMAND"
    powershell -NoProfile -Command $WarmupCommand
}

try {
    Write-Host "HEALTH PROBE"
    Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 30 | ConvertTo-Json -Depth 20
} catch {
    $_ | Out-String
}

try {
    Write-Host "INTEGRITY PROBE"
    Invoke-RestMethod -Uri $IntegrityUrl -Method Get -TimeoutSec 30 | ConvertTo-Json -Depth 20
} catch {
    $_ | Out-String
}
'@

Set-Utf8File -Path (Join-Path $truthEvidenceRoot "05_RELEASE_TRUTH_COMMANDS.ps1") -Content @"
code `"$truthEvidenceRoot\01_RELEASE_TRUTH.md`"
code `"$truthEvidenceRoot\02_OPERATING_RISKS.md`"
code `"$truthEvidenceRoot\03_DEPLOY_WATCH_MATRIX.csv`"
code `"$hardeningOut\10_audit_pack_completeness.csv`"
code `"$hardeningOut\11_artifacts_manifest.csv`"
code `"$hardeningOut\12_deploy_prod_recent.txt`"
code `"$hardeningOut\14_prod_health_watch_recent.txt`"
code `"$worktreeRoot\_release_truth\04_EXECUTE_FROM_TRUTH.ps1`"
"@

# ----------------------------
# Optional tag at exact truth SHA
# ----------------------------
if ($CreateTag) {
    if ($TagName -eq "") {
        $TagName = "release-truth-" + $shortTruth + "-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    }
    Run-Capture -Title "Create release truth tag" -Path (Join-Path $hardeningOut "15_create_tag.txt") -CommandText ("git tag " + $TagName + " " + $truthSha)
    Set-Utf8File -Path (Join-Path $truthEvidenceRoot "06_TAG_INFO.txt") -Content @"
TagName=$TagName
TruthSHA=$truthSha
"@
}

# ----------------------------
# Summary
# ----------------------------
$behindOrigin = $false
try {
    $remoteShow = Get-Content (Join-Path $hardeningOut "04_remote_show.txt") -Raw
    if ($remoteShow -match "behind") { $behindOrigin = $true }
}
catch {}

Set-Utf8File -Path (Join-Path $hardeningOut "SUMMARY.md") -Content @"
# Release Truth Hardening Summary

## Output root
$hardeningOut

## Selected truth SHA
$truthSha

## Clean worktree
$worktreeRoot

## Audit pack complete
$fullAuditPack

## Potential behind-origin indicator
$behindOrigin

## Next steps
- review 10_audit_pack_completeness.csv
- review 12_deploy_prod_recent.txt
- use only clean worktree for release execution
- use 04_EXECUTE_FROM_TRUTH.ps1 from worktree for deployment execution
"@

New-Item -ItemType Directory -Force -Path $hardeningLatest | Out-Null

# Non-destructive, long-path-tolerant sync of this run to latest.
$null = robocopy $hardeningOut $hardeningLatest /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
$syncRc = $LASTEXITCODE
if ($syncRc -ge 8) {
    Write-Warning "Latest sync reported failures (exit=$syncRc)"
}

if ($OpenFiles) {
    Open-IfExists (Join-Path $hardeningLatest "SUMMARY.md")
    Open-IfExists (Join-Path $hardeningLatest "09_release_truth_selection.md")
    Open-IfExists (Join-Path $hardeningLatest "10_audit_pack_completeness.csv")
    Open-IfExists (Join-Path $hardeningLatest "11_artifacts_manifest.csv")
    Open-IfExists (Join-Path $hardeningLatest "12_deploy_prod_recent.txt")
    Open-IfExists (Join-Path $hardeningLatest "14_prod_health_watch_recent.txt")
    Open-IfExists (Join-Path $truthEvidenceRoot "01_RELEASE_TRUTH.md")
    Open-IfExists (Join-Path $truthEvidenceRoot "02_OPERATING_RISKS.md")
    Open-IfExists (Join-Path $truthEvidenceRoot "03_DEPLOY_WATCH_MATRIX.csv")
    Open-IfExists (Join-Path $truthEvidenceRoot "04_EXECUTE_FROM_TRUTH.ps1")
}

Write-Host "Done: $hardeningOut"
Write-Host "Latest: $hardeningLatest"
Write-Host "Worktree: $worktreeRoot"
Write-Host "Truth SHA: $truthSha"
Write-Host "Audit pack complete: $fullAuditPack"
