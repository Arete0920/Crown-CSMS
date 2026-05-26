[CmdletBinding()]
param(
  [string]$OutPath = "audit-artifacts/brand-integration/07_brand_asset_readiness_snapshot.json"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $repoRoot

function Resolve-ManifestPath([string]$manifestAssetPath) {
  return "frontend/dashboards/public" + ($manifestAssetPath -replace '^/brand', '/brand')
}

$crownManifestPath = "frontend/dashboards/public/brand/crown/manifest.json"
$msManifestPath = "frontend/dashboards/public/brand/third-party/microsoft/manifest.json"

$crownManifest = Get-Content $crownManifestPath -Raw | ConvertFrom-Json
$msManifest = Get-Content $msManifestPath -Raw | ConvertFrom-Json

$crownAssets = @()
foreach ($prop in $crownManifest.assets.PSObject.Properties) {
  $path = Resolve-ManifestPath $prop.Value.path
  $exists = Test-Path $path
  $crownAssets += [PSCustomObject]@{
    key = $prop.Name
    path = $prop.Value.path
    resolvedPath = $path
    exists = $exists
  }
}

$msAssets = @()
foreach ($prop in $msManifest.assets.PSObject.Properties) {
  $path = Resolve-ManifestPath $prop.Value.path
  $exists = Test-Path $path
  $msAssets += [PSCustomObject]@{
    key = $prop.Name
    path = $prop.Value.path
    resolvedPath = $path
    exists = $exists
  }
}

$faviconRequired = @(
  "frontend/dashboards/public/brand/crown/favicon/favicon.ico",
  "frontend/dashboards/public/brand/crown/favicon/favicon-16x16.png",
  "frontend/dashboards/public/brand/crown/favicon/favicon-32x32.png",
  "frontend/dashboards/public/brand/crown/favicon/apple-touch-icon.png",
  "frontend/dashboards/public/brand/crown/favicon/android-chrome-192x192.png",
  "frontend/dashboards/public/brand/crown/favicon/android-chrome-512x512.png"
)

$faviconAssets = @()
foreach ($f in $faviconRequired) {
  $faviconAssets += [PSCustomObject]@{
    path = $f
    exists = (Test-Path $f)
  }
}

$result = [PSCustomObject]@{
  generated_at = (Get-Date).ToString("o")
  repo_root = "$repoRoot"
  crown_manifest_assets = [PSCustomObject]@{
    present = @($crownAssets | Where-Object { $_.exists }).Count
    total = @($crownAssets).Count
    items = $crownAssets
  }
  microsoft_manifest_assets = [PSCustomObject]@{
    present = @($msAssets | Where-Object { $_.exists }).Count
    total = @($msAssets).Count
    items = $msAssets
  }
  crown_favicons = [PSCustomObject]@{
    present = @($faviconAssets | Where-Object { $_.exists }).Count
    total = @($faviconAssets).Count
    items = $faviconAssets
  }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutPath) | Out-Null
$result | ConvertTo-Json -Depth 8 | Out-File $OutPath -Encoding utf8
Write-Host "WROTE=$OutPath"
Write-Host ("CROWN_MANIFEST=" + $result.crown_manifest_assets.present + "/" + $result.crown_manifest_assets.total)
Write-Host ("MS_MANIFEST=" + $result.microsoft_manifest_assets.present + "/" + $result.microsoft_manifest_assets.total)
Write-Host ("CROWN_FAVICON=" + $result.crown_favicons.present + "/" + $result.crown_favicons.total)
