param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$inv = "docs\audit\inventories"
$scan = "docs\audit\scans"
$evidence = "docs\audit\evidence"
$reports = "docs\audit\reports"
New-Item -ItemType Directory -Force -Path $reports | Out-Null

function Import-CsvSafe([string]$Path) {
  if (Test-Path $Path) { return Import-Csv $Path }
  return @()
}

$master = Import-CsvSafe "$inv\MASTER_PLATFORM_INVENTORY.csv"
$ui = Import-CsvSafe "$inv\DASHBOARD_WIZARD_PAGE_INVENTORY.csv"
$routes = Import-CsvSafe "$inv\API_ROUTE_CONTRACT_INVENTORY.csv"
$modelSvc = Import-CsvSafe "$inv\MODEL_SERVICE_INVENTORY.csv"
$testsCiDocs = Import-CsvSafe "$inv\TEST_CI_DOC_INVENTORY.csv"
$todo = Import-CsvSafe "$scan\TODO_SCAN.csv"
$place = Import-CsvSafe "$scan\PLACEHOLDER_SCAN.csv"
$routeRisk = Import-CsvSafe "$scan\ROUTE_RISK_SCAN.csv"
$workflowRisk = Import-CsvSafe "$scan\WORKFLOW_RISK_SCAN.csv"
$docClaim = Import-CsvSafe "$scan\DOC_CLAIM_SCAN.csv"
$proof = Import-CsvSafe "$evidence\PROOF_SUMMARY.csv"

$moduleRows = @(
  "Core Platform",
  "SIS Core",
  "Admissions",
  "Re-enrollment",
  "Billing / Payments",
  "Communications",
  "Parent Portal",
  "Teacher Portal",
  "Administrator Portal",
  "Attendance",
  "Scheduling / Gradebook",
  "Activities / Events",
  "Nurse Office",
  "Transportation",
  "Food Services",
  "Volunteer / Family Engagement",
  "Advanced Board Reporting",
  "Extended Discipline",
  "Spiritual Life",
  "Service & Outreach",
  "Crown Compass",
  "Board Governance",
  "PD Hub"
) | ForEach-Object {
  [pscustomobject]@{
    Area = $_
    Layer = if ($_ -match 'Core') { "Core" } elseif ($_ -match 'Spiritual|Service|Compass|Board Governance|PD Hub') { "Add-on" } else { "Module" }
    Owner = switch -Regex ($_) {
      'Core Platform' { 'Dev 1 / Dev 5' ; break }
      'SIS Core|Attendance|Scheduling / Gradebook' { 'Dev 2' ; break }
      'Parent Portal|Teacher Portal|Administrator Portal' { 'Dev 4' ; break }
      'Spiritual|Service|Compass|Board Governance|PD Hub' { 'Product' ; break }
      default { 'Dev 3' ; break }
    }
    DataModel = "MUST_REVIEW"
    Permissions = "MUST_REVIEW"
    Tenant = "MUST_REVIEW"
    Audit = "MUST_REVIEW"
    API = "MUST_REVIEW"
    UI = "MUST_REVIEW"
    Tests = "MUST_REVIEW"
    E2E = "MUST_REVIEW"
    Docs = "MUST_REVIEW"
    KeepRewriteDrop = "MUST_REVIEW"
    FinalStatus = "RED"
    Notes = ""
  }
}
$moduleRows | Export-Csv "$reports\MODULE_COMPLETION_MATRIX.csv" -NoTypeInformation -Encoding UTF8

$krdRows = $master | ForEach-Object {
  [pscustomobject]@{
    Path = $_.Path
    Name = $_.Name
    AssetType = $_.AssetType
    Layer = $_.Layer
    CandidateModule = $_.CandidateModule
    Owner = $_.Owner
    KeepRewriteDrop = "MUST_REVIEW"
    Why = ""
  }
}
$krdRows | Export-Csv "$reports\KEEP_REWRITE_DROP_MATRIX.csv" -NoTypeInformation -Encoding UTF8

$dwRows = $ui | ForEach-Object {
  [pscustomobject]@{
    Path = $_.Path
    Name = $_.Name
    UIKind = $_.UIKind
    CandidateModule = $_.CandidateModule
    Owner = $_.Owner
    RealData = "MUST_REVIEW"
    APIWired = "MUST_REVIEW"
    ValidationComplete = "MUST_REVIEW"
    PermissionsCorrect = "MUST_REVIEW"
    TenantSafe = "MUST_REVIEW"
    Duplicate = "MUST_REVIEW"
    KeepRewriteDrop = "MUST_REVIEW"
    FinalStatus = "RED"
    Notes = ""
  }
}
$dwRows | Export-Csv "$reports\DASHBOARD_WIZARD_STATUS.csv" -NoTypeInformation -Encoding UTF8

