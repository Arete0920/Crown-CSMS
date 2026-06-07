param(
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\95-frontend-unit-capture-debug\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\95-frontend-unit-capture-debug\latest"
New-Dir $outDir
New-Dir $latestDir

$frontendDir = Join-Path $repoRoot "frontend\dashboards"
$stdoutPath = Join-Path $outDir "frontend_unit.stdout.txt"
$stderrPath = Join-Path $outDir "frontend_unit.stderr.txt"
$combinedPath = Join-Path $outDir "frontend_unit.combined.txt"
$summaryPath = Join-Path $outDir "00_SUMMARY.md"
$statusPath = Join-Path $outDir "99_STATUS.json"
$processPath = Join-Path $outDir "20_process_snapshot.txt"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    throw "Missing frontend/dashboards/package.json"
}

$head = (git rev-parse HEAD).Trim()
$branch = (git branch --show-current 2>$null)
if ([string]::IsNullOrWhiteSpace($branch)) { $branch = "detached-head" }

$env:CI = "1"
$env:VITE_SANDBOX_READY_ONLY = "true"
$env:VITE_HIDE_UNREADY_NAV = "true"
$env:VITE_SANDBOX_MODE = "1"

@(
    "# 95 frontend unit capture diagnostic",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Stage: started",
    "- Branch: $branch",
    "- Head: $head",
    "- Timeout seconds: $TimeoutSeconds",
    "- Command: cmd.exe /d /s /c npm.cmd run test:unit",
    ""
) | Set-Content -Path $summaryPath -Encoding UTF8

$start = Get-Date
$exitCode = 1
$timedOut = $false

Push-Location $frontendDir
try {
    $proc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/d", "/s", "/c", "npm.cmd run test:unit") `
        -WorkingDirectory $frontendDir `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -NoNewWindow `
        -PassThru

    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
        $timedOut = $true
        try {
            Get-Process node,cmd,powershell -ErrorAction SilentlyContinue |
                Select-Object ProcessName,Id,CPU,StartTime,Path |
                Sort-Object StartTime |
                Format-Table -AutoSize |
                Out-String |
                Set-Content -Path $processPath -Encoding UTF8
        } catch {
            $_ | Out-String | Set-Content -Path $processPath -Encoding UTF8
        }
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        $exitCode = 124
    } else {
        $exitCode = [int]$proc.ExitCode
    }
} finally {
    Pop-Location
}

@(
    "=== STDOUT ===",
    $(if (Test-Path $stdoutPath) { Get-Content $stdoutPath -Raw } else { "<missing stdout>" }),
    "",
    "=== STDERR ===",
    $(if (Test-Path $stderrPath) { Get-Content $stderrPath -Raw } else { "<missing stderr>" })
) | Set-Content -Path $combinedPath -Encoding UTF8

$seconds = [int]((Get-Date) - $start).TotalSeconds
$passed = ($exitCode -eq 0)

@(
    "# 95 frontend unit capture diagnostic",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Stage: complete",
    "- Branch: $branch",
    "- Head: $head",
    "- Exit code: $exitCode",
    "- Timed out: $timedOut",
    "- Passed: $passed",
    "- Seconds: $seconds",
    "- Stdout: frontend_unit.stdout.txt",
    "- Stderr: frontend_unit.stderr.txt",
    "- Combined: frontend_unit.combined.txt",
    "",
    $(if ($passed) { "RESULT: PASS" } else { "RESULT: ACTION REQUIRED" })
) | Set-Content -Path $summaryPath -Encoding UTF8

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = $branch
    head = $head
    exit_code = $exitCode
    timed_out = $timedOut
    passed = $passed
    seconds = $seconds
    output_dir = $outDir
}
($status | ConvertTo-Json -Depth 5) | Set-Content -Path $statusPath -Encoding UTF8

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "95 frontend unit diagnostic complete."
Write-Host "Summary: $summaryPath"
Write-Host "Latest:  $latestDir"

if (-not $passed) { exit 1 }
