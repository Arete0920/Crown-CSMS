param(
    [string]$FrontendUrl = "http://127.0.0.1:3000",
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrozenTagPattern = "freeze-pass-*",
    [string]$CohortBranchPattern = "sandbox/cohort-*"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Require-Tool {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required tool: $Name"
    }
}

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Test-NpmScript {
    param(
        [string]$PackageJsonPath,
        [string]$ScriptName
    )
    if (-not (Test-Path $PackageJsonPath)) { return $false }
    $json = Get-Content $PackageJsonPath -Raw | ConvertFrom-Json
    if ($null -eq $json.scripts) { return $false }
    return $json.scripts.PSObject.Properties.Name -contains $ScriptName
}

function Invoke-LoggedCommand {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Exe,
        [string[]]$CmdArgs = @(),
        [hashtable]$Env = @{}
    )

    $logPath = Join-Path $script:OutDir "$Name.txt"
    $saved = @{}

    foreach ($k in $Env.Keys) {
        $saved[$k] = [Environment]::GetEnvironmentVariable($k, "Process")
        [Environment]::SetEnvironmentVariable($k, [string]$Env[$k], "Process")
    }

    Push-Location $WorkingDirectory
    try {
        Write-Utf8 $logPath @(
            "=== $Name ==="
            "PWD: $(Get-Location)"
            "CMD: $Exe $($CmdArgs -join ' ')"
            ""
        )

        $global:LASTEXITCODE = 0
        $savedEA = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & $Exe @CmdArgs 1>> $logPath 2>&1
        }
        finally {
            $ErrorActionPreference = $savedEA
        }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        return [pscustomobject]@{
            Name = $Name
            Passed = ($exitCode -eq 0)
            ExitCode = $exitCode
            Log = $logPath
        }
    }
    finally {
        Pop-Location
        foreach ($k in $Env.Keys) {
            [Environment]::SetEnvironmentVariable($k, $saved[$k], "Process")
        }
    }
}

function Test-Url {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
    } catch {
        return $false
    }
}

Require-Tool git
Require-Tool powershell

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot ".crown-audit\sandbox-demo-gate\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\sandbox-demo-gate\latest"

New-Dir $script:OutDir
New-Dir $latestDir

$dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$frozenTag = @((git tag --list $FrozenTagPattern | Sort-Object) | Select-Object -Last 1)
$cohortBranch = @((git branch --list $CohortBranchPattern | ForEach-Object { $_.Trim().TrimStart('*').Trim() } | Sort-Object) | Select-Object -Last 1)

$repoState = [ordered]@{
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    dirty_count = $dirty.Count
    dirty_entries = $dirty
    frozen_tag = $frozenTag
    cohort_branch = $cohortBranch
    frontend_url = $FrontendUrl
    backend_url = $BackendUrl
    frontend_reachable = (Test-Url $FrontendUrl)
    backend_health_reachable = (Test-Url ($BackendUrl.TrimEnd('/') + "/api/health/"))
    backend_integrity_reachable = (Test-Url ($BackendUrl.TrimEnd('/') + "/api/integrity/"))
}

Write-JsonFile -Path (Join-Path $script:OutDir "10_repo_state.json") -Object $repoState

$checks = @()
$dashboardRoot = Join-Path $repoRoot "frontend\dashboards"
$packageJson = Join-Path $dashboardRoot "package.json"

if ($env:CROWN_103_RUN_SCORECARD -eq "1") {
    $checks += Invoke-LoggedCommand -Name "live_scorecard_baseline" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",".\scripts\execution\95_live_scorecard_audit.ps1")
    $checks += Invoke-LoggedCommand -Name "live_scorecard_deep" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",".\scripts\execution\95_live_scorecard_audit.ps1","-Deep")
}

if (Test-Path $packageJson) {
    foreach ($scriptName in @(
        "check:shell-contracts",
        "test:unit",
        "ui:proof:nav",
        "test:release:routes",
        "test:release:a11y",
        "test:e2e:smoke",
        "ui:proof:matrix",
        "ui:proof:matrix-pack-2",
        "ui:proof:matrix-pack-3"
    )) {
        $isUiOrE2E = $scriptName -match 'nav|routes|a11y|smoke|matrix'
        if ($isUiOrE2E -and $env:CROWN_103_RUN_UI_PROOFS -ne "1") {
            continue
        }

        if (Test-NpmScript -PackageJsonPath $packageJson -ScriptName $scriptName) {
            $envBlock = @{}
            if ($isUiOrE2E) {
                $envBlock["CI"] = "1"
            }
            if ($scriptName -eq "test:e2e:smoke") {
                $envBlock["VITE_DEV_BASE_URL"] = "http://127.0.0.1:4173"
                $envBlock["CROWN_DEMO_SCHOOL_ID"] = "19801b59-8c05-4c84-9312-5d792e4e839d"
                if ([string]::IsNullOrWhiteSpace($env:CROWN_DEMO_TOKEN)) {
                    throw "CROWN_DEMO_TOKEN must be set in the environment before running test:e2e:smoke."
                }
                $envBlock["CROWN_DEMO_TOKEN"] = $env:CROWN_DEMO_TOKEN
            }

            $checks += Invoke-LoggedCommand -Name ("frontend_" + ($scriptName -replace '[:\-]','_')) -WorkingDirectory $dashboardRoot -Exe "npm.cmd" -CmdArgs @("run",$scriptName) -Env $envBlock
        }
    }
}

