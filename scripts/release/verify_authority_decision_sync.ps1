Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$statusPath = "docs/CURRENT_RELEASE_STATUS.md"
$scorecardPath = "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md"
$p0Path = "docs/release/P0_EXECUTION_BOARD_20260528.md"

function Extract-Decision([string]$text, [string]$pattern, [string]$label) {
    $m = [regex]::Match($text, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $m.Success) {
        throw "could not extract $label"
    }
    return $m.Groups[1].Value.Trim().ToUpperInvariant()
}

$statusText = Get-Content -Raw -Path $statusPath
$scorecardText = Get-Content -Raw -Path $scorecardPath
$p0Text = Get-Content -Raw -Path $p0Path

$statusDecision = Extract-Decision $statusText "Repository-wide decision:\s*([^\.\r\n]+)" "status decision"
$scorecardDecision = Extract-Decision $scorecardText "Current decision:\s*([^\r\n]+)" "scorecard decision"
$p0Baseline = Extract-Decision $p0Text "Repository-wide decision is\s*([^\(\r\n]+)" "p0 baseline"

Write-Output "[authority-sync] status=$statusDecision scorecard=$scorecardDecision p0=$p0Baseline"

$errors = @()
if ($statusDecision -ne $scorecardDecision) {
    $errors += "status and scorecard decisions diverge"
}
if ($statusDecision -ne $p0Baseline) {
    $errors += "status and p0 baseline decisions diverge"
}

$contradictionPhrases = @(
    'approved slice remains `UNRESTRICTED GO`',
    'canonical approved-slice release authority remains unchanged (`UNRESTRICTED GO`)'
)

foreach ($phrase in $contradictionPhrases) {
    if ($p0Text.Contains($phrase)) {
        $errors += "p0 board contains contradictory phrase: $phrase"
    }
}

if ($errors.Count -gt 0) {
    foreach ($e in $errors) {
        Write-Output "ERROR $e"
    }
    Write-Error "authority decision sync check failed"
    exit 1
}

Write-Output "OK authority decision sync check passed"
exit 0
