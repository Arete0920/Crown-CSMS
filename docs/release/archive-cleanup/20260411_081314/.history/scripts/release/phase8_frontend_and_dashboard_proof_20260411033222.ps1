param(
    [switch]$SkipBuild
)

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

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )
    return ($FullPath.Substring($RepoRoot.Length).TrimStart('\', '/') -replace '\\', '/')
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

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$frontendRoot = Join-Path $script:RepoRoot "frontend"
if (-not (Test-Path $frontendRoot)) {
    throw "Missing frontend directory"
}

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase8"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$nodeVersionFile = Join-Path $outDir "phase8_node_version.txt"
$nodeVersionResult = Invoke-ExternalCapture -FilePath $nodeVersionFile -Exe "node" -Args @("--version")

$packageFiles = @(Get-ChildItem -Path $frontendRoot -Recurse -File -Filter "package.json" -ErrorAction SilentlyContinue | Sort-Object FullName)
$packageRows = New-Object System.Collections.Generic.List[object]
$buildRows = New-Object System.Collections.Generic.List[object]
$pathRows = New-Object System.Collections.Generic.List[object]

foreach ($pkg in $packageFiles) {
    $pkgDir = Split-Path -Parent $pkg.FullName
    $relativePkg = Get-RepoRelativePath -FullPath $pkg.FullName -RepoRoot $script:RepoRoot
    $pkgJson = Get-Content -Path $pkg.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $scripts = $null
    if ($pkgJson.PSObject.Properties.Name -contains 'scripts') {
        $scripts = $pkgJson.scripts
    }
    $scriptNames = @()
    if ($null -ne $scripts) {
        $scriptNames = @($scripts.PSObject.Properties.Name)
    }

    $hasBuild = $scriptNames -contains "build"
    $hasTest = $scriptNames -contains "test"
    $hasLint = $scriptNames -contains "lint"
    $packageName = if ($pkgJson.PSObject.Properties.Name -contains 'name' -and -not [string]::IsNullOrWhiteSpace([string]$pkgJson.name)) {
        [string]$pkgJson.name
    } else {
        Split-Path -Leaf $pkgDir
    }

    $lockManager = if (Test-Path (Join-Path $pkgDir "pnpm-lock.yaml")) {
        "pnpm"
    } elseif (Test-Path (Join-Path $pkgDir "yarn.lock")) {
        "yarn"
    } elseif (Test-Path (Join-Path $pkgDir "package-lock.json")) {
        "npm"
    } else {
        "unknown"
    }

    $packageRows.Add([pscustomobject]@{
        package_name      = $packageName
        package_path      = $relativePkg
        package_dir       = Get-RepoRelativePath -FullPath $pkgDir -RepoRoot $script:RepoRoot
        has_build_script  = $hasBuild
        has_test_script   = $hasTest
        has_lint_script   = $hasLint
        lock_manager      = $lockManager
        script_names      = ($scriptNames -join ', ')
    }) | Out-Null

    if (-not $SkipBuild -and $hasBuild) {
        $safeDirName = ((Get-RepoRelativePath -FullPath $pkgDir -RepoRoot $script:RepoRoot) -replace '[^A-Za-z0-9\-_]', '_')
        $buildLog = Join-Path $outDir ("phase8_build_{0}.txt" -f $safeDirName)
        $result = Invoke-ExternalCapture -FilePath $buildLog -Exe "npm" -Args @("run", "build", "--if-present") -WorkingDirectory $pkgDir
        $buildRows.Add([pscustomobject]@{
            package_name    = [string]$pkgJson.name
            package_dir     = Get-RepoRelativePath -FullPath $pkgDir -RepoRoot $script:RepoRoot
            build_attempted = $true
            build_success   = $result.success
            build_log_path  = Get-RepoRelativePath -FullPath $buildLog -RepoRoot $script:RepoRoot
        }) | Out-Null
    } else {
        $buildRows.Add([pscustomobject]@{
            package_name    = [string]$pkgJson.name
            package_dir     = Get-RepoRelativePath -FullPath $pkgDir -RepoRoot $script:RepoRoot
            build_attempted = $false
            build_success   = $false
            build_log_path  = $null
        }) | Out-Null
    }
}

$frontendFiles = @(Get-ChildItem -Path $frontendRoot -Recurse -File -Include *.tsx,*.ts,*.jsx,*.js -ErrorAction SilentlyContinue)
$dashboardFiles = @($frontendFiles | Where-Object { $_.Name -match 'Dashboard' -or $_.FullName -match '\\dashboards\\|/dashboards/' })
$routeFiles = @($frontendFiles | Where-Object { $_.Name -match 'routes|router|Route' -or $_.FullName -match '\\pages\\|/pages/' })
$componentFiles = @($frontendFiles | Where-Object { $_.FullName -match '\\components\\|/components/' })
$portalFiles = @($frontendFiles | Where-Object { $_.Name -match 'Portal|Parent|Student|Executive|Admin' })

foreach ($file in ($dashboardFiles + $routeFiles + $componentFiles + $portalFiles | Select-Object -Unique)) {
    $category = if ($file.FullName -in $dashboardFiles.FullName) {
        "dashboard"
    } elseif ($file.FullName -in $routeFiles.FullName) {
        "route"
    } elseif ($file.FullName -in $componentFiles.FullName) {
        "component"
    } else {
        "portal"
    }

    $pathRows.Add([pscustomobject]@{
        path       = Get-RepoRelativePath -FullPath $file.FullName -RepoRoot $script:RepoRoot
        category   = $category
        size_bytes = [int64]$file.Length
    }) | Out-Null
}

$packageCsv = Join-Path $outDir "phase8_frontend_packages.csv"
$buildCsv = Join-Path $outDir "phase8_frontend_build_results.csv"
$pathCsv = Join-Path $outDir "phase8_frontend_surface_paths.csv"
$summaryJson = Join-Path $outDir "phase8_frontend_and_dashboard_proof.json"
$summaryMd = Join-Path $outDir "phase8_frontend_and_dashboard_proof.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_FRONTEND_DASHBOARD_PROOF.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_FRONTEND_DASHBOARD_PROOF.json"

$packageRows | Export-Csv -Path $packageCsv -NoTypeInformation -Encoding UTF8
$buildRows | Export-Csv -Path $buildCsv -NoTypeInformation -Encoding UTF8
$pathRows | Export-Csv -Path $pathCsv -NoTypeInformation -Encoding UTF8

$buildAttemptRows = @($buildRows | Where-Object { $_.build_attempted })
$buildSuccessRows = @($buildRows | Where-Object { $_.build_success })

$packagesWithBuildRows = @($packageRows | Where-Object { $_.has_build_script })

$summary = [ordered]@{
    generated_at_utc     = (Get-Date).ToUniversalTime().ToString("o")
    node_available       = $nodeVersionResult.success
    package_count        = $packageRows.Count
    packages_with_build  = $packagesWithBuildRows.Count
    build_attempt_count  = $buildAttemptRows.Count
    build_success_count  = $buildSuccessRows.Count
    dashboard_file_count = $dashboardFiles.Count
    route_file_count     = $routeFiles.Count
    component_file_count = $componentFiles.Count
    portal_file_count    = $portalFiles.Count
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    packages         = $packageRows
    builds           = $buildRows
    paths            = $pathRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$packageLines = ($packageRows | ForEach-Object {
    "- $($_.package_name) | build=$($_.has_build_script) | test=$($_.has_test_script) | lint=$($_.has_lint_script) | manager=$($_.lock_manager) | dir=$($_.package_dir)"
}) -join "`r`n"

$buildLines = if ($buildAttemptRows.Count -gt 0) {
    ($buildRows | Where-Object { $_.build_attempted } | ForEach-Object {
        "- $($_.package_name) | success=$($_.build_success) | log=$($_.build_log_path)"
    }) -join "`r`n"
} else {
    "- no build attempts"
}

$markdown = @"
# LIVE FRONTEND DASHBOARD PROOF

Generated UTC: $($summary.generated_at_utc)

## Frontend Summary
- node available: $($summary.node_available)
- package count: $($summary.package_count)
- packages with build script: $($summary.packages_with_build)
- build attempt count: $($summary.build_attempt_count)
- build success count: $($summary.build_success_count)
- dashboard file count: $($summary.dashboard_file_count)
- route file count: $($summary.route_file_count)
- component file count: $($summary.component_file_count)
- portal file count: $($summary.portal_file_count)

## Packages
$packageLines

## Build Results
$buildLines

## Artifact Paths
- docs/release/live-audit/phase8/phase8_frontend_packages.csv
- docs/release/live-audit/phase8/phase8_frontend_build_results.csv
- docs/release/live-audit/phase8/phase8_frontend_surface_paths.csv
"@

Set-Content -Path $liveMd -Value $markdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 8 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live frontend proof: $liveMd"
Write-Host ""
