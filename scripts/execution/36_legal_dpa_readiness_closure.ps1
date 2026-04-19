$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\legal-dpa-readiness\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$closeoutRoot = Join-Path $repoRoot "audit-artifacts\post-merge-closeout"
$latestCloseout = Get-ChildItem $closeoutRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1

$legalSource = $null
if ($latestCloseout) {
    $candidate = Join-Path $latestCloseout.FullName "04_launch_trackers\02_legal_dpa_readiness.md"
    if (Test-Path $candidate) {
        $legalSource = $candidate
    }
}

if ($legalSource) {
    Copy-Item $legalSource (Join-Path $out "01_legal_dpa_readiness_WORKING.md") -Force
} else {
@"
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
"@ | Set-Content (Join-Path $out "01_legal_dpa_readiness_WORKING.md") -Encoding utf8
}

@"
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
"@ | Set-Content (Join-Path $out "02_legal_owner_assignment.md") -Encoding utf8

@"
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
"@ | Set-Content (Join-Path $out "03_dpa_clause_review_matrix.md") -Encoding utf8

@"
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
"@ | Set-Content (Join-Path $out "04_signature_workflow.md") -Encoding utf8

@"
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
"@ | Set-Content (Join-Path $out "05_data_handling_responsibilities.md") -Encoding utf8

@"
# School-Facing Legal Packet Checklist

- [ ] DPA main document finalized
- [ ] Clause review complete
- [ ] Signature workflow complete
- [ ] Data handling matrix complete
- [ ] School-facing packet assembled
- [ ] File storage location assigned
- [ ] Final approver sign-off recorded
"@ | Set-Content (Join-Path $out "06_school_facing_packet_checklist.md") -Encoding utf8

@"
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
"@ | Set-Content (Join-Path $out "07_final_legal_signoff.md") -Encoding utf8

@"
# Required Evidence Checklist

- [ ] 01_legal_dpa_readiness_WORKING.md complete
- [ ] 02_legal_owner_assignment.md complete
- [ ] 03_dpa_clause_review_matrix.md complete
- [ ] 04_signature_workflow.md complete
- [ ] 05_data_handling_responsibilities.md complete
- [ ] 06_school_facing_packet_checklist.md complete
- [ ] 07_final_legal_signoff.md complete
- [ ] priority_board.csv item 8 moved to Closed
"@ | Set-Content (Join-Path $out "08_required_evidence_checklist.md") -Encoding utf8

@"
code `"$out\01_legal_dpa_readiness_WORKING.md`"
code `"$out\02_legal_owner_assignment.md`"
code `"$out\03_dpa_clause_review_matrix.md`"
code `"$out\04_signature_workflow.md`"
code `"$out\05_data_handling_responsibilities.md`"
code `"$out\06_school_facing_packet_checklist.md`"
code `"$out\07_final_legal_signoff.md`"
code `"$out\08_required_evidence_checklist.md`"
code `"$repoRoot\audit-artifacts\release-war-room\priority_board.csv`"
"@ | Set-Content (Join-Path $out "09_open_files.ps1") -Encoding utf8

$priorityBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
if (Test-Path $priorityBoard) {
    $rows = Import-Csv $priorityBoard
    foreach ($row in $rows) {
        if ($row.Priority -eq "8") {
            $row.Status = "In Progress"
            $row.Notes = "Legal / DPA working folder: " + $out
        }
    }
    $rows | Export-Csv $priorityBoard -NoTypeInformation -Encoding utf8
}

$latestDir = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness\latest"
if (Test-Path $latestDir) {
    Remove-Item $latestDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
Copy-Item (Join-Path $out "*") $latestDir -Recurse -Force

@"
# Legal / DPA Readiness Summary

## Output root
$out

## Review files
- 01_legal_dpa_readiness_WORKING.md
- 02_legal_owner_assignment.md
- 03_dpa_clause_review_matrix.md
- 04_signature_workflow.md
- 05_data_handling_responsibilities.md
- 06_school_facing_packet_checklist.md
- 07_final_legal_signoff.md
- 08_required_evidence_checklist.md

## Exit condition
- all legal evidence files completed
- school-facing packet ready
- final legal sign-off complete
- priority_board.csv item 8 = Closed
"@ | Set-Content (Join-Path $out "SUMMARY.md") -Encoding utf8

Write-Host "Done: $out"
