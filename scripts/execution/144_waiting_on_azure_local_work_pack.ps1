$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ============================================================
# CROWN WAITING-ON-AZURE WORK PACK
# Local validation, UI cleanup proof, route/dashboard/wizard inventory,
# security scan, blocker board, and commit-ready proof packet.
# Does NOT deploy. Does NOT touch Azure.
# ============================================================

Set-Location (git rev-parse --show-toplevel)
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path
$Out = "audit-artifacts\waiting-on-azure-local-work\$Stamp"
$Docs = "docs\crown-master-binder"
$Ops = "$Docs\operations"
$Design = "$Docs\design-system"
$Inventory = "$Docs\inventory"

New-Item -ItemType Directory -Force -Path $Out, $Ops, $Design, $Inventory | Out-Null
Start-Transcript -Path "$Out\00_RUN_LOG.txt" -Force | Out-Null

Write-Host "CROWN waiting-on-Azure local work pack"
Write-Host "Repo: $Root"
Write-Host "Output: $Out"

# ------------------------------------------------------------
# 01. Repo status
# ------------------------------------------------------------
$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD

git status --short | Set-Content "$Out\01_git_status_before.txt" -Encoding UTF8
git status | Set-Content "$Out\02_git_status_full_before.txt" -Encoding UTF8
git log --oneline -25 | Set-Content "$Out\03_recent_commits.txt" -Encoding UTF8

# ------------------------------------------------------------
# 02. Find frontend/backend surfaces
# ------------------------------------------------------------
$PackageFiles = Get-ChildItem -Recurse -File -Filter package.json |
  Where-Object { $_.FullName -notmatch "\\node_modules\\" }

$FrontendRoot = $null
foreach ($pkg in $PackageFiles) {
  try {
    $raw = Get-Content $pkg.FullName -Raw
    if ($raw.ToLowerInvariant() -match "react|vite|next|tailwind|@types/react") {
      $FrontendRoot = Split-Path $pkg.FullName -Parent
      break
    }
  }
  catch {}
}

$BackendManagePy = if (Test-Path "backend\manage.py") { "backend\manage.py" } else { "" }

@"
Repo: $Root
Branch: $Branch
HEAD: $Head
FrontendRoot: $FrontendRoot
BackendManagePy: $BackendManagePy
"@ | Set-Content "$Out\04_detected_surfaces.txt" -Encoding UTF8

# ------------------------------------------------------------
# 03. Run local validation commands
# ------------------------------------------------------------
$Validation = @()

function Add-Validation {
  param(
    [string]$Area,
    [string]$Command,
    [string]$WorkingDirectory
  )

  $idx = $script:Validation.Count + 1
  $safe = ($Area + "_" + $idx) -replace "[^A-Za-z0-9_-]", "_"
  $log = Join-Path $Root "$Out\validation_$safe.txt"

  Push-Location $WorkingDirectory
  try {
    "=== COMMAND ===" | Set-Content $log -Encoding UTF8
    $Command | Add-Content $log -Encoding UTF8
    "`n=== OUTPUT ===" | Add-Content $log -Encoding UTF8

    $prevErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    cmd.exe /c $Command >> $log 2>&1
    $ErrorActionPreference = $prevErrorAction

    $exit = $LASTEXITCODE
    $status = if ($exit -eq 0) { "PASS" } else { "FAIL" }
    $script:Validation += [pscustomobject]@{
      Area = $Area
      Command = $Command
      WorkingDirectory = $WorkingDirectory
      ExitCode = $exit
      Status = $status
      OutputFile = $log
    }
  }
  catch {
    $_ | Out-String | Add-Content $log -Encoding UTF8
    $script:Validation += [pscustomobject]@{
      Area = $Area
      Command = $Command
      WorkingDirectory = $WorkingDirectory
      ExitCode = 999
      Status = "ERROR"
      OutputFile = $log
    }
  }
  finally {
    Pop-Location
  }
}

