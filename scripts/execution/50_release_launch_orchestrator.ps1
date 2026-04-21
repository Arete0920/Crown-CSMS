param(
    [string]$EnvironmentName = "production",
    [string]$ReleaseVersion = "",
    [string]$DeployCommand = "",
    [string]$MigrationCommand = "",
    [string]$WarmupCommand = "",
    [string]$HealthUrl = "http://127.0.0.1:8000/api/health/",
    [string]$IntegrityUrl = "http://127.0.0.1:8000/api/integrity/",
    [switch]$ExecuteDeploy,
    [switch]$OpenFiles
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

function Add-Log {
    param([string]$Path, [string]$Text)
    $Text | Add-Content -Path $Path -Encoding utf8
}

function Invoke-LoggedCommand {
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

function Invoke-WebProbe {
    param(
        [string]$Url,
        [string]$Path
    )
    "=== PROBE ===" | Set-Content -Path $Path -Encoding utf8
    "URL: $Url" | Add-Content -Path $Path -Encoding utf8
    "" | Add-Content -Path $Path -Encoding utf8
    try {
        Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30 | ConvertTo-Json -Depth 20 | Add-Content -Path $Path -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Add-Content -Path $Path -Encoding utf8
    }
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$launchBase = Join-Path $repoRoot "audit-artifacts\release-launch"
$launchOut = Join-Path $launchBase $ts
$launchLatest = Join-Path $launchBase "latest"
New-Item -ItemType Directory -Force -Path $launchOut | Out-Null

$execWindowLatest = Join-Path $repoRoot "audit-artifacts\release-execution-window\latest"
$masterGateLatest = Join-Path $repoRoot "audit-artifacts\release-master-gate\latest"
$controlCenterLatest = Join-Path $repoRoot "audit-artifacts\release-control-center\latest"
$packetLatest = Join-Path $repoRoot "audit-artifacts\release-candidate-packet\latest"
$archiveLatest = Join-Path $repoRoot "audit-artifacts\release-archive-packet\latest"

if (Test-Path $execWindowLatest) {
    New-Item -ItemType Directory -Force -Path (Join-Path $launchOut "01_execution-window") | Out-Null
    Copy-Item (Join-Path $execWindowLatest "*") (Join-Path $launchOut "01_execution-window") -Recurse -Force
}
if (Test-Path $masterGateLatest) {
    New-Item -ItemType Directory -Force -Path (Join-Path $launchOut "02_master-gate") | Out-Null
    Copy-Item (Join-Path $masterGateLatest "*") (Join-Path $launchOut "02_master-gate") -Recurse -Force
}
if (Test-Path $controlCenterLatest) {
    New-Item -ItemType Directory -Force -Path (Join-Path $launchOut "03_control-center") | Out-Null
    Copy-Item (Join-Path $controlCenterLatest "*") (Join-Path $launchOut "03_control-center") -Recurse -Force
}
if (Test-Path $packetLatest) {
    New-Item -ItemType Directory -Force -Path (Join-Path $launchOut "04_candidate-packet") | Out-Null
    Copy-Item (Join-Path $packetLatest "*") (Join-Path $launchOut "04_candidate-packet") -Recurse -Force
}
if (Test-Path $archiveLatest) {
    New-Item -ItemType Directory -Force -Path (Join-Path $launchOut "05_archive-packet") | Out-Null
    Copy-Item (Join-Path $archiveLatest "*") (Join-Path $launchOut "05_archive-packet") -Recurse -Force
}

$releaseVersionFinal = if ($ReleaseVersion -ne "") { $ReleaseVersion } else { (git rev-parse --short HEAD).Trim() }

Set-Utf8File -Path (Join-Path $launchOut "06_release_context.md") -Content @"
# Release Launch Context

## Environment
$EnvironmentName

## Release version
$releaseVersionFinal

## Timestamp
$ts

## Paths
- Execution window: $execWindowLatest
- Master gate: $masterGateLatest
- Control center: $controlCenterLatest
- Candidate packet: $packetLatest
- Archive packet: $archiveLatest

## Commands
- DeployCommand: $DeployCommand
- MigrationCommand: $MigrationCommand
- WarmupCommand: $WarmupCommand

## URLs
- HealthUrl: $HealthUrl
- IntegrityUrl: $IntegrityUrl
"@

Set-Utf8File -Path (Join-Path $launchOut "07_release_window_log.csv") -Content @"
Timestamp,Phase,Owner,Status,Notes
$ts,Window Start,,Started,Release window opened
"@

Set-Utf8File -Path (Join-Path $launchOut "08_deploy_execution_log.txt") -Content "Deploy not run yet."
Set-Utf8File -Path (Join-Path $launchOut "09_migration_execution_log.txt") -Content "Migrations not run yet."
Set-Utf8File -Path (Join-Path $launchOut "10_warmup_execution_log.txt") -Content "Warmup not run yet."
Set-Utf8File -Path (Join-Path $launchOut "11_health_probe_after_release.txt") -Content "Health probe not run yet."
Set-Utf8File -Path (Join-Path $launchOut "12_integrity_probe_after_release.txt") -Content "Integrity probe not run yet."
Set-Utf8File -Path (Join-Path $launchOut "13_smoke_capture.csv") -Content @"
Area,FlowOrEndpoint,Owner,Status,Timestamp,Notes
Health,$HealthUrl,,Open,,
Integrity,$IntegrityUrl,,Open,,
Authentication,Critical login path,,Open,,
Admin,Admin critical workflow,,Open,,
Parent,Parent critical workflow,,Open,,
Teacher,Teacher critical workflow,,Open,,
Payment,Payment-related workflow,,Open,,
"@

Set-Utf8File -Path (Join-Path $launchOut "14_release_decision.md") -Content @"
# Release Decision

## Status
- Current: In Progress

## Release owner
-

## Final approver
-

## Notes
-
"@

Set-Utf8File -Path (Join-Path $launchOut "15_hypercare_WORKING.csv") -Content @"
Timestamp,Check,Owner,Status,Notes
,15-minute health check,,Open,
,1-hour health check,,Open,
,4-hour health check,,Open,
,Next business day review,,Open,
"@

if ($ExecuteDeploy) {
    if ($DeployCommand -ne "") {
        Invoke-LoggedCommand -Title "Deploy command" -Path (Join-Path $launchOut "08_deploy_execution_log.txt") -CommandText $DeployCommand
        Add-Log -Path (Join-Path $launchOut "07_release_window_log.csv") -Text ((Get-Date -Format s) + ",Deploy,,Completed,Deploy command executed")
    }
    if ($MigrationCommand -ne "") {
        Invoke-LoggedCommand -Title "Migration command" -Path (Join-Path $launchOut "09_migration_execution_log.txt") -CommandText $MigrationCommand
        Add-Log -Path (Join-Path $launchOut "07_release_window_log.csv") -Text ((Get-Date -Format s) + ",Migrations,,Completed,Migration command executed")
    }
    if ($WarmupCommand -ne "") {
        Invoke-LoggedCommand -Title "Warmup command" -Path (Join-Path $launchOut "10_warmup_execution_log.txt") -CommandText $WarmupCommand
        Add-Log -Path (Join-Path $launchOut "07_release_window_log.csv") -Text ((Get-Date -Format s) + ",Warmup,,Completed,Warmup command executed")
    }

    Invoke-WebProbe -Url $HealthUrl -Path (Join-Path $launchOut "11_health_probe_after_release.txt")
    Invoke-WebProbe -Url $IntegrityUrl -Path (Join-Path $launchOut "12_integrity_probe_after_release.txt")
}

Set-Utf8File -Path (Join-Path $launchOut "16_release_launch_summary.md") -Content @"
# Release Launch Summary

## Output root
$launchOut

## Environment
$EnvironmentName

## Release version
$releaseVersionFinal

## Execute deploy flag
$($ExecuteDeploy.IsPresent)

## Files
- 06_release_context.md
- 07_release_window_log.csv
- 08_deploy_execution_log.txt
- 09_migration_execution_log.txt
- 10_warmup_execution_log.txt
- 11_health_probe_after_release.txt
- 12_integrity_probe_after_release.txt
- 13_smoke_capture.csv
- 14_release_decision.md
- 15_hypercare_WORKING.csv
"@

if (Test-Path $launchLatest) {
    Remove-Item $launchLatest -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $launchLatest | Out-Null
Copy-Item (Join-Path $launchOut "*") $launchLatest -Recurse -Force

if ($OpenFiles) {
    Open-IfExists (Join-Path $launchLatest "16_release_launch_summary.md")
    Open-IfExists (Join-Path $launchLatest "06_release_context.md")
    Open-IfExists (Join-Path $launchLatest "07_release_window_log.csv")
    Open-IfExists (Join-Path $launchLatest "13_smoke_capture.csv")
    Open-IfExists (Join-Path $launchLatest "14_release_decision.md")
    Open-IfExists (Join-Path $launchLatest "15_hypercare_WORKING.csv")
}

Write-Host "Done: $launchOut"
Write-Host "Latest: $launchLatest"
