$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
if ($null -ne (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)) {
  $PSNativeCommandUseErrorActionPreference = $false
}
if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = "copilot-local-check-only" }
if (-not $env:DJANGO_DEBUG) { $env:DJANGO_DEBUG = "0" }
if (-not $env:DJANGO_ENV) { $env:DJANGO_ENV = "production" }
if (-not $env:CROWN_ENV) { $env:CROWN_ENV = "prod" }

$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

Write-Host "=== BACKEND CHECKS ===" -ForegroundColor Cyan
if (Test-Path "backend\manage.py") {
  python backend\manage.py check 2>&1 | Tee-Object -FilePath "$base\01_manage_check.txt"
  python backend\manage.py showmigrations 2>&1 | Tee-Object -FilePath "$base\02_showmigrations.txt"
  python backend\manage.py check --deploy 2>&1 | Tee-Object -FilePath "$base\03_deploy_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check 2>&1 | Tee-Object -FilePath "$base\01_manage_check.txt"
  python manage.py showmigrations 2>&1 | Tee-Object -FilePath "$base\02_showmigrations.txt"
  python manage.py check --deploy 2>&1 | Tee-Object -FilePath "$base\03_deploy_check.txt"
} else {
  "manage.py not found" | Out-File "$base\01_manage_check.txt"
}

Write-Host "=== PYTEST ===" -ForegroundColor Cyan
pytest -q tests/test_release_tenant_and_urls.py 2>&1 | Tee-Object -FilePath "$base\04_pytest_release_smoke.txt"

Write-Host "=== URL AND HEALTH CHECKS ===" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts\release\11_verify_import_and_migrations.ps1
powershell -ExecutionPolicy Bypass -File scripts\release\12_verify_backend_urls_and_health.ps1
powershell -ExecutionPolicy Bypass -File scripts\release\13_verify_workflows_and_deploy_risk.ps1

Write-Host "=== OPENAPI EXPORT ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "docs\openapi" | Out-Null
if (Test-Path "backend\manage.py") {
  python backend\manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$base\05_openapi_export.txt"
} elseif (Test-Path "manage.py") {
  python manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$base\05_openapi_export.txt"
} else {
  "manage.py not found" | Out-File "$base\05_openapi_export.txt"
}

Write-Host "=== FRONTEND SMOKE ===" -ForegroundColor Cyan
if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  npm ci 2>&1 | Tee-Object -FilePath "..\..\$base\06_npm_ci.txt"
  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$base\07_frontend_test.txt"
  Pop-Location
} else {
  "frontend/dashboards/package.json not found" | Out-File "$base\06_npm_ci.txt"
}

Write-Host "=== FILE PRESENCE ===" -ForegroundColor Cyan
$required = @(
  "docs/release/PRIORITY_15_TO_GREEN.md",
  "docs/release/BRANCH_PROTECTION_REQUIRED_CHECKS.md",
  "docs/release/LOAD_TEST_REPORT_TEMPLATE.md",
  ".github/workflows/dependency-audit.yml",
  ".github/workflows/release-verify.yml",
  "tests/test_release_tenant_and_urls.py",
  "scripts/load/locustfile.py",
  "frontend/dashboards/tests/investor-golden-path.spec.ts",
  "frontend/dashboards/src/components/exports/ExportButton.tsx",
  "frontend/dashboards/src/components/exports/BulkExportMenu.tsx"
)

$result = foreach ($f in $required) {
  [pscustomobject]@{
    File = $f
    Exists = Test-Path $f
    Size = if (Test-Path $f) { (Get-Item $f).Length } else { 0 }
  }
}
$result | Export-Csv "$base\08_required_files.csv" -NoTypeInformation

Write-Host "DONE: $base" -ForegroundColor Green