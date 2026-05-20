#Requires -Version 5.1
<#
.SYNOPSIS
    Crown Release Closeout Proof Gate

.DESCRIPTION
    Fail-closed gate that must return GO-READY before any production release decision.
    No skip flags. No bypass modes. Any FAIL blocks GO-READY.

    Checks:
      1.  Branch must be main
      2.  Working tree must be clean
      3.  HEAD must match origin/main
      4.  Required release-authority files present
      5.  No open PRs (backlog cleared)
      6.  No open issues
      7.  django check clean
      8.  django makemigrations --check --dry-run clean
      9.  Frontend build passes
      10. Frontend verify:full passes
      11. Production /api/health/ reachable and healthy
      12. Production build_sha matches HEAD (hard FAIL — no skip)
      13. Release authority hold resolved
          (INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md must not contain "State: INTEGRITY HOLD")
      14. Founder acceptance signed
          (docs/release/FOUNDER_ACCEPTANCE.md must exist and contain "SIGNED")
#>

$ErrorActionPreference = "Stop"

$RunId   = Get-Date -Format "yyyyMMdd-HHmmss"
$RunDir  = "audit-artifacts/release-closeout-proof/$RunId"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$Gates = [System.Collections.Generic.List[object]]::new()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Add-Gate {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][ValidateSet("PASS","FAIL")][string]$Status,
        [Parameter(Mandatory)][string]$Detail,
        [string]$Artifact = ""
    )
    $Gates.Add([pscustomobject]@{
        name     = $Name
        status   = $Status
        detail   = $Detail
        artifact = $Artifact
    }) | Out-Null
}

function Write-ArtifactText {
    param(
        [Parameter(Mandatory)][string]$Path,
        [AllowNull()][object]$Value
    )
    $text   = if ($null -eq $Value) { "" } else { [string]$Value }
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $text | Out-File $Path -Encoding UTF8
}

