param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$inv = "docs\audit\inventories"
$scan = "docs\audit\scans"
$evidence = "docs\audit\evidence"
$reports = "docs\audit\reports"

function Import-CsvSafe([string]$Path) {
  if (Test-Path $Path) { return Import-Csv $Path }
  return @()
}

function Add-Blocker {
  param(
    [string]$Title,
    [string]$Category,
    [string]$Severity,
    [string]$Owner,
    [string]$Source,
    [string]$AssetCount,
    [string]$WhatItMeans,
    [string]$RequiredAction,
    [string]$Status = "OPEN"
  )
  $script:blockers += [pscustomobject]@{
    Rank = 0
    Severity = $Severity
    Category = $Category
    Title = $Title
    Owner = $Owner
    Status = $Status
    Source = $Source
    AssetCount = $AssetCount
    WhatItMeans = $WhatItMeans
    RequiredAction = $RequiredAction
  }
}

function Severity-Weight([string]$Severity) {
  switch ($Severity) {
    "CRITICAL" { return 400 }
    "HIGH"     { return 300 }
    "MEDIUM"   { return 200 }
    "LOW"      { return 100 }
    default    { return 0 }
  }
}

$blockers = @()
$master      = Import-CsvSafe "$inv\MASTER_PLATFORM_INVENTORY.csv"
$coreInv     = Import-CsvSafe "$inv\CORE_INVENTORY.csv"
$moduleInv   = Import-CsvSafe "$inv\MODULE_INVENTORY.csv"
$addonInv    = Import-CsvSafe "$inv\ADDON_INVENTORY.csv"
$uiInv       = Import-CsvSafe "$inv\DASHBOARD_WIZARD_PAGE_INVENTORY.csv"
$routeInv    = Import-CsvSafe "$inv\API_ROUTE_CONTRACT_INVENTORY.csv"
$modelSvcInv = Import-CsvSafe "$inv\MODEL_SERVICE_INVENTORY.csv"
$testCiInv   = Import-CsvSafe "$inv\TEST_CI_DOC_INVENTORY.csv"

$todoScan      = Import-CsvSafe "$scan\TODO_SCAN.csv"
$placeholder   = Import-CsvSafe "$scan\PLACEHOLDER_SCAN.csv"
$routeRisk     = Import-CsvSafe "$scan\ROUTE_RISK_SCAN.csv"
$workflowRisk  = Import-CsvSafe "$scan\WORKFLOW_RISK_SCAN.csv"
$docClaimRisk  = Import-CsvSafe "$scan\DOC_CLAIM_SCAN.csv"
$dupScan       = Import-CsvSafe "$scan\DUPLICATE_FILENAME_SCAN.csv"
$dashRisk      = Import-CsvSafe "$scan\DASHBOARD_WIZARD_RISK_SCAN.csv"

$proof = Import-CsvSafe "$evidence\PROOF_SUMMARY.csv"
$moduleMatrix = Import-CsvSafe "$reports\MODULE_COMPLETION_MATRIX.csv"
$krdMatrix    = Import-CsvSafe "$reports\KEEP_REWRITE_DROP_MATRIX.csv"
$dwStatus     = Import-CsvSafe "$reports\DASHBOARD_WIZARD_STATUS.csv"

$proofFail = $proof | Where-Object { $_.Status -ne "PASS" }
foreach ($row in $proofFail) {
  $owner = switch -Regex ($row.Check) {
    "DJANGO_CHECK|SHOW_MIGRATIONS|OPENAPI_EXPORT" { "Dev 1 / Dev 5"; break }
    "FRONTEND_LINT|FRONTEND_BUILD"               { "Dev 4"; break }
    "HEALTH_ENDPOINT|INTEGRITY_ENDPOINT"         { "Dev 5"; break }
    "CRITICAL_TEST_CLUSTER|FULL_BACKEND_REGRESSION" { "Dev 5"; break }
    "GH_PR_LIST|GH_RUN_LIST"                     { "Dev 5"; break }
    default                                      { "MUST_ASSIGN" }
  }
  $sev = switch -Regex ($row.Check) {
    "CRITICAL_TEST_CLUSTER|FULL_BACKEND_REGRESSION|HEALTH_ENDPOINT|INTEGRITY_ENDPOINT" { "CRITICAL"; break }
    "DJANGO_CHECK|SHOW_MIGRATIONS|OPENAPI_EXPORT|FRONTEND_BUILD" { "HIGH"; break }
    "FRONTEND_LINT|GH_PR_LIST|GH_RUN_LIST" { "MEDIUM"; break }
    default { "MEDIUM" }
  }
  Add-Blocker -Title "Proof failure: $($row.Check)" -Category "Proof" -Severity $sev -Owner $owner -Source "PROOF_SUMMARY.csv" -AssetCount "1" -WhatItMeans ($row.Notes) -RequiredAction "Fix failing proof item, rerun runtime checks, archive passing artifact."
}

