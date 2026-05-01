$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
# ============================================================
# CROWN JUDGMENT DAY RELEASE GAUNTLET
# Deepest non-destructive release readiness test pack.
#
# Run from repo root in VS Code PowerShell.
#
# Optional env vars:
#   $env:CROWN_BACKEND_BASE_URL   = "https://crown-api-prod.azurewebsites.net"
#   $env:CROWN_FRONTEND_BASE_URL  = "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net"
#   $env:CROWN_APPROVED_SHA       = "b9dad81..."
#   $env:CROWN_RUN_BROWSER        = "YES"
#   $env:CROWN_RUN_SAFE_LOAD      = "YES"
#   $env:CROWN_LOAD_REQUESTS      = "100"
#
# This script:
# - does not deploy
# - does not write to Azure
# - does not perform destructive data mutation
# - creates proof artifacts and a hard GO/NO-GO board
# ============================================================
Set-Location "C:\w\crown_main_postmerge_verify"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path
$Out = Join-Path $Root "audit-artifacts\judgment-day-gauntlet\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = Join-Path $Docs "operations"
$Security = Join-Path $Docs "security"
$Inventory = Join-Path $Docs "inventory"
$Design = Join-Path $Docs "design-system"
New-Item -ItemType Directory -Force -Path $Out,$Ops,$Security,$Inventory,$Design | Out-Null
# Start-Transcript disabled: conflicts with VS Code shell integration in PS5.1
$RunLog = "$Out\00_JUDGMENT_DAY_RUN_LOG.txt"
"CROWN JUDGMENT DAY RELEASE GAUNTLET`nRepo: $Root`nOutput: $Out`nStarted: $(Get-Date -Format 'u')" | Set-Content $RunLog -Encoding UTF8
Write-Host "CROWN JUDGMENT DAY RELEASE GAUNTLET"
Write-Host "Repo: $Root"
Write-Host "Output: $Out"
# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
function Write-Text {
    param([string]$Path, [string]$Text)
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Text | Set-Content $Path -Encoding UTF8
}
function Add-Blocker {
    param(
        [string]$Priority,
        [string]$Lane,
        [string]$Issue,
        [string]$Owner,
        [string]$Evidence,
        [string]$RequiredFix
    )
    $script:Blockers += [pscustomobject]@{
        Priority    = $Priority
        Lane        = $Lane
        Issue       = $Issue
        Owner       = $Owner
        Evidence    = $Evidence
        RequiredFix = $RequiredFix
        Status      = "Open"
    }
}
function Add-Score {
    param(
        [string]$Lane,
        [int]$MaxPoints,
        [int]$EarnedPoints,
        [string]$Status,
        [string]$Evidence,
        [string]$Notes
    )
    $script:Scores += [pscustomobject]@{
        Lane         = $Lane
        MaxPoints    = $MaxPoints
        EarnedPoints = $EarnedPoints
        Status       = $Status
        Evidence     = $Evidence
        Notes        = $Notes
    }
}
function Add-Proof {
    param(
        [string]$ProofId,
        [string]$Lane,
        [string]$Test,
        [string]$Expected,
        [string]$Owner,
        [string]$Status,
        [string]$Evidence
    )
    $script:ProofRows += [pscustomobject]@{
        ProofId  = $ProofId
        Lane     = $Lane
        Test     = $Test
        Expected = $Expected
        Owner    = $Owner
        Status   = $Status
        Evidence = $Evidence
    }
}
function Run-Validation {
    param(
        [string]$Area,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$Purpose
    )
    $idx = $script:ValidationRows.Count + 1
    $safe = ($Area + "_" + $idx) -replace "[^A-Za-z0-9_-]","_"
    $log = "$Out\validation_$safe.txt"
    $timeoutSec = 1200
    if ($env:CROWN_VALIDATION_TIMEOUT_SEC) {
        try {
            $timeoutSec = [int]$env:CROWN_VALIDATION_TIMEOUT_SEC
        } catch {}
    }
    Push-Location $WorkingDirectory
    try {
        "=== COMMAND ===" | Set-Content $log -Encoding UTF8
        $Command | Add-Content $log -Encoding UTF8
        "" | Add-Content $log -Encoding UTF8
        "=== PURPOSE ===" | Add-Content $log -Encoding UTF8
        $Purpose | Add-Content $log -Encoding UTF8
        "" | Add-Content $log -Encoding UTF8
        "=== OUTPUT ===" | Add-Content $log -Encoding UTF8
        $cmdLine = "/c $Command >> ""$log"" 2>&1"
        $proc = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdLine -PassThru -WindowStyle Hidden
        $finished = $proc.WaitForExit($timeoutSec * 1000)
        if (-not $finished) {
            try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
            $exit = 124
            $status = "TIMEOUT"
            try {
                "" | Add-Content $log -Encoding UTF8
                "[TIMEOUT] Command exceeded $timeoutSec seconds and was terminated." | Add-Content $log -Encoding UTF8
            } catch {}
        } else {
            $exit = $proc.ExitCode
            $status = if ($exit -eq 0) { "PASS" } else { "FAIL" }
        }
        $script:ValidationRows += [pscustomobject]@{
            Area             = $Area
            WorkingDirectory = $WorkingDirectory
            Command          = $Command
            Purpose          = $Purpose
            ExitCode         = $exit
            Status           = $status
            OutputFile       = $log
        }
    }
    catch {
        $errText = $_ | Out-String
        if (Test-Path $log) { $errText | Add-Content $log -Encoding UTF8 } else { $errText | Set-Content $log -Encoding UTF8 }
        $script:ValidationRows += [pscustomobject]@{
            Area             = $Area
            WorkingDirectory = $WorkingDirectory
            Command          = $Command
            Purpose          = $Purpose
            ExitCode         = 999
            Status           = "ERROR"
            OutputFile       = $log
        }
    }
    finally {
        Pop-Location
    }
}
function Search-Risk {
    param(
        [array]$Files,
        [array]$Patterns,
        [string]$Type,
        [string]$Output
    )
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($f in $Files) {
        try {
            $hits = Select-String -Path $f.FullName -Pattern $Patterns -SimpleMatch -AllMatches -ErrorAction SilentlyContinue
            foreach ($h in $hits) {
                $null = $rows.Add([pscustomobject]@{
                    Type = $Type
                    File = $f.FullName.Replace($Root,"").TrimStart("\")
                    Line = $h.LineNumber
                    Text = $h.Line.Trim()
                })
            }
        } catch {}
    }
    $rows | Export-Csv $Output -NoTypeInformation
    return $rows.ToArray()
}
function Get-HttpStatus {
    param([string]$Url)
    try {
        $status = curl.exe -s -o NUL -w "%{http_code}" -L -m 20 $Url
        return "$status"
    } catch {
        return "ERROR"
    }
}
function Get-HttpBody {
    param([string]$Url)
    try {
        return (curl.exe -s -L -m 20 $Url)
    } catch {
        return ""
    }
}
$script:Blockers = @()
$script:Scores = @()
$script:ProofRows = @()
$script:ValidationRows = @()
# ------------------------------------------------------------
# 01. Repo identity and workspace hygiene
# ------------------------------------------------------------
$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD
$StatusShort = git status --short
git status --short | Set-Content "$Out\01_git_status_short.txt" -Encoding UTF8
git status | Set-Content "$Out\02_git_status_full.txt" -Encoding UTF8
git log --oneline -50 | Set-Content "$Out\03_recent_commits.txt" -Encoding UTF8
git branch -vv | Set-Content "$Out\04_branches.txt" -Encoding UTF8
git remote -v | Set-Content "$Out\05_remotes.txt" -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($StatusShort)) {
    Add-Score "Repo hygiene" 50 50 "PASS" "$Out\01_git_status_short.txt" "Worktree clean."
} else {
    Add-Score "Repo hygiene" 50 0 "FAIL" "$Out\01_git_status_short.txt" "Worktree has uncommitted changes."
    Add-Blocker "P0" "Repo hygiene" "Worktree is not clean." "Dev 5 / QA Release" "$Out\01_git_status_short.txt" "Commit, restore, or intentionally classify changes before release."
}
# ------------------------------------------------------------
# 02. Detect app surfaces
# ------------------------------------------------------------
$PackageFiles = Get-ChildItem -Recurse -File -Filter package.json |
    Where-Object { $_.FullName -notmatch "\\node_modules\\" }