function Invoke-GateCommand {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FileName,
        [string[]]$Arguments       = @(),
        [int]    $TimeoutSeconds   = 600
    )

    $safe   = $Name.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    $stdout = Join-Path $RunDir "$safe.stdout.txt"
    $stderr = Join-Path $RunDir "$safe.stderr.txt"

    try {
        $resolved = Get-Command "$FileName.exe","$FileName.cmd","$FileName.bat",$FileName `
                        -ErrorAction SilentlyContinue | Select-Object -First 1

        if (-not $resolved) {
            Write-ArtifactText -Path $stderr -Value "Required command not found: $FileName"
            Add-Gate -Name $Name -Status "FAIL" `
                     -Detail "Required command not found: $FileName" -Artifact $stderr
            return
        }

        $exePath = if ($resolved.Path) { $resolved.Path } else { $resolved.Source }
        if ([string]::IsNullOrWhiteSpace($exePath)) {
            Write-ArtifactText -Path $stderr -Value "Cannot resolve path for: $FileName"
            Add-Gate -Name $Name -Status "FAIL" `
                     -Detail "Cannot resolve path for: $FileName" -Artifact $stderr
            return
        }

        $argList = @($Arguments | Where-Object { $null -ne $_ } | ForEach-Object { [string]$_ })
        $proc    = Start-Process -FilePath $exePath -ArgumentList $argList `
                       -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
                       -NoNewWindow -PassThru

        if (-not $proc) {
            Write-ArtifactText -Path $stderr -Value "Failed to start: $FileName"
            Add-Gate -Name $Name -Status "FAIL" -Detail "Failed to start: $FileName" -Artifact $stderr
            return
        }

        $timedOut = $false
        try   { Wait-Process -Id $proc.Id -Timeout $TimeoutSeconds -ErrorAction Stop }
        catch { $timedOut = $true }

        if ($timedOut) {
            try { $proc.Kill($true) } catch {}
            Write-ArtifactText -Path $stderr -Value "TIMEOUT after $TimeoutSeconds seconds"
            Add-Gate -Name $Name -Status "FAIL" `
                     -Detail "Timed out after $TimeoutSeconds seconds" -Artifact $stderr
            return
        }

        $proc.Refresh()
        $exitCode = [int]$proc.ExitCode   # explicit cast — unknown values become non-zero

        if ($exitCode -eq 0) {
            Add-Gate -Name $Name -Status "PASS" `
                     -Detail "$FileName $($argList -join ' ') exited 0" -Artifact $stdout
        } else {
            Add-Gate -Name $Name -Status "FAIL" `
                     -Detail "$FileName $($argList -join ' ') exited $exitCode" -Artifact $stderr
        }
    }
    catch {
        $msg = if ($_.Exception -and $_.Exception.Message) { $_.Exception.Message } else { "Unknown error" }
        Write-ArtifactText -Path $stderr -Value $msg
        Add-Gate -Name $Name -Status "FAIL" -Detail $msg -Artifact $stderr
    }
}

# ---------------------------------------------------------------------------
# Gate 1 — Branch
# ---------------------------------------------------------------------------

$branch = (git branch --show-current 2>$null).Trim()
$head   = (git rev-parse HEAD 2>$null).Trim()

if ($branch -eq "main") {
    Add-Gate -Name "release branch" -Status "PASS" -Detail "Running on main"
} else {
    Add-Gate -Name "release branch" -Status "FAIL" `
             -Detail "Must run from main. Current branch: $branch"
}

git status --short | Out-File (Join-Path $RunDir "git-status-short.txt") -Encoding UTF8
git log --oneline -n 10 | Out-File (Join-Path $RunDir "git-log-latest-10.txt") -Encoding UTF8

# ---------------------------------------------------------------------------
# Gate 2 — Working tree clean
# ---------------------------------------------------------------------------

$dirty = git status --short
if ([string]::IsNullOrWhiteSpace($dirty)) {
    Add-Gate -Name "working tree clean" -Status "PASS" -Detail "No uncommitted changes"
} else {
    Add-Gate -Name "working tree clean" -Status "FAIL" `
             -Detail "Working tree has uncommitted changes" `
             -Artifact (Join-Path $RunDir "git-status-short.txt")
}

# ---------------------------------------------------------------------------
# Gate 3 — main sync
# ---------------------------------------------------------------------------

$originMain = ""
try {
    $originMain = (git rev-parse origin/main).Trim()
    $syncCounts = (git rev-list --left-right --count HEAD...origin/main 2>$null).Trim()
    if ($syncCounts -notmatch '^\d+\s+\d+$') {
        Add-Gate -Name "main sync" -Status "FAIL" -Detail "Unable to compute ahead/behind counts vs origin/main"
    }
    else {
        $parts  = $syncCounts -split '\s+'
        $ahead  = [int]$parts[0]
        $behind = [int]$parts[1]
        if ($ahead -eq 0 -and $behind -eq 0) {
            Add-Gate -Name "main sync" -Status "PASS" -Detail "HEAD matches origin/main: $head"
        } else {
            Add-Gate -Name "main sync" -Status "FAIL" -Detail "Branch diverged from origin/main (ahead=$ahead, behind=$behind)"
        }
    }
}
catch {
    Add-Gate -Name "main sync" -Status "FAIL" -Detail $_.Exception.Message
}

# ---------------------------------------------------------------------------
# Gate 4 — Required release-authority files
# ---------------------------------------------------------------------------

$requiredFiles = @(
    "docs/testing/crown-test-inventory.json",
    "scripts/testing/check-crown-test-inventory.mjs",
    "scripts/testing/check-crown-discovered-surface-coverage.mjs",
    "scripts/testing/crown-surface-discovery.mjs",
    "docs/KNOWN_LIMITATIONS.md",
    "docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md",
    "docs/release/README.md"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Add-Gate -Name "required file: $file" -Status "PASS" -Detail "Present"
    } else {
        Add-Gate -Name "required file: $file" -Status "FAIL" -Detail "Missing required release file"
    }
}

# ---------------------------------------------------------------------------
# Gate 5 — Release authority hold resolved
#          The INTEGRITY HOLD must have been formally lifted before GO-READY.
# ---------------------------------------------------------------------------

