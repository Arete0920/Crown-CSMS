param(
    [string]$BuildTag = '',
    [string]$ApiBaseUrl = ''
)

$ErrorActionPreference = 'Stop'

if (-not $BuildTag) {
    $BuildTag = 'demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

if (-not $ApiBaseUrl) {
    throw 'ApiBaseUrl is required.'
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $RepoRoot

Write-Host '== INVESTOR DEMO PREFLIGHT =='
Write-Host "Repo root: $RepoRoot"
Write-Host "Build tag: $BuildTag"
Write-Host "API Base URL: $ApiBaseUrl"
Write-Host ''

Push-Location $RepoRoot

.\scripts\release\lock-frontend-rc.ps1 -BuildTag $BuildTag -ApiBaseUrl $ApiBaseUrl

Set-Location (Join-Path $RepoRoot 'frontend\dashboards')

npm run verify:api-contracts
npm run verify:navigation

Set-Location $RepoRoot
node .\scripts\release\generate-demo-proof.mjs

Write-Host ''
Write-Host '== PREFLIGHT COMPLETE =='
Write-Host 'Artifacts:'
Write-Host ' - frontend/dashboards/dist/release-candidate.json'
Write-Host ' - frontend/dashboards/dist/demo-proof.json'

Pop-Location
