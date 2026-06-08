param(
    [string]$BaseRef = "origin/main",
    [string]$ExpectedFilesCsv = "",
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$AllowDirtyAuditArtifacts = $true
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Section {
    param([Parameter(Mandatory = $true)][string]$Text)
    Write-Host ""
    Write-Host "=== $Text ==="
}

function Add-Result {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Results,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$Detail = ""
    )

    $Results.Add([pscustomobject]@{
        Name = $Name
        Passed = $Passed
        Detail = $Detail
    }) | Out-Null
}

function Get-GitOutput {
    param([Parameter(Mandatory = $true)][string[]]$Args)

    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed: $output"
    }
    return @($output)
}

function Resolve-CrownPython {
    $candidatePaths = @(
        (Join-Path (Join-Path (Join-Path $repoRoot ".venv") "Scripts") "python.exe"),
        (Join-Path (Join-Path (Join-Path $repoRoot ".venv") "bin") "python")
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    foreach ($candidateName in @("python", "python3")) {
        $cmd = Get-Command $candidateName -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            return $cmd.Source
        }
    }

    return $null
}

$repoRoot = (Get-GitOutput @("rev-parse", "--show-toplevel") | Select-Object -First 1).Trim()
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$preflightRoot = Join-Path (Join-Path $repoRoot ".crown-audit") "release-pr-preflight"
$outDir = Join-Path $preflightRoot $stamp
$latestDir = Join-Path $preflightRoot "latest"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null

$transcript = Join-Path $outDir "preflight_console.txt"
Start-Transcript -Path $transcript -Force | Out-Null

$results = [System.Collections.Generic.List[object]]::new()

