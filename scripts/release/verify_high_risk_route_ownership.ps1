param(
    [string]$OwnershipFile = "docs/release/HIGH_RISK_ROUTE_OWNERSHIP_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $OwnershipFile)) {
    Write-Error "high-risk route ownership file not found: $OwnershipFile"
    exit 1
}

$text = Get-Content -Raw -Path $OwnershipFile
$requiredRoutes = @(
    "PATHS.STUDENT",
    "/student/dashboard",
    "/student/today",
    "/student/assignments",
    "/parent/attendance",
    "/teacher/attendance",
    "/summer-camp",
    "/summer-camp/roster"
)

$requiredOwnerTags = @(
    "owner:student-platform",
    "owner:academics-platform",
    "owner:family-platform",
    "owner:extended-care-platform"
)

$missingRoutes = @()
foreach ($route in $requiredRoutes) {
    if ($text -notmatch [regex]::Escape($route)) {
        $missingRoutes += $route
    }
}

$missingTags = @()
foreach ($tag in $requiredOwnerTags) {
    if ($text -notmatch [regex]::Escape($tag)) {
        $missingTags += $tag
    }
}

Write-Output "[high-risk-route-ownership] routes_missing=$($missingRoutes.Count) tags_missing=$($missingTags.Count)"

if ($missingRoutes.Count -gt 0) {
    $missingRoutes | ForEach-Object { Write-Output "ROUTE_MISSING $_" }
}

if ($missingTags.Count -gt 0) {
    $missingTags | ForEach-Object { Write-Output "TAG_MISSING $_" }
}

if ($missingRoutes.Count -gt 0 -or $missingTags.Count -gt 0) {
    Write-Error "high-risk route ownership check failed"
    exit 1
}

Write-Output "OK high-risk route ownership check passed"
exit 0
