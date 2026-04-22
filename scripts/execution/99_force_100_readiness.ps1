param(
    [switch]$Push,
    [int]$PollSeconds = 20,
    [int]$MaxPollMinutes = 25
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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
    param([string]$Path, $Rows)
    $arr = @($Rows | Where-Object { $null -ne $_ })
    if ($arr.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $arr | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
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

function Parse-RunSummary {
    param([string]$Path)

    $out = [ordered]@{
        OverallScore = ""
        DirtyCount = ""
        ReleaseLine = ""
        TopBlockers = @()
    }

    if (-not (Test-Path $Path)) {
        return [pscustomobject]$out
    }

    $text = Get-Content -Path $Path -Raw

    $m = [regex]::Match($text, 'OVERALL SCORE:\s*([0-9.]+)\s*/\s*10', 'IgnoreCase')
    if ($m.Success) { $out.OverallScore = $m.Groups[1].Value + " / 10" }

    $m = [regex]::Match($text, 'DIRTY COUNT:\s*([0-9]+)', 'IgnoreCase')
    if ($m.Success) { $out.DirtyCount = $m.Groups[1].Value }

    $m = [regex]::Match($text, 'RELEASE:\s*GREEN=.*', 'IgnoreCase')
    if ($m.Success) { $out.ReleaseLine = $m.Value.Trim() }

    $lines = @(Get-Content -Path $Path)
    $start = $lines.IndexOf("TOP BLOCKERS:")
    if ($start -ge 0) {
        for ($i = $start + 1; $i -lt $lines.Count; $i++) {
            $line = $lines[$i].Trim()
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $out.TopBlockers += $line
        }
    }

    return [pscustomobject]$out
}

function Ensure-InfoExcludePattern {
    param([string]$RepoRoot, [string]$Pattern)
    $excludePath = Join-Path $RepoRoot ".git\info\exclude"
    if (-not (Test-Path $excludePath)) {
        New-Dir (Split-Path -Parent $excludePath)
        "" | Set-Content -Path $excludePath -Encoding UTF8
    }
    $content = Get-Content $excludePath -ErrorAction SilentlyContinue
    if ($content -notcontains $Pattern) {
        Add-Content -Path $excludePath -Value $Pattern -Encoding UTF8
    }
}

function Test-GitTracked {
    param([string]$Path)
    & git ls-files --error-unmatch -- "$Path" *> $null
    return ($LASTEXITCODE -eq 0)
}

function Remove-TrackedOrUntracked {
    param([string]$RelativePath)

    if (-not (Test-Path $RelativePath)) { return }

    if (Test-GitTracked $RelativePath) {
        & git rm -r --cached --ignore-unmatch -- "$RelativePath" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "git rm --cached failed for $RelativePath" }
        Remove-Item -Recurse -Force -LiteralPath $RelativePath -ErrorAction Stop
    } else {
        Remove-Item -Recurse -Force -LiteralPath $RelativePath -ErrorAction Stop
    }
}

Require-Tool git
Require-Tool gh
Require-Tool powershell

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne "main") {
    Write-Warning "Running from non-main branch: $currentBranch"
}

Ensure-InfoExcludePattern -RepoRoot $repoRoot -Pattern ".crown-audit/"
Ensure-InfoExcludePattern -RepoRoot $repoRoot -Pattern "docs/investor-audit/public-10of10/"
Ensure-InfoExcludePattern -RepoRoot $repoRoot -Pattern "docs/investor-audit/archives/"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot ".crown-audit\100-readiness\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\100-readiness\latest"
$archiveRoot = Join-Path $repoRoot "docs\investor-audit\archives\$timestamp"

New-Dir $script:OutDir
New-Dir $latestDir
New-Dir $archiveRoot

$cleanupActions = @()

$rootDirsToArchive = @(
    "artifacts\proof"
)

$rootFilePatterns = @(
    ".editorconfig.bak*",
    ".gitignore.bak*",
    "_tmp_*.yaml",
    "*.orig",
    "*.rej",
    "*.tmp"
)

foreach ($dir in $rootDirsToArchive) {
    if (Test-Path $dir) {
        $dest = Join-Path $archiveRoot ($dir -replace '[:\\\/]+','_')
        New-Dir (Split-Path -Parent $dest)

        if (Test-GitTracked $dir) {
            & git mv -- "$dir" "$dest"
            if ($LASTEXITCODE -ne 0) { throw "git mv failed for $dir" }
            $cleanupActions += [pscustomobject]@{
                Path = $dir
                Action = "git_move_to_archive"
                Destination = $dest
                Tracked = $true
            }
        } else {
            Move-Item -LiteralPath (Join-Path $repoRoot $dir) -Destination $dest -Force
            $cleanupActions += [pscustomobject]@{
                Path = $dir
                Action = "move_to_archive"
                Destination = $dest
                Tracked = $false
            }
        }
    }
}

