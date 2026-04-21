param(
    [switch]$Rebuild,
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

function Ensure-LatestArtifacts {
    param([string]$RepoRoot)

    if ($Rebuild) {
        $scriptsToRun = @(
            ".\scripts\execution\31_runtime_release_closure.ps1 -StartLocalServer",
            ".\scripts\execution\35_finalize_payment_item7.ps1",
            ".\scripts\execution\42_finish_release_items_8_9_10.ps1 -ValidateOnly",
            ".\scripts\execution\43_release_master_gate.ps1",
            ".\scripts\execution\44_build_release_candidate_packet.ps1",
            ".\scripts\execution\45_build_release_day_command_pack.ps1"
        )

        foreach ($command in $scriptsToRun) {
            powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location `"$RepoRoot`"; $command"
        }
    }
}

function Read-IfExists {
    param([string]$Path)
    if (Test-Path $Path) {
        return Get-Content $Path -Raw
    }
    return ""
}

function Test-ChecklistCompleted {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    $content = Get-Content $Path -Raw
    if ($content -match "- \[ \]") { return $false }
    return $true
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

Ensure-LatestArtifacts -RepoRoot $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts\release-control-center"
$out = Join-Path $base $ts
$latest = Join-Path $base "latest"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$runtimeLatest = Join-Path $repoRoot "audit-artifacts\runtime-release-closure\latest"
$paymentLatest = Join-Path $repoRoot "audit-artifacts\payment-readiness\latest"
$legalLatest = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness\latest"
$pilotLatest = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness\latest"
$cutoverLatest = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness\latest"
$masterGateLatest = Join-Path $repoRoot "audit-artifacts\release-master-gate\latest"
$packetLatest = Join-Path $repoRoot "audit-artifacts\release-candidate-packet\latest"
$dayPackLatest = Join-Path $repoRoot "audit-artifacts\release-day-command-pack\latest"
$boardPath = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

$boardRows = @()
if (Test-Path $boardPath) {
    $boardRows = Import-Csv $boardPath
}

$item7 = $boardRows | Where-Object { $_.Priority -eq "7" } | Select-Object -First 1
$item8 = $boardRows | Where-Object { $_.Priority -eq "8" } | Select-Object -First 1
$item9 = $boardRows | Where-Object { $_.Priority -eq "9" } | Select-Object -First 1
$item10 = $boardRows | Where-Object { $_.Priority -eq "10" } | Select-Object -First 1

$runtimeFiles = @(
    "03_django_check.txt",
    "04_showmigrations.txt",
    "05_deploy_check.txt",
    "06_health_endpoint.txt",
    "07_integrity_endpoint.txt"
)

$runtimeStatus = @()
foreach ($name in $runtimeFiles) {
    $path = Join-Path $runtimeLatest $name
    $exists = Test-Path $path
    $content = if ($exists) { Get-Content $path -Raw } else { "" }
    $signal = switch ($name) {
        "03_django_check.txt" { $content -match "System check identified no issues" }
        "05_deploy_check.txt" { $content -match "System check identified no issues" }
        "06_health_endpoint.txt" { $content -match "ok|healthy|status" }
        "07_integrity_endpoint.txt" { $content -match "ok|healthy|status" }
        default { $exists -and ($content.Length -gt 0) }
    }
    $runtimeStatus += [pscustomobject]@{
        Area   = $name
        Exists = $exists
        Green  = [bool]$signal
        Path   = $path
    }
}

$runtimeGreen = ($runtimeStatus | Where-Object { $_.Green -eq $false }).Count -eq 0

$paymentClosed = ($item7.Status -eq "Closed")
$legalClosed = ($item8.Status -eq "Closed")
$pilotClosed = ($item9.Status -eq "Closed")
$cutoverClosed = ($item10.Status -eq "Closed")

$masterSummaryPath = Join-Path $masterGateLatest "SUMMARY.md"
$masterSummary = Read-IfExists $masterSummaryPath
$masterReady = $masterSummary -match "Overall release ready: True"

$goNoGoPath = Join-Path $dayPackLatest "06_go_no_go_signoff.md"
$goNoGoContent = Read-IfExists $goNoGoPath
$goNoGoSigned = ($goNoGoContent -match "Status:" -and $goNoGoContent -notmatch "Status:\s*$")

$preflightPath = Join-Path $dayPackLatest "01_preflight_checklist.md"
$preflightDone = Test-ChecklistCompleted -Path $preflightPath

$runbookPath = Join-Path $dayPackLatest "02_release_day_runbook.md"
$smokeMatrixPath = Join-Path $dayPackLatest "03_smoke_test_matrix.csv"
$rollbackQuickSheetPath = Join-Path $dayPackLatest "04_rollback_quick_sheet.md"
$commsTemplatePath = Join-Path $dayPackLatest "05_release_comms_template.md"

$packetSummaryPath = Join-Path $packetLatest "SUMMARY.md"
$packetSummary = Read-IfExists $packetSummaryPath

$overallReady = $runtimeGreen -and $paymentClosed -and $legalClosed -and $pilotClosed -and $cutoverClosed -and $masterReady

$scorecard = @(
    [pscustomobject]@{ Gate = "Runtime proof"; Status = $(if ($runtimeGreen) { "PASS" } else { "FAIL" }); Source = $runtimeLatest; Owner = "Dev 1 / Dev 5" },
    [pscustomobject]@{ Gate = "Payment readiness"; Status = $(if ($paymentClosed) { "PASS" } else { "FAIL" }); Source = $paymentLatest; Owner = "Joanne" },
    [pscustomobject]@{ Gate = "Legal / DPA readiness"; Status = $(if ($legalClosed) { "PASS" } else { "FAIL" }); Source = $legalLatest; Owner = "TC / Legal" },
    [pscustomobject]@{ Gate = "Pilot / LOI readiness"; Status = $(if ($pilotClosed) { "PASS" } else { "FAIL" }); Source = $pilotLatest; Owner = "TC" },
    [pscustomobject]@{ Gate = "Cutover / rollback readiness"; Status = $(if ($cutoverClosed) { "PASS" } else { "FAIL" }); Source = $cutoverLatest; Owner = "Dev 5" },
    [pscustomobject]@{ Gate = "Master release gate"; Status = $(if ($masterReady) { "PASS" } else { "FAIL" }); Source = $masterGateLatest; Owner = "Release lead" },
    [pscustomobject]@{ Gate = "Go / No-Go signoff"; Status = $(if ($goNoGoSigned) { "PASS" } else { "OPEN" }); Source = $goNoGoPath; Owner = "Final approver" },
    [pscustomobject]@{ Gate = "Preflight checklist"; Status = $(if ($preflightDone) { "PASS" } else { "OPEN" }); Source = $preflightPath; Owner = "Release owner" }
)
$scorecard | Export-Csv (Join-Path $out "01_release_scorecard.csv") -NoTypeInformation -Encoding utf8

$ownerMatrix = @(
    [pscustomobject]@{ Priority = 7; Area = "Payment readiness"; Owner = "Joanne"; Status = $item7.Status; Source = $paymentLatest; NextAction = "Complete checklist and finance signoff" },
    [pscustomobject]@{ Priority = 8; Area = "Legal / DPA readiness"; Owner = "TC / Legal"; Status = $item8.Status; Source = $legalLatest; NextAction = "Complete packet and legal signoff" },
    [pscustomobject]@{ Priority = 9; Area = "Pilot / LOI readiness"; Owner = "TC"; Status = $item9.Status; Source = $pilotLatest; NextAction = "Record signed LOI and pilot start" },
    [pscustomobject]@{ Priority = 10; Area = "Cutover / rollback readiness"; Owner = "Dev 5"; Status = $item10.Status; Source = $cutoverLatest; NextAction = "Complete rehearsal and go/no-go" }
)
$ownerMatrix | Export-Csv (Join-Path $out "02_owner_action_matrix.csv") -NoTypeInformation -Encoding utf8

$runtimeStatus | Export-Csv (Join-Path $out "03_runtime_signal_matrix.csv") -NoTypeInformation -Encoding utf8

$releaseDashboard = @()
$releaseDashboard += "# Release Control Center"
$releaseDashboard += ""
$releaseDashboard += "- Output root: $out"
$releaseDashboard += "- Overall ready: $overallReady"
$releaseDashboard += ""
$releaseDashboard += "## Scorecard"
foreach ($row in $scorecard) {
    $releaseDashboard += "- $($row.Gate): $($row.Status)"
}
$releaseDashboard += ""
$releaseDashboard += "## Priority items"
$releaseDashboard += "- Item 7: $($item7.Status)"
$releaseDashboard += "- Item 8: $($item8.Status)"
$releaseDashboard += "- Item 9: $($item9.Status)"
$releaseDashboard += "- Item 10: $($item10.Status)"
$releaseDashboard += ""
$releaseDashboard += "## Command sources"
$releaseDashboard += "- Runtime latest: $runtimeLatest"
$releaseDashboard += "- Payment latest: $paymentLatest"
$releaseDashboard += "- Legal latest: $legalLatest"
$releaseDashboard += "- Pilot latest: $pilotLatest"
$releaseDashboard += "- Cutover latest: $cutoverLatest"
$releaseDashboard += "- Master gate latest: $masterGateLatest"
$releaseDashboard += "- Release packet latest: $packetLatest"
$releaseDashboard += "- Day pack latest: $dayPackLatest"
$releaseDashboard += ""
$releaseDashboard += "## Next step"
if ($overallReady) {
    $releaseDashboard += "- Complete release-day runbook, smoke matrix, and go/no-go signoff."
} else {
    $releaseDashboard += "- Close all FAIL / OPEN gates, then rerun this script."
}
Set-Utf8File -Path (Join-Path $out "04_release_control_center.md") -Content ($releaseDashboard -join "`r`n")

Set-Utf8File -Path (Join-Path $out "05_release_path_map.md") -Content @"
# Release Path Map

## Runtime
$runtimeLatest

## Payment
$paymentLatest

## Legal
$legalLatest

## Pilot
$pilotLatest

## Cutover
$cutoverLatest

## Master Gate
$masterGateLatest

## Release Candidate Packet
$packetLatest

## Release Day Command Pack
$dayPackLatest

## War Room Board
$boardPath
"@

Set-Utf8File -Path (Join-Path $out "06_release_commander_checklist.md") -Content @"
# Release Commander Checklist

## Before release
- [ ] review 01_release_scorecard.csv
- [ ] review 02_owner_action_matrix.csv
- [ ] confirm all FAIL gates are closed
- [ ] confirm payment/legal/pilot/cutover items are closed
- [ ] confirm release-candidate packet is current
- [ ] confirm release-day pack is current

## Release decision
- [ ] preflight checklist complete
- [ ] release-day runbook complete
- [ ] smoke test matrix assigned
- [ ] rollback quick sheet assigned
- [ ] go/no-go signoff completed

## After release
- [ ] archive final packet
- [ ] archive final day pack
- [ ] record final release decision
"@

Set-Utf8File -Path (Join-Path $out "07_post_release_hypercare.md") -Content @"
# Post-Release Hypercare

## Monitoring cadence
- 15 minutes after release
- 1 hour after release
- 4 hours after release
- next business day

## Checks
- [ ] health endpoint
- [ ] integrity endpoint
- [ ] authentication path
- [ ] critical admin path
- [ ] critical parent path
- [ ] critical teacher path
- [ ] payment-related path

## Incident log
- timestamp:
- issue:
- owner:
- action:
- status:
"@

Set-Utf8File -Path (Join-Path $out "08_release_commander_actions.ps1") -Content @"
code `"$out\04_release_control_center.md`"
code `"$out\01_release_scorecard.csv`"
code `"$out\02_owner_action_matrix.csv`"
code `"$out\03_runtime_signal_matrix.csv`"
code `"$out\06_release_commander_checklist.md`"
code `"$out\07_post_release_hypercare.md`"
code `"$boardPath`"
code `"$masterGateLatest\SUMMARY.md`"
code `"$dayPackLatest\06_go_no_go_signoff.md`"
"@

Set-Utf8File -Path (Join-Path $out "09_rebuild_all_release_artifacts.ps1") -Content @"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\42_finish_release_items_8_9_10.ps1 -ValidateOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\43_release_master_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\44_build_release_candidate_packet.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\45_build_release_day_command_pack.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\46_release_control_center.ps1 -OpenFiles
"@

if (Test-Path $latest) {
    Remove-Item $latest -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $latest | Out-Null
Copy-Item (Join-Path $out "*") $latest -Recurse -Force

if ($OpenFiles) {
    Open-IfExists (Join-Path $latest "04_release_control_center.md")
    Open-IfExists (Join-Path $latest "01_release_scorecard.csv")
    Open-IfExists (Join-Path $latest "02_owner_action_matrix.csv")
    Open-IfExists (Join-Path $latest "03_runtime_signal_matrix.csv")
    Open-IfExists (Join-Path $latest "06_release_commander_checklist.md")
    Open-IfExists (Join-Path $latest "07_post_release_hypercare.md")
    Open-IfExists $boardPath
}

Write-Host "Done: $out"
Write-Host "Latest: $latest"
Write-Host "Overall ready: $overallReady"
