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

# 4) Find the run we just triggered (first run created after our trigger time)
Write-Host "Locating the triggered run..."
$maxFindPolls = 12   # ~60s max (12 * 5s)
$findPoll = 0
$run = $null

while ($findPoll -lt $maxFindPolls -and -not $run) {
    $findPoll++

    # Use gh api for strict JSON; avoids stdout contamination from gh run list in some environments.
    $repoApi = "repos/$repo/actions/runs"
    
    # Fetch 20 recent runs and filter locally; keep it simple and deterministic.
    $runsJson = & gh api $repoApi -f per_page=20 2>$null
    
    if (-not $runsJson -or $runsJson.Trim().Length -lt 2) {
        Write-Host "❌ gh api returned empty output"
        exit 1
    }
    
    try {
        $runsObj = $runsJson | ConvertFrom-Json
        $runs = $runsObj.workflow_runs
        
        # Filter to our workflow name, then pick the first created after trigger time
        $runs = $runs | Where-Object { $_.name -eq $workflowName }
        
        foreach ($r in $runs) {
            # created_at is ISO 8601; parse to UTC
            $created = [DateTime]::Parse($r.created_at).ToUniversalTime()
            if ($created -ge $triggeredAtUtc.AddSeconds(-2)) {
                $run = $r
                break
            }
        }
    } catch {
        $runsJson | Out-File -Encoding utf8 "$env:TEMP\p0_4_runs_raw.txt"
        Write-Host "❌ JSON parse failed. Wrote raw gh output to $env:TEMP\p0_4_runs_raw.txt"
        throw
    }

    if (-not $run) {
        Write-Host ("[{0:00}] Run not visible yet; retrying..." -f $findPoll)
        Start-Sleep -Seconds 5
    }
}

if (-not $run) {
    Write-Host "❌ Could not find the workflow run created after trigger time."
    exit 1
}

$runId  = $run.id
$runUrl = $run.html_url

Write-Host "✅ Workflow run detected: $runUrl"
Write-Host "   Run ID: $runId"

# 5) Poll for completion
Write-Host "`n=== Step 3: Wait for Completion ==="
$maxPolls = 60  # 10 minutes max (60 * 10s)
$pollCount = 0

while ($pollCount -lt $maxPolls) {
    $pollCount++

    $viewJson = & gh run view $runId -R $repo --json status,conclusion,url 2>$null
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
