param(
    [string]$DocsRoot = "docs/release"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requiredDocs = @(
    "LIVE_RELEASE_TRUTH.md",
    "LIVE_FINAL_RELEASE_GATE.md",
    "LIVE_RELEASE_GATE_STATUS.md",
    "INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md",
    "PROGRAM_SCORECARD_20260506.md"
)

$requiredTokens = @(
    "Superseded Authority Notice",
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md"
)

$violations = @()
foreach ($doc in $requiredDocs) {
    $fullPath = Join-Path $DocsRoot $doc
    if (-not (Test-Path -Path $fullPath)) {
        $violations += "${fullPath}: missing file"
        continue
    }

    $text = Get-Content -Raw -Path $fullPath
    foreach ($token in $requiredTokens) {
        if ($text -notmatch [regex]::Escape($token)) {
            $violations += "${fullPath}: missing token '$token'"
        }
    }
}

Write-Output "[superseded-watermark] docs=$($requiredDocs.Count) violations=$($violations.Count)"

if ($violations.Count -gt 0) {
    $violations | ForEach-Object { Write-Output "VIOLATION $_" }
    Write-Error "superseded authority watermark verification failed"
    exit 1
}

Write-Output "OK superseded authority watermarks verified"
exit 0
