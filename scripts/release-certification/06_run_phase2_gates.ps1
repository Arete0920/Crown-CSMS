param(
  [string]$OutputDir,
  [string]$FrontendUrl = "http://127.0.0.1:3000"
)

$ErrorActionPreference = "Stop"

$resolvedOutputDir = (Resolve-Path $OutputDir).Path

$env:CERT_FRONTEND_URL = $FrontendUrl
$env:CERT_SANDBOX_MODE = "1"

$backendOut = Join-Path $resolvedOutputDir "06_pytest_reporting_exports_gate.txt"
pytest backend/tests/test_reporting_exports_gate.py -v *> $backendOut
if ($LASTEXITCODE -ne 0) {
  throw "test_reporting_exports_gate.py failed"
}

Push-Location "frontend/dashboards"
$npx = Get-Command npx -ErrorAction SilentlyContinue
if (-not $npx) {
  Pop-Location
  throw "npx is required for sandbox route regression suite."
}

npx playwright test tests/e2e/sandbox-role-route-regression.spec.ts --reporter=line *> (Join-Path $resolvedOutputDir "06_playwright_sandbox_role_routes.txt")
if ($LASTEXITCODE -ne 0) {
  throw "sandbox-role-route-regression.spec.ts failed"
}
Pop-Location

$summary = [pscustomobject]@{
  backend_reporting_export_gate = "executed"
  sandbox_role_route_regression = "executed"
}
$summary | ConvertTo-Json -Depth 4 | Out-File (Join-Path $resolvedOutputDir "06_phase2_summary.json") -Encoding utf8
