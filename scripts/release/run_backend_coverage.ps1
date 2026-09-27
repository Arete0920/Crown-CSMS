#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+(\.\d+)?([a-zA-Z0-9.-]+)?$')]
    [string]$CoverageVersion,

    [string]$OutputDirectory = "audit-artifacts/backend-coverage"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$repositoryRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repositoryRoot)) {
    throw "Unable to resolve the repository root."
}

Push-Location $repositoryRoot
try {
    $sourceSha = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($sourceSha)) {
        throw "Unable to resolve the exact source SHA."
    }

    $initialStatus = @(& git status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the worktree state."
    }
    if ($initialStatus.Count -ne 0) {
        throw "Coverage evidence requires a clean worktree before execution."
    }

    $resolvedOutputDirectory = Join-Path $repositoryRoot $OutputDirectory
    if (Test-Path $resolvedOutputDirectory) {
        Remove-Item -Recurse -Force $resolvedOutputDirectory
    }
    New-Item -ItemType Directory -Path $resolvedOutputDirectory -Force | Out-Null

    $pytestLog = Join-Path $resolvedOutputDirectory "pytest-complete.log"
    $pytestJunit = Join-Path $resolvedOutputDirectory "pytest-junit.xml"
    $coverageText = Join-Path $resolvedOutputDirectory "coverage-report.txt"
    $coverageJson = Join-Path $resolvedOutputDirectory "coverage.json"
    $coverageXml = Join-Path $resolvedOutputDirectory "coverage.xml"
    $governedCoverageJson = Join-Path $resolvedOutputDirectory "governed-coverage.json"
    $metadataPath = Join-Path $resolvedOutputDirectory "run-metadata.json"
    $boundaryConfig = Join-Path $repositoryRoot "scripts/release/backend_coverage_boundary.json"
    $boundaryEvaluator = Join-Path $repositoryRoot "scripts/release/evaluate_backend_coverage.py"

    foreach ($requiredPath in @($boundaryConfig, $boundaryEvaluator)) {
        if (-not (Test-Path $requiredPath)) {
            throw "Missing governed coverage input: $requiredPath"
        }
    }

    Invoke-NativeCommand -Description "Coverage installation" -Command {
        python -m pip install --disable-pip-version-check "coverage==$CoverageVersion"
    }

    $pythonVersion = (& python --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to record the Python version."
    }
    $installedCoverageVersion = (& python -m coverage --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to record the coverage version."
    }
    $pytestVersion = (& python -m pytest --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to record the pytest version."
    }

    Invoke-NativeCommand -Description "Coverage erase" -Command {
        python -m coverage erase
    }

    & python -m coverage run --rcfile=.coveragerc -m pytest -q backend --junitxml=$pytestJunit *>&1 |
        Tee-Object -FilePath $pytestLog
    $pytestExitCode = $LASTEXITCODE

    # Preserve the broad backend/** result as repository-health evidence without
    # using that secondary metric as the release gate.
    & python -m coverage json --rcfile=.coveragerc --fail-under=0 -o $coverageJson
    $coverageJsonExitCode = $LASTEXITCODE
    & python -m coverage xml --rcfile=.coveragerc --fail-under=0 -o $coverageXml
    $coverageXmlExitCode = $LASTEXITCODE
    & python -m coverage report --rcfile=.coveragerc --fail-under=0 *>&1 |
        Tee-Object -FilePath $coverageText
    $broadReportExitCode = $LASTEXITCODE

    $governedCoverageExitCode = 2
    if (Test-Path $coverageJson) {
        & python $boundaryEvaluator `
            --coverage-json $coverageJson `
            --boundary-config $boundaryConfig `
            --coveragerc (Join-Path $repositoryRoot ".coveragerc") `
            --repo-root $repositoryRoot `
            --output $governedCoverageJson
        $governedCoverageExitCode = $LASTEXITCODE
    }

    if (-not (Test-Path $coverageJson)) {
        throw "Coverage JSON was not generated."
    }

    $coverageData = Get-Content -Raw $coverageJson | ConvertFrom-Json -AsHashtable
    $totals = $coverageData["totals"]
    $governedData = $null
    if (Test-Path $governedCoverageJson) {
        $governedData = Get-Content -Raw $governedCoverageJson | ConvertFrom-Json -AsHashtable
    }
    $completedAt = (Get-Date).ToUniversalTime().ToString("o")

    $pytestSummary = $null
    if (Test-Path $pytestJunit) {
        [xml]$pytestXml = Get-Content -Raw $pytestJunit
        $suite = $pytestXml.testsuites.testsuite | Select-Object -First 1
        if ($null -ne $suite) {
            $pytestSummary = [ordered]@{
                tests = [int]$suite.tests
                failures = [int]$suite.failures
                errors = [int]$suite.errors
                skipped = [int]$suite.skipped
                time_seconds = [double]$suite.time
            }
        }
    }

    $artifactDigests = [ordered]@{}
    foreach ($artifactPath in @($pytestLog, $pytestJunit, $coverageText, $coverageJson, $coverageXml, $governedCoverageJson)) {
        if (Test-Path $artifactPath) {
            $artifactDigests[(Split-Path $artifactPath -Leaf)] = (Get-FileHash -Algorithm SHA256 $artifactPath).Hash.ToLowerInvariant()
        }
    }

    $governedMetric = $null
    $thresholdPass = $false
    if ($null -ne $governedData) {
        $governedMetric = $governedData["governed_operational_inclusive"]
        $thresholdPass = [bool]$governedData["threshold_pass"]
    }

    $metadata = [ordered]@{
        schema_version = 2
        generated_at_utc = $completedAt
        repository = "Arete0920/Crown-CSMS"
        source_sha = $sourceSha
        worktree_clean_before_run = $true
        runner = "scripts/release/run_backend_coverage.ps1"
        test_command = "python -m coverage run --rcfile=.coveragerc -m pytest -q backend --junitxml=<artifact-path>"
        coverage_config = ".coveragerc"
        coverage_boundary_config = "scripts/release/backend_coverage_boundary.json"
        coverage_boundary_evaluator = "scripts/release/evaluate_backend_coverage.py"
        coverage_threshold_percent = 75
        release_gate_metric = "operational-inclusive backend application coverage"
        broad_backend_metric_is_repository_health_only = $true
        python_version = $pythonVersion
        pytest_version = $pytestVersion
        requested_coverage_version = $CoverageVersion
        installed_coverage_version = $installedCoverageVersion
        pytest_exit_code = $pytestExitCode
        pytest_summary = $pytestSummary
        coverage_json_exit_code = $coverageJsonExitCode
        coverage_xml_exit_code = $coverageXmlExitCode
        broad_report_exit_code = $broadReportExitCode
        governed_coverage_exit_code = $governedCoverageExitCode
        coverage_gate_exit_code = $governedCoverageExitCode
        broad_backend_repository_health = [ordered]@{
            statements = $totals.num_statements
            covered_lines = $totals.covered_lines
            missing_lines = $totals.missing_lines
            excluded_lines = $totals.excluded_lines
            percent_covered_exact = $totals.percent_covered
            percent_covered_display = $totals.percent_covered_display
            release_gate = $false
        }
        governed_operational_inclusive = $governedMetric
        threshold_pass = $thresholdPass
        artifact_sha256 = $artifactDigests
        artifacts = @(
            "pytest-complete.log",
            "pytest-junit.xml",
            "coverage-report.txt",
            "coverage.json",
            "coverage.xml",
            "governed-coverage.json",
            "run-metadata.json"
        )
    }

    $metadata | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $metadataPath

    if ($pytestExitCode -ne 0) {
        throw "The authoritative backend pytest suite failed with exit code $pytestExitCode."
    }
    if ($coverageJsonExitCode -ne 0 -or $coverageXmlExitCode -ne 0 -or $broadReportExitCode -ne 0) {
        throw "One or more broad coverage evidence reports failed to generate."
    }
    if ($governedCoverageExitCode -eq 2) {
        throw "Governed coverage boundary integrity evaluation failed. Evidence was retained in $OutputDirectory."
    }
    if ($governedCoverageExitCode -ne 0 -or -not $thresholdPass) {
        throw "Governed operational-inclusive backend coverage is below the unchanged 75% threshold. Evidence was retained in $OutputDirectory."
    }

    Write-Host "Backend coverage evidence passed for exact SHA $sourceSha."
    Write-Host "Broad backend/** coverage retained as non-gating repository-health evidence."
    Write-Host "Governed operational-inclusive application coverage passed the unchanged 75% threshold."
    Write-Host "Evidence directory: $OutputDirectory"
}
finally {
    Pop-Location
}
