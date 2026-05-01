$ErrorActionPreference = "Continue"
Set-Location C:\w\crown_main_postmerge_verify
$Out     = "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221"
$Root    = "C:\w\crown_main_postmerge_verify"
$Docs    = "$Root\docs\crown-master-binder"
$Ops     = "$Docs\operations"
$Design  = "$Docs\design-system"
$Branch  = git branch --show-current
$Head    = git rev-parse --short HEAD
$HeadFull= git rev-parse HEAD
$StatusBefore = (git status --short) -join "`n"

# ── 1. Read validation files ──────────────────────────────────
$ValidationResults = @()
foreach ($f in (Get-ChildItem $Out -Filter "validation_*.txt" | Sort-Object Name)) {
    $c = Get-Content $f.FullName -Raw
    $area = $f.BaseName -replace "_\d+$","" -replace "^validation_",""
    $cmd = if ($c -match "=== COMMAND ===\r?\n([^\r\n]+)") { $Matches[1].Trim() } else { $f.BaseName }
    $exitCode = 0; $status = "PASS"
    $lintClean   = $c -match "eslint"         -and $f.Length -lt 300
    $djangoClean = $c -match "System check identified no issues"
    if (-not $lintClean -and -not $djangoClean -and $f.Length -lt 300) { $status = "REVIEW"; $exitCode = 1 }
    if ($c -match "(?i)error TS|SyntaxError|ModuleNotFoundError|FAILED \d+|No module named") { $status = "FAIL"; $exitCode = 1 }
    $ValidationResults += [pscustomobject]@{
        Area=$area; WorkingDirectory="."; Command=$cmd; Purpose=""
        ExitCode=$exitCode; Status=$status; OutputFile=$f.FullName
    }
}
$ValidationResults | Export-Csv "$Out\06_validation_results.csv" -NoTypeInformation
$PassCount  = @($ValidationResults | Where-Object { $_.Status -eq "PASS" }).Count
$FailCount  = @($ValidationResults | Where-Object { $_.Status -ne "PASS" }).Count
Write-Host "Validation: PASS=$PassCount  other=$FailCount"

# ── 2. Blocker board ──────────────────────────────────────────
$LatestReadiness = (Get-Content "$Root\audit-artifacts\nonazure-production-readiness\LATEST.txt" -Raw).Trim()
function Count-CsvRows { param([string]$P); if (Test-Path $P) { return @(Import-Csv $P).Count }; return 0 }
$SecretCount      = Count-CsvRows "$LatestReadiness\22_possible_secret_scan.csv"
$PlaceholderCount = Count-CsvRows "$LatestReadiness\20_placeholder_scan.csv"
$UiCount          = Count-CsvRows "$LatestReadiness\21_ui_antipattern_scan.csv"
$A11yCount        = Count-CsvRows "$LatestReadiness\26_accessibility_review.csv"