if ($env:CROWN_103_RUN_REPORTING_GATE -eq "1" -and (Test-Path (Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py"))) {
    $checks += Invoke-LoggedCommand -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Exe "python" -CmdArgs @("-m","pytest","backend/tests/test_reporting_exports_gate.py","-q")
}

if (Test-Path (Join-Path $repoRoot "backend\manage.py")) {
    $checks += Invoke-LoggedCommand -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Exe "python" -CmdArgs @("manage.py","check")
}

if ($env:CROWN_103_RUN_RELEASE_PYTEST -eq "1") {
    foreach ($testPath in @(
        "tests/test_release_closeout_phase2.py",
        "tests/test_release_route_contracts.py",
        "tests/test_release_tenant_and_urls.py",
        "tests/test_schema_governance_assets.py"
    )) {
        if (Test-Path (Join-Path $repoRoot $testPath)) {
            $checks += Invoke-LoggedCommand -Name ("pytest_" + ($testPath -replace '[\\\/\.-]','_')) -WorkingDirectory $repoRoot -Exe "python" -CmdArgs @("-m","pytest",$testPath,"-q")
        }
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "20_check_results.csv") -Rows $checks

$failedChecks = @($checks | Where-Object { -not $_.Passed })
$findings = New-Object System.Collections.Generic.List[string]

$findings.Add("# Sandbox Demo Gate Findings")
$findings.Add("")
$findings.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$findings.Add("- Current branch: $($repoState.branch)")
$findings.Add("- Current head: $($repoState.head)")
$findings.Add("- Frozen tag: $($repoState.frozen_tag)")
$findings.Add("- Cohort branch: $($repoState.cohort_branch)")
$findings.Add("- Dirty count: $($repoState.dirty_count)")
$findings.Add("- Frontend reachable: $($repoState.frontend_reachable)")
$findings.Add("- Backend health reachable: $($repoState.backend_health_reachable)")
$findings.Add("- Backend integrity reachable: $($repoState.backend_integrity_reachable)")
$findings.Add("- Executed checks: $($checks.Count)")
$findings.Add("- Failed checks: $($failedChecks.Count)")
$findings.Add("")

$findings.Add("## Result")
$findings.Add("")
$pass =
    ($repoState.dirty_count -eq 0) -and
    [bool]$repoState.frozen_tag -and
    [bool]$repoState.cohort_branch -and
    $repoState.frontend_reachable -and
    $repoState.backend_health_reachable -and
    ($failedChecks.Count -eq 0)

if ($pass) {
    $findings.Add("PASS")
} else {
    $findings.Add("REVIEW REQUIRED")
}
$findings.Add("")

$findings.Add("## Blockers")
$findings.Add("")
if ($repoState.dirty_count -gt 0) {
    $findings.Add("- Dirty worktree entries: $($repoState.dirty_count)")
}
if (-not [bool]$repoState.frozen_tag) {
    $findings.Add("- Missing frozen PASS tag")
}
if (-not [bool]$repoState.cohort_branch) {
    $findings.Add("- Missing sandbox cohort branch")
}
if (-not $repoState.frontend_reachable) {
    $findings.Add("- Frontend not reachable at $FrontendUrl")
}
if (-not $repoState.backend_health_reachable) {
    $findings.Add("- Backend health not reachable at $BackendUrl/api/health/")
}
if ($failedChecks.Count -gt 0) {
    foreach ($c in $failedChecks) {
        $findings.Add("- Failed check: $($c.Name) (exit $($c.ExitCode))")
    }
}
if (($repoState.dirty_count -eq 0) -and [bool]$repoState.frozen_tag -and [bool]$repoState.cohort_branch -and $repoState.frontend_reachable -and $repoState.backend_health_reachable -and ($failedChecks.Count -eq 0)) {
    $findings.Add("- None")
}

Write-Utf8 -Path (Join-Path $script:OutDir "30_findings.md") -Lines $findings

$next = New-Object System.Collections.Generic.List[string]
$next.Add('$ErrorActionPreference = "Stop"')
$next.Add('Set-Location "' + $repoRoot + '"')
$next.Add('git status --short')
$next.Add('powershell -ExecutionPolicy Bypass -File .\scripts\execution\95_live_scorecard_audit.ps1')
$next.Add('powershell -ExecutionPolicy Bypass -File .\scripts\execution\95_live_scorecard_audit.ps1 -Deep')
$next.Add('powershell -ExecutionPolicy Bypass -File .\scripts\execution\100_clear_main_failures.ps1')
$next.Add('powershell -ExecutionPolicy Bypass -File .\scripts\execution\99_force_100_readiness.ps1 -Push')
Write-Utf8 -Path (Join-Path $script:OutDir "40_next_actions.ps1") -Lines $next

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Sandbox Demo Gate Summary")
$summary.Add("")
$summary.Add("- Dirty count: $($repoState.dirty_count)")
$summary.Add("- Frozen tag present: $([bool]$repoState.frozen_tag)")
$summary.Add("- Cohort branch present: $([bool]$repoState.cohort_branch)")
$summary.Add("- Frontend reachable: $($repoState.frontend_reachable)")
$summary.Add("- Backend health reachable: $($repoState.backend_health_reachable)")
$summary.Add("- Executed checks: $($checks.Count)")
$summary.Add("- Failed checks: $($failedChecks.Count)")
$summary.Add("")
if ($pass) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
}

Write-Utf8 -Path (Join-Path $script:OutDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_state = $repoState
    checks = $checks
    failed_checks = $failedChecks
    pass = $pass
}
Write-JsonFile -Path (Join-Path $script:OutDir "99_STATUS.json") -Object $status

Copy-Item -Path (Join-Path $script:OutDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $script:OutDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $script:OutDir '99_STATUS.json')"
Write-Host ""

if (-not $pass) { exit 1 }
