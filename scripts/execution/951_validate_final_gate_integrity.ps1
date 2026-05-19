param(
    [string]$GatePath = "scripts/execution/950_final_release_gate.ps1"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $GatePath)) {
    throw "Missing gate file: $GatePath"
}

$Text = Get-Content -Raw $GatePath

$ForbiddenPatterns = @(
    "# Simulate",
    "Simulate some checks",
    "placeholder gate",
    "stub gate",
    '$PassCount = 12',
    '$WarnCount = 2',
    'Skipping production probe as requested.',
    '$Decision = "GO-CANDIDATE"`n}',
    'if ($SkipProductionProbe) {`n    $Decision = "GO-CANDIDATE"'
)

$Hits = @()
foreach ($Pattern in $ForbiddenPatterns) {
    if ($Text -like "*$Pattern*") {
        $Hits += $Pattern
    }
}

if ($Hits.Count -gt 0) {
    Write-Host "FINAL RELEASE GATE INTEGRITY FAIL: forbidden stub/simulation logic found." -ForegroundColor Red
    $Hits | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    throw "Do not trust or commit this gate."
}

$RequiredContent = @(
    "check-crown-test-inventory.mjs",
    "check-crown-discovered-surface-coverage.mjs",
    "Final release gate must run on main",
    "Production build_sha",
    "Skipped by -SkipProductionProbe",
    "Invoke-GateCommand",
    "NO-GO"
)

foreach ($Needle in $RequiredContent) {
    if ($Text -notlike "*$Needle*") {
        throw "FINAL RELEASE GATE INTEGRITY FAIL: missing required content: $Needle"
    }
}

Write-Host "FINAL RELEASE GATE INTEGRITY PASS" -ForegroundColor Green
