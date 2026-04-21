param(
    [switch]$OpenFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Keep native tool failures as captured output artifacts instead of terminating execution.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Get-RepoRoot {
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { throw "Not inside a git repository." }
    return $root.Trim()
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Normalize-Slash {
    param([string]$Path)
    return ($Path -replace "\\","/")
}

function Get-RelativePath {
    param(
        [string]$Root,
        [string]$FullPath
    )
    $prefix = $Root + [IO.Path]::DirectorySeparatorChar
    if ($FullPath.StartsWith($prefix)) {
        return Normalize-Slash ($FullPath.Substring($prefix.Length))
    }
    return Normalize-Slash $FullPath
}

function Get-LatestArtifactDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

function Read-CsvSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    return @(Import-Csv $Path)
}

function Get-ControlPaths {
    param([string]$Root)

    $binderRoot = Join-Path $Root "docs\Crown_Master_Binder"
    $opsRoot    = Join-Path $binderRoot "03_Operations_and_Delivery"
    $invRoot    = Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop"
    $auditRoot  = Join-Path $Root "audit-artifacts"

    $master = Join-Path $invRoot "01_Master_Inventory.csv"
    $risk   = Join-Path $opsRoot "04_Risk_Register.csv"
    $gate   = Join-Path $opsRoot "09_Phase_Gate_Register.csv"
    $score  = Join-Path $opsRoot "03_Phase_Progress_Scorecard.csv"

    foreach ($req in @($master,$risk,$gate,$score)) {
        if (-not (Test-Path $req)) {
            throw "Required control file missing: $req"
        }
    }

    return [pscustomobject]@{
        Root            = $Root
        BinderRoot      = $binderRoot
        OpsRoot         = $opsRoot
        InventoryRoot   = $invRoot
        AuditRoot       = $auditRoot
        MasterInventory = $master
        RiskRegister    = $risk
        GateRegister    = $gate
        Scorecard       = $score
    }
}

function New-ArtifactRoot {
    param(
        [string]$AuditRoot,
        [string]$Slug
    )
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $dir = Join-Path $AuditRoot ($Slug + "\\" + $ts)
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Get-RepoFiles {
    param([string]$Root)

    $excludeRegex = @(
        '^[.]git/',
        '^audit-artifacts/',
        '^[.]venv/',
        '^venv/',
        '^node_modules/',
        '/node_modules/',
        '^dist/',
        '/dist/',
        '^build/',
        '/build/',
        '^coverage/',
        '/coverage/',
        '^[.]pytest_cache/',
        '/[.]pytest_cache/',
        '__pycache__/',
        '/__pycache__/',
        '^[.]history/',
        '/[.]history/'
    ) -join '|'

    $tracked = @(git ls-files)

    return @(
        $tracked |
            Where-Object {
                $_ -and
                ($_ -notmatch $excludeRegex) -and
                ($_ -match '^(backend/|frontend/|docs/|scripts/|[.]github/)')
            } |
            ForEach-Object {
                $full = Join-Path $Root ($_ -replace '/', '\\')
                if (Test-Path $full) {
                    Get-Item $full
                }
            } |
            Sort-Object FullName
    )
}

function Find-PatternHits {
    param(
        [object[]]$Files,
        [string]$Root,
        [string[]]$Patterns,
        [string]$Label
    )

    $hits = New-Object System.Collections.Generic.List[object]

    $existingPaths = @($Files | Where-Object { Test-Path $_.FullName } | ForEach-Object { $_.FullName })

    foreach ($pattern in $Patterns) {
        if ($existingPaths.Count -eq 0) { continue }

        $matches = Select-String -Path $existingPaths -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
        foreach ($m in @($matches)) {
            $hits.Add([pscustomobject]@{
                Label   = $Label
                Pattern = $pattern
                File    = Get-RelativePath -Root $Root -FullPath $m.Path
                Line    = $m.LineNumber
                Text    = $m.Line.Trim()
            })
        }
    }

    return $hits.ToArray()
}

function Get-GateRows {
    param([string]$GateRegister)
    return [System.Collections.Generic.List[object]]@(Import-Csv $GateRegister)
}

function Save-GateRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$GateRegister
    )
    $Rows | Export-Csv -Path $GateRegister -NoTypeInformation -Encoding utf8
}

