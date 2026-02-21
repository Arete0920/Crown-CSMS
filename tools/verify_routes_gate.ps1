# tools/verify_routes_gate.ps1
# Route Gate (static)
# Enforces:
# 1) router.jsx exists
# 2) every routed element <Component /> has a corresponding import
# 3) every import from ../pages points to an existing file
# 4) flags mixed shell risk: pages importing BOTH @mui/material AND CrownLayout
# PS5.1-safe, ASCII-only, UTF-8 output.

$ErrorActionPreference = "Stop"

$repoRoot  = Split-Path -Parent $PSScriptRoot
$routerRel = "frontend/dashboards/src/routes/router.jsx"
$router    = Join-Path $repoRoot $routerRel

if (!(Test-Path $router)) {
  Write-Host "Route Gate FAILED - missing router file: $routerRel" -ForegroundColor Red
  exit 1
}

$raw = Get-Content -Path $router -Raw

# --- Extract imports from ../pages/*.jsx ---
# Handles both default: import Foo from "..."
# and named:           import { Foo } from "..."
$imports = @{}
$reDef  = [regex] 'import\s+([A-Za-z0-9_]+)\s+from\s+[''"](\.\.[\/]pages[\/][^''"]+\.jsx)[''"]'
$reNamed = [regex] 'import\s+\{\s*([A-Za-z0-9_]+)\s*\}\s+from\s+[''"](\.\.[\/]pages[\/][^''"]+\.jsx)[''"]'

foreach ($m in $reDef.Matches($raw)) {
  $comp = $m.Groups[1].Value
  $rel  = $m.Groups[2].Value
  $imports[$comp] = $rel
}
foreach ($m in $reNamed.Matches($raw)) {
  $comp = $m.Groups[1].Value
  $rel  = $m.Groups[2].Value
  $imports[$comp] = $rel
}

# --- Extract routed components referenced as element: <Comp .../> or element: <Comp> ---
# Allow-list: non-page components that may legally appear as route elements
$nonPageAllowList = @("Navigate", "Outlet", "OpsCommandCenter")

$routeCompMatches = [regex]::Matches($raw, 'element\s*:\s*<\s*([A-Za-z0-9_]+)\b')
$routeComps = New-Object System.Collections.Generic.HashSet[string]
foreach ($m in $routeCompMatches) {
  $null = $routeComps.Add($m.Groups[1].Value)
}

# --- Extract paths for informational output ---
$pathMatches = [regex]::Matches($raw, 'path\s*:\s*[''"]([^''"]+)[''"]')
$paths = @()
foreach ($m in $pathMatches) { $paths += $m.Groups[1].Value }

# --- Validate: imported page files exist ---
# Imports are relative to src/routes/, so ../pages/Foo.jsx = src/pages/Foo.jsx
$routesDir = Join-Path $repoRoot "frontend/dashboards/src/routes"
$missingFiles = New-Object System.Collections.Generic.List[object]
foreach ($k in $imports.Keys) {
  $rel    = $imports[$k] -replace '/', '\'
  $pageAbs = [System.IO.Path]::GetFullPath((Join-Path $routesDir $rel))
  if (!(Test-Path $pageAbs)) {
    $missingFiles.Add([pscustomobject]@{ Component=$k; Import=$imports[$k]; Expected=$pageAbs }) | Out-Null
  }
}

# --- Validate: each routed component has an import (or is allow-listed) ---
$missingImports = New-Object System.Collections.Generic.List[object]
foreach ($c in $routeComps) {
  if ($nonPageAllowList -contains $c) { continue }
  if (-not $imports.ContainsKey($c)) {
    $missingImports.Add([pscustomobject]@{ Component=$c; Note="No import from ../pages/*.jsx found" }) | Out-Null
  }
}

# --- Mixed shell risk: pages importing BOTH @mui/material AND CrownLayout ---
$mixedShell = New-Object System.Collections.Generic.List[object]
foreach ($k in $imports.Keys) {
  $rel    = $imports[$k] -replace '/', '\'
  $pageAbs = [System.IO.Path]::GetFullPath((Join-Path $routesDir $rel))
  if (!(Test-Path $pageAbs)) { continue }

  $praw = Get-Content -Path $pageAbs -Raw
  if (($praw -match '@mui/material') -and ($praw -match '\bCrownLayout\b')) {
    $mixedShell.Add([pscustomobject]@{ Page=(Split-Path -Leaf $pageAbs); Component=$k }) | Out-Null
  }
}

Write-Host ("Route Gate: page_imports={0}, routed_components={1}, paths={2}" -f $imports.Count, $routeComps.Count, $paths.Count) -ForegroundColor Cyan

$failed = $false

if ($missingFiles.Count -gt 0) {
  $failed = $true
  Write-Host "" ; Write-Host "Route Gate FAILED - missing imported page files:" -ForegroundColor Red
  $missingFiles | Format-Table -AutoSize | Out-String | Write-Host
}

if ($missingImports.Count -gt 0) {
  $failed = $true
  Write-Host "" ; Write-Host "Route Gate FAILED - routed components missing imports:" -ForegroundColor Red
  $missingImports | Format-Table -AutoSize | Out-String | Write-Host
}

if ($mixedShell.Count -gt 0) {
  $failed = $true
  Write-Host "" ; Write-Host "Route Gate FAILED - mixed shell risk (MUI + CrownLayout in same page):" -ForegroundColor Red
  $mixedShell | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host "" ; Write-Host "Fix: one shell per page. CrownLayout pages must not import @mui/material." -ForegroundColor Yellow
}

if ($failed) { exit 1 }

Write-Host "Route Gate PASSED" -ForegroundColor Green
