# scripts/execution/137_build_51x51_remediation_workpacks.ps1
# CROWN 51x51 remediation workpack builder
# Purpose:
# - Reads the generated 51x51 remediation queue.
# - Produces owner-specific workpacks.
# - Separates FAIL/REVIEW rows into test, tenant, CI, frontend, backend, security, data, and product categories.
# - Creates sprint-ready markdown and CSV files.
# - Does not modify application code.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step($m) { Write-Host "[51x51-WORKPACKS] $m" -ForegroundColor Cyan }
function Ensure-Dir($p) { if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function Safe-Name($s) { return (($s -replace '[^A-Za-z0-9_.-]+','_').Trim('_')) }

try {
    $RepoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
    if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
} catch {
    $RepoRoot = (Get-Location).Path
}

Set-Location $RepoRoot

$Audit = "audit-artifacts\51x51-module-integrity\20260428_042020"
$Queue = Join-Path $Audit "REMEDIATION_QUEUE"
$FailCsv = Join-Path $Queue "01_FAIL_ROWS.csv"
$ReviewCsv = Join-Path $Queue "02_REVIEW_ROWS.csv"
$ModuleCsv = Join-Path $Queue "03_MODULE_REMEDIATION_SUMMARY.csv"
$FixCsv = Join-Path $Queue "04_FULL_FIX_MATRIX.csv"

if (-not (Test-Path $FailCsv)) { throw "Missing $FailCsv" }
if (-not (Test-Path $ReviewCsv)) { throw "Missing $ReviewCsv" }
if (-not (Test-Path $ModuleCsv)) { throw "Missing $ModuleCsv" }
if (-not (Test-Path $FixCsv)) { throw "Missing $FixCsv" }

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Queue "WORKPACKS_$Stamp"
Ensure-Dir $Out
Ensure-Dir (Join-Path $Out "owners")
Ensure-Dir (Join-Path $Out "categories")
Ensure-Dir (Join-Path $Out "modules")

Write-Step "Reading remediation queue."
$failRows = @(Import-Csv $FailCsv)
$reviewRows = @(Import-Csv $ReviewCsv)
$moduleRows = @(Import-Csv $ModuleCsv)
$fixRows = @(Import-Csv $FixCsv)

$allOpenRows = @()
$allOpenRows += $failRows
$allOpenRows += $reviewRows

function Get-WorkCategory($row) {
    $text = "$($row.CheckCategory) $($row.CheckName) $($row.RequiredFixIfMissing) $($row.Status)"
    if ($text -match "Tenant|cross-school|cross-tenant|isolation") { return "Tenant-Isolation" }
    if ($text -match "Permission|RBAC|unauthorized|403|role") { return "Permission-Security" }
    if ($text -match "Unit Tests|API Tests|Frontend Tests|Playwright|E2E|Negative Tests|test") { return "Test-Coverage" }
    if ($text -match "CI|workflow|pipeline|gate") { return "CI-Gate-Wiring" }
    if ($text -match "Frontend|Route|Dashboard|Form|Table|UI|screen|portal") { return "Frontend-Operations" }
    if ($text -match "API|Serializer|Service|Validation|Endpoint|Error") { return "Backend-API" }
    if ($text -match "Data|Model|Migration|Tenant Key|Shadow Record") { return "Data-Model" }
    if ($text -match "Audit|Sensitive|FERPA|COPPA|PII|Security") { return "Security-Compliance" }
    if ($text -match "KPI|Reporting|Export|Metric") { return "KPI-Reporting" }
    if ($text -match "Product|Canonical|Definition|Owner|Layer|Boundary") { return "Product-Governance" }
    return "General-Remediation"
}

$expanded = foreach ($r in $allOpenRows) {
    $category = Get-WorkCategory $r
    [pscustomobject]@{
        ModuleId             = $r.ModuleId
        Layer                = $r.Layer
        Module               = $r.Module
        Owner                = $r.Owner
        CheckId              = $r.CheckId
        CheckCategory        = $r.CheckCategory
        CheckName            = $r.CheckName
        Severity             = $r.Severity
        WorkCategory         = $category
        Status               = $r.Status
        RequiredFixIfMissing = $r.RequiredFixIfMissing
        EvidenceFile         = $r.EvidenceFile
        SprintPriority       = if ($r.Severity -eq "FAIL") { "P1" } else { "P2" }
    }
}

$expandedCsv = Join-Path $Out "00_ALL_OPEN_REMEDIATION_ROWS.csv"
$expanded | Export-Csv -NoTypeInformation -Encoding UTF8 $expandedCsv

Write-Step "Building owner workpacks."
$owners = $expanded | Group-Object Owner | Sort-Object Name
foreach ($ownerGroup in $owners) {
    $owner = $ownerGroup.Name
    $ownerSafe = Safe-Name $owner
    $ownerRows = @($ownerGroup.Group | Sort-Object SprintPriority, ModuleId, CheckId)
    $ownerCsv = Join-Path $Out "owners\$ownerSafe.csv"
    $ownerMd = Join-Path $Out "owners\$ownerSafe.md"
    $ownerRows | Export-Csv -NoTypeInformation -Encoding UTF8 $ownerCsv

    $p1 = @($ownerRows | Where-Object SprintPriority -eq "P1")
    $p2 = @($ownerRows | Where-Object SprintPriority -eq "P2")
    $moduleCount = @($ownerRows | Select-Object ModuleId -Unique).Count

    $lines = @()
    $lines += "# CROWN 51x51 Remediation Workpack - $owner"
    $lines += ""
    $lines += "Generated: $(Get-Date -Format o)"
    $lines += ""
    $lines += "## Decision"
    $lines += ""
    $lines += "**FIX REQUIRED**"
    $lines += ""
    $lines += "## Counts"
    $lines += ""
    $lines += "- Modules affected: $moduleCount"
    $lines += "- P1 FAIL rows: $($p1.Count)"
    $lines += "- P2 REVIEW rows: $($p2.Count)"
    $lines += "- Total open rows: $($ownerRows.Count)"
    $lines += ""
    $lines += "## Execution Rule"
    $lines += ""
    $lines += "Do not mark any module complete until every P1 and P2 row is closed, tests are added, CI is wired, and the 51x51 audit reruns with zero FAIL and zero REVIEW for that module."
    $lines += ""
    $lines += "## P1 FAIL Rows"
    $lines += ""
    $lines += "| ModuleId | Module | Category | Check | Required Fix | Evidence |"
    $lines += "|---:|---|---|---|---|---|"
    foreach ($r in $p1) {
        $lines += "| $($r.ModuleId) | $($r.Module) | $($r.WorkCategory) | $($r.CheckName) | $($r.RequiredFixIfMissing) | $($r.EvidenceFile) |"
    }
    $lines += ""
    $lines += "## P2 REVIEW Rows"
    $lines += ""
    $lines += "| ModuleId | Module | Category | Check | Required Fix | Evidence |"
    $lines += "|---:|---|---|---|---|---|"
    foreach ($r in $p2) {
        $lines += "| $($r.ModuleId) | $($r.Module) | $($r.WorkCategory) | $($r.CheckName) | $($r.RequiredFixIfMissing) | $($r.EvidenceFile) |"
    }
    $lines += ""
    $lines += "## Verification Required"
    $lines += ""
    $lines += "After repairs, run:"
    $lines += ""
    $lines += '```powershell'
    $lines += "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1"
    $lines += "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1 -RunBackendChecks -RunFrontendChecks -RunPlaywright"
    $lines += '```'
    $lines | Set-Content -Encoding UTF8 $ownerMd
}

Write-Step "Building category workpacks."
$categories = $expanded | Group-Object WorkCategory | Sort-Object Name
foreach ($catGroup in $categories) {
    $cat = $catGroup.Name
    $catSafe = Safe-Name $cat
    $catRows = @($catGroup.Group | Sort-Object SprintPriority, Owner, ModuleId, CheckId)
    $catCsv = Join-Path $Out "categories\$catSafe.csv"
    $catMd = Join-Path $Out "categories\$catSafe.md"
    $catRows | Export-Csv -NoTypeInformation -Encoding UTF8 $catCsv

    $p1 = @($catRows | Where-Object SprintPriority -eq "P1")
    $p2 = @($catRows | Where-Object SprintPriority -eq "P2")

    $lines = @()
    $lines += "# CROWN 51x51 Category Workpack - $cat"
    $lines += ""
    $lines += "Generated: $(Get-Date -Format o)"
    $lines += ""
    $lines += "## Counts"
    $lines += ""
    $lines += "- P1 FAIL rows: $($p1.Count)"
    $lines += "- P2 REVIEW rows: $($p2.Count)"
    $lines += "- Total rows: $($catRows.Count)"
    $lines += ""
    $lines += "## Rows"
    $lines += ""
    $lines += "| Priority | Owner | ModuleId | Module | Check | Required Fix |"
    $lines += "|---|---|---:|---|---|---|"
    foreach ($r in $catRows) {
        $lines += "| $($r.SprintPriority) | $($r.Owner) | $($r.ModuleId) | $($r.Module) | $($r.CheckName) | $($r.RequiredFixIfMissing) |"
    }
    $lines | Set-Content -Encoding UTF8 $catMd
}

Write-Step "Building module workpacks."
$modules = $expanded | Group-Object ModuleId | Sort-Object {[int]$_.Name}
foreach ($modGroup in $modules) {
    $rows = @($modGroup.Group | Sort-Object SprintPriority, CheckId)
    $first = $rows[0]
    $modSafe = "{0:D2}_{1}" -f [int]$first.ModuleId, (Safe-Name $first.Module)
    $modCsv = Join-Path $Out "modules\$modSafe.csv"
    $modMd = Join-Path $Out "modules\$modSafe.md"
    $rows | Export-Csv -NoTypeInformation -Encoding UTF8 $modCsv

    $p1 = @($rows | Where-Object SprintPriority -eq "P1")
    $p2 = @($rows | Where-Object SprintPriority -eq "P2")

    $lines = @()
    $lines += "# CROWN Module Remediation - $($first.Module)"
    $lines += ""
    $lines += "Generated: $(Get-Date -Format o)"
    $lines += ""
    $lines += "## Module"
    $lines += ""
    $lines += "- ModuleId: $($first.ModuleId)"
    $lines += "- Layer: $($first.Layer)"
    $lines += "- Owner: $($first.Owner)"
    $lines += "- P1 FAIL rows: $($p1.Count)"
    $lines += "- P2 REVIEW rows: $($p2.Count)"
    $lines += ""
    $lines += "## Required Work"
    $lines += ""
    $lines += "| Priority | Category | Check | Required Fix | Evidence |"
    $lines += "|---|---|---|---|---|"
    foreach ($r in $rows) {
        $lines += "| $($r.SprintPriority) | $($r.WorkCategory) | $($r.CheckName) | $($r.RequiredFixIfMissing) | $($r.EvidenceFile) |"
    }
    $lines += ""
    $lines += "## Completion Standard"
    $lines += ""
    $lines += "This module is not complete until this workpack has zero open rows and the 51x51 audit rerun returns zero FAIL and zero REVIEW for ModuleId $($first.ModuleId)."
    $lines | Set-Content -Encoding UTF8 $modMd
}

Write-Step "Building sprint command board."
$priorityModules = $moduleRows |
    Where-Object { $_.Decision -eq "FIX REQUIRED" } |
    Sort-Object @{Expression={[int]$_.FAIL};Descending=$true}, @{Expression={[int]$_.REVIEW};Descending=$true}, @{Expression={[int]$_.ModuleId};Descending=$false}

$board = Join-Path $Out "01_SPRINT_COMMAND_BOARD.md"
$lines = @()
$lines += "# CROWN 51x51 Sprint Command Board"
$lines += ""
$lines += "Generated: $(Get-Date -Format o)"
$lines += ""
$lines += "## Release Decision"
$lines += ""
$lines += "**NO-GO / FIX REQUIRED**"
$lines += ""
$lines += "## Open Work"
$lines += ""
$lines += "- P1 FAIL rows: $(@($expanded | Where-Object SprintPriority -eq 'P1').Count)"
$lines += "- P2 REVIEW rows: $(@($expanded | Where-Object SprintPriority -eq 'P2').Count)"
$lines += "- Affected modules: $(@($expanded | Select-Object ModuleId -Unique).Count)"
$lines += ""
$lines += "## Priority Module Order"
$lines += ""
$lines += "| Rank | ModuleId | Layer | Module | Owner | FAIL | REVIEW |"
$lines += "|---:|---:|---|---|---|---:|---:|"
$rank = 1
foreach ($m in $priorityModules) {
    $lines += "| $rank | $($m.ModuleId) | $($m.Layer) | $($m.Module) | $($m.Owner) | $($m.FAIL) | $($m.REVIEW) |"
    $rank++
}
$lines += ""
$lines += "## Category Attack Plan"
$lines += ""
$lines += "1. Close Test-Coverage rows first."
$lines += "2. Close Tenant-Isolation and Permission-Security rows before any sandbox expansion."
$lines += "3. Close CI-Gate-Wiring rows so the fixes stay enforced."
$lines += "4. Close Frontend-Operations rows for user-visible dashboard/module completion."
$lines += "5. Close Backend-API and Data-Model rows for system integrity."
$lines += ""
$lines += "## Workpack Locations"
$lines += ""
$lines += "- Owner workpacks: owners/"
$lines += "- Category workpacks: categories/"
$lines += "- Module workpacks: modules/"
$lines += "- Full open row CSV: 00_ALL_OPEN_REMEDIATION_ROWS.csv"
$lines | Set-Content -Encoding UTF8 $board

Write-Step "Building short leadership summary."
$leadership = Join-Path $Out "00_LEADERSHIP_SUMMARY.md"
$top10 = $priorityModules | Select-Object -First 10

$categorySummary = $expanded |
    Group-Object WorkCategory |
    ForEach-Object {
        [pscustomobject]@{
            Category = $_.Name
            P1 = @($_.Group | Where-Object SprintPriority -eq "P1").Count
            P2 = @($_.Group | Where-Object SprintPriority -eq "P2").Count
            Total = $_.Count
        }
    } |
    Sort-Object @{Expression="P1";Descending=$true}, @{Expression="P2";Descending=$true}

$lines = @()
$lines += "# CROWN 51x51 Leadership Summary"
$lines += ""
$lines += "Generated: $(Get-Date -Format o)"
$lines += ""
$lines += "## Current Status"
$lines += ""
$lines += "**NO-GO / FIX REQUIRED**"
$lines += ""
$lines += "The remediation queue is now execution-ready. Work is split by owner, category, and module."
$lines += ""
$lines += "## Counts"
$lines += ""
$lines += "- P1 FAIL rows: $(@($expanded | Where-Object SprintPriority -eq 'P1').Count)"
$lines += "- P2 REVIEW rows: $(@($expanded | Where-Object SprintPriority -eq 'P2').Count)"
$lines += "- Affected modules: $(@($expanded | Select-Object ModuleId -Unique).Count)"
$lines += ""
$lines += "## Top 10 Priority Modules"
$lines += ""
$lines += "| Rank | ModuleId | Module | Owner | FAIL | REVIEW |"
$lines += "|---:|---:|---|---|---:|---:|"
$rank = 1
foreach ($m in $top10) {
    $lines += "| $rank | $($m.ModuleId) | $($m.Module) | $($m.Owner) | $($m.FAIL) | $($m.REVIEW) |"
    $rank++
}
$lines += ""
$lines += "## Category Summary"
$lines += ""
$lines += "| Category | P1 FAIL | P2 REVIEW | Total |"
$lines += "|---|---:|---:|---:|"
foreach ($c in $categorySummary) {
    $lines += "| $($c.Category) | $($c.P1) | $($c.P2) | $($c.Total) |"
}
$lines += ""
$lines += "## Next Gate"
$lines += ""
$lines += "After owner workpacks are closed, rerun:"
$lines += ""
$lines += '```powershell'
$lines += "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1 -RunBackendChecks -RunFrontendChecks -RunPlaywright"
$lines += '```'
$lines += ""
$lines += "GO requires zero FAIL, zero REVIEW, and completed live audit."
$lines | Set-Content -Encoding UTF8 $leadership

Write-Step "Creating index."
$index = Join-Path $Out "START_HERE.md"
$lines = @()
$lines += "# START HERE - CROWN 51x51 Remediation Workpacks"
$lines += ""
$lines += "Generated: $(Get-Date -Format o)"
$lines += ""
$lines += "## Open First"
$lines += ""
$lines += "1. 00_LEADERSHIP_SUMMARY.md"
$lines += "2. 01_SPRINT_COMMAND_BOARD.md"
$lines += "3. owners/"
$lines += "4. categories/"
$lines += "5. modules/"
$lines += ""
$lines += "## Files"
$lines += ""
$lines += "- 00_ALL_OPEN_REMEDIATION_ROWS.csv"
$lines += "- 00_LEADERSHIP_SUMMARY.md"
$lines += "- 01_SPRINT_COMMAND_BOARD.md"
$lines += "- owners/*.md and owners/*.csv"
$lines += "- categories/*.md and categories/*.csv"
$lines += "- modules/*.md and modules/*.csv"
$lines += ""
$lines += "## Decision"
$lines += ""
$lines += "**NO-GO / FIX REQUIRED** until all owner workpacks close and the 51x51 audit rerun returns PASS."
$lines | Set-Content -Encoding UTF8 $index

Write-Host ""
Write-Host "51x51 remediation workpacks created." -ForegroundColor Green
Write-Host "Output: $Out"
Write-Host "Open:"
Write-Host "  $index"
Write-Host "  $leadership"
Write-Host "  $board"
Write-Host ""
code $index
code $leadership
code $board
code (Join-Path $Out "00_ALL_OPEN_REMEDIATION_ROWS.csv")
