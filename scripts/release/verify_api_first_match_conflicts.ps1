param(
    [string[]]$Files = @(
        "backend/crown_api/api_v1_urls.py",
        "backend/crown_api/urls.py"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$allPaths = @{}

foreach ($file in $Files) {
    if (-not (Test-Path -Path $file)) {
        Write-Error "route file not found: $file"
        exit 1
    }

    $text = Get-Content -Raw -Path $file
    $matches = [regex]::Matches($text, 'path\("([^"]*)"')

    foreach ($m in $matches) {
        $routePath = $m.Groups[1].Value

        # Ignore include catch-all sentinel and parameterized token routes.
        if ($routePath -eq "") { continue }
        if ($routePath -match '<[^>]+>') { continue }

        if (-not $allPaths.ContainsKey($routePath)) {
            $allPaths[$routePath] = @()
        }

        $allPaths[$routePath] += $file
    }
}

$conflicts = @()
foreach ($routePath in $allPaths.Keys) {
    $sources = $allPaths[$routePath]
    if ($sources.Count -gt 1) {
        $distinctSources = $sources | Select-Object -Unique
        # Allow known intentional alias pairings in urls.py.
        $isKnownAlias = ($routePath -eq 'api/v1/' -or $routePath -eq 'api/' -or $routePath -eq 'api/v1/dashboards/' -or $routePath -eq 'api/dashboards/')
        if (-not $isKnownAlias -or $distinctSources.Count -gt 1) {
            $conflicts += "$routePath => $($distinctSources -join ', ')"
        }
    }
}

Write-Output "[api-first-match-conflicts] scanned_paths=$($allPaths.Count) conflicts=$($conflicts.Count)"

if ($conflicts.Count -gt 0) {
    $conflicts | ForEach-Object { Write-Output "CONFLICT $_" }
    Write-Error "api first-match conflict check failed"
    exit 1
}

Write-Output "OK api first-match conflict check passed"
exit 0
