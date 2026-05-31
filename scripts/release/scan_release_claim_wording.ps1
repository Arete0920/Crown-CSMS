param(
    [string]$DocsRoot = "docs"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$patterns = @(
    'UNRESTRICTED GO',
    'RELEASE_READY',
    'SHIP\b'
)

$results = @()

Write-Output "[release-claim-scan] docs_root=$DocsRoot"

foreach ($pattern in $patterns) {
    $matches = rg -n --glob "*.md" --glob "*.txt" --glob "*.json" --glob "*.csv" "$pattern" $DocsRoot 2>$null
    if ($LASTEXITCODE -eq 0 -and $matches) {
        foreach ($line in $matches) {
            $results += "[$pattern] $line"
        }
    }
}

if ($results.Count -eq 0) {
    Write-Output "OK no stale or contradictory release-claim wording detected"
    exit 0
}

Write-Output "FOUND $($results.Count) potential stale/contradictory release-claim matches"
$results | ForEach-Object { Write-Output $_ }
Write-Error "release-claim wording scan found potential stale/contradictory language"
exit 1
