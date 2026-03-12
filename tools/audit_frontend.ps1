# tools/audit_frontend.ps1
# Crown2026 Frontend Hygiene Audit
# Checks for hard-coded API URLs, missing env config, and verifies build works.
#
# Usage (standalone):
#   pwsh -File tools/audit_frontend.ps1
#
# Called automatically by audit_all.ps1 unless -NoUI is passed.

$ErrorActionPreference = "Stop"

function Step($name, [scriptblock]$fn) {
  Write-Host ""
  Write-Host "=== $name ===" -ForegroundColor Cyan
  & $fn
  Write-Host "OK: $name" -ForegroundColor Green
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$fe = "frontend/dashboards"
if (-not (Test-Path $fe)) {
  Write-Host "frontend/dashboards not found; skipping frontend audit" -ForegroundColor Yellow
  exit 0
}

Step "Node / npm version" {
  node --version
  npm --version
}

Step "No hard-coded API base URLs in source" {
  $srcGlobs = @(
    "$fe/src/**/*.js",
    "$fe/src/**/*.jsx",
    "$fe/src/**/*.ts",
    "$fe/src/**/*.tsx"
  )
  $dangerousPatterns = "http://localhost:8000|https://localhost:|/api/v1|crown-api\.azurewebsites|REACT_APP_API_URL\s*="
  $hits = @()
  foreach ($glob in $srcGlobs) {
    $files = Get-ChildItem -Path $glob -ErrorAction SilentlyContinue
    if ($files) {
      $found = Select-String -Path $files -Pattern $dangerousPatterns -ErrorAction SilentlyContinue
      if ($found) { $hits += $found }
    }
  }
  if ($hits) {
    Write-Host "Hard-coded API refs detected:" -ForegroundColor Yellow
    $hits | Select-Object Path, LineNumber, Line | Format-Table -AutoSize
    throw "Hard-coded API refs found. Ensure API base URL comes from environment variables (VITE_API_BASE or REACT_APP_API_URL)."
  }
}

Step "package.json has required scripts" {
  $pkg = Get-Content "$fe/package.json" -Raw | ConvertFrom-Json
  $scripts = $pkg.scripts.PSObject.Properties.Name
  $required = @("build", "dev", "test")
  $missing = $required | Where-Object { $_ -notin $scripts }
  if ($missing) {
    Write-Host "WARN: Missing scripts in package.json: $($missing -join ', ')" -ForegroundColor Yellow
  }
  if ("build" -notin $scripts) {
    throw "package.json is missing required 'build' script."
  }
}

Step "No .env files committed (secrets hygiene)" {
  $envFiles = @(".env", ".env.local", ".env.production", ".env.staging") |
  ForEach-Object { Join-Path $fe $_ } |
  Where-Object { Test-Path $_ }
  if ($envFiles) {
    # Verify they are .gitignored - fail if tracked by git
    foreach ($ef in $envFiles) {
      $tracked = git ls-files --error-unmatch $ef 2>$null
      if ($LASTEXITCODE -eq 0) {
        throw "Committed .env file detected: $ef - remove from git tracking and add to .gitignore"
      }
    }
    Write-Host "  .env file(s) exist but are not tracked by git (OK)" -ForegroundColor DarkGray
  }
}

Step "npm install (ci)" {
  Push-Location $fe
  try {
    npm ci --silent
  }
  finally {
    Pop-Location
  }
}

Step "Frontend build" {
  Push-Location $fe
  try {
    npm run build --silent
  }
  finally {
    Pop-Location
  }
}

Write-Host ""
Write-Host "Frontend audit complete." -ForegroundColor Green
