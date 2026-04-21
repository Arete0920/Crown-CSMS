param(
    [switch]$OpenFiles,
    [switch]$ValidateOnly
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

function Copy-SourceOrWrite {
    param(
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$FallbackContent
    )
    if ($SourcePath -and (Test-Path $SourcePath)) {
        Copy-Item $SourcePath $TargetPath -Force
    }
    else {
        Set-Utf8File -Path $TargetPath -Content $FallbackContent
    }
}

function Update-BoardStatus {
    param(
        [string]$BoardPath,
        [string]$Priority,
        [string]$Status,
        [string]$Notes
    )
    if (-not (Test-Path $BoardPath)) { return }
    $rows = Import-Csv $BoardPath
    foreach ($row in $rows) {
        if ($row.Priority -eq $Priority) {
            $row.Status = $Status
            $row.Notes = $Notes
        }
    }
    $rows | Export-Csv $BoardPath -NoTypeInformation -Encoding utf8
}

function Mirror-Latest {
    param(
        [string]$SourceDir,
        [string]$LatestDir
    )
    if (Test-Path $LatestDir) {
        Remove-Item $LatestDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $LatestDir | Out-Null
    Copy-Item (Join-Path $SourceDir "*") $LatestDir -Recurse -Force
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

function Open-FileSet {
    param([string[]]$Paths)
    foreach ($path in $Paths) {
        if (Test-Path $path) {
            code $path
        }
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$board = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
$closeoutRoot = Join-Path $repoRoot "audit-artifacts\post-merge-closeout"
$latestCloseout = Get-ChildItem $closeoutRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1

# ----------------------------
# ITEM 8 - LEGAL / DPA
# ----------------------------
$legalBase = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness"
$legalOut = Join-Path $legalBase $ts
$legalLatest = Join-Path $legalBase "latest"

if (-not $ValidateOnly) {
    New-Item -ItemType Directory -Force -Path $legalOut | Out-Null

    $legalSource = $null
    if ($latestCloseout) {
        $candidate = Join-Path $latestCloseout.FullName "04_launch_trackers\02_legal_dpa_readiness.md"
        if (Test-Path $candidate) { $legalSource = $candidate }
    }

    Copy-SourceOrWrite -SourcePath $legalSource -TargetPath (Join-Path $legalOut "01_legal_dpa_readiness_WORKING.md") -FallbackContent @"
# Legal / DPA Readiness

## Owner
- Primary:
- Secondary:

## Status
- Current status:
- Target date:

## Required evidence
- [ ] DPA template finalized
- [ ] Legal review completed
- [ ] School-facing version approved
- [ ] Signature workflow defined
- [ ] Data handling responsibilities confirmed
- [ ] Retention / deletion language confirmed

## Notes
-
"@

    Set-Utf8File -Path (Join-Path $legalOut "02_legal_owner_assignment.md") -Content @"
# Legal Owner Assignment

## Primary owner
- Name:
- Role:
- Email:

## Secondary owner
- Name:
- Role:
- Email:

## Legal reviewer
- Name:
- Role:
- Email:

## Final approver
- Name:
- Role:
- Email:

## Target close date
- Date:

## Notes
-
"@

    Set-Utf8File -Path (Join-Path $legalOut "03_dpa_clause_review_matrix.md") -Content @"
# DPA Clause Review Matrix

| Clause Area | Current Status | Owner | Needs Revision | Notes |
|---|---|---|---|---|
| Parties / Definitions | Open |  |  |  |
| Data Processing Scope | Open |  |  |  |
| Security Measures | Open |  |  |  |
| Subprocessors | Open |  |  |  |
| Breach Notification | Open |  |  |  |
| Data Subject Rights | Open |  |  |  |
| Retention / Deletion | Open |  |  |  |
| International Transfer | Open |  |  |  |
| Audit / Assistance | Open |  |  |  |
| Governing Law / Venue | Open |  |  |  |
"@

    Set-Utf8File -Path (Join-Path $legalOut "04_signature_workflow.md") -Content @"
# Signature Workflow

## Documents
- DPA:
- Related exhibits:
- School-facing packet:

## Steps
1. Draft prepared by:
2. Internal legal review by:
3. Product / business review by:
4. Final approver:
5. Signature owner:
6. Storage location for executed copies:

## Turnaround target
- Target business days:

## Notes
-
"@

    Set-Utf8File -Path (Join-Path $legalOut "05_data_handling_responsibilities.md") -Content @"
# Data Handling Responsibilities

| Area | Crown Owner | School Owner | Status | Notes |
|---|---|---|---|---|
| Data intake |  |  | Open |  |
| Access control |  |  | Open |  |
| Incident response |  |  | Open |  |
| Retention |  |  | Open |  |
| Deletion |  |  | Open |  |
| Backup / restore |  |  | Open |  |
| Third-party processors |  |  | Open |  |
| Support access |  |  | Open |  |
"@

    Set-Utf8File -Path (Join-Path $legalOut "06_school_facing_packet_checklist.md") -Content @"
# School-Facing Legal Packet Checklist

- [ ] DPA main document finalized
- [ ] Clause review complete
- [ ] Signature workflow complete
- [ ] Data handling matrix complete
- [ ] School-facing packet assembled
- [ ] File storage location assigned
- [ ] Final approver sign-off recorded
"@

    Set-Utf8File -Path (Join-Path $legalOut "07_final_legal_signoff.md") -Content @"
# Final Legal Sign-Off

## Reviewer
- Name:
- Role:

## Checklist
- [ ] DPA reviewed
- [ ] Clause matrix complete
- [ ] Signature flow defined
- [ ] Data handling responsibilities approved
- [ ] School-facing packet ready

## Decision
- Status:
- Date:
- Signature / initials:

## Notes
-
"@

    Set-Utf8File -Path (Join-Path $legalOut "08_required_evidence_checklist.md") -Content @"
# Required Evidence Checklist

- [ ] 01_legal_dpa_readiness_WORKING.md complete
- [ ] 02_legal_owner_assignment.md complete
- [ ] 03_dpa_clause_review_matrix.md complete
- [ ] 04_signature_workflow.md complete
- [ ] 05_data_handling_responsibilities.md complete
- [ ] 06_school_facing_packet_checklist.md complete
- [ ] 07_final_legal_signoff.md complete
- [ ] priority_board.csv item 8 moved to Closed
"@

    Set-Utf8File -Path (Join-Path $legalOut "SUMMARY.md") -Content @"
# Legal / DPA Readiness Summary

## Output root
$legalOut

## Exit condition
- all legal evidence files completed
- school-facing packet ready
- final legal sign-off complete
- priority_board.csv item 8 = Closed
"@

    Update-BoardStatus -BoardPath $board -Priority "8" -Status "In Progress" -Notes ("Legal / DPA working folder: " + $legalOut)
    Mirror-Latest -SourceDir $legalOut -LatestDir $legalLatest
}

$legalRequired = @(
    "01_legal_dpa_readiness_WORKING.md",
    "02_legal_owner_assignment.md",
    "03_dpa_clause_review_matrix.md",
    "04_signature_workflow.md",
    "05_data_handling_responsibilities.md",
    "06_school_facing_packet_checklist.md",
    "07_final_legal_signoff.md",
    "08_required_evidence_checklist.md"
)
$legalReport = Validate-FileSet -Root $legalLatest -RequiredFiles $legalRequired
$legalSignoffReady = $false
$legalSignoffPath = Join-Path $legalLatest "07_final_legal_signoff.md"
if (Test-Path $legalSignoffPath) {
    $content = Get-Content $legalSignoffPath -Raw
    if (($content -match "School-facing packet ready" -and $content -notmatch "\[ \] School-facing packet ready") -or ($content -match "Status:" -and $content -notmatch "Status:\s*$")) {
        $legalSignoffReady = $true
    }
}
$legalValidation = Join-Path $legalLatest "09_legal_closeout_validation.txt"
"=== LEGAL / DPA CLOSEOUT VALIDATION ===" | Set-Content $legalValidation -Encoding utf8
$legalReport | Format-Table File, Exists, Size, NonEmpty -AutoSize | Out-String | Add-Content $legalValidation
"" | Add-Content $legalValidation
("Final legal signoff ready: " + $legalSignoffReady) | Add-Content $legalValidation
$legalAllReady = ($legalReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$legalCanClose = $legalAllReady -and $legalSignoffReady
("Can close item 8: " + $legalCanClose) | Add-Content $legalValidation
if ($legalCanClose) {
    Update-BoardStatus -BoardPath $board -Priority "8" -Status "Closed" -Notes "Closed via legal-dpa latest validation"
    $checklist = Join-Path $legalLatest "08_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $c = Get-Content $checklist -Raw
        $c = $c -replace "- \[ \]", "- [x]"
        Set-Content $checklist $c -Encoding utf8
    }
}

# ----------------------------
# ITEM 9 - PILOT / LOI
# ----------------------------
$pilotBase = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness"
$pilotOut = Join-Path $pilotBase $ts
$pilotLatest = Join-Path $pilotBase "latest"

if (-not $ValidateOnly) {
    New-Item -ItemType Directory -Force -Path $pilotOut | Out-Null

    $trackerMd = $null
    $trackerCsv = $null
    if ($latestCloseout) {
        $candidateMd = Join-Path $latestCloseout.FullName "04_launch_trackers\03_pilot_loi_tracker.md"
        $candidateCsv = Join-Path $latestCloseout.FullName "04_launch_trackers\05_pilot_loi_tracker.csv"
        if (Test-Path $candidateMd) { $trackerMd = $candidateMd }
        if (Test-Path $candidateCsv) { $trackerCsv = $candidateCsv }
    }

    Copy-SourceOrWrite -SourcePath $trackerMd -TargetPath (Join-Path $pilotOut "01_pilot_loi_tracker_WORKING.md") -FallbackContent @"
# Pilot / LOI Tracker

| School | Contact | Stage | LOI | Pilot Start | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
"@

    Copy-SourceOrWrite -SourcePath $trackerCsv -TargetPath (Join-Path $pilotOut "02_pilot_loi_tracker_WORKING.csv") -FallbackContent @"
School,Contact,Stage,LOI,PilotStart,Notes
"@

    Set-Utf8File -Path (Join-Path $pilotOut "03_pipeline_owner_assignment.md") -Content @"
# Pipeline Owner Assignment

## Primary owner
- Name:
- Role:
- Email:

## Secondary owner
- Name:
- Role:
- Email:

## Target schools this sprint
- 1.
- 2.
- 3.

## Weekly target
- Signed LOIs target:
- Pilot starts target:

## Notes
-
"@

    Set-Utf8File -Path (Join-Path $pilotOut "04_outreach_conversion_checklist.md") -Content @"
# Outreach / Conversion Checklist

- [ ] target schools selected
- [ ] contact list confirmed
- [ ] outreach messages prepared
- [ ] follow-up schedule defined
- [ ] LOI template ready
- [ ] pilot start windows proposed
- [ ] next actions logged for each target
"@

    Set-Utf8File -Path (Join-Path $pilotOut "05_required_evidence_checklist.md") -Content @"
# LOI / Pilot Evidence Checklist

- [ ] 01_pilot_loi_tracker_WORKING.md complete
- [ ] 02_pilot_loi_tracker_WORKING.csv complete
- [ ] 03_pipeline_owner_assignment.md complete
- [ ] 04_outreach_conversion_checklist.md complete
- [ ] at least one signed LOI recorded
- [ ] at least one pilot start date recorded
- [ ] priority_board.csv item 9 moved to Closed
"@

    Set-Utf8File -Path (Join-Path $pilotOut "SUMMARY.md") -Content @"
# Pilot / LOI Summary

## Output root
$pilotOut

## Exit condition
- at least one signed LOI recorded
- at least one pilot start date recorded
- priority_board.csv item 9 = Closed
"@

    Update-BoardStatus -BoardPath $board -Priority "9" -Status "In Progress" -Notes ("Pilot / LOI working folder: " + $pilotOut)
    Mirror-Latest -SourceDir $pilotOut -LatestDir $pilotLatest
}

$pilotRequired = @(
    "01_pilot_loi_tracker_WORKING.md",
    "02_pilot_loi_tracker_WORKING.csv",
    "03_pipeline_owner_assignment.md",
    "04_outreach_conversion_checklist.md",
    "05_required_evidence_checklist.md"
)
$pilotReport = Validate-FileSet -Root $pilotLatest -RequiredFiles $pilotRequired
$pilotCsv = Join-Path $pilotLatest "02_pilot_loi_tracker_WORKING.csv"
$loiCount = 0
$pilotCount = 0
if (Test-Path $pilotCsv) {
    try {
        $rows = Import-Csv $pilotCsv
        $loiCount = @($rows | Where-Object { $_.LOI -and $_.LOI.Trim() -ne "" -and $_.LOI -notin @("No", "Open", "Pending") }).Count
        $pilotCount = @($rows | Where-Object { $_.PilotStart -and $_.PilotStart.Trim() -ne "" }).Count
    }
    catch {
        $loiCount = 0
        $pilotCount = 0
    }
}
$pilotValidation = Join-Path $pilotLatest "06_pilot_loi_closeout_validation.txt"
"=== PILOT / LOI CLOSEOUT VALIDATION ===" | Set-Content $pilotValidation -Encoding utf8
$pilotReport | Format-Table File, Exists, Size, NonEmpty -AutoSize | Out-String | Add-Content $pilotValidation
"" | Add-Content $pilotValidation
("Signed LOI rows: " + $loiCount) | Add-Content $pilotValidation
("Pilot start rows: " + $pilotCount) | Add-Content $pilotValidation
$pilotAllReady = ($pilotReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$pilotCanClose = $pilotAllReady -and ($loiCount -ge 1) -and ($pilotCount -ge 1)
("Can close item 9: " + $pilotCanClose) | Add-Content $pilotValidation
if ($pilotCanClose) {
    Update-BoardStatus -BoardPath $board -Priority "9" -Status "Closed" -Notes "Closed via pilot-loi latest validation"
    $checklist = Join-Path $pilotLatest "05_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $c = Get-Content $checklist -Raw
        $c = $c -replace "- \[ \]", "- [x]"
        Set-Content $checklist $c -Encoding utf8
    }
}

# ----------------------------
# ITEM 10 - CUTOVER / ROLLBACK
# ----------------------------
$cutBase = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness"
$cutOut = Join-Path $cutBase $ts
$cutLatest = Join-Path $cutBase "latest"

if (-not $ValidateOnly) {
    New-Item -ItemType Directory -Force -Path $cutOut | Out-Null

    $warRoomChecklist = Join-Path $repoRoot "audit-artifacts\release-war-room\cutover_rollback_checklist.md"
    Copy-SourceOrWrite -SourcePath $warRoomChecklist -TargetPath (Join-Path $cutOut "01_cutover_rollback_checklist_WORKING.md") -FallbackContent @"
# Cutover and Rollback Checklist

## Owners
- Release:
- Rollback:
- Verification:
- Final sign-off:

## Cutover
- [ ] deployment command documented
- [ ] env vars verified
- [ ] database backup verified
- [ ] migration plan verified
- [ ] smoke test list ready

## Rollback
- [ ] rollback command documented
- [ ] prior artifact available
- [ ] database rollback path documented
- [ ] verification steps documented

## Final proof
- [ ] cutover rehearsal completed
- [ ] rollback rehearsal completed
- [ ] timestamps captured
- [ ] go/no-go signed
"@

    Set-Utf8File -Path (Join-Path $cutOut "02_release_owner_assignment.md") -Content @"
# Release Owner Assignment

## Release owner
- Name:
- Role:
- Email:

## Rollback owner
- Name:
- Role:
- Email:

## Verification owner
- Name:
- Role:
- Email:

## Final approver
- Name:
- Role:
- Email:
"@

    Set-Utf8File -Path (Join-Path $cutOut "03_rehearsal_log.md") -Content @"
# Rehearsal Log

| Timestamp | Step | Owner | Status | Notes |
|---|---|---|---|---|
|  | Cutover rehearsal |  |  |  |
|  | Rollback rehearsal |  |  |  |
|  | Final go/no-go |  |  |  |
"@

    Set-Utf8File -Path (Join-Path $cutOut "04_required_evidence_checklist.md") -Content @"
# Required Evidence Checklist

- [ ] 01_cutover_rollback_checklist_WORKING.md complete
- [ ] 02_release_owner_assignment.md complete
- [ ] 03_rehearsal_log.md complete
- [ ] cutover rehearsal marked complete
- [ ] rollback rehearsal marked complete
- [ ] go/no-go signed
- [ ] priority_board.csv item 10 moved to Closed
"@

    Set-Utf8File -Path (Join-Path $cutOut "SUMMARY.md") -Content @"
# Cutover / Rollback Summary

## Output root
$cutOut

## Exit condition
- cutover rehearsal complete
- rollback rehearsal complete
- go/no-go signed
- priority_board.csv item 10 = Closed
"@

    Update-BoardStatus -BoardPath $board -Priority "10" -Status "In Progress" -Notes ("Cutover / rollback working folder: " + $cutOut)
    Mirror-Latest -SourceDir $cutOut -LatestDir $cutLatest
}

$cutRequired = @(
    "01_cutover_rollback_checklist_WORKING.md",
    "02_release_owner_assignment.md",
    "03_rehearsal_log.md",
    "04_required_evidence_checklist.md"
)
$cutReport = Validate-FileSet -Root $cutLatest -RequiredFiles $cutRequired
$cutChecklistPath = Join-Path $cutLatest "01_cutover_rollback_checklist_WORKING.md"
$cutoverReady = $false
$rollbackReady = $false
$goNoGoReady = $false
if (Test-Path $cutChecklistPath) {
    $content = Get-Content $cutChecklistPath -Raw
    if ($content -notmatch "\[ \] cutover rehearsal completed") { $cutoverReady = $true }
    if ($content -notmatch "\[ \] rollback rehearsal completed") { $rollbackReady = $true }
    if ($content -notmatch "\[ \] go/no-go signed") { $goNoGoReady = $true }
}
$cutValidation = Join-Path $cutLatest "05_cutover_closeout_validation.txt"
"=== CUTOVER / ROLLBACK CLOSEOUT VALIDATION ===" | Set-Content $cutValidation -Encoding utf8
$cutReport | Format-Table File, Exists, Size, NonEmpty -AutoSize | Out-String | Add-Content $cutValidation
"" | Add-Content $cutValidation
("Cutover rehearsal complete: " + $cutoverReady) | Add-Content $cutValidation
("Rollback rehearsal complete: " + $rollbackReady) | Add-Content $cutValidation
("Go/no-go signed: " + $goNoGoReady) | Add-Content $cutValidation
$cutAllReady = ($cutReport | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$cutCanClose = $cutAllReady -and $cutoverReady -and $rollbackReady -and $goNoGoReady
("Can close item 10: " + $cutCanClose) | Add-Content $cutValidation
if ($cutCanClose) {
    Update-BoardStatus -BoardPath $board -Priority "10" -Status "Closed" -Notes "Closed via cutover-rollback latest validation"
    $checklist = Join-Path $cutLatest "04_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $c = Get-Content $checklist -Raw
        $c = $c -replace "- \[ \]", "- [x]"
        Set-Content $checklist $c -Encoding utf8
    }
}

# ----------------------------
# OPEN FILES IF REQUESTED
# ----------------------------
if ($OpenFiles) {
    Open-FileSet @(
        (Join-Path $legalLatest "SUMMARY.md"),
        (Join-Path $legalLatest "01_legal_dpa_readiness_WORKING.md"),
        (Join-Path $legalLatest "02_legal_owner_assignment.md"),
        (Join-Path $legalLatest "03_dpa_clause_review_matrix.md"),
        (Join-Path $legalLatest "04_signature_workflow.md"),
        (Join-Path $legalLatest "05_data_handling_responsibilities.md"),
        (Join-Path $legalLatest "06_school_facing_packet_checklist.md"),
        (Join-Path $legalLatest "07_final_legal_signoff.md"),
        (Join-Path $legalLatest "08_required_evidence_checklist.md"),
        (Join-Path $legalLatest "09_legal_closeout_validation.txt"),

        (Join-Path $pilotLatest "SUMMARY.md"),
        (Join-Path $pilotLatest "01_pilot_loi_tracker_WORKING.md"),
        (Join-Path $pilotLatest "02_pilot_loi_tracker_WORKING.csv"),
        (Join-Path $pilotLatest "03_pipeline_owner_assignment.md"),
        (Join-Path $pilotLatest "04_outreach_conversion_checklist.md"),
        (Join-Path $pilotLatest "05_required_evidence_checklist.md"),
        (Join-Path $pilotLatest "06_pilot_loi_closeout_validation.txt"),

        (Join-Path $cutLatest "SUMMARY.md"),
        (Join-Path $cutLatest "01_cutover_rollback_checklist_WORKING.md"),
        (Join-Path $cutLatest "02_release_owner_assignment.md"),
        (Join-Path $cutLatest "03_rehearsal_log.md"),
        (Join-Path $cutLatest "04_required_evidence_checklist.md"),
        (Join-Path $cutLatest "05_cutover_closeout_validation.txt"),

        $board
    )
}

Write-Host "LEGAL latest: $legalLatest"
Write-Host "PILOT latest: $pilotLatest"
Write-Host "CUTOVER latest: $cutLatest"
Write-Host "BOARD: $board"
Write-Host "Validation complete."
