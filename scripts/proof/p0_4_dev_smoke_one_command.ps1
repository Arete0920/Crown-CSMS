#!/usr/bin/env pwsh
<#
.SYNOPSIS
    P0.4: Single-command proof for DEV Smoke - Golden Path
.DESCRIPTION
    Asserts DEV reports expected SHA, triggers smoke workflow, waits for completion, fails if smoke fails.
.PARAMETER ExpectedSHA
    The SHA DEV must report (defaults to local HEAD)
.EXAMPLE
    .\scripts\proof\p0_4_dev_smoke_one_command.ps1
    .\scripts\proof\p0_4_dev_smoke_one_command.ps1 -ExpectedSHA a3ca35c87a903306a6b1d4ea01f993fc3417f1c6
#>
param(
    [string]$ExpectedSHA = ""
)

$ErrorActionPreference = "Stop"

# Define ESC character for reliable ANSI stripping in regex
$esc = [char]27

# Sanity: ensure ANSI stripping pattern works in this shell
$__ansiTest = "hello$esc[32mworld$esc[0m"
$__ansiOut  = $__ansiTest -replace "$esc\[[0-9;]*m", ""
if ($__ansiOut -ne "helloworld") {
    throw "ANSI strip self-test failed; regex not stripping ESC sequences in this environment."
}

$env:GH_PAGER = "cat"
$env:GH_FORCE_TTY = 0

# 1) Determine expected SHA (local HEAD if not provided)
if ([string]::IsNullOrWhiteSpace($ExpectedSHA)) {
    $ExpectedSHA = (git rev-parse HEAD).Trim()
    Write-Host "Using local HEAD as expected SHA: $ExpectedSHA"
} else {
    Write-Host "Using provided expected SHA: $ExpectedSHA"
}

# 2) Assert DEV reports expected SHA
Write-Host "`n=== Step 1: Verify DEV SHA ==="
$base = "https://crown-api-dev.azurewebsites.net"
try {
    $healthJson = curl.exe -s "$base/health/"
    $health = $healthJson | ConvertFrom-Json
    $devSHA = $health.build_sha
    $env = $health.env
    $db = $health.db
    
    Write-Host "DEV /health/ reports:"
    Write-Host "  build_sha: $devSHA"
    Write-Host "  env:       $env"
    Write-Host "  db:        $db"
    
    if ($devSHA -ne $ExpectedSHA) {
        throw "FAILED: DEV reports '$devSHA' but expected '$ExpectedSHA'"
    }
    Write-Host "✅ DEV SHA matches expected: $ExpectedSHA"
} catch {
    Write-Host "❌ Failed to verify DEV SHA: $_"
    exit 1
}

# 3) Trigger DEV Smoke - Golden Path workflow
Write-Host "`n=== Step 2: Trigger DEV Smoke Workflow ==="
$workflowName = "DEV Smoke - Golden Path"
$repo = "tcmegahan/Crown2026"

$env:GH_PAGER = "cat"
$env:GH_FORCE_TTY = 0

# Capture a trigger timestamp to avoid grabbing someone else's run
$triggeredAtUtc = [DateTime]::UtcNow
Write-Host ("Trigger time (UTC): {0:o}" -f $triggeredAtUtc)

Write-Host "Triggering workflow: $workflowName"
# NOTE: gh workflow run does NOT support --json
gh workflow run "$workflowName" -R $repo | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to trigger workflow"
    exit 1
}

# Wait for run to appear (GitHub may take a few seconds)
Write-Host "Waiting for run to appear..."
Start-Sleep -Seconds 5

# 4) Locate the triggered run (clean JSON via gh run list)
Write-Host "Locating the triggered run..."

$runsRaw = & gh run list -R $repo --workflow "$workflowName" --limit 5 --json databaseId,status,conclusion,createdAt,url 2>$null
# Join in case PowerShell returns an array of lines
$runsJson = ($runsRaw -join "`n")

# Strip ANSI escape codes (some gh builds still emit them)
$runsJson = $runsJson -replace "$esc\[[0-9;]*m", ""

# Also strip stray '.' lines if present (defensive; seen in your environment)
$runsJson = ($runsJson -split "`n" | Where-Object { $_.Trim() -ne "." }) -join "`n"

if (-not $runsJson) { throw "gh run list returned empty output" }

$runs = $runsJson | ConvertFrom-Json

# Pick the first run created after trigger time
$run = $runs | Where-Object {
  [DateTime]::Parse($_.createdAt).ToUniversalTime() -ge $triggeredAtUtc.AddSeconds(-2)
} | Select-Object -First 1

if (-not $run) {
  throw "Could not find a workflow run created after trigger time"
}

$runId  = $run.databaseId
$runUrl = $run.url

Write-Host "✅ Workflow run detected:"
Write-Host "   Run ID:  $runId"
Write-Host "   Run URL: $runUrl"

# 5) Poll for completion
Write-Host "`n=== Step 3: Wait for Completion ==="
$maxPolls = 60  # 10 minutes max (60 * 10s)
$pollCount = 0

while ($pollCount -lt $maxPolls) {
    $pollCount++

    $viewRaw  = & gh run view $runId -R $repo --json status,conclusion,url 2>$null
    $viewJson = ($viewRaw -join "`n")
    $viewJson = $viewJson -replace "$esc\[[0-9;]*m", ""
    $viewJson = ($viewJson -split "`n" | Where-Object { $_.Trim() -ne "." }) -join "`n"

    $currentRun = $viewJson | ConvertFrom-Json
    $status = $currentRun.status
    $conclusion = $currentRun.conclusion
    $url = $currentRun.url

    Write-Host ("[{0:00}] Status: {1,-15} Conclusion: {2}" -f $pollCount, $status, $(if ($conclusion) { $conclusion } else { "pending" }))

    if ($status -eq "completed") {
        Write-Host "`n=== Final Result ==="
        Write-Host "Run URL: $url"
        Write-Host "Status: $status"
        Write-Host "Conclusion: $conclusion"

        if ($conclusion -eq "success") {
            Write-Host "✅ P0.4 CLOSED: DEV Smoke passed on SHA $ExpectedSHA"
            exit 0
        } else {
            Write-Host "❌ FAILED: DEV Smoke concluded with '$conclusion'"
            Write-Host "View logs: $url"
            exit 1
        }
    }

    Start-Sleep -Seconds 10
}

# Timeout
Write-Host "❌ TIMEOUT: Workflow did not complete within $($maxPolls * 10) seconds"
Write-Host "View run: $runUrl"
exit 1
