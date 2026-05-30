param(
    [string]$DocsGlob = "docs/release/*.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$decisionPattern = '(?im)^\s*[-*]?\s*(ship decision|overall status|current decision|repository-wide decision)\s*:\s*(ship|release_ready|unrestricted go|conditional go|no-go)\b|\bUNRESTRICTED GO\b'
$branchPattern = 'branch'
$shaPattern = 'sha|commit'
$scopeNoticePattern = 'Superseded Authority Notice|superseded authority notice|Authority Scope Notice|authority scope notice'

$files = Get-ChildItem -Path $DocsGlob -File
if (-not $files) {
    Write-Error "no release docs found for glob: $DocsGlob"
    exit 1
}

$violations = @()

foreach ($f in $files) {
    $text = Get-Content -Raw -Path $f.FullName
    if ($text -match $decisionPattern) {
        if ($text -match $scopeNoticePattern) {
            continue
        }

        $hasBranch = $text -match $branchPattern
        $hasSha = $text -match $shaPattern
        if (-not $hasBranch -or -not $hasSha) {
            $violations += "$($f.FullName): missing branch and/or sha metadata"
        }
    }
}

Write-Output "[release-claim-branch-sha] scanned=$($files.Count) violations=$($violations.Count)"

if ($violations.Count -gt 0) {
    $violations | Select-Object -First 50 | ForEach-Object { Write-Output "VIOLATION $_" }
    Write-Error "release claim branch/sha check failed"
    exit 1
}

Write-Output "OK release claim branch/sha check passed"
exit 0
