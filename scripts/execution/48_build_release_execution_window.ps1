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

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Target
    )
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
        Copy-Item $Source $Target -Force
        return $true
    }
    return $false
}

function Copy-LatestTree {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )
    if (Test-Path $SourceDir) {
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
        Copy-Item (Join-Path $SourceDir "*") $TargetDir -Recurse -Force
        return $true
    }
    return $false
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts\release-execution-window"
$out = Join-Path $base $ts
$latest = Join-Path $base "latest"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$masterGateLatest = Join-Path $repoRoot "audit-artifacts\release-master-gate\latest"
$packetLatest = Join-Path $repoRoot "audit-artifacts\release-candidate-packet\latest"
$dayPackLatest = Join-Path $repoRoot "audit-artifacts\release-day-command-pack\latest"
$controlLatest = Join-Path $repoRoot "audit-artifacts\release-control-center\latest"
$archiveLatest = Join-Path $repoRoot "audit-artifacts\release-archive-packet\latest"
$warRoomBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

Copy-LatestTree -SourceDir $masterGateLatest -TargetDir (Join-Path $out "01_master-gate") | Out-Null
Copy-LatestTree -SourceDir $packetLatest -TargetDir (Join-Path $out "02_release-candidate-packet") | Out-Null
Copy-LatestTree -SourceDir $dayPackLatest -TargetDir (Join-Path $out "03_release-day-command-pack") | Out-Null
Copy-LatestTree -SourceDir $controlLatest -TargetDir (Join-Path $out "04_release-control-center") | Out-Null
Copy-LatestTree -SourceDir $archiveLatest -TargetDir (Join-Path $out "05_release-archive-packet") | Out-Null
Copy-IfExists -Source $warRoomBoard -Target (Join-Path $out "06_priority_board.csv") | Out-Null

$masterSummary = ""
if (Test-Path (Join-Path $masterGateLatest "SUMMARY.md")) {
    $masterSummary = Get-Content (Join-Path $masterGateLatest "SUMMARY.md") -Raw
}
$releaseReady = $masterSummary -match "Overall release ready: True"

Set-Utf8File -Path (Join-Path $out "07_release_preflight_WORKING.md") -Content @"
# Release Preflight Working Checklist

## Release window
- Date:
- Start time:
- End time:
- Environment:
- Release version / commit:

## Required confirmations
- [ ] release-candidate packet reviewed
- [ ] priority board reviewed
- [ ] runtime proof still green
- [ ] payment readiness still closed
- [ ] legal readiness still closed
- [ ] pilot readiness still closed
- [ ] cutover readiness still closed
- [ ] release owner present
- [ ] rollback owner present
- [ ] verification owner present
- [ ] communication owner present
- [ ] backup verification recorded
- [ ] migration path confirmed
- [ ] smoke test owners assigned

## People on point
- Release owner:
- Rollback owner:
- Verification owner:
- Comms owner:
- Final approver:

## Notes
-
"@

Set-Utf8File -Path (Join-Path $out "08_release_window_tracker.csv") -Content @"
Timestamp,Phase,Owner,Status,Notes
,Preflight,,Open,
,Deploy Start,,Open,
,Migrations,,Open,
,Smoke Tests,,Open,
,Go-NoGo,,Open,
,Hypercare,,Open,
"@

Set-Utf8File -Path (Join-Path $out "09_smoke_test_matrix_WORKING.csv") -Content @"
Area,FlowOrEndpoint,Owner,Status,Timestamp,Notes
Health,/api/health/,,Open,,
Integrity,/api/integrity/,,Open,,
Authentication,Critical login path,,Open,,
Admin,Admin critical workflow,,Open,,
Parent,Parent critical workflow,,Open,,
Teacher,Teacher critical workflow,,Open,,
Payment,Payment-related workflow,,Open,,
"@

Set-Utf8File -Path (Join-Path $out "10_go_no_go_WORKING.md") -Content @"
# Go / No-Go Working Decision

## Gate source
- Master gate says release ready: $releaseReady

## Final checks
- [ ] preflight complete
- [ ] release runbook completed
- [ ] smoke test matrix assigned
- [ ] rollback sheet assigned
- [ ] release communications drafted
- [ ] final approver present

## Decision
- Status:
- Date:
- Time:
- Release owner:
- Final approver:
- Verification owner:
- Notes:
"@

Set-Utf8File -Path (Join-Path $out "11_release_decision_log.md") -Content @"
# Release Decision Log

| Timestamp | Decision | Owner | Status | Notes |
|---|---|---|---|---|
|  | Start preflight |  | Open |  |
|  | Approve release window |  | Open |  |
|  | Approve deploy start |  | Open |  |
|  | Approve go/no-go |  | Open |  |
|  | Approve hypercare close |  | Open |  |
"@

Set-Utf8File -Path (Join-Path $out "12_hypercare_log.csv") -Content @"
Timestamp,Check,Owner,Status,Notes
,15-minute health check,,Open,
,1-hour health check,,Open,
,4-hour health check,,Open,
,Next business day review,,Open,
"@

Set-Utf8File -Path (Join-Path $out "13_release_comms_WORKING.md") -Content @"
# Release Communications Working Draft

## Internal start notice
Release window has started.
Release owner:
Rollback owner:
Verification owner:
Environment:
Start time:
Expected completion:

## Internal success notice
Release completed successfully.
Timestamp:
Release owner:
Smoke test summary:
Notes:

## Internal rollback notice
Release rolled back.
Timestamp:
Reason:
Rollback owner:
Next steps:
"@

Set-Utf8File -Path (Join-Path $out "14_release_runbook_WORKING.md") -Content @"
# Release Runbook Working Copy

