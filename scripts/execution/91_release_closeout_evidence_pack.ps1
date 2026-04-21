param(
    [switch]$OpenPack,
    [switch]$CreateGitTag,
    [string]$TagName = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { throw "Not inside a git repository." }
    return $root.Trim()
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Normalize-Slash {
    param([string]$Path)
    return ($Path -replace "\\","/")
}

function Get-LatestDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

function Copy-IfExists {
    param(
        [string]$SourcePath,
        [string]$DestPath
    )
    if (Test-Path $SourcePath) {
        $destDir = Split-Path -Parent $DestPath
        if ($destDir -and -not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        Copy-Item -Path $SourcePath -Destination $DestPath -Force
        return $true
    }
    return $false
}

function Read-TextSafe {
    param([string]$Path)
    if (Test-Path $Path) {
        return Get-Content -Raw -Path $Path
    }
    return ""
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$artifactRoot = Join-Path $repoRoot ("audit-artifacts\release_closeout_evidence_pack\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null

$gateBase    = Join-Path $repoRoot "audit-artifacts\gate_finalization_and_executive_completion"
$phase5Base  = Join-Path $repoRoot "audit-artifacts\phase5_core_build_enforcement"
$phase6Base  = Join-Path $repoRoot "audit-artifacts\phase6_first_wave_module_enforcement"
$phase7Base  = Join-Path $repoRoot "audit-artifacts\phase7_hardening_release_enforcement"
$phase567Base= Join-Path $repoRoot "audit-artifacts\phase567_master_summary"
$phase12Base = Join-Path $repoRoot "audit-artifacts\phase12_decision_closer"

$latestGate    = Get-LatestDir -BasePath $gateBase
$latestPhase5  = Get-LatestDir -BasePath $phase5Base
$latestPhase6  = Get-LatestDir -BasePath $phase6Base
$latestPhase7  = Get-LatestDir -BasePath $phase7Base
$latestPhase567= Get-LatestDir -BasePath $phase567Base
$latestPhase12 = Get-LatestDir -BasePath $phase12Base

if (-not $latestGate) {
    throw "Missing gate finalization artifacts under: $gateBase"
}

$execSummaryPath = Join-Path $latestGate.FullName "EXECUTIVE_COMPLETION_SUMMARY.md"
$gateSummaryPath = Join-Path $latestGate.FullName "GATE_FINALIZATION_SUMMARY.md"
$gateMatrixPath  = Join-Path $latestGate.FullName "gate_decision_matrix.csv"

if (-not (Test-Path $execSummaryPath)) { throw "Missing EXECUTIVE_COMPLETION_SUMMARY.md" }
if (-not (Test-Path $gateSummaryPath)) { throw "Missing GATE_FINALIZATION_SUMMARY.md" }
if (-not (Test-Path $gateMatrixPath))  { throw "Missing gate_decision_matrix.csv" }

$execSummaryText = Read-TextSafe -Path $execSummaryPath
if ($execSummaryText -notmatch "Overall status:\s+COMPLETE") {
    throw "Latest executive summary is not COMPLETE."
}
if ($execSummaryText -notmatch "Approved gates:\s+7") {
    throw "Latest executive summary does not show 7 approved gates."
}
if ($execSummaryText -notmatch "Rework-required gates:\s+0") {
    throw "Latest executive summary does not show 0 rework-required gates."
}

# ------------------------------------------------------------
# 1) COPY FINAL AUTHORITY FILES
# ------------------------------------------------------------
$copyLedger = New-Object System.Collections.Generic.List[object]

function Copy-And-Record {
    param(
        [string]$Label,
        [string]$Source,
        [string]$Dest
    )

    $ok = Copy-IfExists -SourcePath $Source -DestPath $Dest
    $copyLedger.Add([pscustomobject]@{
        Label       = $Label
        SourcePath  = Normalize-Slash $Source
        DestPath    = Normalize-Slash $Dest
        Copied      = $ok
    })
}

Copy-And-Record -Label "ExecutiveCompletionSummary" -Source $execSummaryPath -Dest (Join-Path $artifactRoot "final\EXECUTIVE_COMPLETION_SUMMARY.md")
Copy-And-Record -Label "GateFinalizationSummary"   -Source $gateSummaryPath -Dest (Join-Path $artifactRoot "final\GATE_FINALIZATION_SUMMARY.md")
Copy-And-Record -Label "GateDecisionMatrix"        -Source $gateMatrixPath  -Dest (Join-Path $artifactRoot "final\gate_decision_matrix.csv")

if ($latestPhase5) {
    Copy-And-Record -Label "Phase5Summary" -Source (Join-Path $latestPhase5.FullName "SUMMARY.md") -Dest (Join-Path $artifactRoot "phase5\SUMMARY.md")
    Copy-And-Record -Label "Phase5CoreMatrix" -Source (Join-Path $latestPhase5.FullName "core_contract_matrix.csv") -Dest (Join-Path $artifactRoot "phase5\core_contract_matrix.csv")
    Copy-And-Record -Label "Phase5CoreGaps" -Source (Join-Path $latestPhase5.FullName "core_gaps.csv") -Dest (Join-Path $artifactRoot "phase5\core_gaps.csv")
    Copy-And-Record -Label "Phase5DjangoCheck" -Source (Join-Path $latestPhase5.FullName "django_check.txt") -Dest (Join-Path $artifactRoot "phase5\django_check.txt")
    Copy-And-Record -Label "Phase5ShowMigrations" -Source (Join-Path $latestPhase5.FullName "django_showmigrations.txt") -Dest (Join-Path $artifactRoot "phase5\django_showmigrations.txt")
}

if ($latestPhase6) {
    Copy-And-Record -Label "Phase6Summary" -Source (Join-Path $latestPhase6.FullName "SUMMARY.md") -Dest (Join-Path $artifactRoot "phase6\SUMMARY.md")
    Copy-And-Record -Label "Phase6ModuleMatrix" -Source (Join-Path $latestPhase6.FullName "module_presence_matrix.csv") -Dest (Join-Path $artifactRoot "phase6\module_presence_matrix.csv")
    Copy-And-Record -Label "Phase6ModuleGaps" -Source (Join-Path $latestPhase6.FullName "module_gaps.csv") -Dest (Join-Path $artifactRoot "phase6\module_gaps.csv")
    Copy-And-Record -Label "Phase6IntegrationHits" -Source (Join-Path $latestPhase6.FullName "module_integration_control_hits.csv") -Dest (Join-Path $artifactRoot "phase6\module_integration_control_hits.csv")
}

if ($latestPhase7) {
    Copy-And-Record -Label "Phase7Summary" -Source (Join-Path $latestPhase7.FullName "SUMMARY.md") -Dest (Join-Path $artifactRoot "phase7\SUMMARY.md")
    Copy-And-Record -Label "Phase7ReadinessChecklist" -Source (Join-Path $latestPhase7.FullName "release_readiness_checklist.csv") -Dest (Join-Path $artifactRoot "phase7\release_readiness_checklist.csv")
    Copy-And-Record -Label "Phase7DeployCheck" -Source (Join-Path $latestPhase7.FullName "django_check_deploy.txt") -Dest (Join-Path $artifactRoot "phase7\django_check_deploy.txt")
}

if ($latestPhase567) {
    Copy-And-Record -Label "Phase567MasterSummary" -Source (Join-Path $latestPhase567.FullName "SUMMARY.md") -Dest (Join-Path $artifactRoot "phase567\SUMMARY.md")
}

if ($latestPhase12) {
    Copy-And-Record -Label "Phase12DecisionCloserSummary" -Source (Join-Path $latestPhase12.FullName "SUMMARY.md") -Dest (Join-Path $artifactRoot "phase12\SUMMARY.md")
    Copy-And-Record -Label "Phase12AutoClosedRows" -Source (Join-Path $latestPhase12.FullName "auto_closed_rows.csv") -Dest (Join-Path $artifactRoot "phase12\auto_closed_rows.csv")
    Copy-And-Record -Label "Phase12FullRerunResults" -Source (Join-Path $latestPhase12.FullName "full_rerun_results.csv") -Dest (Join-Path $artifactRoot "phase12\full_rerun_results.csv")
}

# Control files
Copy-And-Record -Label "GateRegister" -Source (Join-Path $repoRoot "docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv") -Dest (Join-Path $artifactRoot "controls\09_Phase_Gate_Register.csv")
Copy-And-Record -Label "Scorecard"    -Source (Join-Path $repoRoot "docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv") -Dest (Join-Path $artifactRoot "controls\03_Phase_Progress_Scorecard.csv")
Copy-And-Record -Label "RiskRegister" -Source (Join-Path $repoRoot "docs\Crown_Master_Binder\03_Operations_and_Delivery\04_Risk_Register.csv") -Dest (Join-Path $artifactRoot "controls\04_Risk_Register.csv")
Copy-And-Record -Label "MasterInventory" -Source (Join-Path $repoRoot "docs\Crown_Master_Binder\04_Inventory_Keep_Rewrite_Drop\01_Master_Inventory.csv") -Dest (Join-Path $artifactRoot "controls\01_Master_Inventory.csv")

$copyLedger | Export-Csv -Path (Join-Path $artifactRoot "copy_ledger.csv") -NoTypeInformation -Encoding utf8

# ------------------------------------------------------------
# 2) SNAPSHOT GIT STATE
# ------------------------------------------------------------
cmd /c "git rev-parse HEAD 2>&1" | Set-Content -Path (Join-Path $artifactRoot "git_HEAD.txt") -Encoding utf8
cmd /c "git status --short 2>&1" | Set-Content -Path (Join-Path $artifactRoot "git_status_short.txt") -Encoding utf8
cmd /c "git branch --show-current 2>&1" | Set-Content -Path (Join-Path $artifactRoot "git_branch.txt") -Encoding utf8
cmd /c "git log --oneline -20 2>&1" | Set-Content -Path (Join-Path $artifactRoot "git_log_last20.txt") -Encoding utf8
cmd /c "git diff --stat 2>&1" | Set-Content -Path (Join-Path $artifactRoot "git_diff_stat.txt") -Encoding utf8

$headSha = (Get-Content -Raw -Path (Join-Path $artifactRoot "git_HEAD.txt")).Trim()
$currentBranch = (Get-Content -Raw -Path (Join-Path $artifactRoot "git_branch.txt")).Trim()

# ------------------------------------------------------------
# 3) OPTIONAL TAG
# ------------------------------------------------------------
$tagStatus = "NotRequested"
if ($CreateGitTag) {
    if ([string]::IsNullOrWhiteSpace($TagName)) {
        throw "CreateGitTag was requested but TagName is empty."
    }

    $existingTag = git tag --list $TagName
    if ($existingTag) {
        $tagStatus = "AlreadyExists"
    }
    else {
        git tag $TagName 2>&1 | Out-Null
        $tagStatus = "Created"
    }
}

# ------------------------------------------------------------
# 4) RELEASE MANIFEST
# ------------------------------------------------------------
$manifestRows = @(
    [pscustomobject]@{ Key = "ReleaseStatus"; Value = "COMPLETE" }
    [pscustomobject]@{ Key = "ApprovedGates"; Value = "7" }
    [pscustomobject]@{ Key = "ReworkRequiredGates"; Value = "0" }
    [pscustomobject]@{ Key = "GitBranch"; Value = $currentBranch }
    [pscustomobject]@{ Key = "GitHEAD"; Value = $headSha }
    [pscustomobject]@{ Key = "GateArtifactFolder"; Value = Normalize-Slash $latestGate.FullName }
    [pscustomobject]@{ Key = "Phase5ArtifactFolder"; Value = $(if ($latestPhase5) { Normalize-Slash $latestPhase5.FullName } else { "" }) }
    [pscustomobject]@{ Key = "Phase6ArtifactFolder"; Value = $(if ($latestPhase6) { Normalize-Slash $latestPhase6.FullName } else { "" }) }
    [pscustomobject]@{ Key = "Phase7ArtifactFolder"; Value = $(if ($latestPhase7) { Normalize-Slash $latestPhase7.FullName } else { "" }) }
    [pscustomobject]@{ Key = "Phase567ArtifactFolder"; Value = $(if ($latestPhase567) { Normalize-Slash $latestPhase567.FullName } else { "" }) }
    [pscustomobject]@{ Key = "Phase12ArtifactFolder"; Value = $(if ($latestPhase12) { Normalize-Slash $latestPhase12.FullName } else { "" }) }
    [pscustomobject]@{ Key = "GitTagStatus"; Value = $tagStatus }
    [pscustomobject]@{ Key = "GitTagName"; Value = $TagName }
)
$manifestRows | Export-Csv -Path (Join-Path $artifactRoot "RELEASE_MANIFEST.csv") -NoTypeInformation -Encoding utf8

# ------------------------------------------------------------
# 5) HUMAN SUMMARY
# ------------------------------------------------------------
$summaryLines = @(
    "# Crown Release Closeout Evidence Pack",
    "",
    "## Final authority state",
    "- Overall status: COMPLETE",
    "- Approved gates: 7",
    "- Rework-required gates: 0",
    "",
    "## Git state",
    "- Branch: $currentBranch",
    "- HEAD: $headSha",
    "- Tag status: $tagStatus" + $(if ($TagName) { " ($TagName)" } else { "" }),
    "",
    "## Evidence sources copied",
    "- Latest gate finalization artifacts",
    "- Latest Phase 5 core build artifacts",
    "- Latest Phase 6 first-wave module artifacts",
    "- Latest Phase 7 hardening / release artifacts",
    "- Latest Phase 567 master summary",
    "- Latest Phase 12 decision closer artifacts",
    "- Current gate register / scorecard / risk register / master inventory",
    "",
    "## Root cause note",
    "- The prior G-005 closure issue was traced to Django startup missing SECRET_KEY in the Phase 5 check path and is no longer blocking final closure.",
    "",
    "## Pack location",
    "- $artifactRoot"
)
Write-Utf8File -Path (Join-Path $artifactRoot "RELEASE_CLOSEOUT_SUMMARY.md") -Content ($summaryLines -join [Environment]::NewLine)

# ------------------------------------------------------------
# 6) ZIP THE PACK
# ------------------------------------------------------------
$zipPath = Join-Path $repoRoot ("audit-artifacts\release_closeout_evidence_pack_" + (Split-Path $artifactRoot -Leaf) + ".zip")
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $artifactRoot "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "DONE"
Write-Host "Release evidence pack: $artifactRoot"
Write-Host "Zip file: $zipPath"
Write-Host "Git HEAD: $headSha"
Write-Host "Branch: $currentBranch"
Write-Host "Tag status: $tagStatus"
Write-Host "Release status: COMPLETE"

if ($OpenPack) {
    code (Join-Path $artifactRoot "RELEASE_CLOSEOUT_SUMMARY.md")
    code (Join-Path $artifactRoot "RELEASE_MANIFEST.csv")
    code (Join-Path $artifactRoot "copy_ledger.csv")
    code (Join-Path $artifactRoot "final\EXECUTIVE_COMPLETION_SUMMARY.md")
    code (Join-Path $artifactRoot "final\GATE_FINALIZATION_SUMMARY.md")
    code (Join-Path $artifactRoot "final\gate_decision_matrix.csv")
}
