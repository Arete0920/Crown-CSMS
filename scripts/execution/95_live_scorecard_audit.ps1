param(
    [switch]$Deep
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$script:IsWindowsPlatform = $false
if (Get-Variable IsWindows -ErrorAction SilentlyContinue) {
    $script:IsWindowsPlatform = [bool]$IsWindows
} else {
    $script:IsWindowsPlatform = ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT)
}

function Invoke-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$LogFile,
        [Parameter(Mandatory = $true)][string]$Exe,
        [string[]]$CmdParts = @(),
        [hashtable]$Env = @{}
    )

    $fullLog = Join-Path $script:OutDir $LogFile
    $saved = @{}

    foreach ($k in $Env.Keys) {
        $saved[$k] = [Environment]::GetEnvironmentVariable($k, "Process")
        [Environment]::SetEnvironmentVariable($k, [string]$Env[$k], "Process")
    }

    # If CI mode is requested, ensure port 4173 is free before starting
    if ($Env.ContainsKey("CI")) {
        Wait-Port4173Free
    }

    Push-Location $WorkingDirectory
    try {
        "=== $Name ===" | Set-Content -Path $fullLog -Encoding UTF8
        "PWD: $(Get-Location)" | Add-Content -Path $fullLog -Encoding UTF8
        "CMD: $Exe $($CmdParts -join ' ')" | Add-Content -Path $fullLog -Encoding UTF8
        "" | Add-Content -Path $fullLog -Encoding UTF8

        $outTmp = Join-Path $script:OutDir ("$Name.stdout.tmp")
        $errTmp = Join-Path $script:OutDir ("$Name.stderr.tmp")
        $timeoutSec = 900
        $exitCode = 1
        if ($env:CROWN_95_CMD_TIMEOUT_SEC -and $env:CROWN_95_CMD_TIMEOUT_SEC -match '^\d+$') {
            $timeoutSec = [int]$env:CROWN_95_CMD_TIMEOUT_SEC
        }

        try {
            $resolvedExe = Resolve-CrownExecutable -Exe $Exe
            $resolvedCommand = Get-Command $resolvedExe -ErrorAction SilentlyContinue

            if ($null -eq $resolvedCommand) {
                throw "Executable not found: $resolvedExe (original: $Exe)"
            }

            $proc = Start-Process -FilePath $resolvedCommand.Source -ArgumentList $CmdParts -WorkingDirectory (Get-Location).Path -NoNewWindow -PassThru -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp
            $finished = $proc.WaitForExit($timeoutSec * 1000)

            if (-not $finished) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                "TIMEOUT: command exceeded ${timeoutSec}s and was terminated." | Add-Content -Path $fullLog -Encoding UTF8
                $exitCode = 124
            } else {
                $exitCode = [int]$proc.ExitCode
            }

            if (Test-Path $outTmp) {
                Get-Content $outTmp -ErrorAction SilentlyContinue | Add-Content -Path $fullLog -Encoding UTF8
            }
            if (Test-Path $errTmp) {
                Get-Content $errTmp -ErrorAction SilentlyContinue | Add-Content -Path $fullLog -Encoding UTF8
            }
        } catch {
            "ERROR: $_" | Add-Content -Path $fullLog -Encoding UTF8
            $exitCode = 1
        } finally {
            Remove-Item $outTmp -Force -ErrorAction SilentlyContinue
            Remove-Item $errTmp -Force -ErrorAction SilentlyContinue
        }

        return [pscustomobject]@{
            Name      = $Name
            Passed    = ($exitCode -eq 0)
            ExitCode  = $exitCode
            LogFile   = $fullLog
            LogRel    = $LogFile
        }
    }
    finally {
        Pop-Location
        foreach ($k in $Env.Keys) {
            [Environment]::SetEnvironmentVariable($k, $saved[$k], "Process")
        }
        # Kill any lingering preview server on port 4173 after CI suite completes
        if ($Env.ContainsKey("CI")) {
            Stop-Port4173Listeners
        }
    }
}

function Resolve-CrownExecutable {
    param(
        [Parameter(Mandatory = $true)][string]$Exe
    )

    if ($script:IsWindowsPlatform) {
        return $Exe
    }

    switch -Regex ($Exe) {
        '^npm(\.cmd)?$' { return 'npm' }
        '^npx(\.cmd)?$' { return 'npx' }
        '^node(\.exe)?$' { return 'node' }
        '^python(\.exe)?$' { return 'python' }
        '^py(\.exe)?$' { return 'python' }
        default { return $Exe }
    }
}

function Get-Score {
    param([double]$Value)
    return [math]::Round([math]::Max(0, [math]::Min(10, $Value)), 1)
}

function Get-StatusFromScore {
    param([double]$Value)
    if ($Value -ge 9.0) { return "Strong" }
    if ($Value -ge 8.0) { return "Good" }
    if ($Value -ge 7.0) { return "Mixed" }
    return "Weak"
}

