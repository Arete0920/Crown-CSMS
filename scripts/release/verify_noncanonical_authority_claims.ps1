param(
    [string]$DocsRoot = "docs/release"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$allowList = @(
    "CURRENT_RELEASE_SCORECARD_20260528.md",
    "P0_EXECUTION_BOARD_20260528.md",
    "RELEASE_AUTHORITY_PRECEDENCE_TABLE_20260530.md"
)

$claimPattern = '(?im)^\s*[-*]?\s*(ship decision|overall status|current decision|repository-wide decision)\s*:\s*(ship|release_ready|unrestricted go|conditional go|no-go)\b|\bUNRESTRICTED GO\b'
$supersededPattern = 'Superseded Authority Notice|superseded authority notice|Authority Scope Notice|authority scope notice'

$files = Get-ChildItem -Path $DocsRoot -Filter *.md -File
$violations = @()

foreach ($file in $files) {
    if ($allowList -contains $file.Name) {
        continue
    }

    $text = Get-Content -Raw -Path $file.FullName
    if ($text -match $supersededPattern) {
        continue
    }

    if ($text -match $claimPattern) {
        $violations += "$($file.FullName): contains non-canonical release authority claim language"
    }
}

Write-Output "[noncanonical-authority-claims] scanned=$($files.Count) violations=$($violations.Count)"

if ($violations.Count -gt 0) {
    $violations | Select-Object -First 50 | ForEach-Object { Write-Output "VIOLATION $_" }
    Write-Error "non-canonical authority claims check failed"
    exit 1
}

Write-Output "OK non-canonical authority claims check passed"
exit 0
