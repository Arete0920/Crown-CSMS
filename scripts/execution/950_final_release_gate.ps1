param(
    [switch]$SkipProductionProbe
)

$ErrorActionPreference = "Stop"

$RunId = Get-Date -Format "yyyyMMdd-HHmmss"
$RunDir = "audit-artifacts/final-release-gate/$RunId"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$Gates = New-Object System.Collections.Generic.List[object]

function Add-Gate {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][ValidateSet("PASS","FAIL","WARN")][string]$Status,
        [Parameter(Mandatory = $true)][string]$Detail,
        [string]$Artifact = ""
    )

    $Gates.Add([pscustomobject]@{
        name = $Name
        status = $Status
        detail = $Detail
        artifact = $Artifact
    }) | Out-Null
}

function Write-ArtifactText {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowNull()][object]$Value
    )

    $Text = if ($null -eq $Value) { "" } else { [string]$Value }
    $Parent = Split-Path -Parent $Path
    if ($Parent -and -not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    $Text | Out-File $Path -Encoding UTF8
}

function Invoke-GateCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FileName,
        [string[]]$Arguments = @(),
        [int]$TimeoutSeconds = 600
    )

    $SafeName = $Name.ToLowerInvariant() -replace '[^a-z0-9]+','-'
    $StdoutPath = Join-Path $RunDir "$SafeName.stdout.txt"
    $StderrPath = Join-Path $RunDir "$SafeName.stderr.txt"
    $MetaPath = Join-Path $RunDir "$SafeName.meta.json"

    try {
        if ([string]::IsNullOrWhiteSpace($FileName)) {
            Write-ArtifactText -Path $StderrPath -Value "No executable specified."
            Add-Gate -Name $Name -Status "FAIL" -Detail "No executable specified." -Artifact $StderrPath
            return
        }

        $Candidates = @(
            "$FileName.exe",
            "$FileName.cmd",
            "$FileName.bat",
            $FileName
        )
        $Resolved = $null
        foreach ($Candidate in $Candidates) {
            $Resolved = Get-Command $Candidate -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($Resolved) {
                break
            }
        }
        if (-not $Resolved) {
            Write-ArtifactText -Path $StderrPath -Value "Required command not found: $FileName"
            Add-Gate -Name $Name -Status "FAIL" -Detail "Required command not found: $FileName" -Artifact $StderrPath
            return
        }

        $ResolvedPath = $null
        if ($Resolved.Path) {
            $ResolvedPath = $Resolved.Path
        } elseif ($Resolved.Source) {
            $ResolvedPath = $Resolved.Source
        }

        if ([string]::IsNullOrWhiteSpace($ResolvedPath)) {
            Write-ArtifactText -Path $StderrPath -Value "Unable to resolve executable path for: $FileName"
            Add-Gate -Name $Name -Status "FAIL" -Detail "Unable to resolve executable path for: $FileName" -Artifact $StderrPath
            return
        }

        $ArgList = @()
        foreach ($Arg in @($Arguments)) {
            if ($null -ne $Arg) {
                $ArgList += [string]$Arg
            }
        }

        $proc = Start-Process -FilePath $ResolvedPath -ArgumentList $ArgList -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath -NoNewWindow -PassThru

        if (-not $proc) {
            Write-ArtifactText -Path $StderrPath -Value "Failed to start command: $FileName"
            Add-Gate -Name $Name -Status "FAIL" -Detail "Failed to start command: $FileName" -Artifact $StderrPath
            return
        }

        $TimedOut = $false
        try {
            Wait-Process -Id $proc.Id -Timeout $TimeoutSeconds -ErrorAction Stop
        }
        catch {
            $TimedOut = $true
        }

        if ($TimedOut) {
            try { $proc.Kill($true) } catch {}
            Write-ArtifactText -Path $StderrPath -Value "TIMEOUT after $TimeoutSeconds seconds"
            Add-Gate -Name $Name -Status "FAIL" -Detail "Timed out after $TimeoutSeconds seconds" -Artifact $StderrPath
            return
        }

        $proc.Refresh()
        $Stdout = if (Test-Path $StdoutPath) { Get-Content -Raw $StdoutPath } else { "" }
        $Stderr = if (Test-Path $StderrPath) { Get-Content -Raw $StderrPath } else { "" }
        $ExitCode = [int]$proc.ExitCode

        Write-ArtifactText -Path $StdoutPath -Value $Stdout
        Write-ArtifactText -Path $StderrPath -Value $Stderr

        $CommandLine = "$FileName $(@($Arguments) -join ' ')"

        [pscustomobject]@{
            name = $Name
            command = $CommandLine
            executable = $ResolvedPath
            exit_code = $ExitCode
            timeout_seconds = $TimeoutSeconds
            stdout = $StdoutPath
            stderr = $StderrPath
        } | ConvertTo-Json -Depth 10 | Out-File $MetaPath -Encoding UTF8

        if ($ExitCode -eq 0) {
            Add-Gate -Name $Name -Status "PASS" -Detail "$CommandLine exited 0" -Artifact $StdoutPath
        } else {
            Add-Gate -Name $Name -Status "FAIL" -Detail "$CommandLine exited $ExitCode" -Artifact $StderrPath
        }
    }
    catch {
        $Message = if ($_.Exception -and $_.Exception.Message) { $_.Exception.Message } else { "Unknown command execution error" }
        Write-ArtifactText -Path $StderrPath -Value $Message
        Add-Gate -Name $Name -Status "FAIL" -Detail $Message -Artifact $StderrPath
    }
}

