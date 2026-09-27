param(
    [switch]$Deep
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
        & $Exe @CmdArgs *>&1 | Tee-Object -FilePath $logPath -Append | Out-Null
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

function Invoke-GhJson {
    param([string[]]$GhArgs)
    $raw = & gh @GhArgs
    if ($LASTEXITCODE -ne 0) {
        throw "gh command failed: gh $($GhArgs -join ' ')"
    }
    if ([string]::IsNullOrWhiteSpace(($raw | Out-String))) {
        return $null
    }
    return ($raw | ConvertFrom-Json)
}

Require-Tool git
Require-Tool powershell

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot ".crown-audit\full-completion\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\full-completion\latest"

New-Dir $script:OutDir
New-Dir $latestDir

$repoState = [ordered]@{
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    main_head_sha = $null
    dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    commit_count = [int]((git rev-list --count HEAD).Trim())
    open_prs = $null
    open_issues = $null
    failing_main_runs = @()
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
    try {
        $repoState.open_prs = [int](& gh pr list --state open --limit 100 --json number --jq "length")
    } catch {}
    try {
        $repoState.open_issues = [int](& gh issue list --state open --limit 200 --json number --jq "length")
    } catch {}
    try {
        $mainHeadSha = (& gh api "repos/Arete0920/Crown-CSMS/commits/main" --jq ".sha").Trim()
        if (-not [string]::IsNullOrWhiteSpace($mainHeadSha)) {
            $repoState.main_head_sha = $mainHeadSha
        }

        $mainRuns = Invoke-GhJson -GhArgs @(
            "run","list",
            "--branch","main",
            "--limit","80",
            "--json","databaseId,workflowName,status,conclusion,createdAt,url,headSha"
        )
        $repoState.failing_main_runs = @(
            $mainRuns |
            Where-Object {
                $_.status -eq "completed" -and $_.conclusion -in @("failure","cancelled","timed_out","action_required","startup_failure")
            } |
            Where-Object {
                [string]::IsNullOrWhiteSpace($repoState.main_head_sha) -or $_.headSha -eq $repoState.main_head_sha
            } |
            Group-Object workflowName |
            ForEach-Object { $_.Group | Sort-Object createdAt -Descending | Select-Object -First 1 }
        )
    } catch {}
}

Write-JsonFile -Path (Join-Path $script:OutDir "10_repo_state.json") -Object $repoState

$frontendInventory = @()
$backendInventory = @()
$workflowInventory = @()

$frontendRoot = Join-Path $repoRoot "frontend"
$dashboardRoot = Join-Path $repoRoot "frontend\dashboards"
$backendRoot = Join-Path $repoRoot "backend"
$workflowRoot = Join-Path $repoRoot ".github\workflows"

$trackedFiles = @((git ls-files) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

if (Test-Path $frontendRoot) {
    $frontendFiles = $trackedFiles | Where-Object {
        $_ -like 'frontend/*' -and
        $_ -notlike '*/node_modules/*' -and
        $_ -notlike '*/dist/*' -and
        $_ -notlike '*/playwright-report/*' -and
        $_ -notlike '*/test-results/*' -and
        [IO.Path]::GetExtension($_).ToLowerInvariant() -in @('.js','.jsx','.ts','.tsx','.css','.json')
    }

    foreach ($rel in $frontendFiles) {
        $full = Join-Path $repoRoot ($rel -replace '/', '\\')
        $name = [IO.Path]::GetFileName($rel)
        $extension = [IO.Path]::GetExtension($rel)
        $kind = "other"
        if ($full -match '\\src\\pages\\') { $kind = "page" }
        elseif ($full -match '\\src\\components\\') { $kind = "component" }
        elseif ($full -match '\\src\\routes\\') { $kind = "route" }
        elseif ($name -match 'wizard' -or $full -match 'wizard') { $kind = "wizard" }
        elseif ($full -match '\\tests\\') { $kind = "test" }

        $frontendInventory += [pscustomobject]@{
            Kind = $kind
            Path = ($rel -replace '/', '\\')
            Extension = $extension
            Length = $null
        }
    }
}

if (Test-Path $backendRoot) {
    $backendFiles = $trackedFiles | Where-Object {
        $_ -like 'backend/*' -and
        $_ -notlike '*/migrations/*' -and
        $_ -notlike '*/__pycache__/*' -and
        $_ -notlike '*/venv/*' -and
        [IO.Path]::GetExtension($_).ToLowerInvariant() -in @('.py','.json','.yml','.yaml')
    }

    foreach ($rel in $backendFiles) {
        $full = Join-Path $repoRoot ($rel -replace '/', '\\')
        $name = [IO.Path]::GetFileName($rel)
        $extension = [IO.Path]::GetExtension($rel)
        $kind = "other"
        if ($full -match '\\crown_api\\') { $kind = "api" }
        elseif ($full -match '\\comms\\') { $kind = "communications" }
        elseif ($name -match 'wizard' -or $full -match 'wizard') { $kind = "wizard" }
        elseif ($full -match '\\tests?\\') { $kind = "test" }
        elseif ($full -match '\\core\\') { $kind = "core" }
        else { $kind = "backend" }

        $backendInventory += [pscustomobject]@{
            Kind = $kind
            Path = ($rel -replace '/', '\\')
            Extension = $extension
            Length = $null
        }
    }
}

if (Test-Path $workflowRoot) {
    $workflowFiles = $trackedFiles | Where-Object {
        $_ -like '.github/workflows/*' -and [IO.Path]::GetExtension($_).ToLowerInvariant() -in @('.yml','.yaml')
    }
    foreach ($rel in $workflowFiles) {
        $name = [IO.Path]::GetFileName($rel)
        $workflowInventory += [pscustomobject]@{
            Workflow = $name
            Path = ($rel -replace '/', '\\')
            Length = $null
            LastWriteTime = $null
        }
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "20_frontend_inventory.csv") -Rows $frontendInventory
Write-CsvSafe -Path (Join-Path $script:OutDir "21_backend_inventory.csv") -Rows $backendInventory
Write-CsvSafe -Path (Join-Path $script:OutDir "22_workflows.csv") -Rows $workflowInventory

$checks = @()

if ($Deep -and $env:CROWN_102_RUN_HEAVY -eq "1") {
    $scoreScript = Join-Path $repoRoot "scripts\execution\95_live_scorecard_audit.ps1"
    if (Test-Path $scoreScript) {
        $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_baseline" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",$scoreScript)
        $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_deep" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",$scoreScript,"-Deep")
    }

    if (Test-Path (Join-Path $dashboardRoot "package.json")) {
        $packageJson = Join-Path $dashboardRoot "package.json"

        foreach ($scriptName in @(
            "check:shell-contracts",
            "test:unit",
            "test:release:a11y",
            "ui:proof:nav",
            "test:release:routes",
            "ui:proof:matrix",
            "ui:proof:matrix-pack-2",
            "ui:proof:matrix-pack-3",
            "test:e2e:smoke"
        )) {
            if (Test-NpmScript -PackageJsonPath $packageJson -ScriptName $scriptName) {
                $envBlock = @{}
                if ($scriptName -match 'a11y|nav|routes|matrix|smoke') {
                    $envBlock["CI"] = "1"
                }
                $checks += Invoke-LoggedCommand -Name ("frontend_" + ($scriptName -replace '[:\-]','_')) -WorkingDirectory $dashboardRoot -Exe "npm.cmd" -CmdArgs @("run",$scriptName) -Env $envBlock
            }
        }
    }

    if (Test-Path (Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py")) {
        $checks += Invoke-LoggedCommand -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Exe "python" -CmdArgs @("-m","pytest","backend/tests/test_reporting_exports_gate.py","-q")
    }

    if (Test-Path (Join-Path $repoRoot "backend\manage.py")) {
        $checks += Invoke-LoggedCommand -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Exe "python" -CmdArgs @("manage.py","check")
    }

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

Write-CsvSafe -Path (Join-Path $script:OutDir "30_check_results.csv") -Rows $checks

$failedChecks = @($checks | Where-Object { -not $_.Passed })

$findings = New-Object System.Collections.Generic.List[string]
$findings.Add("# Full Completion Audit Findings")
$findings.Add("")
$findings.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$findings.Add("- Branch: $($repoState.branch)")
$findings.Add("- Head: $($repoState.head)")
$findings.Add("- Commit count: $($repoState.commit_count)")
$findings.Add("- Dirty count: $(@($repoState.dirty).Count)")
$findings.Add("- Open PRs: $($repoState.open_prs)")
$findings.Add("- Open issues: $($repoState.open_issues)")
$findings.Add("- Failing main workflows: $(@($repoState.failing_main_runs).Count)")
$findings.Add("- Frontend files inventoried: $($frontendInventory.Count)")
$findings.Add("- Backend files inventoried: $($backendInventory.Count)")
$findings.Add("- Workflow files inventoried: $($workflowInventory.Count)")
$findings.Add("- Executed checks: $($checks.Count)")
$findings.Add("- Failed checks: $($failedChecks.Count)")
$findings.Add("- Deep mode: $Deep")
$findings.Add("")

$findings.Add("## Completion verdict")
$findings.Add("")
if (@($repoState.dirty).Count -eq 0 -and $failedChecks.Count -eq 0 -and @($repoState.failing_main_runs).Count -eq 0 -and ($repoState.open_prs -eq 0) -and ($repoState.open_issues -eq 0)) {
    $findings.Add("PASS")
} else {
    $findings.Add("REVIEW REQUIRED")
}
$findings.Add("")

$findings.Add("## Blockers")
$findings.Add("")
if (@($repoState.dirty).Count -gt 0) {
    $findings.Add("- Dirty worktree entries: $(@($repoState.dirty).Count)")
}
if (@($repoState.failing_main_runs).Count -gt 0) {
    foreach ($r in $repoState.failing_main_runs) {
        $findings.Add("- Failing main workflow: $($r.workflowName) [$($r.databaseId)] => $($r.conclusion)")
    }
}
if ($failedChecks.Count -gt 0) {
    foreach ($c in $failedChecks) {
        $findings.Add("- Failed local check: $($c.Name) (exit $($c.ExitCode))")
    }
}
if (($repoState.open_prs -eq 0) -and ($repoState.open_issues -eq 0) -and (@($repoState.dirty).Count -eq 0) -and ($failedChecks.Count -eq 0) -and (@($repoState.failing_main_runs).Count -eq 0)) {
    $findings.Add("- None")
}
$findings.Add("")

$findings.Add("## Area counts")
$findings.Add("")
$frontendCounts = $frontendInventory | Group-Object Kind | Sort-Object Name
foreach ($g in $frontendCounts) {
    $findings.Add("- Frontend $($g.Name): $($g.Count)")
}
$backendCounts = $backendInventory | Group-Object Kind | Sort-Object Name
foreach ($g in $backendCounts) {
    $findings.Add("- Backend $($g.Name): $($g.Count)")
}

Write-Utf8 -Path (Join-Path $script:OutDir "40_findings.md") -Lines $findings

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Full Completion Audit Summary")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Dirty count: $(@($repoState.dirty).Count)")
$summary.Add("- Open PRs: $($repoState.open_prs)")
$summary.Add("- Open issues: $($repoState.open_issues)")
$summary.Add("- Failing main workflows: $(@($repoState.failing_main_runs).Count)")
$summary.Add("- Executed checks: $($checks.Count)")
$summary.Add("- Failed checks: $($failedChecks.Count)")
$summary.Add("- Deep mode: $Deep")
$summary.Add("")
if (@($repoState.dirty).Count -eq 0 -and $failedChecks.Count -eq 0 -and @($repoState.failing_main_runs).Count -eq 0 -and ($repoState.open_prs -eq 0) -and ($repoState.open_issues -eq 0)) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
}

Write-Utf8 -Path (Join-Path $script:OutDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_state = $repoState
    frontend_inventory_count = $frontendInventory.Count
    backend_inventory_count = $backendInventory.Count
    workflow_inventory_count = $workflowInventory.Count
    checks = $checks
    failed_checks = $failedChecks
    pass = (
        (@($repoState.dirty).Count -eq 0) -and
        ($failedChecks.Count -eq 0) -and
        (@($repoState.failing_main_runs).Count -eq 0) -and
        ($repoState.open_prs -eq 0) -and
        ($repoState.open_issues -eq 0)
    )
}

Write-JsonFile -Path (Join-Path $script:OutDir "99_STATUS.json") -Object $status

Copy-Item -Path (Join-Path $script:OutDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $script:OutDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $script:OutDir '99_STATUS.json')"
Write-Host ""

if ($failedChecks.Count -gt 0 -or @($repoState.dirty).Count -gt 0 -or @($repoState.failing_main_runs).Count -gt 0 -or ($repoState.open_prs -ne 0) -or ($repoState.open_issues -ne 0)) {
    exit 1
}
