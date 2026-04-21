param(
    [switch]$OpenFiles
)

$ErrorActionPreference = "Stop"

function Set-Utf8File {
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

function Copy-LatestFolder {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )
    if (Test-Path $SourcePath) {
        New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null
        Copy-Item (Join-Path $SourcePath "*") $TargetPath -Recurse -Force
        return $true
    }
    return $false
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) {
        code $Path
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$packetBase = Join-Path $repoRoot "audit-artifacts\release-candidate-packet"
$packetOut = Join-Path $packetBase $ts
$packetLatest = Join-Path $packetBase "latest"
New-Item -ItemType Directory -Force -Path $packetOut | Out-Null

$runtimeLatest = Join-Path $repoRoot "audit-artifacts\runtime-release-closure\latest"
$paymentLatest = Join-Path $repoRoot "audit-artifacts\payment-readiness\latest"
$legalLatest = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness\latest"
$pilotLatest = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness\latest"
$cutoverLatest = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness\latest"
$masterGateLatest = Join-Path $repoRoot "audit-artifacts\release-master-gate\latest"
$warRoomBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
$warRoomChecklist = Join-Path $repoRoot "audit-artifacts\release-war-room\cutover_rollback_checklist.md"

$copied = @()
$copied += [pscustomobject]@{ Name = "runtime-release-closure"; Copied = (Copy-LatestFolder -SourcePath $runtimeLatest -TargetPath (Join-Path $packetOut "01_runtime-release-closure")) }
$copied += [pscustomobject]@{ Name = "payment-readiness"; Copied = (Copy-LatestFolder -SourcePath $paymentLatest -TargetPath (Join-Path $packetOut "02_payment-readiness")) }
$copied += [pscustomobject]@{ Name = "legal-dpa-readiness"; Copied = (Copy-LatestFolder -SourcePath $legalLatest -TargetPath (Join-Path $packetOut "03_legal-dpa-readiness")) }
$copied += [pscustomobject]@{ Name = "pilot-loi-readiness"; Copied = (Copy-LatestFolder -SourcePath $pilotLatest -TargetPath (Join-Path $packetOut "04_pilot-loi-readiness")) }
$copied += [pscustomobject]@{ Name = "cutover-rollback-readiness"; Copied = (Copy-LatestFolder -SourcePath $cutoverLatest -TargetPath (Join-Path $packetOut "05_cutover-rollback-readiness")) }
$copied += [pscustomobject]@{ Name = "release-master-gate"; Copied = (Copy-LatestFolder -SourcePath $masterGateLatest -TargetPath (Join-Path $packetOut "06_release-master-gate")) }

if (Test-Path $warRoomBoard) {
    Copy-Item $warRoomBoard (Join-Path $packetOut "07_priority_board.csv") -Force
}
if (Test-Path $warRoomChecklist) {
    Copy-Item $warRoomChecklist (Join-Path $packetOut "08_cutover_rollback_checklist.md") -Force
}

$boardRows = @()
if (Test-Path $warRoomBoard) {
    $boardRows = Import-Csv $warRoomBoard
}

$item7 = ($boardRows | Where-Object { $_.Priority -eq "7" } | Select-Object -First 1)
$item8 = ($boardRows | Where-Object { $_.Priority -eq "8" } | Select-Object -First 1)
$item9 = ($boardRows | Where-Object { $_.Priority -eq "9" } | Select-Object -First 1)
$item10 = ($boardRows | Where-Object { $_.Priority -eq "10" } | Select-Object -First 1)

$masterSummaryPath = Join-Path $masterGateLatest "SUMMARY.md"
$overallReady = $false
if (Test-Path $masterSummaryPath) {
    $masterSummary = Get-Content $masterSummaryPath -Raw
    if ($masterSummary -match "Overall release ready: True") {
        $overallReady = $true
    }
}

$manifest = @()
$manifest += "# Release Candidate Packet Manifest"
$manifest += ""
$manifest += "## Packet root"
$manifest += "$packetOut"
$manifest += ""
$manifest += "## Included folders"
foreach ($row in $copied) {
    $manifest += "- $($row.Name): $($row.Copied)"
}
$manifest += ""
$manifest += "## Board states"
$manifest += "- Item 7: $($item7.Status)"
$manifest += "- Item 8: $($item8.Status)"
$manifest += "- Item 9: $($item9.Status)"
$manifest += "- Item 10: $($item10.Status)"
$manifest += ""
$manifest += "## Master gate"
$manifest += "- Overall release ready: $overallReady"
$manifest += ""

Set-Utf8File -Path (Join-Path $packetOut "MANIFEST.md") -Content ($manifest -join "`r`n")

$execSummary = @()
$execSummary += "# Release Candidate Executive Summary"
$execSummary += ""
$execSummary += "- Packet root: $packetOut"
$execSummary += "- Overall release ready: $overallReady"
$execSummary += ""
$execSummary += "## Gate status"
$execSummary += "- Payment readiness: $($item7.Status)"
$execSummary += "- Legal / DPA readiness: $($item8.Status)"
$execSummary += "- Pilot / LOI readiness: $($item9.Status)"
$execSummary += "- Cutover / rollback readiness: $($item10.Status)"
$execSummary += ""
$execSummary += "## Required next action"
if ($overallReady) {
    $execSummary += "- Complete final release decision and archive packet."
}
else {
    $execSummary += "- Close all remaining FAIL / open items and rebuild packet."
}
$execSummary += ""

Set-Utf8File -Path (Join-Path $packetOut "SUMMARY.md") -Content ($execSummary -join "`r`n")

if (-not (Test-Path $packetLatest)) {
    New-Item -ItemType Directory -Force -Path $packetLatest | Out-Null
}
Copy-Item (Join-Path $packetOut "*") $packetLatest -Recurse -Force

$zipPath = Join-Path $packetOut ("release-candidate-packet-" + $ts + ".zip")
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $packetOut "*") -DestinationPath $zipPath -Force

Set-Utf8File -Path (Join-Path $packetOut "ZIP_PATH.txt") -Content $zipPath

if ($OpenFiles) {
    Open-IfExists (Join-Path $packetLatest "SUMMARY.md")
    Open-IfExists (Join-Path $packetLatest "MANIFEST.md")
    Open-IfExists (Join-Path $packetLatest "07_priority_board.csv")
    Open-IfExists (Join-Path $packetLatest "06_release-master-gate\SUMMARY.md")
    Open-IfExists (Join-Path $packetLatest "06_release-master-gate\07_open_blockers.txt")
}

Write-Host "Done: $packetOut"
Write-Host "Latest: $packetLatest"
Write-Host "Zip: $zipPath"