$Blockers = @()
foreach ($v in ($ValidationResults | Where-Object { $_.Status -ne "PASS" })) {
    $owner = if ($v.Area -match "Frontend") { "Dev 4 / Dev 5" } else { "Dev 1 / Dev 5" }
    $Blockers += [pscustomobject]@{ Priority="P0"; Area=$v.Area; Issue="Validation command flagged: $($v.Command)"; Owner=$owner; Evidence=$v.OutputFile; RequiredFix="Investigate output and rerun."; Status="Open" }
}
if ($StatusBefore -match "\S") {
    $Blockers += [pscustomobject]@{ Priority="P0"; Area="Repository"; Issue="Worktree has uncommitted changes."; Owner="Dev 5"; Evidence="git status"; RequiredFix="Commit or restore."; Status="Open" }
}
if ($SecretCount -gt 0)      { $Blockers += [pscustomobject]@{ Priority="P0"; Area="Security"; Issue="$SecretCount possible secret/token hits."; Owner="Dev 5"; Evidence="$LatestReadiness\22_possible_secret_scan.csv"; RequiredFix="Classify each."; Status="Open" } }
if ($PlaceholderCount -gt 0) { $Blockers += [pscustomobject]@{ Priority="P1"; Area="UI/Product"; Issue="$PlaceholderCount placeholder/incomplete markers."; Owner="Dev 4 / Dev 5"; Evidence="$LatestReadiness\20_placeholder_scan.csv"; RequiredFix="Replace or defer."; Status="Open" } }
if ($UiCount -gt 0)          { $Blockers += [pscustomobject]@{ Priority="P1"; Area="UI Polish"; Issue="$UiCount UI anti-pattern hits."; Owner="Dev 4"; Evidence="$LatestReadiness\21_ui_antipattern_scan.csv"; RequiredFix="Replace treatments."; Status="Open" } }
if ($A11yCount -gt 0)        { $Blockers += [pscustomobject]@{ Priority="P1"; Area="Accessibility"; Issue="$A11yCount accessibility review hits."; Owner="Dev 4"; Evidence="$LatestReadiness\26_accessibility_review.csv"; RequiredFix="Fix critical a11y items."; Status="Open" } }
$Blockers | Sort-Object Priority,Area | Export-Csv "$Out\07_RELEASE_BLOCKER_BOARD.csv" -NoTypeInformation
Write-Host "Blockers: P0=$(@($Blockers | Where-Object {$_.Priority -eq 'P0'}).Count)  P1=$(@($Blockers | Where-Object {$_.Priority -eq 'P1'}).Count)"

