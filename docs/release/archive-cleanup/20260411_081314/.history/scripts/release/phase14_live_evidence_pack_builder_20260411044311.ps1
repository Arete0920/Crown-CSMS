$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)
    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Copy-IfExists {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    if (Test-Path $Source) {
        $destDir = Split-Path -Parent $Destination
        if ($destDir) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        Copy-Item -Path $Source -Destination $Destination -Force
        return $true
    }
    return $false
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase14"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packetRoot = Join-Path $script:RepoRoot ("docs\release\evidence\live-pack\" + $timestamp)
New-Item -ItemType Directory -Force -Path $packetRoot | Out-Null

$includePaths = @(
    "docs/release/LIVE_RELEASE_TRUTH.md",
    "docs/release/LIVE_BACKEND_VERIFICATION.md",
    "docs/release/LIVE_MODULE_PROOF_MATRIX.md",
    "docs/release/LIVE_EVIDENCE_INDEX.md",
    "docs/release/LIVE_ACTION_REGISTER.md",
    "docs/release/LIVE_RUNTIME_API_VERIFICATION.md",
    "docs/release/LIVE_FRONTEND_DASHBOARD_PROOF.md",
    "docs/release/LIVE_REPORTING_EXPORT_AUDIT.md",
    "docs/release/LIVE_RELEASE_GATE_STATUS.md",
    "docs/release/LIVE_FINAL_RELEASE_GATE.md",
    "docs/release/LIVE_FINAL_SIGNOFF_CHECKLIST.md",
    "docs/release/LIVE_MODULE_STATUS_SUMMARY.md",
    "docs/release/LIVE_REPO_HYGIENE_PLAN.md",
    "docs/release/LIVE_WORKFLOW_CANONICALIZATION_PLAN.md"
)

$manifestRows = New-Object System.Collections.Generic.List[object]

foreach ($path in $includePaths) {
    $source = Join-Path $script:RepoRoot ($path -replace '/', '\')
    $dest = Join-Path $packetRoot ($path -replace '/', '\')
    $copied = Copy-IfExists -Source $source -Destination $dest
    $manifestRows.Add([pscustomobject]@{
        source_path = $path
        copied      = $copied
        packet_path = if ($copied) { $dest.Substring($script:RepoRoot.Length).TrimStart('\') -replace '\\','/' } else { $null }
    }) | Out-Null
}

$phaseDirs = @(
    "docs/release/live-audit/phase1",
    "docs/release/live-audit/phase2",
    "docs/release/live-audit/phase3",
    "docs/release/live-audit/phase4",
    "docs/release/live-audit/phase5",
    "docs/release/live-audit/phase6",
    "docs/release/live-audit/phase7",
    "docs/release/live-audit/phase8",
    "docs/release/live-audit/phase9",
    "docs/release/live-audit/phase10",
    "docs/release/live-audit/phase11",
    "docs/release/live-audit/phase12",
    "docs/release/live-audit/phase13"
)

foreach ($dir in $phaseDirs) {
    $sourceDir = Join-Path $script:RepoRoot ($dir -replace '/', '\')
    $destDir = Join-Path $packetRoot ($dir -replace '/', '\')
    if (Test-Path $sourceDir) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        Copy-Item -Path (Join-Path $sourceDir "*") -Destination $destDir -Recurse -Force
        $manifestRows.Add([pscustomobject]@{
            source_path = $dir
            copied      = $true
            packet_path = $destDir.Substring($script:RepoRoot.Length).TrimStart('\') -replace '\\','/'
        }) | Out-Null
    }
}

$manifestItems = if ($manifestRows.Count -gt 0) { $manifestRows.ToArray() } else { @() }
$manifestCsv = Join-Path $packetRoot "manifest.csv"
$manifestItems | Export-Csv -Path $manifestCsv -NoTypeInformation -Encoding UTF8

$indexMd = Join-Path $packetRoot "INDEX.md"
$indexLines = ($manifestRows | ForEach-Object {
    "- $($_.source_path) | copied=$($_.copied) | packet_path=$($_.packet_path)"
}) -join "`r`n"

$indexMarkdown = @"
# LIVE EVIDENCE PACK INDEX

Generated UTC: $((Get-Date).ToUniversalTime().ToString("o"))

## Manifest
$indexLines
"@
Set-Content -Path $indexMd -Value $indexMarkdown -Encoding UTF8

$zipPath = Join-Path $script:RepoRoot ("docs\release\evidence\live-pack\crown_live_evidence_pack_" + $timestamp + ".zip")
if (Test-Path $zipPath) { Remove-Item -Path $zipPath -Force }
Compress-Archive -Path (Join-Path $packetRoot "*") -DestinationPath $zipPath -Force

$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_EVIDENCE_PACKET.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_EVIDENCE_PACKET.json"
$phaseSummaryJson = Join-Path $outDir "phase14_live_evidence_pack_builder.json"
$phaseSummaryMd = Join-Path $outDir "phase14_live_evidence_pack_builder.md"

$copiedManifestRows = @($manifestRows | Where-Object { $_.copied })
$copiedCount = $copiedManifestRows.Count
$summary = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    packet_root      = $packetRoot.Substring($script:RepoRoot.Length).TrimStart('\') -replace '\\','/'
    zip_path         = $zipPath.Substring($script:RepoRoot.Length).TrimStart('\') -replace '\\','/'
    manifest_count   = $manifestRows.Count
    copied_count     = $copiedCount
}

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    manifest         = $manifestItems
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
} | ConvertTo-Json -Depth 6 | Set-Content -Path $phaseSummaryJson -Encoding UTF8

$liveMarkdown = @"
# LIVE EVIDENCE PACKET

Generated UTC: $($summary.generated_at_utc)

## Summary
- packet root: $($summary.packet_root)
- zip path: $($summary.zip_path)
- manifest count: $($summary.manifest_count)
- copied count: $($summary.copied_count)

## Key Files
- $($summary.packet_root)/INDEX.md
- $($summary.packet_root)/manifest.csv
- $($summary.zip_path)
"@

$phaseMarkdown = @"
# Phase 14 Live Evidence Pack Builder

Generated UTC: $($summary.generated_at_utc)

## Outputs
- docs/release/LIVE_EVIDENCE_PACKET.md
- $($summary.zip_path)

## Summary
- manifest count: $($summary.manifest_count)
- copied count: $($summary.copied_count)

## Packet Root
- $($summary.packet_root)
"@

Set-Content -Path $liveMd -Value $liveMarkdown -Encoding UTF8
Set-Content -Path $phaseSummaryMd -Value $phaseMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 14 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live evidence packet: $liveMd"
Write-Host "Zip: $zipPath"
Write-Host ""