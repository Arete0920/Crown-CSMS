$ErrorActionPreference = "Stop"

$verify = "audit-artifacts\release-verify"
$manifest = "audit-artifacts\release-manifest"
New-Item -ItemType Directory -Force -Path $verify, $manifest | Out-Null

Write-Host "=== PATCH GUARD ===" -ForegroundColor Cyan
python scripts\release\release_patch_guard.py 2>&1 | Tee-Object -FilePath "$verify\20_patch_guard.txt"

Write-Host "=== PACKAGE READINESS ===" -ForegroundColor Cyan
python scripts\release\verify_required_release_packages.py 2>&1 | Tee-Object -FilePath "$verify\21_package_readiness.txt"

Write-Host "=== ROUTE CATALOG ===" -ForegroundColor Cyan
python scripts\release\route_catalog.py 2>&1 | Tee-Object -FilePath "$manifest\09_route_catalog.txt"

Write-Host "=== SEED / FIXTURE PARITY ===" -ForegroundColor Cyan
python scripts\release\seed_fixture_parity.py 2>&1 | Tee-Object -FilePath "$verify\22_seed_fixture_parity.txt"

Write-Host "=== WORKFLOW PREFLIGHT ===" -ForegroundColor Cyan
python scripts\release\workflow_preflight.py 2>&1 | Tee-Object -FilePath "$manifest\10_workflow_preflight.txt"

Write-Host "=== PYTEST ROUTE CONTRACTS ===" -ForegroundColor Cyan
pytest -q tests/test_release_route_contracts.py tests/test_release_closeout_phase2.py tests/test_mock_seed_scan_output.py 2>&1 | Tee-Object -FilePath "$verify\23_pytest_route_contracts.txt"

Write-Host "=== COMPUWERX SANDBOX PROOF ===" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts\release\compuwerx_sandbox_capture.ps1

Write-Host "=== FRONTEND RELEASE TESTS ===" -ForegroundColor Cyan
if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  npm ci 2>&1 | Tee-Object -FilePath "..\..\$verify\24_npm_ci_release_doctor.txt"
  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$verify\25_frontend_unit_release_doctor.txt"
  npx playwright install --with-deps 2>&1 | Tee-Object -FilePath "..\..\$verify\26_playwright_install_release_doctor.txt"
  npx playwright test tests/release-auth-golden-path.spec.ts 2>&1 | Tee-Object -FilePath "..\..\$verify\27_playwright_auth_golden_path.txt"
  npx playwright test tests/release-accessibility.spec.ts 2>&1 | Tee-Object -FilePath "..\..\$verify\28_playwright_accessibility.txt"
  Pop-Location
} else {
  "frontend/dashboards/package.json not found" | Out-File "$verify\24_npm_ci_release_doctor.txt"
}

@"
# SHIP CANDIDATE 32â€“46

Generated: $(Get-Date -Format s)

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_32_46_TO_GREEN.md
- docs/release/RELEASE_ENV_MATRIX.md

Exit checks:
- release_patch_guard.json shows duplicate insertions normalized
- release_package_readiness.json present
- route_catalog.json present
- workflow_preflight.json green
- seed_fixture_parity.json green
- route contract pytest green
- auth golden path and accessibility smoke green
- compuwerx sandbox artifact present
"@ | Out-File "docs\release\SHIP_CANDIDATE_32_46.md" -Encoding utf8

Write-Host "Release doctor complete." -ForegroundColor Green