if ($todoScan.Count -gt 0) {
  Add-Blocker -Title "Residual TODO / FIXME / HACK / XXX markers" -Category "Code Hygiene" -Severity "HIGH" -Owner "All Leads" -Source "TODO_SCAN.csv" -AssetCount "$($todoScan.Count)" -WhatItMeans "The codebase still contains unresolved markers that can hide incomplete or risky logic." -RequiredAction "Review every hit; remove resolved markers, convert real blockers into tracked issues, eliminate noise."
}
if ($placeholder.Count -gt 0) {
  Add-Blocker -Title "Placeholders / dummy values / hard-coded examples remain" -Category "UI / Data Truth" -Severity "HIGH" -Owner "Dev 4 / Dev 3 / Dev 5" -Source "PLACEHOLDER_SCAN.csv" -AssetCount "$($placeholder.Count)" -WhatItMeans "Placeholders may indicate fake data paths, sample IDs, or unfinished user flows." -RequiredAction "Replace placeholder content with production-safe UX or remove the asset from final release."
}
if ($routeRisk.Count -gt 0) {
  Add-Blocker -Title "Route contract risk and duplicate-path risk" -Category "API / Routing" -Severity "CRITICAL" -Owner "Dev 1" -Source "ROUTE_RISK_SCAN.csv" -AssetCount "$($routeRisk.Count)" -WhatItMeans "Routing complexity or duplicate prefixes can break contracts and invalidate release claims." -RequiredAction "Review every route hit, eliminate duplicate prefixes, verify auth and tenant behavior, and re-run proof."
}
if ($workflowRisk.Count -gt 0) {
  Add-Blocker -Title "Workflow policy and CI/CD risk" -Category "CI / CD" -Severity "HIGH" -Owner "Dev 5" -Source "WORKFLOW_RISK_SCAN.csv" -AssetCount "$($workflowRisk.Count)" -WhatItMeans "Workflow sprawl, risky conditions, or stale action references weaken release confidence." -RequiredAction "Reduce workflow noise, verify release path, and document the canonical CI/CD surface."
}
if ($docClaimRisk.Count -gt 0) {
  Add-Blocker -Title "Docs and release language drift from release truth" -Category "Docs / Governance" -Severity "HIGH" -Owner "Docs / TC" -Source "DOC_CLAIM_SCAN.csv" -AssetCount "$($docClaimRisk.Count)" -WhatItMeans "Some docs may still contain language that weakens final release truth or over/understates completion." -RequiredAction "Update active docs to match the final release standard and retire or relabel conflicting language."
}
if ($dupScan.Count -gt 0) {
  Add-Blocker -Title "Duplicate filenames increase review and maintenance risk" -Category "Repo Hygiene" -Severity "MEDIUM" -Owner "Docs / Dev Lead" -Source "DUPLICATE_FILENAME_SCAN.csv" -AssetCount "$($dupScan.Count)" -WhatItMeans "Duplicate file names can hide stale or conflicting assets." -RequiredAction "Review duplicates, archive stale copies, and clarify canonical versions."
}
if ($dashRisk.Count -gt 0) {
  Add-Blocker -Title "Dashboard / wizard risk markers remain" -Category "UI / Workflows" -Severity "HIGH" -Owner "Dev 4" -Source "DASHBOARD_WIZARD_RISK_SCAN.csv" -AssetCount "$($dashRisk.Count)" -WhatItMeans "Dashboards or wizards may still rely on placeholders, unfinished logic, or unresolved markers." -RequiredAction "Review every dashboard and wizard hit, confirm real API wiring, permissions, tenant safety, and end-to-end proof."
}