$Branch = (git branch --show-current).Trim()
$Head = (git rev-parse HEAD).Trim()
$OriginMain = ""

git status --short | Out-File (Join-Path $RunDir "git-status-short.txt") -Encoding UTF8
git log --oneline -n 20 | Out-File (Join-Path $RunDir "git-log-latest-20.txt") -Encoding UTF8

# Final release must run from main.
if ($Branch -eq "main") {
    Add-Gate -Name "release branch" -Status "PASS" -Detail "Running on main"
} else {
    Add-Gate -Name "release branch" -Status "FAIL" -Detail "Final release gate must run on main. Current branch: $Branch"
}

# Final release must have a clean tree.
$Dirty = git status --short
if ([string]::IsNullOrWhiteSpace($Dirty)) {
    Add-Gate -Name "working tree clean" -Status "PASS" -Detail "No uncommitted changes"
} else {
    Add-Gate -Name "working tree clean" -Status "FAIL" -Detail "Working tree has uncommitted changes" -Artifact (Join-Path $RunDir "git-status-short.txt")
}

# Final release must match origin/main.
try {
    git fetch origin main | Out-Null
    $OriginMain = (git rev-parse origin/main).Trim()

    if ($Head -eq $OriginMain) {
        Add-Gate -Name "main sync" -Status "PASS" -Detail "HEAD matches origin/main: $Head"
    } else {
        Add-Gate -Name "main sync" -Status "FAIL" -Detail "HEAD $Head does not match origin/main $OriginMain"
    }
}
catch {
    Add-Gate -Name "main sync" -Status "FAIL" -Detail $_.Exception.Message
}

# Required release-control files.
$RequiredFiles = @(
    "docs/testing/crown-test-inventory.json",
    "scripts/testing/check-crown-test-inventory.mjs",
    "scripts/testing/check-crown-discovered-surface-coverage.mjs",
    "scripts/testing/crown-surface-discovery.mjs",
    "docs/KNOWN_LIMITATIONS.md",
    "docs/release/INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md",
    "docs/release/README.md"
)

foreach ($File in $RequiredFiles) {
    if (Test-Path $File) {
        Add-Gate -Name "required file: $File" -Status "PASS" -Detail "Present"
    } else {
        Add-Gate -Name "required file: $File" -Status "FAIL" -Detail "Missing required release-control file"
    }
}

# Release-control validators.
Invoke-GateCommand `
    -Name "crown test inventory" `
    -FileName "node" `
    -Arguments @("scripts/testing/check-crown-test-inventory.mjs") `
    -TimeoutSeconds 300

Invoke-GateCommand `
    -Name "crown discovered surface coverage" `
    -FileName "node" `
    -Arguments @("scripts/testing/check-crown-discovered-surface-coverage.mjs") `
    -TimeoutSeconds 300

# Backend checks.
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

# Frontend checks.
if (Test-Path "frontend/dashboards/package.json") {
    Invoke-GateCommand `
        -Name "frontend build" `
        -FileName "npm" `
        -Arguments @("--prefix", "frontend/dashboards", "run", "build") `
        -TimeoutSeconds 1200

    $Pkg = Get-Content -Raw "frontend/dashboards/package.json"
    if ($Pkg -match '"verify:full"') {
        Invoke-GateCommand `
            -Name "frontend verify full" `
            -FileName "npm" `
            -Arguments @("--prefix", "frontend/dashboards", "run", "verify:full") `
            -TimeoutSeconds 1800
    } else {
        Add-Gate -Name "frontend verify full" -Status "FAIL" -Detail "frontend/dashboards/package.json missing verify:full script"
    }
} else {
    Add-Gate -Name "frontend package" -Status "FAIL" -Detail "frontend/dashboards/package.json missing"
}

