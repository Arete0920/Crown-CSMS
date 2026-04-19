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

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) {
        code $Path
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveBase = Join-Path $repoRoot "audit-artifacts\release-archive-packet"
$archiveOut = Join-Path $archiveBase $ts
$archiveLatest = Join-Path $archiveBase "latest"
New-Item -ItemType Directory -Force -Path $archiveOut | Out-Null

$pathsToCopy = @(
    @{ Source = ".\audit-artifacts\release-control-center\latest"; Target = "01_release-control-center" },
    @{ Source = ".\audit-artifacts\release-master-gate\latest"; Target = "02_release-master-gate" },
    @{ Source = ".\audit-artifacts\release-candidate-packet\latest"; Target = "03_release-candidate-packet" },
    @{ Source = ".\audit-artifacts\release-day-command-pack\latest"; Target = "04_release-day-command-pack" },
    @{ Source = ".\audit-artifacts\release-war-room"; Target = "05_release-war-room" }
)

$copied = @()
foreach ($entry in $pathsToCopy) {
    $src = Join-Path $repoRoot $entry.Source
    $dst = Join-Path $archiveOut $entry.Target
    if (Test-Path $src) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item (Join-Path $src "*") $dst -Recurse -Force
        $copied += [pscustomobject]@{ Source = $src; Target = $dst; Copied = $true }
    }
    else {
        $copied += [pscustomobject]@{ Source = $src; Target = $dst; Copied = $false }
    }
}

$copied | Export-Csv (Join-Path $archiveOut "01_archive_manifest.csv") -NoTypeInformation -Encoding utf8

Set-Utf8File -Path (Join-Path $archiveOut "02_archive_notes.md") -Content @"
# Release Archive Notes

## Archive root
$archiveOut

## Included sets
- release-control-center latest
- release-master-gate latest
- release-candidate-packet latest
- release-day-command-pack latest
- release-war-room

## Purpose
- preserve final release decision artifacts
- preserve working board and packet state
- preserve release-day command pack
"@

$zipPath = Join-Path $archiveOut ("release-archive-packet-" + $ts + ".zip")
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
$zipFiles = Get-ChildItem $archiveOut -Recurse -File | Where-Object {
    try {
        $stream = [System.IO.File]::Open($_.FullName, 'Open', 'Read', 'ReadWrite')
        $stream.Close()
        $true
    }
    catch {
        $false
    }
} | Select-Object -ExpandProperty FullName
if ($zipFiles.Count -gt 0) {
    Compress-Archive -Path $zipFiles -DestinationPath $zipPath -Force
}
else {
    throw "No readable files available to package in archive: $archiveOut"
}
Set-Utf8File -Path (Join-Path $archiveOut "03_zip_path.txt") -Content $zipPath

if (-not (Test-Path $archiveLatest)) {
    New-Item -ItemType Directory -Force -Path $archiveLatest | Out-Null
}
Copy-Item (Join-Path $archiveOut "*") $archiveLatest -Recurse -Force

if ($OpenFiles) {
    Open-IfExists (Join-Path $archiveLatest "01_archive_manifest.csv")
    Open-IfExists (Join-Path $archiveLatest "02_archive_notes.md")
    Open-IfExists (Join-Path $archiveLatest "03_zip_path.txt")
}

Write-Host "Done: $archiveOut"
Write-Host "Latest: $archiveLatest"
Write-Host "Zip: $zipPath"
