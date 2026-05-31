param(
    [string]$LogFile = "docs/release/RELEASE_AUTHORITY_CHANGE_CONTROL_LOG_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $LogFile)) {
    Write-Error "change control log not found: $LogFile"
    exit 1
}

$text = Get-Content -Raw -Path $LogFile

$requiredChecklistItems = @(
    "Canonical authority and scorecard decisions are synchronized.",
    "Branch and SHA metadata fields are updated where required.",
    "Non-canonical docs do not assert controlling go/no-go language.",
    "Authority ownership map is still complete for all controlling artifacts.",
    "Mainline authority presence check is green.",
    "Validator outputs are captured in the execution board evidence column."
)

$missingChecklist = @()
foreach ($item in $requiredChecklistItems) {
    if ($text -notmatch [regex]::Escape("[x] $item")) {
        $missingChecklist += $item
    }
}

$changeIdMatches = [regex]::Matches($text, 'AUTH-CC-\d{3}')

Write-Output "[authority-change-control] checklist_missing=$($missingChecklist.Count) entries=$($changeIdMatches.Count)"

if ($changeIdMatches.Count -lt 3) {
    Write-Error "change-control log must contain at least 3 AUTH-CC entries"
    exit 1
}

if ($missingChecklist.Count -gt 0) {
    $missingChecklist | ForEach-Object { Write-Output "MISSING_CHECKLIST $_" }
    Write-Error "authority change-control checklist check failed"
    exit 1
}

Write-Output "OK authority change-control log check passed"
exit 0
