param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
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

function Try-RequestEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSec = 15
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSec -MaximumRedirection 2 -UseBasicParsing
        $sw.Stop()
        return [pscustomobject]@{
            url            = $Url
            success        = $true
            status_code    = [int]$response.StatusCode
            content_type   = [string]$response.Headers["Content-Type"]
            content_length = if ($response.Content) { [int]$response.Content.Length } else { 0 }
            elapsed_ms     = [int]$sw.ElapsedMilliseconds
            error_message  = $null
        }
    } catch {
        $sw.Stop()
        $statusCode = $null
        try {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $statusCode = [int]$_.Exception.Response.StatusCode
            }
        } catch {
        }

        return [pscustomobject]@{
            url            = $Url
            success        = $false
            status_code    = $statusCode
            content_type   = $null
            content_length = 0
            elapsed_ms     = [int]$sw.ElapsedMilliseconds
            error_message  = $_.Exception.Message
        }
    }
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$backendRoot = Join-Path $script:RepoRoot "backend"
$contractsRoot = Join-Path $script:RepoRoot "contracts"
$docsOpenApiRoot = Join-Path $script:RepoRoot "docs\openapi"
$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase7"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$endpointRows = New-Object System.Collections.Generic.List[object]
$endpointTargets = @(
    [pscustomobject]@{ label = "health"; path = "/api/health/" },
    [pscustomobject]@{ label = "integrity"; path = "/api/integrity/" },
    [pscustomobject]@{ label = "schema"; path = "/api/schema/" },
    [pscustomobject]@{ label = "openapi_json"; path = "/openapi.json" },
    [pscustomobject]@{ label = "swagger"; path = "/swagger/" },
    [pscustomobject]@{ label = "redoc"; path = "/redoc/" }
)

foreach ($target in $endpointTargets) {
    $result = Try-RequestEndpoint -Url ($BaseUrl.TrimEnd('/') + $target.path)
    $endpointRows.Add([pscustomobject]@{
        label          = $target.label
        url            = $result.url
        success        = $result.success
        status_code    = $result.status_code
        content_type   = $result.content_type
        content_length = $result.content_length
        elapsed_ms     = $result.elapsed_ms
        error_message  = $result.error_message
    }) | Out-Null
}

$backendFiles = @()
if (Test-Path $backendRoot) {
    $backendFiles = @(Get-ChildItem -Path $backendRoot -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
}

$patterns = @("/api/health/", "/api/integrity/", "/api/schema/", "openapi", "swagger", "redoc", "urlpatterns", "path(", "include(")
$urlScanLines = New-Object System.Collections.Generic.List[string]
$urlHitCount = 0
foreach ($pattern in $patterns) {
    $urlScanLines.Add("===== $pattern =====") | Out-Null
    $hits = @()
    if ($backendFiles.Count -gt 0) {
        $hits = @(Select-String -Path $backendFiles -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue)
    }
    foreach ($hit in $hits) {
        $urlHitCount += 1
        $urlScanLines.Add(("{0}:{1}:{2}" -f (Get-RepoRelativePath -FullPath $hit.Path -RepoRoot $script:RepoRoot), $hit.LineNumber, $hit.Line.Trim())) | Out-Null
    }
    $urlScanLines.Add("") | Out-Null
}

$urlScanFile = Join-Path $outDir "phase7_runtime_api_url_scan.txt"
Set-Content -Path $urlScanFile -Value ($urlScanLines -join "`r`n") -Encoding UTF8

$contractsFileCount = if (Test-Path $contractsRoot) {
    (Get-ChildItem -Path $contractsRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
} else {
    0
}

$openApiFileCount = if (Test-Path $docsOpenApiRoot) {
    (Get-ChildItem -Path $docsOpenApiRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
} else {
    0
}

$endpointCsv = Join-Path $outDir "phase7_runtime_endpoint_results.csv"
$summaryJson = Join-Path $outDir "phase7_runtime_and_api_surface_verification.json"
$summaryMd = Join-Path $outDir "phase7_runtime_and_api_surface_verification.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_RUNTIME_API_VERIFICATION.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_RUNTIME_API_VERIFICATION.json"

$endpointRows | Export-Csv -Path $endpointCsv -NoTypeInformation -Encoding UTF8

$endpointSuccessRows = @($endpointRows | Where-Object { $_.success })
$endpointSuccessCount = $endpointSuccessRows.Count

$summary = [ordered]@{
    generated_at_utc      = (Get-Date).ToUniversalTime().ToString("o")
    base_url              = $BaseUrl
    endpoint_count        = $endpointRows.Count
    endpoint_success_count = $endpointSuccessCount
    runtime_any_success   = ($endpointSuccessCount -gt 0)
    contracts_file_count  = $contractsFileCount
    openapi_file_count    = $openApiFileCount
    url_hit_count         = $urlHitCount
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    endpoints        = $endpointRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$endpointLines = ($endpointRows | ForEach-Object {
    "- $($_.label) | success=$($_.success) | status=$($_.status_code) | elapsed_ms=$($_.elapsed_ms) | url=$($_.url)"
}) -join "`r`n"

$markdown = @"
# LIVE RUNTIME API VERIFICATION

Generated UTC: $($summary.generated_at_utc)

## Runtime Summary
- base url: $($summary.base_url)
- endpoint count: $($summary.endpoint_count)
- endpoint success count: $($summary.endpoint_success_count)
- runtime any success: $($summary.runtime_any_success)
- contracts file count: $($summary.contracts_file_count)
- docs/openapi file count: $($summary.openapi_file_count)
- backend url hit count: $($summary.url_hit_count)

## Endpoint Results
$endpointLines

## Artifact Paths
- docs/release/live-audit/phase7/phase7_runtime_endpoint_results.csv
- docs/release/live-audit/phase7/phase7_runtime_api_url_scan.txt
"@

Set-Content -Path $liveMd -Value $markdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 7 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live runtime verification: $liveMd"
Write-Host ""
