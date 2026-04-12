$ErrorActionPreference = "Stop"

$verify = "audit-artifacts\release-verify"
$manifest = "audit-artifacts\release-manifest"
New-Item -ItemType Directory -Force -Path $verify, $manifest | Out-Null

Write-Host "=== SCHEMA INVENTORY BASELINE ===" -ForegroundColor Cyan
python scripts\release\schema_w002_inventory.py 2>&1 | Tee-Object -FilePath "$verify\30_schema_inventory_baseline.txt"

Write-Host "=== FUNCTION VIEW AUTO-PATCH ===" -ForegroundColor Cyan
python scripts\release\patch_schema_function_views.py 2>&1 | Tee-Object -FilePath "$verify\31_function_view_patch.txt"

Write-Host "=== APIVIEW METHOD AUTO-PATCH ===" -ForegroundColor Cyan
python scripts\release\patch_schema_apiview_methods.py 2>&1 | Tee-Object -FilePath "$verify\32_apiview_patch.txt"

Write-Host "=== PY COMPILE PATCHED FILES ===" -ForegroundColor Cyan
$patchedJson = @(
  "audit-artifacts\release-verify\schema_function_patch_report.json",
  "audit-artifacts\release-verify\schema_apiview_patch_report.json"
)
$pyFiles = @()
foreach ($jsonPath in $patchedJson) {
  if (Test-Path $jsonPath) {
    $items = Get-Content $jsonPath | ConvertFrom-Json
    foreach ($item in $items) {
      if ($item.changed -eq $true) {
        $pyFiles += $item.file
      }
    }
  }
}
$pyFiles = $pyFiles | Sort-Object -Unique
if ($pyFiles.Count -gt 0) {
  python -m py_compile $pyFiles 2>&1 | Tee-Object -FilePath "$verify\33_py_compile_schema_patch.txt"
} else {
  "No changed Python files from schema patch pass." | Out-File "$verify\33_py_compile_schema_patch.txt"
}

Write-Host "=== DEPLOY CHECK AFTER PATCH ===" -ForegroundColor Cyan
if (Test-Path "backend\manage.py") {
  python backend\manage.py check --deploy 2>&1 | Tee-Object -FilePath "$verify\34_manage_check_deploy_after_schema_patch.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check --deploy 2>&1 | Tee-Object -FilePath "$verify\34_manage_check_deploy_after_schema_patch.txt"
} else {
  "manage.py not found" | Out-File "$verify\34_manage_check_deploy_after_schema_patch.txt"
}

Write-Host "=== SCHEMA INVENTORY AFTER PATCH ===" -ForegroundColor Cyan
python scripts\release\schema_w002_inventory.py 2>&1 | Tee-Object -FilePath "$verify\35_schema_inventory_after_patch.txt"

Write-Host "=== SPECTACULAR EXPORT ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "docs\openapi" | Out-Null
if (Test-Path "backend\manage.py") {
  python backend\manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$verify\36_spectacular_export.txt"
} elseif (Test-Path "manage.py") {
  python manage.py spectacular --file docs/openapi/crown-openapi.yaml 2>&1 | Tee-Object -FilePath "$verify\36_spectacular_export.txt"
} else {
  "manage.py not found" | Out-File "$verify\36_spectacular_export.txt"
}

Write-Host "=== ROUTE CATALOG ===" -ForegroundColor Cyan
python scripts\release\route_catalog_release.py 2>&1 | Tee-Object -FilePath "$manifest\11_route_catalog_release.txt"

Write-Host "=== SCHEMA PROGRESS DOC ===" -ForegroundColor Cyan
python scripts\release\update_schema_progress_doc.py 2>&1 | Tee-Object -FilePath "$verify\37_schema_progress_doc.txt"

Write-Host "=== SCHEMA GATE ===" -ForegroundColor Cyan
python scripts\release\schema_gate.py 2>&1 | Tee-Object -FilePath "$verify\38_schema_gate.txt"

Write-Host "=== PYTEST ===" -ForegroundColor Cyan
pytest -q tests/test_schema_governance_assets.py 2>&1 | Tee-Object -FilePath "$verify\39_pytest_schema_governance.txt"

Write-Host "=== FRONTEND SMOKE ===" -ForegroundColor Cyan
if (Test-Path "frontend\dashboards\package.json") {
  Push-Location "frontend\dashboards"
  $prevEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"

  npm ci 2>&1 | Tee-Object -FilePath "..\..\$verify\40_npm_ci_schema_green_pass.txt"
  if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }

  npm run test --if-present 2>&1 | Tee-Object -FilePath "..\..\$verify\41_frontend_test_schema_green_pass.txt"
  if ($LASTEXITCODE -ne 0) { throw "npm test failed with exit code $LASTEXITCODE" }

  $ErrorActionPreference = $prevEap
  Pop-Location
} else {
  "frontend/dashboards/package.json not found" | Out-File "$verify\40_npm_ci_schema_green_pass.txt"
}

@"
# SHIP CANDIDATE 47-61

Generated: $(Get-Date -Format s)

Artifacts:
- audit-artifacts/release-verify
- audit-artifacts/release-manifest
- docs/release/PRIORITY_47_61_TO_GREEN.md
- docs/release/SCHEMA_W002_PROGRESS.md
- docs/openapi/crown-openapi.yaml

Exit checks:
- schema_w002_summary.json present
- schema_function_patch_report.json present
- schema_apiview_patch_report.json present
- route catalog present
- schema gate passes against SCHEMA_W002_BUDGET.json
- py_compile passes on changed files
- spectacular export writes crown-openapi.yaml
"@ | Out-File "docs\release\SHIP_CANDIDATE_47_61.md" -Encoding utf8

Write-Host "Schema green pass complete." -ForegroundColor Green