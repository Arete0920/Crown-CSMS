#!/usr/bin/env pwsh
# tools/verify_prod_build_sha.ps1
#
# Deterministic prod integrity guard.
# Compares an expected Git SHA against the BUILD_SHA app setting
# on the target Azure App Service.
#
# Usage:
#   .\tools\verify_prod_build_sha.ps1 -ExpectedSha (git rev-parse HEAD)
#
# In CI (tag-driven deploy workflow):
#   - run AFTER deploy step
#   - pass the release tag SHA as -ExpectedSha
#   - fail the job if this script throws

param(
  [Parameter(Mandatory=$true)][string]$ExpectedSha,
  [Parameter(Mandatory=$false)][string]$AppName = "crown-api-prod",
  [Parameter(Mandatory=$false)][string]$ResourceGroup = "crown-rg"
)

$ErrorActionPreference = "Stop"

Write-Host "--- Crown Prod Integrity Check ---"
Write-Host "App:            $AppName"
Write-Host "Resource Group: $ResourceGroup"
Write-Host "Expected SHA:   $ExpectedSha"

$deployed = az webapp config appsettings list `
  --name $AppName `
  --resource-group $ResourceGroup `
  --query "[?name=='BUILD_SHA'].value | [0]" `
  -o tsv 2>&1

if (-not $deployed -or $deployed.ToString().Trim() -eq "") {
  throw "BUILD_SHA is missing on $AppName. Refusing to proceed."
}

$deployed = $deployed.ToString().Trim()
Write-Host "Deployed SHA:   $deployed"

if ($deployed.ToLower() -ne $ExpectedSha.Trim().ToLower()) {
  Write-Host ""
  Write-Host "FAIL: PROD DRIFT DETECTED" -ForegroundColor Red
  Write-Host "  Expected: $ExpectedSha"
  Write-Host "  Deployed: $deployed"
  throw "PROD DRIFT: deployed BUILD_SHA does not match expected SHA. Deploy did not land or setting was not updated."
}

Write-Host ""
Write-Host "OK: prod BUILD_SHA matches expected SHA." -ForegroundColor Green
Write-Host "--- Integrity check passed ---"
