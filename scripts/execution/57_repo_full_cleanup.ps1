param(
    [int]$KeepNewestPerLane = 1,
    [int]$PruneZipDays = 7,
    [switch]$ApplyArtifactPrune,
    [switch]$RemoveStaleSiblingDirs,
    [switch]$OpenReports
)

$ErrorActionPreference = "Stop"

function Get-LatestTimestampDir {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return $null }
    return Get-ChildItem $Root -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{8}_\d{6}$' } |
        Sort-Object Name -Descending |
        Select-Object -First 1
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$hygieneScript = Join-Path $repoRoot "scripts\execution\57_repo_hygiene_cleanup.ps1"
if (-not (Test-Path $hygieneScript)) {
    throw "Required script not found: $hygieneScript"
}

# Delegate operational work to the existing hygiene script.
& $hygieneScript `
    -KeepNewestPerLane $KeepNewestPerLane `
    -PruneZipDays $PruneZipDays `
    -ApplyArtifactPrune:$ApplyArtifactPrune `
    -RemoveStaleSiblingDirs:$RemoveStaleSiblingDirs

$hygieneLatest = Get-LatestTimestampDir -Root ".\audit-artifacts\repo-hygiene-cleanup"
if (-not $hygieneLatest) {
    throw "No timestamped output found under .\audit-artifacts\repo-hygiene-cleanup"
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$targetBase = Join-Path $repoRoot ("audit-artifacts\repo-full-cleanup\" + $ts)
$targetReports = Join-Path $targetBase "reports"
New-Item -ItemType Directory -Force -Path $targetReports | Out-Null

$sourceReadme = Join-Path $hygieneLatest.FullName "README_REPO_HYGIENE_CLEANUP.txt"
$targetReadme = Join-Path $targetBase "README_REPO_FULL_CLEANUP.txt"
if (Test-Path $sourceReadme) {
    Copy-Item -Force $sourceReadme $targetReadme
} else {
    @"
REPO FULL CLEANUP COMPLETE

Source hygiene report folder:
$($hygieneLatest.FullName)
"@ | Set-Content -Path $targetReadme -Encoding utf8
}

$copyMap = @(
    @{ From = "reports\SUMMARY.md";             To = "reports\SUMMARY.md" },
    @{ From = "reports\05_artifact_prune_plan.csv"; To = "reports\06_artifact_prune_plan.csv" },
    @{ From = "reports\06_zip_prune_plan.csv";      To = "reports\07_zip_prune_plan.csv" },
    @{ From = "reports\07_sibling_dir_review.csv";  To = "reports\08_sibling_dir_review.csv" }
)

foreach ($m in $copyMap) {
    $src = Join-Path $hygieneLatest.FullName $m.From
    $dst = Join-Path $targetBase $m.To
    if (Test-Path $src) {
        $dstDir = Split-Path -Parent $dst
        if ($dstDir -and -not (Test-Path $dstDir)) {
            New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        }
        Copy-Item -Force $src $dst
    }
}

Write-Host ""
Write-Host "DONE"
Write-Host "Repo full cleanup report root: $targetBase"

if ($OpenReports) {
    Open-IfExists $targetReadme
    Open-IfExists (Join-Path $targetBase "reports\SUMMARY.md")
    Open-IfExists (Join-Path $targetBase "reports\06_artifact_prune_plan.csv")
    Open-IfExists (Join-Path $targetBase "reports\07_zip_prune_plan.csv")
    Open-IfExists (Join-Path $targetBase "reports\08_sibling_dir_review.csv")
}