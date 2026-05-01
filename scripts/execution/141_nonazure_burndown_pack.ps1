$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
# ============================================================
# CROWN NON-AZURE BURN-DOWN + UI POLISH EXECUTION PACK
# Run from repo root after the non-Azure readiness pack.
# Does NOT touch Azure.
# ============================================================
Set-Location (git rev-parse --show-toplevel)
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path
$Base = "audit-artifacts\nonazure-production-readiness"
$Out = "audit-artifacts\nonazure-burndown\$Stamp"
$Docs = "docs\crown-master-binder"
$Ops = "$Docs\operations"
$Design = "$Docs\design-system"
$Exec = "scripts\execution"
New-Item -ItemType Directory -Force -Path $Out, $Ops, $Design, $Exec | Out-Null
$LatestFile = "$Base\LATEST.txt"
if (-not (Test-Path $LatestFile)) {
    @"
# STOP -- Non-Azure readiness pack not found
Run the prior non-Azure production readiness pack first.
Expected file:
$LatestFile
After that exists, rerun this burn-down pack.
"@ | Set-Content "$Out\00_STOP_RUN_PRIMARY_PACK_FIRST.md" -Encoding UTF8
    code "$Out\00_STOP_RUN_PRIMARY_PACK_FIRST.md"
    throw "Missing $LatestFile. Run the non-Azure readiness pack first."
}
$Latest = (Get-Content $LatestFile -Raw).Trim()
if (-not (Test-Path $Latest)) {
    throw "LATEST.txt points to missing folder: $Latest"
}
$ScorecardPath  = Join-Path $Latest "50_NONAZURE_SCORECARD.csv"
$QueuePath      = Join-Path $Latest "40_REMEDIATION_QUEUE.csv"
$PlaceholderPath= Join-Path $Latest "20_placeholder_scan.csv"
$UiPath         = Join-Path $Latest "21_ui_antipattern_scan.csv"
$SecretPath     = Join-Path $Latest "22_possible_secret_scan.csv"
$A11yPath       = Join-Path $Latest "26_accessibility_review.csv"
$RoutePath      = Join-Path $Latest "23_route_inventory.csv"
$DashboardPath  = Join-Path $Latest "24_dashboard_inventory.csv"
$WizardPath     = Join-Path $Latest "25_wizard_inventory.csv"
function Import-CsvSafe {
    param([string]$Path)
    if (Test-Path $Path) { return @(Import-Csv $Path) }
    return @()
}
$Score        = Import-CsvSafe $ScorecardPath
$Queue        = Import-CsvSafe $QueuePath
$Placeholders = Import-CsvSafe $PlaceholderPath
$UiHits       = Import-CsvSafe $UiPath
$SecretHits   = Import-CsvSafe $SecretPath
$A11yHits     = Import-CsvSafe $A11yPath
$RouteHits    = Import-CsvSafe $RoutePath
$DashboardHits= Import-CsvSafe $DashboardPath
$WizardHits   = Import-CsvSafe $WizardPath
$Fail    = @($Score | Where-Object { $_.Status -eq "FAIL" })
$Review  = @($Score | Where-Object { $_.Status -eq "REVIEW" })
$Pass    = @($Score | Where-Object { $_.Status -eq "PASS" })
$Skipped = @($Score | Where-Object { $_.Status -eq "SKIPPED" })
$P0 = @($Queue | Where-Object { $_.Priority -eq "P0" })
$P1 = @($Queue | Where-Object { $_.Priority -eq "P1" })
$P2 = @($Queue | Where-Object { $_.Priority -eq "P2" })
# ------------------------------------------------------------
# 01. Team execution assignments
# ------------------------------------------------------------
$Assignments = @()
function Add-Assignment {
    param(
        [string]$Priority,
        [string]$Owner,
        [string]$Area,
        [string]$Task,
        [string]$Evidence,
        [string]$Acceptance
    )
    $script:Assignments += [pscustomobject]@{
        Priority   = $Priority
        Owner      = $Owner
        Area       = $Area
        Task       = $Task
        Evidence   = $Evidence
        Acceptance = $Acceptance
        Status     = "Open"
    }
}
Add-Assignment "P0" "Dev 5 - QA/Release" "Repository hygiene" "Resolve any dirty worktree, stale branch, or untracked proof artifacts before final release scoring." "git status --short" "Clean worktree or intentional committed artifacts."
Add-Assignment "P0" "Dev 5 - QA/Release" "Security" "Review all possible secret hits and classify each as false positive, removed, or moved to secret store." "22_possible_secret_scan.csv" "Zero real secrets in repo."
Add-Assignment "P0" "Dev 1 - Platform" "Tenant/RBAC proof" "Prepare tenant isolation and RBAC test proof matrix for admin, teacher, parent, finance, admissions, and student roles." "05_QA_REGRESSION_MATRIX.csv" "Every protected role path has expected allow/deny result."
Add-Assignment "P1" "Dev 4 - Frontend/UX" "UI polish" "Replace off-brand dark/navy/gray-heavy treatments, dead links, placeholder surfaces, and inconsistent KPI cards." "21_ui_antipattern_scan.csv" "No unresolved UI anti-patterns on production-facing screens."
Add-Assignment "P1" "Dev 4 - Frontend/UX" "Dashboard polish" "Classify every dashboard/KPI as real data, seeded sandbox data, placeholder, broken, duplicate, or deferred." "24_dashboard_inventory.csv" "No unmarked fake/placeholder dashboard metric."
Add-Assignment "P1" "Dev 4 - Frontend/UX" "Accessibility" "Fix missing image alt text, button type issues, missing labels, weak focus states, and unclear empty states." "26_accessibility_review.csv" "No critical accessibility review items on demo/sandbox paths."
Add-Assignment "P1" "Dev 2 - SIS/Data" "SIS truth" "Verify no module creates shadow student, household, guardian, enrollment, attendance, grade, or transcript truth." "MASTER_INVENTORY.csv" "All student-record truth maps to SIS Core."
Add-Assignment "P1" "Dev 3 - Modules" "Admissions/enrollment/billing" "Confirm Admissions, Re-enrollment, and Billing use Core/SIS APIs and do not bypass lifecycle rules." "02_CORE_MODULE_ADDON_CLASSIFICATION.csv" "Workflow contracts documented and accepted."
Add-Assignment "P1" "Dev 5 - QA/Release" "Sandbox proof" "Execute sandbox-only login proof after Azure is ready: prefilled credentials, role landing pages, no real data, no console-critical errors." "06_SANDBOX_PROOF_CHECKLIST.csv" "Every sandbox proof row has artifact evidence."
Add-Assignment "P2" "TC / Product" "Canons approval" "Approve or edit Core Canon, SIS Canon, Modules/Add-ons Canon, Definition of Done, UI Polish Standard." "docs/crown-master-binder/canons" "Canons marked approved working authority."
foreach ($q in $Queue) {
    Add-Assignment $q.Priority $q.Owner $q.Area $q.Issue $q.Evidence $q.Action
}
$AssignmentsPath = "$Out\01_TEAM_ASSIGNMENTS.csv"
$Assignments | Sort-Object Priority, Owner, Area | Export-Csv $AssignmentsPath -NoTypeInformation
# ------------------------------------------------------------
# 02. UI polish action board
# ------------------------------------------------------------
$UiBoard = @()
function Add-UiTask {
    param(
        [string]$Priority,
        [string]$FindingType,
        [string]$Path,
        [string]$Line,
        [string]$Action
    )
    $script:UiBoard += [pscustomobject]@{
        Priority    = $Priority
        FindingType = $FindingType
        File        = $Path
        Line        = $Line
        Action      = $Action
        Owner       = "Dev 4 - Frontend/UX"
        Status      = "Open"
    }
}
foreach ($h in $UiHits | Select-Object -First 500) {
    Add-UiTask "P1" $h.FindingType $h.RelativePath $h.LineNumber "Replace dead link, off-brand dark treatment, hardcoded color, or temporary UI pattern."
}
foreach ($h in $Placeholders | Select-Object -First 500) {
    Add-UiTask "P1" $h.FindingType $h.RelativePath $h.LineNumber "Replace placeholder/incomplete copy or formally defer outside release."
}
foreach ($h in $A11yHits | Select-Object -First 500) {
    Add-UiTask "P1" $h.FindingType $h.RelativePath $h.LineNumber "Fix accessibility issue before sandbox/release proof."
}
$UiBoardPath = "$Out\02_UI_POLISH_ACTION_BOARD.csv"
$UiBoard | Export-Csv $UiBoardPath -NoTypeInformation
# ------------------------------------------------------------
# 03. Production release proof board
# ------------------------------------------------------------
$ProofBoard = @(
    [pscustomobject]@{ Gate="Repo clean"; Owner="Dev 5"; RequiredProof="git status --short returns empty or only approved committed docs"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Canons approved"; Owner="TC"; RequiredProof="Core, SIS, Modules/Add-ons, Definition of Done approved"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Security review"; Owner="Dev 5"; RequiredProof="Possible secret scan reviewed with zero real secrets"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Tenant isolation"; Owner="Dev 1"; RequiredProof="Cross-school access denied in API and UI"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="RBAC"; Owner="Dev 1"; RequiredProof="Each role allow/deny matrix tested"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="SIS data truth"; Owner="Dev 2"; RequiredProof="No shadow student/household/enrollment records"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Admissions workflow"; Owner="Dev 3"; RequiredProof="Inquiry/applicant/admit/enroll flow works"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Re-enrollment workflow"; Owner="Dev 3"; RequiredProof="Returning student workflow works"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Billing workflow"; Owner="Dev 3"; RequiredProof="Charges/payments/balances work"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Dashboard integrity"; Owner="Dev 4"; RequiredProof="No unmarked fake dashboard metrics"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="UI polish"; Owner="Dev 4"; RequiredProof="No unresolved critical UI polish items"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Sandbox login proof"; Owner="Dev 5"; RequiredProof="All sandbox school logins work and are prefilled"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Frontend Azure proof"; Owner="Azure team"; RequiredProof="Frontend root 200 and build.json SHA match"; Status="Waiting on Azure"; Evidence="" }
    [pscustomobject]@{ Gate="Backend Azure proof"; Owner="Azure team"; RequiredProof="Backend health 200 and SHA match"; Status="Waiting on Azure"; Evidence="" }
)
$ProofBoardPath = "$Out\03_PRODUCTION_RELEASE_PROOF_BOARD.csv"
$ProofBoard | Export-Csv $ProofBoardPath -NoTypeInformation
# ------------------------------------------------------------
# 04. Write executive burn-down markdown
# ------------------------------------------------------------
$TopQueueTable = if ($Queue.Count -gt 0) {
    ($Queue | Select-Object Priority,Area,Issue,Owner,Action | Sort-Object Priority, Area | Format-Table -AutoSize | Out-String)
} else {
    "No remediation rows found."
}
$TopUiTable = if ($UiBoard.Count -gt 0) {
    ($UiBoard | Select-Object -First 40 Priority,FindingType,File,Line,Action | Format-Table -AutoSize | Out-String)
} else {
    "No UI polish rows found."
}
$BurnDown = @"
# CROWN Non-Azure Burn-Down Board
Generated: $(Get-Date -Format s)
Source readiness packet: $Latest

## Current Non-Azure Score
PASS: $($Pass.Count)
REVIEW: $($Review.Count)
FAIL: $($Fail.Count)
SKIPPED: $($Skipped.Count)
TOTAL: $($Score.Count)

## Queue Counts
P0: $($P0.Count)
P1: $($P1.Count)
P2: $($P2.Count)
UI polish rows: $($UiBoard.Count)
Possible secret hits: $($SecretHits.Count)
Placeholder/incomplete hits: $($Placeholders.Count)
UI anti-pattern hits: $($UiHits.Count)
Accessibility review hits: $($A11yHits.Count)
Route references: $($RouteHits.Count)
Dashboard references: $($DashboardHits.Count)
Wizard references: $($WizardHits.Count)

## Rule
Azure remains separate. This board is for everything the team can clean while Azure/admin secret setup is being completed.

## Immediate Execution Order
1. Clear P0 queue.
2. Review possible secret hits.
3. Clean repository state.
4. Approve canons and Definition of Done.
5. Burn down UI polish board.
6. Classify dashboards, routes, and wizards.
7. Run role/tenant/sandbox proof after Azure is ready.
8. Re-score both Azure and non-Azure gates.

## P0/P1/P2 Remediation Queue
$TopQueueTable

## First UI Polish Rows
$TopUiTable

## Generated Files
- Team assignments: $AssignmentsPath
- UI polish board: $UiBoardPath
- Production release proof board: $ProofBoardPath
- Source scorecard: $ScorecardPath
- Source remediation queue: $QueuePath
"@
$BurnDownPath = "$Out\99_BURNDOWN_BOARD.md"
$BurnDown | Set-Content $BurnDownPath -Encoding UTF8
Copy-Item $BurnDownPath "$Ops\07_CURRENT_BURNDOWN_BOARD.md" -Force
Copy-Item $AssignmentsPath "$Ops\08_TEAM_ASSIGNMENTS.csv" -Force
Copy-Item $UiBoardPath "$Design\03_UI_POLISH_ACTION_BOARD.csv" -Force
Copy-Item $ProofBoardPath "$Ops\09_PRODUCTION_RELEASE_PROOF_BOARD.csv" -Force
# ------------------------------------------------------------
# 05. Create one-page dev prompts
# ------------------------------------------------------------
$DevPrompts = @{
"DEV1_PLATFORM_PROMPT.md" = @"
# Dev 1 -- Platform Core Assignment
## Mission
Protect CROWN's platform truth: auth, RBAC, tenant isolation, audit, request identity, and API guardrails.
## Work Now
1. Review tenant isolation and RBAC coverage.
2. Confirm no route/API bypasses permissions.
3. Create proof rows for each role.
4. Confirm audit logging exists for sensitive actions.
## Required Evidence
- Tenant isolation proof.
- Role allow/deny matrix.
- Audit event coverage list.
- P0/P1 issues closed or formally deferred.
## Do Not
- Change Azure setup.
- Create new product scope.
- Accept frontend-only permission enforcement.
"@
"DEV2_SIS_PROMPT.md" = @"
# Dev 2 -- SIS/Data Assignment
## Mission
Protect the canonical SIS truth.
## Work Now
1. Review student, household, guardian, enrollment, roster, attendance, grades, transcripts.
2. Confirm modules do not create shadow records.
3. Validate lifecycle states.
4. Map SIS APIs to Admissions, Re-enrollment, Billing, Parent Portal, Teacher Portal.
## Required Evidence
- Entity ownership map.
- Lifecycle state map.
- Shadow-record review.
- SIS API contract notes.
## Do Not
- Let modules invent separate student truth.
- Treat dashboards as data ownership.
"@
"DEV3_MODULES_PROMPT.md" = @"
# Dev 3 -- Modules Assignment
## Mission
Make first-wave modules operational and connected to Core/SIS.
## Work Now
1. Admissions: prove inquiry/applicant/admit/enroll flow.
2. Re-enrollment: prove returning-student workflow.
3. Billing: prove charges/payments/balances.
4. Communications: classify minimum viable spine.
## Required Evidence
- Workflow proof notes.
- API/data dependency map.
- Known gaps listed in remediation queue.
## Do Not
- Build module-specific duplicate records.
- Mark screens done without workflow proof.
"@
"DEV4_FRONTEND_PROMPT.md" = @"
# Dev 4 -- Frontend/UI Assignment
## Mission
Make CROWN look polished, consistent, light, royal, credible, and production-grade.
## Work Now
1. Use CROWN UI Polish Standard.
2. Apply crown-theme.css.
3. Replace inconsistent KPI cards with shared CROWN components.
4. Remove dead links, dark navy-heavy pages, placeholder copy, and raw debug content.
5. Classify dashboards, routes, and wizards.
## Required Evidence
- UI polish action board closed or reduced.
- Screenshots of admin, parent, teacher, finance/admissions dashboard.
- No unmarked fake dashboard metrics.
- No critical accessibility issues.
## Do Not
- Add another design style.
- Build new dashboards before underlying data contract exists.
"@
"DEV5_QA_RELEASE_PROMPT.md" = @"
# Dev 5 -- QA/Release Assignment
## Mission
Keep release proof honest.
## Work Now
1. Own non-Azure scorecard.
2. Own remediation queue.
3. Own sandbox proof checklist.
4. Own regression matrix.
5. Confirm repo/worktree cleanliness.
6. Prepare final evidence packet after Azure is ready.
## Required Evidence
- Clean scorecard.
- Closed P0/P1 rows.
- Sandbox proof screenshots/logs.
- Regression proof.
- Final GO/NO-GO packet.
## Do Not
- Accept verbal proof.
- Mark PASS without artifact evidence.
"@
}
foreach ($k in $DevPrompts.Keys) {
    $DevPrompts[$k] | Set-Content "$Out\$k" -Encoding UTF8
    Copy-Item "$Out\$k" "$Ops\$k" -Force
}
# ------------------------------------------------------------
# 06. Git status and open files
# ------------------------------------------------------------
git status --short | Set-Content "$Out\90_git_status_after_burndown.txt" -Encoding UTF8
@"
# CROWN Burn-Down Pack Complete
Generated:
$Out

Open first:
$BurnDownPath

Then:
$AssignmentsPath
$UiBoardPath
$ProofBoardPath

Important:
This did not touch Azure.
This did not deploy.
This created operating/control artifacts only.
"@ | Set-Content "$Out\00_README.md" -Encoding UTF8
code $BurnDownPath
code $AssignmentsPath
code $UiBoardPath
code $ProofBoardPath
code "$Out\DEV4_FRONTEND_PROMPT.md"
code "$Out\90_git_status_after_burndown.txt"
Write-Host ""
Write-Host "CROWN non-Azure burn-down pack complete."
Write-Host "Output: $Out"
Write-Host ""
Write-Host "Open first:"
Write-Host $BurnDownPath
Write-Host ""
Write-Host "Then assign:"
Write-Host $AssignmentsPath
Write-Host $UiBoardPath
Write-Host $ProofBoardPath
