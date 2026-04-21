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
$dayBase = Join-Path $repoRoot "audit-artifacts\release-day-command-pack"
$dayOut = Join-Path $dayBase $ts
$dayLatest = Join-Path $dayBase "latest"
New-Item -ItemType Directory -Force -Path $dayOut | Out-Null

$packetLatest = Join-Path $repoRoot "audit-artifacts\release-candidate-packet\latest"
$masterGateLatest = Join-Path $repoRoot "audit-artifacts\release-master-gate\latest"
$boardPath = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

$releaseReady = $false
$masterSummaryPath = Join-Path $masterGateLatest "SUMMARY.md"
if (Test-Path $masterSummaryPath) {
    $masterSummary = Get-Content $masterSummaryPath -Raw
    if ($masterSummary -match "Overall release ready: True") {
        $releaseReady = $true
    }
}

Set-Utf8File -Path (Join-Path $dayOut "01_preflight_checklist.md") -Content @"
# Release Day Preflight Checklist

- [ ] release-candidate packet reviewed
- [ ] priority board reviewed
- [ ] runtime proof still green
- [ ] payment readiness still closed
- [ ] legal readiness still closed
- [ ] pilot readiness still closed
- [ ] cutover readiness still closed
- [ ] deploy owner present
- [ ] rollback owner present
- [ ] verification owner present
- [ ] communication owner present
"@

Set-Utf8File -Path (Join-Path $dayOut "02_release_day_runbook.md") -Content @"
# Release Day Runbook

## Before deploy
- confirm final approver
- confirm rollback owner
- confirm production window
- confirm backup status
- confirm smoke test owners

## Deploy
1. start timestamp:
2. deploy command:
3. migration command:
4. smoke test start:
5. smoke test end:

## After deploy
- confirm health endpoint
- confirm integrity endpoint
- confirm critical app path
- confirm payment-related path
- confirm user-facing path

## Final status
- release completed:
- release owner:
- final approver:
"@

Set-Utf8File -Path (Join-Path $dayOut "03_smoke_test_matrix.csv") -Content @"
Area,EndpointOrFlow,Owner,Status,Timestamp,Notes
Health,/api/health/, ,Open,,
Integrity,/api/integrity/, ,Open,,
Admin critical flow, , ,Open,,
Parent critical flow, , ,Open,,
Teacher critical flow, , ,Open,,
Payment-related flow, , ,Open,,
"@

Set-Utf8File -Path (Join-Path $dayOut "04_rollback_quick_sheet.md") -Content @"
# Rollback Quick Sheet

## Trigger conditions
- critical smoke failure
- data integrity issue
- authentication failure
- payment-critical failure

## Rollback owner
- Name:
- Phone:
- Email:

## Rollback steps
1. stop current deployment
2. execute rollback command
3. restore prior artifact
4. verify health
5. verify integrity
6. rerun smoke checks

## Timestamp log
- rollback started:
- rollback completed:
- verified by:
"@

Set-Utf8File -Path (Join-Path $dayOut "05_release_comms_template.md") -Content @"
# Release Communications Template

## Internal start notice
Release window has started.
Owner:
Rollback owner:
Verification owner:
Expected completion:

## Internal success notice
Release completed successfully.
Timestamp:
Smoke tests:
Owner:

## Internal rollback notice
Release rolled back.
Timestamp:
Reason:
Rollback owner:
Next steps:
"@

Set-Utf8File -Path (Join-Path $dayOut "06_go_no_go_signoff.md") -Content @"
# Go / No-Go Sign-Off

## Gate
- Release ready from master gate: $releaseReady

## Decision
- Status:
- Date:
- Final approver:
- Release owner:
- Verification owner:
- Notes:
"@

Set-Utf8File -Path (Join-Path $dayOut "07_release_packet_pointer.txt") -Content @"
Release candidate latest:
$packetLatest

Master gate latest:
$masterGateLatest

Priority board:
$boardPath
"@

Set-Utf8File -Path (Join-Path $dayOut "SUMMARY.md") -Content @"
# Release Day Command Pack Summary

## Output root
$dayOut

## Release ready from master gate
$releaseReady

## Files
- 01_preflight_checklist.md
- 02_release_day_runbook.md
- 03_smoke_test_matrix.csv
- 04_rollback_quick_sheet.md
- 05_release_comms_template.md
- 06_go_no_go_signoff.md
- 07_release_packet_pointer.txt
"@

if (-not (Test-Path $dayLatest)) {
    New-Item -ItemType Directory -Force -Path $dayLatest | Out-Null
}
Copy-Item (Join-Path $dayOut "*") $dayLatest -Recurse -Force

if ($OpenFiles) {
    Open-IfExists (Join-Path $dayLatest "SUMMARY.md")
    Open-IfExists (Join-Path $dayLatest "01_preflight_checklist.md")
    Open-IfExists (Join-Path $dayLatest "02_release_day_runbook.md")
    Open-IfExists (Join-Path $dayLatest "03_smoke_test_matrix.csv")
    Open-IfExists (Join-Path $dayLatest "04_rollback_quick_sheet.md")
    Open-IfExists (Join-Path $dayLatest "05_release_comms_template.md")
    Open-IfExists (Join-Path $dayLatest "06_go_no_go_signoff.md")
}

Write-Host "Done: $dayOut"
Write-Host "Latest: $dayLatest"
Write-Host "Release ready from master gate: $releaseReady"
