param(
    [string]$StudentMap = "docs/release/CANONICAL_OWNERSHIP_MAP_STUDENT_HOUSEHOLD_GUARDIAN_ENROLLMENT_20260530.md",
    [string]$FinanceMap = "docs/release/CANONICAL_OWNERSHIP_MAP_INVOICE_PAYMENT_LEDGER_20260530.md",
    [string]$GradesMap = "docs/release/CANONICAL_OWNERSHIP_MAP_ASSIGNMENT_GRADE_ENTRY_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$checks = @(
    @{ File = $StudentMap; Tokens = @("households.Household", "households.Guardian", "households.Student", "academics.Enrollment", "core.Enrollment") },
    @{ File = $FinanceMap; Tokens = @("finance.FinanceInvoice", "finance.FinancePayment", "finance.FinanceAllocation", "core.LedgerEntry", "payments.PaymentIntentRecord") },
    @{ File = $GradesMap; Tokens = @("academics.Assignment", "academics.AssignmentCategory", "gradebook.GradeEntry", "assignment_name") }
)

$totalMissing = 0

foreach ($check in $checks) {
    if (-not (Test-Path -Path $check.File)) {
        Write-Output "MAP_FILE_MISSING $($check.File)"
        $totalMissing += 1
        continue
    }

    $text = Get-Content -Raw -Path $check.File
    $missingTokens = @()
    foreach ($token in $check.Tokens) {
        if ($text -notmatch [regex]::Escape($token)) {
            $missingTokens += $token
        }
    }

    Write-Output "[canonical-map-check] file=$($check.File) missing_tokens=$($missingTokens.Count)"
    foreach ($token in $missingTokens) {
        Write-Output "TOKEN_MISSING $token"
    }

    $totalMissing += $missingTokens.Count
}

if ($totalMissing -gt 0) {
    Write-Error "canonical data ownership map check failed"
    exit 1
}

Write-Output "OK canonical data ownership maps check passed"
exit 0