$proofPass = ($proof | Where-Object { $_.Status -eq "PASS" }).Count
$proofFail = ($proof | Where-Object { $_.Status -ne "PASS" }).Count

$scorecard = @()
$scorecard += "# Final Audit Scorecard"
$scorecard += ""
$scorecard += "| Area | Count |"
$scorecard += "|---|---:|"
$scorecard += "| Total assets | $($master.Count) |"
$scorecard += "| UI assets | $($ui.Count) |"
$scorecard += "| API / route assets | $($routes.Count) |"
$scorecard += "| Model / service assets | $($modelSvc.Count) |"
$scorecard += "| Test / CI / doc assets | $($testsCiDocs.Count) |"
$scorecard += "| TODO / FIXME / HACK / XXX hits | $($todo.Count) |"
$scorecard += "| Placeholder / dummy / mock hits | $($place.Count) |"
$scorecard += "| Route risk hits | $($routeRisk.Count) |"
$scorecard += "| Workflow risk hits | $($workflowRisk.Count) |"
$scorecard += "| Doc claim risk hits | $($docClaim.Count) |"
$scorecard += "| Proof PASS rows | $proofPass |"
$scorecard += "| Proof FAIL rows | $proofFail |"
$scorecard += ""
$scorecard += "## Immediate Review Files"
$scorecard += "- reports/MODULE_COMPLETION_MATRIX.csv"
$scorecard += "- reports/KEEP_REWRITE_DROP_MATRIX.csv"
$scorecard += "- reports/DASHBOARD_WIZARD_STATUS.csv"
$scorecard += "- evidence/PROOF_SUMMARY.csv"
$scorecard += "- scans/TODO_SCAN.csv"
$scorecard += "- scans/PLACEHOLDER_SCAN.csv"
$scorecard += "- scans/ROUTE_RISK_SCAN.csv"
$scorecard += "- scans/WORKFLOW_RISK_SCAN.csv"
$scorecard | Set-Content "$reports\FINAL_AUDIT_SCORECARD.md" -Encoding UTF8

$summary = @()
$summary += "# Final Executive Audit Summary"
$summary += ""
$summary += "## What this pack answers"
$summary += "- What exists"
$summary += "- Who owns it"
$summary += "- What layer it belongs to"
$summary += "- Whether it is likely keep / rewrite / drop"
$summary += "- Where route, workflow, placeholder, and TODO risks exist"
$summary += "- Which proof checks passed and failed"
$summary += ""
$summary += "## Current Counts"
$summary += "- Total assets: $($master.Count)"
$summary += "- UI assets: $($ui.Count)"
$summary += "- API / route assets: $($routes.Count)"
$summary += "- Model / service assets: $($modelSvc.Count)"
$summary += "- Test / CI / doc assets: $($testsCiDocs.Count)"
$summary += "- TODO-like hits: $($todo.Count)"
$summary += "- Placeholder hits: $($place.Count)"
$summary += "- Route risk hits: $($routeRisk.Count)"
$summary += "- Workflow risk hits: $($workflowRisk.Count)"
$summary += "- Proof pass rows: $proofPass"
$summary += "- Proof fail rows: $proofFail"
$summary += ""
$summary += "## Required Human Review"
$summary += "1. Fill MODULE_COMPLETION_MATRIX.csv"
$summary += "2. Fill KEEP_REWRITE_DROP_MATRIX.csv"
$summary += "3. Review DASHBOARD_WIZARD_STATUS.csv"
$summary += "4. Review PROOF_SUMMARY.csv"
$summary += "5. Decide final in-scope / out-of-scope rows for the release claim"
$summary += ""
$summary += "## Rule"
$summary += "If a module or workflow is not fully proven end to end, do not mark it complete."
$summary | Set-Content "$reports\FINAL_EXECUTIVE_AUDIT_SUMMARY.md" -Encoding UTF8

Write-Host "Status book generated."
Write-Host "Open:"
Write-Host "  docs\audit\reports\FINAL_EXECUTIVE_AUDIT_SUMMARY.md"
Write-Host "  docs\audit\reports\FINAL_AUDIT_SCORECARD.md"
