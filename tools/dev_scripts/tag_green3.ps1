param(
  [Parameter(Mandatory=$true)][string]$TagName
)

$ErrorActionPreference = "Stop"

$gate = Join-Path $PSScriptRoot "golden_path_gate.ps1"
if (-not (Test-Path $gate)) { throw "Missing gate: $gate" }

1..3 | ForEach-Object {
  Write-Host "--- GATE RUN $_ ---"
  powershell -ExecutionPolicy Bypass -File $gate
  if ($LASTEXITCODE -ne 0) { throw "GREEN_3X_FAILED run=$_ exit=$LASTEXITCODE" }
}

Write-Host "GREEN_3X=YES"

Set-Location (Join-Path $env:USERPROFILE "OneDrive\Desktop\Crown2026_DEMO_TAG")

git tag $TagName
git push origin $TagName
git show -s --decorate --oneline $TagName

Write-Host "TAGGED=YES name=$TagName"
exit 0
