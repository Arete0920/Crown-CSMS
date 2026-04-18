param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$src = Join-Path $RepoRoot "frontend\dashboards\src"
$out = Join-Path $RepoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

if (-not (Test-Path $src)) {
    throw "Missing frontend source path: $src"
}

$files = Get-ChildItem $src -Recurse -File | Where-Object {
    $_.Extension -in ".js", ".jsx", ".ts", ".tsx"
}

$routeDefPatterns = @(
    'path\s*:\s*["''](?<route>/[^"''\s]+)["'']',
    '<Route[^>]*\spath=["''](?<route>/[^"''\s]+)["'']'
)

$routeRefPatterns = @(
    '<Link[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    '<NavLink[^>]*\bto=\{?["''](?<route>/[^"''\s]+)["'']\}?',
    'navigate\(\s*["''](?<route>/[^"''\s]+)["'']',
    'router\.push\(\s*["''](?<route>/[^"''\s]+)["'']',
    'href=\{?["''](?<route>/[^"''\s]+)["'']\}?'
)

function Normalize-Route([string]$route) {
    if ([string]::IsNullOrWhiteSpace($route)) { return $null }
    if ($route -match '^(https?:)?//') { return $null }
    if (-not $route.StartsWith('/')) { return $null }

    $route = $route.Split('?')[0].Split('#')[0]

    if ($route.Length -gt 1 -and $route.EndsWith('/')) {
        $route = $route.TrimEnd('/')
    }

    return $route
}

function Route-ToRegex([string]$route) {
    if ($route -eq "/") { return '^/$' }

    $escaped = [regex]::Escape($route)
    $escaped = $escaped -replace '\\:[A-Za-z0-9_]+', '[^/]+'
    $escaped = $escaped -replace '\\\*', '.*'
    return "^$escaped/?$"
}

$routeDefs = New-Object System.Collections.Generic.HashSet[string]
$routeRefs = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw

    foreach ($pattern in $routeDefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) { [void]$routeDefs.Add($route) }
        }
    }

    foreach ($pattern in $routeRefPatterns) {
        foreach ($m in [regex]::Matches($content, $pattern)) {
            $route = Normalize-Route $m.Groups["route"].Value
            if ($route) {
                $routeRefs.Add([pscustomobject]@{
                    File  = $file.FullName.Replace($RepoRoot, "").TrimStart("\")
                    Route = $route
                })
            }
        }
    }
}

$criticalRoutes = @(
    "/login",
    "/admin",
    "/admissions",
    "/finance",
    "/billing",
    "/financial-aid",
    "/academics",
    "/communications",
    "/board/executive"
)

foreach ($r in $criticalRoutes) { [void]$routeDefs.Add($r) }

$compiledDefs = $routeDefs | ForEach-Object {
    [pscustomobject]@{
        Route = $_
        Regex = Route-ToRegex $_
    }
}

$missing = foreach ($ref in $routeRefs) {
    $matched = $false
    foreach ($def in $compiledDefs) {
        if ($ref.Route -match $def.Regex) {
            $matched = $true
            break
        }
    }

    if (-not $matched) {
        [pscustomobject]@{
            Route = $ref.Route
            File = $ref.File
            Problem = "Link target not matched by any declared route"
        }
    }
}

$routeDefs | Sort-Object | Set-Content (Join-Path $out "declared-routes.txt")
$routeRefs | Sort-Object Route, File | Export-Csv (Join-Path $out "route-references.csv") -NoTypeInformation
$missing | Sort-Object Route, File | Export-Csv (Join-Path $out "missing-routes.csv") -NoTypeInformation

@"
# Frontend Wiring Summary

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Declared routes: $($routeDefs.Count)
Route references: $($routeRefs.Count)
Missing route matches: $(@($missing).Count)

Critical routes:
$($criticalRoutes | ForEach-Object { "- $_" } | Out-String)
"@ | Set-Content (Join-Path $out "frontend-wiring-summary.md")

if (@($missing).Count -gt 0) {
    Write-Host "FAIL: missing route matches found. See artifacts\wiring-proof\missing-routes.csv" -ForegroundColor Red
    exit 1
}

Write-Host "PASS: frontend wiring check clean." -ForegroundColor Green
exit 0