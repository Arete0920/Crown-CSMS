param(
    [int]$PollSeconds = 20,
    [int]$MaxPollMinutes = 20
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

Require-Tool git
Require-Tool gh

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\clear-main-failures\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\clear-main-failures\latest"
New-Dir $outDir
New-Dir $latestDir

$runs = Invoke-GhJson -GhArgs @(
    "run","list",
    "--branch","main",
    "--limit","120",
    "--json","databaseId,workflowName,status,conclusion,createdAt,url,displayTitle,event,headSha"
)

$latestPerWorkflow = @(
    $runs |
    Group-Object workflowName |
    ForEach-Object { $_.Group | Sort-Object createdAt -Descending | Select-Object -First 1 }
)

$failed = @(
    $latestPerWorkflow |
    Where-Object {
        $_.status -eq "completed" -and $_.conclusion -in @("failure","cancelled","timed_out","action_required","startup_failure")
    }
) | Sort-Object workflowName

Write-CsvSafe -Path (Join-Path $outDir "10_failed_runs.csv") -Rows $failed

$logsIndex = @()
foreach ($run in $failed) {
    $logPath = Join-Path $outDir ("logs\" + $run.databaseId + ".failed.log")
    New-Dir (Split-Path -Parent $logPath)
    try {
        $env:GH_PAGER = "cat"
        gh run view $run.databaseId --log-failed *> $logPath
        $logsIndex += [pscustomobject]@{
            databaseId = $run.databaseId
            workflowName = $run.workflowName
            log = $logPath
            captured = $true
        }
    }
    catch {
        $logsIndex += [pscustomobject]@{
            databaseId = $run.databaseId
            workflowName = $run.workflowName
            log = $logPath
            captured = $false
        }
    }
}
Write-CsvSafe -Path (Join-Path $outDir "20_failed_logs_index.csv") -Rows $logsIndex

$rerunResults = @()
foreach ($run in $failed) {
    & gh run rerun $run.databaseId | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $rerunResults += [pscustomobject]@{
            databaseId = $run.databaseId
            workflowName = $run.workflowName
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
        $view = Invoke-GhJson -GhArgs @(
            "run","view",$run.databaseId.ToString(),
            "--json","databaseId,workflowName,status,conclusion,url"
        )
        if ($view.status -eq "completed") {
            $final = $view
            break
        }
    }

    if ($null -eq $final) {
        $final = Invoke-GhJson -GhArgs @(
            "run","view",$run.databaseId.ToString(),
            "--json","databaseId,workflowName,status,conclusion,url"
        )
    }

    $rerunResults += [pscustomobject]@{
        databaseId = $final.databaseId
        workflowName = $final.workflowName
        status = $final.status
        conclusion = $final.conclusion
        url = $final.url
    }
}

Write-CsvSafe -Path (Join-Path $outDir "30_rerun_results.csv") -Rows $rerunResults

$stillFailing = @(
    $rerunResults | Where-Object {
        $_.status -ne "completed" -or $_.conclusion -ne "success"
    }
)

$next = @()
$next += '$ErrorActionPreference = "Stop"'
$next += ('Set-Location "' + $repoRoot + '"')
$next += ''
$next += '# Open the failed logs first'
foreach ($r in $stillFailing) {
    $next += ('code ".\.crown-audit\clear-main-failures\latest\logs\' + $r.databaseId + '.failed.log"')
}
$next += ''
$next += '# Re-check live run state'
$next += 'gh run list --branch main --limit 40 --json databaseId,workflowName,status,conclusion,createdAt,url'
$next += ''
$next += '# Re-run final readiness once all main workflows are green'
$next += 'powershell -ExecutionPolicy Bypass -File .\scripts\execution\99_force_100_readiness.ps1 -Push'
Write-Utf8 (Join-Path $outDir "40_next_commands.ps1") $next

$summary = @()
$summary += "# Clear Main Failures Summary"
$summary += ""
$summary += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$summary += "- Failed workflows before rerun: $($failed.Count)"
$summary += "- Failed workflows after rerun: $($stillFailing.Count)"
$summary += ""

if ($stillFailing.Count -eq 0) {
    $summary += "## Result"
    $summary += ""
    $summary += "PASS"
    $summary += ""
    $summary += "Run next:"
    $summary += "powershell -ExecutionPolicy Bypass -File .\scripts\execution\99_force_100_readiness.ps1 -Push"
} else {
    $summary += "## Result"
    $summary += ""
    $summary += "REVIEW REQUIRED"
    $summary += ""
    $summary += "Still failing workflows:"
    foreach ($r in $stillFailing) {
        $summary += "- $($r.workflowName) [$($r.databaseId)] => $($r.status) / $($r.conclusion)"
    }
}

Write-Utf8 (Join-Path $outDir "00_SUMMARY.md") $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    failed_before = $failed
    rerun_results = $rerunResults
    still_failing = $stillFailing
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
Write-Host ""

if ($stillFailing.Count -gt 0) { exit 1 }