if ($uiInv.Count -gt 0) {
  $dashCount = ($uiInv | Where-Object { $_.UIKind -eq "Dashboard" }).Count
  $wizCount  = ($uiInv | Where-Object { $_.UIKind -eq "Wizard" }).Count
  $pageCount = ($uiInv | Where-Object { $_.UIKind -ne "Dashboard" -and $_.UIKind -ne "Wizard" }).Count
  Add-Blocker -Title "UI surface requires explicit classification and completion review" -Category "UI Inventory" -Severity "HIGH" -Owner "Dev 4" -Source "DASHBOARD_WIZARD_PAGE_INVENTORY.csv" -AssetCount "$($uiInv.Count)" -WhatItMeans "The platform contains $dashCount dashboards, $wizCount wizards, and $pageCount pages/components that need direct keep/rewrite/drop and completion decisions." -RequiredAction "Review every UI row and fill DASHBOARD_WIZARD_STATUS.csv fully."
}
if ($routeInv.Count -gt 0) {
  Add-Blocker -Title "API and route surface requires contract-level verification" -Category "API Inventory" -Severity "HIGH" -Owner "Dev 1 / Dev 5" -Source "API_ROUTE_CONTRACT_INVENTORY.csv" -AssetCount "$($routeInv.Count)" -WhatItMeans "The repo contains a large API/route surface that needs explicit auth, tenant, and docs verification." -RequiredAction "Fill the API route inventory and mark contract state for every public/release-relevant route."
}
if ($modelSvcInv.Count -gt 0) {
  Add-Blocker -Title "Models and services need keep/rewrite/drop decisions" -Category "Backend Inventory" -Severity "MEDIUM" -Owner "Dev 1 / Dev 2 / Dev 3" -Source "MODEL_SERVICE_INVENTORY.csv" -AssetCount "$($modelSvcInv.Count)" -WhatItMeans "Core logic assets must be classified so stale or overlapping services do not survive into release truth." -RequiredAction "Review model/service inventory and complete the keep/rewrite/drop matrix."
}

if ($moduleMatrix.Count -gt 0) {
  $redRows = $moduleMatrix | Where-Object { $_.FinalStatus -eq "RED" }
  foreach ($r in $redRows) {
    $owner = if ($r.Owner) { $r.Owner } else { "MUST_ASSIGN" }
    Add-Blocker -Title "Module not complete: $($r.Area)" -Category "Module Completion" -Severity "CRITICAL" -Owner $owner -Source "MODULE_COMPLETION_MATRIX.csv" -AssetCount "1" -WhatItMeans "The module is still red and cannot be part of a final completion claim." -RequiredAction "Finish missing DataModel, Permissions, Tenant, Audit, API, UI, Tests, E2E, Docs, then mark GREEN only with proof."
  }
  $yellowRows = $moduleMatrix | Where-Object { $_.FinalStatus -eq "YELLOW" }
  foreach ($r in $yellowRows) {
    $owner = if ($r.Owner) { $r.Owner } else { "MUST_ASSIGN" }
    Add-Blocker -Title "Module partially complete: $($r.Area)" -Category "Module Completion" -Severity "HIGH" -Owner $owner -Source "MODULE_COMPLETION_MATRIX.csv" -AssetCount "1" -WhatItMeans "The module is not release-clean yet." -RequiredAction "Close remaining gaps and convert to GREEN with evidence."
  }
} else {
  Add-Blocker -Title "Module completion matrix not yet filled" -Category "Governance" -Severity "CRITICAL" -Owner "All Leads" -Source "MODULE_COMPLETION_MATRIX.csv" -AssetCount "1" -WhatItMeans "Without a filled completion matrix, there is no trustworthy platform-wide status map." -RequiredAction "Fill every row and status immediately."
}

if ($krdMatrix.Count -eq 0) {
  Add-Blocker -Title "Keep / Rewrite / Drop matrix not yet filled" -Category "Governance" -Severity "HIGH" -Owner "All Leads" -Source "KEEP_REWRITE_DROP_MATRIX.csv" -AssetCount "1" -WhatItMeans "Stale and duplicate assets cannot be managed without explicit decisions." -RequiredAction "Complete keep/rewrite/drop decisions across the inventory."
}
if ($dwStatus.Count -eq 0) {
  Add-Blocker -Title "Dashboard / wizard status matrix not yet filled" -Category "Governance" -Severity "HIGH" -Owner "Dev 4" -Source "DASHBOARD_WIZARD_STATUS.csv" -AssetCount "1" -WhatItMeans "UI truth is still unknown." -RequiredAction "Complete dashboard/wizard/page review and mark status for every row."
}

$grouped = $blockers | Group-Object Title,Category,Owner
$deduped = foreach ($g in $grouped) {
  $first = $g.Group[0]
  $countSum = 0
  foreach ($row in $g.Group) {
    $n = 0
    [void][int]::TryParse($row.AssetCount, [ref]$n)
    $countSum += $n
  }
  [pscustomobject]@{
    Rank = 0
    Severity = $first.Severity
    Category = $first.Category
    Title = $first.Title
    Owner = $first.Owner
    Status = $first.Status
    Source = ($g.Group | Select-Object -ExpandProperty Source -Unique) -join "; "
    AssetCount = if ($countSum -gt 0) { $countSum } else { "" }
    WhatItMeans = $first.WhatItMeans
    RequiredAction = $first.RequiredAction
    Score = (Severity-Weight $first.Severity) + [math]::Min($countSum,99)
  }
}

$top = $deduped | Sort-Object Score -Descending, Title | Select-Object -First 25
$rank = 1
$top = $top | ForEach-Object {
  $_.Rank = $rank
  $rank++
  $_
}

