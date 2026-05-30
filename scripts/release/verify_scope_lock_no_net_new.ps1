param(
    [string]$ScopeLockDoc = "docs/release/PRODUCTION_RELEASE_SCOPE_LOCK_20260528.md",
    [string]$OwnershipMapA = "docs/release/CANONICAL_OWNERSHIP_MAP_STUDENT_HOUSEHOLD_GUARDIAN_ENROLLMENT_20260530.md",
    [string]$OwnershipMapB = "docs/release/CANONICAL_OWNERSHIP_MAP_INVOICE_PAYMENT_LEDGER_20260530.md",
    [string]$OwnershipMapC = "docs/release/CANONICAL_OWNERSHIP_MAP_ASSIGNMENT_GRADE_ENTRY_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$required = @($ScopeLockDoc, $OwnershipMapA, $OwnershipMapB, $OwnershipMapC)
$missing = @($required | Where-Object { -not (Test-Path -Path $_) })
if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Output "MISSING $_" }
    Write-Error "scope-lock/no-net-new validation failed (missing files)"
    exit 2
}

$scopeText = Get-Content -Raw -Path $ScopeLockDoc
if ($scopeText -notmatch '(?i)scope\s*lock') {
    Write-Error "scope lock document missing explicit scope-lock language"
    exit 3
}

$mapAText = Get-Content -Raw -Path $OwnershipMapA
$mapBText = Get-Content -Raw -Path $OwnershipMapB
$mapCText = Get-Content -Raw -Path $OwnershipMapC

$hits = 0
if ($mapAText -match '(?i)no\s*net-new\s*writes|no\s*new\s*canonical\s*writes') { $hits++ }
if ($mapBText -match '(?i)no\s*net-new\s*writes|no\s*new\s*canonical\s*writes') { $hits++ }
if ($mapCText -match '(?i)no\s*net-new\s*writes|no\s*new\s*canonical\s*writes') { $hits++ }

Write-Output "[scope-lock-no-net-new] ownership_maps_with_no_net_new_language=$hits"
if ($hits -lt 1) {
    Write-Error "no ownership map contains no-net-new write controls"
    exit 4
}

Write-Output "OK scope lock and no-net-new verification passed"
exit 0
