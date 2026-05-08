$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
# ============================================================
# CROWN PHASE 2 -- NON-AZURE VALIDATION, PROOF PACK, COMMIT PREP
# Run from repo root.
# Does not touch Azure.
# ============================================================
Set-Location (git rev-parse --show-toplevel)
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path
$Out = Join-Path $Root "audit-artifacts\nonazure-phase2-validation\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = Join-Path $Docs "operations"
$Design = Join-Path $Docs "design-system"
$Canons = Join-Path $Docs "canons"
$Inventory = Join-Path $Docs "inventory"
$Scripts = Join-Path $Root "scripts\execution"
New-Item -ItemType Directory -Force -Path $Out,$Ops,$Design,$Canons,$Inventory,$Scripts | Out-Null
Start-Transcript -Path "$Out\00_PHASE2_RUN_LOG.txt" -Force | Out-Null
Write-Host "CROWN Phase 2 non-Azure validation"
Write-Host "Repo: $Root"
Write-Host "Output: $Out"

# ------------------------------------------------------------
# 01. Basic repo state
# ------------------------------------------------------------
$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD
$StatusBefore = (git status --short) -join "`n"
git status --short | Set-Content "$Out\01_git_status_before.txt" -Encoding UTF8
git status | Set-Content "$Out\02_git_status_full_before.txt" -Encoding UTF8
git log --oneline -20 | Set-Content "$Out\03_recent_commits.txt" -Encoding UTF8

