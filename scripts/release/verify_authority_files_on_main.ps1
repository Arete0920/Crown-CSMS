param(
    [string]$MainRef = "origin/main"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$required = @(
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md",
    "docs/release/P0_EXECUTION_BOARD_20260528.md"
)

$missing = @()

Write-Output "[authority-main-check] main_ref=$MainRef"

foreach ($path in $required) {
    git cat-file -e "$MainRef`:$path" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "PRESENT $path"
    }
    else {
        Write-Output "MISSING $path"
        $missing += $path
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("authority files missing on {0}: {1}" -f $MainRef, ($missing -join ", "))
    exit 1
}

Write-Output "OK all authority files present on $MainRef"
exit 0