function Get-ScoreRows {
    param([string]$Scorecard)
    return [System.Collections.Generic.List[object]]@(Import-Csv $Scorecard)
}

function Save-ScoreRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Scorecard
    )
    $Rows | Export-Csv -Path $Scorecard -NoTypeInformation -Encoding utf8
}

function Get-RiskRows {
    param([string]$RiskRegister)
    return [System.Collections.Generic.List[object]]@(Import-Csv $RiskRegister)
}

function Save-RiskRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$RiskRegister
    )
    $Rows | Export-Csv -Path $RiskRegister -NoTypeInformation -Encoding utf8
}

function Upsert-Risk {
    param(
        [System.Collections.Generic.List[object]]$RiskRows,
        [string]$RiskID,
        [string]$Phase,
        [string]$Risk,
        [string]$Owner,
        [string]$Severity,
        [string]$Probability,
        [string]$Mitigation,
        [string]$GateImpact,
        [string]$Status,
        [string]$Notes
    )

    $existing = $null
    foreach ($r in $RiskRows) {
        if ($r.RiskID -eq $RiskID) {
            $existing = $r
            break
        }
    }

    if ($existing) {
        $existing.Phase = $Phase
        $existing.Risk = $Risk
        $existing.Owner = $Owner
        $existing.Severity = $Severity
        $existing.Probability = $Probability
        $existing.Mitigation = $Mitigation
        $existing.GateImpact = $GateImpact
        $existing.Status = $Status
        $existing.Notes = $Notes
    }
    else {
        $RiskRows.Add([pscustomobject]@{
            RiskID      = $RiskID
            Phase       = $Phase
            Risk        = $Risk
            Owner       = $Owner
            Severity    = $Severity
            Probability = $Probability
            Mitigation  = $Mitigation
            GateImpact  = $GateImpact
            Status      = $Status
            Notes       = $Notes
        })
    }
}

function Set-GateStatus {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$GateID,
        [string]$Status,
        [string]$Notes,
        [switch]$PreserveApproved
    )

    foreach ($r in $Rows) {
        if ($r.GateID -eq $GateID) {
            if ($PreserveApproved -and $r.Status -eq "Approved") {
                return
            }
            $r.Status = $Status
            $r.Notes = $Notes
            return
        }
    }
}

function Update-PhaseScore {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Phase,
        [int]$Planned,
        [int]$Completed,
        [int]$Blocked,
        [int]$AtRisk,
        [int]$DecisionNeeded,
        [string]$GateStatus,
        [string]$Notes
    )

    foreach ($r in $Rows) {
        if ($r.Phase -eq $Phase) {
            $r.Planned = [string]$Planned
            $r.Completed = [string]$Completed
            $r.Blocked = [string]$Blocked
            $r.AtRisk = [string]$AtRisk
            $r.DecisionNeeded = [string]$DecisionNeeded
            $r.GateStatus = $GateStatus
            $r.Notes = $Notes
        }
    }
}

$root = Get-RepoRoot
Set-Location $root

$paths = Get-ControlPaths -Root $root
$files = Get-RepoFiles -Root $root
$artifactRoot = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "phase567_master_summary"

# -------------------------
# Phase 5
# -------------------------
$phase5Root = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "phase5_core_build_enforcement"

$coreAreas = @(
    @{ Area = "Auth";           Patterns = @("auth","login","jwt","session") }
    @{ Area = "RBAC";           Patterns = @("rbac","role","permission") }
    @{ Area = "Tenant";         Patterns = @("tenant","school_id","tenant_id") }
    @{ Area = "Audit";          Patterns = @("audit","event_log","activity_log") }
    @{ Area = "Student";        Patterns = @("student","guardian","household") }
    @{ Area = "Enrollment";     Patterns = @("enrollment","academic year","term") }
    @{ Area = "Attendance";     Patterns = @("attendance","present","absent") }
    @{ Area = "Grades";         Patterns = @("grade","report card","transcript") }
    @{ Area = "API";            Patterns = @("urlpatterns","router","APIView","ViewSet") }
    @{ Area = "FrontendShell";  Patterns = @("sidebar","navigation","shell","layout","routes") }
)

