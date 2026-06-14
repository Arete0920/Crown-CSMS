param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path $repoRoot "audit-artifacts/route-exposure-guard-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$routerPath = "frontend/dashboards/src/routes/router.jsx"
if (-not (Test-Path $routerPath)) {
    throw "Missing router file: $routerPath"
}

$router = Get-Content $routerPath -Raw
$findings = New-Object System.Collections.Generic.List[object]

function Add-Finding {
    param([string]$Id, [string]$Route, [string]$Evidence, [string]$RequiredFix)
    $findings.Add([pscustomobject]@{
        id = $Id
        route = $Route
        evidence = $Evidence
        required_fix = $RequiredFix
    })
}

function Get-RouteBlock {
    param([string]$Route)
    $escaped = [regex]::Escape($Route)
    $pattern = ('path:\s*[''\"]{0}[''\"][\s\S]{{0,900}}?\n\s*}},' -f $escaped)
    $match = [regex]::Match($router, $pattern)
    if ($match.Success) { return $match.Value }
    return ""
}

$requiredGuardedRoutes = @(
    "/parent",
    "/parent/dashboard",
    "/parent/attendance",
    "/parent/communications",
    "/parent/schedule",
    "/parent/students/:id",
    "/student/dashboard",
    "/teacher/dashboard",
    "/teacher/classes",
    "/teacher/lesson-plans",
    "/teacher/curriculum",
    "/finance/dashboard",
    "/school-admin-dashboard"
)

foreach ($route in $requiredGuardedRoutes) {
    $block = Get-RouteBlock -Route $route
    if ([string]::IsNullOrWhiteSpace($block)) {
        Add-Finding -Id "RG-001" -Route $route -Evidence "Route block not found in router.jsx." -RequiredFix "Either add an explicitly guarded route or remove this route from production/sandbox navigation."
        continue
    }

    $hasGuard = $block -match "RoleRouteGuard|RoleGuard|RequirePermission|Navigate"
    if (-not $hasGuard) {
        Add-Finding -Id "RG-002" -Route $route -Evidence "Route block has no RoleRouteGuard, RoleGuard, RequirePermission, or Navigate containment." -RequiredFix "Wrap route element in an explicit role/permission guard or remove the route."
    }

    $isParentRoute = $route -like "/parent*"
    if ($isParentRoute -and $block -match "<Navigate" -and $block -notmatch "RoleRouteGuard|RoleGuard|RequirePermission") {
        Add-Finding -Id "RG-003" -Route $route -Evidence "Parent alias redirects without role guard containment." -RequiredFix "Wrap the alias in RoleRouteGuard allowedRoles parent before redirecting or replace with a guarded parent landing route."
    }
}

$resultsPath = Join-Path $base "00_route_exposure_findings.csv"
$findings | Export-Csv -Path $resultsPath -NoTypeInformation -Encoding UTF8

$summaryPath = Join-Path $base "00_ROUTE_EXPOSURE_SUMMARY.md"
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Route Exposure Guard Gate")
$md.Add("")
$md.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("- Evidence root: $base")
$md.Add("- Findings: $($findings.Count)")
$md.Add("")
if ($findings.Count -eq 0) {
    $md.Add("## Verdict")
    $md.Add("")
    $md.Add("PASS")
} else {
    $md.Add("## Verdict")
    $md.Add("")
    $md.Add("FAIL")
    $md.Add("")
    $md.Add("## Findings")
    foreach ($finding in $findings) {
        $md.Add("- $($finding.id) $($finding.route): $($finding.evidence) Fix: $($finding.required_fix)")
    }
}
$md | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "ROUTE_EXPOSURE_EVIDENCE=$base"
Write-Host "ROUTE_EXPOSURE_SUMMARY=$summaryPath"
Write-Host "ROUTE_EXPOSURE_FINDINGS=$resultsPath"

if ($findings.Count -gt 0) {
    exit 1
}
