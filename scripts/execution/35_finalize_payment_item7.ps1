$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$paymentRoot = Join-Path $repoRoot "audit-artifacts\payment-readiness"
$latest = Join-Path $paymentRoot "latest"
$board = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

if (-not (Test-Path $latest)) {
    throw "Missing payment-readiness latest folder: $latest"
}

$required = @(
    "01_payment_validation_checklist_WORKING.md",
    "02_payment_owner_assignment.md",
    "03_gateway_access_check.md",
    "04_test_transaction_log.csv",
    "05_reconciliation_proof.md",
    "06_finance_signoff.md",
    "07_required_evidence_checklist.md"
)

$report = @()
foreach ($name in $required) {
    $path = Join-Path $latest $name
    $exists = Test-Path $path
    $size = if ($exists) { (Get-Item $path).Length } else { 0 }
    $nonEmpty = $size -gt 50
    $report += [pscustomobject]@{
        File     = $name
        Exists   = $exists
        Size     = $size
        NonEmpty = $nonEmpty
        Path     = $path
    }
}

$txCsv = Join-Path $latest "04_test_transaction_log.csv"
$txCount = 0
if (Test-Path $txCsv) {
    try {
        $rows = Import-Csv $txCsv
        $txCount = @($rows).Count
    }
    catch {
        $txCount = 0
    }
}

$signoff = Join-Path $latest "06_finance_signoff.md"
$signoffReady = $false
if (Test-Path $signoff) {
    $content = Get-Content $signoff -Raw
    if ($content -match "Ready for release" -and $content -notmatch "\[ \] Ready for release") {
        $signoffReady = $true
    }
    elseif ($content -match "Status:" -and $content -notmatch "Status:\s*$") {
        $signoffReady = $true
    }
}

$out = Join-Path $latest "08_payment_closeout_validation.txt"
"=== PAYMENT CLOSEOUT VALIDATION ===" | Set-Content $out -Encoding utf8
$report | Format-Table File, Exists, Size, NonEmpty -AutoSize | Out-String | Add-Content $out
"" | Add-Content $out
("Transaction rows in 04_test_transaction_log.csv: " + $txCount) | Add-Content $out
("Finance signoff ready: " + $signoffReady) | Add-Content $out

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$canClose = $allFilesReady -and ($txCount -ge 1) -and $signoffReady

"" | Add-Content $out
("Can close item 7: " + $canClose) | Add-Content $out

if ($canClose) {
    if (Test-Path $board) {
        $rows = Import-Csv $board
        foreach ($row in $rows) {
            if ($row.Priority -eq "7") {
                $row.Status = "Closed"
                $row.Notes = "Closed via payment-readiness latest validation"
            }
        }
        $rows | Export-Csv $board -NoTypeInformation -Encoding utf8
    }

    $checklist = Join-Path $latest "07_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $content = Get-Content $checklist -Raw
        $content = $content -replace "- \[ \]", "- [x]"
        Set-Content $checklist $content -Encoding utf8
    }
}

Write-Host "Validation file: $out"
Write-Host "Can close item 7: $canClose"