$FrontendRoot = $null
$FrontendPackageJson = $null
foreach ($pkg in $PackageFiles) {
    try {
        $raw = Get-Content $pkg.FullName -Raw
        if ($raw.ToLowerInvariant() -match "react|vite|next|tailwind|@types/react|playwright") {
            $FrontendRoot = Split-Path $pkg.FullName -Parent
            $FrontendPackageJson = $pkg.FullName
            break
        }
    } catch {}
}
$BackendManagePy = ""
if (Test-Path "backend\manage.py") {
    $BackendManagePy = "backend\manage.py"
}
$BackendBaseUrl = $env:CROWN_BACKEND_BASE_URL
if ([string]::IsNullOrWhiteSpace($BackendBaseUrl)) {
    $BackendBaseUrl = "https://crown-api-prod.azurewebsites.net"
}
$FrontendBaseUrl = $env:CROWN_FRONTEND_BASE_URL
if ([string]::IsNullOrWhiteSpace($FrontendBaseUrl)) {
    $FrontendBaseUrl = "https://yellow-forest-0eecc8b0f.7.azurestaticapps.net"
}
$ApprovedSha = $env:CROWN_APPROVED_SHA
if ([string]::IsNullOrWhiteSpace($ApprovedSha)) {
    $ApprovedSha = $HeadFull
}
@"
Repo: $Root
Branch: $Branch
HEAD: $Head
HEAD_FULL: $HeadFull
FrontendRoot: $FrontendRoot
FrontendPackageJson: $FrontendPackageJson
BackendManagePy: $BackendManagePy
BackendBaseUrl: $BackendBaseUrl
FrontendBaseUrl: $FrontendBaseUrl
ApprovedShaForGate: $ApprovedSha
"@ | Set-Content "$Out\06_detected_surfaces.txt" -Encoding UTF8
# ------------------------------------------------------------
# 03. Local validation gauntlet
# ------------------------------------------------------------
if ($FrontendPackageJson) {
    $pkg = Get-Content $FrontendPackageJson -Raw | ConvertFrom-Json
    if ($pkg.scripts) {
        foreach ($scriptName in @("typecheck","lint","test","build")) {
            if ($pkg.scripts.PSObject.Properties.Name -contains $scriptName) {
                Write-Host "  [TRACE] Running Frontend $scriptName..."
                Run-Validation "Frontend" $FrontendRoot "npm run $scriptName" "Frontend validation: $scriptName"
                Write-Host "  [TRACE] Done Frontend $scriptName (rows=$($script:ValidationRows.Count))"
            }
        }
    }
}
if ($BackendManagePy) {
    Run-Validation "Backend" $Root "python backend\manage.py check" "Django system check"
    Run-Validation "Backend" $Root "python backend\manage.py check --deploy" "Django deploy/security check"
    Run-Validation "Backend" $Root "python backend\manage.py showmigrations" "Django migration inventory"
}
if ((Test-Path "pytest.ini") -or (Test-Path "pyproject.toml") -or (Test-Path "backend\pytest.ini")) {
    Run-Validation "Backend" $Root "python -m pytest -x -q --tb=short" "Python test suite (fast: stop-on-first-fail)"
}
$ValidationRows | Export-Csv "$Out\10_validation_results.csv" -NoTypeInformation
$ValidationTotal = $ValidationRows.Count
$ValidationFail = @($ValidationRows | Where-Object { $_.Status -ne "PASS" }).Count
$ValidationPass = @($ValidationRows | Where-Object { $_.Status -eq "PASS" }).Count
if ($ValidationTotal -eq 0) {
    Add-Score "Local validation" 100 0 "REVIEW" "$Out\10_validation_results.csv" "No validation commands detected."
    Add-Blocker "P1" "Local validation" "No build/lint/test/check commands detected." "Dev 5 / QA Release" "$Out\10_validation_results.csv" "Document exact validation commands and rerun gauntlet."
} elseif ($ValidationFail -eq 0) {
    Add-Score "Local validation" 100 100 "PASS" "$Out\10_validation_results.csv" "All detected validation commands passed."
} else {
    $earned = [int](100 * (($ValidationTotal - $ValidationFail) / [Math]::Max(1,$ValidationTotal)))
    Add-Score "Local validation" 100 $earned "FAIL" "$Out\10_validation_results.csv" "$ValidationFail validation commands failed."
    foreach ($v in $ValidationRows | Where-Object { $_.Status -ne "PASS" }) {
        Add-Blocker "P0" "Local validation" "Validation failed: $($v.Command)" "Dev 5 / owning dev" $v.OutputFile "Fix validation failure and rerun gauntlet."
    }
}
# ------------------------------------------------------------
# 04. Static source scan
# ------------------------------------------------------------
$Excluded = @(
    "\\.git\\",
    "\\node_modules\\",
    "\\audit-artifacts\\",
    "\\dist\\",
    "\\build\\",
    "\\coverage\\",
    "\\.next\\",
    "\\.venv\\",
    "\\venv\\",
    "\\__pycache__\\",
    "\\.pytest_cache\\",
    "\\.mypy_cache\\",
    "\\.ruff_cache\\")
