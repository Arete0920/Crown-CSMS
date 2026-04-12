$ErrorActionPreference = "Stop"

$base = "audit-artifacts\freeze-reconcile"
$docsDir = "docs\release"
New-Item -ItemType Directory -Force -Path $base | Out-Null

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, (New-Object System.Text.UTF8Encoding($false)))
}

$expected = @(
    # restore generators
    "scripts/release/fix_15_to_green.ps1",
    "scripts/release/fix_16_31_to_green.ps1",
    "scripts/release/fix_32_46_to_green.ps1",
    "scripts/release/fix_47_61_to_green.ps1",
    "scripts/release/28_run_next_release_sequence.ps1",

    # release verify chain
    "scripts/release/20_release_verify.ps1",
    "scripts/release/25_build_ship_candidate.ps1",
    "scripts/release/26_release_doctor.ps1",
    "scripts/release/27_schema_green_pass.ps1",

    # schema governance
    "scripts/release/schema_w002_inventory.py",
    "scripts/release/patch_schema_function_views.py",
    "scripts/release/patch_schema_apiview_methods.py",
    "scripts/release/schema_gate.py",
    "scripts/release/route_catalog_release.py",
    "scripts/release/update_schema_progress_doc.py",

    # closeout tools
    "scripts/release/release_patch_guard.py",
    "scripts/release/verify_required_release_packages.py",
    "scripts/release/route_catalog.py",
    "scripts/release/mock_seed_scan.py",
    "scripts/release/seed_release_demo.py",
    "scripts/release/seed_fixture_parity.py",
    "scripts/release/workflow_preflight.py",
    "scripts/release/compuwerx_sandbox_capture.ps1",
    "scripts/release/11_verify_import_and_migrations.ps1",
    "scripts/release/12_verify_backend_urls_and_health.ps1",
    "scripts/release/13_verify_workflows_and_deploy_risk.ps1",
    "scripts/load/locustfile.py",

    # backend package
    "release_closeout/__init__.py",
    "release_closeout/apps.py",
    "release_closeout/pdf_utils.py",
    "release_closeout/services.py",
    "release_closeout/views.py",
    "release_closeout/urls.py",
    "backend/core/api_schema.py",

    # docs
    "docs/release/PRIORITY_15_TO_GREEN.md",
    "docs/release/PRIORITY_16_31_TO_GREEN.md",
    "docs/release/PRIORITY_32_46_TO_GREEN.md",
    "docs/release/PRIORITY_47_61_TO_GREEN.md",
    "docs/release/BRANCH_PROTECTION_REQUIRED_CHECKS.md",
    "docs/release/LOAD_TEST_REPORT_TEMPLATE.md",
    "docs/release/RELEASE_ENV_MATRIX.md",
    "docs/release/SCHEMA_W002_BUDGET.json",
    "docs/release/SCHEMA_W002_PROGRESS.md",
    "docs/release/SHIP_CANDIDATE.md",
    "docs/release/SHIP_CANDIDATE_32_46.md",
    "docs/release/SHIP_CANDIDATE_47_61.md",
    "docs/release/NEXT_ACTION_SUMMARY.md",
    "docs/release/TOP_W002_OFFENDERS_PRE.md",
    "docs/release/TOP_W002_OFFENDERS_POST.md",

    # workflows
    ".github/workflows/dependency-audit.yml",
    ".github/workflows/release-verify.yml",
    ".github/workflows/schema-governance.yml",

    # tests
    "tests/test_release_tenant_and_urls.py",
    "tests/test_release_closeout_phase2.py",
    "tests/test_mock_seed_scan_output.py",
    "tests/test_release_route_contracts.py",
    "tests/test_schema_governance_assets.py",

    # frontend
    "frontend/dashboards/src/lib/releaseApi.ts",
    "frontend/dashboards/src/components/exports/ExportButton.tsx",
    "frontend/dashboards/src/components/exports/BulkExportMenu.tsx",
    "frontend/dashboards/src/components/release/Closeout16to31Panel.tsx",
    "frontend/dashboards/src/components/release/ReleaseExportButton.tsx",
    "frontend/dashboards/src/components/release/ReleaseStatusMatrix.tsx",
    "frontend/dashboards/src/components/release/SchemaStatusWidget.tsx",
    "frontend/dashboards/tests/investor-golden-path.spec.ts",
    "frontend/dashboards/tests/release-closeout-routes.spec.ts",
    "frontend/dashboards/tests/release-closeout-widget.test.tsx",
    "frontend/dashboards/tests/release-auth-golden-path.spec.ts",
    "frontend/dashboards/tests/release-accessibility.spec.ts",
    "frontend/dashboards/tests/schema-status-widget.test.tsx"
)