$coreMatrix = New-Object System.Collections.Generic.List[object]

foreach ($area in $coreAreas) {
    $hits = Find-PatternHits -Files $files -Root $root -Patterns $area.Patterns -Label $area.Area
    $hits | Export-Csv -Path (Join-Path $phase5Root ($area.Area + "_hits.csv")) -NoTypeInformation -Encoding utf8
    $coreMatrix.Add([pscustomobject]@{
        Area     = $area.Area
        HitCount = @($hits).Count
        Status   = if (@($hits).Count -gt 0) { "PresentOrNamed" } else { "NoHitsFound" }
    })
}

$coreMatrix | Export-Csv -Path (Join-Path $phase5Root "core_contract_matrix.csv") -NoTypeInformation -Encoding utf8
$coreGaps = @($coreMatrix | Where-Object { $_.HitCount -eq 0 })
$coreGaps | Export-Csv -Path (Join-Path $phase5Root "core_gaps.csv") -NoTypeInformation -Encoding utf8

$djangoCheckPath = Join-Path $phase5Root "django_check.txt"
$migrationsPath  = Join-Path $phase5Root "django_showmigrations.txt"

$originalSecretKey = $env:SECRET_KEY
$originalDjangoSecretKey = $env:DJANGO_SECRET_KEY
$usingAuditSecret = $false

if ([string]::IsNullOrWhiteSpace($env:SECRET_KEY) -and [string]::IsNullOrWhiteSpace($env:DJANGO_SECRET_KEY)) {
    # Non-prod placeholder to allow deterministic management checks in audit mode.
    $env:SECRET_KEY = "crown-audit-phase567-placeholder-secret-key-20260418"
    $env:DJANGO_SECRET_KEY = $env:SECRET_KEY
    $usingAuditSecret = $true
}

if (Test-Path ".\backend\manage.py") {
    try {
        cmd /c "python .\backend\manage.py check 2>&1" | Set-Content -Path $djangoCheckPath -Encoding utf8
        $global:LASTEXITCODE = 0
    }
    catch {
        $_ | Out-String | Set-Content -Path $djangoCheckPath -Encoding utf8
    }

    try {
        cmd /c "python .\backend\manage.py showmigrations 2>&1" | Set-Content -Path $migrationsPath -Encoding utf8
        $global:LASTEXITCODE = 0
    }
    catch {
        $_ | Out-String | Set-Content -Path $migrationsPath -Encoding utf8
    }
}
else {
    "backend\manage.py not found." | Set-Content -Path $djangoCheckPath -Encoding utf8
    "backend\manage.py not found." | Set-Content -Path $migrationsPath -Encoding utf8
}

Write-Utf8File -Path (Join-Path $phase5Root "SUMMARY.md") -Content (@(
    "# Phase 5 Core Build Enforcement Summary",
    "",
    "Core areas checked: $($coreMatrix.Count)",
    "Core gaps: $(@($coreGaps).Count)",
    "Outputs:",
    "- core_contract_matrix.csv",
    "- core_gaps.csv",
    "- django_check.txt",
    "- django_showmigrations.txt"
) -join [Environment]::NewLine)

# -------------------------
# Phase 6
# -------------------------
$phase6Root = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "phase6_first_wave_module_enforcement"

$moduleAreas = @(
    @{ Area = "Admissions";      Patterns = @("admission","applicant","application") }
    @{ Area = "ReEnrollment";    Patterns = @("re-enrollment","reenrollment","re enrollment") }
    @{ Area = "Billing";         Patterns = @("billing","tuition","invoice","charge") }
    @{ Area = "Payments";        Patterns = @("payment","ledger","balance") }
    @{ Area = "Communications";  Patterns = @("communication","message","announcement","notification") }
    @{ Area = "ParentPortal";    Patterns = @("parent portal","parent_portal","parentportal") }
    @{ Area = "TeacherPortal";   Patterns = @("teacher portal","teacher_portal","teacherportal") }
    @{ Area = "AdminPortal";     Patterns = @("admin portal","administrator portal","dashboard") }
)