$SourceFiles = Get-ChildItem -Recurse -File |
    Where-Object {
        $p = $_.FullName
        $ok = $true
        foreach ($e in $Excluded) {
            if ($p -match $e) { $ok = $false }
        }
        $ok -and ($_.Extension.ToLowerInvariant() -in @(".py",".ts",".tsx",".js",".jsx",".html",".css",".md",".json",".yml",".yaml"))
    }
Write-Host "  [TRACE] Static scan file count: $($SourceFiles.Count)"
Write-Host "  [TRACE] Static scan: possible secrets..."
$SecretHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Possible Secret" `
    -Output "$Out\20_possible_secret_scan.csv" `
    -Patterns @(
        "BEGIN PRIVATE KEY",
        "client_secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "password=",
        "password:",
        "SECRET_KEY",
        "AZURE_CREDENTIALS",
        "AZURE_SWA_TOKEN",
        "connectionString",
        "AccountKey="
    )
Write-Host "  [TRACE] Static scan: placeholders..."
$PlaceholderHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Placeholder/Incomplete" `
    -Output "$Out\21_placeholder_incomplete_scan.csv" `
    -Patterns @(
        "TODO",
        "FIXME",
        "TBD",
        "coming soon",
        "placeholder",
        "lorem",
        "dummy",
        "fake",
        "not implemented",
        "hardcoded",
        "replace me",
        "needs wiring",
        "demo only"
    )
Write-Host "  [TRACE] Static scan: UI risks..."
$UiRiskHits = Search-Risk `
    -Files $SourceFiles `
    -Type "UI Risk" `
    -Output "$Out\22_ui_risk_scan.csv" `
    -Patterns @(
        "href=""#""",
        "href='#'",
        "javascript:void",
        "bg-gray-900",
        "bg-slate-900",
        "bg-zinc-900",
        "bg-neutral-900",
        "#000000",
        "#111827",
        "#0f172a",
        "navy",
        "dark placeholder"
    )
Write-Host "  [TRACE] Static scan: tenant signals..."
$TenantSignals = Search-Risk `
    -Files $SourceFiles `
    -Type "Tenant Signal" `
    -Output "$Out\23_tenant_signal_scan.csv" `
    -Patterns @(
        "tenant",
        "Tenant",
        "school_id",
        "schoolId",
        "schoolContext",
        "SchoolContext",
        "X-School-Id",
        "x-school-id",
        "request.school",
        "request.tenant",
        "current_school",
        "currentSchool"
    )
Write-Host "  [TRACE] Static scan: tenant risks..."
$TenantRiskHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Tenant Risk" `
    -Output "$Out\24_tenant_risk_scan.csv" `
    -Patterns @(
        ".objects.all()",
        "AllowAny",
        "skip_tenant",
        "ignore_tenant",
        "bypass",
        "without_tenant",
        "withoutTenant",
        "school_id=None",
        "tenant_id=None"
    )
Write-Host "  [TRACE] Static scan: permissions..."
$PermissionSignals = Search-Risk `
    -Files $SourceFiles `
    -Type "RBAC/Permission Signal" `
    -Output "$Out\25_permission_signal_scan.csv" `
    -Patterns @(
        "permission_classes",
        "permissions",
        "IsAuthenticated",
        "IsAdmin",
        "role",
        "Role",
        "RBAC",
        "has_perm",
        "can_view",
        "can_edit",
        "require_role",
        "allowed_roles"
    )
Write-Host "  [TRACE] Static scan: route inventory..."
$RouteHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Route/Nav" `
    -Output "$Out\26_route_inventory.csv" `
    -Patterns @(
        "<Route",
        "path=",
        "path:",
        "href=",
        "to=",
        "navigate(",
        "router.push",
        "createBrowserRouter",
        "urlpatterns",
        "router.register"
    )
Write-Host "  [TRACE] Static scan: dashboard inventory..."
$DashboardHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Dashboard/KPI" `
    -Output "$Out\27_dashboard_inventory.csv" `
    -Patterns @(
        "dashboard",
        "Dashboard",
        "kpi",
        "KPI",
        "metric",
        "Metric",
        "widget",
        "Widget"
    )
Write-Host "  [TRACE] Static scan: wizard inventory..."
$WizardHits = Search-Risk `
    -Files $SourceFiles `
    -Type "Wizard" `
    -Output "$Out\28_wizard_inventory.csv" `
    -Patterns @(
        "wizard",
        "Wizard",
        "stepper",
        "Stepper",
        "multi-step",
        "multistep"
    )
Write-Host "  [TRACE] Static scan: complete"
Copy-Item "$Out\26_route_inventory.csv" "$Inventory\JUDGMENT_DAY_ROUTE_INVENTORY.csv" -Force
Copy-Item "$Out\27_dashboard_inventory.csv" "$Inventory\JUDGMENT_DAY_DASHBOARD_INVENTORY.csv" -Force
Copy-Item "$Out\28_wizard_inventory.csv" "$Inventory\JUDGMENT_DAY_WIZARD_INVENTORY.csv" -Force
# Security scoring
$LatestSecurityReport = Get-ChildItem "audit-artifacts" -Recurse -File -Filter "22b_security_triage_report.md" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$SecurityTriagedPass = $false
if ($LatestSecurityReport) {
    $securityText = Get-Content $LatestSecurityReport.FullName -Raw
    if ($securityText -match "0 real" -or $securityText -match "Real hardcoded production secrets.*0") {
        $SecurityTriagedPass = $true
    }
}
if ($SecurityTriagedPass) {
    Add-Score "Security secret scan" 100 100 "PASS" $LatestSecurityReport.FullName "Prior triage report shows zero real hardcoded production secrets."
} elseif ($SecretHits.Count -eq 0) {
    Add-Score "Security secret scan" 100 100 "PASS" "$Out\20_possible_secret_scan.csv" "No possible secret hits."
} else {
    Add-Score "Security secret scan" 100 40 "REVIEW" "$Out\20_possible_secret_scan.csv" "$($SecretHits.Count) possible secret hits require triage."
    Add-Blocker "P0" "Security" "$($SecretHits.Count) possible secret/token hits require triage." "Dev 5 / QA Release" "$Out\20_possible_secret_scan.csv" "Classify false positives and remove or rotate real secrets."
}
# Tenant/RBAC static scoring
if ($TenantSignals.Count -gt 0 -and $TenantRiskHits.Count -eq 0) {
    Add-Score "Tenant isolation static scan" 75 75 "PASS" "$Out\23_tenant_signal_scan.csv" "Tenant signals found and no static tenant-risk hits."
} elseif ($TenantSignals.Count -gt 0) {
    Add-Score "Tenant isolation static scan" 75 45 "REVIEW" "$Out\24_tenant_risk_scan.csv" "$($TenantRiskHits.Count) tenant risk hits require review."
    Add-Blocker "P0" "Tenant isolation" "$($TenantRiskHits.Count) tenant-risk hits require manual review." "Dev 1 / Dev 5" "$Out\24_tenant_risk_scan.csv" "Verify every risk hit is tenant-scoped or fix query/permission logic."
} else {
    Add-Score "Tenant isolation static scan" 75 0 "FAIL" "$Out\23_tenant_signal_scan.csv" "No tenant isolation signals found."
    Add-Blocker "P0" "Tenant isolation" "No tenant/school isolation signals found." "Dev 1" "$Out\23_tenant_signal_scan.csv" "Locate or implement backend tenant isolation before release."
}
if ($PermissionSignals.Count -gt 0) {
    Add-Score "RBAC static scan" 50 50 "PASS" "$Out\25_permission_signal_scan.csv" "Permission/RBAC signals found."
} else {
    Add-Score "RBAC static scan" 50 0 "FAIL" "$Out\25_permission_signal_scan.csv" "No permission/RBAC signals found."
    Add-Blocker "P0" "RBAC" "No RBAC/permission signals found." "Dev 1" "$Out\25_permission_signal_scan.csv" "Locate or implement backend permission enforcement before release."
}
# UI/static scoring
$UiEarned = 100
$UiStatus = "PASS"
$UiNotes = "No major UI static scan blockers."
if ($PlaceholderHits.Count -gt 0) {
    $UiEarned -= 30
    $UiStatus = "REVIEW"
    Add-Blocker "P1" "UI/Product" "$($PlaceholderHits.Count) placeholder or incomplete markers found." "Dev 4 / Dev 5" "$Out\21_placeholder_incomplete_scan.csv" "Remove, replace, or formally defer production-facing markers."
}
if ($UiRiskHits.Count -gt 0) {
    $UiEarned -= 30
    $UiStatus = "REVIEW"
    Add-Blocker "P1" "UI polish" "$($UiRiskHits.Count) UI risk hits found." "Dev 4" "$Out\22_ui_risk_scan.csv" "Fix dead links, dark/off-brand styles, and hardcoded visual drift."
}
if ($RouteHits.Count -eq 0) {
    $UiEarned -= 20
    $UiStatus = "REVIEW"
    Add-Blocker "P1" "Routes" "No route/navigation references detected." "Dev 4 / Dev 5" "$Out\26_route_inventory.csv" "Confirm route system and rerun inventory."
}
if ($DashboardHits.Count -eq 0) {
    $UiEarned -= 20
    $UiStatus = "REVIEW"
    Add-Blocker "P1" "Dashboards" "No dashboard/KPI references detected." "Dev 4" "$Out\27_dashboard_inventory.csv" "Confirm dashboard naming and rerun inventory."
}
if ($UiEarned -lt 0) { $UiEarned = 0 }
Add-Score "UI/routes/dashboard/wizard static scan" 100 $UiEarned $UiStatus "$Out\21_placeholder_incomplete_scan.csv; $Out\22_ui_risk_scan.csv; $Out\26_route_inventory.csv; $Out\27_dashboard_inventory.csv" $UiNotes
# ------------------------------------------------------------
# 05. Read-only deployment integrity probes
# ------------------------------------------------------------
$BackendHealthUrl = "$BackendBaseUrl/api/health/"
$FrontendRootUrl = "$FrontendBaseUrl/"
$BuildJsonUrl = "$FrontendBaseUrl/build.json"
$BackendStatus = Get-HttpStatus $BackendHealthUrl
$BackendBody = Get-HttpBody $BackendHealthUrl
$FrontendStatus = Get-HttpStatus $FrontendRootUrl
$BuildJsonStatus = Get-HttpStatus $BuildJsonUrl
$BuildJsonBody = Get-HttpBody $BuildJsonUrl
$BackendBody | Set-Content "$Out\30_backend_health_body.txt" -Encoding UTF8
$BuildJsonBody | Set-Content "$Out\31_frontend_build_json_body.txt" -Encoding UTF8
@"
BackendHealthUrl: $BackendHealthUrl
BackendStatus: $BackendStatus
FrontendRootUrl: $FrontendRootUrl
FrontendStatus: $FrontendStatus
BuildJsonUrl: $BuildJsonUrl
BuildJsonStatus: $BuildJsonStatus
ApprovedSha: $ApprovedSha
"@ | Set-Content "$Out\32_deployment_probe_summary.txt" -Encoding UTF8
$BackendShaMatch = $false
$FrontendShaMatch = $false
if ($BackendBody -match [regex]::Escape($ApprovedSha) -or ($ApprovedSha.Length -ge 7 -and $BackendBody -match [regex]::Escape($ApprovedSha.Substring(0,7)))) {
    $BackendShaMatch = $true
}
if ($BuildJsonBody -match [regex]::Escape($ApprovedSha) -or ($ApprovedSha.Length -ge 7 -and $BuildJsonBody -match [regex]::Escape($ApprovedSha.Substring(0,7)))) {
    $FrontendShaMatch = $true
}
$DeployPoints = 0
if ($BackendStatus -eq "200") { $DeployPoints += 20 }
if ($BackendShaMatch) { $DeployPoints += 30 }
if ($FrontendStatus -eq "200") { $DeployPoints += 20 }
if ($BuildJsonStatus -eq "200") { $DeployPoints += 15 }
if ($FrontendShaMatch) { $DeployPoints += 15 }
$DeployStatus = if ($DeployPoints -eq 100) { "PASS" } else { "FAIL" }
Add-Score "Deployment integrity read-only probe" 100 $DeployPoints $DeployStatus "$Out\32_deployment_probe_summary.txt" "Backend status=$BackendStatus; backend SHA match=$BackendShaMatch; frontend status=$FrontendStatus; build.json status=$BuildJsonStatus; frontend SHA match=$FrontendShaMatch."
if ($BackendStatus -ne "200") {
    Add-Blocker "P0" "Deployment integrity" "Backend health is not HTTP 200." "Azure/DevOps team" "$Out\32_deployment_probe_summary.txt" "Repair backend deployment/runtime."
}
if (-not $BackendShaMatch) {
    Add-Blocker "P0" "Deployment integrity" "Backend live SHA does not match approved SHA." "Azure/DevOps team" "$Out\30_backend_health_body.txt" "Deploy approved backend build and rerun proof."
}
if ($FrontendStatus -ne "200") {
    Add-Blocker "P0" "Deployment integrity" "Frontend root is not HTTP 200." "Azure/DevOps team" "$Out\32_deployment_probe_summary.txt" "Repair dashboard/frontend deployment."
}
if ($BuildJsonStatus -ne "200") {
    Add-Blocker "P0" "Deployment integrity" "Frontend build.json is not HTTP 200." "Azure/DevOps team" "$Out\32_deployment_probe_summary.txt" "Publish build.json with deployed frontend."
}
if (-not $FrontendShaMatch) {
    Add-Blocker "P0" "Deployment integrity" "Frontend build SHA does not match approved SHA." "Azure/DevOps team" "$Out\31_frontend_build_json_body.txt" "Deploy approved frontend build and rerun proof."
}
# ------------------------------------------------------------
# 06. Browser smoke test if Playwright is available/enabled
# ------------------------------------------------------------
$BrowserPoints = 0
$BrowserStatus = "SKIPPED"
$BrowserEvidence = "$Out\40_browser_smoke.txt"
$RunBrowser = $env:CROWN_RUN_BROWSER
if ([string]::IsNullOrWhiteSpace($RunBrowser)) {
    $RunBrowser = "YES"
}
$HasPlaywright = $false
if ($FrontendPackageJson) {
    $pkgText = Get-Content $FrontendPackageJson -Raw
    if ($pkgText -match "playwright|@playwright/test") {
        $HasPlaywright = $true
    }
}
if ($RunBrowser -eq "YES" -and $HasPlaywright -and $FrontendRoot) {
    $E2EDir = Join-Path $FrontendRoot "tests\e2e"
    New-Item -ItemType Directory -Force -Path $E2EDir | Out-Null
    $SpecPath = Join-Path $E2EDir "crown_judgment_day_smoke.spec.ts"
    $Spec = @"
import { test, expect } from '@playwright/test';
const baseUrl = process.env.CROWN_FRONTEND_BASE_URL || '$FrontendBaseUrl';
test('CROWN frontend root loads without hard 404', async ({ page }) => {
  const response = await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  expect(response?.status(), 'root status').toBeLessThan(400);
  await expect(page.locator('body')).toBeVisible();
});
test('CROWN frontend has no obvious empty body', async ({ page }) => {
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  const text = (await page.locator('body').innerText()).trim();
  expect(text.length, 'body text length').toBeGreaterThan(20);
});
test('CROWN frontend has no console errors on root load', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  expect(errors, 'console errors').toEqual([]);
});
"@
    $Spec | Set-Content $SpecPath -Encoding UTF8
    Push-Location $FrontendRoot
    try {
        "=== Playwright judgment day smoke ===" | Set-Content $BrowserEvidence -Encoding UTF8
        "Spec: $SpecPath" | Add-Content $BrowserEvidence -Encoding UTF8
        "BaseUrl: $FrontendBaseUrl" | Add-Content $BrowserEvidence -Encoding UTF8
        "" | Add-Content $BrowserEvidence -Encoding UTF8
        cmd.exe /c "npx playwright test tests/e2e/crown_judgment_day_smoke.spec.ts --reporter=line" >> $BrowserEvidence 2>&1
        $browserExit = $LASTEXITCODE
        if ($browserExit -eq 0) {
            $BrowserPoints = 100
            $BrowserStatus = "PASS"
        } else {
            $BrowserPoints = 0
            $BrowserStatus = "FAIL"
            Add-Blocker "P0" "Browser smoke" "Browser smoke test failed." "Dev 4 / Dev 5" $BrowserEvidence "Fix frontend availability/console/root rendering and rerun."
        }
    }
    catch {
        $_ | Out-String | Add-Content $BrowserEvidence -Encoding UTF8
        $BrowserStatus = "ERROR"
        Add-Blocker "P0" "Browser smoke" "Browser smoke test errored." "Dev 4 / Dev 5" $BrowserEvidence "Fix Playwright/browser test execution and rerun."
    }
    finally {
        Pop-Location
    }
} else {
    @"
Browser smoke skipped.
RunBrowser: $RunBrowser
HasPlaywright: $HasPlaywright
FrontendRoot: $FrontendRoot
To force browser smoke:
- Ensure @playwright/test exists in frontend package.
- Set `$env:CROWN_RUN_BROWSER = "YES"
- Rerun gauntlet.
"@ | Set-Content $BrowserEvidence -Encoding UTF8
}
Add-Score "Browser smoke" 100 $BrowserPoints $BrowserStatus $BrowserEvidence "Root load, visible body, and console-error smoke."
# ------------------------------------------------------------
# 07. Safe load probe
# ------------------------------------------------------------
$LoadPoints = 0
$LoadStatus = "SKIPPED"
$LoadEvidence = "$Out\50_safe_load_probe.csv"
$RunSafeLoad = $env:CROWN_RUN_SAFE_LOAD
if ([string]::IsNullOrWhiteSpace($RunSafeLoad)) {
    $RunSafeLoad = "YES"
}
$LoadRequests = 100
if ($env:CROWN_LOAD_REQUESTS) {
    try { $LoadRequests = [int]$env:CROWN_LOAD_REQUESTS } catch { $LoadRequests = 100 }
}
$LoadRows = @()
if ($RunSafeLoad -eq "YES" -and $BackendStatus -eq "200") {
    for ($i = 1; $i -le $LoadRequests; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $status = Get-HttpStatus $BackendHealthUrl
        $sw.Stop()
        $LoadRows += [pscustomobject]@{
            Request = $i
            Url = $BackendHealthUrl
            Status = $status
            Ms = $sw.ElapsedMilliseconds
        }
    }
    $LoadRows | Export-Csv $LoadEvidence -NoTypeInformation
    $LoadFailures = @($LoadRows | Where-Object { $_.Status -ne "200" }).Count
    $AvgMs = if ($LoadRows.Count -gt 0) { [int](($LoadRows | Measure-Object Ms -Average).Average) } else { 0 }
    $MaxMs = if ($LoadRows.Count -gt 0) { [int](($LoadRows | Measure-Object Ms -Maximum).Maximum) } else { 0 }
    if ($LoadFailures -eq 0 -and $AvgMs -lt 2000) {
        $LoadPoints = 50
        $LoadStatus = "PASS"
    } elseif ($LoadFailures -eq 0) {
        $LoadPoints = 30
        $LoadStatus = "REVIEW"
        Add-Blocker "P1" "Safe load probe" "Backend health stayed up but average latency is high: ${AvgMs}ms." "Dev 1 / DevOps" $LoadEvidence "Review backend performance."
    } else {
        $LoadPoints = 0
        $LoadStatus = "FAIL"
        Add-Blocker "P0" "Safe load probe" "$LoadFailures of $LoadRequests backend health probes failed." "Dev 1 / DevOps" $LoadEvidence "Fix backend reliability before release."
    }
    @"
Requests: $LoadRequests
Failures: $LoadFailures
AverageMs: $AvgMs
MaxMs: $MaxMs
"@ | Set-Content "$Out\51_safe_load_summary.txt" -Encoding UTF8
} else {
    @"
Safe load probe skipped.
RunSafeLoad: $RunSafeLoad
BackendStatus: $BackendStatus
BackendHealthUrl: $BackendHealthUrl
"@ | Set-Content "$Out\51_safe_load_summary.txt" -Encoding UTF8
}
Add-Score "Safe load probe" 50 $LoadPoints $LoadStatus "$Out\51_safe_load_summary.txt" "Read-only backend health probe."
# ------------------------------------------------------------
# 08. Required manual/runtime proof matrices
# ------------------------------------------------------------
# Tenant isolation
$TenantProofs = @(
    @("TI-001","Tenant isolation","School A admin cannot access School B student by URL/API id.","403/404/safe redirect","Dev 1 / Dev 2 / Dev 5"),
    @("TI-002","Tenant isolation","School A parent cannot access School B household record.","403/404/safe redirect","Dev 1 / Dev 2 / Dev 5"),
    @("TI-003","Tenant isolation","School A finance user cannot access School B billing data.","403/404/safe redirect","Dev 1 / Dev 3 / Dev 5"),
    @("TI-004","Tenant isolation","School A teacher cannot access School B roster/attendance/grades.","403/404/safe redirect","Dev 1 / Dev 2 / Dev 5"),
    @("TI-005","Tenant isolation","School A dashboard cannot aggregate School B data.","Only active school data","Dev 1 / Dev 4 / Dev 5"),
    @("TI-006","Tenant isolation","Unauthorized school switcher context change is rejected.","Denied","Dev 1 / Dev 5"),
    @("TI-007","Tenant isolation","School A user cannot download School B document/file.","403/404/safe redirect","Dev 1 / Dev 5"))
