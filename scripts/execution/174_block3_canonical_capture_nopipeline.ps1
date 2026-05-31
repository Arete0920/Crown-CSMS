param(
    [string]$EvidenceRoot,
    [switch]$UseTimestamp
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Missing venv python at $pythonExe"
}

if ($UseTimestamp) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $EvidenceRoot = Join-Path $repoRoot "audit-artifacts\final-95-plus-sprint\$stamp"
}

if (-not $EvidenceRoot) {
    throw "Provide -EvidenceRoot or use -UseTimestamp"
}

if (-not (Test-Path $EvidenceRoot)) {
    New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
}

function Invoke-CapturePytest {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)][string]$TargetPath,
        [Parameter(Mandatory=$true)][string[]]$PytestArgs,
        [Parameter(Mandatory=$true)][string]$ExitKey
    )

    $outFile = Join-Path $EvidenceRoot $TargetPath
    $stdoutTmp = [System.IO.Path]::GetTempFileName()
    $stderrTmp = [System.IO.Path]::GetTempFileName()

    try {
        Set-Content -Path $outFile -Value $Label

        $argList = @('-m','pytest') + $PytestArgs

        $proc = Start-Process -FilePath $pythonExe `
            -ArgumentList $argList `
            -WorkingDirectory $repoRoot `
            -RedirectStandardOutput $stdoutTmp `
            -RedirectStandardError $stderrTmp `
            -PassThru -Wait -NoNewWindow

        if (Test-Path $stdoutTmp) {
            Add-Content -Path $outFile -Value (Get-Content -Path $stdoutTmp)
        }
        if (Test-Path $stderrTmp) {
            Add-Content -Path $outFile -Value (Get-Content -Path $stderrTmp)
        }

        Add-Content -Path $outFile -Value "$ExitKey=$($proc.ExitCode)"
        return $proc.ExitCode
    }
    finally {
        Remove-Item -Path $stdoutTmp -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $stderrTmp -Force -ErrorAction SilentlyContinue
    }
}

$runPlan = @(
    @{
        Label = "=== ADMISSIONS ENDPOINTS (CANONICAL NOPIPE SCRIPT) ==="
        TargetPath = "08_admissions_endpoints.txt"
        PytestArgs = @("backend/applications/tests/test_admissions_endpoints.py", "-q", "-s")
        ExitKey = "admissions_endpoints_exit"
    },
    @{
        Label = "=== AFTERCARE (CANONICAL NOPIPE SCRIPT) ==="
        TargetPath = "09_aftercare.txt"
        PytestArgs = @("backend/aftercare", "-q", "-s")
        ExitKey = "aftercare_exit"
    },
    @{
        Label = "=== LATER TIER METRICS (CANONICAL NOPIPE SCRIPT) ==="
        TargetPath = "10_later_tier_metrics.txt"
        PytestArgs = @("backend/tests/test_later_tier_metrics_api.py", "-q", "-s")
        ExitKey = "later_tier_metrics_exit"
    }
)

foreach ($spec in $runPlan) {
    $code = Invoke-CapturePytest -Label $spec.Label -TargetPath $spec.TargetPath -PytestArgs $spec.PytestArgs -ExitKey $spec.ExitKey
    if ($code -ne 0) {
        Write-Host "First blocker captured in $($spec.TargetPath) with exit=$code"
        exit $code
    }
}

Write-Host "Block-3 canonical capture complete at: $EvidenceRoot"
exit 0
