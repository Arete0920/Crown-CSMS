<#
.SYNOPSIS
  Runs static CROWN Guided Proof Sandbox gate checks.

.DESCRIPTION
  This script verifies that sandbox implementation files, docs, manifests, and safety scripts exist.
  It does not replace frontend build, backend tests, deployed smoke, or authenticated tenant-isolation proof.
#>

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$requiredFiles = @(
  "frontend/dashboards/src/sandbox/sandboxExperience.js",
  "frontend/dashboards/src/pages/SandboxLandingPage.jsx",
  "frontend/dashboards/src/sandbox/SandboxCommandCenter.jsx",
  "frontend/dashboards/src/sandbox/sandboxTelemetry.js",
  "frontend/dashboards/src/tests/sandboxExperience.test.jsx",
  "frontend/dashboards/src/tests/sandboxCommandCenter.test.jsx",
  "backend/core/management/commands/sandbox_seed.py",
  "backend/core/management/commands/sandbox_verify.py",
  "sandbox/seed_packs/school/heritage_core/manifest.json",
  "sandbox/seed_packs/daycare/emmanuel_early_learning/manifest.json",
  "sandbox/seed_packs/camp/cedar_ridge_summer_camp/manifest.json",
  "docs/compliance/SANDBOX_DATA_POLICY.md",
  "docs/product/GUIDED_PROOF_SANDBOX_BLUEPRINT.md",
  "scripts/execution/210_apply_guided_sandbox_frontend_patch.ps1",
  "scripts/execution/211_sandbox_no_real_data_scan.ps1"
)

$missing = @()
foreach ($relative in $requiredFiles) {
  $path = Join-Path $repoRoot $relative
  if (-not (Test-Path $path)) { $missing += $relative }
}

if ($missing.Count -gt 0) {
  $missing | ForEach-Object { Write-Host "FAIL missing $_" }
  throw "Sandbox static gate failed: $($missing.Count) required file(s) missing."
}

$catalog = Get-Content (Join-Path $repoRoot "frontend/dashboards/src/sandbox/sandboxExperience.js") -Raw
foreach ($track in @("school", "daycare", "camp")) {
  if ($catalog -notmatch "key: `"$track`"") {
    throw "Sandbox catalog missing track: $track"
  }
}

$policy = Get-Content (Join-Path $repoRoot "docs/compliance/SANDBOX_DATA_POLICY.md") -Raw
foreach ($term in @("Status: Active", "School demo", "Daycare / early learning demo", "Camp / summer program demo", "Demo data only")) {
  if ($policy -notmatch [regex]::Escape($term)) {
    throw "Sandbox policy missing required term: $term"
  }
}

& (Join-Path $repoRoot "scripts/execution/211_sandbox_no_real_data_scan.ps1")

Write-Host "PASS static guided sandbox gate checks completed."
Write-Host "NOT VERIFIED: frontend build, backend command execution, deployed route smoke, login preselection, role proof, reset proof, cross-tenant proof."