foreach ($p in $TenantProofs) {
    Add-Proof $p[0] $p[1] $p[2] $p[3] $p[4] "Manual Runtime Required" ""
}
# RBAC
$RbacProofs = @(
    @("RBAC-001","RBAC","Parent cannot access admin dashboard.","Denied","Dev 1 / Dev 5"),
    @("RBAC-002","RBAC","Teacher cannot access finance billing admin.","Denied","Dev 1 / Dev 5"),
    @("RBAC-003","RBAC","Student cannot access staff/student admin records.","Denied","Dev 1 / Dev 5"),
    @("RBAC-004","RBAC","Finance cannot edit grades/transcripts.","Denied","Dev 1 / Dev 5"),
    @("RBAC-005","RBAC","Admissions cannot edit transcript records.","Denied","Dev 1 / Dev 5"),
    @("RBAC-006","RBAC","Direct API call outside role is denied even if frontend route is guessed.","Denied","Dev 1 / Dev 5"))
foreach ($p in $RbacProofs) {
    Add-Proof $p[0] $p[1] $p[2] $p[3] $p[4] "Manual Runtime Required" ""
}
# Workflows
$WorkflowProofs = @(
    @("WF-001","Workflow","Inquiry to applicant to admitted to enrolled.","Canonical SIS student/enrollment created once","Dev 2 / Dev 3 / Dev 5"),
    @("WF-002","Workflow","Re-enrollment checklist to next-year enrollment.","Returning student status updates correctly","Dev 2 / Dev 3 / Dev 5"),
    @("WF-003","Workflow","Billing charge to payment to balance.","Admin and parent views reconcile","Dev 3 / Dev 5"),
    @("WF-004","Workflow","Teacher roster to attendance posting.","Attendance persists and admin sees result","Dev 2 / Dev 4 / Dev 5"),
    @("WF-005","Workflow","Parent portal household/student/billing/messages.","Parent sees only authorized household data","Dev 4 / Dev 5"),
    @("WF-006","Workflow","Admin dashboard KPI drill-downs.","Dashboard totals match source data","Dev 4 / Dev 5"))