if ($FrontendRoot) {
  $pkg = Get-Content (Join-Path $FrontendRoot "package.json") -Raw | ConvertFrom-Json
  if ($pkg.scripts) {
    foreach ($s in @("typecheck", "lint", "test", "build")) {
      if ($pkg.scripts.PSObject.Properties.Name -contains $s) {
        Add-Validation "Frontend" "npm run $s" $FrontendRoot
      }
    }
  }
}

if ($BackendManagePy) {
  Add-Validation "Backend" "python backend\manage.py check" $Root
  Add-Validation "Backend" "python backend\manage.py check --deploy" $Root
  Add-Validation "Backend" "python backend\manage.py showmigrations" $Root
}

if ((Test-Path "pytest.ini") -or (Test-Path "pyproject.toml") -or (Test-Path "backend\pytest.ini")) {
  Add-Validation "Backend" "python -m pytest" $Root
}

$Validation | Export-Csv "$Out\10_validation_results.csv" -NoTypeInformation

# ------------------------------------------------------------
# 04. Scan repo for release risks
# ------------------------------------------------------------
$Excluded = @(
  "\\.git\\",
  "\\node_modules\\",
  "\\dist\\",
  "\\build\\",
  "\\coverage\\",
  "\\.next\\",
  "\\.venv\\",
  "\\venv\\",
  "\\__pycache__\\"
)

$Files = Get-ChildItem -Recurse -File |
  Where-Object {
    $p = $_.FullName
    $ok = $true
    foreach ($e in $Excluded) {
      if ($p -match $e) { $ok = $false }
    }

    $ok -and ($_.Extension.ToLowerInvariant() -in @(".ts", ".tsx", ".js", ".jsx", ".py", ".html", ".css", ".md", ".json", ".yml", ".yaml"))
  }

function Search-Risk {
  param(
    [array]$Patterns,
    [string]$Type,
    [string]$Output
  )

  $rows = @()
  foreach ($f in $Files) {
    try {
      $hits = Select-String -Path $f.FullName -Pattern $Patterns -AllMatches -ErrorAction SilentlyContinue
      foreach ($h in $hits) {
        $rows += [pscustomobject]@{
          Type = $Type
          File = $f.FullName.Replace($Root, "").TrimStart("\\")
          Line = $h.LineNumber
          Text = $h.Line.Trim()
        }
      }
    }
    catch {}
  }

  $rows | Export-Csv $Output -NoTypeInformation
  return $rows
}

$PlaceholderHits = Search-Risk `
  -Type "Placeholder/Incomplete" `
  -Output "$Out\20_placeholder_incomplete_scan.csv" `
  -Patterns @("TODO", "FIXME", "TBD", "coming soon", "placeholder", "lorem", "dummy", "fake", "not implemented", "hardcoded", "replace me", "needs wiring", "demo only")

$UiHits = Search-Risk `
  -Type "UI Risk" `
  -Output "$Out\21_ui_risk_scan.csv" `
  -Patterns @('href="#"', "href='#'", "javascript:void", "bg-gray-900", "bg-slate-900", "bg-zinc-900", "bg-neutral-900", "#000000", "#111827", "#0f172a", "navy", "dark placeholder")

$SecretHits = Search-Risk `
  -Type "Possible Secret" `
  -Output "$Out\22_possible_secret_scan.csv" `
  -Patterns @("BEGIN PRIVATE KEY", "client_secret", "api_key", "apikey", "access_token", "refresh_token", "password=", "password:", "SECRET_KEY", "AZURE_CREDENTIALS", "AZURE_SWA_TOKEN", "connectionString", "AccountKey=")

$RouteHits = Search-Risk `
  -Type "Route/Nav" `
  -Output "$Out\23_route_inventory.csv" `
  -Patterns @("<Route", "path=", "path:", "href=", "to=", "navigate\(", "router.push", "createBrowserRouter")

