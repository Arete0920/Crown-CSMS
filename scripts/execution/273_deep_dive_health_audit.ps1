$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Repo = "C:\w\crown_main_postmerge_verify"
if (!(Test-Path $Repo)) {
    throw "Repo path not found: $Repo"
}

Set-Location $Repo

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = "audit-artifacts\deep-dive-health\$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Invoke-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$FileName,
        [Parameter(Mandatory = $true)][scriptblock]$Block,
        [switch]$AllowFailure
    )

    $Path = Join-Path $Out $FileName
    try {
        & $Block *> $Path
    }
    catch {
        if ($AllowFailure) {
            $_ | Out-String | Add-Content $Path -Encoding UTF8
        }
        else {
            throw
        }
    }
}

Invoke-Capture -FileName "01_git_status_short.txt" -AllowFailure -Block {
    git status --short
    "ExitCode=$LASTEXITCODE"
}
Invoke-Capture -FileName "02_git_status_full.txt" -AllowFailure -Block {
    git status
    "ExitCode=$LASTEXITCODE"
}
Invoke-Capture -FileName "03_git_diff_stat.txt" -AllowFailure -Block {
    git diff --stat
    "ExitCode=$LASTEXITCODE"
}
Invoke-Capture -FileName "04_cached_diff_stat.txt" -AllowFailure -Block {
    git diff --cached --stat
    "ExitCode=$LASTEXITCODE"
}

Invoke-Capture -FileName "05_frontend_build.txt" -AllowFailure -Block {
    if (Test-Path "frontend\dashboards\package.json") {
        cmd /c "cd /d C:\w\crown_main_postmerge_verify\frontend\dashboards && npm run build"
        "ExitCode=$LASTEXITCODE"
    }
    else {
        "MISSING: frontend\\dashboards\\package.json"
    }
}

Invoke-Capture -FileName "06_backend_check_deploy.txt" -AllowFailure -Block {
    if (Test-Path "backend\manage.py") {
        cmd /c "cd /d C:\w\crown_main_postmerge_verify && python backend\manage.py check --deploy"
        "ExitCode=$LASTEXITCODE"
    }
    else {
        "MISSING: backend\\manage.py"
    }
}

$LatestPostAzure = Get-ChildItem "audit-artifacts\post-azure-live-proof" -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($LatestPostAzure) {
    $SummaryPath = Join-Path $LatestPostAzure.FullName "POST_AZURE_SUMMARY.md"
    if (Test-Path $SummaryPath) {
        Copy-Item $SummaryPath (Join-Path $Out "07_latest_post_azure_summary.md") -Force
    }
}

$Rows = Get-Content (Join-Path $Out "01_git_status_short.txt") -ErrorAction SilentlyContinue
$Classified = @()
foreach ($Row in $Rows) {
    if (-not $Row -or $Row.Trim().Length -eq 0) {
        continue
    }

    $Path = $Row.Substring(3).Trim()
    $Bucket = if ($Path -like ".vscode/*" -or
                     $Path -eq ".markdownlintignore" -or
                     $Path -like "scripts/execution/27*" -or
                     $Path -like "docs/crown-master-binder/operations/CURRENT_*") {
        "HYGIENE_OR_CONTROL"
    }
    elseif ($Path -like "audit-artifacts/*" -or $Path -like "docs/crown-master-binder/*") {
        "GENERATED_OR_BINDER"
    }
    elseif ($Path -like "frontend/*" -or $Path -like "backend/*" -or $Path -like ".github/*") {
        "APP_OR_PIPELINE"
    }
    else {
        "OTHER_REVIEW_REQUIRED"
    }

    $Classified += [pscustomobject]@{
        Status = $Row.Substring(0,2)
        Bucket = $Bucket
        Path = $Path
    }
}

$Classified | Export-Csv (Join-Path $Out "08_change_classification.csv") -NoTypeInformation
$BucketCounts = $Classified | Group-Object Bucket | Sort-Object Name
$BucketCounts | Select-Object Name, Count | Format-Table -AutoSize | Out-String |
    Out-File (Join-Path $Out "09_bucket_counts.txt") -Encoding UTF8

$BackendSecurityCount = 0
$BackendDeployFile = Join-Path $Out "06_backend_check_deploy.txt"
if (Test-Path $BackendDeployFile) {
    $BackendSecurityCount = @(Select-String -Path $BackendDeployFile -Pattern "security\\.W[0-9]+" -AllMatches).Count
}

$FrontendBuildFile = Join-Path $Out "05_frontend_build.txt"
$FrontendBuildPassed = $false
if (Test-Path $FrontendBuildFile) {
    $BuildText = Get-Content $FrontendBuildFile -Raw
    if ($BuildText -match "built in" -and $BuildText -notmatch "Command exited with code 1") {
        $FrontendBuildPassed = $true
    }
}

$TopChanged = $Classified | Group-Object Path | Sort-Object Count -Descending | Select-Object -First 30
$TopChanged | Select-Object Count, Name | Format-Table -AutoSize | Out-String |
    Out-File (Join-Path $Out "10_top_changed_paths.txt") -Encoding UTF8

$Summary = Join-Path $Out "00_DEEP_DIVE_SUMMARY.md"
@"
# CROWN Deep Dive Health Audit

Generated: $Stamp
Repo: $Repo

## Overall disposition

- Deployment status remains NO-GO until Azure live proof passes.
- Frontend build signal: $(if ($FrontendBuildPassed) { "PASS" } else { "FAIL_OR_UNSTABLE_CAPTURE" })
- Backend deploy security warning count: $BackendSecurityCount
- Current dirty rows: $(@($Rows).Count)

## Change buckets

$($BucketCounts | Select-Object Name, Count | Format-Table -AutoSize | Out-String)

## Read next

1. 06_backend_check_deploy.txt
2. 05_frontend_build.txt
3. 08_change_classification.csv
4. 09_bucket_counts.txt
5. 10_top_changed_paths.txt
6. 07_latest_post_azure_summary.md

## Guardrails

- Do not auto-commit app or pipeline code.
- Keep hygiene/control commits isolated.
- Keep production marked NO-GO while SHA mismatch or frontend 404 persists.
"@ | Out-File $Summary -Encoding UTF8

Write-Host ""
Write-Host "=== CROWN DEEP DIVE HEALTH AUDIT COMPLETE ==="
Write-Host "Out: $Out"
Write-Host "Summary: $Summary"
Write-Host ""

if (Get-Command code -ErrorAction SilentlyContinue) {
    code $Summary
    code $Out
}
