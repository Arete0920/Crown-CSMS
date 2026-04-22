param(
    [int]$TargetPR = 733,
    [switch]$RerunFailed,
    [switch]$PrepareMerge,
    [switch]$AutoMergeIfGreen,
    [int]$PollSeconds = 20,
    [int]$MaxPollMinutes = 25
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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

function Require-Tool {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required tool missing: $Name"
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

    try {
        return ($raw | ConvertFrom-Json)
    } catch {
        throw "gh JSON parse failed for args: gh $($GhArgs -join ' ')"
    }
}

function Invoke-LoggedCommand {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Exe,
        [string[]]$Args = @(),
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
            "CMD: $Exe $($Args -join ' ')"
            ""
        )
        $global:LASTEXITCODE = 0
        & $Exe @Args *>&1 | Tee-Object -FilePath $logPath -Append | Out-Null
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        return [pscustomobject]@{
            Name     = $Name
            Passed   = ($exitCode -eq 0)
            ExitCode = $exitCode
            Log      = $logPath
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
        Path = $Path
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

Require-Tool git
Require-Tool gh
Require-Tool powershell

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$dirty = @(git status --porcelain=v1)
if (@($dirty | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
    throw "Worktree must be clean before mainline reconciliation."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:OutDir = Join-Path $repoRoot "audit-artifacts\mainline-reconcile\$timestamp"
$latestDir = Join-Path $repoRoot "audit-artifacts\mainline-reconcile\latest"

New-Dir $script:OutDir
New-Dir $latestDir

$repoSlug = (& gh repo view --json nameWithOwner --jq .nameWithOwner).Trim()
$currentBranch = (git branch --show-current).Trim()
$currentHead = (git rev-parse HEAD).Trim()

git fetch origin main | Out-Null
$mainHead = (git rev-parse origin/main).Trim()

$pr = Invoke-GhJson -GhArgs @("pr","view",$TargetPR.ToString(),"--json","number,title,state,isDraft,mergeStateStatus,headRefName,baseRefName,url,reviewDecision")
Write-JsonFile -Path (Join-Path $script:OutDir "10_pr_status.json") -Object $pr

$runList = Invoke-GhJson -GhArgs @(
    "run","list",
    "--branch","main",
    "--limit","60",
    "--json","databaseId,workflowName,status,conclusion,createdAt,displayTitle,url,headSha,event"
)

$failedBefore = @(
    $runList | Where-Object {
        $_.status -eq "completed" -and $_.conclusion -in @("failure","cancelled","timed_out","action_required","startup_failure")
    } | Sort-Object workflowName, createdAt -Descending
)

$latestFailedByWorkflow = @(
    $failedBefore |
    Group-Object workflowName |
    ForEach-Object { $_.Group | Sort-Object createdAt -Descending | Select-Object -First 1 }
)

Write-CsvSafe -Path (Join-Path $script:OutDir "20_failed_runs_before.csv") -Rows $latestFailedByWorkflow

$rerunResults = @()

if ($RerunFailed) {
    foreach ($run in $latestFailedByWorkflow) {
        & gh run rerun $run.databaseId | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $rerunResults += [pscustomobject]@{
                workflowName = $run.workflowName
                databaseId = $run.databaseId
                rerunRequested = $false
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

        $rerunResults += [pscustomobject]@{
            workflowName = $final.workflowName
            databaseId = $final.databaseId
            rerunRequested = $true
            status = $final.status
            conclusion = $final.conclusion
            url = $final.url
        }
    }
}

Write-CsvSafe -Path (Join-Path $script:OutDir "21_failed_runs_after.csv") -Rows $rerunResults

$checks = @()

$scorecardScript = Join-Path $repoRoot "scripts\execution\95_live_scorecard_audit.ps1"
if (Test-Path $scorecardScript) {
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_baseline" -WorkingDirectory $repoRoot -Exe "powershell" -Args @("-ExecutionPolicy","Bypass","-File",$scorecardScript)
    $checks += Invoke-LoggedCommand -Name "95_live_scorecard_audit_deep" -WorkingDirectory $repoRoot -Exe "powershell" -Args @("-ExecutionPolicy","Bypass","-File",$scorecardScript,"-Deep")
}

$frontendDir = Join-Path $repoRoot "frontend\dashboards"
if (Test-Path (Join-Path $frontendDir "package.json")) {
    $checks += Invoke-LoggedCommand -Name "frontend_shell_contracts" -WorkingDirectory $frontendDir -Exe "npm.cmd" -Args @("run","check:shell-contracts")
    $checks += Invoke-LoggedCommand -Name "frontend_unit" -WorkingDirectory $frontendDir -Exe "npm.cmd" -Args @("run","test:unit")
    $checks += Invoke-LoggedCommand -Name "frontend_release_a11y" -WorkingDirectory $frontendDir -Exe "npm.cmd" -Args @("run","test:release:a11y") -Env @{ CI = "1" }
    $checks += Invoke-LoggedCommand -Name "frontend_nav" -WorkingDirectory $frontendDir -Exe "npm.cmd" -Args @("run","ui:proof:nav") -Env @{ CI = "1" }
    $checks += Invoke-LoggedCommand -Name "frontend_release_routes" -WorkingDirectory $frontendDir -Exe "npm.cmd" -Args @("run","test:release:routes") -Env @{ CI = "1" }
}

$backendGate = Join-Path $repoRoot "backend\tests\test_reporting_exports_gate.py"
if (Test-Path $backendGate) {
    $checks += Invoke-LoggedCommand -Name "backend_reporting_exports_gate" -WorkingDirectory $repoRoot -Exe "python" -Args @("-m","pytest","backend/tests/test_reporting_exports_gate.py","-q")
}

$backendManage = Join-Path $repoRoot "backend\manage.py"
if (Test-Path $backendManage) {
    $checks += Invoke-LoggedCommand -Name "backend_django_check" -WorkingDirectory (Join-Path $repoRoot "backend") -Exe "python" -Args @("manage.py","check")
}

Write-CsvSafe -Path (Join-Path $script:OutDir "30_check_results.csv") -Rows $checks

$summaryPath = Join-Path $repoRoot "audit-artifacts\live-scorecard\latest\RUN_SUMMARY.txt"
$summary = Parse-RunSummary -Path $summaryPath

$allChecksPassed = (@($checks | Where-Object { -not $_.Passed }).Count -eq 0)
$allRerunsPassed = (@($rerunResults | Where-Object { $_.status -ne "completed" -or $_.conclusion -ne "success" }).Count -eq 0)
$dirtyAfter = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count

$mergeCmds = New-Object System.Collections.Generic.List[string]
$mergeCmds.Add('$ErrorActionPreference = "Stop"')
$mergeCmds.Add('Set-Location "' + $repoRoot + '"')
$mergeCmds.Add('')

if ($PrepareMerge) {
    $mergeCmds.Add('gh pr view ' + $TargetPR)
    $mergeCmds.Add('gh pr checks ' + $TargetPR)
    $mergeCmds.Add('')
    if (
        $pr.state -eq "OPEN" -and
        -not $pr.isDraft -and
        $pr.mergeStateStatus -eq "CLEAN" -and
        $allChecksPassed -and
        $allRerunsPassed -and
        $dirtyAfter -eq 0
    ) {
        $mergeCmds.Add('gh pr merge ' + $TargetPR + ' --squash --delete-branch')
    } else {
        $mergeCmds.Add('# Merge not auto-approved by script. Review summary first.')
        $mergeCmds.Add('# If PR is obsolete after mainline reconciliation, close it:')
        $mergeCmds.Add('gh pr close ' + $TargetPR + ' --comment "Superseded by verified mainline reconciliation and current main state."')
    }
}

Write-Utf8 (Join-Path $script:OutDir "40_merge_or_close_commands.ps1") $mergeCmds

if (
    $AutoMergeIfGreen -and
    $pr.state -eq "OPEN" -and
    -not $pr.isDraft -and
    $pr.mergeStateStatus -eq "CLEAN" -and
    $allChecksPassed -and
    $allRerunsPassed -and
    $dirtyAfter -eq 0
) {
    & gh pr merge $TargetPR --squash --delete-branch | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Auto-merge failed."
    }
}

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add("# Mainline Reconciliation Summary")
$summaryLines.Add("")
$summaryLines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summaryLines.Add("- Repo: $repoSlug")
$summaryLines.Add("- Starting branch: $currentBranch")
$summaryLines.Add("- Starting head: $currentHead")
$summaryLines.Add("- Main head after sync: $mainHead")
$summaryLines.Add("- Target PR: #$($pr.number) $($pr.title)")
$summaryLines.Add("- PR state: $($pr.state)")
$summaryLines.Add("- PR draft: $($pr.isDraft)")
$summaryLines.Add("- PR mergeStateStatus: $($pr.mergeStateStatus)")
$summaryLines.Add("- PR review decision: $($pr.reviewDecision)")
$summaryLines.Add("- Failed workflow groups before rerun: $($latestFailedByWorkflow.Count)")
$summaryLines.Add("- Failed workflow groups after rerun not green: $(@($rerunResults | Where-Object { $_.status -ne 'completed' -or $_.conclusion -ne 'success' }).Count)")
$summaryLines.Add("- Local check failures: $(@($checks | Where-Object { -not $_.Passed }).Count)")
$summaryLines.Add("- Dirty count after reconciliation: $dirtyAfter")
$summaryLines.Add("- Latest scorecard overall: $($summary.OverallScore)")
$summaryLines.Add("- Latest scorecard dirty count: $($summary.DirtyCount)")
$summaryLines.Add("- Latest release line: $($summary.ReleaseLine)")
$summaryLines.Add("")

$summaryLines.Add("## Next action")
$summaryLines.Add("")
if (
    $pr.state -eq "OPEN" -and
    -not $pr.isDraft -and
    $pr.mergeStateStatus -eq "CLEAN" -and
    $allChecksPassed -and
    $allRerunsPassed -and
    $dirtyAfter -eq 0
) {
    $summaryLines.Add("1. Run 40_merge_or_close_commands.ps1 to merge PR #$TargetPR.")
} else {
    $summaryLines.Add("1. Review 10_pr_status.json, 20_failed_runs_before.csv, 21_failed_runs_after.csv, and 30_check_results.csv.")
    $summaryLines.Add("2. Use 40_merge_or_close_commands.ps1 only after remaining GitHub/mainline issues are resolved.")
}

Write-Utf8 (Join-Path $script:OutDir "00_SUMMARY.md") $summaryLines

Copy-Item -Path (Join-Path $script:OutDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $script:OutDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host ""
