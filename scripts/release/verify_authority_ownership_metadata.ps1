param(
    [string]$OwnershipFile = "docs/release/RELEASE_AUTHORITY_OWNERSHIP_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $OwnershipFile)) {
    Write-Error "ownership file not found: $OwnershipFile"
    exit 1
}

$text = Get-Content -Raw -Path $OwnershipFile
$requiredArtifacts = @(
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md",
    "docs/release/P0_EXECUTION_BOARD_20260528.md",
    "docs/release/RELEASE_AUTHORITY_PRECEDENCE_TABLE_20260530.md",
    "docs/release/FULL_COMPLETION_EXECUTION_BOARD_20260530.md",
    "scripts/release/verify_authority_decision_sync.ps1",
    "scripts/release/verify_authority_files_on_main.ps1",
    "scripts/release/verify_release_claim_branch_sha.ps1",
    "scripts/release/verify_noncanonical_authority_claims.ps1",
    "scripts/release/verify_canonical_status_metadata.ps1"
)

$missing = @()
foreach ($artifact in $requiredArtifacts) {
    if ($text -notmatch [regex]::Escape($artifact)) {
        $missing += $artifact
    }
}

Write-Output "[authority-ownership] required=$($requiredArtifacts.Count) missing=$($missing.Count)"

if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Output "MISSING $_" }
    Write-Error "authority ownership metadata check failed"
    exit 1
}

Write-Output "OK authority ownership metadata check passed"
exit 0
