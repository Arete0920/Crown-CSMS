param(
    [string]$DocsGlob = "docs/release/*.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$decisionPattern = 'decision|go|release posture|release authority'
$branchPattern = 'branch'
$shaPattern = 'sha|commit'
$supersededPattern = 'Superseded Authority Notice|superseded authority notice'

$files = Get-ChildItem -Path $DocsGlob -File
if (-not $files) {
    Write-Error "no release docs found for glob: $DocsGlob"
    exit 1
}

$violations = @()

foreach ($f in $files) {
    $text = Get-Content -Raw -Path $f.FullName
    if ($text -match $decisionPattern) {
        if ($text -match $supersededPattern) {
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
