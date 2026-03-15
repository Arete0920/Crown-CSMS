param(
    [string]$BuildTag = '',
    [string]$ApiBaseUrl = ''
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $RepoRoot
$FrontendDir = Join-Path $RepoRoot 'frontend\dashboards'

if (-not $BuildTag) {
    $BuildTag = 'rc-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

if (-not $ApiBaseUrl) {
    throw 'ApiBaseUrl is required.'
}

Push-Location $RepoRoot

$env:VITE_BUILD_SHA = (git rev-parse --short HEAD).Trim()
$env:VITE_BUILD_TAG = $BuildTag
$env:VITE_BUILD_TIME = [DateTime]::UtcNow.ToString('o')
$env:VITE_API_BASE_URL = $ApiBaseUrl

Write-Host '== FRONTEND RC LOCK =='
Write-Host "RepoRoot: $RepoRoot"
Write-Host "Build SHA: $env:VITE_BUILD_SHA"
Write-Host "Build Tag: $env:VITE_BUILD_TAG"
Write-Host "Build Time: $env:VITE_BUILD_TIME"
Write-Host "API Base URL: $env:VITE_API_BASE_URL"
Write-Host ''

Set-Location $FrontendDir

if (Test-Path 'package-lock.json') {
    npm ci
}
else {
    npm install
}

npm run test:contracts
npm run test:unit
npm run build

Set-Location $RepoRoot
node scripts/release/verify-frontend-rc.mjs

Write-Host ''
Write-Host '== RC LOCK COMPLETE =='
Write-Host 'Artifact: frontend/dashboards/dist/release-candidate.json'
Write-Host "Tag candidate: $env:VITE_BUILD_TAG"

Pop-Location
