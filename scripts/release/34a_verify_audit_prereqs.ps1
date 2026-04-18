$ErrorActionPreference = "Continue"

Write-Host "=== PYTHON ==="
python --version 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "python not available" }

Write-Host "=== GITHUB CLI ==="
gh auth status

Write-Host "=== DJANGO MANAGE CHECK ==="
if (Test-Path "backend/manage.py") {
  python backend/manage.py check
  python backend/manage.py showmigrations
  python backend/manage.py help | Select-String "show_urls"
} elseif (Test-Path "manage.py") {
  python manage.py check
  python manage.py showmigrations
  python manage.py help | Select-String "show_urls"
} else {
  Write-Host "manage.py not found"
}