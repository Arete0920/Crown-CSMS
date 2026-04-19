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

function Validate-FileSet {
    param(
        [string]$Root,
        [string[]]$RequiredFiles
    )
    $result = @()
    foreach ($name in $RequiredFiles) {
        $path = Join-Path $Root $name
        $exists = Test-Path $path
        $size = if ($exists) { (Get-Item $path).Length } else { 0 }
        $nonEmpty = $size -gt 50
        $result += [pscustomobject]@{
            File     = $name
            Exists   = $exists
            Size     = $size
            NonEmpty = $nonEmpty
            Path     = $path
        }
    }
    return $result
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$releaseBase = Join-Path $repoRoot "audit-artifacts\release-master-gate"
$releaseOut = Join-Path $releaseBase $ts
$releaseLatest = Join-Path $releaseBase "latest"
New-Item -ItemType Directory -Force -Path $releaseOut | Out-Null

$runtimeLatest = Join-Path $repoRoot "audit-artifacts\runtime-release-closure\latest"
$paymentLatest = Join-Path $repoRoot "audit-artifacts\payment-readiness\latest"
$legalLatest = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness\latest"
$pilotLatest = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness\latest"
$cutoverLatest = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness\latest"
$boardPath = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

$runtimeRequired = @(
    "03_django_check.txt",
    "04_showmigrations.txt",
    "05_deploy_check.txt",
    "06_health_endpoint.txt",
    "07_integrity_endpoint.txt"
)
$paymentRequired = @(
    "01_payment_validation_checklist_WORKING.md",
    "02_payment_owner_assignment.md",
    "03_gateway_access_check.md",
    "04_test_transaction_log.csv",
    "05_reconciliation_proof.md",
    "06_finance_signoff.md",
    "07_required_evidence_checklist.md",
    "08_payment_closeout_validation.txt"
)
$legalRequired = @(
    "01_legal_dpa_readiness_WORKING.md",
    "02_legal_owner_assignment.md",
    "03_dpa_clause_review_matrix.md",
    "04_signature_workflow.md",
    "05_data_handling_responsibilities.md",
    "06_school_facing_packet_checklist.md",
    "07_final_legal_signoff.md",
    "08_required_evidence_checklist.md",
    "09_legal_closeout_validation.txt"
)
$pilotRequired = @(
    "01_pilot_loi_tracker_WORKING.md",
    "02_pilot_loi_tracker_WORKING.csv",
    "03_pipeline_owner_assignment.md",
    "04_outreach_conversion_checklist.md",
    "05_required_evidence_checklist.md",
    "06_pilot_loi_closeout_validation.txt"
)
$cutoverRequired = @(
    "01_cutover_rollback_checklist_WORKING.md",
    "02_release_owner_assignment.md",
    "03_rehearsal_log.md",
    "04_required_evidence_checklist.md",
    "05_cutover_closeout_validation.txt"
)

$runtimeReport = Validate-FileSet -Root $runtimeLatest -RequiredFiles $runtimeRequired
$paymentReport = Validate-FileSet -Root $paymentLatest -RequiredFiles $paymentRequired
$legalReport = Validate-FileSet -Root $legalLatest -RequiredFiles $legalRequired
$pilotReport = Validate-FileSet -Root $pilotLatest -RequiredFiles $pilotRequired
$cutoverReport = Validate-FileSet -Root $cutoverLatest -RequiredFiles $cutoverRequired

$boardRows = @()
if (Test-Path $boardPath) {
    $boardRows = Import-Csv $boardPath
}

$runtimeGreen = $false
$runtimeValidation = @{}
foreach ($name in @("03_django_check.txt", "05_deploy_check.txt", "06_health_endpoint.txt", "07_integrity_endpoint.txt")) {
    $p = Join-Path $runtimeLatest $name
    $txt = if (Test-Path $p) { Get-Content $p -Raw } else { "" }
    $runtimeValidation[$name] = $txt
}

if (
    ($runtimeValidation["03_django_check.txt"] -match "System check identified no issues") -and
    ($runtimeValidation["05_deploy_check.txt"] -match "System check identified no issues") -and
    ($runtimeValidation["06_health_endpoint.txt"] -match "status" -or $runtimeValidation["06_health_endpoint.txt"] -match "ok" -or $runtimeValidation["06_health_endpoint.txt"] -match "healthy") -and
    ($runtimeValidation["07_integrity_endpoint.txt"] -match "status" -or $runtimeValidation["07_integrity_endpoint.txt"] -match "ok" -or $runtimeValidation["07_integrity_endpoint.txt"] -match "healthy")
) {
    $runtimeGreen = $true
}

$paymentClosed = $false
$legalClosed = $false
$pilotClosed = $false
$cutoverClosed = $false

if ($boardRows.Count -gt 0) {
    foreach ($row in $boardRows) {
        if ($row.Priority -eq "7" -and $row.Status -eq "Closed") { $paymentClosed = $true }
        if ($row.Priority -eq "8" -and $row.Status -eq "Closed") { $legalClosed = $true }
        if ($row.Priority -eq "9" -and $row.Status -eq "Closed") { $pilotClosed = $true }
        if ($row.Priority -eq "10" -and $row.Status -eq "Closed") { $cutoverClosed = $true }
    }
}

$allRuntimeFilesPresent = ($runtimeReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$allPaymentFilesPresent = ($paymentReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$allLegalFilesPresent = ($legalReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$allPilotFilesPresent = ($pilotReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$allCutoverFilesPresent = ($cutoverReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0

$overallReleaseReady = $runtimeGreen -and $paymentClosed -and $legalClosed -and $pilotClosed -and $cutoverClosed

$gateMatrix = @()
$gateMatrix += [pscustomobject]@{ Gate = "Runtime proof"; FilesPresent = $allRuntimeFilesPresent; Status = $(if ($runtimeGreen) { "PASS" } else { "FAIL" }); Detail = "django check, deploy check, health, integrity" }
$gateMatrix += [pscustomobject]@{ Gate = "Payment readiness"; FilesPresent = $allPaymentFilesPresent; Status = $(if ($paymentClosed) { "PASS" } else { "FAIL" }); Detail = "Board item 7 must be Closed" }
$gateMatrix += [pscustomobject]@{ Gate = "Legal / DPA readiness"; FilesPresent = $allLegalFilesPresent; Status = $(if ($legalClosed) { "PASS" } else { "FAIL" }); Detail = "Board item 8 must be Closed" }
$gateMatrix += [pscustomobject]@{ Gate = "Pilot / LOI readiness"; FilesPresent = $allPilotFilesPresent; Status = $(if ($pilotClosed) { "PASS" } else { "FAIL" }); Detail = "Board item 9 must be Closed" }
$gateMatrix += [pscustomobject]@{ Gate = "Cutover / rollback readiness"; FilesPresent = $allCutoverFilesPresent; Status = $(if ($cutoverClosed) { "PASS" } else { "FAIL" }); Detail = "Board item 10 must be Closed" }

$gateMatrix | Export-Csv (Join-Path $releaseOut "01_gate_matrix.csv") -NoTypeInformation -Encoding utf8

$runtimeReport | Export-Csv (Join-Path $releaseOut "02_runtime_report.csv") -NoTypeInformation -Encoding utf8
$paymentReport | Export-Csv (Join-Path $releaseOut "03_payment_report.csv") -NoTypeInformation -Encoding utf8
$legalReport | Export-Csv (Join-Path $releaseOut "04_legal_report.csv") -NoTypeInformation -Encoding utf8
$pilotReport | Export-Csv (Join-Path $releaseOut "05_pilot_report.csv") -NoTypeInformation -Encoding utf8
$cutoverReport | Export-Csv (Join-Path $releaseOut "06_cutover_report.csv") -NoTypeInformation -Encoding utf8

$blockers = @()
if (-not $runtimeGreen) { $blockers += "Runtime proof not fully green." }
if (-not $paymentClosed) { $blockers += "Payment readiness not closed." }
if (-not $legalClosed) { $blockers += "Legal / DPA readiness not closed." }
if (-not $pilotClosed) { $blockers += "Pilot / LOI readiness not closed." }
if (-not $cutoverClosed) { $blockers += "Cutover / rollback readiness not closed." }

if ($blockers.Count -eq 0) {
    $blockers += "No open blockers."
}

Set-Utf8File -Path (Join-Path $releaseOut "07_open_blockers.txt") -Content ($blockers -join "`r`n")

Set-Utf8File -Path (Join-Path $releaseOut "08_go_no_go_checklist.md") -Content @"
# Go / No-Go Checklist

## Runtime
- [ ] django check green
- [ ] deploy check green
- [ ] health endpoint green
- [ ] integrity endpoint green

## Business / Legal
- [ ] payment readiness closed
- [ ] legal / DPA readiness closed
- [ ] pilot / LOI readiness closed

## Release Controls
- [ ] cutover rehearsal closed
- [ ] rollback rehearsal closed
- [ ] final go/no-go recorded

## Decision
- Status:
- Date:
- Release owner:
- Verification owner:
- Final approver:
- Notes:
"@

Set-Utf8File -Path (Join-Path $releaseOut "09_release_decision.md") -Content @"
# Release Decision

## Overall release ready
$overallReleaseReady

## Gate summary
- Runtime green: $runtimeGreen
- Payment closed: $paymentClosed
- Legal closed: $legalClosed
- Pilot closed: $pilotClosed
- Cutover closed: $cutoverClosed

## Decision
- Status:
- Date:
- Approver:
- Notes:
"@

Set-Utf8File -Path (Join-Path $releaseOut "10_release_packet_manifest.md") -Content @"
# Release Packet Manifest

## Runtime latest
$runtimeLatest

## Payment latest
$paymentLatest

## Legal latest
$legalLatest

## Pilot latest
$pilotLatest

## Cutover latest
$cutoverLatest

## Board
$boardPath
"@

if (Test-Path $boardPath) {
    Copy-Item $boardPath (Join-Path $releaseOut "11_priority_board_snapshot.csv") -Force
}

if (-not (Test-Path $releaseLatest)) {
    New-Item -ItemType Directory -Force -Path $releaseLatest | Out-Null
}
Get-ChildItem $releaseOut -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $releaseLatest $_.Name) -Force
}

$summary = @()
$summary += "# Release Master Gate Summary"
$summary += ""
$summary += "- Output root: $releaseOut"
$summary += "- Overall release ready: $overallReleaseReady"
$summary += ""
$summary += "## Gate results"
foreach ($row in $gateMatrix) {
    $summary += "- $($row.Gate): $($row.Status)"
}
$summary += ""
$summary += "## Open blockers"
foreach ($b in $blockers) {
    $summary += "- $b"
}
$summary += ""
$summary += "## Next action"
$summary += "- If any gate is FAIL, close that item and rerun this script."
$summary += "- If all gates are PASS, complete 08_go_no_go_checklist.md and 09_release_decision.md."

Set-Utf8File -Path (Join-Path $releaseOut "SUMMARY.md") -Content ($summary -join "`r`n")

if (-not (Test-Path $releaseLatest)) {
    New-Item -ItemType Directory -Force -Path $releaseLatest | Out-Null
}
Copy-Item (Join-Path $releaseOut "SUMMARY.md") (Join-Path $releaseLatest "SUMMARY.md") -Force

if ($OpenFiles) {
    Open-IfExists (Join-Path $releaseLatest "SUMMARY.md")
    Open-IfExists (Join-Path $releaseLatest "01_gate_matrix.csv")
    Open-IfExists (Join-Path $releaseLatest "07_open_blockers.txt")
    Open-IfExists (Join-Path $releaseLatest "08_go_no_go_checklist.md")
    Open-IfExists (Join-Path $releaseLatest "09_release_decision.md")
    Open-IfExists (Join-Path $releaseLatest "11_priority_board_snapshot.csv")
    Open-IfExists $boardPath
}

Write-Host "Done: $releaseOut"
Write-Host "Latest: $releaseLatest"
Write-Host "Overall release ready: $overallReleaseReady"