$DashboardHits = Search-Risk `
  -Type "Dashboard/KPI" `
  -Output "$Out\24_dashboard_inventory.csv" `
  -Patterns @("dashboard", "Dashboard", "kpi", "KPI", "metric", "Metric", "widget", "Widget")

$WizardHits = Search-Risk `
  -Type "Wizard" `
  -Output "$Out\25_wizard_inventory.csv" `
  -Patterns @("wizard", "Wizard", "stepper", "Stepper", "multi-step", "multistep")

Copy-Item "$Out\23_route_inventory.csv" "$Inventory\WAITING_ON_AZURE_ROUTE_INVENTORY.csv" -Force
Copy-Item "$Out\24_dashboard_inventory.csv" "$Inventory\WAITING_ON_AZURE_DASHBOARD_INVENTORY.csv" -Force
Copy-Item "$Out\25_wizard_inventory.csv" "$Inventory\WAITING_ON_AZURE_WIZARD_INVENTORY.csv" -Force

# ------------------------------------------------------------
# 05. Ensure CROWN UI standard files exist
# ------------------------------------------------------------
$UiStandard = @"
# CROWN UI Completion Standard

## Required visual direction
CROWN should be clean, light, royal, modern, credible, and calm.

Use:
- light royal blue accents
- white/near-white card surfaces
- soft borders
- readable typography
- consistent spacing
- clear page hierarchy
- visible focus states
- clean empty/error/loading states

Avoid:
- dark navy-heavy dashboards
- raw gray blocks
- dead links
- placeholder labels
- fake metrics without sandbox labeling
- inconsistent KPI card designs
- page-specific styling systems

## Required production-facing pages
- Login / sandbox login
- School administrator dashboard
- Parent portal
- Teacher portal
- Admissions dashboard/workflow
- Billing dashboard/workflow
- Student records / SIS screens
- Communications screens

## Screen acceptance rule
A screen is not production-ready until:
- it has no dead links
- it has no placeholder copy
- it has no unmarked fake metric
- it follows the shared CROWN visual style
- it has loading, empty, error, and success states where applicable
- it respects RBAC
- it respects tenant context
"@

$UiStandard | Set-Content "$Design\WAITING_ON_AZURE_UI_COMPLETION_STANDARD.md" -Encoding UTF8