## Before deploy
- Final approver:
- Release owner:
- Rollback owner:
- Verification owner:
- Environment:
- Deployment target:
- Backup confirmation:

## Deploy commands
- Deploy command:
- Migration command:
- Static/assets command:
- Warmup command:

## Verification steps
1. Health endpoint
2. Integrity endpoint
3. Authentication flow
4. Admin critical flow
5. Parent critical flow
6. Teacher critical flow
7. Payment-related flow

## Rollback commands
- Rollback command:
- Previous artifact reference:
- Restore steps:

## Notes
-
"@

Set-Utf8File -Path (Join-Path $out "15_release_command_shell.ps1") -Content @'
param(
    [string]$DeployCommand = "",
    [string]$MigrationCommand = "",
    [string]$WarmupCommand = ""
)

$ErrorActionPreference = "Stop"

Write-Host "RELEASE COMMAND SHELL"
Write-Host "1. Fill DeployCommand, MigrationCommand, WarmupCommand before execution."
Write-Host "2. Review 14_release_runbook_WORKING.md before using this file."
Write-Host "3. This file does not auto-deploy until commands are explicitly provided."

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
'@

Set-Utf8File -Path (Join-Path $out "16_validate_release_execution_window.ps1") -Content @'
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$latest = Join-Path $repoRoot "audit-artifacts\release-execution-window\latest"
if (-not (Test-Path $latest)) {
    throw "Missing release execution window latest folder."
}

$required = @(
    "07_release_preflight_WORKING.md",
    "08_release_window_tracker.csv",
    "09_smoke_test_matrix_WORKING.csv",
    "10_go_no_go_WORKING.md",
    "11_release_decision_log.md",
    "12_hypercare_log.csv",
    "13_release_comms_WORKING.md",
    "14_release_runbook_WORKING.md"
)

$report = foreach ($name in $required) {
    $path = Join-Path $latest $name
    [pscustomobject]@{
        File     = $name
        Exists   = Test-Path $path
        Size     = if (Test-Path $path) { (Get-Item $path).Length } else { 0 }
        NonEmpty = if (Test-Path $path) { (Get-Item $path).Length -gt 50 } else { $false }
    }
}

$out = Join-Path $latest "17_release_execution_validation.txt"
"=== RELEASE EXECUTION WINDOW VALIDATION ===" | Set-Content $out -Encoding utf8
$report | Format-Table File,Exists,Size,NonEmpty -AutoSize | Out-String | Add-Content $out

$preflight = Get-Content (Join-Path $latest "07_release_preflight_WORKING.md") -Raw
$gng = Get-Content (Join-Path $latest "10_go_no_go_WORKING.md") -Raw

$preflightReady = ($preflight -notmatch "- \[ \]")
$gngReady = (($gng -match "Status:") -and ($gng -notmatch "Status:\s*$"))

"" | Add-Content $out
("Preflight complete: " + $preflightReady) | Add-Content $out
("Go / No-Go completed: " + $gngReady) | Add-Content $out

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$canExecute = $allFilesReady -and $preflightReady -and $gngReady

("Ready to execute release window: " + $canExecute) | Add-Content $out
Write-Host "Validation file: $out"
Write-Host "Ready to execute release window: $canExecute"
'@

Set-Utf8File -Path (Join-Path $out "18_release_execution_summary.md") -Content @"
# Release Execution Window Summary

## Output root
$out

## Release ready from master gate
$releaseReady

## Working files
- 07_release_preflight_WORKING.md
- 08_release_window_tracker.csv
- 09_smoke_test_matrix_WORKING.csv
- 10_go_no_go_WORKING.md
- 11_release_decision_log.md
- 12_hypercare_log.csv
- 13_release_comms_WORKING.md
- 14_release_runbook_WORKING.md
- 15_release_command_shell.ps1
- 16_validate_release_execution_window.ps1

## Exit condition
- preflight completed
- go / no-go completed
- validation says ready to execute release window = True
"@

New-Item -ItemType Directory -Force -Path $latest | Out-Null

# Lock-tolerant sync to latest: do not delete latest, copy what we can.
Get-ChildItem -Path $out -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($out.Length).TrimStart('\\')
    $targetPath = Join-Path $latest $relative

    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Force -Path $targetPath | Out-Null
    }
    else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetPath) | Out-Null
        try {
            Copy-Item -Path $_.FullName -Destination $targetPath -Force -ErrorAction Stop
        }
        catch {
            Write-Warning "Could not copy to latest: $targetPath"
        }
    }
}

if ($OpenFiles) {
    Open-IfExists (Join-Path $latest "18_release_execution_summary.md")
    Open-IfExists (Join-Path $latest "07_release_preflight_WORKING.md")
    Open-IfExists (Join-Path $latest "08_release_window_tracker.csv")
    Open-IfExists (Join-Path $latest "09_smoke_test_matrix_WORKING.csv")
    Open-IfExists (Join-Path $latest "10_go_no_go_WORKING.md")
    Open-IfExists (Join-Path $latest "11_release_decision_log.md")
    Open-IfExists (Join-Path $latest "12_hypercare_log.csv")
    Open-IfExists (Join-Path $latest "13_release_comms_WORKING.md")
    Open-IfExists (Join-Path $latest "14_release_runbook_WORKING.md")
    Open-IfExists (Join-Path $latest "15_release_command_shell.ps1")
    Open-IfExists (Join-Path $latest "16_validate_release_execution_window.ps1")
}

Write-Host "Done: $out"
Write-Host "Latest: $latest"
Write-Host "Release ready from master gate: $releaseReady"
