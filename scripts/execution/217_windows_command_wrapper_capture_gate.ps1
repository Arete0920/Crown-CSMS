param(
    [string]$OutputRoot = "audit-artifacts/windows-command-wrapper-capture",
    [switch]$FailOnFinding
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Invoke-CaptureCandidate {
    param(
        [string]$Name,
        [string]$Exe,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$OutputDir,
        [switch]$UseCmdBridge
    )

    $stdout = Join-Path $OutputDir ("{0}.stdout.txt" -f $Name)
    $stderr = Join-Path $OutputDir ("{0}.stderr.txt" -f $Name)
    $started = Get-Date
    $filePath = $Exe
    $argumentList = $Arguments
    $mode = "direct"

    if ($UseCmdBridge) {
        $mode = "cmd-bridge"
        $filePath = "cmd.exe"
        $escaped = @('/d', '/c', '"' + $Exe + '"') + $Arguments
        $argumentList = $escaped
    }

    $exitCode = $null
    $status = "UNKNOWN"
    $errorText = ""

    try {
        $proc = Start-Process -FilePath $filePath -ArgumentList $argumentList -WorkingDirectory $WorkingDirectory -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $finished = $proc.WaitForExit(30000)
        if (-not $finished) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            $status = "TIMEOUT"
            $exitCode = 124
        } else {
            $exitCode = [int]$proc.ExitCode
            $status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
        }
    } catch {
        $status = "ERROR"
        $exitCode = 1
        $errorText = $_.Exception.Message
        $errorText | Set-Content -Path $stderr -Encoding UTF8
    }

    return [pscustomobject]@{
        name = $Name
        mode = $mode
        file_path = $filePath
        arguments = ($argumentList -join ' ')
        working_directory = $WorkingDirectory
        status = $status
        exit_code = $exitCode
        error = $errorText
        stdout = $stdout
        stderr = $stderr
        duration_sec = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot (Join-Path $OutputRoot $stamp)
$latestDir = Join-Path $repoRoot (Join-Path $OutputRoot "latest")
New-Dir $outDir
New-Dir $latestDir

$isWindows = $false
if (Get-Variable IsWindows -ErrorAction SilentlyContinue) {
    $isWindows = [bool]$IsWindows
} else {
    $isWindows = ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT)
}

$results = New-Object System.Collections.Generic.List[object]
$results.Add((Invoke-CaptureCandidate -Name "python_direct_version" -Exe "python" -Arguments @("--version") -WorkingDirectory $repoRoot -OutputDir $outDir)) | Out-Null

$npmCmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
if ($null -ne $npmCmd) {
    $results.Add((Invoke-CaptureCandidate -Name "npm_cmd_direct_version" -Exe $npmCmd.Source -Arguments @("--version") -WorkingDirectory $repoRoot -OutputDir $outDir)) | Out-Null
    $results.Add((Invoke-CaptureCandidate -Name "npm_cmd_bridge_version" -Exe $npmCmd.Source -Arguments @("--version") -WorkingDirectory $repoRoot -OutputDir $outDir -UseCmdBridge)) | Out-Null
}

$npxCmd = Get-Command "npx.cmd" -ErrorAction SilentlyContinue
if ($null -ne $npxCmd) {
    $results.Add((Invoke-CaptureCandidate -Name "npx_cmd_direct_version" -Exe $npxCmd.Source -Arguments @("--version") -WorkingDirectory $repoRoot -OutputDir $outDir)) | Out-Null
    $results.Add((Invoke-CaptureCandidate -Name "npx_cmd_bridge_version" -Exe $npxCmd.Source -Arguments @("--version") -WorkingDirectory $repoRoot -OutputDir $outDir -UseCmdBridge)) | Out-Null
}

$rows = @($results.ToArray())
$directWrapperErrors = @($rows | Where-Object { $_.mode -eq "direct" -and $_.file_path -match "\.cmd$" -and $_.status -ne "PASS" })
$bridgeWrapperErrors = @($rows | Where-Object { $_.mode -eq "cmd-bridge" -and $_.status -ne "PASS" })

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    is_windows = $isWindows
    result_count = $rows.Count
    direct_wrapper_error_count = $directWrapperErrors.Count
    bridge_wrapper_error_count = $bridgeWrapperErrors.Count
    pass = ($bridgeWrapperErrors.Count -eq 0)
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
$rows | Export-Csv -Path (Join-Path $outDir "20_command_wrapper_capture_results.csv") -NoTypeInformation -Encoding UTF8

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Windows Command Wrapper Capture Gate")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Windows: $isWindows")
$summary.Add("- Results: $($rows.Count)")
$summary.Add("- Direct wrapper errors: $($directWrapperErrors.Count)")
$summary.Add("- Cmd bridge errors: $($bridgeWrapperErrors.Count)")
$summary.Add("")
$summary.Add("## Verdict")
$summary.Add("")
if ($status.pass) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
}
$summary | Set-Content -Path (Join-Path $outDir "00_SUMMARY.md") -Encoding UTF8
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "WINDOWS_WRAPPER_EVIDENCE=$outDir"
Write-Host "WINDOWS_WRAPPER_SUMMARY=$(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "WINDOWS_WRAPPER_RESULTS=$(Join-Path $outDir '20_command_wrapper_capture_results.csv')"

if ($FailOnFinding -and -not $status.pass) { exit 1 }
