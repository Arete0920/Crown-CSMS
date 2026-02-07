# install-hooks.ps1
# Installs Git hooks from scripts/hooks/ into .git/hooks/
# Run once after cloning the repo

$ErrorActionPreference = "Stop"

Write-Host "`n🔧 Installing Git hooks..." -ForegroundColor Cyan

$hooksSource = Join-Path $PSScriptRoot "hooks"
$hooksTarget = Join-Path (Get-Location) ".git\hooks"

if (-not (Test-Path $hooksTarget)) {
    Write-Host "❌ Error: .git/hooks not found. Are you in the repo root?" -ForegroundColor Red
    exit 1
}

# Copy pre-commit hook
$preCommitSource = Join-Path $hooksSource "pre-commit"
$preCommitTarget = Join-Path $hooksTarget "pre-commit"

if (-not (Test-Path $preCommitSource)) {
    Write-Host "❌ Error: $preCommitSource not found" -ForegroundColor Red
    exit 1
}

Copy-Item -Force $preCommitSource $preCommitTarget
Write-Host "✓ Installed pre-commit hook" -ForegroundColor Green

# Make executable (Git Bash compatibility)
if (Get-Command "bash" -ErrorAction SilentlyContinue) {
    bash -c "chmod +x '$($preCommitTarget -replace '\\', '/')'"
    Write-Host "✓ Made hook executable (bash)" -ForegroundColor Green
}

Write-Host "`n✅ Git hooks installed successfully!" -ForegroundColor Green
Write-Host "   Hooks will run automatically on commit." -ForegroundColor Gray
Write-Host "   To bypass (NOT RECOMMENDED): git commit --no-verify" -ForegroundColor Yellow
