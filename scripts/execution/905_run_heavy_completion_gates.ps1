param(
    [switch]$Run105First
)

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Branch-Name {
    $name = (git branch --show-current 2>$null)
    if ($name) { return $name.Trim() }
    $ref = (git rev-parse --abbrev-ref HEAD 2>$null)
    if ($ref -and $ref.Trim() -ne "HEAD") { return $ref.Trim() }
    return "detached-head"
}

function Invoke-Gate {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory,
        [string]$LogPath
    )

    Write-Host "==> $Name"
    $start = Get-Date
    $ok = $true
    $exitCode = 0

    @(
        "==> $Name",
        "Started: $($start.ToString('s'))",
        "WorkingDirectory: $WorkingDirectory",
        "Command: $Command",
        ""
    ) | Set-Content -Path $LogPath -Encoding UTF8

    Push-Location $WorkingDirectory
    try {
        if (Get-Command cmd.exe -ErrorAction SilentlyContinue) {
            cmd.exe /c $Command 1>> $LogPath 2>&1
        } else {
            pwsh -NoLogo -NoProfile -Command $Command 1>> $LogPath 2>&1
        }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        if ($exitCode -ne 0) { $ok = $false }
    } catch {
        $ok = $false
        $_ | Out-String | Add-Content -Path $LogPath
        $exitCode = 1
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

function Write-Outputs {
    param(
        [object[]]$Steps,
        [string]$OutDir,
        [string]$LatestDir,
        [string]$Branch,
        [string]$Head,
        [string]$Stage
    )

    New-Dir $OutDir
    New-Dir $LatestDir

    $summaryPath = Join-Path $OutDir "00_SUMMARY.md"
    $stepsPath = Join-Path $OutDir "20_execution_steps.csv"
    $statusPath = Join-Path $OutDir "99_STATUS.json"

    $Steps | Export-Csv -Path $stepsPath -NoTypeInformation -Encoding UTF8
    $failed = @($Steps | Where-Object { -not $_.Passed })
    $passed = @($Steps | Where-Object { $_.Passed })
    $isPass = ($Stage -eq "complete" -and $failed.Count -eq 0 -and $Steps.Count -gt 0)

    @(
        "# CROWN Heavy Completion Gates",
        "",
        "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "- Stage: $Stage",
        "- Branch: $Branch",
        "- Head: $Head",
        "- Passed steps: $($passed.Count)",
        "- Failed steps: $($failed.Count)",
        "",
        $(if ($isPass) { "RESULT: PASS" } elseif ($Stage -eq "complete") { "RESULT: ACTION REQUIRED" } else { "RESULT: RUNNING_OR_INTERRUPTED" })
    ) | Set-Content -Path $summaryPath -Encoding UTF8

    $status = [ordered]@{
        generated_at = (Get-Date).ToString("s")
        stage = $Stage
        branch = $Branch
        head = $Head
        passed = $isPass
        passed_steps = $passed.Count
        failed_steps = $failed.Count
        output_dir = $OutDir
    }
    ($status | ConvertTo-Json -Depth 5) | Set-Content -Path $statusPath -Encoding UTF8
    Copy-Item -Path (Join-Path $OutDir "*") -Destination $LatestDir -Recurse -Force
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$head = (git rev-parse HEAD).Trim()
$branch = Branch-Name
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\heavy-completion-gates\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\heavy-completion-gates\latest"
$logsDir = Join-Path $outDir "logs"
New-Dir $logsDir

$env:VITE_SANDBOX_READY_ONLY = "true"
$env:VITE_HIDE_UNREADY_NAV = "true"
$env:VITE_SANDBOX_MODE = "1"
$env:CROWN_ENV = "production"
$env:CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = "0"
$env:TENANT_HEADER_REQUIRED = "0"

$steps = New-Object System.Collections.Generic.List[object]
Write-Outputs -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "started"

$gate105 = "powershell -ExecutionPolicy Bypass -File scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep"
$gate106 = "powershell -ExecutionPolicy Bypass -File scripts\execution\106_crown_full_completion_truth_gate.ps1 -Deep"

if ($Run105First) {
    $steps.Add((Invoke-Gate "Dashboard module completion gate" $gate105 $repoRoot (Join-Path $logsDir "105_dashboard_module_completion_gate.log"))) | Out-Null
    Write-Outputs -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "105-complete"
    $steps.Add((Invoke-Gate "Full completion truth gate" $gate106 $repoRoot (Join-Path $logsDir "106_full_completion_truth_gate.log"))) | Out-Null
} else {
    $steps.Add((Invoke-Gate "Full completion truth gate" $gate106 $repoRoot (Join-Path $logsDir "106_full_completion_truth_gate.log"))) | Out-Null
    Write-Outputs -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "106-complete"
    $steps.Add((Invoke-Gate "Dashboard module completion gate" $gate105 $repoRoot (Join-Path $logsDir "105_dashboard_module_completion_gate.log"))) | Out-Null
}

Write-Outputs -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "complete"

Write-Host "Heavy completion gates complete."
Write-Host "Summary: $outDir\00_SUMMARY.md"
Write-Host "Latest:  $latestDir"

$failed = @($steps | Where-Object { -not $_.Passed })
if ($failed.Count -gt 0) { exit 1 }
