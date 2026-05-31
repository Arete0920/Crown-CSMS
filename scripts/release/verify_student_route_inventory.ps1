param(
    [string]$RouterFile = "frontend/dashboards/src/routes/router.jsx",
    [string]$InventoryFile = "docs/release/STUDENT_ROUTE_GUARD_INVENTORY_20260530.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $RouterFile)) {
    Write-Error "router file not found: $RouterFile"
    exit 1
}

if (-not (Test-Path -Path $InventoryFile)) {
    Write-Error "inventory file not found: $InventoryFile"
    exit 1
}

$router = Get-Content -Raw -Path $RouterFile
$inventory = Get-Content -Raw -Path $InventoryFile

$routerChecks = @(
    "path: PATHS.STUDENT,",
    "path: '/student/dashboard',",
    "path: '/student/today',",
    "path: '/student/assignments',",
    '<RoleRouteGuard allowedRoles={["student"]}>',
    '<RoleGuard allowedRoles={STUDENT_LEARNING_ALLOWED_ROLES}>'
)

$missingRouter = @()
foreach ($token in $routerChecks) {
    if ($router -notmatch [regex]::Escape($token)) {
        $missingRouter += $token
    }
}

$inventoryChecks = @(
    "| PATHS.STUDENT |",
    "| /student/dashboard |",
    "| /student/today |",
    "| /student/assignments |",
    "RoleRouteGuard",
    "RoleGuard"
)

$missingInventory = @()
foreach ($token in $inventoryChecks) {
    if ($inventory -notmatch [regex]::Escape($token)) {
        $missingInventory += $token
    }
}

Write-Output "[student-route-inventory] router_missing=$($missingRouter.Count) inventory_missing=$($missingInventory.Count)"

if ($missingRouter.Count -gt 0) {
    $missingRouter | ForEach-Object { Write-Output "ROUTER_MISSING $_" }
}

if ($missingInventory.Count -gt 0) {
    $missingInventory | ForEach-Object { Write-Output "INVENTORY_MISSING $_" }
}

if ($missingRouter.Count -gt 0 -or $missingInventory.Count -gt 0) {
    Write-Error "student route inventory check failed"
    exit 1
}

Write-Output "OK student route inventory check passed"
exit 0