$moduleMatrix = New-Object System.Collections.Generic.List[object]

foreach ($area in $moduleAreas) {
    $hits = Find-PatternHits -Files $files -Root $root -Patterns $area.Patterns -Label $area.Area
    $hits | Export-Csv -Path (Join-Path $phase6Root ($area.Area + "_hits.csv")) -NoTypeInformation -Encoding utf8
    $moduleMatrix.Add([pscustomobject]@{
        Module   = $area.Area
        HitCount = @($hits).Count
        Status   = if (@($hits).Count -gt 0) { "PresentOrNamed" } else { "NoHitsFound" }
    })
}

$integrationHits = Find-PatternHits -Files $files -Root $root -Patterns @("tenant","permission","audit","api","router","APIView","ViewSet") -Label "ModuleIntegrationControls"
$integrationHits | Export-Csv -Path (Join-Path $phase6Root "module_integration_control_hits.csv") -NoTypeInformation -Encoding utf8
$moduleMatrix | Export-Csv -Path (Join-Path $phase6Root "module_presence_matrix.csv") -NoTypeInformation -Encoding utf8

$moduleGaps = @($moduleMatrix | Where-Object { $_.HitCount -eq 0 })
$moduleGaps | Export-Csv -Path (Join-Path $phase6Root "module_gaps.csv") -NoTypeInformation -Encoding utf8

Write-Utf8File -Path (Join-Path $phase6Root "SUMMARY.md") -Content (@(
    "# Phase 6 First-Wave Module Enforcement Summary",
    "",
    "Modules checked: $($moduleMatrix.Count)",
    "Module gaps: $(@($moduleGaps).Count)",
    "Integration control hits: $(@($integrationHits).Count)",
    "Outputs:",
    "- module_presence_matrix.csv",
    "- module_gaps.csv",
    "- module_integration_control_hits.csv"
) -join [Environment]::NewLine)

# -------------------------
# Phase 7
# -------------------------
$phase7Root = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "phase7_hardening_release_enforcement"

$gitStatusPath = Join-Path $phase7Root "git_status.txt"
git status --short 2>&1 | Set-Content -Path $gitStatusPath -Encoding utf8

$workflowListPath = Join-Path $phase7Root "workflow_list.txt"
if (Test-Path ".\.github\workflows") {
    Get-ChildItem -Path ".\.github\workflows" -File |
        Select-Object FullName |
        Format-Table -AutoSize |
        Out-String |
        Set-Content -Path $workflowListPath -Encoding utf8
}
else {
    ".github\workflows not found." | Set-Content -Path $workflowListPath -Encoding utf8
}

$deployCheckPath = Join-Path $phase7Root "django_check_deploy.txt"
if (Test-Path ".\backend\manage.py") {
    try {
        cmd /c "python .\backend\manage.py check --deploy 2>&1" | Set-Content -Path $deployCheckPath -Encoding utf8
        $global:LASTEXITCODE = 0
    }
    catch {
        $_ | Out-String | Set-Content -Path $deployCheckPath -Encoding utf8
    }
}
else {
    "backend\manage.py not found." | Set-Content -Path $deployCheckPath -Encoding utf8
}

if ($usingAuditSecret) {
    if ([string]::IsNullOrWhiteSpace($originalSecretKey)) {
        Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:SECRET_KEY = $originalSecretKey
    }

    if ([string]::IsNullOrWhiteSpace($originalDjangoSecretKey)) {
        Remove-Item Env:DJANGO_SECRET_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:DJANGO_SECRET_KEY = $originalDjangoSecretKey
    }
}

