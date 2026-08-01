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
    $metadataPath = Join-Path $resolvedOutputDirectory "run-metadata.json"

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

    # Generate machine-readable reports even when the configured 75% threshold is not met.
    & python -m coverage json --rcfile=.coveragerc --fail-under=0 -o $coverageJson
    $coverageJsonExitCode = $LASTEXITCODE
    & python -m coverage xml --rcfile=.coveragerc --fail-under=0 -o $coverageXml
    $coverageXmlExitCode = $LASTEXITCODE
    & python -m coverage report --rcfile=.coveragerc *>&1 |
        Tee-Object -FilePath $coverageText
    $coverageGateExitCode = $LASTEXITCODE

    if (-not (Test-Path $coverageJson)) {
        throw "Coverage JSON was not generated."
    }

    $coverageData = Get-Content -Raw $coverageJson | ConvertFrom-Json
    $totals = $coverageData.totals
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
    foreach ($artifactPath in @($pytestLog, $pytestJunit, $coverageText, $coverageJson, $coverageXml)) {
        if (Test-Path $artifactPath) {
            $artifactDigests[(Split-Path $artifactPath -Leaf)] = (Get-FileHash -Algorithm SHA256 $artifactPath).Hash.ToLowerInvariant()
        }
    }

    $metadata = [ordered]@{
        schema_version = 1
        generated_at_utc = $completedAt
        repository = "tcmegahan/Crown2026"
        source_sha = $sourceSha
        worktree_clean_before_run = $true
        runner = "scripts/release/run_backend_coverage.ps1"
        test_command = "python -m coverage run --rcfile=.coveragerc -m pytest -q backend --junitxml=<artifact-path>"
        coverage_config = ".coveragerc"
        coverage_threshold_percent = 75
        python_version = $pythonVersion
        pytest_version = $pytestVersion
        requested_coverage_version = $CoverageVersion
        installed_coverage_version = $installedCoverageVersion
        pytest_exit_code = $pytestExitCode
        pytest_summary = $pytestSummary
        coverage_json_exit_code = $coverageJsonExitCode
        coverage_xml_exit_code = $coverageXmlExitCode
        coverage_gate_exit_code = $coverageGateExitCode
        statements = $totals.num_statements
        covered_lines = $totals.covered_lines
        missing_lines = $totals.missing_lines
        excluded_lines = $totals.excluded_lines
        percent_covered_exact = $totals.percent_covered
        percent_covered_display = $totals.percent_covered_display
        threshold_pass = ($coverageGateExitCode -eq 0)
        artifact_sha256 = $artifactDigests
        artifacts = @(
            "pytest-complete.log",
            "pytest-junit.xml",
            "coverage-report.txt",
            "coverage.json",
            "coverage.xml",
            "run-metadata.json"
        )
    }

    $metadata | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $metadataPath

    if ($pytestExitCode -ne 0) {
        throw "The authoritative backend pytest suite failed with exit code $pytestExitCode."
    }
    if ($coverageJsonExitCode -ne 0 -or $coverageXmlExitCode -ne 0) {
        throw "One or more machine-readable coverage reports failed to generate."
    }
    if ($coverageGateExitCode -ne 0) {
        throw "Coverage is below the configured 75% threshold. Evidence was retained in $OutputDirectory."
    }

    Write-Host "Backend coverage evidence passed for exact SHA $sourceSha."
    Write-Host "Evidence directory: $OutputDirectory"
}
finally {
    Pop-Location
}