$authorityFile = "docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md"
if (Test-Path $authorityFile) {
    $authorityContent = Get-Content -Raw $authorityFile
    if ($authorityContent -match "State:\s*INTEGRITY HOLD") {
        Add-Gate -Name "release authority hold" -Status "FAIL" `
                 -Detail "INTEGRITY HOLD is still active in $authorityFile" `
                 -Artifact $authorityFile
    } else {
        Add-Gate -Name "release authority hold" -Status "PASS" `
                 -Detail "Integrity hold lifted"
    }
} else {
    Add-Gate -Name "release authority hold" -Status "FAIL" `
             -Detail "$authorityFile is missing"
}

# ---------------------------------------------------------------------------
# Gate 6 - Founder acceptance signed
# ---------------------------------------------------------------------------

$founderFile = "docs/release/FOUNDER_ACCEPTANCE.md"
if (Test-Path $founderFile) {
    $founderContent = Get-Content -Raw $founderFile
    if ($founderContent -match "SIGNED") {
        Add-Gate -Name "founder acceptance" -Status "PASS" -Detail "Founder acceptance signed"
    } else {
        Add-Gate -Name "founder acceptance" -Status "FAIL" -Detail "$founderFile exists but does not contain SIGNED"
    }
} else {
    Add-Gate -Name "founder acceptance" -Status "FAIL" -Detail "$founderFile missing - founder acceptance not on record"
}

# ---------------------------------------------------------------------------
# Gate 7 — Crown test inventory
# ---------------------------------------------------------------------------

Invoke-GateCommand `
    -Name "crown test inventory" `
    -FileName "node" `
    -Arguments @("scripts/testing/check-crown-test-inventory.mjs") `
    -TimeoutSeconds 300

# ---------------------------------------------------------------------------
# Gate 8 — Crown discovered surface coverage
# ---------------------------------------------------------------------------

Invoke-GateCommand `
    -Name "crown discovered surface coverage" `
    -FileName "node" `
    -Arguments @("scripts/testing/check-crown-discovered-surface-coverage.mjs") `
    -TimeoutSeconds 300

# ---------------------------------------------------------------------------
# Gates 9–10 — Backend
# ---------------------------------------------------------------------------

if (Test-Path "backend/manage.py") {
    Invoke-GateCommand `
        -Name "django check" `
        -FileName "python" `
        -Arguments @("backend/manage.py", "check") `
        -TimeoutSeconds 600

    Invoke-GateCommand `
        -Name "django migrations dry run" `
        -FileName "python" `
        -Arguments @("backend/manage.py", "makemigrations", "--check", "--dry-run") `
        -TimeoutSeconds 600
} else {
    Add-Gate -Name "backend manage.py" -Status "FAIL" -Detail "backend/manage.py missing"
}

# ---------------------------------------------------------------------------
# Gates 11–12 — Frontend
# ---------------------------------------------------------------------------

if (Test-Path "frontend/dashboards/package.json") {
    Invoke-GateCommand `
        -Name "frontend build" `
        -FileName "npm" `
        -Arguments @("--prefix", "frontend/dashboards", "run", "build") `
        -TimeoutSeconds 1200

    $pkg = Get-Content -Raw "frontend/dashboards/package.json"
    if ($pkg -match '"verify:full"') {
        Invoke-GateCommand `
            -Name "frontend verify full" `
            -FileName "npm" `
            -Arguments @("--prefix", "frontend/dashboards", "run", "verify:full") `
            -TimeoutSeconds 1800
    } else {
        Add-Gate -Name "frontend verify full" -Status "FAIL" `
                 -Detail "frontend/dashboards/package.json missing verify:full script"
    }
} else {
    Add-Gate -Name "frontend package" -Status "FAIL" `
             -Detail "frontend/dashboards/package.json missing"
}

# ---------------------------------------------------------------------------
# Gate 13 — GitHub backlog
# ---------------------------------------------------------------------------

if (Get-Command gh -ErrorAction SilentlyContinue) {
    try {
        gh pr    list --state open --json number,title,headRefName,url |
            Out-File (Join-Path $RunDir "open-prs.json") -Encoding UTF8
        gh issue list --state open --json number,title,url |
            Out-File (Join-Path $RunDir "open-issues.json") -Encoding UTF8

        $openPrs    = Get-Content -Raw (Join-Path $RunDir "open-prs.json")    | ConvertFrom-Json
        $openIssues = Get-Content -Raw (Join-Path $RunDir "open-issues.json") | ConvertFrom-Json

        if (@($openPrs).Count -eq 0) {
            Add-Gate -Name "open PR backlog" -Status "PASS" -Detail "No open PRs"
        } else {
            Add-Gate -Name "open PR backlog" -Status "FAIL" `
                     -Detail "$(@($openPrs).Count) open PR(s)" `
                     -Artifact (Join-Path $RunDir "open-prs.json")
        }

        if (@($openIssues).Count -eq 0) {
            Add-Gate -Name "open issue backlog" -Status "PASS" -Detail "No open issues"
        } else {
            Add-Gate -Name "open issue backlog" -Status "FAIL" `
                     -Detail "$(@($openIssues).Count) open issue(s)" `
                     -Artifact (Join-Path $RunDir "open-issues.json")
        }
    }
    catch {
        Add-Gate -Name "github backlog scan" -Status "FAIL" -Detail $_.Exception.Message
    }
} else {
    Add-Gate -Name "github cli" -Status "FAIL" -Detail "gh CLI not available"
}

# ---------------------------------------------------------------------------
# Gates 14–16 — Production probe (MANDATORY — no skip flag)
# ---------------------------------------------------------------------------

try {
    $health = Invoke-RestMethod "https://crown-api-prod.azurewebsites.net/api/health/" `
                  -TimeoutSec 30
    $health | ConvertTo-Json -Depth 20 |
        Out-File (Join-Path $RunDir "prod-health.json") -Encoding UTF8

    # 14. Production health
    if ($health.status -eq "ok" -or $health.ok -eq $true) {
        Add-Gate -Name "production health" -Status "PASS" -Detail "Production reports ok"
    } else {
        Add-Gate -Name "production health" -Status "FAIL" `
                 -Detail "Production health did not report ok" `
                 -Artifact (Join-Path $RunDir "prod-health.json")
    }

    # 15. Production database
    if ($health.db -eq "ok") {
        Add-Gate -Name "production database" -Status "PASS" -Detail "Production DB reports ok"
    } else {
        Add-Gate -Name "production database" -Status "FAIL" `
                 -Detail "Production DB did not report ok" `
                 -Artifact (Join-Path $RunDir "prod-health.json")
    }

    # 16. Production build_sha — hard FAIL, no skip, no WARN path
    if ($health.build_sha -and ($health.build_sha -eq $head)) {
        Add-Gate -Name "production currentness" -Status "PASS" `
                 -Detail "Production build_sha matches HEAD: $head" `
                 -Artifact (Join-Path $RunDir "prod-health.json")
    } else {
        $prodSha = if ($health.build_sha) { $health.build_sha } else { "(missing)" }
        Add-Gate -Name "production currentness" -Status "FAIL" `
                 -Detail "Production build_sha '$prodSha' does not match HEAD '$head'. Deploy required before release." `
                 -Artifact (Join-Path $RunDir "prod-health.json")
    }
}
catch {
    Add-Gate -Name "production probe" -Status "FAIL" `
             -Detail "Production probe failed: $($_.Exception.Message)"
}

# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------

$failCount = @($Gates | Where-Object { $_.status -eq "FAIL" }).Count
$passCount = @($Gates | Where-Object { $_.status -eq "PASS" }).Count

# Fail-closed: GO-READY requires zero failures.
$decision = if ($failCount -eq 0) { "GO-READY" } else { "NO-GO" }

$scorecard = [pscustomobject]@{
    run_id      = $RunId
    decision    = $decision
    branch      = $branch
    head        = $head
    origin_main = $originMain
    pass        = $passCount
    fail        = $failCount
    gates       = $Gates
}

$jsonPath = Join-Path $RunDir "release-closeout-scorecard.json"
$mdPath   = Join-Path $RunDir "release-closeout-scorecard.md"

$scorecard | ConvertTo-Json -Depth 20 | Out-File $jsonPath -Encoding UTF8

$md  = @()
$md += "# Crown Release Closeout Proof Gate"
$md += ""
$md += "- Run ID  : $RunId"
$md += "- Decision: **$decision**"
$md += "- Branch  : $branch"
$md += "- HEAD    : $head"
$md += "- PASS    : $passCount"
$md += "- FAIL    : $failCount"
$md += ""
$md += "## Gates"
$md += ""

foreach ($g in $Gates) {
    $md += "- **$($g.status)** - $($g.name): $($g.detail)"
}

$md -join "`n" | Out-File $mdPath -Encoding UTF8

Write-Host ""
Write-Host "Decision: $decision"
Write-Host "PASS: $passCount  FAIL: $failCount"
Write-Host "Scorecard: $mdPath"
Write-Host ""

if ($failCount -gt 0) { exit 1 }
exit 0
