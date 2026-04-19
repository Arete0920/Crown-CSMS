$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
if ($null -ne (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)) {
  $PSNativeCommandUseErrorActionPreference = $false
}
. "$PSScriptRoot\..\Get-RequiredEnv.ps1"
$env:DJANGO_SECRET_KEY = Get-RequiredEnv "DJANGO_SECRET_KEY"
if (-not $env:DJANGO_DEBUG) { $env:DJANGO_DEBUG = "0" }
if (-not $env:DJANGO_ENV) { $env:DJANGO_ENV = "production" }
if (-not $env:CROWN_ENV) { $env:CROWN_ENV = "prod" }

$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

python scripts\release\mock_seed_scan.py
python scripts\release\seed_release_demo.py

powershell -ExecutionPolicy Bypass -File scripts\release\22_release_manifest.ps1
powershell -ExecutionPolicy Bypass -File scripts\release\23_workflow_inventory.ps1

if (Test-Path "backend\manage.py") {
  python backend\manage.py check 2>&1 | Tee-Object -FilePath "$base\10_manage_check_phase2.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check 2>&1 | Tee-Object -FilePath "$base\10_manage_check_phase2.txt"
}

pytest -q tests/test_release_closeout_phase2.py tests/test_mock_seed_scan_output.py 2>&1 | Tee-Object -FilePath "$base\11_pytest_phase2.txt"

if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  npm ci 2>&1 | Tee-Object -FilePath "..\..\$base\12_npm_ci_phase2.txt"
  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$base\13_frontend_tests_phase2.txt"
  npx playwright test tests/release-closeout-routes.spec.ts 2>&1 | Tee-Object -FilePath "..\..\$base\14_playwright_routes_phase2.txt"
  Pop-Location
}

powershell -ExecutionPolicy Bypass -File scripts\release\24_verify_portals_and_exports.ps1

@"
# SHIP CANDIDATE

Generated: $(Get-Date -Format s)

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_16_31_TO_GREEN.md

Exit criteria:
- pytest phase2 green
- frontend smoke green
- mock_seed_scan shows 0 hits or all hits intentionally remediated
- release-closeout status endpoint green
- transcript / report-card / discipline / board PDF endpoints return 200
"@ | Out-File "docs\release\SHIP_CANDIDATE.md" -Encoding utf8

Write-Host "Ship candidate bundle complete."