try {
    Write-Section "RELEASE PR PREFLIGHT"

    $branch = (Get-GitOutput @("branch", "--show-current") | Select-Object -First 1).Trim()
    $head = (Get-GitOutput @("rev-parse", "HEAD") | Select-Object -First 1).Trim()

    Write-Host "Repo: $repoRoot"
    Write-Host "Branch: $branch"
    Write-Host "HEAD: $head"
    Write-Host "BaseRef: $BaseRef"

    Write-Section "FETCH BASE"
    Get-GitOutput @("fetch", "origin") | ForEach-Object { Write-Host $_ }

    $baseExists = $true
    try {
        Get-GitOutput @("rev-parse", "--verify", $BaseRef) | Out-Null
    } catch {
        $baseExists = $false
    }
    Add-Result -Results $results -Name "base_ref_exists" -Passed $baseExists -Detail $BaseRef

    Write-Section "WORKTREE HYGIENE"
    $statusLines = @(git status --porcelain=v1)
    $blockingDirty = @(
        $statusLines | Where-Object {
            if ([string]::IsNullOrWhiteSpace($_)) { return $false }
            if ($AllowDirtyAuditArtifacts -and ($_ -match '\.crown-audit[\\/]|audit-artifacts[\\/]')) { return $false }
            return $true
        }
    )

    $statusLines | Set-Content (Join-Path $outDir "git_status_porcelain.txt") -Encoding UTF8
    Add-Result -Results $results -Name "worktree_clean" -Passed ($blockingDirty.Count -eq 0) -Detail "blocking_dirty_count=$($blockingDirty.Count)"

    if ($blockingDirty.Count -gt 0) {
        Write-Host "Blocking dirty rows:"
        $blockingDirty | ForEach-Object { Write-Host $_ }
    }

    Write-Section "DIFF SCOPE"
    $changedFiles = @()
    if (-not $baseExists) {
        Add-Result -Results $results -Name "diff_scope" -Passed $false -Detail "base_ref_missing=$BaseRef"
        "BASE REF MISSING: $BaseRef" | Set-Content (Join-Path $outDir "changed_files.txt") -Encoding UTF8
    } else {
        $changedFiles = @(Get-GitOutput @("diff", "--name-only", "$BaseRef...HEAD"))
        $changedFiles | Sort-Object | Set-Content (Join-Path $outDir "changed_files.txt") -Encoding UTF8
        Add-Result -Results $results -Name "diff_scope" -Passed $true -Detail "changed_file_count=$($changedFiles.Count)"
    }

    Write-Host "Changed file count: $($changedFiles.Count)"
    $changedFiles | Sort-Object | ForEach-Object { Write-Host $_ }

    if (-not [string]::IsNullOrWhiteSpace($ExpectedFilesCsv)) {
        $expected = @(
            $ExpectedFilesCsv.Split(",") |
                ForEach-Object { $_.Trim() } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                Sort-Object
        )
        $actual = @($changedFiles | Sort-Object)

        $missing = @($expected | Where-Object { $_ -notin $actual })
        $extra = @($actual | Where-Object { $_ -notin $expected })

        Add-Result -Results $results -Name "expected_file_scope" -Passed (($missing.Count -eq 0) -and ($extra.Count -eq 0)) -Detail "missing=$($missing.Count); extra=$($extra.Count)"

        if ($missing.Count -gt 0) {
            Write-Host "Missing expected files:"
            $missing | ForEach-Object { Write-Host $_ }
        }
        if ($extra.Count -gt 0) {
            Write-Host "Extra files:"
            $extra | ForEach-Object { Write-Host $_ }
        }
    } else {
        Add-Result -Results $results -Name "expected_file_scope" -Passed $true -Detail "not_provided"
    }

    Write-Section "POWERSHELL PARSE CHECK"
    $psFiles = @(git ls-files "*.ps1" "*.psm1")
    $parseErrors = [System.Collections.Generic.List[string]]::new()

    foreach ($file in $psFiles) {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repoRoot $file), [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) {
            foreach ($err in $errors) {
                $parseErrors.Add("$file :: $($err.Message)") | Out-Null
            }
        }
    }

    $parseErrors | Set-Content (Join-Path $outDir "powershell_parse_errors.txt") -Encoding UTF8
    Add-Result -Results $results -Name "powershell_parse" -Passed ($parseErrors.Count -eq 0) -Detail "parse_errors=$($parseErrors.Count)"

    Write-Section "CI PORTABILITY RISK SCAN"
    $riskPatterns = @(
        "cmd\.exe",
        "npm\.cmd",
        "npx\.cmd",
        "powershell\.exe",
        "Get-NetTCPConnection",
        '\$IsWindows',
        "netstat -ano"
    )

    $riskHits = [System.Collections.Generic.List[string]]::new()
    $scanFiles = @(
        $changedFiles |
            Where-Object { $_ -match '\.(ps1|psm1|yml|yaml|js|jsx|ts|tsx|json|py)$' } |
            Where-Object { Test-Path (Join-Path $repoRoot $_) }
    )

    foreach ($changedFile in $scanFiles) {
        $scanPath = Join-Path $repoRoot $changedFile
        foreach ($pattern in $riskPatterns) {
            $matches = @(Select-String -Path $scanPath -Pattern $pattern -ErrorAction SilentlyContinue)
            foreach ($m in $matches) {
                $riskHits.Add("${changedFile}:$($m.LineNumber): $($m.Line.Trim())") | Out-Null
            }
        }
    }

    $riskHits | Set-Content (Join-Path $outDir "ci_portability_risks.txt") -Encoding UTF8

    $unguardedHardRisks = @(
        $riskHits | Where-Object {
            ($_ -match "cmd\.exe|npm\.cmd|npx\.cmd|powershell\.exe") -and
            ($_ -notmatch "Resolve-CrownExecutable|Resolve-NpmCommand|Resolve-PowerShellCommand|IsWindowsPlatform|Get-Command")
        }
    )

    Add-Result -Results $results -Name "ci_portability_scan" -Passed ($unguardedHardRisks.Count -eq 0) -Detail "changed_files_scanned=$($scanFiles.Count); risk_hits=$($riskHits.Count); unguarded_hard_risks=$($unguardedHardRisks.Count)"

    Write-Section "BACKEND CHECK"
    if ($SkipBackend) {
        Add-Result -Results $results -Name "backend_manage_check" -Passed $true -Detail "skipped"
    } else {
        $pythonExe = Resolve-CrownPython
        $rootManage = Join-Path $repoRoot "manage.py"
        $backendRoot = Join-Path $repoRoot "backend"
        $backendManage = Join-Path $backendRoot "manage.py"

        if ($pythonExe -and (Test-Path $rootManage)) {
            & $pythonExe $rootManage check 2>&1 | Tee-Object -FilePath (Join-Path $outDir "backend_manage_check.txt")
            Add-Result -Results $results -Name "backend_manage_check" -Passed ($LASTEXITCODE -eq 0) -Detail "exit=$LASTEXITCODE"
        } elseif ($pythonExe -and (Test-Path $backendManage)) {
            Push-Location $backendRoot
            try {
                & $pythonExe manage.py check 2>&1 | Tee-Object -FilePath (Join-Path $outDir "backend_manage_check.txt")
                Add-Result -Results $results -Name "backend_manage_check" -Passed ($LASTEXITCODE -eq 0) -Detail "exit=$LASTEXITCODE"
            } finally {
                Pop-Location
            }
        } else {
            Add-Result -Results $results -Name "backend_manage_check" -Passed $false -Detail "python/manage.py not found"
        }
    }

    Write-Section "FRONTEND SHELL CONTRACTS"
    $dashRoot = Join-Path (Join-Path $repoRoot "frontend") "dashboards"
    if ($SkipFrontend) {
        Add-Result -Results $results -Name "frontend_shell_contracts" -Passed $true -Detail "skipped"
    } elseif (Test-Path (Join-Path $dashRoot "package.json")) {
        Push-Location $dashRoot
        try {
            npm run check:shell-contracts 2>&1 | Tee-Object -FilePath (Join-Path $outDir "frontend_shell_contracts.txt")
            Add-Result -Results $results -Name "frontend_shell_contracts" -Passed ($LASTEXITCODE -eq 0) -Detail "exit=$LASTEXITCODE"
        } finally {
            Pop-Location
        }
    } else {
        Add-Result -Results $results -Name "frontend_shell_contracts" -Passed $false -Detail "frontend/dashboards/package.json not found"
    }

    Write-Section "SUMMARY"
    $failed = @($results | Where-Object { -not $_.Passed })
    $passed = @($results | Where-Object { $_.Passed })

    $summary = [ordered]@{
        generated_at = (Get-Date).ToString("s")
        repo = $repoRoot
        branch = $branch
        head = $head
        base_ref = $BaseRef
        pass = ($failed.Count -eq 0)
        passed_count = $passed.Count
        failed_count = $failed.Count
        results = @($results)
        out_dir = $outDir
    }

    $summary | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outDir "99_STATUS.json") -Encoding UTF8
    $summary | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $latestDir "99_STATUS.json") -Encoding UTF8

    "PASS=$($summary.pass)" | Set-Content (Join-Path $outDir "00_SUMMARY.md") -Encoding UTF8
    "PASS=$($summary.pass)" | Set-Content (Join-Path $latestDir "00_SUMMARY.md") -Encoding UTF8

    Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

    $results | Format-Table -AutoSize

    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "FAILED PREFLIGHT ITEMS:"
        $failed | ForEach-Object { Write-Host "$($_.Name): $($_.Detail)" }
        exit 1
    }

    Write-Host "RELEASE_PR_PREFLIGHT_PASS=True"
    exit 0
}
finally {
    Stop-Transcript | Out-Null
}