$UiChecklist = @(
  [pscustomobject]@{ Screen = "Sandbox Login"; Owner = "Dev 4 / Dev 5"; Required = "Sandbox-only options; prefilled sandbox credentials; no real school confusion"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Admin Dashboard"; Owner = "Dev 4"; Required = "Light royal CROWN design; real/seeded-labeled KPIs; no dead links"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Parent Portal"; Owner = "Dev 4"; Required = "Household/student/billing/communications clarity; no placeholder content"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Teacher Portal"; Owner = "Dev 4"; Required = "Roster/attendance/class workflow obvious and polished"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Admissions"; Owner = "Dev 3 / Dev 4"; Required = "Inquiry/applicant/checklist/status flow is workflow-backed"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Billing"; Owner = "Dev 3 / Dev 4"; Required = "Charges/payments/balances clear; no fake money unless sandbox-labeled"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "SIS Records"; Owner = "Dev 2 / Dev 4"; Required = "Student/household/guardian/enrollment screens consistent and role-safe"; Status = "Open"; Evidence = "" },
  [pscustomobject]@{ Screen = "Error/Empty States"; Owner = "Dev 4"; Required = "No raw debug output; clear next action"; Status = "Open"; Evidence = "" }
)

$UiChecklist | Export-Csv "$Design\WAITING_ON_AZURE_UI_COMPLETION_CHECKLIST.csv" -NoTypeInformation
Copy-Item "$Design\WAITING_ON_AZURE_UI_COMPLETION_CHECKLIST.csv" "$Out\30_ui_completion_checklist.csv" -Force

# ------------------------------------------------------------
# 06. Create blocker board
# ------------------------------------------------------------
$Blockers = @()

function Add-Blocker {
  param(
    [string]$Priority,
    [string]$Area,
    [string]$Issue,
    [string]$Owner,
    [string]$Evidence,
    [string]$RequiredFix
  )

  $script:Blockers += [pscustomobject]@{
    Priority = $Priority
    Area = $Area
    Issue = $Issue
    Owner = $Owner
    Evidence = $Evidence
    RequiredFix = $RequiredFix
    Status = "Open"
  }
}

foreach ($v in $Validation | Where-Object { $_.Status -ne "PASS" }) {
  Add-Blocker "P0" $v.Area "Validation failed or needs review: $($v.Command)" "Dev 5" $v.OutputFile "Fix failing command or document why it is not release-applicable."
}

if ($SecretHits.Count -gt 0) {
  Add-Blocker "P0" "Security" "$($SecretHits.Count) possible secret/token hits found." "Dev 5" "$Out\22_possible_secret_scan.csv" "Review each hit; remove real secrets; classify false positives."
}

if ($PlaceholderHits.Count -gt 0) {
  Add-Blocker "P1" "Product/UI" "$($PlaceholderHits.Count) placeholder/incomplete markers found." "Dev 4 / Dev 5" "$Out\20_placeholder_incomplete_scan.csv" "Remove, replace, or formally defer production-facing markers."
}

if ($UiHits.Count -gt 0) {
  Add-Blocker "P1" "UI Polish" "$($UiHits.Count) UI risk hits found." "Dev 4" "$Out\21_ui_risk_scan.csv" "Fix dead links, dark/off-brand treatments, and hardcoded visual drift."
}

if ($RouteHits.Count -eq 0) {
  Add-Blocker "P1" "Routes" "No route references found." "Dev 4" "$Out\23_route_inventory.csv" "Confirm frontend router structure and rescan."
}

if ($DashboardHits.Count -eq 0) {
  Add-Blocker "P1" "Dashboards" "No dashboard references found." "Dev 4" "$Out\24_dashboard_inventory.csv" "Confirm dashboard naming/routes and rescan."
}

$Blockers | Sort-Object Priority, Area | Export-Csv "$Out\40_LOCAL_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\40_LOCAL_BLOCKER_BOARD.csv" "$Ops\WAITING_ON_AZURE_LOCAL_BLOCKER_BOARD.csv" -Force

# ------------------------------------------------------------
# 07. Final local proof board
# ------------------------------------------------------------
$ProofBoard = @(
  [pscustomobject]@{ Gate = "Local validation"; Required = "All applicable local build/lint/test/check commands pass"; Status = "Open"; Evidence = "$Out\10_validation_results.csv" },
  [pscustomobject]@{ Gate = "Security scan"; Required = "Zero real secrets in repo"; Status = "Open"; Evidence = "$Out\22_possible_secret_scan.csv" },
  [pscustomobject]@{ Gate = "Placeholder cleanup"; Required = "No production-facing placeholder/incomplete markers"; Status = "Open"; Evidence = "$Out\20_placeholder_incomplete_scan.csv" },
  [pscustomobject]@{ Gate = "UI polish"; Required = "No critical off-brand/dead-link UI risks"; Status = "Open"; Evidence = "$Out\21_ui_risk_scan.csv" },
  [pscustomobject]@{ Gate = "Route inventory"; Required = "Routes inventoried and reviewed"; Status = "Open"; Evidence = "$Out\23_route_inventory.csv" },
  [pscustomobject]@{ Gate = "Dashboard inventory"; Required = "Dashboards/KPIs inventoried and classified"; Status = "Open"; Evidence = "$Out\24_dashboard_inventory.csv" },
  [pscustomobject]@{ Gate = "Wizard inventory"; Required = "Wizards inventoried and classified"; Status = "Open"; Evidence = "$Out\25_wizard_inventory.csv" },
  [pscustomobject]@{ Gate = "Azure backend proof"; Required = "Backend approved SHA live"; Status = "Waiting on Azure"; Evidence = "" },
  [pscustomobject]@{ Gate = "Azure frontend proof"; Required = "Frontend root/build.json live and SHA match"; Status = "Waiting on Azure"; Evidence = "" },
  [pscustomobject]@{ Gate = "Post-Azure sandbox proof"; Required = "Sandbox browser proof after deploy"; Status = "Waiting on Azure"; Evidence = "" }
)

$ProofBoard | Export-Csv "$Out\50_PROOF_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\50_PROOF_BOARD.csv" "$Ops\WAITING_ON_AZURE_PROOF_BOARD.csv" -Force

# ------------------------------------------------------------
# 08. Summary
# ------------------------------------------------------------
$ValidationPass = @($Validation | Where-Object { $_.Status -eq "PASS" }).Count
$ValidationFail = @($Validation | Where-Object { $_.Status -ne "PASS" }).Count
$P0 = @($Blockers | Where-Object { $_.Priority -eq "P0" }).Count
$P1 = @($Blockers | Where-Object { $_.Priority -eq "P1" }).Count
$P2 = @($Blockers | Where-Object { $_.Priority -eq "P2" }).Count

$Decision = if ($P0 -eq 0 -and $ValidationFail -eq 0) {
  "LOCAL_WORK_GREEN_PENDING_AZURE"
}
else {
  "LOCAL_REMEDIATION_REQUIRED_PENDING_AZURE"
}

$Summary = @"
# CROWN Waiting-on-Azure Local Work Summary

Generated: $(Get-Date -Format s)
Repo: $Root
Branch: $Branch
HEAD: $Head
HEAD_FULL: $HeadFull

## Decision
$Decision

## What Was Done Locally
- Captured repo state.
- Detected frontend/backend surfaces.
- Ran local validation commands.
- Scanned for placeholders/incomplete markers.
- Scanned for UI polish risks.
- Scanned for possible secrets.
- Built route inventory.
- Built dashboard/KPI inventory.
- Built wizard inventory.
- Generated UI completion standard.
- Generated UI completion checklist.
- Generated local blocker board.
- Generated proof board.

## Counts
Validation PASS: $ValidationPass
Validation non-PASS: $ValidationFail
P0 blockers: $P0
P1 blockers: $P1
P2 blockers: $P2
Possible secret hits: $($SecretHits.Count)
Placeholder/incomplete hits: $($PlaceholderHits.Count)
UI risk hits: $($UiHits.Count)
Route references: $($RouteHits.Count)
Dashboard/KPI references: $($DashboardHits.Count)
Wizard references: $($WizardHits.Count)

## Open First
- Local blocker board: $Out\40_LOCAL_BLOCKER_BOARD.csv
- Validation results: $Out\10_validation_results.csv
- UI checklist: $Out\30_ui_completion_checklist.csv
- Proof board: $Out\50_PROOF_BOARD.csv

## Rule
Everything in this packet can be worked before Azure is fixed.
Azure-only items remain waiting:
- backend approved SHA proof
- frontend root/build.json proof
- workflow success proof
- post-Azure sandbox browser proof
"@

$Summary | Set-Content "$Out\99_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_SUMMARY.md" "$Ops\WAITING_ON_AZURE_CURRENT_SUMMARY.md" -Force

git status --short | Set-Content "$Out\90_git_status_after.txt" -Encoding UTF8

# ------------------------------------------------------------
# 09. Open files
# ------------------------------------------------------------
code "$Out\99_SUMMARY.md"
code "$Out\40_LOCAL_BLOCKER_BOARD.csv"
code "$Out\10_validation_results.csv"
code "$Out\30_ui_completion_checklist.csv"
code "$Out\50_PROOF_BOARD.csv"
code "$Out\90_git_status_after.txt"

Write-Host ""
Write-Host "Completed waiting-on-Azure local work pack."
Write-Host "Decision: $Decision"
Write-Host "Output: $Out"
Write-Host ""

Stop-Transcript | Out-Null