foreach ($p in $WorkflowProofs) {
    Add-Proof $p[0] $p[1] $p[2] $p[3] $p[4] "Manual Runtime Required" ""
}
# Chaos/security/data
$ChaosProofs = @(
    @("CHAOS-001","Browser chaos","Double-click submit does not duplicate records.","No duplicate/corruption","Dev 4 / Dev 5"),
    @("CHAOS-002","Browser chaos","Refresh/back mid-wizard recovers safely.","No stuck state/corruption","Dev 4 / Dev 5"),
    @("CHAOS-003","Browser chaos","Two tabs editing same record handles stale update safely.","No silent overwrite","Dev 1 / Dev 5"),
    @("SEC-001","Security red team","IDOR object id swapping fails.","Denied","Dev 1 / Dev 5"),
    @("SEC-002","Security red team","XSS payload in names/messages/notes is neutralized.","No script execution","Dev 1 / Dev 4 / Dev 5"),
    @("DATA-001","Data integrity","Migration check and backup/restore procedure verified.","No data loss","Dev 2 / Dev 5"),
    @("DATA-002","Data integrity","Withdrawn/archived student keeps history but blocks active workflows.","Correct lifecycle behavior","Dev 2 / Dev 5"))
foreach ($p in $ChaosProofs) {
    Add-Proof $p[0] $p[1] $p[2] $p[3] $p[4] "Manual Runtime Required" ""
}
$ProofRows | Export-Csv "$Out\60_required_runtime_proof_matrix.csv" -NoTypeInformation
Copy-Item "$Out\60_required_runtime_proof_matrix.csv" "$Ops\JUDGMENT_DAY_REQUIRED_RUNTIME_PROOF_MATRIX.csv" -Force
# Runtime proof scoring: not awarded until executed.
Add-Score "Required runtime proof matrix" 175 0 "MANUAL_REQUIRED" "$Out\60_required_runtime_proof_matrix.csv" "Tenant/RBAC/workflow/chaos/security/data proof rows must be executed with evidence before release GO."
Add-Blocker "P0" "Runtime proof" "Tenant/RBAC/workflow/security runtime proof matrix is not executed yet." "Dev 5 / all leads" "$Out\60_required_runtime_proof_matrix.csv" "Execute every manual runtime proof row with evidence."
# ------------------------------------------------------------
# 09. CROWN Judgment Day master runbook
# ------------------------------------------------------------
$Runbook = @"
# CROWN Judgment Day Release Gauntlet Runbook
Generated: $(Get-Date -Format s)

