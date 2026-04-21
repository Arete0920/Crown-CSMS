$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\pilot-loi-readiness\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$closeoutRoot = Join-Path $repoRoot "audit-artifacts\post-merge-closeout"
$latestCloseout = Get-ChildItem $closeoutRoot -Directory -ErrorAction SilentlyContinue |
Sort-Object Name -Descending |
Select-Object -First 1

$trackerMd = $null
$trackerCsv = $null
if ($latestCloseout) {
    $candidateMd = Join-Path $latestCloseout.FullName "04_launch_trackers\03_pilot_loi_tracker.md"
    $candidateCsv = Join-Path $latestCloseout.FullName "04_launch_trackers\05_pilot_loi_tracker.csv"
    if (Test-Path $candidateMd) { $trackerMd = $candidateMd }
    if (Test-Path $candidateCsv) { $trackerCsv = $candidateCsv }
}

if ($trackerMd) {
    Copy-Item $trackerMd (Join-Path $out "01_pilot_loi_tracker_WORKING.md") -Force
}
else {
    @"
# Pilot / LOI Tracker

| School | Contact | Stage | LOI | Pilot Start | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
"@ | Set-Content (Join-Path $out "01_pilot_loi_tracker_WORKING.md") -Encoding utf8
}

if ($trackerCsv) {
    Copy-Item $trackerCsv (Join-Path $out "02_pilot_loi_tracker_WORKING.csv") -Force
}
else {
    @"
School,Contact,Stage,LOI,PilotStart,Notes
"@ | Set-Content (Join-Path $out "02_pilot_loi_tracker_WORKING.csv") -Encoding utf8
}

@"
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
"@ | Set-Content (Join-Path $out "03_pipeline_owner_assignment.md") -Encoding utf8

@"
# Outreach / Conversion Checklist

- [ ] target schools selected
- [ ] contact list confirmed
- [ ] outreach messages prepared
- [ ] follow-up schedule defined
- [ ] LOI template ready
- [ ] pilot start windows proposed
- [ ] next actions logged for each target
"@ | Set-Content (Join-Path $out "04_outreach_conversion_checklist.md") -Encoding utf8

@"
# LOI / Pilot Evidence Checklist

- [ ] 01_pilot_loi_tracker_WORKING.md complete
- [ ] 02_pilot_loi_tracker_WORKING.csv complete
- [ ] 03_pipeline_owner_assignment.md complete
- [ ] 04_outreach_conversion_checklist.md complete
- [ ] at least one signed LOI recorded
- [ ] at least one pilot start date recorded
- [ ] priority_board.csv item 9 moved to Closed
"@ | Set-Content (Join-Path $out "05_required_evidence_checklist.md") -Encoding utf8

@"
# Pilot / LOI Summary

## Output root
$out

## Exit condition
- at least one signed LOI recorded
- at least one pilot start date recorded
- priority_board.csv item 9 = Closed
"@ | Set-Content (Join-Path $out "SUMMARY.md") -Encoding utf8

$priorityBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
if (Test-Path $priorityBoard) {
    $rows = Import-Csv $priorityBoard
    foreach ($row in $rows) {
        if ($row.Priority -eq "9") {
            $row.Status = "In Progress"
            $row.Notes = "Pilot / LOI working folder: " + $out
        }
    }
    $rows | Export-Csv $priorityBoard -NoTypeInformation -Encoding utf8
}

$latestDir = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness\latest"
if (Test-Path $latestDir) { Remove-Item $latestDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
Copy-Item (Join-Path $out "*") $latestDir -Recurse -Force

Write-Host "Done: $out"
