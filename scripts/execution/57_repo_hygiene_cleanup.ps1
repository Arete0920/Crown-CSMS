param(
    [int]$KeepNewestPerLane = 1,
    [int]$PruneZipDays = 7,
    [switch]$ApplyArtifactPrune,
    [switch]$RemoveStaleSiblingDirs,
    [switch]$OpenReports
)

$ErrorActionPreference = "Stop"

function Set-Utf8File {
    param([string]$Path,[string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Add-Utf8Text {
    param([string]$Path,[string]$Content)
    $Content | Add-Content -Path $Path -Encoding utf8
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

function Backup-IfExists {
    param([string]$Source,[string]$BackupDir)
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
        Copy-Item $Source (Join-Path $BackupDir ([IO.Path]::GetFileName($Source))) -Force
    }
}

function Get-TimestampDirs {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return @() }
    return @(Get-ChildItem $Root -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{8}_\d{6}$' } |
        Sort-Object Name -Descending)
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot ("audit-artifacts\repo-hygiene-cleanup\" + $ts)
$backupDir = Join-Path $base "backup"
$reportDir = Join-Path $base "reports"
New-Item -ItemType Directory -Force -Path $backupDir,$reportDir | Out-Null

# --------------------------------------------------
# 1. VS Code workspace / settings cleanup
# --------------------------------------------------
New-Item -ItemType Directory -Force -Path ".vscode" | Out-Null

$workspacePath = Join-Path $repoRoot "Crown2026_clean.code-workspace"
$settingsPath = Join-Path $repoRoot ".vscode\settings.json"
$psAnalyzerPath = Join-Path $repoRoot ".vscode\PSScriptAnalyzerSettings.psd1"
$readmePath = Join-Path $base "README_REPO_HYGIENE_CLEANUP.txt"

Backup-IfExists -Source $workspacePath -BackupDir $backupDir
Backup-IfExists -Source $settingsPath -BackupDir $backupDir
Backup-IfExists -Source $psAnalyzerPath -BackupDir $backupDir

$workspaceJson = @"
{
  "folders": [
    {
      "path": "."
    }
  ],
  "settings": {
    "files.exclude": {
      "**/audit-artifacts/**": true,
      "**/AUDIT_PACK_*/**": true,
      "**/Crown2026_release_truth_*/**": true,
      "**/Crown2026_deploypr_fixwt/**": true,
      "**/.venv/**": true,
      "**/node_modules/**": true,
      "**/dist/**": true,
      "**/build/**": true,
      "**/coverage/**": true,
      "**/.pytest_cache/**": true,
      "**/__pycache__/**": true,
      "**/*.zip": true
    },
    "search.exclude": {
      "**/audit-artifacts/**": true,
      "**/AUDIT_PACK_*/**": true,
      "**/Crown2026_release_truth_*/**": true,
      "**/Crown2026_deploypr_fixwt/**": true,
      "**/.venv/**": true,
      "**/node_modules/**": true,
      "**/dist/**": true,
      "**/build/**": true,
      "**/coverage/**": true,
      "**/.pytest_cache/**": true,
      "**/__pycache__/**": true
    },
    "files.watcherExclude": {
      "**/audit-artifacts/**": true,
      "**/AUDIT_PACK_*/**": true,
      "**/Crown2026_release_truth_*/**": true,
      "**/Crown2026_deploypr_fixwt/**": true,
      "**/.venv/**": true,
      "**/node_modules/**": true,
      "**/dist/**": true,
      "**/build/**": true,
      "**/coverage/**": true,
      "**/.pytest_cache/**": true,
      "**/__pycache__/**": true
    },
    "powershell.scriptAnalysis.enable": true,
    "powershell.scriptAnalysis.settingsPath": ".vscode/PSScriptAnalyzerSettings.psd1",
    "powershell.integratedConsole.showOnStartup": false,
    "markdown.validate.enabled": false,
    "markdownlint.config": {
      "MD022": false,
      "MD031": false,
      "MD032": false,
      "MD040": false
    },
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.eol": "\n",
    "workbench.editor.enablePreview": false,
    "explorer.excludeGitIgnore": false
  }
}
"@
$workspaceJson | Set-Content -Path $workspacePath -Encoding utf8
$workspaceJson | ConvertFrom-Json | Out-Null

$settingsJson = @"
{
  "files.exclude": {
    "**/audit-artifacts/**": true,
    "**/AUDIT_PACK_*/**": true,
    "**/Crown2026_release_truth_*/**": true,
    "**/Crown2026_deploypr_fixwt/**": true,
    "**/.venv/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/coverage/**": true,
    "**/.pytest_cache/**": true,
    "**/__pycache__/**": true,
    "**/*.zip": true
  },
  "search.exclude": {
    "**/audit-artifacts/**": true,
    "**/AUDIT_PACK_*/**": true,
    "**/Crown2026_release_truth_*/**": true,
    "**/Crown2026_deploypr_fixwt/**": true,
    "**/.venv/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/coverage/**": true,
    "**/.pytest_cache/**": true,
    "**/__pycache__/**": true
  },
  "files.watcherExclude": {
    "**/audit-artifacts/**": true,
    "**/AUDIT_PACK_*/**": true,
    "**/Crown2026_release_truth_*/**": true,
    "**/Crown2026_deploypr_fixwt/**": true,
    "**/.venv/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/coverage/**": true,
    "**/.pytest_cache/**": true,
    "**/__pycache__/**": true
  },
  "powershell.scriptAnalysis.enable": true,
  "powershell.scriptAnalysis.settingsPath": ".vscode/PSScriptAnalyzerSettings.psd1",
  "markdown.validate.enabled": false
}
"@
$settingsJson | Set-Content -Path $settingsPath -Encoding utf8

@'
@{
    ExcludeRules = @(
        'PSUseApprovedVerbs'
    )

    Rules = @{
        PSUseApprovedVerbs = @{
            Enable = $false
        }
        PSAvoidUsingWriteHost = @{
            Enable = $false
        }
    }
}
'@ | Set-Content -Path $psAnalyzerPath -Encoding utf8

# --------------------------------------------------
# 2. Local-only exclude for generated clutter
# --------------------------------------------------
$gitExcludePath = Join-Path $repoRoot ".git\info\exclude"
Backup-IfExists -Source $gitExcludePath -BackupDir $backupDir

$excludeEntries = @(
    "",
    "# repo-hygiene-cleanup generated noise exclusions",
    "audit-artifacts/",
    "AUDIT_PACK_*/",
    "Crown2026_clean.code-workspace"
)

$currentExclude = ""
if (Test-Path $gitExcludePath) {
    $currentExclude = Get-Content $gitExcludePath -Raw
}

$toAppend = @()
foreach ($entry in $excludeEntries) {
    if ($entry -and $currentExclude -notmatch [regex]::Escape($entry)) {
        $toAppend += $entry
    }
}
if ($toAppend.Count -gt 0) {
    Add-Utf8Text -Path $gitExcludePath -Content (($toAppend -join "`r`n") + "`r`n")
}

# --------------------------------------------------
# 3. Git hygiene capture + prune
# --------------------------------------------------
$gitStatusPath = Join-Path $reportDir "01_git_status.txt"
$gitWorktreesPath = Join-Path $reportDir "02_git_worktrees.txt"
$gitRemotesPath = Join-Path $reportDir "03_git_remote_show.txt"
$gitGcPath = Join-Path $reportDir "04_git_gc.txt"

git status --short --branch | Set-Content -Path $gitStatusPath -Encoding utf8
git worktree list --porcelain | Set-Content -Path $gitWorktreesPath -Encoding utf8
git remote show origin | Set-Content -Path $gitRemotesPath -Encoding utf8
git remote prune origin 2>&1 | Out-File -FilePath $gitGcPath -Encoding utf8
git gc --prune=now 2>&1 | Out-File -FilePath $gitGcPath -Append -Encoding utf8

# --------------------------------------------------
# 4. Artifact pruning plan
# --------------------------------------------------
$auditRoot = Join-Path $repoRoot "audit-artifacts"
$prunePlan = @()
$deletedItems = @()

if (Test-Path $auditRoot) {
    $lanes = Get-ChildItem $auditRoot -Directory -ErrorAction SilentlyContinue
    foreach ($lane in $lanes) {
        $tsDirs = Get-TimestampDirs -Root $lane.FullName
        $keepNames = @()
        if (Test-Path (Join-Path $lane.FullName "latest")) {
            $keepNames += "latest"
        }
        if ($tsDirs.Count -gt 0) {
            $keepNames += @($tsDirs | Select-Object -First $KeepNewestPerLane | ForEach-Object { $_.Name })
        }

        $allDirs = Get-ChildItem $lane.FullName -Directory -ErrorAction SilentlyContinue
        foreach ($d in $allDirs) {
            $delete = $keepNames -notcontains $d.Name
            $prunePlan += [pscustomobject]@{
                Lane = $lane.Name
                Name = $d.Name
                FullPath = $d.FullName
                Keep = (-not $delete)
                Deleted = $false
            }

            if ($ApplyArtifactPrune -and $delete) {
                try {
                    Remove-Item $d.FullName -Recurse -Force -ErrorAction Stop
                    $deletedItems += $d.FullName
                } catch {}
            }
        }
    }
}

$prunePlanPath = Join-Path $reportDir "05_artifact_prune_plan.csv"
$prunePlanAfter = foreach ($row in $prunePlan) {
    [pscustomobject]@{
        Lane = $row.Lane
        Name = $row.Name
        FullPath = $row.FullPath
        Keep = $row.Keep
        Deleted = ($(if ($deletedItems -contains $row.FullPath) { $true } else { $false }))
    }
}
$prunePlanAfter | Export-Csv $prunePlanPath -NoTypeInformation -Encoding utf8

# --------------------------------------------------
# 5. Zip cleanup
# --------------------------------------------------
$zipPlan = @()
$zipCutoff = (Get-Date).AddDays(-1 * $PruneZipDays)

if (Test-Path $auditRoot) {
    $zips = Get-ChildItem $auditRoot -Recurse -File -Filter *.zip -ErrorAction SilentlyContinue
    foreach ($z in $zips) {
        $delete = $z.LastWriteTime -lt $zipCutoff
        $zipPlan += [pscustomobject]@{
            FullPath = $z.FullName
            LastWriteTime = $z.LastWriteTime
            Delete = $delete
            Deleted = $false
        }

        if ($ApplyArtifactPrune -and $delete) {
            try {
                Remove-Item $z.FullName -Force -ErrorAction Stop
                $zipPlan[-1].Deleted = $true
            } catch {}
        }
    }
}
$zipPlan | Export-Csv (Join-Path $reportDir "06_zip_prune_plan.csv") -NoTypeInformation -Encoding utf8

# --------------------------------------------------
# 6. Stale sibling directory cleanup
# --------------------------------------------------
$siblingRoot = Split-Path $repoRoot -Parent
$worktreePaths = @()
if (Test-Path $gitWorktreesPath) {
    $worktreePaths = Get-Content $gitWorktreesPath | Where-Object { $_ -match '^worktree ' } | ForEach-Object { ($_ -replace '^worktree ','').Trim() }
}

$siblingCandidates = @()
Get-ChildItem $siblingRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "Crown2026*" -or $_.Name -like "*deploypr_fixwt*" -or $_.Name -like "Crown2026_release_truth_*" } |
    ForEach-Object {
        $isCurrent = ($_.FullName -eq $repoRoot)
        $isWorktree = $worktreePaths -contains $_.FullName
        $safeDelete = (-not $isCurrent -and -not $isWorktree)

        $deleted = $false
        if ($RemoveStaleSiblingDirs -and $safeDelete) {
            try {
                Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop
                $deleted = $true
            } catch {}
        }

        $siblingCandidates += [pscustomobject]@{
            Name = $_.Name
            FullPath = $_.FullName
            IsCurrentRepo = $isCurrent
            IsActiveGitWorktree = $isWorktree
            SafeDeleteCandidate = $safeDelete
            Deleted = $deleted
        }
    }

$siblingCandidates | Export-Csv (Join-Path $reportDir "07_sibling_dir_review.csv") -NoTypeInformation -Encoding utf8

# --------------------------------------------------
# 7. Summary
# --------------------------------------------------
$deletedArtifactCount = @($prunePlanAfter | Where-Object { $_.Deleted -eq $true }).Count
$deletedZipCount = @($zipPlan | Where-Object { $_.Deleted -eq $true }).Count
$deletedSiblingCount = @($siblingCandidates | Where-Object { $_.Deleted -eq $true }).Count

@"
REPO HYGIENE CLEANUP COMPLETE

Created / updated:
- $workspacePath
- $settingsPath
- $psAnalyzerPath
- $gitExcludePath

Reports:
- $reportDir\01_git_status.txt
- $reportDir\02_git_worktrees.txt
- $reportDir\03_git_remote_show.txt
- $reportDir\04_git_gc.txt
- $reportDir\05_artifact_prune_plan.csv
- $reportDir\06_zip_prune_plan.csv
- $reportDir\07_sibling_dir_review.csv

ApplyArtifactPrune: $($ApplyArtifactPrune.IsPresent)
RemoveStaleSiblingDirs: $($RemoveStaleSiblingDirs.IsPresent)

Deleted:
- artifact dirs: $deletedArtifactCount
- zip files: $deletedZipCount
- sibling dirs: $deletedSiblingCount

NEXT
1. Open Crown2026_clean.code-workspace
2. Run Developer: Reload Window
3. Re-check Problems
4. Review 05_artifact_prune_plan.csv and 07_sibling_dir_review.csv
"@ | Set-Content -Path $readmePath -Encoding utf8

@"
# Repo Hygiene Cleanup Summary

## Output root
$base

## Key actions
- single-root workspace refreshed
- generated artifact folders excluded from VS Code noise
- local-only git exclude updated for generated clutter
- git remote prune and git gc run
- artifact prune plan generated
- zip prune plan generated
- sibling directory review generated

## Execution flags
- ApplyArtifactPrune = $($ApplyArtifactPrune.IsPresent)
- RemoveStaleSiblingDirs = $($RemoveStaleSiblingDirs.IsPresent)

## Deleted counts
- Artifact directories = $deletedArtifactCount
- Zip files = $deletedZipCount
- Sibling directories = $deletedSiblingCount
"@ | Set-Content -Path (Join-Path $reportDir "SUMMARY.md") -Encoding utf8

Write-Host ""
Write-Host "DONE"
Write-Host "Workspace:"
Write-Host $workspacePath
Write-Host ""
Write-Host "Reports:"
Write-Host $reportDir

if ($OpenReports) {
    Open-IfExists $workspacePath
    Open-IfExists $readmePath
    Open-IfExists (Join-Path $reportDir "SUMMARY.md")
    Open-IfExists (Join-Path $reportDir "05_artifact_prune_plan.csv")
    Open-IfExists (Join-Path $reportDir "06_zip_prune_plan.csv")
    Open-IfExists (Join-Path $reportDir "07_sibling_dir_review.csv")
}