function Test-Port4173Listening {
    if ($script:IsWindowsPlatform) {
        $getNetTcp = Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue
        if ($null -ne $getNetTcp) {
            return [bool](Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue)
        }

        $netstatCmd = Get-Command netstat -ErrorAction SilentlyContinue
        if ($null -eq $netstatCmd) { return $false }

        return [bool]((& netstat -ano 2>$null) | Where-Object { $_ -match ":4173\s.*LISTENING" })
    }

    $lsofCmd = Get-Command lsof -ErrorAction SilentlyContinue
    if ($null -ne $lsofCmd) {
        return [bool](& lsof -ti tcp:4173 -sTCP:LISTEN 2>$null)
    }

    $ssCmd = Get-Command ss -ErrorAction SilentlyContinue
    if ($null -ne $ssCmd) {
        return [bool]((& ss -ltnp "sport = :4173" 2>$null) | Where-Object { $_ -match ":4173" })
    }

    return $false
}

function Wait-Port4173Free {
    for ($i = 0; $i -lt 3; $i++) {
        Stop-Port4173Listeners
        if (-not (Test-Port4173Listening)) { break }
        Start-Sleep -Seconds 2
    }

    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-Port4173Listening)) { return }
        Start-Sleep -Milliseconds 500
    }
}

function Stop-Port4173Listeners {
    # Cross-platform cleanup for preview server port 4173.

    if ($script:IsWindowsPlatform) {
        $getNetTcp = Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue
        if ($null -ne $getNetTcp) {
            $tcpConns = Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue
            foreach ($conn in $tcpConns) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
            return
        }

        $netstatCmd = Get-Command netstat -ErrorAction SilentlyContinue
        if ($null -eq $netstatCmd) { return }

        $netstatLines = (& netstat -ano 2>$null) | Where-Object { $_ -match ":4173\s.*LISTENING" }
        foreach ($line in $netstatLines) {
            $pidStr = ($line.Trim() -split '\s+')[-1]
            if ($pidStr -match '^\d+$' -and $pidStr -ne '0') {
                Stop-Process -Id ([int]$pidStr) -Force -ErrorAction SilentlyContinue
            }
        }
        return
    }

    $lsofCmd = Get-Command lsof -ErrorAction SilentlyContinue
    if ($null -ne $lsofCmd) {
        $pids = & lsof -ti tcp:4173 -sTCP:LISTEN 2>$null
        foreach ($pid in @($pids)) {
            if ("$pid" -match '^\d+$') {
                Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
            }
        }
        return
    }

    $ssCmd = Get-Command ss -ErrorAction SilentlyContinue
    if ($null -eq $ssCmd) { return }

    $ssLines = & ss -ltnp "sport = :4173" 2>$null
    foreach ($line in @($ssLines)) {
        foreach ($m in [regex]::Matches($line, 'pid=(\d+)')) {
            Stop-Process -Id ([int]$m.Groups[1].Value) -Force -ErrorAction SilentlyContinue
        }
    }
}

function Add-Note {
    param(
        [string[]]$Existing,
        [string]$Text
    )
    if ([string]::IsNullOrWhiteSpace($Text)) { return $Existing }
    return @($Existing + $Text)
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot "audit-artifacts\live-scorecard\$timestamp"
$latestDir = Join-Path $repoRoot "audit-artifacts\live-scorecard\latest"

New-Item -ItemType Directory -Force -Path $script:OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null

$repoState = [ordered]@{}
$branchRaw = ""
try {
    $branchRaw = [string](git branch --show-current 2>$null)
} catch {
    $branchRaw = ""
}
$branchRaw = ("$branchRaw").Trim()
if ([string]::IsNullOrWhiteSpace($branchRaw)) {
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_HEAD_REF)) {
        $branchRaw = [string]$env:GITHUB_HEAD_REF
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF_NAME)) {
        $branchRaw = [string]$env:GITHUB_REF_NAME
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF)) {
        $branchRaw = [string]$env:GITHUB_REF
    }
    else {
        $branchRaw = "detached-head"
    }
}
$branchRaw = ("$branchRaw").Trim()
if ($branchRaw -like "refs/heads/*") {
    $branchRaw = $branchRaw.Substring(11)
}

$headRaw = ""
try {
    $headRaw = [string](git rev-parse HEAD 2>$null)
} catch {
    $headRaw = ""
}
$headRaw = ("$headRaw").Trim()
if ([string]::IsNullOrWhiteSpace($headRaw)) {
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_SHA)) {
        $headRaw = ("$env:GITHUB_SHA").Trim()
    }
    else {
        $headRaw = "UNKNOWN"
    }
}

$commitCountRaw = ""
try {
    $commitCountRaw = [string](git rev-list --count HEAD 2>$null)
} catch {
    $commitCountRaw = "0"
}
$commitCount = 0
if (-not [int]::TryParse(("$commitCountRaw").Trim(), [ref]$commitCount)) {
    $commitCount = 0
}

