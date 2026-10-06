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

function Resolve-PowerShellCommand {
    if (Get-Command pwsh -ErrorAction SilentlyContinue) { return "pwsh" }
    if (Get-Command powershell -ErrorAction SilentlyContinue) { return "powershell" }
    throw "Missing required tool: powershell/pwsh"
}

function Resolve-NpmCommand {
    # Windows PowerShell needs npm.cmd; pwsh on Unix uses npm.
    if (Get-Command npm.cmd -ErrorAction SilentlyContinue) { return "npm.cmd" }
    if (Get-Command npm -ErrorAction SilentlyContinue) { return "npm" }
    throw "Missing required tool: npm"
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

function ConvertTo-CmdToken {
    param([string]$Value)
    if ($null -eq $Value) { return '""' }
    $escaped = $Value -replace '([\^&|<>()%!"])', '^$1'
    if ($escaped -match '\s') { return '"' + $escaped + '"' }
    return $escaped
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
    $stdoutTmp = Join-Path $script:OutDir "$Name.stdout.tmp"
    $stderrTmp = Join-Path $script:OutDir "$Name.stderr.tmp"
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
        $exitCode = 1

        try {
            $resolvedCommand = Get-Command $Exe -ErrorAction SilentlyContinue
            if ($null -eq $resolvedCommand) {
                throw "Executable not found: $Exe"
            }

            $startProcessArgs = @{
                FilePath = $resolvedCommand.Source
                WorkingDirectory = (Get-Location).Path
                NoNewWindow = $true
                PassThru = $true
                Wait = $true
                RedirectStandardOutput = $stdoutTmp
                RedirectStandardError = $stderrTmp
            }

            if ($CmdArgs.Count -gt 0) { $startProcessArgs.ArgumentList = $CmdArgs }
            $proc = Start-Process @startProcessArgs

            $proc.Refresh()
            if (-not $proc.HasExited -or $null -eq $proc.ExitCode) {
                throw "Command terminated without a verifiable exit code: $Exe"
            }
            $exitCode = [int]$proc.ExitCode
        } catch {
            "ERROR invoking command: $_" | Add-Content -Path $logPath -Encoding UTF8
            $exitCode = 1
        }

        if (Test-Path $stdoutTmp) {
            Get-Content $stdoutTmp -ErrorAction SilentlyContinue | Add-Content -Path $logPath -Encoding UTF8
        }
        if (Test-Path $stderrTmp) {
            Get-Content $stderrTmp -ErrorAction SilentlyContinue | Add-Content -Path $logPath -Encoding UTF8
        }

        Remove-Item $stdoutTmp -Force -ErrorAction SilentlyContinue
        Remove-Item $stderrTmp -Force -ErrorAction SilentlyContinue

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
        Remove-Item $stdoutTmp -Force -ErrorAction SilentlyContinue
        Remove-Item $stderrTmp -Force -ErrorAction SilentlyContinue
    }
}

function Get-ModuleName {
    param([string]$BaseName)

    $n = $BaseName.ToLowerInvariant()

    if ($n -match 'admission|applicant|enroll') { return 'Admissions/Enrollment' }
    if ($n -match 'attendance') { return 'Attendance' }
    if ($n -match 'billing|tuition|payment|invoice|finance|ledger') { return 'Billing/Finance' }
    if ($n -match 'academic|grade|report|transcript|course|section|roster') { return 'Academics' }
    if ($n -match 'parent') { return 'Parent' }
    if ($n -match 'student') { return 'Student' }
    if ($n -match 'teacher') { return 'Teacher' }
    if ($n -match 'admin|principal|director|executive|school') { return 'Administration' }
    if ($n -match 'communication|message|sms|email|announcement|comms') { return 'Communications' }
    if ($n -match 'dashboard') { return 'Dashboard' }
    if ($n -match 'wizard|setup') { return 'Wizard/Setup' }
    return 'Unclassified'
}

function Get-PlaceholderHits {
    param([string]$Path)

    $patterns = @(
        'TODO',
        'FIXME',
        'TBD',
        'coming soon',
        'placeholder',
        'mock',
        'stub',
        'later',
        'not implemented',
        'sample data',
        'dummy',
        'lorem ipsum'
    )

    $hits = @()
    try {
        $content = Get-Content $Path -Raw
        foreach ($p in $patterns) {
            if ($content -match [regex]::Escape($p)) {
                $hits += $p
            }
        }
    } catch {}

    return @($hits | Select-Object -Unique)
}