# GitHub backlog checks.
if (Get-Command gh -ErrorAction SilentlyContinue) {
    try {
        gh pr list --state open --json number,title,headRefName,baseRefName,url |
            Out-File (Join-Path $RunDir "open-prs.json") -Encoding UTF8

        gh issue list --state open --json number,title,url |
            Out-File (Join-Path $RunDir "open-issues.json") -Encoding UTF8

        $OpenPrs = Get-Content -Raw (Join-Path $RunDir "open-prs.json") | ConvertFrom-Json
        $OpenIssues = Get-Content -Raw (Join-Path $RunDir "open-issues.json") | ConvertFrom-Json

        if (@($OpenPrs).Count -eq 0) {
            Add-Gate -Name "open PR backlog" -Status "PASS" -Detail "No open PRs"
        } else {
            Add-Gate -Name "open PR backlog" -Status "FAIL" -Detail "$(@($OpenPrs).Count) open PR(s)" -Artifact (Join-Path $RunDir "open-prs.json")
        }

        if (@($OpenIssues).Count -eq 0) {
            Add-Gate -Name "open issue backlog" -Status "PASS" -Detail "No open issues"
        } else {
            Add-Gate -Name "open issue backlog" -Status "FAIL" -Detail "$(@($OpenIssues).Count) open issue(s)" -Artifact (Join-Path $RunDir "open-issues.json")
        }
    }
    catch {
        Add-Gate -Name "github backlog scan" -Status "FAIL" -Detail $_.Exception.Message
    }
} else {
    Add-Gate -Name "github cli" -Status "FAIL" -Detail "gh CLI not available"
}

# Production currentness.
if ($SkipProductionProbe) {
    Add-Gate -Name "production currentness" -Status "WARN" -Detail "Skipped by -SkipProductionProbe"
} else {
    try {
        $Health = Invoke-RestMethod "https://crown-api-prod.azurewebsites.net/api/health/" -TimeoutSec 20
        $Health | ConvertTo-Json -Depth 20 | Out-File (Join-Path $RunDir "prod-health.json") -Encoding UTF8

        if ($Health.build_sha -and $Health.build_sha -eq $Head) {
            Add-Gate -Name "production currentness" -Status "PASS" -Detail "Production build_sha matches HEAD $Head" -Artifact (Join-Path $RunDir "prod-health.json")
        } else {
            Add-Gate -Name "production currentness" -Status "FAIL" -Detail "Production build_sha '$($Health.build_sha)' does not match HEAD '$Head'" -Artifact (Join-Path $RunDir "prod-health.json")
        }

        if ($Health.status -eq "ok" -or $Health.ok -eq $true) {
            Add-Gate -Name "production health" -Status "PASS" -Detail "Production health reports ok"
        } else {
            Add-Gate -Name "production health" -Status "FAIL" -Detail "Production health did not report ok"
        }

        if ($Health.db -eq "ok") {
            Add-Gate -Name "production database" -Status "PASS" -Detail "Production DB reports ok"
        } else {
            Add-Gate -Name "production database" -Status "FAIL" -Detail "Production DB did not report ok"
        }
    }
    catch {
        Add-Gate -Name "production probe" -Status "FAIL" -Detail $_.Exception.Message
    }
}

$FailCount = @($Gates | Where-Object { $_.status -eq "FAIL" }).Count
$WarnCount = @($Gates | Where-Object { $_.status -eq "WARN" }).Count
$PassCount = @($Gates | Where-Object { $_.status -eq "PASS" }).Count
$Decision = if ($FailCount -eq 0) { "GO-CANDIDATE" } else { "NO-GO" }

$Scorecard = [pscustomobject]@{
    run_id = $RunId
    decision = $Decision
    branch = $Branch
    head = $Head
    origin_main = $OriginMain
    pass = $PassCount
    warn = $WarnCount
    fail = $FailCount
    gates = $Gates
}

$JsonPath = Join-Path $RunDir "final-release-scorecard.json"
$MdPath = Join-Path $RunDir "final-release-scorecard.md"

$Scorecard | ConvertTo-Json -Depth 20 | Out-File $JsonPath -Encoding UTF8

$Md = @()
$Md += "# CROWN Final Release Gate Scorecard"
$Md += ""
$Md += "- Run ID: $RunId"
$Md += "- Decision: $Decision"
$Md += "- Branch: $Branch"
$Md += "- HEAD: $Head"
$Md += "- Origin main: $OriginMain"
$Md += "- PASS: $PassCount"
$Md += "- WARN: $WarnCount"
$Md += "- FAIL: $FailCount"
$Md += ""
$Md += "## Gates"
$Md += ""

foreach ($Gate in $Gates) {
    $Md += "- **$($Gate.status)** - $($Gate.name): $($Gate.detail)"
}

$Md -join "`n" | Out-File $MdPath -Encoding UTF8

Write-Host ""
Write-Host "Decision: $Decision"
Write-Host "PASS: $PassCount WARN: $WarnCount FAIL: $FailCount"
Write-Host "Scorecard: $MdPath"
Write-Host ""

if ($FailCount -gt 0) {
    exit 1
}

exit 0