$inventory = foreach ($path in $expected) {
    $exists = Test-Path $path
    [pscustomobject]@{
        File = $path
        Exists = $exists
        Size = if ($exists) { (Get-Item $path).Length } else { 0 }
        LastWriteTime = if ($exists) { (Get-Item $path).LastWriteTime.ToString("s") } else { "" }
    }
}

$inventory | Export-Csv "$base\01_expected_file_inventory.csv" -NoTypeInformation

$missing = $inventory | Where-Object { -not $_.Exists }
$present = $inventory | Where-Object { $_.Exists }

$missing | Export-Csv "$base\02_missing_files.csv" -NoTypeInformation
$present | Export-Csv "$base\03_present_files.csv" -NoTypeInformation

"=== GIT STATUS ===" | Out-File "$base\04_git_status.txt"
git status --short | Add-Content "$base\04_git_status.txt"

"=== CURRENT BRANCH ===" | Out-File "$base\05_git_branch.txt"
git branch --show-current | Add-Content "$base\05_git_branch.txt"

"=== RECENT COMMITS ===" | Out-File "$base\06_recent_commits.txt"
git log --oneline -20 | Add-Content "$base\06_recent_commits.txt"

"=== RELEASE SCRIPTS PRESENT ===" | Out-File "$base\07_release_script_presence.txt"
$inventory |
    Where-Object { $_.File -like "scripts/release/*" -or $_.File -like "scripts/load/*" } |
    Format-Table -AutoSize |
    Out-String |
    Add-Content "$base\07_release_script_presence.txt"

"=== DOCS PRESENT ===" | Out-File "$base\08_release_docs_presence.txt"
$inventory |
    Where-Object { $_.File -like "docs/release/*" } |
    Format-Table -AutoSize |
    Out-String |
    Add-Content "$base\08_release_docs_presence.txt"

"=== FRONTEND PRESENT ===" | Out-File "$base\09_frontend_presence.txt"
$inventory |
    Where-Object { $_.File -like "frontend/dashboards/*" } |
    Format-Table -AutoSize |
    Out-String |
    Add-Content "$base\09_frontend_presence.txt"

"=== BACKEND PACKAGE PRESENT ===" | Out-File "$base\10_backend_presence.txt"
$inventory |
    Where-Object { $_.File -like "release_closeout/*" -or $_.File -eq "backend/core/api_schema.py" } |
    Format-Table -AutoSize |
    Out-String |
    Add-Content "$base\10_backend_presence.txt"

# last known freeze-progress evidence
$knownEvidence = @(
    "_tmp_prod_schema_batch6_check.txt",
    "_tmp_prod_schema_batch7_check.txt",
    "_tmp_prod_schema_batch8_check.txt",
    "docs/reviews/PRODUCTION_RELEASE_PRIORITY_CHECKLIST.md",
    "audit-artifacts/release-verify/schema_w002_summary.json",
    "audit-artifacts/release-verify/schema_function_patch_report.json",
    "audit-artifacts/release-verify/schema_apiview_patch_report.json",
    "audit-artifacts/release-manifest/release_route_catalog.json",
    "docs/openapi/crown-openapi.yaml"
)

$evidenceInventory = foreach ($path in $knownEvidence) {
    $exists = Test-Path $path
    [pscustomobject]@{
        File = $path
        Exists = $exists
        Size = if ($exists) { (Get-Item $path).Length } else { 0 }
        LastWriteTime = if ($exists) { (Get-Item $path).LastWriteTime.ToString("s") } else { "" }
    }
}
$evidenceInventory | Export-Csv "$base\11_known_evidence_inventory.csv" -NoTypeInformation

# parse W002 evidence if present
$schemaSummary = [ordered]@{
    Batch6Total = ""
    Batch6W002 = ""
    Batch7Total = ""
    Batch7W002 = ""
    Batch8Total = ""
    Batch8W002 = ""
    LatestSummaryW002 = ""
    LatestSummaryBudgetPass = ""
}

function Parse-W002File {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return @{ Total = ""; W002 = "" }
    }

    $text = Get-Content $Path -Raw
    $total = ""
    $w002 = ""

    $m1 = [regex]::Match($text, "System check identified\s+([0-9]+)\s+issue")
    if ($m1.Success) { $total = $m1.Groups[1].Value }

    $w002 = ([regex]::Matches($text, "drf_spectacular\.W002")).Count
    return @{ Total = $total; W002 = $w002 }
}

$b6 = Parse-W002File "_tmp_prod_schema_batch6_check.txt"
$b7 = Parse-W002File "_tmp_prod_schema_batch7_check.txt"
$b8 = Parse-W002File "_tmp_prod_schema_batch8_check.txt"

$schemaSummary.Batch6Total = $b6.Total
$schemaSummary.Batch6W002 = $b6.W002
$schemaSummary.Batch7Total = $b7.Total
$schemaSummary.Batch7W002 = $b7.W002
$schemaSummary.Batch8Total = $b8.Total
$schemaSummary.Batch8W002 = $b8.W002