foreach ($pattern in $rootFilePatterns) {
    $matches = @(Get-ChildItem -Path $repoRoot -File -Force -Filter $pattern -ErrorAction SilentlyContinue)
    foreach ($m in $matches) {
        $relative = $m.Name
        $dest = Join-Path $archiveRoot ("root-files\" + $m.Name)
        New-Dir (Split-Path -Parent $dest)

        if (Test-GitTracked $relative) {
            & git mv -- "$relative" "$dest"
            if ($LASTEXITCODE -ne 0) { throw "git mv failed for $relative" }
            $cleanupActions += [pscustomobject]@{
                Path = $relative
                Action = "git_move_to_archive"
                Destination = $dest
                Tracked = $true
            }
        } else {
            Move-Item -LiteralPath $m.FullName -Destination $dest -Force
            $cleanupActions += [pscustomobject]@{
                Path = $relative
                Action = "move_to_archive"
                Destination = $dest
                Tracked = $false
            }
        }
    }
}

if (Test-Path '$($latest.Name)') {
    Remove-TrackedOrUntracked -RelativePath '$($latest.Name)'
    $cleanupActions += [pscustomobject]@{
        Path = '$($latest.Name)'
        Action = "remove_literal_latest_name_path"
        Destination = ""
        Tracked = $false
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "10_root_cleanup_actions.csv") -Rows @($cleanupActions)

$changesBeforeCommit = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($changesBeforeCommit.Count -gt 0) {
    git add -A | Out-Null
    git commit -m "Polish public repo root for investor-facing 100 percent readiness" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Commit failed." }
    if ($Push) {
        git push | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Push failed." }
    }
}

$runs = Invoke-GhJson -GhArgs @(
    "run","list",
    "--branch","main",
    "--limit","80",
    "--json","databaseId,workflowName,status,conclusion,createdAt,url,displayTitle,event"
)

$failedBefore = @(
    $runs |
    Where-Object {
        $_.status -eq "completed" -and $_.conclusion -in @("failure","cancelled","timed_out","action_required","startup_failure")
    } |
    Group-Object workflowName |
    ForEach-Object { $_.Group | Sort-Object createdAt -Descending | Select-Object -First 1 }
)

Write-CsvSafe -Path (Join-Path $script:OutDir "20_failed_runs_before.csv") -Rows $failedBefore

$failedAfter = @()

foreach ($run in $failedBefore) {
    & gh run rerun $run.databaseId | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $failedAfter += [pscustomobject]@{
            workflowName = $run.workflowName
            databaseId = $run.databaseId
            status = "rerun_failed"
            conclusion = ""
            url = $run.url
        }
        continue
    }

    $deadline = (Get-Date).AddMinutes($MaxPollMinutes)
    $final = $null

    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds $PollSeconds
        $view = Invoke-GhJson -GhArgs @("run","view",$run.databaseId.ToString(),"--json","databaseId,workflowName,status,conclusion,url")
        if ($view.status -eq "completed") {
            $final = $view
            break
        }
    }

    if ($null -eq $final) {
        $final = Invoke-GhJson -GhArgs @("run","view",$run.databaseId.ToString(),"--json","databaseId,workflowName,status,conclusion,url")
    }

    $failedAfter += [pscustomobject]@{
        workflowName = $final.workflowName
        databaseId = $final.databaseId
        status = $final.status
        conclusion = $final.conclusion
        url = $final.url
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "21_failed_runs_after.csv") -Rows $failedAfter

$checks = @()

$scoreScript = Join-Path $repoRoot "scripts\execution\95_live_scorecard_audit.ps1"
if (Test-Path $scoreScript) {
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_baseline" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",$scoreScript)
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_deep" -WorkingDirectory $repoRoot -Exe "powershell" -CmdArgs @("-ExecutionPolicy","Bypass","-File",$scoreScript,"-Deep")
}