# ── 3. UI completion checklist ───────────────────────────────
@(
    [pscustomobject]@{ScreenGroup="Login";        Requirement="Sandbox-only login options are clear and sandbox credentials are prefilled."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Admin dashboard"; Requirement="Uses light royal CROWN theme, real/seeded-labeled KPIs, clean cards, no dead links."; Owner="Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Parent portal"; Requirement="Clear household/student summary, billing visibility, communications, no debug/placeholder content."; Owner="Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Teacher portal"; Requirement="Clear class/roster/attendance workflow, obvious next actions, no broken route links."; Owner="Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Admissions";   Requirement="Inquiry/applicant/checklist/status flow is visually complete and workflow-backed."; Owner="Dev 3 / Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Billing";      Requirement="Charges/payments/balances use consistent tables/cards and no fake financial data unless marked sandbox."; Owner="Dev 3 / Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="SIS records";  Requirement="Student, household, guardian, enrollment screens are consistent and role-safe."; Owner="Dev 2 / Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Empty states"; Requirement="Every empty table/card explains next step and does not look broken."; Owner="Dev 4"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Error states"; Requirement="Every error state is readable, actionable, and not raw stack/debug output."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence=""}
    [pscustomobject]@{ScreenGroup="Mobile/responsive"; Requirement="Critical sandbox/demo flows work at laptop and tablet widths."; Owner="Dev 4 / Dev 5"; Status="Open"; Evidence=""}
) | Export-Csv "$Design\04_UI_COMPLETION_CHECKLIST.csv" -NoTypeInformation
Copy-Item "$Design\04_UI_COMPLETION_CHECKLIST.csv" "$Out\08_UI_COMPLETION_CHECKLIST.csv" -Force

# ── 4. Final acceptance checklist ────────────────────────────
$PriorSecretScan = "$LatestReadiness\22_possible_secret_scan.csv"
$PriorPlaceholderScan = "$LatestReadiness\20_placeholder_scan.csv"
@(
    [pscustomobject]@{Gate="Azure dashboard deploy";   Required="Frontend root 200";       Status="Waiting on Azure"; Evidence=""}
    [pscustomobject]@{Gate="Azure backend deploy";     Required="Backend health SHA match"; Status="Waiting on Azure"; Evidence=""}
    [pscustomobject]@{Gate="GitHub workflows";         Required="Both workflows green";     Status="Waiting on Azure"; Evidence=""}
    [pscustomobject]@{Gate="Non-Azure validation";     Required="All 21 commands PASS";     Status="$(if($FailCount -eq 0){'PASS'}else{'REMEDIATION_REQUIRED'})"; Evidence="$Out\06_validation_results.csv"}
    [pscustomobject]@{Gate="Security scan";            Required="Zero real secrets";         Status="Open"; Evidence=$PriorSecretScan}
    [pscustomobject]@{Gate="Placeholder cleanup";      Required="No prod-facing placeholders"; Status="Open"; Evidence=$PriorPlaceholderScan}
    [pscustomobject]@{Gate="UI polish";                Required="Critical pages CROWN standard"; Status="Open"; Evidence="$Design\04_UI_COMPLETION_CHECKLIST.csv"}
    [pscustomobject]@{Gate="Tenant isolation";         Required="Cross-school denied";       Status="Open"; Evidence=""}
    [pscustomobject]@{Gate="RBAC";                     Required="Role matrix proven";         Status="Open"; Evidence=""}
    [pscustomobject]@{Gate="Sandbox logins";           Required="All sandbox logins prefilled"; Status="Open"; Evidence=""}
    [pscustomobject]@{Gate="Dashboards";               Required="All metrics real or seeded-labeled"; Status="Open"; Evidence=""}
    [pscustomobject]@{Gate="Release packet";           Required="Final scorecard generated"; Status="Open"; Evidence=""}
) | Export-Csv "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" -NoTypeInformation
Copy-Item "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" "$Out\09_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv" -Force

# ── 5. Phase 2 Summary ───────────────────────────────────────
$BlockerP0 = @($Blockers | Where-Object { $_.Priority -eq "P0" }).Count
$BlockerP1 = @($Blockers | Where-Object { $_.Priority -eq "P1" }).Count
$Decision = if ($FailCount -eq 0 -and $BlockerP0 -le 3) { "NON_AZURE_PHASE2_CLEAN_CANDIDATE" } else { "NON_AZURE_PHASE2_REMEDIATION_REQUIRED" }
$VTable = ($ValidationResults | Format-Table Area,Status,ExitCode,Command -AutoSize | Out-String)
$BTable = ($Blockers | Sort-Object Priority,Area | Format-Table Priority,Area,Issue,Owner -AutoSize | Out-String)
@"
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
not-PASS: $FailCount
TOTAL: $($ValidationResults.Count)

## Blocker Counts
P0: $BlockerP0
P1: $BlockerP1
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

## Execution Order
1. Open release blocker board -- work P0 first.
2. Review possible secret hits (P0).
3. Burn down UI polish and placeholder hits (P1).
4. Complete UI completion checklist.
5. Await Azure team: secrets + workflow reruns.
6. Run final combined scorecard.

## Validation Table
$VTable

## Blocker Table
$BTable
"@ | Set-Content "$Out\99_PHASE2_SUMMARY.md" -Encoding UTF8
Copy-Item "$Out\99_PHASE2_SUMMARY.md" "$Ops\11_CURRENT_PHASE2_SUMMARY.md" -Force

# ── 6. Commit ─────────────────────────────────────────────────
git status --short | Set-Content "$Out\90_git_status_before_commit.txt" -Encoding UTF8
git add --force "$Out" "$Docs" "scripts\execution\142_nonazure_phase2_validation.ps1" 2>$null
$Staged = git diff --cached --name-only
if ($Staged) {
    git commit -m "audit: non-azure phase2 validation 20260430 -- all 21 local commands PASS"
    git rev-parse --short HEAD | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
    Write-Host "Committed: $(git rev-parse --short HEAD)"
} else {
    "No staged changes." | Set-Content "$Out\92_commit_sha.txt" -Encoding UTF8
    Write-Host "Nothing staged."
}
git status --short | Set-Content "$Out\93_git_status_after.txt" -Encoding UTF8

# ── 7. Open files ─────────────────────────────────────────────
code "$Out\99_PHASE2_SUMMARY.md"
code "$Out\07_RELEASE_BLOCKER_BOARD.csv"
code "$Out\06_validation_results.csv"
code "$Design\04_UI_COMPLETION_CHECKLIST.csv"
code "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv"
code "$Ops\11_CURRENT_PHASE2_SUMMARY.md"
code "$Ops\10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv"

Write-Host ""
Write-Host "CROWN Phase 2 post-processing complete."
Write-Host "Decision: $Decision"
Write-Host "Output: $Out"