$top | Select-Object Rank,Severity,Category,Title,Owner,Status,Source,AssetCount,WhatItMeans,RequiredAction | Export-Csv "$reports\BOARD_TOP_25_BLOCKERS.csv" -NoTypeInformation -Encoding UTF8

$totalAssets = $master.Count
$totalUI = $uiInv.Count
$totalRoutes = $routeInv.Count
$totalModelSvc = $modelSvcInv.Count
$totalTestsCiDocs = $testCiInv.Count
$proofPass = ($proof | Where-Object { $_.Status -eq "PASS" }).Count
$proofFailCount = ($proof | Where-Object { $_.Status -ne "PASS" }).Count
$redModules = if ($moduleMatrix.Count -gt 0) { ($moduleMatrix | Where-Object { $_.FinalStatus -eq "RED" }).Count } else { 0 }
$yellowModules = if ($moduleMatrix.Count -gt 0) { ($moduleMatrix | Where-Object { $_.FinalStatus -eq "YELLOW" }).Count } else { 0 }
$greenModules = if ($moduleMatrix.Count -gt 0) { ($moduleMatrix | Where-Object { $_.FinalStatus -eq "GREEN" }).Count } else { 0 }

$overall = "RED"
if ($proofFailCount -eq 0 -and $redModules -eq 0 -and $yellowModules -le 2) { $overall = "YELLOW" }
if ($proofFailCount -eq 0 -and $redModules -eq 0 -and $yellowModules -eq 0 -and $greenModules -gt 0) { $overall = "GREEN" }

$md = @()
$md += "# Crown Executive Board Report"
$md += ""
$md += "## Overall Status"
$md += "- Overall board status: **$overall**"
$md += "- Total inventoried assets: **$totalAssets**"
$md += "- UI assets reviewed by inventory: **$totalUI**"
$md += "- API / route assets inventoried: **$totalRoutes**"
$md += "- Model / service assets inventoried: **$totalModelSvc**"
$md += "- Test / CI / doc assets inventoried: **$totalTestsCiDocs**"
$md += "- Proof checks passed: **$proofPass**"
$md += "- Proof checks failed: **$proofFailCount**"
$md += "- Modules GREEN: **$greenModules**"
$md += "- Modules YELLOW: **$yellowModules**"
$md += "- Modules RED: **$redModules**"
$md += ""
$md += "## Strategic Frame"
$md += "- Crown is governed as **Core, Modules, and Add-ons**."
$md += "- Core owns truth. Modules run school operations. Add-ons integrate through approved contracts."
$md += "- No module should be treated as complete unless it is end-to-end proven."
$md += ""
$md += "## Top 25 Blockers"
$md += ""
$md += "| Rank | Severity | Category | Title | Owner | Source | Count |"
$md += "|---:|---|---|---|---|---|---:|"
foreach ($b in $top) {
  $count = if ($b.AssetCount) { $b.AssetCount } else { "" }
  $md += "| $($b.Rank) | $($b.Severity) | $($b.Category) | $($b.Title) | $($b.Owner) | $($b.Source) | $count |"
}
$md += ""
$md += "## Immediate Actions"
$md += "1. Fix all proof failures first."
$md += "2. Fill the module completion matrix completely."
$md += "3. Fill the dashboard / wizard status matrix completely."
$md += "4. Complete keep / rewrite / drop decisions."
$md += "5. Do not claim completion for any RED or YELLOW module."
$md += ""
$md += "## Owner Lanes"
$md += "- Dev 1: platform, auth, RBAC, tenant, API contracts"
$md += "- Dev 2: SIS/data truth"
$md += "- Dev 3: admissions, reenrollment, billing, operational workflows"
$md += "- Dev 4: shell, dashboards, wizards, pages, UI consistency"
$md += "- Dev 5: integration, testing, regression, release readiness"
$md += "- TC: final scope, canon approval, release truth, sign-off"
$md += ""
$md += "## Generated Files"
$md += "- reports/BOARD_TOP_25_BLOCKERS.csv"
$md += "- reports/EXEC_BOARD_REPORT.md"
$md += "- reports/MODULE_COMPLETION_MATRIX.csv"
$md += "- reports/KEEP_REWRITE_DROP_MATRIX.csv"
$md += "- reports/DASHBOARD_WIZARD_STATUS.csv"
$md += "- evidence/PROOF_SUMMARY.csv"
$md | Set-Content "$reports\EXEC_BOARD_REPORT.md" -Encoding UTF8

Write-Host "Board report generated:"
Write-Host "  $reports\BOARD_TOP_25_BLOCKERS.csv"
Write-Host "  $reports\EXEC_BOARD_REPORT.md"
