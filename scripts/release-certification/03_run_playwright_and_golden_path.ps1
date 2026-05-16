param(
  [string]$OutputDir,
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$FrontendUrl = "http://127.0.0.1:3000",
  [string]$SandboxAdminEmail = "admin@heritage.test",
  [string]$SandboxAdminPassword = "Crown2026!",
  [string]$SandboxSecondAdminEmail = "admin@harvest.test",
  [string]$SandboxSecondAdminPassword = "Crown2026!",
  [string]$SchoolAdminRoute = "/school-admin-dashboard"
)

$ErrorActionPreference = "Stop"

$resolvedOutputDir = (Resolve-Path $OutputDir).Path

$env:CERT_BASE_URL = $BaseUrl
$env:CERT_FRONTEND_URL = $FrontendUrl
$env:CERT_SANDBOX_ADMIN_EMAIL = $SandboxAdminEmail
$env:CERT_SANDBOX_ADMIN_PASSWORD = $SandboxAdminPassword
$env:CERT_SANDBOX_SECOND_ADMIN_EMAIL = $SandboxSecondAdminEmail
$env:CERT_SANDBOX_SECOND_ADMIN_PASSWORD = $SandboxSecondAdminPassword
$env:CERT_SCHOOL_ADMIN_ROUTE = $SchoolAdminRoute

if (Test-Path "tests/test_golden_path.py") {
  pytest tests/test_golden_path.py -v *> (Join-Path $resolvedOutputDir "03_pytest_golden_path.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "tests/test_golden_path.py failed"
  }
}
if (Test-Path "tests/test_tenant_isolation.py") {
  pytest tests/test_tenant_isolation.py -v *> (Join-Path $resolvedOutputDir "03_pytest_tenant_isolation.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "tests/test_tenant_isolation.py failed"
  }
}

Push-Location "frontend/dashboards"
$npx = Get-Command npx -ErrorAction SilentlyContinue
if (-not $npx) {
  Pop-Location
  throw "npx is required for Playwright certification."
}

npx playwright test tests/e2e/sandbox-admin-dashboard-cert.spec.ts --reporter=line *> (Join-Path $resolvedOutputDir "03_playwright_sandbox_admin.txt")
if ($LASTEXITCODE -ne 0) {
  throw "sandbox-admin-dashboard-cert.spec.ts failed"
}
if (Test-Path "tests/investor-golden-path.spec.ts") {
  npx playwright test tests/investor-golden-path.spec.ts --reporter=line *> (Join-Path $resolvedOutputDir "03_playwright_investor_golden_path.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "investor-golden-path.spec.ts failed"
  }
}
if (Test-Path "tests/release-auth-golden-path.spec.ts") {
  npx playwright test tests/release-auth-golden-path.spec.ts --reporter=line *> (Join-Path $resolvedOutputDir "03_playwright_release_auth.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "release-auth-golden-path.spec.ts failed"
  }
}
Pop-Location

$summary = [pscustomobject]@{
  sandbox_admin_route = $SchoolAdminRoute
  primary_admin       = $SandboxAdminEmail
  second_admin        = $SandboxSecondAdminEmail
}
$summary | ConvertTo-Json -Depth 4 | Out-File (Join-Path $resolvedOutputDir "03_playwright_summary.json") -Encoding utf8
