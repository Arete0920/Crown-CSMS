param(
    [string]$RegisterFile = "docs/release/DUPLICATE_TRUTH_REGISTER_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $RegisterFile)) {
    Write-Error "duplicate truth register file not found: $RegisterFile"
    exit 1
}

$text = Get-Content -Raw -Path $RegisterFile

$requiredOverlapIds = @(
    "OVL-001",
    "OVL-002",
    "OVL-003",
    "OVL-004",
    "OVL-005",
    "OVL-006"
)

$requiredCanonicalOwners = @(
    "households.Student",
    "households.Guardian",
    "households.Household",
    "academics.Enrollment",
    "finance.FinancePayment",
    "academics.Assignment"
)

$missingIds = @()
foreach ($id in $requiredOverlapIds) {
    if ($text -notmatch [regex]::Escape($id)) {
        $missingIds += $id
    }
}

$missingOwners = @()
foreach ($owner in $requiredCanonicalOwners) {
    if ($text -notmatch [regex]::Escape($owner)) {
        $missingOwners += $owner
    }
}

$controlledCount = ([regex]::Matches($text, "status:\s*controlled", "IgnoreCase")).Count

Write-Output "[duplicate-truth-overlap] missing_ids=$($missingIds.Count) missing_owners=$($missingOwners.Count) controlled_rows=$controlledCount"

foreach ($id in $missingIds) {
    Write-Output "OVERLAP_ID_MISSING $id"
}
foreach ($owner in $missingOwners) {
    Write-Output "CANONICAL_OWNER_MISSING $owner"
}

if ($controlledCount -lt $requiredOverlapIds.Count) {
    Write-Output "CONTROLLED_ROWS_INSUFFICIENT expected=$($requiredOverlapIds.Count) actual=$controlledCount"
    Write-Error "duplicate truth overlap check failed"
    exit 1
}

if ($missingIds.Count -gt 0 -or $missingOwners.Count -gt 0) {
    Write-Error "duplicate truth overlap check failed"
    exit 1
}

Write-Output "OK duplicate truth overlap check passed"
exit 0