## Purpose
This is the harshest release readiness gate for CROWN. It is designed to kill weak release candidates before schools, sandbox testers, or customers experience failures.

## Automatic NO-GO Conditions
Any one of these is a production NO-GO:
- tenant leak
- role bypass
- real secret exposed
- broken login
- broken billing reconciliation
- frontend unavailable
- backend unavailable
- backend live SHA mismatch
- frontend build SHA mismatch
- deployment workflow failed
- database migration corruption
- backup cannot restore
- unresolved P0 blocker
- unexecuted tenant/RBAC runtime proof

## Scoring
Total score: 1000 points
- Repo hygiene: 50
- Local validation: 100
- Security secret scan: 100
- Tenant isolation static scan: 75
- RBAC static scan: 50
- UI/routes/dashboard/wizard static scan: 100
- Deployment integrity read-only probe: 100
- Browser smoke: 100
- Safe load probe: 50
- Required runtime proof matrix: 175
- Evidence/operations completeness: 100

## Score Bands
- 950-1000: Production GO candidate
- 900-949: Release candidate, minor fixes only
- 800-899: Strong but not production-final
- 700-799: Major hardening required
- Below 700: Not release-ready

## Evidence Folder
$Out

## Required Manual Proof Matrix
$Out\60_required_runtime_proof_matrix.csv
"@
Write-Text "$Out\70_JUDGMENT_DAY_RUNBOOK.md" $Runbook
Copy-Item "$Out\70_JUDGMENT_DAY_RUNBOOK.md" "$Ops\JUDGMENT_DAY_RUNBOOK.md" -Force
# ------------------------------------------------------------
# 10. Evidence completeness score
# ------------------------------------------------------------
$EvidenceFiles = @(
    "$Out\01_git_status_short.txt",
    "$Out\10_validation_results.csv",
    "$Out\20_possible_secret_scan.csv",
    "$Out\23_tenant_signal_scan.csv",
    "$Out\25_permission_signal_scan.csv",
    "$Out\26_route_inventory.csv",
    "$Out\27_dashboard_inventory.csv",
    "$Out\32_deployment_probe_summary.txt",
    "$Out\40_browser_smoke.txt",
    "$Out\51_safe_load_summary.txt",
    "$Out\60_required_runtime_proof_matrix.csv",
    "$Out\70_JUDGMENT_DAY_RUNBOOK.md"
)
$MissingEvidence = @()
foreach ($e in $EvidenceFiles) {
    if (-not (Test-Path $e)) {
        $MissingEvidence += $e
    }
}
if ($MissingEvidence.Count -eq 0) {
    Add-Score "Evidence/operations completeness" 100 100 "PASS" "$Out" "Expected gauntlet evidence files generated."
} else {
    $earned = [int](100 * (($EvidenceFiles.Count - $MissingEvidence.Count) / [Math]::Max(1,$EvidenceFiles.Count)))
    Add-Score "Evidence/operations completeness" 100 $earned "REVIEW" "$Out" "$($MissingEvidence.Count) expected evidence files missing."
    Add-Blocker "P1" "Evidence" "$($MissingEvidence.Count) expected evidence files missing." "Dev 5 / QA Release" "$Out" "Regenerate missing evidence."
}
# ------------------------------------------------------------
# 11. Final scoring and decision
# ------------------------------------------------------------
$Scores | Export-Csv "$Out\80_JUDGMENT_DAY_SCORECARD.csv" -NoTypeInformation
$Blockers | Sort-Object Priority,Lane | Export-Csv "$Out\81_JUDGMENT_DAY_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\80_JUDGMENT_DAY_SCORECARD.csv" "$Ops\JUDGMENT_DAY_SCORECARD.csv" -Force
Copy-Item "$Out\81_JUDGMENT_DAY_BLOCKER_BOARD.csv" "$Ops\JUDGMENT_DAY_BLOCKER_BOARD.csv" -Force
$TotalEarned = ($Scores | Measure-Object EarnedPoints -Sum).Sum
$TotalMax = ($Scores | Measure-Object MaxPoints -Sum).Sum
$Pct = if ($TotalMax -gt 0) { [math]::Round(($TotalEarned / $TotalMax) * 100, 1) } else { 0 }
$P0Count = @($Blockers | Where-Object { $_.Priority -eq "P0" }).Count
$P1Count = @($Blockers | Where-Object { $_.Priority -eq "P1" }).Count
$P2Count = @($Blockers | Where-Object { $_.Priority -eq "P2" }).Count
$AutoNoGo = $false
$AutoNoGoReasons = @()
if ($P0Count -gt 0) {
    $AutoNoGo = $true
    $AutoNoGoReasons += "P0 blockers remain: $P0Count"
}
if ($DeployStatus -ne "PASS") {
    $AutoNoGo = $true
    $AutoNoGoReasons += "Deployment integrity failed"
}
if ($BrowserStatus -eq "FAIL" -or $BrowserStatus -eq "ERROR") {
    $AutoNoGo = $true
    $AutoNoGoReasons += "Browser smoke failed"
}
if ($SecurityTriagedPass -eq $false -and $SecretHits.Count -gt 0) {
    $AutoNoGo = $true
    $AutoNoGoReasons += "Possible secrets require triage"
}
$Decision = if ($AutoNoGo) {
    "NO-GO"
} elseif ($TotalEarned -ge 950) {
    "PRODUCTION_GO_CANDIDATE"
} elseif ($TotalEarned -ge 900) {
    "RELEASE_CANDIDATE_MINOR_FIXES"
} elseif ($TotalEarned -ge 800) {
    "STRONG_NOT_PRODUCTION_FINAL"
} elseif ($TotalEarned -ge 700) {
    "MAJOR_HARDENING_REQUIRED"
} else {
    "NOT_RELEASE_READY"
}
$Summary = @"
# CROWN Judgment Day Release Gauntlet Summary
Generated: $(Get-Date -Format s)
Repo: $Root
Branch: $Branch
HEAD: $Head
HEAD_FULL: $HeadFull
BackendBaseUrl: $BackendBaseUrl
FrontendBaseUrl: $FrontendBaseUrl
ApprovedShaForGate: $ApprovedSha