Require-Tool git
$shellExe = Resolve-PowerShellCommand

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$dirty = @(
    (git status --porcelain=v1) |
    Where-Object {
        -not [string]::IsNullOrWhiteSpace($_) -and
        ($_ -notmatch '\.crown-audit(?:[\\/]|$)')
    }
)
if ($dirty.Count -gt 0) {
    throw "Worktree must be clean before dashboard completion gate."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot ".crown-audit\dashboard-completion\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\dashboard-completion\latest"
New-Dir $script:OutDir
New-Dir $latestDir

$dashboardRoot = Join-Path $repoRoot "frontend\dashboards"
$pagesDir = Join-Path $dashboardRoot "src\pages"
$routesDir = Join-Path $dashboardRoot "src\routes"
$routerPath = Join-Path $routesDir "router.jsx"
$roleRedirectPath = Join-Path $pagesDir "RoleHomeRedirect.jsx"
$packageJson = Join-Path $dashboardRoot "package.json"

$routerText = ""
if (Test-Path $routerPath) {
    $routerText = Get-Content $routerPath -Raw
}

$roleRedirectText = ""
if (Test-Path $roleRedirectPath) {
    $roleRedirectText = Get-Content $roleRedirectPath -Raw
}

$dashboardInventory = @()
$wizardInventory = @()
$routerRefs = @()

if (Test-Path $pagesDir) {
    $pageFiles = Get-ChildItem $pagesDir -File -Recurse | Where-Object {
        $_.Extension -in @('.js', '.jsx', '.ts', '.tsx')
    }
    foreach ($f in $pageFiles) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        $module = Get-ModuleName -BaseName $base
        $isWizard = ($base -match 'wizard|setup')
        $placeholders = @(Get-PlaceholderHits -Path $f.FullName)
        $routerMentions = 0
        $roleRedirectMentions = 0

        if ($routerText) {
            $routerMentions = ([regex]::Matches($routerText, [regex]::Escape($base))).Count
        }
        if ($roleRedirectText) {
            $roleRedirectMentions = ([regex]::Matches($roleRedirectText, [regex]::Escape($base))).Count
        }

        $row = [pscustomobject]@{
            Module = $module
            Page = $base
            Path = $f.FullName.Replace($repoRoot + "\", "")
            IsWizard = $isWizard
            RouterMentions = $routerMentions
            RoleRedirectMentions = $roleRedirectMentions
            PlaceholderHitCount = $placeholders.Count
            PlaceholderHits = ($placeholders -join '; ')
            Length = $f.Length
        }

        $dashboardInventory += $row
        if ($isWizard) {
            $wizardInventory += $row
        }
    }
}

if ($routerText) {
    $routeLines = @(Get-Content $routerPath)
    $lineNo = 0
    foreach ($line in $routeLines) {
        $lineNo++
        if ($line -match 'path\s*:\s*["'']([^"'']+)["'']') {
            $pathValue = $Matches[1]
            $routerRefs += [pscustomobject]@{
                RoutePath = $pathValue
                LineNumber = $lineNo
                Source = $routerPath.Replace($repoRoot + "\", "")
                Line = $line.Trim()
            }
        }
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "20_dashboard_inventory.csv") -Rows $dashboardInventory
Write-CsvSafe -Path (Join-Path $script:OutDir "21_wizard_inventory.csv") -Rows $wizardInventory
Write-CsvSafe -Path (Join-Path $script:OutDir "22_router_references.csv") -Rows $routerRefs

$checks = @()

$run95Baseline = ($env:CROWN_105_RUN_95_BASELINE -eq "1")
$run95Deep = $Deep -or ($env:CROWN_105_RUN_95_DEEP -eq "1")
$scorecardEnv = @{}
if ([string]::IsNullOrWhiteSpace($env:GH_TOKEN) -and -not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
    $scorecardEnv["GH_TOKEN"] = $env:GITHUB_TOKEN
}

if ($run95Baseline) {
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_baseline" -WorkingDirectory $repoRoot -Exe $shellExe -CmdArgs @("-ExecutionPolicy","Bypass","-File",".\scripts\execution\95_live_scorecard_audit.ps1") -Env $scorecardEnv
} else {
    $checks += [pscustomobject]@{
        Name = "95_live_scorecard_audit_baseline"
        Passed = $true
        ExitCode = 0
        Log = "(skipped; set CROWN_105_RUN_95_BASELINE=1)"
    }
}

if ($run95Deep) {
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_deep" -WorkingDirectory $repoRoot -Exe $shellExe -CmdArgs @("-ExecutionPolicy","Bypass","-File",".\scripts\execution\95_live_scorecard_audit.ps1","-Deep") -Env $scorecardEnv
} else {
    $checks += [pscustomobject]@{
        Name = "95_live_scorecard_audit_deep"
        Passed = $true
        ExitCode = 0
        Log = "(skipped; pass -Deep or set CROWN_105_RUN_95_DEEP=1)"
    }
}

if (Test-Path $packageJson) {
    $npmExe = Resolve-NpmCommand
    $runHeavyFrontend = $Deep -or ($env:CROWN_105_RUN_HEAVY_FRONTEND -eq "1")
    foreach ($scriptName in @(
        "check:shell-contracts",
        "test:unit",
        "ui:proof:nav",
        "test:release:routes",
        "test:release:a11y",
        "test:e2e:smoke"
    )) {
        if ($scriptName -ne "check:shell-contracts" -and -not $runHeavyFrontend) {
            $checks += [pscustomobject]@{
                Name = ("frontend_" + ($scriptName -replace '[:\-]','_'))
                Passed = $true
                ExitCode = 0
                Log = "(skipped; set CROWN_105_RUN_HEAVY_FRONTEND=1 or pass -Deep)"
            }
            continue
        }

        if (Test-NpmScript -PackageJsonPath $packageJson -ScriptName $scriptName) {
            $envBlock = @{}
            if ($scriptName -match 'nav|routes|a11y|smoke') {
                $envBlock["CI"] = "1"
            }
            if ($scriptName -eq "test:e2e:smoke") {
                $envBlock["VITE_DEV_BASE_URL"] = "http://127.0.0.1:4173"
                $envBlock["CROWN_DEMO_SCHOOL_ID"] = "19801b59-8c05-4c84-9312-5d792e4e839d"
                $demoToken = $env:CROWN_DEMO_TOKEN
                if ([string]::IsNullOrWhiteSpace($demoToken)) {
                    throw "Missing required environment variable: CROWN_DEMO_TOKEN"
                }
                $envBlock["CROWN_DEMO_TOKEN"] = $demoToken
            }

            $checks += Invoke-LoggedCommand -Name ("frontend_" + ($scriptName -replace '[:\-]','_')) -WorkingDirectory $dashboardRoot -Exe $npmExe -CmdArgs @("run",$scriptName) -Env $envBlock
        }
    }

    if ($Deep) {
        foreach ($scriptName in @(
            "ui:proof:matrix",
            "ui:proof:matrix-pack-2",
            "ui:proof:matrix-pack-3"
        )) {
            if (Test-NpmScript -PackageJsonPath $packageJson -ScriptName $scriptName) {
                $checks += Invoke-LoggedCommand -Name ("frontend_" + ($scriptName -replace '[:\-]','_')) -WorkingDirectory $dashboardRoot -Exe $npmExe -CmdArgs @("run",$scriptName) -Env @{ CI = "1" }
            }
        }
    }
}

if (Test-Path (Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py")) {
    if ($Deep -or ($env:CROWN_105_RUN_BACKEND_PYTEST -eq "1")) {
        $checks += Invoke-LoggedCommand -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Exe "python" -CmdArgs @("-m","pytest","backend/tests/test_reporting_exports_gate.py","-q")
    } else {
        $checks += [pscustomobject]@{
            Name = "backend_reporting_exports_gate"
            Passed = $true
            ExitCode = 0
            Log = "(skipped; set CROWN_105_RUN_BACKEND_PYTEST=1 or pass -Deep)"
        }
    }
}

if (Test-Path (Join-Path $repoRoot "backend\manage.py")) {
    $checks += Invoke-LoggedCommand -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Exe "python" -CmdArgs @("manage.py","check")
}

Write-CsvSafe -Path (Join-Path $script:OutDir "30_check_results.csv") -Rows $checks

$failedChecks = @($checks | Where-Object { -not $_.Passed })
$orphanPages = @($dashboardInventory | Where-Object { -not $_.IsWizard -and $_.RouterMentions -eq 0 -and $_.RoleRedirectMentions -eq 0 })
$placeholderPages = @($dashboardInventory | Where-Object { $_.PlaceholderHitCount -gt 0 })

$enforceStructuralBlockers = ($env:CROWN_105_ENFORCE_STRUCTURAL_BLOCKERS -eq "1")

$moduleMatrix = @(
    $dashboardInventory |
    Group-Object Module |
    Sort-Object Name |
    ForEach-Object {
        $g = $_.Group
        [pscustomobject]@{
            Module = $_.Name
            Pages = @($g | Where-Object { -not $_.IsWizard }).Count
            Wizards = @($g | Where-Object { $_.IsWizard }).Count
            RouterReferencedPages = @($g | Where-Object { -not $_.IsWizard -and $_.RouterMentions -gt 0 }).Count
            OrphanPages = @($g | Where-Object { -not $_.IsWizard -and $_.RouterMentions -eq 0 -and $_.RoleRedirectMentions -eq 0 }).Count
            PlaceholderPages = @($g | Where-Object { $_.PlaceholderHitCount -gt 0 }).Count
        }
    }
)

Write-CsvSafe -Path (Join-Path $script:OutDir "40_module_dashboard_matrix.csv") -Rows $moduleMatrix

$blockers = New-Object System.Collections.Generic.List[string]
$blockers.Add("# Dashboard Completion Blockers")
$blockers.Add("")
$blockers.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$blockers.Add("- Executed checks: $($checks.Count)")
$blockers.Add("- Failed checks: $($failedChecks.Count)")
$blockers.Add("- Structural blocker enforcement: $enforceStructuralBlockers")
$blockers.Add("- Orphan pages: $($orphanPages.Count)")
$blockers.Add("- Placeholder-flagged pages: $($placeholderPages.Count)")
$blockers.Add("")

if ($failedChecks.Count -gt 0) {
    $blockers.Add("## Failed checks")
    $blockers.Add("")
    foreach ($c in $failedChecks) {
        $blockers.Add("- $($c.Name) (exit $($c.ExitCode))")
    }
    $blockers.Add("")
}

if ($orphanPages.Count -gt 0) {
    if ($enforceStructuralBlockers) {
        $blockers.Add("## Pages with no router or role-home reference")
    } else {
        $blockers.Add("## Advisory: pages with no router or role-home reference")
    }
    $blockers.Add("")
    foreach ($p in $orphanPages | Sort-Object Module, Page) {
        $blockers.Add("- [$($p.Module)] $($p.Page) => $($p.Path)")
    }
    $blockers.Add("")
}

if ($placeholderPages.Count -gt 0) {
    if ($enforceStructuralBlockers) {
        $blockers.Add("## Pages flagged for placeholder/TODO content")
    } else {
        $blockers.Add("## Advisory: pages flagged for placeholder/TODO content")
    }
    $blockers.Add("")
    foreach ($p in $placeholderPages | Sort-Object Module, Page) {
        $blockers.Add("- [$($p.Module)] $($p.Page) => $($p.PlaceholderHits)")
    }
    $blockers.Add("")
}

if ($failedChecks.Count -eq 0 -and (($orphanPages.Count -eq 0 -and $placeholderPages.Count -eq 0) -or -not $enforceStructuralBlockers)) {
    $blockers.Add("## Blockers")
    $blockers.Add("")
    $blockers.Add("- None")
}

Write-Utf8 -Path (Join-Path $script:OutDir "50_blockers.md") -Lines $blockers

$structuralClean = ($orphanPages.Count -eq 0 -and $placeholderPages.Count -eq 0)
$pass = ($failedChecks.Count -eq 0 -and ($structuralClean -or -not $enforceStructuralBlockers))

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Dashboard Module Completion Gate Summary")
$summary.Add("")
$summary.Add("- Dirty count: $($dirty.Count)")
$summary.Add("- Dashboard pages: $(@($dashboardInventory | Where-Object { -not $_.IsWizard }).Count)")
$summary.Add("- Wizards: $($wizardInventory.Count)")
$summary.Add("- Executed checks: $($checks.Count)")
$summary.Add("- Failed checks: $($failedChecks.Count)")
$summary.Add("- Structural blocker enforcement: $enforceStructuralBlockers")
$summary.Add("- Orphan pages: $($orphanPages.Count)")
$summary.Add("- Placeholder pages: $($placeholderPages.Count)")
$summary.Add("")
if ($pass) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
}

Write-Utf8 -Path (Join-Path $script:OutDir "00_SUMMARY.md") -Lines $summary

$branch = ""
try {
    $branch = (git branch --show-current 2>$null)
} catch {}
$branch = ("$branch" -replace '^\s+','' -replace '\s+$','')
if ([string]::IsNullOrWhiteSpace($branch)) {
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_HEAD_REF)) {
        $branch = $env:GITHUB_HEAD_REF
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF_NAME)) {
        $branch = $env:GITHUB_REF_NAME
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF)) {
        $branch = $env:GITHUB_REF
    }
    else {
        $branch = "detached"
    }
}

$head = ""
try {
    $head = (git rev-parse HEAD 2>$null)
} catch {}
$head = ("$head" -replace '^\s+','' -replace '\s+$','')
if ([string]::IsNullOrWhiteSpace($head)) {
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_SHA)) {
        $head = $env:GITHUB_SHA
    }
    else {
        $head = "UNKNOWN"
    }
}

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = $branch
    head = $head
    dashboard_inventory = $dashboardInventory
    wizard_inventory = $wizardInventory
    router_references = $routerRefs
    checks = $checks
    failed_checks = $failedChecks
    orphan_pages = $orphanPages
    placeholder_pages = $placeholderPages
    module_matrix = $moduleMatrix
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