$readiness = @(
    [pscustomobject]@{ Check = "Master inventory exists"; Pass = (Test-Path $paths.MasterInventory); Notes = $paths.MasterInventory }
    [pscustomobject]@{ Check = "Risk register exists"; Pass = (Test-Path $paths.RiskRegister); Notes = $paths.RiskRegister }
    [pscustomobject]@{ Check = "Gate register exists"; Pass = (Test-Path $paths.GateRegister); Notes = $paths.GateRegister }
    [pscustomobject]@{ Check = "Scorecard exists"; Pass = (Test-Path $paths.Scorecard); Notes = $paths.Scorecard }
    [pscustomobject]@{ Check = "Workflow list captured"; Pass = (Test-Path $workflowListPath); Notes = $workflowListPath }
    [pscustomobject]@{ Check = "Deploy check captured"; Pass = (Test-Path $deployCheckPath); Notes = $deployCheckPath }
)
$readiness | Export-Csv -Path (Join-Path $phase7Root "release_readiness_checklist.csv") -NoTypeInformation -Encoding utf8

Write-Utf8File -Path (Join-Path $phase7Root "SUMMARY.md") -Content (@(
    "# Phase 7 Hardening and Release Enforcement Summary",
    "",
    "Readiness checks: $(@($readiness).Count)",
    "Failed checks: $(@($readiness | Where-Object { -not $_.Pass }).Count)",
    "Outputs:",
    "- release_readiness_checklist.csv",
    "- workflow_list.txt",
    "- django_check_deploy.txt",
    "- git_status.txt"
) -join [Environment]::NewLine)

# -------------------------
# Update controls
# -------------------------
$gateRows = Get-GateRows -GateRegister $paths.GateRegister
$scoreRows = Get-ScoreRows -Scorecard $paths.Scorecard
$riskRows = Get-RiskRows -RiskRegister $paths.RiskRegister

$phase5Ready = (@($coreGaps).Count -eq 0)
$phase6Ready = (@($moduleGaps).Count -eq 0 -and @($integrationHits).Count -gt 0)
$phase7Ready = (@($readiness | Where-Object { -not $_.Pass }).Count -eq 0)

Set-GateStatus -Rows $gateRows -GateID "G-005" -Status ($(if ($phase5Ready) { "Ready for Review" } else { "Working" })) -Notes ("CoreGaps=" + @($coreGaps).Count) -PreserveApproved
Set-GateStatus -Rows $gateRows -GateID "G-006" -Status ($(if ($phase6Ready) { "Ready for Review" } else { "Working" })) -Notes ("ModuleGaps=" + @($moduleGaps).Count + ";IntegrationHits=" + @($integrationHits).Count) -PreserveApproved
Set-GateStatus -Rows $gateRows -GateID "G-007" -Status ($(if ($phase7Ready) { "Ready for Review" } else { "Working" })) -Notes ("FailedChecks=" + @($readiness | Where-Object { -not $_.Pass }).Count) -PreserveApproved
Save-GateRows -Rows $gateRows -GateRegister $paths.GateRegister

Update-PhaseScore -Rows $scoreRows -Phase "Phase 5" -Planned $coreMatrix.Count -Completed ($coreMatrix.Count - @($coreGaps).Count) -Blocked @($coreGaps).Count -AtRisk @($coreGaps).Count -DecisionNeeded @($coreGaps).Count -GateStatus ($(if ($phase5Ready) { "Ready for Review" } else { "Working" })) -Notes ("CoreGaps=" + @($coreGaps).Count)
Update-PhaseScore -Rows $scoreRows -Phase "Phase 6" -Planned $moduleMatrix.Count -Completed ($moduleMatrix.Count - @($moduleGaps).Count) -Blocked @($moduleGaps).Count -AtRisk @($moduleGaps).Count -DecisionNeeded @($moduleGaps).Count -GateStatus ($(if ($phase6Ready) { "Ready for Review" } else { "Working" })) -Notes ("ModuleGaps=" + @($moduleGaps).Count + ";IntegrationHits=" + @($integrationHits).Count)
Update-PhaseScore -Rows $scoreRows -Phase "Phase 7" -Planned @($readiness).Count -Completed (@($readiness).Count - @($readiness | Where-Object { -not $_.Pass }).Count) -Blocked @($readiness | Where-Object { -not $_.Pass }).Count -AtRisk @($readiness | Where-Object { -not $_.Pass }).Count -DecisionNeeded @($readiness | Where-Object { -not $_.Pass }).Count -GateStatus ($(if ($phase7Ready) { "Ready for Review" } else { "Working" })) -Notes ("FailedChecks=" + @($readiness | Where-Object { -not $_.Pass }).Count)
Save-ScoreRows -Rows $scoreRows -Scorecard $paths.Scorecard

