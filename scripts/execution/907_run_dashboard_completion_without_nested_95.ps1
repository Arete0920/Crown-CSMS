param(
    [switch]$EnforceStructuralBlockers
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$LogPath
    )

    $start = Get-Date
    @(
        "=== $Name ===",
        "Started: $($start.ToString('s'))",
        "PWD: $WorkingDirectory",
        "CMD: $Command",
        ""
    ) | Set-Content -Path $LogPath -Encoding UTF8

    $ok = $true
    $exitCode = 0
    Push-Location $WorkingDirectory
    try {
        cmd.exe /d /s /c $Command 1>> $LogPath 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        if ($exitCode -ne 0) { $ok = $false }
    } catch {
        $ok = $false
        $exitCode = 1
        $_ | Out-String | Add-Content -Path $LogPath
    } finally {
        Pop-Location
    }

    $seconds = [int]((Get-Date) - $start).TotalSeconds
    @(
        "",
        "Completed: $((Get-Date).ToString('s'))",
        "ExitCode: $exitCode",
        "Passed: $ok",
        "Seconds: $seconds"
    ) | Add-Content -Path $LogPath -Encoding UTF8

    return [pscustomobject]@{
        Name = $Name
        Command = $Command
        WorkingDirectory = $WorkingDirectory
        LogPath = $LogPath
        ExitCode = $exitCode
        Passed = $ok
        Seconds = $seconds
    }
}

function Has-NpmScript {
    param([string]$PackageJsonPath, [string]$ScriptName)
    if (-not (Test-Path $PackageJsonPath)) { return $false }
    $json = Get-Content $PackageJsonPath -Raw | ConvertFrom-Json
    if ($null -eq $json.scripts) { return $false }
    return $json.scripts.PSObject.Properties.Name -contains $ScriptName
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and ($_ -notmatch '\.crown-audit(?:[\\/]|$)') -and ($_ -notmatch 'audit-artifacts[\\/]live-scorecard(?:[\\/]|$)') })
if ($dirty.Count -gt 0) { throw "Worktree must be clean before dashboard completion runner. Dirty rows: $($dirty.Count)" }

$head = (git rev-parse HEAD).Trim()
$branch = (git branch --show-current 2>$null)
if ([string]::IsNullOrWhiteSpace($branch)) { $branch = "detached-head" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\dashboard-completion-no95\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\dashboard-completion-no95\latest"
$logsDir = Join-Path $outDir "logs"
New-Dir $logsDir
New-Dir $latestDir

$dashboardRoot = Join-Path $repoRoot "frontend\dashboards"
$packageJson = Join-Path $dashboardRoot "package.json"
if (-not (Test-Path $packageJson)) { throw "Missing frontend/dashboards/package.json" }

$env:CI = "1"
$env:VITE_SANDBOX_READY_ONLY = "true"
$env:VITE_HIDE_UNREADY_NAV = "true"
$env:VITE_SANDBOX_MODE = "1"
$env:CROWN_ENV = "production"
$env:CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = "0"
$env:TENANT_HEADER_REQUIRED = "0"

$steps = New-Object System.Collections.Generic.List[object]

$scripts = @(
    "check:shell-contracts",
    "test:unit",
    "ui:proof:nav",
    "test:release:routes",
    "test:release:a11y",
    "ui:proof:matrix",
    "ui:proof:matrix-pack-2",
    "ui:proof:matrix-pack-3"
)

foreach ($scriptName in $scripts) {
    if (Has-NpmScript -PackageJsonPath $packageJson -ScriptName $scriptName) {
        $safeName = "frontend_" + ($scriptName -replace '[:\-]', '_')
        $steps.Add((Invoke-Step -Name $safeName -WorkingDirectory $dashboardRoot -Command "npm.cmd run $scriptName" -LogPath (Join-Path $logsDir "$safeName.log"))) | Out-Null
    }
}

if (Test-Path (Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py")) {
    $steps.Add((Invoke-Step -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Command "python -m pytest backend\tests\test_reporting_exports_gate.py -q" -LogPath (Join-Path $logsDir "backend_reporting_exports_gate.log"))) | Out-Null
}

if (Test-Path (Join-Path $repoRoot "backend\manage.py")) {
    $steps.Add((Invoke-Step -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Command "python manage.py check" -LogPath (Join-Path $logsDir "backend_django_check.log"))) | Out-Null
}

$failed = @($steps | Where-Object { -not $_.Passed })
$passed = @($steps | Where-Object { $_.Passed })
$pass = ($failed.Count -eq 0 -and $steps.Count -gt 0)

$stepsPath = Join-Path $outDir "30_check_results.csv"
$summaryPath = Join-Path $outDir "00_SUMMARY.md"
$statusPath = Join-Path $outDir "99_STATUS.json"
$blockersPath = Join-Path $outDir "50_blockers.md"
$steps | Export-Csv -Path $stepsPath -NoTypeInformation -Encoding UTF8

@(
    "# Dashboard Completion Without Nested 95",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $branch",
    "- Head: $head",
    "- Executed checks: $($steps.Count)",
    "- Passed checks: $($passed.Count)",
    "- Failed checks: $($failed.Count)",
    "- Structural blocker enforcement requested: $EnforceStructuralBlockers",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" })
) | Set-Content -Path $summaryPath -Encoding UTF8

$blockers = New-Object System.Collections.Generic.List[string]
$blockers.Add("# Dashboard Completion No-95 Blockers")
$blockers.Add("")
$blockers.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$blockers.Add("- Failed checks: $($failed.Count)")
$blockers.Add("")
if ($failed.Count -eq 0) {
    $blockers.Add("## Blockers")
    $blockers.Add("")
    $blockers.Add("- None from executed no-95 checks.")
} else {
    $blockers.Add("## Failed checks")
    $blockers.Add("")
    foreach ($f in $failed) { $blockers.Add("- $($f.Name) exit $($f.ExitCode): $($f.LogPath)") }
}
$blockers | Set-Content -Path $blockersPath -Encoding UTF8

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = $branch
    head = $head
    pass = $pass
    executed_checks = $steps.Count
    passed_checks = $passed.Count
    failed_checks = $failed.Count
    failed = $failed
    output_dir = $outDir
}
($status | ConvertTo-Json -Depth 8) | Set-Content -Path $statusPath -Encoding UTF8

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "Dashboard completion no-95 runner complete."
Write-Host "Summary: $summaryPath"
Write-Host "Latest:  $latestDir"

if (-not $pass) { exit 1 }
