[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$RecoveryScript = 'scripts\recovery\run_revised_48h_sprint.ps1'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Save-Text {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Copy-Or-Placeholder {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Source) {
        Copy-Item $Source $Destination -Force
    }
    else {
        Save-Text -Path $Destination -Text ''
    }
}

function Read-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { return Get-Content -Raw $Path }
    return ''
}

function Parse-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try { return Get-Content -Raw $Path | ConvertFrom-Json } catch { return $null }
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$artifactsRoot = Join-Path $RepoRoot 'audit-artifacts'
$artifacts = Join-Path $artifactsRoot ("maximum-proof-$timestamp")
$packetZip = Join-Path $artifactsRoot ("maximum-proof-$timestamp.zip")
$recoveryScriptPath = Join-Path $RepoRoot $RecoveryScript

if (-not (Test-Path $recoveryScriptPath)) {
    throw "Missing recovery script: $recoveryScriptPath"
}

New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
$before = @(Get-ChildItem $artifactsRoot -Directory -Filter 'revised-48h-*' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)

& powershell -ExecutionPolicy Bypass -File $recoveryScriptPath
$revisedExit = $LASTEXITCODE

$afterDirs = Get-ChildItem $artifactsRoot -Directory -Filter 'revised-48h-*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
$sourceDir = $null
foreach ($dir in $afterDirs) {
    if ($before -notcontains $dir.FullName) {
        $sourceDir = $dir.FullName
        break
    }
}
if (-not $sourceDir -and $afterDirs.Count -gt 0) {
    $sourceDir = $afterDirs[0].FullName
}
if (-not $sourceDir) {
    throw 'Could not locate revised sprint artifact directory.'
}

Copy-Or-Placeholder (Join-Path $sourceDir '15_missing_deploy_inputs.txt') (Join-Path $artifacts '22_missing_deploy_inputs.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '23_run_view.json') (Join-Path $artifacts '31_run_view.json')
Copy-Or-Placeholder (Join-Path $sourceDir '26_failed_job_log.txt') (Join-Path $artifacts '33_failed_job_log.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '25_azure_login_failure.txt') (Join-Path $artifacts '34_azure_login_failure.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '27_live_health.txt') (Join-Path $artifacts '35_live_health.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '28_live_integrity_no_header.txt') (Join-Path $artifacts '36_live_integrity_no_header.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '29_live_integrity_with_header.txt') (Join-Path $artifacts '37_live_integrity_with_header.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '30_live_identity_compare.txt') (Join-Path $artifacts '38_live_identity_compare.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '31_frontend_lint_before.txt') (Join-Path $artifacts '39_frontend_lint_before.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '32_frontend_lint_after.txt') (Join-Path $artifacts '40_frontend_lint_after.txt')
Copy-Or-Placeholder (Join-Path $sourceDir '00_summary.txt') (Join-Path $artifacts '00_summary.txt')

$missingInputsText = Read-IfExists (Join-Path $artifacts '22_missing_deploy_inputs.txt')
$runView = Parse-JsonFile (Join-Path $artifacts '31_run_view.json')
$health = Parse-JsonFile (Join-Path $artifacts '35_live_health.txt')
$identityText = Read-IfExists (Join-Path $artifacts '38_live_identity_compare.txt')
$azureLoginText = Read-IfExists (Join-Path $artifacts '34_azure_login_failure.txt')
$summaryText = Read-IfExists (Join-Path $artifacts '00_summary.txt')

$hardFailures = New-Object System.Collections.Generic.List[string]
if ($revisedExit -ne 0) { $hardFailures.Add("Underlying revised sprint exited with code $revisedExit") }
if ($missingInputsText.Trim()) { $hardFailures.Add('Deploy workflow has missing secret/variable references') }
if ($runView -and $runView.conclusion -ne 'success') { $hardFailures.Add("Controlled deploy conclusion = $($runView.conclusion)") }
if ($azureLoginText.Trim()) { $hardFailures.Add('Controlled deploy failed at Azure Login') }
if ($health -and $health.build_sha -and $identityText -notmatch [regex]::Escape([string]$health.build_sha)) { $hardFailures.Add('Live build identity does not match controlled deploy') }
if ($summaryText -match 'live_integrity_no_header_status = 400|live_integrity_with_header_status = 400') { $hardFailures.Add('Live integrity endpoint is not 200/200') }

$cert = @()
$cert += 'Crown2026 maximum proof certification'
$cert += "timestamp=$timestamp"
$cert += "repo_root=$RepoRoot"
$cert += "source_revised_artifacts=$sourceDir"
$cert += "revised_exit_code=$revisedExit"
$cert += ''
$cert += 'Summary:'
if ($summaryText.Trim()) {
    $cert += $summaryText.TrimEnd().Split([Environment]::NewLine)
}
$cert += ''
if ($hardFailures.Count -eq 0) {
    $cert += 'VERDICT=PASS'
    $cert += 'RELEASE_CERTIFICATION=PROVEN'
}
else {
    $cert += 'VERDICT=FAIL'
    $cert += 'RELEASE_CERTIFICATION=NOT_PROVEN'
    $cert += ''
    $cert += 'Hard failures:'
    foreach ($failure in $hardFailures) {
        $cert += "- $failure"
    }
}
Save-Text -Path (Join-Path $artifacts '98_release_certification.txt') -Text ($cert -join [Environment]::NewLine)

if (Test-Path $packetZip) { Remove-Item -Force $packetZip }
Compress-Archive -Path (Join-Path $artifacts '*') -DestinationPath $packetZip -Force

Write-Host $artifacts
Write-Host $packetZip
if ($hardFailures.Count -gt 0) { exit 1 }
exit 0