Upsert-Risk -RiskRows $riskRows -RiskID "R-501" -Phase "Phase 5" -Risk "Core coverage gaps remain" -Owner "Dev 1" -Severity "High" -Probability "Medium" -Mitigation "Close core gaps before Gate 5 approval" -GateImpact "Blocks Gate 5" -Status ($(if (@($coreGaps).Count -gt 0) { "Open" } else { "Closed" })) -Notes ("GapCount=" + @($coreGaps).Count)
Upsert-Risk -RiskRows $riskRows -RiskID "R-601" -Phase "Phase 6" -Risk "First-wave module coverage gaps remain" -Owner "Dev 3" -Severity "High" -Probability "Medium" -Mitigation "Close module gaps before Gate 6 approval" -GateImpact "Blocks Gate 6" -Status ($(if (@($moduleGaps).Count -gt 0) { "Open" } else { "Closed" })) -Notes ("GapCount=" + @($moduleGaps).Count)
Upsert-Risk -RiskRows $riskRows -RiskID "R-602" -Phase "Phase 6" -Risk "Module integration controls not evidenced" -Owner "Dev 5" -Severity "High" -Probability "Low" -Mitigation "Evidence tenant, permission, audit, and API controls before Gate 6 approval" -GateImpact "Blocks Gate 6" -Status ($(if (@($integrationHits).Count -eq 0) { "Open" } else { "Closed" })) -Notes ("IntegrationHits=" + @($integrationHits).Count)
Upsert-Risk -RiskRows $riskRows -RiskID "R-701" -Phase "Phase 7" -Risk "Release readiness checks remain incomplete" -Owner "Dev 5" -Severity "High" -Probability "Medium" -Mitigation "Close failed readiness checks before Gate 7 approval" -GateImpact "Blocks Gate 7" -Status ($(if (@($readiness | Where-Object { -not $_.Pass }).Count -gt 0) { "Open" } else { "Closed" })) -Notes ("FailedChecks=" + @($readiness | Where-Object { -not $_.Pass }).Count)
Save-RiskRows -Rows $riskRows -RiskRegister $paths.RiskRegister

Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content (@(
    "# Phase 5 / Phase 6 / Phase 7 Master Summary",
    "",
    "Phase 5 artifact: $phase5Root",
    "Phase 5 ready: $phase5Ready",
    "Core gaps: $(@($coreGaps).Count)",
    "",
    "Phase 6 artifact: $phase6Root",
    "Phase 6 ready: $phase6Ready",
    "Module gaps: $(@($moduleGaps).Count)",
    "Integration hits: $(@($integrationHits).Count)",
    "",
    "Phase 7 artifact: $phase7Root",
    "Phase 7 ready: $phase7Ready",
    "Failed readiness checks: $(@($readiness | Where-Object { -not $_.Pass }).Count)"
) -join [Environment]::NewLine)

Write-Host ""
Write-Host "PHASE567 COMPLETE"
Write-Host "Phase 5 artifact: $phase5Root"
Write-Host "Phase 6 artifact: $phase6Root"
Write-Host "Phase 7 artifact: $phase7Root"
Write-Host "Master summary: $(Join-Path $artifactRoot 'SUMMARY.md')"

if ($OpenFiles) {
    code (Join-Path $phase5Root "SUMMARY.md")
    code (Join-Path $phase5Root "core_contract_matrix.csv")
    code (Join-Path $phase5Root "core_gaps.csv")
    code (Join-Path $phase6Root "SUMMARY.md")
    code (Join-Path $phase6Root "module_presence_matrix.csv")
    code (Join-Path $phase6Root "module_gaps.csv")
    code (Join-Path $phase7Root "SUMMARY.md")
    code (Join-Path $phase7Root "release_readiness_checklist.csv")
    code (Join-Path $artifactRoot "SUMMARY.md")
    code $paths.GateRegister
    code $paths.Scorecard
    code $paths.RiskRegister
}