$repoState.Branch = $branchRaw
$repoState.Head = $headRaw
$repoState.CommitCount = $commitCount
$repoState.StatusLines = @(git status --porcelain)
$repoState.DirtyCount = @($repoState.StatusLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count

$trackedFiles = @(git ls-files)
$tmpTrackedCount = @(
    $trackedFiles | Where-Object {
        $_ -match '(^|/)(_tmp_|tmp_|temp_|backup_|scratch_)' -or
        $_ -match '(^|/).*\.tmp$'
    }
).Count

$ghAvailable = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)
$github = [ordered]@{
    Available = $ghAvailable
    RepoSlug = $null
    OpenPRCount = $null
    OpenIssueCount = $null
    OpenPRs = @()
    OpenIssues = @()
}

if ($ghAvailable) {
    try {
        $github.RepoSlug = (gh repo view --json nameWithOwner --jq .nameWithOwner).Trim()
    } catch {
        $github.RepoSlug = $null
    }

    try {
        $prJson = gh pr list --state open --limit 100 --json number,title,isDraft,mergeStateStatus,headRefName
        if (-not [string]::IsNullOrWhiteSpace($prJson)) {
            $github.OpenPRs = @($prJson | ConvertFrom-Json)
            $github.OpenPRCount = $github.OpenPRs.Count
        }
    } catch {
        $github.OpenPRCount = $null
    }

    try {
        $issueJson = gh issue list --state open --limit 200 --json number,title
        if (-not [string]::IsNullOrWhiteSpace($issueJson)) {
            $github.OpenIssues = @($issueJson | ConvertFrom-Json)
            $github.OpenIssueCount = $github.OpenIssues.Count
        }
    } catch {
        $github.OpenIssueCount = $null
    }
}

$frontendDir = Join-Path $repoRoot "frontend\dashboards"

# Ensure port 4173 is free before starting any Playwright/CI suites
Wait-Port4173Free

$results = @()

