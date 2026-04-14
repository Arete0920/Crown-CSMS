param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$dirs = @(
  "docs\audit",
  "docs\audit\inventories",
  "docs\audit\scans",
  "docs\audit\evidence",
  "docs\audit\reports",
  "artifacts\deep-audit\logs"
)

foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

Write-Host "Deep audit directories ready."
Write-Host "Next: run 01_inventory_all.ps1"