# ------------------------------------------------------------
# 02. Find latest generated non-Azure artifacts
# ------------------------------------------------------------
$LatestReadinessPointer = Join-Path $Root "audit-artifacts\nonazure-production-readiness\LATEST.txt"
$LatestReadiness = ""
if (Test-Path $LatestReadinessPointer) {
    $LatestReadiness = (Get-Content $LatestReadinessPointer -Raw).Trim()
}
$LatestBurndown = ""
if (Test-Path "audit-artifacts\nonazure-burndown") {
    $LatestBurndown = Get-ChildItem (Join-Path $Root "audit-artifacts\nonazure-burndown") -Directory |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
@"
# Phase 2 Source Artifact Pointers
Generated: $(Get-Date -Format s)
Latest readiness packet:
$LatestReadiness
Latest burn-down packet:
$LatestBurndown
"@ | Set-Content "$Out\04_source_artifact_pointers.md" -Encoding UTF8

# ------------------------------------------------------------
# 03. Create production readiness command matrix
# ------------------------------------------------------------
$Commands = @()
function Add-Command {
    param(
        [string]$Area,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$Purpose
    )
    $script:Commands += [pscustomobject]@{
        Area = $Area
        WorkingDirectory = $WorkingDirectory
        Command = $Command
        Purpose = $Purpose
        Status = "Detected"
        OutputFile = ""
    }
}

# package.json command discovery
    $PackageFiles = Get-ChildItem $Root -Recurse -File -Filter package.json |
    Where-Object { $_.FullName -notmatch "\\node_modules\\" }
foreach ($pkg in $PackageFiles) {
    try {
        $json = Get-Content $pkg.FullName -Raw | ConvertFrom-Json
        $dir = Split-Path $pkg.FullName -Parent
        $relDir = Resolve-Path $dir -Relative
        if ($json.scripts) {
            foreach ($prop in $json.scripts.PSObject.Properties) {
                $name = $prop.Name
                if ($name -match "lint|typecheck|test|build|check") {
                    # Exclude server/watcher/reporter commands that block indefinitely
                    if ($name -notmatch "report|watch|dev|serve|start|headed|storybook") {
                        Add-Command "Frontend/Node" $relDir "npm run $name" "Detected package script: $name"
                    }
                }
            }
        }
    } catch {
        Add-Command "Frontend/Node" "." "echo package parse failed: $($pkg.FullName)" "package.json parse warning"
    }
}

# backend / python detection
if (Test-Path "backend\manage.py") {
    Add-Command "Backend/Django" "." "python backend\manage.py check" "Django system check"
    Add-Command "Backend/Django" "." "python backend\manage.py check --deploy" "Django deploy/security check"
    Add-Command "Backend/Django" "." "python backend\manage.py showmigrations" "Django migration inventory"
}
if ((Test-Path "pytest.ini") -or (Test-Path "pyproject.toml") -or (Test-Path "backend\pytest.ini")) {
    Add-Command "Backend/Python" "." "python -m pytest" "Python test suite"
}
$Commands | Export-Csv "$Out\05_detected_validation_commands.csv" -NoTypeInformation

# ------------------------------------------------------------
# 04. Run safe local validations and capture outputs
# ------------------------------------------------------------
$ValidationResults = @()
function Invoke-Validation {
    param(
        [string]$Area,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$Purpose,
        [int]$Index
    )
    $safeName = ($Area + "_" + $Index) -replace "[^a-zA-Z0-9_-]","_"
    $outputFile = "$Out\validation_$safeName.txt"
    Push-Location $WorkingDirectory
    try {
        "=== COMMAND ===" | Set-Content $outputFile -Encoding UTF8
        $Command | Add-Content $outputFile -Encoding UTF8
        "" | Add-Content $outputFile -Encoding UTF8
        "=== PURPOSE ===" | Add-Content $outputFile -Encoding UTF8
        $Purpose | Add-Content $outputFile -Encoding UTF8
        "" | Add-Content $outputFile -Encoding UTF8
        "=== OUTPUT ===" | Add-Content $outputFile -Encoding UTF8
        # Scope to Continue so non-zero exit from cmd.exe does not throw under ErrorActionPreference=Stop
        $savedEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        cmd.exe /c $Command >> $outputFile 2>&1
        $exit = $LASTEXITCODE
        $ErrorActionPreference = $savedEAP
        $status = if ($exit -eq 0) { "PASS" } else { "FAIL" }
        $script:ValidationResults += [pscustomobject]@{
            Area = $Area
            WorkingDirectory = $WorkingDirectory
            Command = $Command
            Purpose = $Purpose
            ExitCode = $exit
            Status = $status
            OutputFile = $outputFile
        }
    }
    catch {
        $_ | Out-String | Add-Content $outputFile -Encoding UTF8
        $script:ValidationResults += [pscustomobject]@{
            Area = $Area
            WorkingDirectory = $WorkingDirectory
            Command = $Command
            Purpose = $Purpose
            ExitCode = 999
            Status = "ERROR"
            OutputFile = $outputFile
        }
    }
    finally {
        Pop-Location
    }
}

$i = 0
foreach ($cmd in $Commands) {
    $i++
    Write-Host "Running validation $i/$($Commands.Count): $($cmd.Command)"
    Invoke-Validation -Area $cmd.Area -WorkingDirectory $cmd.WorkingDirectory -Command $cmd.Command -Purpose $cmd.Purpose -Index $i
}
$ValidationResults | Export-Csv "$Out\06_validation_results.csv" -NoTypeInformation

# ------------------------------------------------------------
# 05. Create release blocker board from validation + prior scans
# ------------------------------------------------------------
$Blockers = @()
function Add-Blocker {
    param(
        [string]$Priority,
        [string]$Area,
        [string]$Issue,
        [string]$Owner,
        [string]$Evidence,
        [string]$Fix
    )
    $script:Blockers += [pscustomobject]@{
        Priority = $Priority
        Area = $Area
        Issue = $Issue
        Owner = $Owner
        Evidence = $Evidence
        RequiredFix = $Fix
        Status = "Open"
    }
}

foreach ($v in $ValidationResults | Where-Object { $_.Status -ne "PASS" }) {
    $owner = if ($v.Area -match "Frontend|Node") { "Dev 4 / Dev 5" }
             elseif ($v.Area -match "Backend|Django|Python") { "Dev 1 / Dev 2 / Dev 5" }
             else { "Dev 5" }
    Add-Blocker "P0" $v.Area "Validation command failed: $($v.Command)" $owner $v.OutputFile "Fix failing validation and rerun Phase 2."
}
if (-not [string]::IsNullOrWhiteSpace($StatusBefore)) {
    Add-Blocker "P0" "Repository" "Worktree has uncommitted changes before Phase 2 commit." "Dev 5" "$Out\01_git_status_before.txt" "Review and intentionally commit, restore, or isolate changes."
}

# Pull prior scan counts if available
function Measure-CsvRows {
    param([string]$Path)
    if (Test-Path $Path) {
        return @((Import-Csv $Path)).Count
    }
    return 0
}

$PriorSecretScan      = if ($LatestReadiness) { Join-Path $LatestReadiness "22_possible_secret_scan.csv" } else { "" }
$PriorPlaceholderScan = if ($LatestReadiness) { Join-Path $LatestReadiness "20_placeholder_scan.csv" } else { "" }
$PriorUiScan          = if ($LatestReadiness) { Join-Path $LatestReadiness "21_ui_antipattern_scan.csv" } else { "" }
$PriorA11yScan        = if ($LatestReadiness) { Join-Path $LatestReadiness "26_accessibility_review.csv" } else { "" }

$SecretCount      = Measure-CsvRows $PriorSecretScan
$PlaceholderCount = Measure-CsvRows $PriorPlaceholderScan
$UiCount          = Measure-CsvRows $PriorUiScan
$A11yCount        = Measure-CsvRows $PriorA11yScan

if ($SecretCount -gt 0) {
    Add-Blocker "P0" "Security" "$SecretCount possible secret/token hits require review." "Dev 5" $PriorSecretScan "Classify each as false positive or remove/move secret."
}
if ($PlaceholderCount -gt 0) {
    Add-Blocker "P1" "UI/Product" "$PlaceholderCount placeholder/incomplete markers require review." "Dev 4 / Dev 5" $PriorPlaceholderScan "Replace or formally defer each production-facing marker."
}
if ($UiCount -gt 0) {
    Add-Blocker "P1" "UI Polish" "$UiCount UI anti-pattern hits require review." "Dev 4" $PriorUiScan "Replace dead links, dark/off-brand treatments, and hardcoded visual drift."
}
if ($A11yCount -gt 0) {
    Add-Blocker "P1" "Accessibility" "$A11yCount accessibility review hits require review." "Dev 4" $PriorA11yScan "Fix critical accessibility issues on sandbox/demo paths."
}
$Blockers | Sort-Object Priority, Area | Export-Csv "$Out\07_RELEASE_BLOCKER_BOARD.csv" -NoTypeInformation

# ------------------------------------------------------------
# 06. Create UI completion checklist for the team
# ------------------------------------------------------------
$UiChecklist = @(
    [pscustomobject]@{ ScreenGroup="Login"; Requirement="Sandbox-only login options are clear and sandbox credentials are prefilled."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Admin dashboard"; Requirement="Uses light royal CROWN theme, real/seeded-labeled KPIs, clean cards, no dead links."; Owner="Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Parent portal"; Requirement="Clear household/student summary, billing visibility, communications, no debug/placeholder content."; Owner="Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Teacher portal"; Requirement="Clear class/roster/attendance workflow, obvious next actions, no broken route links."; Owner="Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Admissions"; Requirement="Inquiry/applicant/checklist/status flow is visually complete and workflow-backed."; Owner="Dev 3 / Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Billing"; Requirement="Charges/payments/balances use consistent tables/cards and no fake financial data unless marked sandbox."; Owner="Dev 3 / Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="SIS records"; Requirement="Student, household, guardian, enrollment screens are consistent and role-safe."; Owner="Dev 2 / Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Empty states"; Requirement="Every empty table/card explains next step and does not look broken."; Owner="Dev 4"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Error states"; Requirement="Every error state is readable, actionable, and not raw stack/debug output."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence="" }
    [pscustomobject]@{ ScreenGroup="Mobile/responsive"; Requirement="Critical sandbox/demo flows work at laptop and tablet widths."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence="" }
)
$UiChecklist | Export-Csv "$Design\04_UI_COMPLETION_CHECKLIST.csv" -NoTypeInformation
Copy-Item "$Design\04_UI_COMPLETION_CHECKLIST.csv" "$Out\08_UI_COMPLETION_CHECKLIST.csv" -Force

# ------------------------------------------------------------
# 07. Create final release acceptance checklist
# ------------------------------------------------------------
$Acceptance = @(
    [pscustomobject]@{ Gate="Azure dashboard deploy"; Required="Handled by dev/admin team; frontend root 200"; Status="Waiting on Azure"; Evidence="" }
    [pscustomobject]@{ Gate="Azure backend deploy"; Required="Handled by dev/admin team; backend health SHA matches approved SHA"; Status="Waiting on Azure"; Evidence="" }
    [pscustomobject]@{ Gate="GitHub workflows"; Required="Dashboard and backend deploy workflows successful"; Status="Waiting on Azure"; Evidence="" }
    [pscustomobject]@{ Gate="Non-Azure validation"; Required="All local build/lint/test/check commands PASS"; Status="Open"; Evidence="$Out\06_validation_results.csv" }
    [pscustomobject]@{ Gate="Security scan"; Required="Zero real secrets in repo"; Status="Open"; Evidence=$PriorSecretScan }
    [pscustomobject]@{ Gate="Placeholder cleanup"; Required="No production-facing placeholder/incomplete markers"; Status="Open"; Evidence=$PriorPlaceholderScan }
    [pscustomobject]@{ Gate="UI polish"; Required="Critical pages use CROWN light royal standard"; Status="Open"; Evidence="$Design\04_UI_COMPLETION_CHECKLIST.csv" }
    [pscustomobject]@{ Gate="Tenant isolation"; Required="Cross-school access denied"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="RBAC"; Required="Role allow/deny matrix proven"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Sandbox logins"; Required="All sandbox school logins work and are prefilled"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Dashboards"; Required="All metrics real or clearly marked seeded sandbox"; Status="Open"; Evidence="" }
    [pscustomobject]@{ Gate="Release packet"; Required="Final scorecard and proof artifacts generated"; Status="Open"; Evidence="" }
)
$Acceptance | Export-Csv "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" -NoTypeInformation
Copy-Item "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" "$Out\09_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" -Force

# ------------------------------------------------------------
# 08. Summary
# ------------------------------------------------------------
$PassCount  = @($ValidationResults | Where-Object { $_.Status -eq "PASS" }).Count
$FailCount  = @($ValidationResults | Where-Object { $_.Status -eq "FAIL" }).Count
$ErrorCount = @($ValidationResults | Where-Object { $_.Status -eq "ERROR" }).Count
$BlockerP0  = @($Blockers | Where-Object { $_.Priority -eq "P0" }).Count
$BlockerP1  = @($Blockers | Where-Object { $_.Priority -eq "P1" }).Count
$BlockerP2  = @($Blockers | Where-Object { $_.Priority -eq "P2" }).Count

$Decision = if ($FailCount -eq 0 -and $ErrorCount -eq 0 -and $BlockerP0 -eq 0) {
    "NON_AZURE_PHASE2_CLEAN_CANDIDATE"
} else {
    "NON_AZURE_PHASE2_REMEDIATION_REQUIRED"
}

$ValidationTable = $ValidationResults | Format-Table -AutoSize | Out-String
$BlockerTable    = $Blockers | Sort-Object Priority, Area | Format-Table -AutoSize | Out-String

$Summary = @"
# CROWN Phase 2 Non-Azure Validation Summary
Generated: $(Get-Date -Format s)
Repo: $Root
Branch: $Branch
HEAD: $Head
HEAD_FULL: $HeadFull

## Decision
$Decision

## Validation Results
PASS: $PassCount
FAIL: $FailCount
ERROR: $ErrorCount
TOTAL: $($ValidationResults.Count)

## Blocker Counts
P0: $BlockerP0
P1: $BlockerP1
P2: $BlockerP2
TOTAL: $($Blockers.Count)

## Prior Scan Counts
Possible secret hits: $SecretCount
Placeholder/incomplete hits: $PlaceholderCount
UI anti-pattern hits: $UiCount
Accessibility review hits: $A11yCount

## Key Files
- Validation results: $Out\06_validation_results.csv
- Release blocker board: $Out\07_RELEASE_BLOCKER_BOARD.csv
- UI completion checklist: $Out\08_UI_COMPLETION_CHECKLIST.csv
- Final release acceptance checklist: $Out\09_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv
- Git status before: $Out\01_git_status_before.txt

## Execution Order
1. Open release blocker board.
2. Clear all P0 blockers first.
3. Clear validation failures.
4. Review possible secret hits.
5. Burn down UI polish and placeholder hits.
6. Complete UI completion checklist.
7. Wait for Azure team to finish secrets/deploys.
8. Run final Azure + non-Azure combined scorecard.

## Validation Table
$ValidationTable

## Blocker Table
$BlockerTable
"@

$Summary | Set-Content "$Out\99_PHASE2_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_PHASE2_SUMMARY.md" "$Ops\11_CURRENT_PHASE2_SUMMARY.md" -Force

# ------------------------------------------------------------
# 09. Optional controlled commit of generated control artifacts
# ------------------------------------------------------------
git status --short | Set-Content "$Out\90_git_status_before_commit.txt" -Encoding UTF8
$CommitMessage = "audit: add non-azure phase2 validation and release readiness controls"
git add --force "$Out" "$Docs" "$Scripts" 2>$null
git status --short | Set-Content "$Out\91_git_status_staged.txt" -Encoding UTF8
$Staged = git diff --cached --name-only
if ($Staged) {
    git commit -m $CommitMessage
    git rev-parse --short HEAD | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
} else {
    "No staged changes to commit." | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
}
git status --short | Set-Content "$Out\93_git_status_after.txt" -Encoding UTF8

# ------------------------------------------------------------
# 10. Open outputs
# ------------------------------------------------------------
code "$Out\99_PHASE2_SUMMARY.md"
code "$Out\07_RELEASE_BLOCKER_BOARD.csv"
code "$Out\06_validation_results.csv"
code "$Design\04_UI_COMPLETION_CHECKLIST.csv"
code "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv"
code "$Out\93_git_status_after.txt"

Write-Host ""
Write-Host "CROWN Phase 2 complete."
Write-Host "Decision: $Decision"
Write-Host "Output: $Out"
Write-Host ""
Write-Host "Open first:"
Write-Host "$Out\99_PHASE2_SUMMARY.md"
Write-Host "$Out\07_RELEASE_BLOCKER_BOARD.csv"

Stop-Transcript | Out-Null
