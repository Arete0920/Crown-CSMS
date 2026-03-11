#!/usr/bin/env pwsh
param(
    [string]$AppName = "crown-api-prod",
    [string]$ResourceGroup = "crown-rg",
    [string]$HealthUrl = "https://crown-api-prod.azurewebsites.net/health",
    [string]$OutputDir = "release_proof",
    [string]$ExpectedSha = "",
    [string]$ExpectedTag = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) is required."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $OutputDir $stamp
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

Write-Host "Collecting release proof into: $runDir"

$healthText = ""
try {
    $healthText = & curl.exe -fsS $HealthUrl
}
catch {
    $healthText = "{`"error`":`"health probe failed`"}"
}
$healthPath = Join-Path $runDir "health.json"
Set-Content -Path $healthPath -Value $healthText -Encoding utf8

$runtimePath = Join-Path $runDir "runtime.json"
& az webapp config container show --name $AppName --resource-group $ResourceGroup -o json | Out-File -FilePath $runtimePath -Encoding utf8

$appSettingsPath = Join-Path $runDir "appsettings_keys.txt"
& az webapp config appsettings list --name $AppName --resource-group $ResourceGroup --query "[].name" -o tsv | Out-File -FilePath $appSettingsPath -Encoding utf8

$summary = [ordered]@{
    timestamp_utc               = (Get-Date).ToUniversalTime().ToString("o")
    app_name                    = $AppName
    resource_group              = $ResourceGroup
    health_url                  = $HealthUrl
    expected_sha                = $ExpectedSha
    expected_tag                = $ExpectedTag
    health_status               = "unknown"
    health_build_sha            = ""
    health_prod_deploy_tag      = ""
    appsettings_build_sha       = ""
    appsettings_prod_deploy_tag = ""
    verdict                     = "UNKNOWN"
}

$health = $null
try {
    $health = Get-Content $healthPath -Raw | ConvertFrom-Json
    if ($health.status) { $summary.health_status = [string]$health.status }
    if ($health.build_sha) { $summary.health_build_sha = [string]$health.build_sha }
    if ($health.prod_deploy_tag) { $summary.health_prod_deploy_tag = [string]$health.prod_deploy_tag }
}
catch {
    # Keep defaults for non-JSON or failing health response.
}

try {
    $buildSha = & az webapp config appsettings list --name $AppName --resource-group $ResourceGroup --query "[?name=='BUILD_SHA'].value | [0]" -o tsv
    $deployTag = & az webapp config appsettings list --name $AppName --resource-group $ResourceGroup --query "[?name=='PROD_DEPLOY_TAG'].value | [0]" -o tsv
    if ($buildSha) { $summary.appsettings_build_sha = [string]$buildSha }
    if ($deployTag) { $summary.appsettings_prod_deploy_tag = [string]$deployTag }
}
catch {
    # Keep defaults if appsettings read fails.
}

$shaOk = $true
if ($ExpectedSha) {
    $liveSha = $summary.health_build_sha
    $appSha = $summary.appsettings_build_sha
    $shaOk = ($liveSha -eq $ExpectedSha) -or ($appSha -eq $ExpectedSha)
}

$tagOk = $true
if ($ExpectedTag) {
    $liveTag = $summary.health_prod_deploy_tag
    $appTag = $summary.appsettings_prod_deploy_tag
    $tagOk = ($liveTag -eq $ExpectedTag) -or ($appTag -eq $ExpectedTag)
}

if ($shaOk -and $tagOk -and $summary.health_status -eq "ok") {
    $summary.verdict = "PASS"
}
else {
    $summary.verdict = "FAIL"
}

$summaryPath = Join-Path $runDir "summary.json"
$summary | ConvertTo-Json -Depth 6 | Out-File -FilePath $summaryPath -Encoding utf8

$zipPath = Join-Path $OutputDir ("release_proof_{0}.zip" -f $stamp)
Compress-Archive -Path (Join-Path $runDir "*") -DestinationPath $zipPath -Force

Write-Host "Summary: $summaryPath"
Write-Host "Archive: $zipPath"
Write-Host "Verdict: $($summary.verdict)"

if ($summary.verdict -ne "PASS") {
    exit 2
}
