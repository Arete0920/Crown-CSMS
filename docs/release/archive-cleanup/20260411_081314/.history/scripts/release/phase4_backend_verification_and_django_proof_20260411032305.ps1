$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)
    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Invoke-ExternalCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [string]$WorkingDirectory = $script:RepoRoot
    )

    Push-Location $WorkingDirectory
    $nativePreferenceVar = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
    $hadNativePreference = ($null -ne $nativePreferenceVar)
    $oldNativePreference = if ($hadNativePreference) { [bool]$nativePreferenceVar.Value } else { $false }
    $oldErrorActionPreference = $ErrorActionPreference

    if ($hadNativePreference) {
        $global:PSNativeCommandUseErrorActionPreference = $false
    }
    $ErrorActionPreference = 'Continue'

    try {
        $text = & $Exe @Args 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
        if ($hadNativePreference) {
            $global:PSNativeCommandUseErrorActionPreference = $oldNativePreference
        }
        Pop-Location
    }

    $normalized = if ($text) { $text.TrimEnd() } else { "" }
    $header = @(
        "COMMAND: $Exe $($Args -join ' ')",
        "WORKDIR: $WorkingDirectory",
        "EXIT_CODE: $exitCode",
        ""
    ) -join "`r`n"

    Set-Content -Path $FilePath -Value ($header + $normalized + "`r`n") -Encoding UTF8

    return [pscustomobject]@{
        command   = "$Exe $($Args -join ' ')"
        exit_code = $exitCode
        path      = $FilePath
        success   = ($exitCode -eq 0)
    }
}

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )
    return ($FullPath.Substring($RepoRoot.Length).TrimStart('\', '/') -replace '\\', '/')
}

function Get-GitFileCommitIso {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    try {
        return (Invoke-Git -Args @("log", "-1", "--format=%cI", "--", $RelativePath))
    } catch {
        return $null
    }
}

function Get-SafeFileCount {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
}

function Get-PreferredPythonExe {
    $candidates = @(
        (Join-Path $script:RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $script:RepoRoot "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return "python"
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$backendRoot = Join-Path $script:RepoRoot "backend"
$managePy = Join-Path $backendRoot "manage.py"
if (-not (Test-Path $managePy)) {
    throw "Missing backend/manage.py"
}

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase4"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$pythonVersionFile = Join-Path $outDir "phase4_python_version.txt"
$djangoVersionFile = Join-Path $outDir "phase4_django_version.txt"
$checkFile = Join-Path $outDir "phase4_manage_check.txt"
$deployCheckFile = Join-Path $outDir "phase4_manage_check_deploy.txt"
$showMigrationsFile = Join-Path $outDir "phase4_showmigrations.txt"
$urlsSearchFile = Join-Path $outDir "phase4_url_surface_scan.txt"
$appInventoryCsv = Join-Path $outDir "phase4_backend_app_inventory.csv"
$testInventoryCsv = Join-Path $outDir "phase4_backend_test_inventory.csv"
$summaryJson = Join-Path $outDir "phase4_backend_verification_and_django_proof.json"
$summaryMd = Join-Path $outDir "phase4_backend_verification_and_django_proof.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_BACKEND_VERIFICATION.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_BACKEND_VERIFICATION.json"

$pythonExe = Get-PreferredPythonExe

$pythonVersion = Invoke-ExternalCapture -FilePath $pythonVersionFile -Exe $pythonExe -Args @("--version")
$djangoVersion = Invoke-ExternalCapture -FilePath $djangoVersionFile -Exe $pythonExe -Args @("-c", "import django; print(django.get_version())")
$checkResult = Invoke-ExternalCapture -FilePath $checkFile -Exe $pythonExe -Args @("backend/manage.py", "check")
$deployCheckResult = Invoke-ExternalCapture -FilePath $deployCheckFile -Exe $pythonExe -Args @("backend/manage.py", "check", "--deploy")
$showMigrationsResult = Invoke-ExternalCapture -FilePath $showMigrationsFile -Exe $pythonExe -Args @("backend/manage.py", "showmigrations")

$backendDirs = Get-ChildItem -Path $backendRoot -Directory | Sort-Object Name
$appInventory = New-Object System.Collections.Generic.List[object]
$testInventory = New-Object System.Collections.Generic.List[object]

foreach ($dir in $backendDirs) {
    $hasSignals = @(
        (Test-Path (Join-Path $dir.FullName "apps.py")),
        (Test-Path (Join-Path $dir.FullName "models.py")),
        (Test-Path (Join-Path $dir.FullName "views.py")),
        (Test-Path (Join-Path $dir.FullName "urls.py")),
        (Test-Path (Join-Path $dir.FullName "migrations")),
        (Test-Path (Join-Path $dir.FullName "tests"))
    ) -contains $true

    if (-not $hasSignals) { continue }

    $relative = Get-RepoRelativePath -FullPath $dir.FullName -RepoRoot $script:RepoRoot
    $testDir = Join-Path $dir.FullName "tests"
    $testFileCount = Get-SafeFileCount -Path $testDir
    $pyTestsOutsideDir = @(Get-ChildItem -Path $dir.FullName -File -Filter "test_*.py" -ErrorAction SilentlyContinue).Count

    $appInventory.Add([pscustomobject]@{
        module_name         = $dir.Name
        path                = $relative
        has_apps_py         = Test-Path (Join-Path $dir.FullName "apps.py")
        has_models_py       = Test-Path (Join-Path $dir.FullName "models.py")
        has_views_py        = Test-Path (Join-Path $dir.FullName "views.py")
        has_urls_py         = Test-Path (Join-Path $dir.FullName "urls.py")
        has_admin_py        = Test-Path (Join-Path $dir.FullName "admin.py")
        has_migrations      = Test-Path (Join-Path $dir.FullName "migrations")
        has_tests_dir       = Test-Path $testDir
        test_file_count     = ($testFileCount + $pyTestsOutsideDir)
        total_file_count    = Get-SafeFileCount -Path $dir.FullName
        last_commit_iso     = Get-GitFileCommitIso -RelativePath $relative
    }) | Out-Null

    if (Test-Path $testDir) {
        Get-ChildItem -Path $testDir -Recurse -File -Filter "*.py" -ErrorAction SilentlyContinue | ForEach-Object {
            $testInventory.Add([pscustomobject]@{
                module_name      = $dir.Name
                test_path        = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot
                size_bytes       = [int64]$_.Length
                last_commit_iso  = Get-GitFileCommitIso -RelativePath (Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot)
            }) | Out-Null
        }
    }

    Get-ChildItem -Path $dir.FullName -File -Filter "test_*.py" -ErrorAction SilentlyContinue | ForEach-Object {
        $testInventory.Add([pscustomobject]@{
            module_name      = $dir.Name
            test_path        = Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot
            size_bytes       = [int64]$_.Length
            last_commit_iso  = Get-GitFileCommitIso -RelativePath (Get-RepoRelativePath -FullPath $_.FullName -RepoRoot $script:RepoRoot)
        }) | Out-Null
    }
}

$appInventory | Export-Csv -Path $appInventoryCsv -NoTypeInformation -Encoding UTF8
$testInventory | Export-Csv -Path $testInventoryCsv -NoTypeInformation -Encoding UTF8

$allBackendFiles = Get-ChildItem -Path $backendRoot -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
$urlPatterns = @("/api/health/", "/api/integrity/", "urlpatterns", "path(", "include(")
$urlLines = New-Object System.Collections.Generic.List[string]
foreach ($pattern in $urlPatterns) {
    $urlLines.Add("===== $pattern =====") | Out-Null
    $hits = Select-String -Path $allBackendFiles -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
    foreach ($hit in $hits) {
        $urlLines.Add(("{0}:{1}:{2}" -f (Get-RepoRelativePath -FullPath $hit.Path -RepoRoot $script:RepoRoot), $hit.LineNumber, $hit.Line.Trim())) | Out-Null
    }
    $urlLines.Add("") | Out-Null
}
Set-Content -Path $urlsSearchFile -Value ($urlLines -join "`r`n") -Encoding UTF8

$appsWithModels = @($appInventory | Where-Object { $_.has_models_py }).Count
$appsWithUrls = @($appInventory | Where-Object { $_.has_urls_py }).Count
$appsWithTests = @($appInventory | Where-Object { $_.test_file_count -gt 0 }).Count
$totalApps = @($appInventory).Count
$totalTests = @($testInventory).Count

$summary = [ordered]@{
    generated_at_utc      = (Get-Date).ToUniversalTime().ToString("o")
    repo_root             = $script:RepoRoot
    backend_root          = $backendRoot
    manage_py_exists      = (Test-Path $managePy)
    python_version_ok     = $pythonVersion.success
    django_import_ok      = $djangoVersion.success
    manage_check_ok       = $checkResult.success
    manage_check_deploy_ok = $deployCheckResult.success
    showmigrations_ok     = $showMigrationsResult.success
    backend_app_count     = $totalApps
    backend_apps_with_models = $appsWithModels
    backend_apps_with_urls = $appsWithUrls
    backend_apps_with_tests = $appsWithTests
    backend_test_file_count = $totalTests
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    app_inventory    = $appInventory
    test_inventory   = $testInventory
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$topApps = ($appInventory | Sort-Object module_name | Select-Object -First 60 | ForEach-Object {
    "- $($_.module_name) | models=$($_.has_models_py) | urls=$($_.has_urls_py) | tests=$($_.test_file_count) | last_commit=$($_.last_commit_iso)"
}) -join "`r`n"

$liveMarkdown = @"
# LIVE BACKEND VERIFICATION

Generated UTC: $($summary.generated_at_utc)

## Command Results
- python --version: $($pythonVersion.success)
- django import/version: $($djangoVersion.success)
- manage.py check: $($checkResult.success)
- manage.py check --deploy: $($deployCheckResult.success)
- manage.py showmigrations: $($showMigrationsResult.success)

## Backend Inventory
- backend app count: $($summary.backend_app_count)
- apps with models.py: $($summary.backend_apps_with_models)
- apps with urls.py: $($summary.backend_apps_with_urls)
- apps with tests: $($summary.backend_apps_with_tests)
- backend test file count: $($summary.backend_test_file_count)

## Backend Module Snapshot
$topApps

## Artifact Paths
- docs/release/live-audit/phase4/phase4_python_version.txt
- docs/release/live-audit/phase4/phase4_django_version.txt
- docs/release/live-audit/phase4/phase4_manage_check.txt
- docs/release/live-audit/phase4/phase4_manage_check_deploy.txt
- docs/release/live-audit/phase4/phase4_showmigrations.txt
- docs/release/live-audit/phase4/phase4_url_surface_scan.txt
- docs/release/live-audit/phase4/phase4_backend_app_inventory.csv
- docs/release/live-audit/phase4/phase4_backend_test_inventory.csv
"@

Set-Content -Path $liveMd -Value $liveMarkdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $liveMarkdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 4 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live backend verification: $liveMd"
Write-Host ""