if (Test-Path (Join-Path $frontendDir "package.json")) {
    $results += Invoke-Capture -Name "frontend_check_shell_contracts" -WorkingDirectory $frontendDir -LogFile "frontend_check_shell_contracts.txt" -Exe "npm" -CmdParts @("run", "check:shell-contracts")
    $results += Invoke-Capture -Name "frontend_unit" -WorkingDirectory $frontendDir -LogFile "frontend_unit.txt" -Exe "npm" -CmdParts @("run", "test:unit") -Env @{ CI = "1" }

    # Build once and start a single shared preview server for all Playwright suites.
    # This avoids the Windows issue where per-suite CI builds leave orphaned node processes
    # on port 4173, causing reuseExistingServer:false to reject subsequent suite startups.
    $buildResult = Invoke-Capture -Name "frontend_build" -WorkingDirectory $frontendDir -LogFile "frontend_build.txt" -Exe "npm" -CmdParts @("run", "build")
    $buildRecord = @($buildResult | Where-Object { $_ -and $_.PSObject.Properties.Name -contains "ExitCode" } | Select-Object -Last 1)
    $buildExit = if ($buildRecord.Count -gt 0 -and $null -ne $buildRecord[0].ExitCode) { [int]$buildRecord[0].ExitCode } else { 1 }

    if ($buildExit -eq 0) {
        # Ensure port is clear, then start the preview server as a background job
        Wait-Port4173Free
        $previewJob = Start-Job -ScriptBlock {
            param($dir)
            Set-Location $dir
            $npmCommand = Get-Command npm -ErrorAction Stop
            & $npmCommand.Source run preview -- --port 4173 --strictPort 2>&1
        } -ArgumentList $frontendDir

        # Wait until port 4173 is accepting connections (up to 60s)
        $ready = $false
        $deadline = (Get-Date).AddSeconds(60)
        while ((Get-Date) -lt $deadline) {
            try {
                $r = Invoke-WebRequest -Uri "http://localhost:4173" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                $ready = $true
                break
            } catch { Start-Sleep -Milliseconds 800 }
        }

        if ($ready) {
            # All Playwright suites reuse the running preview server (no CI=1 means reuseExistingServer:true)
            # VITE_DEV_BASE_URL is already the default; set retries via PLAYWRIGHT_RETRIES if needed
            $results += Invoke-Capture -Name "frontend_release_a11y" -WorkingDirectory $frontendDir -LogFile "frontend_release_a11y.txt" -Exe "npm" -CmdParts @("run", "test:release:a11y") -Env @{ PLAYWRIGHT_RETRIES = "2" }
            $results += Invoke-Capture -Name "frontend_nav"           -WorkingDirectory $frontendDir -LogFile "frontend_nav.txt"           -Exe "npm" -CmdParts @("run", "ui:proof:nav")
            $results += Invoke-Capture -Name "frontend_release_routes" -WorkingDirectory $frontendDir -LogFile "frontend_release_routes.txt" -Exe "npm" -CmdParts @("run", "test:release:routes")

            if ($Deep) {
                $results += Invoke-Capture -Name "frontend_matrix_1" -WorkingDirectory $frontendDir -LogFile "frontend_matrix_1.txt" -Exe "npm" -CmdParts @("run", "ui:proof:matrix")
                $results += Invoke-Capture -Name "frontend_matrix_2" -WorkingDirectory $frontendDir -LogFile "frontend_matrix_2.txt" -Exe "npm" -CmdParts @("run", "ui:proof:matrix-pack-2")
                $results += Invoke-Capture -Name "frontend_matrix_3" -WorkingDirectory $frontendDir -LogFile "frontend_matrix_3.txt" -Exe "npm" -CmdParts @("run", "ui:proof:matrix-pack-3")
            }
        } else {
            "Preview server did not become ready within 60s" | Set-Content -Path (Join-Path $script:OutDir "frontend_preview_timeout.txt") -Encoding UTF8
            $results += [pscustomobject]@{ Name = "frontend_release_a11y"; Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
            $results += [pscustomobject]@{ Name = "frontend_nav";           Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
            $results += [pscustomobject]@{ Name = "frontend_release_routes"; Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
        }

        # Kill the preview server job and any leftover node process on port 4173
        if ($previewJob) { Stop-Job $previewJob -ErrorAction SilentlyContinue; Remove-Job $previewJob -Force -ErrorAction SilentlyContinue }
        Wait-Port4173Free
    } else {
        "Build failed (exit $buildExit) - skipping Playwright suites" | Set-Content -Path (Join-Path $script:OutDir "frontend_playwright_skipped.txt") -Encoding UTF8
        $results += [pscustomobject]@{ Name = "frontend_release_a11y"; Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
        $results += [pscustomobject]@{ Name = "frontend_nav";           Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
        $results += [pscustomobject]@{ Name = "frontend_release_routes"; Passed = $false; ExitCode = 1; LogFile = ""; LogRel = "" }
    }
}

if (Test-Path (Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py")) {
    $results += Invoke-Capture -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -LogFile "backend_reporting_exports_gate.txt" -Exe "python" -CmdParts @("-m", "pytest", "backend/tests/test_reporting_exports_gate.py", "-q")
}

if (Test-Path (Join-Path $repoRoot "backend\manage.py")) {
    $results += Invoke-Capture -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -LogFile "backend_django_check.txt" -Exe "python" -CmdParts @("manage.py", "check")
}

$releaseRoot = Join-Path $repoRoot "audit-artifacts\release-certification"
$releaseInfo = [ordered]@{
    Directory = $null
    SummaryFile = $null
    CsvFile = $null
    FinalStatus = "UNKNOWN"
    FinalStatusPromoted = $false
    Green = $null
    Amber = $null
    Red = $null
    PerformanceLane = $null
}

if (Test-Path $releaseRoot) {
    $latestRelease = Get-ChildItem -Path $releaseRoot -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "00_release_gate_results.csv") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -ne $latestRelease) {
        $releaseInfo.Directory = $latestRelease.FullName
        $releaseInfo.CsvFile = Join-Path $latestRelease.FullName "00_release_gate_results.csv"
        $releaseInfo.SummaryFile = Join-Path $latestRelease.FullName "SUMMARY.md"

        $csv = Import-Csv -Path $releaseInfo.CsvFile
        $statusColumn = @("Status", "status") | Where-Object { $csv[0].PSObject.Properties.Name -contains $_ } | Select-Object -First 1
        if ($null -ne $statusColumn) {
            $releaseInfo.Green = @($csv | Where-Object { $_.$statusColumn -match '^GREEN$' }).Count
            $releaseInfo.Amber = @($csv | Where-Object { $_.$statusColumn -match '^AMBER$' }).Count
            $releaseInfo.Red = @($csv | Where-Object { $_.$statusColumn -match '^RED$' }).Count
        }

        if (Test-Path $releaseInfo.SummaryFile) {
            $summaryText = Get-Content -Path $releaseInfo.SummaryFile -Raw
            # Accept both "FINAL: PASS" and "FINAL = PASS" summary styles.
            $finalMatch = [regex]::Match($summaryText, 'FINAL\s*[:=]\s*(PASS|FAIL)', 'IgnoreCase')
            if ($finalMatch.Success) {
                $releaseInfo.FinalStatus = $finalMatch.Groups[1].Value.ToUpperInvariant()
            }

            $perfBlock = [regex]::Match($summaryText, 'Performance/Resilience.*?(GREEN|AMBER|RED)', 'IgnoreCase,Singleline')
            if ($perfBlock.Success) {
                $releaseInfo.PerformanceLane = $perfBlock.Groups[1].Value.ToUpperInvariant()
            }
        }
    }
}

$mainlineInfo = [ordered]@{
    CheckCsv = $null
    BaselinePassed = $null
    DeepPassed = $null
}

$mainlineCheckCsv = Join-Path $repoRoot "audit-artifacts\mainline-reconcile\latest\30_check_results.csv"
if (Test-Path $mainlineCheckCsv) {
    $mainlineInfo.CheckCsv = $mainlineCheckCsv
    try {
        $mainlineRows = @(Import-Csv -Path $mainlineCheckCsv)
        $baselineRow = $mainlineRows | Where-Object { $_.Name -eq "95_live_scorecard_audit_baseline" } | Select-Object -First 1
        $deepRow = $mainlineRows | Where-Object { $_.Name -eq "95_live_scorecard_audit_deep" } | Select-Object -First 1

        if ($null -ne $baselineRow) {
            $mainlineInfo.BaselinePassed = ([string]$baselineRow.Passed).Trim().ToLowerInvariant() -eq "true"
        }
        if ($null -ne $deepRow) {
            $mainlineInfo.DeepPassed = ([string]$deepRow.Passed).Trim().ToLowerInvariant() -eq "true"
        }
    } catch {
        $mainlineInfo.BaselinePassed = $null
        $mainlineInfo.DeepPassed = $null
    }
}

$pr733Info = [ordered]@{
    Number = 733
    State = $null
    MergedAt = $null
    MergeCommit = $null
    Merged = $null
    RequiredChecksGreen = $null
    FailingChecks = $null
    TotalChecks = $null
}

if ($ghAvailable) {
    try {
        $pr733Json = gh pr view 733 --json number,state,mergedAt,mergeCommit,statusCheckRollup
        if (-not [string]::IsNullOrWhiteSpace($pr733Json)) {
            $pr733 = $pr733Json | ConvertFrom-Json
            $pr733Info.State = [string]$pr733.state
            $pr733Info.MergedAt = [string]$pr733.mergedAt
            if ($null -ne $pr733.mergeCommit) {
                $pr733Info.MergeCommit = [string]$pr733.mergeCommit.oid
            }
            $pr733Info.Merged = ($pr733Info.State -eq "MERGED") -and (-not [string]::IsNullOrWhiteSpace($pr733Info.MergedAt))

            $rollup = @($pr733.statusCheckRollup)
            $pr733Info.TotalChecks = $rollup.Count
            if ($rollup.Count -gt 0) {
                $badChecks = @(
                    $rollup | Where-Object {
                        $status = ([string]$_.status).ToUpperInvariant()
                        $conclusion = ([string]$_.conclusion).ToUpperInvariant()
                        if ($status -ne "COMPLETED") { return $true }
                        return $conclusion -notin @("SUCCESS", "NEUTRAL", "SKIPPED")
                    }
                )
                $pr733Info.FailingChecks = $badChecks.Count
                $pr733Info.RequiredChecksGreen = ($badChecks.Count -eq 0)
            }
        }
    } catch {
        $pr733Info.Merged = $null
        $pr733Info.RequiredChecksGreen = $null
    }
}

function Find-Result {
    param([string]$Name)
    return $results | Where-Object { $_.Name -eq $Name } | Select-Object -First 1
}

$failedExecutedChecksCount = @($results | Where-Object { -not $_.Passed }).Count
$junkDirtyCount = @(
    $repoState.StatusLines | Where-Object {
        $_ -match '(^|/)(_tmp_|tmp_|temp_|backup_|scratch_)' -or
        $_ -match '(^|/).*\.tmp$'
    }
).Count

$noImmediateBlockers = ($repoState.DirtyCount -eq 0) -and ($failedExecutedChecksCount -eq 0) -and ($releaseInfo.PerformanceLane -eq "GREEN")
$releasePerfectGreen = ($releaseInfo.Green -eq 6) -and ($releaseInfo.Amber -eq 0) -and ($releaseInfo.Red -eq 0)

if (($releaseInfo.FinalStatus -eq "UNKNOWN") -and $releasePerfectGreen -and $noImmediateBlockers) {
    $releaseInfo.FinalStatus = "PASS"
    $releaseInfo.FinalStatusPromoted = $true
}

$frontendScore = 10.0
$frontendNotes = @()

$frontendChecks = @(@(
    Find-Result "frontend_check_shell_contracts",
    Find-Result "frontend_unit",
    Find-Result "frontend_release_a11y",
    Find-Result "frontend_nav",
    Find-Result "frontend_release_routes"
) | Where-Object { $null -ne $_ })

foreach ($r in $frontendChecks) {
    if (-not $r.Passed) {
        switch ($r.Name) {
            "frontend_check_shell_contracts" { $frontendScore -= 2.0; $frontendNotes = Add-Note $frontendNotes "shell contracts failed" }
            "frontend_unit"                  { $frontendScore -= 2.0; $frontendNotes = Add-Note $frontendNotes "unit tests failed" }
            "frontend_release_a11y"         { $frontendScore -= 2.0; $frontendNotes = Add-Note $frontendNotes "release a11y failed" }
            "frontend_nav"                  { $frontendScore -= 1.5; $frontendNotes = Add-Note $frontendNotes "nav proof failed" }
            "frontend_release_routes"       { $frontendScore -= 1.5; $frontendNotes = Add-Note $frontendNotes "release routes failed" }
        }
    }
}

if ($Deep) {
    foreach ($n in @("frontend_matrix_1", "frontend_matrix_2", "frontend_matrix_3")) {
        $r = Find-Result $n
        if ($null -ne $r -and -not $r.Passed) {
            $frontendScore -= 0.8
            $frontendNotes = Add-Note $frontendNotes "$n failed"
        }
    }
}

if ($frontendChecks.Count -gt 0 -and @($frontendChecks | Where-Object { $_.Passed }).Count -eq $frontendChecks.Count) {
    $frontendNotes = Add-Note $frontendNotes "all high-signal frontend checks passed"
}
$frontendScore = Get-Score $frontendScore

$backendScore = 10.0
$backendNotes = @()
$backendGate = Find-Result "backend_reporting_exports_gate"
$backendDjango = Find-Result "backend_django_check"

if ($null -ne $backendGate) {
    if ($backendGate.Passed) {
        $backendNotes = Add-Note $backendNotes "reporting/export/transcript gate passed"
    } else {
        $backendScore -= 3.0
        $backendNotes = Add-Note $backendNotes "reporting/export/transcript gate failed"
    }
}
if ($null -ne $backendDjango) {
    if ($backendDjango.Passed) {
        $backendNotes = Add-Note $backendNotes "django check passed"
    } else {
        $backendScore -= 1.5
        $backendNotes = Add-Note $backendNotes "django check failed"
    }
}
$backendScore = Get-Score $backendScore

$releaseScore = 6.0
$releaseNotes = @()
if ($null -ne $releaseInfo.Green) {
    if ($releasePerfectGreen -and ($releaseInfo.PerformanceLane -eq "GREEN") -and $noImmediateBlockers) {
        $releaseScore = 10.0
        $releaseNotes = Add-Note $releaseNotes "fully green release lanes with no blockers"
    } elseif (($releaseInfo.Red -eq 0) -and ($releaseInfo.Amber -eq 0) -and ($releaseInfo.FinalStatus -eq "PASS")) {
        $releaseScore = 9.5
    } elseif (($releaseInfo.Red -eq 0) -and ($releaseInfo.Amber -eq 1)) {
        $releaseScore = 8.8
    } elseif (($releaseInfo.Red -eq 0) -and ($releaseInfo.Amber -eq 2)) {
        $releaseScore = 7.8
    } else {
        $releaseScore = 5.5 - ($releaseInfo.Red * 1.0) - ($releaseInfo.Amber * 0.3)
    }

    $releaseNotes = Add-Note $releaseNotes "GREEN $($releaseInfo.Green) / AMBER $($releaseInfo.Amber) / RED $($releaseInfo.Red)"
    if ($releaseInfo.FinalStatus -ne "UNKNOWN") {
        $releaseNotes = Add-Note $releaseNotes "final $($releaseInfo.FinalStatus)"
    }
    if ($releaseInfo.FinalStatusPromoted) {
        $releaseNotes = Add-Note $releaseNotes "final status promoted from UNKNOWN based on green evidence"
    }
    if ($null -ne $releaseInfo.PerformanceLane) {
        $releaseNotes = Add-Note $releaseNotes "performance lane $($releaseInfo.PerformanceLane)"
    }
}
$releaseScore = Get-Score $releaseScore

$repoScore = 10.0
$repoNotes = @()
if ($repoState.DirtyCount -gt 0) {
    $repoScore -= [math]::Min(2.5, ($repoState.DirtyCount * 0.15))
    $repoNotes = Add-Note $repoNotes "$($repoState.DirtyCount) dirty worktree entries"
} else {
    $repoNotes = Add-Note $repoNotes "clean worktree"
}
if ($junkDirtyCount -gt 0) {
    $repoScore -= [math]::Min(1.5, ($junkDirtyCount * 0.25))
    $repoNotes = Add-Note $repoNotes "$junkDirtyCount dirty temp/junk entries"
} else {
    $repoNotes = Add-Note $repoNotes "no dirty temp/junk entries"
}
if ($null -ne $github.OpenPRCount) {
    if ($github.OpenPRCount -gt 1) {
        $repoScore -= [math]::Min(1.5, ($github.OpenPRCount - 1) * 0.3)
    }
    $repoNotes = Add-Note $repoNotes "$($github.OpenPRCount) open PRs"
}
if ($null -ne $github.OpenIssueCount) {
    $repoNotes = Add-Note $repoNotes "$($github.OpenIssueCount) open issues"
}
if ($pr733Info.Merged -eq $false) {
    $repoScore -= 1.0
    $repoNotes = Add-Note $repoNotes "PR #733 not merged"
} elseif ($pr733Info.Merged -eq $true) {
    $repoNotes = Add-Note $repoNotes "PR #733 merged"
}
if ($pr733Info.RequiredChecksGreen -eq $false) {
    $repoScore -= 1.0
    $repoNotes = Add-Note $repoNotes "PR #733 required checks not green"
} elseif ($pr733Info.RequiredChecksGreen -eq $true) {
    $repoNotes = Add-Note $repoNotes "PR #733 required checks green"
}
$repoAllGreen = ($repoState.DirtyCount -eq 0) -and ($junkDirtyCount -eq 0) -and $noImmediateBlockers -and ($pr733Info.Merged -eq $true) -and ($pr733Info.RequiredChecksGreen -eq $true)
if ($repoAllGreen) {
    $repoScore = 10.0
    $repoNotes = Add-Note $repoNotes "fully green merge posture"
}
$repoScore = Get-Score $repoScore

$postMergeScore = 6.0
$postMergeNotes = @()
$postMergeAllGreen = ($pr733Info.Merged -eq $true) -and ($pr733Info.RequiredChecksGreen -eq $true) -and ($mainlineInfo.BaselinePassed -eq $true) -and ($mainlineInfo.DeepPassed -eq $true) -and ($repoState.DirtyCount -eq 0)

if ($pr733Info.Merged -eq $true) {
    $postMergeNotes = Add-Note $postMergeNotes "PR #733 merged"
} else {
    $postMergeNotes = Add-Note $postMergeNotes "PR #733 not merged"
}
if ($pr733Info.RequiredChecksGreen -eq $true) {
    $postMergeNotes = Add-Note $postMergeNotes "required checks green"
} else {
    $postMergeNotes = Add-Note $postMergeNotes "required checks not green"
}
if ($mainlineInfo.BaselinePassed -eq $true) {
    $postMergeNotes = Add-Note $postMergeNotes "mainline baseline audit passed"
} else {
    $postMergeNotes = Add-Note $postMergeNotes "mainline baseline audit not passing"
}
if ($mainlineInfo.DeepPassed -eq $true) {
    $postMergeNotes = Add-Note $postMergeNotes "mainline deep audit passed"
} else {
    $postMergeNotes = Add-Note $postMergeNotes "mainline deep audit not passing"
}
if ($repoState.DirtyCount -eq 0) {
    $postMergeNotes = Add-Note $postMergeNotes "main branch/local state clean"
} else {
    $postMergeNotes = Add-Note $postMergeNotes "main branch/local state dirty"
}

if ($postMergeAllGreen) {
    $postMergeScore = 10.0
} else {
    if ($pr733Info.Merged -ne $true) { $postMergeScore -= 1.5 }
    if ($pr733Info.RequiredChecksGreen -ne $true) { $postMergeScore -= 1.5 }
    if ($mainlineInfo.BaselinePassed -ne $true) { $postMergeScore -= 0.5 }
    if ($mainlineInfo.DeepPassed -ne $true) { $postMergeScore -= 0.5 }
    if ($repoState.DirtyCount -gt 0) { $postMergeScore -= 1.0 }
}
$postMergeScore = Get-Score $postMergeScore

$governanceScore = 7.5
$governanceNotes = @()
foreach ($f in @(".github\CODEOWNERS", "SECURITY.md", "CONTRIBUTING.md", "README.md")) {
    if (Test-Path (Join-Path $repoRoot $f)) {
        $governanceScore += 0.5
        $governanceNotes = Add-Note $governanceNotes "$f present"
    } else {
        $governanceNotes = Add-Note $governanceNotes "$f missing"
    }
}
$governanceScore = Get-Score $governanceScore

$overallScore = Get-Score (
    ($releaseScore * 0.25) +
    ($frontendScore * 0.20) +
    ($backendScore * 0.20) +
    ($repoScore * 0.15) +
    ($governanceScore * 0.10) +
    ($postMergeScore * 0.10)
)

$areas = @(
    [pscustomobject]@{
        Area   = "Release certification"
        Score  = $releaseScore
        Status = Get-StatusFromScore $releaseScore
        Note   = ($releaseNotes -join "; ")
    },
    [pscustomobject]@{
        Area   = "Frontend dashboard and wizard integrity"
        Score  = $frontendScore
        Status = Get-StatusFromScore $frontendScore
        Note   = ($frontendNotes -join "; ")
    },
    [pscustomobject]@{
        Area   = "Backend reporting exports transcripts"
        Score  = $backendScore
        Status = Get-StatusFromScore $backendScore
        Note   = ($backendNotes -join "; ")
    },
    [pscustomobject]@{
        Area   = "Repo hygiene and merge posture"
        Score  = $repoScore
        Status = Get-StatusFromScore $repoScore
        Note   = ($repoNotes -join "; ")
    },
    [pscustomobject]@{
        Area   = "Post-merge mainline verification"
        Score  = $postMergeScore
        Status = Get-StatusFromScore $postMergeScore
        Note   = ($postMergeNotes -join "; ")
    },
    [pscustomobject]@{
        Area   = "Governance and controls"
        Score  = $governanceScore
        Status = Get-StatusFromScore $governanceScore
        Note   = ($governanceNotes -join "; ")
    }
)

$topBlockers = @()
if ($releaseInfo.PerformanceLane -eq "AMBER") {
    $topBlockers += "Performance/Resilience lane still AMBER"
}
if ($repoState.DirtyCount -gt 0) {
    $topBlockers += "Worktree is dirty"
}
foreach ($r in $results | Where-Object { -not $_.Passed }) {
    $topBlockers += "$($r.Name) failed"
}
if ($pr733Info.Merged -eq $false) {
    $topBlockers += "PR #733 is not merged"
}
if ($pr733Info.RequiredChecksGreen -eq $false) {
    $topBlockers += "PR #733 required checks are not all green"
}
if ($mainlineInfo.BaselinePassed -eq $false) {
    $topBlockers += "mainline baseline audit is not passing"
}
if ($mainlineInfo.DeepPassed -eq $false) {
    $topBlockers += "mainline deep audit is not passing"
}
if ($junkDirtyCount -gt 0) {
    $topBlockers += "dirty temp/junk entries detected"
}
if ($topBlockers.Count -eq 0) {
    $topBlockers += "No immediate blockers detected in the executed audit scope"
}

$payload = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo = [ordered]@{
        root = $repoRoot
        branch = $repoState.Branch
        head = $repoState.Head
        commit_count = $repoState.CommitCount
        dirty_count = $repoState.DirtyCount
        temp_like_tracked_files = $tmpTrackedCount
        dirty_temp_like_entries = $junkDirtyCount
    }
    github = $github
    pr733 = $pr733Info
    mainline = $mainlineInfo
    release = $releaseInfo
    checks = $results
    scorecard = [ordered]@{
        overall_score = $overallScore
        areas = $areas
        top_blockers = $topBlockers
    }
}

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Crown2026 Live Scorecard Audit")
$md.Add("")
$md.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$md.Add("- Repo: $repoRoot")
$md.Add("- Branch: $($repoState.Branch)")
$md.Add("- Head: $($repoState.Head)")
$md.Add("- Commits: $($repoState.CommitCount)")
$md.Add("- Dirty entries: $($repoState.DirtyCount)")
if ($github.RepoSlug) { $md.Add("- GitHub repo: $($github.RepoSlug)") }
if ($null -ne $github.OpenPRCount) { $md.Add("- Open PRs: $($github.OpenPRCount)") }
if ($null -ne $github.OpenIssueCount) { $md.Add("- Open issues: $($github.OpenIssueCount)") }
$md.Add("")
$md.Add("## Overall")
$md.Add("")
$md.Add("- Overall score: **$overallScore / 10**")
$md.Add("")
$md.Add("## Scorecard")
$md.Add("")
$md.Add("| Area | Score | Status | Note |")
$md.Add("|---|---:|---|---|")
foreach ($a in $areas) {
    $note = ($a.Note -replace '\|', '/')
    $md.Add("| $($a.Area) | $($a.Score) | $($a.Status) | $note |")
}
$md.Add("")
$md.Add("## Top blockers")
$md.Add("")
foreach ($b in $topBlockers) {
    $md.Add("- $b")
}
$md.Add("")
$md.Add("## Executed checks")
$md.Add("")
$md.Add("| Check | Passed | Exit | Log |")
$md.Add("|---|---|---:|---|")
foreach ($r in $results) {
    $md.Add("| $($r.Name) | $($r.Passed) | $($r.ExitCode) | $($r.LogRel) |")
}
$md.Add("")
$md.Add("## Release artifact source")
$md.Add("")
$md.Add("- Release dir: $($releaseInfo.Directory)")
$md.Add("- Release summary: $($releaseInfo.SummaryFile)")
$md.Add("- Release csv: $($releaseInfo.CsvFile)")
$md.Add("")
$md.Add("## Post-merge verification source")
$md.Add("")
$md.Add("- PR #733 merged: $($pr733Info.Merged)")
$md.Add("- PR #733 required checks green: $($pr733Info.RequiredChecksGreen)")
$md.Add("- Mainline check csv: $($mainlineInfo.CheckCsv)")
$md.Add("- Mainline baseline passed: $($mainlineInfo.BaselinePassed)")
$md.Add("- Mainline deep passed: $($mainlineInfo.DeepPassed)")

$scorecardMd = Join-Path $script:OutDir "SCORECARD.md"
$scorecardJson = Join-Path $script:OutDir "SCORECARD.json"
$runSummary = Join-Path $script:OutDir "RUN_SUMMARY.txt"

$md | Set-Content -Path $scorecardMd -Encoding UTF8
($payload | ConvertTo-Json -Depth 8) | Set-Content -Path $scorecardJson -Encoding UTF8

@(
    "OVERALL SCORE: $overallScore / 10"
    "BRANCH: $($repoState.Branch)"
    "HEAD: $($repoState.Head)"
    "DIRTY COUNT: $($repoState.DirtyCount)"
    "OPEN PRs: $($github.OpenPRCount)"
    "OPEN ISSUES: $($github.OpenIssueCount)"
    "RELEASE: GREEN=$($releaseInfo.Green) AMBER=$($releaseInfo.Amber) RED=$($releaseInfo.Red) FINAL=$($releaseInfo.FinalStatus) PERF=$($releaseInfo.PerformanceLane)"
    "POST-MERGE: PR733_MERGED=$($pr733Info.Merged) REQUIRED_CHECKS_GREEN=$($pr733Info.RequiredChecksGreen) MAINLINE_BASELINE=$($mainlineInfo.BaselinePassed) MAINLINE_DEEP=$($mainlineInfo.DeepPassed)"
    ""
    "TOP BLOCKERS:"
) + $topBlockers | Set-Content -Path $runSummary -Encoding UTF8

Copy-Item -Path (Join-Path $script:OutDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SCORECARD: $scorecardMd"
Write-Host "JSON:      $scorecardJson"
Write-Host "SUMMARY:   $runSummary"
