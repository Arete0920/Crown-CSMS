$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontendDir = Join-Path $repoRoot 'frontend\dashboards'

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found at $frontendDir"
}

Set-Location $frontendDir
npm run dev -- --host 127.0.0.1 --port 3000