## Decision
$Decision

## Score
Earned: $TotalEarned / $TotalMax
Percent: $Pct / 100

## Blockers
P0: $P0Count
P1: $P1Count
P2: $P2Count

## Automatic NO-GO Reasons
$($AutoNoGoReasons -join "`n")

## Critical Live Probe Results
Backend health status: $BackendStatus
Backend SHA match: $BackendShaMatch
Frontend root status: $FrontendStatus
Frontend build.json status: $BuildJsonStatus
Frontend SHA match: $FrontendShaMatch

## Static Scan Counts
Possible secret hits: $($SecretHits.Count)
Placeholder/incomplete hits: $($PlaceholderHits.Count)
UI risk hits: $($UiRiskHits.Count)
Tenant signals: $($TenantSignals.Count)
Tenant risk hits: $($TenantRiskHits.Count)
Permission/RBAC signals: $($PermissionSignals.Count)
Route references: $($RouteHits.Count)
Dashboard/KPI references: $($DashboardHits.Count)
Wizard references: $($WizardHits.Count)

## Validation Counts
Validation total: $ValidationTotal
Validation pass: $ValidationPass
Validation non-pass: $ValidationFail

## Browser and Load
Browser smoke: $BrowserStatus
Safe load: $LoadStatus

## Open First
1. $Out\81_JUDGMENT_DAY_BLOCKER_BOARD.csv
2. $Out\80_JUDGMENT_DAY_SCORECARD.csv
3. $Out\60_required_runtime_proof_matrix.csv
4. $Out\70_JUDGMENT_DAY_RUNBOOK.md

