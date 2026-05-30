Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$canonical = @(
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md",
    "docs/release/P0_EXECUTION_BOARD_20260528.md"
)

$staged = git diff --cached --name-only
$stagedSet = New-Object System.Collections.Generic.HashSet[string]
$staged | ForEach-Object { if ($_ -and $_.Trim().Length -gt 0) { [void]$stagedSet.Add($_.Trim()) } }

$changedCanonical = @()
foreach ($path in $canonical) {
    if ($stagedSet.Contains($path)) {
        $changedCanonical += $path
    }
}

if ($changedCanonical.Count -eq 0) {
    Write-Output "[authority-edit-sync] no canonical authority files staged"
    exit 0
}

$missing = @()
foreach ($path in $canonical) {
    if (-not $stagedSet.Contains($path)) {
        $missing += $path
    }
}

Write-Output "[authority-edit-sync] staged canonical files: $($changedCanonical -join ', ')"

if ($missing.Count -gt 0) {
    Write-Output "MISSING_COMPANION_AUTHORITY_FILES $($missing -join ', ')"
    Write-Error "authority edit sync check failed"
    exit 1
}

Write-Output "OK authority edit sync check passed"
exit 0
