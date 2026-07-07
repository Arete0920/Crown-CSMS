# tools/verify_routes_gate.ps1
# Route Gate (static)
# Enforces:
# 1) router.jsx exists
# 2) every routed element <Component /> has a corresponding import
# 3) every import from ../pages points to an existing file
# 4) flags mixed shell risk: pages importing BOTH @mui/material AND CrownLayout
# PS5.1-safe, ASCII-only, UTF-8 output.

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$routerRel = 'frontend/dashboards/src/routes/router.jsx'
$router = Join-Path $repoRoot $routerRel

if (-not (Test-Path $router)) {
  Write-Host "Route Gate FAILED - missing router file: $routerRel" -ForegroundColor Red
  exit 1
}

$raw = Get-Content -Path $router -Raw

$imports = @{}
$reDef = [regex]::new('import\s+([A-Za-z0-9_]+)\s+from\s+[\x27\x22](\.\.[\\/]pages[\\/][^\x27\x22]+\.jsx)[\x27\x22]')
$reNamed = [regex]::new('import\s+\{([^}]+)\}\s+from\s+[\x27\x22](\.\.[\\/]pages[\\/][^\x27\x22]+\.jsx)[\x27\x22]')
$reLazy = [regex]::new('const\s+([A-Za-z0-9_]+)\s*=\s*Object\.assign\(lazy\(\(\)\s*=>\s*import\(\s*[\x27\x22](\.\.[\\/]pages[\\/][^\x27\x22]+\.jsx)[\x27\x22]\s*\)')

foreach ($match in $reDef.Matches($raw)) {
  $imports[$match.Groups[1].Value] = $match.Groups[2].Value
}

foreach ($match in $reNamed.Matches($raw)) {
  $relativePath = $match.Groups[2].Value
  foreach ($part in ($match.Groups[1].Value -split ',')) {
    $component = ($part.Trim() -replace '\s+as\s+.*$', '')
    if ($component) {
      $imports[$component] = $relativePath
    }
  }
}

foreach ($match in $reLazy.Matches($raw)) {
  $imports[$match.Groups[1].Value] = $match.Groups[2].Value
}

$nonPageAllowList = @('Navigate', 'Outlet', 'OpsCommandCenter')
$routeCompPattern = 'element\s*:\s*<\s*([A-Za-z0-9_]+)\b'
$routeCompMatches = [regex]::Matches($raw, $routeCompPattern)
$routeComps = New-Object System.Collections.Generic.HashSet[string]
foreach ($match in $routeCompMatches) {
  $null = $routeComps.Add($match.Groups[1].Value)
}

$pathPattern = 'path\s*:\s*[\x27\x22]([^\x27\x22]+)[\x27\x22]'
$pathMatches = [regex]::Matches($raw, $pathPattern)
$paths = @()
foreach ($match in $pathMatches) { $paths += $match.Groups[1].Value }

$routesDir = Join-Path $repoRoot 'frontend/dashboards/src/routes'
$missingFiles = New-Object System.Collections.Generic.List[object]
foreach ($component in $imports.Keys) {
  $relativePath = $imports[$component] -replace '/', '\'
  $pageAbs = [System.IO.Path]::GetFullPath((Join-Path $routesDir $relativePath))
  if (-not (Test-Path $pageAbs)) {
    $missingFiles.Add([pscustomobject]@{ Component = $component; Import = $imports[$component]; Expected = $pageAbs }) | Out-Null
  }
}

$missingImports = New-Object System.Collections.Generic.List[object]
foreach ($component in $routeComps) {
  if ($nonPageAllowList -contains $component) { continue }
  if (-not $imports.ContainsKey($component)) {
    $missingImports.Add([pscustomobject]@{ Component = $component; Note = 'No import from ../pages/*.jsx found' }) | Out-Null
  }
}

$mixedShell = New-Object System.Collections.Generic.List[object]
foreach ($component in $imports.Keys) {
  $relativePath = $imports[$component] -replace '/', '\'
  $pageAbs = [System.IO.Path]::GetFullPath((Join-Path $routesDir $relativePath))
  if (-not (Test-Path $pageAbs)) { continue }

  $pageRaw = Get-Content -Path $pageAbs -Raw
  if (($pageRaw -match '@mui/material') -and ($pageRaw -match '\bCrownLayout\b')) {
    $mixedShell.Add([pscustomobject]@{ Page = (Split-Path -Leaf $pageAbs); Component = $component }) | Out-Null
  }
}

Write-Host ("Route Gate: page_imports={0}, routed_components={1}, paths={2}" -f $imports.Count, $routeComps.Count, $paths.Count) -ForegroundColor Cyan

$failed = $false

if ($missingFiles.Count -gt 0) {
  $failed = $true
  Write-Host ''
  Write-Host 'Route Gate FAILED - missing imported page files:' -ForegroundColor Red
  $missingFiles | Format-Table -AutoSize | Out-String | Write-Host
}

if ($missingImports.Count -gt 0) {
  $failed = $true
  Write-Host ''
  Write-Host 'Route Gate FAILED - routed components missing imports:' -ForegroundColor Red
  $missingImports | Format-Table -AutoSize | Out-String | Write-Host
}

if ($mixedShell.Count -gt 0) {
  $failed = $true
  Write-Host ''
  Write-Host 'Route Gate FAILED - mixed shell risk (MUI + CrownLayout in same page):' -ForegroundColor Red
  $mixedShell | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host ''
  Write-Host 'Fix: one shell per page. CrownLayout pages must not import @mui/material.' -ForegroundColor Yellow
}

if ($failed) { exit 1 }

Write-Host 'Route Gate PASSED' -ForegroundColor Green
