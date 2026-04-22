param(
    [int]$TailLines = 120
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

function Write-CsvSafe {
    param([string]$Path, $Rows)
    $arr = @($Rows | Where-Object { $null -ne $_ })
    if ($arr.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $arr | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$sourceDir = Join-Path $repoRoot ".crown-audit\clear-main-failures\latest"
$failedCsv = Join-Path $sourceDir "10_failed_runs.csv"
$logsIndexCsv = Join-Path $sourceDir "20_failed_logs_index.csv"

if (-not (Test-Path $failedCsv)) {
    throw "Missing $failedCsv"
}
if (-not (Test-Path $logsIndexCsv)) {
    throw "Missing $logsIndexCsv"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\failed-main-triage\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\failed-main-triage\latest"
New-Dir $outDir
New-Dir $latestDir

$failedRuns = @(Import-Csv $failedCsv)
$logsIndex = @(Import-Csv $logsIndexCsv)

$errorPatterns = @(
    'Traceback',
    'Error:',
    'ERROR:',
    'Exception:',
    'FAILED',
    'AssertionError',
    'ModuleNotFoundError',
    'ImportError',
    'Permission denied',
    'denied',
    'timed out',
    'timeout',
    'not found',
    'No such file',
    'Process completed with exit code',
    'npm ERR!',
    'pytest',
    'playwright',
    'gitleaks',
    'schema',
    'deploy',
    'health',
    'smoke'
)

$signatures = @()
$fixPlan = @()
$fixPlan += "# Failed Main Workflow Fix Plan"
$fixPlan += ""
$fixPlan += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$fixPlan += "- Failed workflows detected: $($failedRuns.Count)"
$fixPlan += ""

foreach ($run in $failedRuns) {
    $logRow = $logsIndex | Where-Object { $_.databaseId -eq $run.databaseId } | Select-Object -First 1
    $logPath = $null
    if ($null -ne $logRow) { $logPath = $logRow.log }

    $topHits = @()
    $tail = @()

    if ($logPath -and (Test-Path $logPath)) {
        $lines = @(Get-Content $logPath)
        $tail = @($lines | Select-Object -Last $TailLines)

        foreach ($pattern in $errorPatterns) {
            $matches = @($lines | Select-String -Pattern $pattern -SimpleMatch | Select-Object -First 3)
            foreach ($m in $matches) {
                $topHits += ($m.Line.Trim())
            }
        }

        $topHits = @($topHits | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique | Select-Object -First 8)
    }

    if ($topHits.Count -eq 0 -and $tail.Count -gt 0) {
        $topHits = @($tail | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 8)
    }

    $signatureText = ($topHits -join " || ")

    $signatures += [pscustomobject]@{
        workflowName = $run.workflowName
        databaseId = $run.databaseId
        createdAt = $run.createdAt
        signature = $signatureText
        log = $logPath
    }

    $fixPlan += "## $($run.workflowName) [$($run.databaseId)]"
    $fixPlan += ""
    $fixPlan += "- Created: $($run.createdAt)"
    $fixPlan += "- Log: $logPath"
    $fixPlan += "- Failure signature:"
    if ($topHits.Count -gt 0) {
        foreach ($hit in $topHits) {
            $fixPlan += "  - $hit"
        }
    } else {
        $fixPlan += "  - No signature extracted automatically."
    }
    $fixPlan += ""
}

Write-CsvSafe -Path (Join-Path $outDir "10_failed_runs.csv") -Rows $failedRuns
Write-CsvSafe -Path (Join-Path $outDir "20_error_signatures.csv") -Rows $signatures
Write-Utf8 -Path (Join-Path $outDir "30_workflow_fix_plan.md") -Lines $fixPlan

$openLogs = @()
$openLogs += '$ErrorActionPreference = "Stop"'
$openLogs += ('Set-Location "' + $repoRoot + '"')
$openLogs += ''
foreach ($s in $signatures) {
    if ($s.log -and (Test-Path $s.log)) {
        $openLogs += ('code "' + $s.log + '"')
    }
}
Write-Utf8 -Path (Join-Path $outDir "40_open_logs.ps1") -Lines $openLogs

$summary = @()
$summary += "# Failed Main Workflow Triage Summary"
$summary += ""
$summary += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$summary += "- Failed workflows: $($failedRuns.Count)"
$summary += ""
$summary += "## Next"
$summary += ""
$summary += "1. Open all failed logs with 40_open_logs.ps1"
$summary += "2. Fix each workflow listed in 30_workflow_fix_plan.md"
$summary += "3. Commit and push the fixes"
$summary += "4. Rerun 100_clear_main_failures.ps1"
$summary += "5. When failed workflows after rerun = 0, rerun 99_force_100_readiness.ps1 -Push"

Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host ""