$frontendDir = Join-Path $repoRoot "frontend\dashboards"
if (Test-Path (Join-Path $frontendDir "package.json")) {
    $checks += Invoke-LoggedCommand -Name "frontend_shell_contracts" -WorkingDirectory $frontendDir -Exe "npm.cmd" -CmdArgs @("run","check:shell-contracts")
    $checks += Invoke-LoggedCommand -Name "frontend_unit" -WorkingDirectory $frontendDir -Exe "npm.cmd" -CmdArgs @("run","test:unit")
    $checks += Invoke-LoggedCommand -Name "frontend_release_a11y" -WorkingDirectory $frontendDir -Exe "npm.cmd" -CmdArgs @("run","test:release:a11y") -Env @{ CI = "1" }
    $checks += Invoke-LoggedCommand -Name "frontend_nav" -WorkingDirectory $frontendDir -Exe "npm.cmd" -CmdArgs @("run","ui:proof:nav") -Env @{ CI = "1" }
    $checks += Invoke-LoggedCommand -Name "frontend_release_routes" -WorkingDirectory $frontendDir -Exe "npm.cmd" -CmdArgs @("run","test:release:routes") -Env @{ CI = "1" }
}

$backendGate = Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py"
if (Test-Path $backendGate) {
    $checks += Invoke-LoggedCommand -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Exe "python" -CmdArgs @("-m","pytest","backend/tests/test_reporting_exports_gate.py","-q")
}

$backendManage = Join-Path $repoRoot "backend\manage.py"
if (Test-Path $backendManage) {
    $checks += Invoke-LoggedCommand -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Exe "python" -CmdArgs @("manage.py","check")
}

Write-CsvSafe -Path (Join-Path $script:OutDir "30_local_checks.csv") -Rows $checks

if ($Push) {
    $dirtyMid = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($dirtyMid.Count -gt 0) {
        git add -A | Out-Null
        git commit -m "Refresh investor-facing readiness evidence" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Evidence commit failed." }
        git push | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Evidence push failed." }
    }
}

$repoSlug = (& gh repo view --json nameWithOwner --jq .nameWithOwner).Trim()
$openPRs = [int](& gh pr list --state open --limit 100 --json number --jq "length")
$openIssues = [int](& gh issue list --state open --limit 200 --json number --jq "length")
$dirtyCount = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
$runSummary = Parse-RunSummary -Path (Join-Path $repoRoot "audit-artifacts\live-scorecard\latest\RUN_SUMMARY.txt")

$failedAfterCount = @($failedAfter | Where-Object { $_.status -ne "completed" -or $_.conclusion -ne "success" }).Count
$localFailedCount = @($checks | Where-Object { -not $_.Passed }).Count

$pass =
    ($failedAfterCount -eq 0) -and
    ($localFailedCount -eq 0) -and
    ($openPRs -eq 0) -and
    ($openIssues -eq 0) -and
    ($dirtyCount -eq 0) -and
    ($runSummary.OverallScore -eq "10 / 10") -and
    ($runSummary.ReleaseLine -match 'FINAL=PASS') -and
    (@($runSummary.TopBlockers).Count -eq 0 -or (@($runSummary.TopBlockers).Count -eq 1 -and $runSummary.TopBlockers[0] -match 'none|No immediate blockers'))

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add("# 100 Percent Readiness Summary")
$summaryLines.Add("")
$summaryLines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summaryLines.Add("- Repo: $repoSlug")
$summaryLines.Add("- Open PRs: $openPRs")
$summaryLines.Add("- Open issues: $openIssues")
$summaryLines.Add("- Dirty count: $dirtyCount")
$summaryLines.Add("- Root cleanup actions: $($cleanupActions.Count)")
$summaryLines.Add("- Failed main workflows before rerun: $($failedBefore.Count)")
$summaryLines.Add("- Failed main workflows after rerun: $failedAfterCount")
$summaryLines.Add("- Local verification failures: $localFailedCount")
$summaryLines.Add("- Local scorecard overall: $($runSummary.OverallScore)")
$summaryLines.Add("- Local release line: $($runSummary.ReleaseLine)")
$summaryLines.Add("")
$summaryLines.Add("## Result")
$summaryLines.Add("")
if ($pass) {
    $summaryLines.Add("PASS")
} else {
    $summaryLines.Add("REVIEW REQUIRED")
}

Write-Utf8 (Join-Path $script:OutDir "00_SUMMARY.md") $summaryLines

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo = $repoSlug
    open_prs = $openPRs
    open_issues = $openIssues
    dirty_count = $dirtyCount
    root_cleanup_actions = $cleanupActions
    failed_before = $failedBefore
    failed_after = $failedAfter
    local_checks = $checks
    local_scorecard = $runSummary
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
