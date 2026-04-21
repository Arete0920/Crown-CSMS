$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\cutover-rollback-readiness\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$warRoom = Join-Path $repoRoot "audit-artifacts\release-war-room\cutover_rollback_checklist.md"
if (Test-Path $warRoom) {
    Copy-Item $warRoom (Join-Path $out "01_cutover_rollback_checklist_WORKING.md") -Force
} else {
@"
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
"@ | Set-Content (Join-Path $out "01_cutover_rollback_checklist_WORKING.md") -Encoding utf8
}

@"
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
"@ | Set-Content (Join-Path $out "02_release_owner_assignment.md") -Encoding utf8

@"
# Rehearsal Log

| Timestamp | Step | Owner | Status | Notes |
|---|---|---|---|---|
|  | Cutover rehearsal |  |  |  |
|  | Rollback rehearsal |  |  |  |
|  | Final go/no-go |  |  |  |
"@ | Set-Content (Join-Path $out "03_rehearsal_log.md") -Encoding utf8

@"
# Required Evidence Checklist

- [ ] 01_cutover_rollback_checklist_WORKING.md complete
- [ ] 02_release_owner_assignment.md complete
- [ ] 03_rehearsal_log.md complete
- [ ] cutover rehearsal marked complete
- [ ] rollback rehearsal marked complete
- [ ] go/no-go signed
- [ ] priority_board.csv item 10 moved to Closed
"@ | Set-Content (Join-Path $out "04_required_evidence_checklist.md") -Encoding utf8

@"
# Cutover / Rollback Summary

## Output root
$out

## Exit condition
- cutover rehearsal complete
- rollback rehearsal complete
- go/no-go signed
- priority_board.csv item 10 = Closed
"@ | Set-Content (Join-Path $out "SUMMARY.md") -Encoding utf8

$priorityBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
if (Test-Path $priorityBoard) {
    $rows = Import-Csv $priorityBoard
    foreach ($row in $rows) {
        if ($row.Priority -eq "10") {
            $row.Status = "In Progress"
            $row.Notes = "Cutover / rollback working folder: " + $out
        }
    }
    $rows | Export-Csv $priorityBoard -NoTypeInformation -Encoding utf8
}

$latestDir = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness\latest"
if (Test-Path $latestDir) { Remove-Item $latestDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
Copy-Item (Join-Path $out "*") $latestDir -Recurse -Force

Write-Host "Done: $out"
