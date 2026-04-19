$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\payment-readiness\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$closeoutRoot = Join-Path $repoRoot "audit-artifacts\post-merge-closeout"
$latestCloseout = Get-ChildItem $closeoutRoot -Directory -ErrorAction SilentlyContinue |
Sort-Object Name -Descending |
Select-Object -First 1

$paymentChecklistSource = $null
if ($latestCloseout) {
    $candidate = Join-Path $latestCloseout.FullName "04_launch_trackers\01_payment_validation_checklist.md"
    if (Test-Path $candidate) {
        $paymentChecklistSource = $candidate
    }
}

if ($paymentChecklistSource) {
    Copy-Item $paymentChecklistSource (Join-Path $out "01_payment_validation_checklist_WORKING.md") -Force
}
else {
    @"
# Payment Validation Checklist

## Owner
- Primary:
- Secondary:

## Status
- Current status:
- Target date:

## Required evidence
- [ ] Executed payment agreement on file
- [ ] Sandbox credentials verified
- [ ] Live test transaction completed
- [ ] Reconciliation proof captured
- [ ] Refund / reversal path verified
- [ ] Finance sign-off recorded

## Notes
-
"@ | Set-Content (Join-Path $out "01_payment_validation_checklist_WORKING.md") -Encoding utf8
}

@"
# Payment Owner Assignment

## Primary owner
- Name:
- Role:
- Email:

## Secondary owner
- Name:
- Role:
- Email:

## Finance sign-off owner
- Name:
- Role:
- Email:

## Gateway contact
- Name:
- Company:
- Email:
- Phone:

## Target close date
- Date:

## Notes
-
"@ | Set-Content (Join-Path $out "02_payment_owner_assignment.md") -Encoding utf8

@"
# Gateway Access Check

## Environment
- Sandbox:
- Production:

## Credentials
- [ ] API credentials verified
- [ ] Portal login verified
- [ ] Webhook or callback endpoint documented
- [ ] Settlement account documented
- [ ] Support contact verified

## Transaction path
- [ ] Charge path documented
- [ ] Reconciliation path documented
- [ ] Refund / reversal path documented

## Notes
-
"@ | Set-Content (Join-Path $out "03_gateway_access_check.md") -Encoding utf8

@"
Timestamp,Environment,TransactionType,Amount,Reference,Status,ProcessorResponse,VerifiedBy,Notes
"@ | Set-Content (Join-Path $out "04_test_transaction_log.csv") -Encoding utf8

@"
# Reconciliation Proof

## Test transaction
- Date:
- Reference:
- Amount:
- Environment:

## Evidence captured
- [ ] Processor confirmation captured
- [ ] Internal record captured
- [ ] Matching ledger/balance entry captured
- [ ] Reconciliation reviewed by finance
- [ ] Refund / reversal proof captured if applicable

## File references
- Screenshot / PDF 1:
- Screenshot / PDF 2:
- Export / CSV:

## Notes
-
"@ | Set-Content (Join-Path $out "05_reconciliation_proof.md") -Encoding utf8

@"
# Finance Sign-Off

## Reviewer
- Name:
- Role:

## Checklist
- [ ] Agreement on file
- [ ] Access verified
- [ ] Test transaction verified
- [ ] Reconciliation verified
- [ ] Refund / reversal path verified
- [ ] Ready for release

## Decision
- Status:
- Date:
- Signature / initials:

## Notes
-
"@ | Set-Content (Join-Path $out "06_finance_signoff.md") -Encoding utf8

@"
# Required Evidence Checklist

- [ ] 01_payment_validation_checklist_WORKING.md complete
- [ ] 02_payment_owner_assignment.md complete
- [ ] 03_gateway_access_check.md complete
- [ ] 04_test_transaction_log.csv contains at least one verified transaction
- [ ] 05_reconciliation_proof.md complete
- [ ] 06_finance_signoff.md complete
- [ ] priority_board.csv item 7 moved to Closed
"@ | Set-Content (Join-Path $out "07_required_evidence_checklist.md") -Encoding utf8

@"
code `"$out\01_payment_validation_checklist_WORKING.md`"
code `"$out\02_payment_owner_assignment.md`"
code `"$out\03_gateway_access_check.md`"
code `"$out\04_test_transaction_log.csv`"
code `"$out\05_reconciliation_proof.md`"
code `"$out\06_finance_signoff.md`"
code `"$out\07_required_evidence_checklist.md`"
code `"$repoRoot\audit-artifacts\release-war-room\priority_board.csv`"
"@ | Set-Content (Join-Path $out "08_open_files.ps1") -Encoding utf8

$priorityBoard = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"
if (Test-Path $priorityBoard) {
    $rows = Import-Csv $priorityBoard
    foreach ($row in $rows) {
        if ($row.Priority -eq "7") {
            $row.Status = "In Progress"
            $row.Notes = "Payment readiness working folder: " + $out
        }
    }
    $rows | Export-Csv $priorityBoard -NoTypeInformation -Encoding utf8
}

$latestDir = Join-Path $repoRoot "audit-artifacts\payment-readiness\latest"
if (Test-Path $latestDir) {
    Remove-Item $latestDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
Copy-Item (Join-Path $out "*") $latestDir -Recurse -Force

@"
# Payment Readiness Summary

## Output root
$out

## Review files
- 01_payment_validation_checklist_WORKING.md
- 02_payment_owner_assignment.md
- 03_gateway_access_check.md
- 04_test_transaction_log.csv
- 05_reconciliation_proof.md
- 06_finance_signoff.md
- 07_required_evidence_checklist.md

## Exit condition
- all payment evidence files completed
- one verified transaction logged
- reconciliation proof complete
- finance sign-off complete
- priority_board.csv item 7 = Closed
"@ | Set-Content (Join-Path $out "SUMMARY.md") -Encoding utf8

Write-Host "Done: $out"