if (Test-Path "audit-artifacts/release-verify/schema_w002_summary.json") {
    $s = Get-Content "audit-artifacts/release-verify/schema_w002_summary.json" | ConvertFrom-Json
    $schemaSummary.LatestSummaryW002 = $s.total_w002
    $schemaSummary.LatestSummaryBudgetPass = $s.budget_pass
}

$schemaSummary | ConvertTo-Json -Depth 5 | Out-File "$base\12_schema_progress_snapshot.json" -Encoding utf8

# verify package.json / requirements presence
$pkgCheck = [ordered]@{
    FrontendPackageJson = Test-Path "frontend/dashboards/package.json"
    FrontendPackageLock = Test-Path "frontend/dashboards/package-lock.json"
    BackendRequirements = Test-Path "backend/requirements.txt"
    RootRequirements = Test-Path "requirements.txt"
    ManagePyBackend = Test-Path "backend/manage.py"
    ManagePyRoot = Test-Path "manage.py"
}
$pkgCheck | ConvertTo-Json -Depth 5 | Out-File "$base\13_runtime_presence.json" -Encoding utf8

# build restore decision
$restoreFix15 = -not (Test-Path "scripts/release/fix_15_to_green.ps1")
$restoreFix16 = -not (Test-Path "scripts/release/fix_16_31_to_green.ps1")
$restoreFix32 = -not (Test-Path "scripts/release/fix_32_46_to_green.ps1")
$restoreFix47 = -not (Test-Path "scripts/release/fix_47_61_to_green.ps1")
$restoreSeq = -not (Test-Path "scripts/release/28_run_next_release_sequence.ps1")

$summary = @()
$summary += "# VS CODE FREEZE RECONCILIATION"
$summary += ""
$summary += "## Current State"
$summary += ""
$summary += "- Expected files checked: $($inventory.Count)"
$summary += "- Present: $($present.Count)"
$summary += "- Missing: $($missing.Count)"
$summary += ""
$summary += "## Last Known Schema Progress"
$summary += ""
$summary += "- Batch 6: total=$($schemaSummary.Batch6Total) W002=$($schemaSummary.Batch6W002)"
$summary += "- Batch 7: total=$($schemaSummary.Batch7Total) W002=$($schemaSummary.Batch7W002)"
$summary += "- Batch 8: total=$($schemaSummary.Batch8Total) W002=$($schemaSummary.Batch8W002)"
if ($schemaSummary.LatestSummaryW002 -ne "") {
    $summary += "- Latest summary JSON W002: $($schemaSummary.LatestSummaryW002)"
    $summary += "- Latest budget pass: $($schemaSummary.LatestSummaryBudgetPass)"
}
$summary += ""
$summary += "## Restore Decision"
$summary += ""
$summary += "- Restore fix_15 pack: $restoreFix15"
$summary += "- Restore fix_16_31 pack: $restoreFix16"
$summary += "- Restore fix_32_46 pack: $restoreFix32"
$summary += "- Restore fix_47_61 pack: $restoreFix47"
$summary += "- Restore next-sequence pack: $restoreSeq"
$summary += ""
$summary += "## Required Next Action"
$summary += ""
if ($missing.Count -gt 0) {
    $summary += "Missing files exist. Recreate missing generator scripts first, then rerun all fix packs."
}
else {
    $summary += "Core files appear present. Run the verification chain and inspect failures."
}
$summary += ""
$summary += "## Exact Next Commands"
$summary += ""
$summary += "1. Restore any missing fix packs."
$summary += "2. Run fix_15_to_green.ps1"
$summary += "3. Run fix_16_31_to_green.ps1"
$summary += "4. Run fix_32_46_to_green.ps1"
$summary += "5. Run fix_47_61_to_green.ps1"
$summary += "6. Run 28_run_next_release_sequence.ps1"
$summary += "7. Run 27_schema_green_pass.ps1"
$summary += "8. Run 20_release_verify.ps1"
$summary += "9. Run 25_build_ship_candidate.ps1"
$summary += "10. Run 26_release_doctor.ps1"

Write-Utf8File -Path "$docsDir\FREEZE_RECONCILIATION_SUMMARY.md" -Content ($summary -join "`r`n")

Write-Host "DONE" -ForegroundColor Green
Write-Host "Open docs\release\FREEZE_RECONCILIATION_SUMMARY.md" -ForegroundColor Yellow
Write-Host "Open audit-artifacts\freeze-reconcile\02_missing_files.csv" -ForegroundColor Yellow
Write-Host "Open audit-artifacts\freeze-reconcile\12_schema_progress_snapshot.json" -ForegroundColor Yellow