## Scorecard
$($Scores | Format-Table -AutoSize | Out-String)

## Blocker Board
$($Blockers | Sort-Object Priority,Lane | Format-Table -AutoSize | Out-String)
"@
Write-Text "$Out\99_JUDGMENT_DAY_SUMMARY.md" $Summary
Copy-Item "$Out\99_JUDGMENT_DAY_SUMMARY.md" "$Ops\JUDGMENT_DAY_CURRENT_SUMMARY.md" -Force
git status --short | Set-Content "$Out\90_git_status_after.txt" -Encoding UTF8
# ------------------------------------------------------------
# 12. Open result files
# ------------------------------------------------------------
code "$Out\99_JUDGMENT_DAY_SUMMARY.md"
code "$Out\81_JUDGMENT_DAY_BLOCKER_BOARD.csv"
code "$Out\80_JUDGMENT_DAY_SCORECARD.csv"
code "$Out\60_required_runtime_proof_matrix.csv"
code "$Out\70_JUDGMENT_DAY_RUNBOOK.md"
code "$Out\90_git_status_after.txt"
Write-Host ""
Write-Host "CROWN Judgment Day Gauntlet complete."
Write-Host "Decision: $Decision"
Write-Host "Score: $TotalEarned / $TotalMax ($Pct/100)"
Write-Host "P0: $P0Count  P1: $P1Count  P2: $P2Count"
Write-Host "Output: $Out"
Write-Host ""
"Completed: $(Get-Date -Format 'u')  Decision: $Decision  Score: $TotalEarned/$TotalMax" | Add-Content $RunLog -Encoding UTF8
