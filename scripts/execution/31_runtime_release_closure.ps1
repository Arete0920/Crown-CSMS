param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$StartLocalServer
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Path, [string]$Title)
    "=== $Title ===" | Set-Content -Path $Path -Encoding utf8
}

function Add-CommandOutput {
    param([string]$Path, [scriptblock]$Command)
    try {
        & $Command 2>&1 | Out-File -FilePath $Path -Append -Encoding utf8
    }
    catch {
        ($_ | Out-String) | Out-File -FilePath $Path -Append -Encoding utf8
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

# Ensure local runtime commands have a non-empty secret for settings bootstrap.
if (-not $env:DJANGO_SECRET_KEY -and -not $env:SECRET_KEY) {
    $env:DJANGO_SECRET_KEY = "local-dev-runtime-closure-key-abcdefghijklmnopqrstuvwxyz-123456"
    $env:SECRET_KEY = $env:DJANGO_SECRET_KEY
}
elseif (-not $env:DJANGO_SECRET_KEY -and $env:SECRET_KEY) {
    $env:DJANGO_SECRET_KEY = $env:SECRET_KEY
}
elseif (-not $env:SECRET_KEY -and $env:DJANGO_SECRET_KEY) {
    $env:SECRET_KEY = $env:DJANGO_SECRET_KEY
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $repoRoot ("audit-artifacts\runtime-release-closure\" + $ts)
New-Item -ItemType Directory -Force -Path $out | Out-Null

$serverJob = $null
$serverLog = Join-Path $out "00_runserver.log"

if ($StartLocalServer) {
    $python = "python"
    $manage = Join-Path $repoRoot "backend\manage.py"
    if (Test-Path $manage) {
        $serverJob = Start-Process -FilePath powershell -ArgumentList @(
            "-NoProfile",
            "-Command",
            "Set-Location `"$repoRoot`"; $python backend\manage.py runserver 127.0.0.1:8000 --noreload *> `"$serverLog`""
        ) -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 12
    }
}

Write-Section (Join-Path $out "01_repo_state.txt") "Repo state"
Add-CommandOutput (Join-Path $out "01_repo_state.txt") { git status --short --branch }
Add-CommandOutput (Join-Path $out "01_repo_state.txt") { git rev-parse HEAD }
Add-CommandOutput (Join-Path $out "01_repo_state.txt") { git branch --show-current }

Write-Section (Join-Path $out "02_python_version.txt") "Python version"
Add-CommandOutput (Join-Path $out "02_python_version.txt") { python --version }

Write-Section (Join-Path $out "03_django_check.txt") "Django check"
Add-CommandOutput (Join-Path $out "03_django_check.txt") { python backend\manage.py check }

Write-Section (Join-Path $out "04_showmigrations.txt") "Showmigrations"
Add-CommandOutput (Join-Path $out "04_showmigrations.txt") { python backend\manage.py showmigrations }

Write-Section (Join-Path $out "05_deploy_check.txt") "Deploy check"
$deployEnvNames = @("CROWN_ENV", "DJANGO_ENV", "DJANGO_DEBUG", "DEBUG", "DATABASE_URL")
$deployEnvBackup = @{}
foreach ($name in $deployEnvNames) {
    $deployEnvBackup[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    $env:CROWN_ENV = "prod"
    $env:DJANGO_ENV = "prod"
    $env:DJANGO_DEBUG = "0"
    $env:DEBUG = "0"
    if (-not $env:DATABASE_URL) {
        $sqlitePath = (Join-Path $repoRoot "backend\db.sqlite3") -replace "\\", "/"
        $env:DATABASE_URL = "sqlite:///$sqlitePath"
    }
    Add-CommandOutput (Join-Path $out "05_deploy_check.txt") { python backend\manage.py check --deploy --tag security }
}
finally {
    foreach ($name in $deployEnvNames) {
        [Environment]::SetEnvironmentVariable($name, $deployEnvBackup[$name], "Process")
    }
}

Write-Section (Join-Path $out "06_health_endpoint.txt") "Health endpoint"
Add-CommandOutput (Join-Path $out "06_health_endpoint.txt") {
    try {
        Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/health/") -Method Get -TimeoutSec 20 | ConvertTo-Json -Depth 20
    }
    catch {
        $_ | Out-String
    }
}

Write-Section (Join-Path $out "07_integrity_endpoint.txt") "Integrity endpoint"
Add-CommandOutput (Join-Path $out "07_integrity_endpoint.txt") {
    try {
        Invoke-RestMethod -Uri ($BaseUrl.TrimEnd("/") + "/api/integrity/") -Method Get -TimeoutSec 20 | ConvertTo-Json -Depth 20
    }
    catch {
        $_ | Out-String
    }
}

Write-Section (Join-Path $out "08_required_checks.txt") "Required checks"
Add-CommandOutput (Join-Path $out "08_required_checks.txt") {
    gh api repos/tcmegahan/Crown2026/branches/main/protection --jq '.required_status_checks.contexts'
}

Write-Section (Join-Path $out "09_main_runs.txt") "Latest main runs"
Add-CommandOutput (Join-Path $out "09_main_runs.txt") {
    gh run list --branch main --limit 20 --json workflowName, status, conclusion, createdAt, displayTitle --jq '.[] | {workflow:.workflowName,status,conclusion,createdAt,title:.displayTitle}'
}

Write-Section (Join-Path $out "10_legacy_workflow_inventory.txt") "Legacy workflow inventory"
$wf = Get-ChildItem ".github\workflows" -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in ".yml", ".yaml" }
if ($wf) {
    $wf.FullName | Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt")
    foreach ($p in @("ci.yml", "dev-smoke.yml", "deploy-dev.yml", "prod-health-watch.yml")) {
        Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt") ""
        Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt") ("===== " + $p + " =====")
        $match = $wf | Where-Object { $_.Name -eq $p }
        if ($match) {
            $match.FullName | Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt")
        }
        else {
            "MISSING" | Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt")
        }
    }
}
else {
    "No workflow files found." | Add-Content (Join-Path $out "10_legacy_workflow_inventory.txt")
}

$summary = @()
$summary += "# Runtime Release Closure"
$summary += ""
$summary += "- Output root: $out"
$summary += "- Base URL: $BaseUrl"
$summary += "- Local server started by script: $($StartLocalServer.IsPresent)"
$summary += ""
$summary += "## Review files"
$summary += "- 03_django_check.txt"
$summary += "- 04_showmigrations.txt"
$summary += "- 05_deploy_check.txt"
$summary += "- 06_health_endpoint.txt"
$summary += "- 07_integrity_endpoint.txt"
$summary += "- 08_required_checks.txt"
$summary += "- 09_main_runs.txt"
$summary += "- 10_legacy_workflow_inventory.txt"
$summary += ""
$summary += "## Required next action"
$summary += "- Fix every non-green item and rerun this script until all runtime files are clean."

$summary -join "`r`n" | Set-Content (Join-Path $out "SUMMARY.md") -Encoding utf8

if ($serverJob) {
    try {
        Stop-Process -Id $serverJob.Id -Force -ErrorAction SilentlyContinue
    }
    catch {}
}

Write-Host "Done: $out"
