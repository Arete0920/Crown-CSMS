param(
    [string]$RepoRoot = (Resolve-Path ".").Path,
    [string]$OutDir = "audit-artifacts/evening-release-truth"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "== $Message =="
}

function Invoke-AndCapture {
    param(
        [string]$Name,
        [string]$Command,
        [string]$OutputPath
    )

    Write-Step $Name
    Write-Host $Command

    $fullOutputPath = Join-Path $RepoRoot $OutputPath
    $parent = Split-Path -Parent $fullOutputPath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    cmd.exe /c $Command *> $fullOutputPath
    $exit = $LASTEXITCODE

    if ($exit -ne 0) {
        Write-Host "FAIL: $Name exited $exit"
        return @{
            name = $Name
            status = "FAIL"
            exitCode = $exit
            output = $OutputPath
        }
    }

    Write-Host "PASS: $Name"
    return @{
        name = $Name
        status = "PASS"
        exitCode = 0
        output = $OutputPath
    }
}

Set-Location $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$artifactDir = Join-Path $OutDir $stamp
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

$gitSha = (git rev-parse HEAD).Trim()
$branch = (git rev-parse --abbrev-ref HEAD).Trim()

$results = @()

$results += Invoke-AndCapture `
    -Name "Git status" `
    -Command "git status --short" `
    -OutputPath "$artifactDir/01_git_status.txt"

$results += Invoke-AndCapture `
    -Name "Release truth keyword scan" `
    -Command "git grep -n \"NO-GO\|MVP\|deferred\|production ready\|FINAL GO\|zero blockers\" -- docs audit-artifacts README.md 2>NUL" `
    -OutputPath "$artifactDir/02_release_truth_keyword_scan.txt"

$results += Invoke-AndCapture `
    -Name "Dashboard completeness guard" `
    -Command "cd frontend\dashboards && npm run verify:dashboard-completeness" `
    -OutputPath "$artifactDir/03_dashboard_completeness_guard.txt"

$results += Invoke-AndCapture `
    -Name "Frontend release verification" `
    -Command "cd frontend\dashboards && npm run test -- --run" `
    -OutputPath "$artifactDir/04_frontend_tests.txt"

$results += Invoke-AndCapture `
    -Name "Backend admissions tests" `
    -Command "cd backend && python -m pytest applications/tests/test_admissions_endpoints.py -q" `
    -OutputPath "$artifactDir/05_backend_admissions_tests.txt"

$summary = @{
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    branch = $branch
    gitSha = $gitSha
    artifactDir = $artifactDir
    results = $results
    passCount = ($results | Where-Object { $_.status -eq "PASS" }).Count
    failCount = ($results | Where-Object { $_.status -eq "FAIL" }).Count
}

$summaryJson = $summary | ConvertTo-Json -Depth 10
$summaryPath = Join-Path $RepoRoot "$artifactDir/00_SUMMARY.json"
$summaryJson | Set-Content -Encoding UTF8 $summaryPath

$md = @()
$md += "# Evening Release Truth Proof - $stamp"
$md += ""
$md += "- Branch: ``$branch``"
$md += "- SHA: ``$gitSha``"
$md += "- PASS: $($summary.passCount)"
$md += "- FAIL: $($summary.failCount)"
$md += ""
$md += "| Check | Status | Output |"
$md += "| --- | --- | --- |"

foreach ($r in $results) {
    $md += "| $($r.name) | $($r.status) | ``$($r.output)`` |"
}

$mdPath = Join-Path $RepoRoot "$artifactDir/00_SUMMARY.md"
$md -join "`r`n" | Set-Content -Encoding UTF8 $mdPath

if ($summary.failCount -gt 0) {
    Write-Host ""
    Write-Host "FINAL STATUS: FAIL"
    Write-Host "Summary: $mdPath"
    exit 1
}

Write-Host ""
Write-Host "FINAL STATUS: PASS"
Write-Host "Summary: $mdPath"
exit 0
