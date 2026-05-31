param(
    [string]$RouterFile = "frontend/dashboards/src/routes/router.jsx",
    [string]$PolicyFile = "docs/release/ROUTE_GUARD_POLICY_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $RouterFile)) {
    Write-Error "router file not found: $RouterFile"
    exit 1
}

if (-not (Test-Path -Path $PolicyFile)) {
    Write-Error "policy file not found: $PolicyFile"
    exit 1
}

$router = Get-Content -Raw -Path $RouterFile
$policy = Get-Content -Raw -Path $PolicyFile

$requiredPolicyTokens = @(
    "deny-by-default",
    "RoleGuard",
    "RoleRouteGuard",
    "PATHS.STUDENT",
    "/student/dashboard"
)

$missingPolicy = @()
foreach ($token in $requiredPolicyTokens) {
    if ($policy -notmatch [regex]::Escape($token)) {
        $missingPolicy += $token
    }
}

$requiredRouterTokens = @(
    "path: PATHS.STUDENT,",
    "path: '/student/dashboard',",
    "path: '/parent/attendance',",
    "path: '/teacher/attendance',",
    '<RoleRouteGuard allowedRoles={["student"]}>',
    '<RoleRouteGuard allowedRoles={["parent"]}>',
    '<RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>'
)

$missingRouter = @()
foreach ($token in $requiredRouterTokens) {
    if ($router -notmatch [regex]::Escape($token)) {
        $missingRouter += $token
    }
}

Write-Output "[route-guard-policy] policy_missing=$($missingPolicy.Count) router_missing=$($missingRouter.Count)"

if ($missingPolicy.Count -gt 0) {
    $missingPolicy | ForEach-Object { Write-Output "POLICY_MISSING $_" }
}

if ($missingRouter.Count -gt 0) {
    $missingRouter | ForEach-Object { Write-Output "ROUTER_MISSING $_" }
}

if ($missingPolicy.Count -gt 0 -or $missingRouter.Count -gt 0) {
    Write-Error "route guard policy check failed"
    exit 1
}

Write-Output "OK route guard policy check passed"
exit 0
